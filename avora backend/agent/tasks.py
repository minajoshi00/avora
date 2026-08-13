"""
============================================================
AVORA Task State & Persistence
============================================================

Tasks survive restarts so "continue what we were doing" works
for real, and so a task blocked on a login can resume after the
user authenticates.

Lifecycle
---------
CREATED -> PLANNING -> RUNNING -> VERIFYING -> COMPLETED
                    \-> WAITING_FOR_PERMISSION -> RUNNING
                    \-> WAITING_FOR_USER       -> RUNNING
                    \-> BLOCKED / FAILED / CANCELLED
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AgentTasks")


class TaskState:
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    VERIFYING = "VERIFYING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    #: States where the task can still make progress.
    RESUMABLE = (
        WAITING_FOR_PERMISSION, WAITING_FOR_USER, BLOCKED, PLANNING, RUNNING,
    )
    TERMINAL = (COMPLETED, CANCELLED, FAILED)


@dataclass
class PlanStep:
    """One step of an executable plan."""

    index: int
    description: str
    tool: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending|running|done|failed|skipped
    result: Optional[Dict[str, Any]] = None
    attempts: int = 0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        return cls(
            index=int(data.get("index", 0)),
            description=data.get("description", ""),
            tool=data.get("tool"),
            args=dict(data.get("args") or {}),
            status=data.get("status", "pending"),
            result=data.get("result"),
            attempts=int(data.get("attempts", 0) or 0),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
        )


@dataclass
class AgentTask:
    """A goal AVORA is working on."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    goal: str = ""
    state: str = TaskState.CREATED
    steps: List[PlanStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    project_path: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    blocked_reason: str = ""
    pending_permission: Optional[Dict[str, Any]] = None
    summary: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    undo_stack: List[Dict[str, Any]] = field(default_factory=list)

    # -- Progress --------------------------------------------------

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        done = sum(1 for s in self.steps if s.status in ("done", "skipped"))
        return round(done / len(self.steps), 3)

    @property
    def current_step(self) -> Optional[PlanStep]:
        for step in self.steps:
            if step.status in ("pending", "running"):
                return step
        return None

    @property
    def is_active(self) -> bool:
        return self.state not in TaskState.TERMINAL

    def log(self, message: str, level: str = "info", **extra: Any) -> None:
        self.events.append({
            "ts": time.time(), "level": level, "message": str(message)[:500], **extra,
        })
        if len(self.events) > 200:
            self.events = self.events[-200:]
        self.updated_at = time.time()

    def set_state(self, state: str, reason: str = "") -> None:
        self.state = state
        self.updated_at = time.time()
        if reason:
            self.blocked_reason = reason
        self.log(f"state -> {state}" + (f" ({reason})" if reason else ""))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "state": self.state,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_path": self.project_path,
            "context": self.context,
            "blocked_reason": self.blocked_reason,
            "pending_permission": self.pending_permission,
            "summary": self.summary,
            "events": self.events[-50:],
            "undo_stack": self.undo_stack,
            "progress": self.progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentTask":
        task = cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            goal=data.get("goal", ""),
            state=data.get("state", TaskState.CREATED),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            project_path=data.get("project_path"),
            context=dict(data.get("context") or {}),
            blocked_reason=data.get("blocked_reason", ""),
            pending_permission=data.get("pending_permission"),
            summary=data.get("summary", ""),
            events=list(data.get("events") or []),
            undo_stack=list(data.get("undo_stack") or []),
        )
        task.steps = [PlanStep.from_dict(s) for s in data.get("steps", [])]
        return task

    def status_line(self) -> str:
        """Short human-readable status for the UI."""
        if self.state == TaskState.COMPLETED:
            return f"Completed: {self.goal}"
        if self.state == TaskState.WAITING_FOR_USER:
            return f"Waiting for you: {self.blocked_reason or self.goal}"
        if self.state == TaskState.WAITING_FOR_PERMISSION:
            return f"Needs permission: {self.blocked_reason or self.goal}"
        step = self.current_step
        if step:
            return f"{self.goal} - step {step.index + 1}/{len(self.steps)}: {step.description}"
        return f"{self.goal} [{self.state}]"


