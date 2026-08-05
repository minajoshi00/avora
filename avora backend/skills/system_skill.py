"""
============================================================
AVORA System Skill
============================================================

Handles system-level operations:
- Settings
- Power actions
- System information
"""

import os
import platform
import subprocess
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from skills.skill_base import BaseSkill, register_skill

logger = logging.getLogger("SystemSkill")


class SystemSkill(BaseSkill):
    """Skill for system-level operations."""
    
    def __init__(self):
        super().__init__(
            name="system_skill",
            description="System settings and power management"
        )
        self._is_windows = os.name == "nt"
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool:
        """Can handle system-related intents."""
        from core.intelligence_engine import IntentType
        return intent in [
            IntentType.POWER_ACTION,
            IntentType.OPEN_APP,
        ]
    
    def plan(self, intent: str, params: Dict[str, Any], 
             context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create plan for system operations."""
        target = params.get("target", "")
        entities = params.get("entities", {})
        
        if not target:
            return None
        
        plan = {
            "skill": "system_skill",
            "action": "execute",
            "intent": intent,
            "target": target,
            "context": context,
            "steps": []
        }
        
        if "shutdown" in target.lower():
            plan["steps"].append({"type": "power", "action": "shutdown"})
        elif "restart" in target.lower():
            plan["steps"].append({"type": "power", "action": "restart"})
        elif "sleep" in target.lower():
            plan["steps"].append({"type": "power", "action": "sleep"})
        elif "lock" in target.lower():
            plan["steps"].append({"type": "power", "action": "lock"})
        elif "settings" in target.lower():
            plan["steps"].append({"type": "settings", "action": "open"})
        else:
            plan["steps"].append({"type": "general", "target": target})
        
        return plan
    
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system action from plan."""
        steps = plan.get("steps", [])
        results = []
        
        for step in steps:
            step_type = step.get("type")
            
            if step_type == "power":
                result = self._execute_power(step.get("action"))
            elif step_type == "settings":
                result = self._open_settings()
            else:
                result = {
                    "success": False,
                    "message": f"Unknown system action: {step_type}"
                }
            
            results.append(result)
        
        if results:
            last = results[-1]
            if last.get("success"):
                return {
                    "success": True,
                    "message": last.get("message", "Action completed"),
                    "results": results
                }
        
        return {
            "success": False,
            "message": "Failed to execute system action",
            "results": results
        }
    
    def _execute_power(self, action: str) -> Dict[str, Any]:
        """Execute power action."""
        try:
            if action == "shutdown":
                if self._is_windows:
                    subprocess.run(["shutdown", "/s", "/t", "5"], check=False)
                return {"success": True, "message": "Shutting down in 5 seconds"}
            elif action == "restart":
                if self._is_windows:
                    subprocess.run(["shutdown", "/r", "/t", "5"], check=False)
                return {"success": True, "message": "Restarting in 5 seconds"}
            elif action == "sleep":
                if self._is_windows:
                    subprocess.run(["rundll32.exe", "powrprof.dll", "SetSuspendState", "0", "1", "0"], check=False)
                return {"success": True, "message": "Putting computer to sleep"}
            elif action == "lock":
                if self._is_windows:
                    subprocess.run(["rundll32.exe", "user32.dll", "LockWorkStation"], check=False)
                return {"success": True, "message": "Locking computer"}
            
            return {"success": False, "message": f"Unknown power action: {action}"}
            
        except Exception as e:
            logger.error(f"Power action failed: {e}")
            return {"success": False, "message": f"Failed: {e}"}
    
    def _open_settings(self) -> Dict[str, Any]:
        """Open Windows Settings."""
        try:
            if self._is_windows:
                subprocess.Popen(
                    ["start", "", "ms-settings:"],
                    shell=True
                )
                return {"success": True, "message": "Opening Settings"}
            
            return {"success": False, "message": "Settings not available on this platform"}
            
        except Exception as e:
            logger.error(f"Failed to open settings: {e}")
            return {"success": False, "message": f"Failed to open settings: {e}"}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        info = {
            "platform": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
        
        if self._is_windows:
            try:
                info["os_version"] = platform.win32_ver()[1]
            except:
                pass
        
        return info


skill = SystemSkill()
register_skill("system_skill", skill)

__all__ = ["SystemSkill", "skill"]