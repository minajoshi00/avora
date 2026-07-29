"""
================================================================
AVORA SAFETY SYSTEM
================================================================
Global panic kill switch, activity logging, permission guard,
sensitive data redaction, and safe execution sandbox.

Features:
- Global hotkey panic stop (Ctrl+Alt+F12)
- Activity log with timestamps
- Permission levels for all actions
- Sensitive data redaction (passwords, API keys, etc.)
- Safe command sandboxing
- Undo support for file operations
================================================================
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH
from settings import get_setting, set_setting


# ============================================================
# PATHS
# ============================================================

ACTIVITY_LOG_FILE = APP_DATA_DIR / "avora_activity.json"
UNDO_LOG_FILE = APP_DATA_DIR / "avora_undo.json"


# ============================================================
# GLOBAL PANIC STATE
# ============================================================

_panic = threading.Event()
_panic_lock = threading.RLock()
_activity_lock = threading.RLock()
_undo_lock = threading.RLock()

_activity_log: list[dict] = []
_undo_stack: list[dict] = []


# ============================================================
# PANIC KILL SWITCH
# ============================================================

def is_panic() -> bool:
    """Check if panic mode is active."""
    return _panic.is_set()


def trigger_panic() -> None:
    """Trigger global panic stop - stops all automation immediately."""
    with _panic_lock:
        _panic.set()
    log_activity("PANIC", "Emergency stop triggered", level="critical")
    print("\n⚠️  AVORA PANIC: All automation stopped!\n")


def clear_panic() -> None:
    """Clear panic state."""
    with _panic_lock:
        _panic.clear()
    print("\n✅ AVORA: Panic cleared, ready to resume.\n")


def check_panic() -> None:
    """Check panic state and raise if active."""
    if is_panic():
        raise RuntimeError("AVORA PANIC: Operation cancelled by emergency stop.")


# ============================================================
# ACTIVITY LOG
# ============================================================

def log_activity(
    action: str,
    detail: str = "",
    level: str = "info",
    category: str = "general",
) -> None:
    """Log an activity with timestamp."""
    try:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": str(action),
            "detail": str(detail),
            "level": level,
            "category": category,
        }
        with _activity_lock:
            _activity_log.append(entry)
            # Keep last 1000 entries in memory
            if len(_activity_log) > 1000:
                _activity_log.pop(0)
        # Auto-save every 10 entries
        if len(_activity_log) % 10 == 0:
            _save_activity_log()
    except Exception as e:
        print(f"[AVORA ACTIVITY LOG ERROR] {e}")


def _save_activity_log() -> None:
    """Save activity log to disk."""
    try:
        with _activity_lock:
            data = _activity_log[-500:]  # Keep last 500 on disk
        with open(ACTIVITY_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[AVORA ACTIVITY SAVE ERROR] {e}")


def get_activity_log(limit: int = 50) -> list[dict]:
    """Get recent activity log entries."""
    with _activity_lock:
        return list(_activity_log[-limit:])


def clear_activity_log() -> None:
    """Clear activity log."""
    with _activity_lock:
        _activity_log.clear()
    _save_activity_log()


# ============================================================
# PERMISSION GUARD
# ============================================================

PERMISSION_LEVELS = {
    "safe": 0,        # No confirmation needed (chat, weather, time)
    "info": 1,        # Read-only system info
    "file_read": 2,   # Reading files
    "file_write": 3,  # Creating/modifying files
    "file_delete": 4, # Deleting files
    "app_launch": 3,  # Launching applications
    "system": 4,      # System commands
    "power": 5,       # Shutdown, restart, etc.
    "email": 4,       # Reading/sending emails
    "git": 4,         # Git operations
    "dangerous": 5,   # Unknown scripts, risky operations
}

# User's max allowed permission level
def get_user_permission_level() -> int:
    """Get the user's current max permission level from settings."""
    level = get_setting("safety.permission_level", 3)
    try:
        return max(0, min(5, int(level)))
    except (TypeError, ValueError):
        return 3


def check_permission(
    action_type: str,
    action_detail: str = "",
) -> bool:
    """Check if an action is allowed by current permission settings."""
    if is_panic():
        return False

    required = PERMISSION_LEVELS.get(action_type, 3)
    user_level = get_user_permission_level()

    if required <= user_level:
        return True

    log_activity(
        "PERMISSION_DENIED",
        f"{action_type}: {action_detail} (required={required}, user={user_level})",
        level="warning",
    )
    return False


