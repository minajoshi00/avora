"""
===============================================================
                    AUTOMATION PERMISSIONS
===============================================================
Permission-based action system for AVORA automation.

Three-tier permission model:
  LEVEL 1 - Safe (Automatic)
    No confirmation required.
    Examples: open apps, read files, web search, weather, calendar
  
  LEVEL 2 - Confirm Once
    Ask once, then remember permission.
    Examples: close apps, move files, browser automation
  
  LEVEL 3 - Always Confirm
    Always require confirmation.
    Examples: delete files, system commands, install software

Features:
  - Persistent permission storage
  - Activity logging for all actions
  - Sensitive data redaction
  - Undo support for file operations
===============================================================
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from app_paths import APP_DATA_DIR
from avora_safety import (
    log_activity,
    get_activity_log,
    redact_sensitive,
    push_undo,
    is_command_safe,
)


# ============================================================
# PERMISSION LEVELS
# ============================================================

class PermissionLevel:
    SAFE = 1           # Automatic - no confirmation
    CONFIRM_ONCE = 2   # Ask once, remember choice
    ALWAYS_CONFIRM = 3 # Always require confirmation


# ============================================================
# ACTION CATEGORIES
# ============================================================

ACTION_CATEGORIES = {
    # LEVEL 1 - Safe (Automatic)
    "open_app": PermissionLevel.SAFE,
    "open_folder": PermissionLevel.SAFE,
    "search_files": PermissionLevel.SAFE,
    "read_file": PermissionLevel.SAFE,
    "read_clipboard": PermissionLevel.SAFE,
    "read_screen": PermissionLevel.SAFE,
    "check_weather": PermissionLevel.SAFE,
    "check_calendar": PermissionLevel.SAFE,
    "check_emails": PermissionLevel.SAFE,
    "create_reminder": PermissionLevel.SAFE,
    "web_search": PermissionLevel.SAFE,
    "list_folder": PermissionLevel.SAFE,
    "get_time": PermissionLevel.SAFE,
    "take_screenshot": PermissionLevel.SAFE,
    "ask_ai": PermissionLevel.SAFE,
    
    # LEVEL 2 - Confirm Once
    "close_app": PermissionLevel.CONFIRM_ONCE,
    "move_file": PermissionLevel.CONFIRM_ONCE,
    "rename_file": PermissionLevel.CONFIRM_ONCE,
    "download_file": PermissionLevel.CONFIRM_ONCE,
    "browser_automation": PermissionLevel.CONFIRM_ONCE,
    "type_text": PermissionLevel.CONFIRM_ONCE,
    "control_media": PermissionLevel.CONFIRM_ONCE,
    "create_file": PermissionLevel.CONFIRM_ONCE,
    "open_file": PermissionLevel.CONFIRM_ONCE,
    
    # LEVEL 3 - Always Confirm
    "delete_file": PermissionLevel.ALWAYS_CONFIRM,
    "format_drive": PermissionLevel.ALWAYS_CONFIRM,
    "registry_change": PermissionLevel.ALWAYS_CONFIRM,
    "run_powershell": PermissionLevel.ALWAYS_CONFIRM,
    "run_cmd": PermissionLevel.ALWAYS_CONFIRM,
    "install_software": PermissionLevel.ALWAYS_CONFIRM,
    "uninstall_software": PermissionLevel.ALWAYS_CONFIRM,
    "system_settings": PermissionLevel.ALWAYS_CONFIRM,
    "shutdown": PermissionLevel.ALWAYS_CONFIRM,
    "restart": PermissionLevel.ALWAYS_CONFIRM,
}


# ============================================================
# PERMISSION MANAGER
# ============================================================

class AutomationPermissionManager:
    """Manages automation permissions with persistence."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._permissions_file = APP_DATA_DIR / "automation_permissions.json"
        self._permissions: Dict[str, Dict[str, Any]] = {}
        self._load_permissions()
    
    def _load_permissions(self):
        """Load saved permissions from disk."""
        try:
            if self._permissions_file.exists():
                with open(self._permissions_file, "r", encoding="utf-8") as f:
                    self._permissions = json.load(f)
        except Exception:
            self._permissions = {}
    
    def _save_permissions(self):
        """Save permissions to disk."""
        try:
            self._permissions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._permissions_file, "w", encoding="utf-8") as f:
                json.dump(self._permissions, f, indent=2)
        except Exception as e:
            print(f"[PERMISSION] Save error: {e}")
    
    def get_permission_level(self, action: str) -> int:
        """Get permission level for an action (1, 2, or 3)."""
        action_lower = action.lower().strip()
        
        # Check if user has explicitly allowed/denied this action
        if action_lower in self._permissions:
            entry = self._permissions[action_lower]
            if entry.get("allowed", False):
                return PermissionLevel.SAFE  # Treat as safe if previously allowed
            else:
                return PermissionLevel.ALWAYS_CONFIRM  # Denied = always confirm
        
        # Check category defaults
        return ACTION_CATEGORIES.get(action_lower, PermissionLevel.ALWAYS_CONFIRM)
    
    def request_permission(
        self,
        action: str,
        details: str = ""
    ) -> tuple[bool, str]:
        """
        Request permission for an action.
        Returns (allowed: bool, reason: str)
        """
        action_lower = action.lower().strip()
        level = self.get_permission_level(action_lower)
        
        # Log the request
        log_activity(
            "PERMISSION_REQUEST",
            f"{action}: {details}",
            level="info",
            category="automation",
        )
        
        if level == PermissionLevel.SAFE:
            # Automatic - no confirmation needed
            return True, "Automatic (safe action)"
        
        elif level == PermissionLevel.CONFIRM_ONCE:
            # Check if we've asked before
            if action_lower in self._permissions:
                entry = self._permissions[action_lower]
                if entry.get("allowed", False):
                    return True, "Previously allowed"
                else:
                    return False, "Previously denied"
            
            # Need to ask user - return special flag
            return None, "Requires confirmation (Level 2)"
        
        else:  # ALWAYS_CONFIRM
            # Always ask
            return None, "Requires confirmation (Level 3)"
    
    def grant_permission(self, action: str, remember: bool = False):
        """
        Grant permission for an action.
        
        Args:
            action: The action to grant permission for
            remember: If True, save this choice for future (Level 2 only)
        """
        action_lower = action.lower().strip()
        
        with self._lock:
            if remember:
                self._permissions[action_lower] = {
                    "allowed": True,
                    "granted_at": datetime.now().isoformat(timespec="seconds"),
                }
                self._save_permissions()
        
        log_activity(
            "PERMISSION_GRANTED",
            f"{action} (remember={remember})",
            level="info",
            category="automation",
        )
    
    def deny_permission(self, action: str, remember: bool = False):
        """
        Deny permission for an action.
        
        Args:
            action: The action to deny permission for
            remember: If True, save this choice for future (Level 2 only)
        """
        action_lower = action.lower().strip()
        
        with self._lock:
            if remember:
                self._permissions[action_lower] = {
                    "allowed": False,
                    "denied_at": datetime.now().isoformat(timespec="seconds"),
                }
                self._save_permissions()
        
        log_activity(
            "PERMISSION_DENIED",
            f"{action} (remember={remember})",
            level="warning",
            category="automation",
        )
    
    def is_permission_granted(self, action: str) -> bool:
        """Check if permission has been explicitly granted."""
        action_lower = action.lower().strip()
        if action_lower in self._permissions:
            return self._permissions[action_lower].get("allowed", False)
        return False
    
    def get_permission_summary(self) -> Dict[str, Any]:
        """Get summary of permission state."""
        with self._lock:
            return {
                "total_saved": len(self._permissions),
                "granted": sum(1 for p in self._permissions.values() if p.get("allowed")),
                "denied": sum(1 for p in self._permissions.values() if not p.get("allowed")),
                "permissions": dict(self._permissions),
            }
    
    def clear_permissions(self):
        """Clear all saved permissions."""
        with self._lock:
            self._permissions.clear()
            self._save_permissions()
        
        log_activity(
            "PERMISSIONS_CLEARED",
            "All saved permissions cleared",
            level="info",
            category="automation",
        )


