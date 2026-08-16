"""
============================================================
AVORA Structured Memory
============================================================

The existing memory.py stores flat user "facts" and stays the
source of truth for those. This module adds the *structured*
memory the agent loop needs, without duplicating that store.

Memory types
------------
- project     : known projects, their paths, frameworks, quirks
- preference  : how the user likes things done
- episodic    : what happened (tasks, outcomes, errors and fixes)
- solution    : error signature -> fix that actually worked
- workflow    : repeated action sequences worth automating

Retrieval is relevance-scored, not "dump everything", so prompts
stay small and useful.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AgentMemory")

MAX_PER_TYPE = {
    "project": 100,
    "preference": 200,
    "episodic": 400,
    "solution": 300,
    "workflow": 100,
}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "to", "of", "in", "on", "at", "for", "with", "my", "me", "i", "you",
    "it", "this", "that", "please", "can", "do", "did", "does", "how",
    "what", "why", "when", "where", "avora", "fix", "make", "get", "run",
}


def _tokens(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9_\-\.]+", str(text).lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


@dataclass
class MemoryEntry:
    """A single structured memory."""

    id: str
    type: str
    key: str
    value: Any
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "episodic"),
            key=data.get("key", ""),
            value=data.get("value"),
            tags=list(data.get("tags") or []),
            created_at=data.get("created_at", time.time()),
            last_used=data.get("last_used", time.time()),
            use_count=int(data.get("use_count", 0) or 0),
            confidence=float(data.get("confidence", 1.0) or 1.0),
        )

    def text_blob(self) -> str:
        return f"{self.key} {self.value} {' '.join(self.tags)}"


class MemoryEngine:
    """Structured, relevance-retrieved long-term memory."""

    _instance: Optional["MemoryEngine"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_ready", False):
            return
        self._ready = True
        self._entries: Dict[str, MemoryEntry] = {}
        self._state_lock = threading.RLock()
        self._store = self._resolve_store()
        self._load()

    def _resolve_store(self) -> Path:
        try:
            from app_paths import APP_DATA_DIR

            base = Path(APP_DATA_DIR)
        except Exception:
            base = Path(
                os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            ) / "AVORA"
        base.mkdir(parents=True, exist_ok=True)
        return base / "agent_memory.json"

    def _load(self) -> None:
        try:
            if not self._store.exists():
                return
            data = json.loads(self._store.read_text(encoding="utf-8"))
            with self._state_lock:
                for item in data.get("entries", []):
                    entry = MemoryEntry.from_dict(item)
                    if entry.id:
                        self._entries[entry.id] = entry
            logger.info("Loaded %d structured memories", len(self._entries))
        except Exception as exc:
            logger.warning("Memory load failed: %s", exc)

    def _save(self) -> None:
        try:
            with self._state_lock:
                payload = {"entries": [e.to_dict() for e in self._entries.values()]}
            tmp = self._store.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            tmp.replace(self._store)
        except Exception as exc:
            logger.warning("Memory save failed: %s", exc)

    # -- Write -----------------------------------------------------

    def remember(
        self,
        type: str,
        key: str,
        value: Any,
        tags: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> MemoryEntry:
        """
        Store or update a memory.

        Same (type, key) updates in place so memory converges instead
        of accumulating duplicates.
        """
        entry_id = f"{type}:{re.sub(r'[^a-z0-9]+', '_', str(key).lower())[:80]}"
        now = time.time()
        with self._state_lock:
            existing = self._entries.get(entry_id)
            if existing:
                existing.value = value
                existing.last_used = now
                existing.use_count += 1
                existing.confidence = max(existing.confidence, confidence)
                if tags:
                    existing.tags = sorted(set(existing.tags) | set(tags))
                entry = existing
            else:
                entry = MemoryEntry(
                    id=entry_id, type=type, key=str(key), value=value,
                    tags=sorted(set(tags or [])), confidence=confidence,
                )
                self._entries[entry_id] = entry
            self._prune(type)
        self._save()
        return entry

    def _prune(self, type: str) -> None:
        """Drop least-valuable entries when a type exceeds its cap."""
        cap = MAX_PER_TYPE.get(type, 200)
        of_type = [e for e in self._entries.values() if e.type == type]
        if len(of_type) <= cap:
            return
        of_type.sort(key=lambda e: (e.use_count, e.last_used))
        for entry in of_type[: len(of_type) - cap]:
            self._entries.pop(entry.id, None)

    # -- Domain helpers -------------------------------------------

    def remember_project(self, path: str, info: Dict[str, Any]) -> MemoryEntry:
        name = info.get("name") or Path(path).name
        return self.remember(
            "project", name,
            {
                "path": path,
                "kind": info.get("kind"),
                "frameworks": info.get("frameworks", []),
                "test_command": info.get("test_command"),
                "build_command": info.get("build_command"),
                "dev_command": info.get("dev_command"),
                "deployment_targets": info.get("deployment_targets", []),
            },
            tags=["project", str(info.get("kind") or "")] + list(info.get("frameworks") or []),
        )

    def remember_solution(self, error_signature: str, fix: str, worked: bool = True) -> MemoryEntry:
        """Record that a specific fix resolved a specific error."""
        return self.remember(
            "solution", error_signature[:80],
            {"error": error_signature, "fix": fix, "worked": worked},
            tags=["solution"], confidence=1.0 if worked else 0.3,
        )

    def recall_solution(self, error_signature: str) -> Optional[Dict[str, Any]]:
        """Look up a previously successful fix for this error."""
        results = self.retrieve(error_signature, types=["solution"], limit=1, min_score=0.3)
        if results and isinstance(results[0].value, dict):
            if results[0].value.get("worked"):
                return results[0].value
        return None

    def remember_preference(self, key: str, value: Any) -> MemoryEntry:
        return self.remember("preference", key, value, tags=["preference"])

    def record_episode(
        self, goal: str, outcome: str, detail: str = "", tags: Optional[List[str]] = None
    ) -> MemoryEntry:
        return self.remember(
            "episodic", f"{goal[:60]}@{int(time.time())}",
            {"goal": goal, "outcome": outcome, "detail": detail[:500], "at": time.time()},
            tags=(tags or []) + ["episode", outcome],
        )

    def get_projects(self) -> List[Dict[str, Any]]:
        with self._state_lock:
            projects = [e for e in self._entries.values() if e.type == "project"]
        projects.sort(key=lambda e: e.last_used, reverse=True)
        return [{"name": e.key, **(e.value if isinstance(e.value, dict) else {})} for e in projects]

    def find_project(self, query: str) -> Optional[Dict[str, Any]]:
        """Find a remembered project by fuzzy name."""
        needle = (query or "").strip().lower()
        if not needle:
            return None
        for project in self.get_projects():
            name = str(project.get("name", "")).lower()
            if needle == name or needle in name or name in needle:
                path = project.get("path")
                if path and Path(path).is_dir():
                    return project
        return None

    # -- Read ------------------------------------------------------

    def retrieve(
        self,
        query: str,
        types: Optional[List[str]] = None,
        limit: int = 8,
        min_score: float = 0.15,
    ) -> List[MemoryEntry]:
        """Relevance-scored retrieval. Only returns what's actually related."""
        query_tokens = set(_tokens(query))
        if not query_tokens:
            return []

        now = time.time()
        scored: List[tuple] = []
        with self._state_lock:
            candidates = [
                e for e in self._entries.values() if not types or e.type in types
            ]

        for entry in candidates:
            entry_tokens = set(_tokens(entry.text_blob()))
            if not entry_tokens:
                continue
            overlap = query_tokens & entry_tokens
            if not overlap:
                continue
            # Jaccard-ish overlap, weighted by usefulness and recency.
            score = len(overlap) / len(query_tokens)
            score *= 0.6 + 0.4 * entry.confidence
            age_days = max(0.0, (now - entry.last_used) / 86400)
            score *= 1.0 / (1.0 + 0.02 * age_days)
            score *= 1.0 + min(0.3, 0.05 * entry.use_count)
            if score >= min_score:
                scored.append((score, entry))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = [entry for _, entry in scored[:limit]]

        now = time.time()
        with self._state_lock:
            for entry in top:
                entry.last_used = now
                entry.use_count += 1
        return top

    def build_context(self, query: str, limit: int = 6) -> str:
        """
        Compact, relevant memory context for the prompt.

        Returns "" when nothing is relevant, so we never pad prompts.
        """
        entries = self.retrieve(query, limit=limit)
        if not entries:
            return ""
        lines: List[str] = []
        for entry in entries:
            value = entry.value
            if isinstance(value, dict):
                if entry.type == "project":
                    lines.append(
                        f"- Project '{entry.key}': {value.get('path')} "
                        f"({value.get('kind')}, {', '.join(value.get('frameworks') or [])})"
                    )
                elif entry.type == "solution":
                    lines.append(
                        f"- Previously fixed '{str(value.get('error'))[:60]}' by: {value.get('fix')}"
                    )
                elif entry.type == "episodic":
                    lines.append(f"- Earlier: {value.get('goal')} -> {value.get('outcome')}")
                else:
                    lines.append(f"- {entry.key}: {json.dumps(value, default=str)[:160]}")
            else:
                lines.append(f"- {entry.key}: {str(value)[:160]}")
        return "\n".join(lines)

    def stats(self) -> Dict[str, Any]:
        with self._state_lock:
            counts: Dict[str, int] = {}
            for entry in self._entries.values():
                counts[entry.type] = counts.get(entry.type, 0) + 1
            return {"total": len(self._entries), "by_type": counts, "store": str(self._store)}

    def forget(self, entry_id: str) -> bool:
        with self._state_lock:
            removed = self._entries.pop(entry_id, None) is not None
        if removed:
            self._save()
        return removed

    def clear(self, type: Optional[str] = None) -> int:
        with self._state_lock:
            if type is None:
                count = len(self._entries)
                self._entries = {}
            else:
                targets = [k for k, v in self._entries.items() if v.type == type]
                for key in targets:
                    self._entries.pop(key, None)
                count = len(targets)
        self._save()
        return count


_engine: Optional[MemoryEngine] = None


def get_memory_engine() -> MemoryEngine:
    global _engine
    if _engine is None:
        _engine = MemoryEngine()
    return _engine


__all__ = ["MemoryEngine", "MemoryEntry", "get_memory_engine"]
