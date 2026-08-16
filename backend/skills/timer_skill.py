""" 
============================================================ 
AVORA Timer Skill 
============================================================ 

Handles timer creation for AI Friend. 

Features: 
    â€���¢ Create timers with specified duration and text 
    â€���¢ Supports seconds, minutes, and hours 
    â€���¢ Integrates with existing reminder system 

""" 

from __future__ import annotations 

import logging 
from typing import Dict, Any, Optional 

from skills.skill_base import BaseSkill, register_skill 
from reminders import create_timer 

logger = logging.getLogger("TimerSkill") 


class TimerSkill(BaseSkill): 
    """Skill for creating timers.""" 
    
    def __init__(self): 
        super().__init__( 
            name="timer_skill", 
            description="Creates timers" 
        ) 
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool: 
        """Can handle set_timer intents.""" 
        from core.intelligence_engine import IntentType 
        return intent == IntentType.SET_TIMER 
    
    def plan(self, intent: str, params: Dict[str, Any], 
             context: Dict[str, Any]) -> Optional[Dict[str, Any]]: 
        """Create a plan to set a timer.""" 
        target = params.get("target", "") 
        if not target: 
            return None 
        
        return { 
            "skill": "timer_skill", 
            "action": "set_timer", 
            "target": target, 
            "context": context, 
        } 
    
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]: 
        """Execute the timer plan.""" 
        target = plan.get("target", "") 
        entities = plan.get("entities", {}) 
        if not target: 
            return { 
                "success": False, 
                "message": "No time specified", 
            } 
        
        try: 
            # Extract the number and unit from entities 
            # regex_group_2 is the number, regex_group_3 is the unit 
            number_str = entities.get("regex_group_2", "") 
            unit = entities.get("regex_group_3", "").lower() 
            
            if not number_str: 
                return { 
                    "success": False, 
                    "message": "Invalid time specification", 
                } 
            
            number = float(number_str) 
            # Convert to minutes 
            if unit.startswith("second"): 
                minutes = number / 60.0 
            elif unit.startswith("minute"): 
                minutes = number 
            elif unit.startswith("hour"): 
                minutes = number * 60.0 
            else: 
                return { 
                    "success": False, 
                    "message": f"Unsupported time unit: {unit}", 
                } 
            
            # The target is the number, but we want to use the original text for the timer? 
            # The reminders.create_timer expects a text and minutes. 
            # We don't have the original text, so we'll use a default. 
            # Alternatively, we could use the target as the text? But the target is the number. 
            # Let's use a default text like "Timer". 
            text = "Timer" 
            result = create_timer(text, int(minutes)) 
            
            return { 
                "success": True, 
                "message": result, 
            } 
        except ValueError as e: 
            logger.error(f"Timer value error: {e}") 
            return { 
                "success": False, 
                "message": f"Invalid time value: {str(e)}", 
            } 
        except Exception as e: 
            logger.error(f"Timer error: {e}") 
            return { 
                "success": False, 
                "message": f"Failed to create timer: {str(e)}", 
            } 


skill = TimerSkill() 
register_skill("timer_skill", skill) 

__all__ = ["TimerSkill", "skill"] 
