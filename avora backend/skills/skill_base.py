"""
============================================================
AVORA Skill Framework
============================================================

Plugin system for AVORA's capabilities.
Each skill handles a specific domain of functionality.

Each skill implements:
- can_handle(): Check if skill can process the request
- plan(): Create action plan for the request
- execute(): Execute the action
- cancel(): Cancel ongoing operations
- status(): Get current skill status

SKILL REGISTRY
==============
All skills must be registered in SKILL_REGISTRY.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger("Skills")


class BaseSkill(ABC):
    """Base class for all AVORA skills."""
    
    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description
        self._enabled = True
        self._last_error: Optional[str] = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool:
        """
        Check if this skill can handle the given request.
        
        Args:
            intent: The detected intent type
            params: Additional parameters from the request
            
        Returns:
            True if this skill can handle the request
        """
        return False
    
    @abstractmethod
    def plan(self, intent: str, params: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create an action plan for the request.
        
        Args:
            intent: The detected intent type
            params: Parameters from the request
            context: Current system context
            
        Returns:
            Plan dictionary or None if skill cannot handle
        """
        pass
    
    @abstractmethod
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action plan.
        
        Args:
            plan: The plan created by plan()
            
        Returns:
            Execution result dictionary
        """
        pass
    
    def cancel(self) -> bool:
        """
        Cancel any ongoing operation.
        
        Returns:
            True if cancellation was successful
        """
        return True
    
    def status(self) -> Dict[str, Any]:
        """
        Get the current status of the skill.
        
        Returns:
            Status dictionary
        """
        return {
            "name": self._name,
            "enabled": self._enabled,
            "description": self._description,
            "last_error": self._last_error,
        }
    
    def disable(self):
        """Disable this skill."""
        self._enabled = False
    
    def enable(self):
        """Enable this skill."""
        self._enabled = True
    
    def set_error(self, error: str):
        """Record the last error."""
        self._last_error = error


# Registry for all skills
SKILL_REGISTRY: Dict[str, BaseSkill] = {}


def register_skill(name: str, skill: BaseSkill):
    """Register a skill in the global registry."""
    SKILL_REGISTRY[name] = skill
    logger.debug(f"Registered skill: {name}")


def get_skill(name: str) -> Optional[BaseSkill]:
    """Get a skill by name."""
    return SKILL_REGISTRY.get(name)


def get_all_skills() -> List[BaseSkill]:
    """Get all registered skills."""
    return list(SKILL_REGISTRY.values())


def get_enabled_skills() -> List[BaseSkill]:
    """Get all enabled skills."""
    return [s for s in SKILL_REGISTRY.values() if s.enabled]


__all__ = [
    "BaseSkill",
    "SKILL_REGISTRY",
    "register_skill",
    "get_skill",
    "get_all_skills",
    "get_enabled_skills",
]