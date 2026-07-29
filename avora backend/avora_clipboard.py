"""
================================================================
AVORA CLIPBOARD MANAGER
================================================================
Searchable clipboard history with privacy controls and
sensitive-data exclusions.

Features:
- Captures text, links, code, and images from clipboard
- Searchable history (by content, type, date)
- Privacy controls (exclude sensitive data)
- Configurable history size
- Image preview support
- Low-resource: polls clipboard at configurable intervals
================================================================
"""

from __future__ import annotations

import os
import re
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH
from settings import get_setting
from avora_safety import redact_sensitive


# ============================================================
# PATHS
# ============================================================

CLIPBOARD_FILE = APP_DATA_DIR / "avora_clipboard.json"


# ============================================================
# STATE
# ============================================================

_history: list[dict] = []
_history_lock = threading.RLock()
_last_clipboard_text: str = ""
_clipboard_thread: Optional[threading.Thread] = None
_running = False


# ============================================================
# SENSITIVE DATA DETECTION
# ============================================================

SENSITIVE_PATTERNS = [
    r'(?i)(?:password|passwd|pwd)\s*[:=]\s*\S+',
    r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*\S+',
    r'(?i)(?:secret|secret[_-]?key)\s*[:=]\s*\S+',
    r'(?i)(?:private[_-]?key|privkey)\s*[:=]\s*\S+',
    r'(?i)(?:access[_-]?token|accesstoken)\s*[:=]\s*\S+',
    r'(?i)(?:bearer\s+)[A-Za-z0-9._-]+',
    r'\b\d{16}\b',  # Credit card numbers
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
]


def _is_sensitive(text: str) -> bool:
    """Check if clipboard content contains sensitive data."""
    if not text:
        return False
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


# ============================================================
# CLIPBOARD TYPE DETECTION
# ============================================================

def _detect_type(text: str) -> str:
    """Detect the type of clipboard content."""
    if not text:
        return "empty"

    # URL
    if re.match(r'^https?://', text.strip()):
        return "link"

    # Code (has code-like patterns)
    code_indicators = [
        'def ', 'function ', 'class ', 'import ',
        'var ', 'let ', 'const ', 'if (', 'for (',
        '<html', '<div', 'SELECT ', 'INSERT ',
        'public ', 'private ', 'function(',
    ]
    if any(ind in text for ind in code_indicators):
        return "code"

    # Long text
    if len(text) > 200:
        return "text"

    # Short text
    return "text"


# ============================================================
# HISTORY MANAGEMENT
# ============================================================

def _max_history() -> int:
    try:
        return max(1, int(get_setting("clipboard.max_history", 100)))
    except (TypeError, ValueError):
        return 100


def _save_to_disk() -> None:
    """Save clipboard history to disk."""
    try:
        with _history_lock:
            data = _history[-_max_history():]
        with open(CLIPBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[AVORA CLIPBOARD SAVE ERROR] {e}")


def _load_from_disk() -> None:
    """Load clipboard history from disk."""
    try:
        if CLIPBOARD_FILE.exists():
            with open(CLIPBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    with _history_lock:
                        _history.extend(data[-_max_history():])
    except Exception:
        pass


def add_entry(text: str, content_type: str = None) -> bool:
    """Add a new entry to clipboard history."""
    if not text:
        return False

    # Check privacy settings
    if get_setting("clipboard.exclude_sensitive", True):
        if _is_sensitive(text):
            return False

    # Check type settings
    if content_type is None:
        content_type = _detect_type(text)

    if content_type == "image" and not get_setting("clipboard.save_images", True):
        return False
    if content_type == "link" and not get_setting("clipboard.save_links", True):
        return False
    if content_type == "code" and not get_setting("clipboard.save_code", True):
        return False

    # Prevent duplicates
    with _history_lock:
        if _history and _history[-1].get("content") == text:
            return False

        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "content": text,
            "type": content_type,
            "preview": text[:200] + ("..." if len(text) > 200 else ""),
        }
        _history.append(entry)

        # Trim to max
        while len(_history) > _max_history():
            _history.pop(0)

    _save_to_disk()
    return True


def get_history(limit: int = 50) -> list[dict]:
    """Get clipboard history entries."""
    with _history_lock:
        return list(_history[-limit:])


def search_history(query: str, limit: int = 20) -> list[dict]:
    """Search clipboard history by content."""
    if not query:
        return get_history(limit)

    query_lower = query.lower().strip()
    results = []

    with _history_lock:
        for entry in reversed(_history):
            content = entry.get("content", "").lower()
            if query_lower in content:
                results.append(entry)
                if len(results) >= limit:
                    break

    return results


def delete_entry(index: int) -> bool:
    """Delete an entry from history by index."""
    with _history_lock:
        if 0 <= index < len(_history):
            _history.pop(index)
            _save_to_disk()
            return True
    return False


def clear_history() -> bool:
    """Clear all clipboard history."""
    with _history_lock:
        _history.clear()
    _save_to_disk()
    return True


def get_stats() -> dict:
    """Get clipboard statistics."""
    with _history_lock:
        total = len(_history)
        types = {}
        for entry in _history:
            t = entry.get("type", "unknown")
            types[t] = types.get(t, 0) + 1

    return {
        "total_entries": total,
        "by_type": types,
        "max_history": _max_history(),
    }


# ============================================================
# CLIPBOARD POLLING
# ============================================================

def _get_clipboard_text() -> Optional[str]:
    """Get text from system clipboard."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            text = root.clipboard_get()
            return text if text else None
        finally:
            root.destroy()
    except Exception:
        return None


def _clipboard_poll_loop() -> None:
    """Background thread that polls the clipboard."""
    global _last_clipboard_text

    while _running:
        try:
            if not get_setting("clipboard.enabled", True):
                time.sleep(1)
                continue

            text = _get_clipboard_text()

            if text and text != _last_clipboard_text:
                _last_clipboard_text = text
                add_entry(text)

        except Exception:
            pass

        # Poll interval: 0.5 seconds for responsiveness, low CPU
        time.sleep(0.5)


def start_clipboard_monitor() -> bool:
    """Start the clipboard monitoring thread."""
    global _clipboard_thread, _running

    if _running:
        return True

    _running = True
    _clipboard_thread = threading.Thread(
        target=_clipboard_poll_loop,
        daemon=True,
        name="AvoraClipboardMonitor",
    )
    _clipboard_thread.start()
    return True


def stop_clipboard_monitor() -> None:
    """Stop the clipboard monitoring thread."""
    global _running, _clipboard_thread

    _running = False
    _clipboard_thread = None


# ============================================================
# INITIALIZATION
# ============================================================

def initialize() -> None:
    """Initialize the clipboard manager."""
    _load_from_disk()

    if get_setting("clipboard.enabled", True):
        start_clipboard_monitor()

    print("[AVORA] Clipboard Manager loaded.")


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "add_entry",
    "get_history",
    "search_history",
    "delete_entry",
    "clear_history",
    "get_stats",
    "start_clipboard_monitor",
    "stop_clipboard_monitor",
    "initialize",
]
