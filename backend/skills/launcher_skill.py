"""
============================================================
AVORA Launcher Skill
============================================================

Application launching skill with intelligent discovery
and ranking. Handles opening apps, files, folders,
and desktop shortcuts.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from skills.skill_base import BaseSkill, register_skill
from launcher_engine import get_launcher_engine

logger = logging.getLogger("LauncherSkill")


class LauncherSkill(BaseSkill):
    """Skill for launching applications, files, and folders."""
    
    def __init__(self):
        super().__init__(
            name="launcher_skill",
            description="Open applications, files, and folders on your computer"
        )
        self._launcher = get_launcher_engine()
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool:
        """Can handle app, file, folder, and game launch intents."""
        from core.intelligence_engine import IntentType
        
        return intent in [
            IntentType.OPEN_APP.value,
            IntentType.OPEN_FILE.value,
            IntentType.OPEN_FOLDER.value,
            IntentType.LAUNCH_GAME.value,
        ]
    
    def plan(self, intent: str, params: Dict[str, Any], 
             context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a plan to launch the requested item."""
        from core.intelligence_engine import IntentType
        
        target = params.get("target", "")
        if not target:
            return None
        
        plan = {
            "skill": "launcher_skill",
            "action": "launch",
            "intent": intent,
            "target": target,
            "context": context,
            "steps": [],
        }
        
        if intent == IntentType.OPEN_APP:
            plan["steps"].append({
                "type": "find_app",
                "query": target,
            })
            plan["steps"].append({
                "type": "launch_app",
                "target": target,
            })
        elif intent == IntentType.OPEN_FILE:
            plan["steps"].append({
                "type": "find_file",
                "path": target,
            })
            plan["steps"].append({
                "type": "launch_file",
                "path": target,
            })
        elif intent == IntentType.OPEN_FOLDER:
            plan["steps"].append({
                "type": "open_folder",
                "path": target,
            })
        elif intent == IntentType.LAUNCH_GAME:
            plan["steps"].append({
                "type": "find_game",
                "query": target,
            })
            plan["steps"].append({
                "type": "launch_game",
                "target": target,
            })
        
        return plan
    
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the launch plan."""
        intent = plan.get("intent", "")
        target = plan.get("target", "")
        context = plan.get("context", {})
        
        if intent == "open_app" or (hasattr(self, '_intent_enum') and 
                                      intent.value == "open_app"):
            return self._launch_application(target)
        elif intent == "open_file":
            return self._launch_file(target)
        elif intent == "open_folder":
            return self._open_folder(target)
        elif intent == "launch_game":
            return self._launch_game(target)
        else:
            return {
                "success": False,
                "message": f"Cannot launch {intent}",
                "error": "Unsupported intent",
            }
    
    def _launch_application(self, app_name: str) -> Dict[str, Any]:
        """Launch an application by name."""
        try:
            results = self._launcher.search_apps(app_name, limit=10)
            
            if not results:
                return {
                    "success": False,
                    "message": f"I couldn't find '{app_name}' on your computer.",
                    "target": app_name,
                }
            
            if len(results) == 1:
                result = results[0]
                path = result["path"]
                
                if not Path(path).exists():
                    return {
                        "success": False,
                        "message": f"I couldn't find '{app_name}' - the file was moved or deleted.",
                        "target": app_name,
                    }
                
                if self._launcher.launch_app(path):
                    return {
                        "success": True,
                        "message": f"🚀 Opening {Path(path).stem}, brooo.",
                        "target": app_name,
                        "path": str(path),
                    }
                else:
                    return {
                        "success": False,
                        "message": f"😕 I had trouble launching {app_name}.",
                        "target": app_name,
                    }
            
            else:
                display_names = [Path(r["path"]).stem for r in results[:3]]
                formatted = "\n".join(f"{i+1}. {n}" for i, n in enumerate(display_names))
                
                return {
                    "success": True,
                    "needs_choice": True,
                    "message": f"🤔 I found multiple {app_name}s:\n{formatted}\nWhich one should I open?",
                    "matches": results,
                    "query": app_name,
                }
                
        except Exception as e:
            logger.error(f"Launch error: {e}")
            return {
                "success": False,
                "message": f"❌ Error launching {app_name}: {e}",
            }
    
    def _launch_file(self, file_path: str) -> Dict[str, Any]:
        """Launch a file with its default application."""
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "message": f"File not found: {file_path}",
            }
        
        try:
            if os.name == 'nt':
                os.startfile(str(path))
            else:
                import subprocess
                subprocess.run(["open", str(path)], check=False)
            
            return {
                "success": True,
                "message": f"🚀 Opening {path.name}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error opening file: {e}",
            }
    
    def _open_folder(self, folder_path: str) -> Dict[str, Any]:
        """Open a folder in the file explorer."""
        path = Path(folder_path)
        
        if not path.exists():
            return {
                "success": False,
                "message": f"Folder not found: {folder_path}",
            }
        
        try:
            import subprocess
            if os.name == 'nt':
                subprocess.run(["explorer", str(path)], check=False, shell=False)
            else:
                subprocess.run(["open", str(path)], check=False)
            
            return {
                "success": True,
                "message": f"📁 Opening folder: {path}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error opening folder: {e}",
            }
    
    def _launch_game(self, game_name: str) -> Dict[str, Any]:
        """Launch a game."""
        return self._launch_application(game_name)


skill = LauncherSkill()
register_skill("launcher_skill", skill)

__all__ = ["LauncherSkill", "skill"]