# ============================================================
# GLOBAL PERMISSION MANAGER
# ============================================================

_permission_manager = AutomationPermissionManager()


def get_permission_manager() -> AutomationPermissionManager:
    """Get the global permission manager."""
    return _permission_manager


# ============================================================
# ACTIVITY LOGGER
# ============================================================

class ActivityLogger:
    """Enhanced activity logging for automation."""
    
    def __init__(self):
        self._lock = threading.RLock()
    
    def log_action(
        self,
        category: str,
        action: str,
        details: str = "",
        level: str = "info",
    ):
        """Log an automation action."""
        # Redact sensitive information
        safe_details = redact_sensitive(details)
        safe_action = redact_sensitive(action)
        
        log_activity(
            action=safe_action,
            detail=safe_details,
            level=level,
            category=category,
        )
    
    def get_recent_actions(self, limit: int = 20) -> list[dict]:
        """Get recent automation actions."""
        entries = get_activity_log(limit=limit)
        # Filter for automation-related entries
        return [
            e for e in entries
            if e.get("category") in ("automation", "AUTOMATION", "PERMISSION_REQUEST", "PERMISSION_GRANTED", "PERMISSION_DENIED")
        ]
    
    def format_action_log(self, limit: int = 10) -> str:
        """Format action log for display."""
        actions = self.get_recent_actions(limit=limit)
        
        if not actions:
            return "No recent actions."
        
        lines = []
        for entry in actions:
            timestamp = entry.get("timestamp", "")
            action = entry.get("action", "")
            detail = entry.get("detail", "")
            level = entry.get("level", "info")
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = timestamp
            
            # Format level indicator
            if level == "error":
                indicator = "❌"
            elif level == "warning":
                indicator = "⚠️"
            else:
                indicator = "✓"
            
            lines.append(f"{indicator} [{time_str}] {action}")
            if detail and detail != action:
                lines.append(f"   └─ {detail}")
        
        return "\n".join(lines)


# ============================================================
# GLOBAL LOGGER
# ============================================================

_activity_logger = ActivityLogger()


def get_activity_logger() -> ActivityLogger:
    """Get the global activity logger."""
    return _activity_logger


# ============================================================
# CONFIRMATION DIALOG HELPER
# ============================================================

def format_permission_message(action: str, details: str, level: int) -> str:
    """Format a permission request message for the user."""
    if level == PermissionLevel.CONFIRM_ONCE:
        title = "Allow AVORA to perform this action?"
        message = f"Action: {action}\nDetails: {details}\n\n"
        message += "This action requires confirmation. Allow once, or allow and remember for future?"
    else:  # ALWAYS_CONFIRM
        title = "Confirm Action Required"
        message = f"⚠️  Action: {action}\nDetails: {details}\n\n"
        message += "This action requires explicit confirmation every time.\n\n"
        message += "Do you want to proceed?"
    
    return title, message