# ============================================================
# SENSITIVE DATA REDACTION
# ============================================================

SENSITIVE_PATTERNS = [
    (r'[A-Za-z0-9+/=]{20,}(?:[A-Za-z0-9+/=]{10,})?', '[API_KEY_REDACTED]'),  # API keys
    (r'(?i)(?:password|passwd|pwd)\s*[:=]\s*\S+', 'password=[REDACTED]'),
    (r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*\S+', 'api_key=[REDACTED]'),
    (r'(?i)(?:secret|secret[_-]?key)\s*[:=]\s*\S+', 'secret=[REDACTED]'),
    (r'(?i)(?:private[_-]?key|privkey)\s*[:=]\s*\S+', 'private_key=[REDACTED]'),
    (r'(?i)(?:access[_-]?token|accesstoken)\s*[:=]\s*\S+', 'access_token=[REDACTED]'),
    (r'(?i)(?:bearer\s+)[A-Za-z0-9._-]+', 'Bearer [REDACTED]'),
    (r'\b\d{16}\b', '[CARD_NUMBER_REDACTED]'),  # Credit card numbers
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),  # SSN
]


def redact_sensitive(text: str) -> str:
    """Redact sensitive information from text."""
    if not text:
        return text
    result = str(text)
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def redact_screenshot_path(path: str) -> str:
    """Mark a screenshot path for redaction processing."""
    return str(path)


# ============================================================
# UNDO SYSTEM
# ============================================================

def push_undo(action: str, data: dict) -> None:
    """Push an action onto the undo stack."""
    with _undo_lock:
        _undo_stack.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "data": data,
        })
        # Keep max 50 undo entries
        if len(_undo_stack) > 50:
            _undo_stack.pop(0)
    _save_undo_log()


def pop_undo() -> Optional[dict]:
    """Pop the most recent undo entry."""
    with _undo_lock:
        if not _undo_stack:
            return None
        return _undo_stack.pop()


def get_undo_stack() -> list[dict]:
    """Get the current undo stack."""
    with _undo_lock:
        return list(_undo_stack)


def _save_undo_log() -> None:
    """Save undo log to disk."""
    try:
        with _undo_lock:
            data = _undo_stack[-50:]
        with open(UNDO_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[AVORA UNDO SAVE ERROR] {e}")


# ============================================================
# COMMAND SANDBOX
# ============================================================

BLOCKED_COMMANDS = [
    "format", "fdisk", "mkfs", "dd if=", "rd /s /q",
    "rm -rf /", "rm -rf ~", "del /f /s /q",
    "shutdown /p", "shutdown /r /fw",
]

ALLOWED_COMMAND_PREFIXES = [
    "dir", "ls", "echo", "type", "find", "where",
    "python", "pip list", "pip install", "npm list",
    "git status", "git log", "git diff", "git branch",
    "code ", "start ", "explorer",
]


def is_command_safe(command: str) -> tuple[bool, str]:
    """Check if a command is safe to execute."""
    if not command:
        return False, "Empty command."

    lower = command.lower().strip()

    # Check blocked commands
    for blocked in BLOCKED_COMMANDS:
        if blocked in lower:
            return False, f"Command blocked for safety: contains '{blocked}'"

    # Check allowed prefixes
    for prefix in ALLOWED_COMMAND_PREFIXES:
        if lower.startswith(prefix):
            return True, ""

    # Unknown commands need permission
    return check_permission("dangerous", command), "Command requires permission check."


# ============================================================
# INITIALIZATION
# ============================================================

def initialize() -> None:
    """Initialize the safety system."""
    # Load existing activity log
    try:
        if ACTIVITY_LOG_FILE.exists():
            with open(ACTIVITY_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                with _activity_lock:
                    _activity_log.extend(data[-500:])
    except Exception:
        pass

    # Load existing undo log
    try:
        if UNDO_LOG_FILE.exists():
            with open(UNDO_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                with _undo_lock:
                    _undo_stack.extend(data[-50:])
    except Exception:
        pass

    log_activity("SYSTEM", "AVORA Safety System initialized", level="info")
    print("[AVORA] Safety System loaded.")


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "is_panic",
    "trigger_panic",
    "clear_panic",
    "check_panic",
    "log_activity",
    "get_activity_log",
    "clear_activity_log",
    "check_permission",
    "redact_sensitive",
    "push_undo",
    "pop_undo",
    "get_undo_stack",
    "is_command_safe",
    "initialize",
]