class TaskManager:
    """Persistent store of agent tasks."""

    _instance: Optional["TaskManager"] = None
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
        self._tasks: Dict[str, AgentTask] = {}
        self._state_lock = threading.RLock()
        self._cancel_flags: Dict[str, threading.Event] = {}
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
        return base / "agent_tasks.json"

    def _load(self) -> None:
        try:
            if not self._store.exists():
                return
            data = json.loads(self._store.read_text(encoding="utf-8"))
            with self._state_lock:
                for item in data.get("tasks", []):
                    task = AgentTask.from_dict(item)
                    # A task interrupted mid-run by a restart is not
                    # actually running; mark it resumable instead.
                    if task.state in (TaskState.RUNNING, TaskState.VERIFYING,
                                      TaskState.PLANNING):
                        task.state = TaskState.BLOCKED
                        task.blocked_reason = "Interrupted when AVORA closed"
                    self._tasks[task.id] = task
        except Exception as exc:
            logger.warning("Task load failed: %s", exc)

    def save(self) -> None:
        try:
            with self._state_lock:
                tasks = sorted(self._tasks.values(), key=lambda t: t.updated_at, reverse=True)
                payload = {"tasks": [t.to_dict() for t in tasks[:100]]}
            tmp = self._store.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            tmp.replace(self._store)
        except Exception as exc:
            logger.warning("Task save failed: %s", exc)

    # -- CRUD ------------------------------------------------------

    def create(self, goal: str, project_path: Optional[str] = None, **context: Any) -> AgentTask:
        task = AgentTask(goal=goal, project_path=project_path, context=dict(context))
        task.log(f"Task created: {goal}")
        with self._state_lock:
            self._tasks[task.id] = task
            self._cancel_flags[task.id] = threading.Event()
        self.save()
        return task

    def get(self, task_id: str) -> Optional[AgentTask]:
        with self._state_lock:
            return self._tasks.get(task_id)

    def all(self, limit: int = 50) -> List[AgentTask]:
        with self._state_lock:
            tasks = sorted(self._tasks.values(), key=lambda t: t.updated_at, reverse=True)
        return tasks[:limit]

    def active(self) -> List[AgentTask]:
        return [t for t in self.all() if t.is_active]

    def latest_resumable(self) -> Optional[AgentTask]:
        """
        The task 'continue' should pick up.

        Most recently updated non-terminal task with unfinished steps.
        """
        for task in self.all():
            if task.state in TaskState.RESUMABLE and task.is_active:
                return task
        return None

    def latest(self) -> Optional[AgentTask]:
        tasks = self.all(limit=1)
        return tasks[0] if tasks else None

    def update(self, task: AgentTask) -> None:
        task.updated_at = time.time()
        with self._state_lock:
            self._tasks[task.id] = task
        self.save()

    def cancel(self, task_id: str) -> bool:
        with self._state_lock:
            task = self._tasks.get(task_id)
            flag = self._cancel_flags.get(task_id)
        if not task:
            return False
        if flag:
            flag.set()
        task.set_state(TaskState.CANCELLED, "Cancelled by user")
        self.update(task)
        return True

    def cancel_flag(self, task_id: str) -> threading.Event:
        with self._state_lock:
            if task_id not in self._cancel_flags:
                self._cancel_flags[task_id] = threading.Event()
            return self._cancel_flags[task_id]

    def is_cancelled(self, task_id: str) -> bool:
        return self.cancel_flag(task_id).is_set()

    def cleanup(self, older_than_days: float = 14) -> int:
        cutoff = time.time() - older_than_days * 86400
        with self._state_lock:
            stale = [
                tid for tid, t in self._tasks.items()
                if t.state in TaskState.TERMINAL and t.updated_at < cutoff
            ]
            for tid in stale:
                self._tasks.pop(tid, None)
                self._cancel_flags.pop(tid, None)
        if stale:
            self.save()
        return len(stale)


_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    global _manager
    if _manager is None:
        _manager = TaskManager()
    return _manager


__all__ = ["AgentTask", "PlanStep", "TaskState", "TaskManager", "get_task_manager"]
