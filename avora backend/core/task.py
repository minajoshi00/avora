"""
================================================================
CORE TASK REPRESENTATION
================================================================

Structured task representation that captures:
- goal: What the user wants to achieve
- intent: The action type (open, search, find, etc.)
- entities: Applications, people, files, targets, locations
- context: Current state (active application, location, person, etc.)
- prerequisites: What must be true before actions execute
- actions: Ordered list of actions to execute
- dependencies: What each action depends on
- expected_result: What success looks like
- verification: How to verify the result
- recovery_strategy: What to do if something fails
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time

import logging

logger = logging.getLogger("avora.core.task")


class IntentType(Enum):
    """Types of user intents that can be detected."""
    OPEN_APP = "open_app"
    OPEN_FILE = "open_file"
    OPEN_FOLDER = "open_folder"
    SEARCH_WEB = "search_web"
    SEARCH_FILES = "search_files"
    FIND_PERSON = "find_person"
    FIND_FILE = "find_file"
    PLAY_MEDIA = "play_media"
    CALCULATE = "calculate"
    SET_TIMER = "set_timer"
    SETTING_CHANGE = "setting_change"
    POWER_ACTION = "power_action"
    LAUNCH_GAME = "launch_game"
    WRITE = "write"
    PROACTIVE_HINT = "proactive_hint"
    CONTEXT_QUERY = "context_query"
    GREETING = "greeting"
    FAREWELL = "farewell"
    UNKNOWN = "unknown"
    SEND_MESSAGE = "send_message"
    CHECK_STATUS = "check_status"
    COMPARE = "compare"
    WEATHER_QUERY = "weather_query"
    LEARNING = "learning"
    NOTE = "note"
    PYTHON_EXECUTE = "python_execute"
    JAVASCRIPT_EXECUTE = "javascript_execute"
    SUMMARIZE = "summarize"


@dataclass
class TaskEntity:
    """An entity extracted from user input."""
    type: str  # "application", "person", "file", "folder", "website", "setting", "query"
    value: str
    normalized: str = ""


@dataclass
class TaskAction:
    """A single action within a task plan."""
    action: str  # e.g., "open", "search", "find", "click", "type", "change_setting"
    target: str  # e.g., "Instagram", "Atharba Bhandari", "physics PDF"
    context: Optional[str] = None  # e.g., "Instagram" (the environment)
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: Optional[str] = None  # What this action depends on
    expected_result: Optional[str] = None
    verification: Optional[str] = None


@dataclass
class TaskContext:
    """Current context that survives between actions."""
    active_application: Optional[str] = None
    active_location: Optional[str] = None  # e.g., "Downloads", "Desktop"
    active_person: Optional[str] = None
    active_file: Optional[str] = None
    active_webpage: Optional[str] = None
    last_result: Optional[Dict] = None
    last_search_results: Optional[List] = None

    # For reference resolution
    recent_actions: List[Dict] = field(default_factory=list)
    referenced_entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskPlan:
    """A structured plan for executing actions."""
    goal: str
    intent: IntentType
    entities: List[TaskEntity]
    context: TaskContext
    actions: List[TaskAction] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=lambda: {})
    expected_result: Optional[str] = None
    verification: Optional[str] = None
    recovery_strategy: Optional[str] = None
    priority: int = 5
    estimated_duration: float = 0.0
    requires_confirmation: bool = False

    def is_valid(self) -> bool:
        """Check if the plan is valid."""
        return len(self.actions) > 0 and self.intent != IntentType.UNKNOWN

    def add_action(self, action: TaskAction):
        """Add an action to the plan."""
        self.actions.append(action)

    def get_action_index(self, action_name: str, target: str) -> Optional[int]:
        """Find the index of an action by name and target."""
        for i, action in enumerate(self.actions):
            if action.action == action_name and action.target == target:
                return i
        return None


@dataclass
class DetectedIntent:
    """Result of intent detection with full entity and context information."""
    intent: IntentType
    target: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_match: Optional[str] = None
    context_needed: List[str] = field(default_factory=list)

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if intent confidence meets threshold."""
        return self.confidence >= threshold


@dataclass
class TaskResult:
    """Result of task execution."""
    success: bool
    message: str
    actions_taken: List[str]
    duration: float
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_updates: Optional[TaskContext] = None