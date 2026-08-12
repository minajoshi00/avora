"""
============================================================
AVORA Launch History
============================================================

Tracks application launch history for analytics and ranking.
"""

import json
import time
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

from app_paths import APP_DATA_DIR

logger = logging.getLogger("LaunchHistory")

_HISTORY_FILE = APP_DATA_DIR / "launch_history.json"
_history_lock = threading.RLock()
_history: List[Dict[str, Any]] = []


def _load_history():
    global _history
    try:
        if _HISTORY_FILE.exists():
            with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
                _history = json.load(f)
    except Exception:
        _history = []


def _save_history():
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_history, f, indent=2, default=str)
    except Exception as e:
        logger.debug(f"History save error: {e}")


def record_launch(app_name: str, app_path: str, success: bool = True, error_message: Optional[str] = None):
    """Record an application launch."""
    with _history_lock:
        _history.append({
            "app_name": app_name,
            "app_path": app_path,
            "timestamp": time.time(),
            "success": success,
            "error_message": error_message,
        })
        _save_history()


def get_recent_launches(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent launch history."""
    with _history_lock:
        return list(reversed(_history[-limit:]))


def get_launch_count(app_name: str) -> int:
    """Get the number of times an app was launched."""
    with _history_lock:
        return sum(1 for entry in _history if entry.get("app_name") == app_name)


class LaunchHistory:
    """Launch history manager."""

    def __init__(self):
        _load_history()

    def record(self, app_name: str, app_path: str, success: bool = True, error_message: Optional[str] = None):
        record_launch(app_name, app_path, success, error_message)

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return get_recent_launches(limit)

    def get_count(self, app_name: str) -> int:
        return get_launch_count(app_name)


_instance = None


def get_launch_history() -> LaunchHistory:
    """Get the singleton launch history."""
    global _instance
    if _instance is None:
        _instance = LaunchHistory()
    return _instance


__all__ = ["LaunchHistory", "get_launch_history", "record_launch", "get_recent_launches", "get_launch_count"]
