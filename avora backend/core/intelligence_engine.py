"""
============================================================
AVORA Intelligence Engine
============================================================

Central pipeline for processing user requests through
the complete AI reasoning lifecycle.

Pipeline:
    User Request → Intent Detection → Context Collection → 
    Memory Retrieval → Reasoning → Action Planning → 
    Skill Selection → Execution → Response Generation

This is the main entry point for all user interactions.
"""

import os
import re
import json
import time
import logging
import threading
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

from app_database import get_database
from app_paths import APP_DATA_DIR

logger = logging.getLogger("IntelligenceEngine")


class IntentType(Enum):
    """Types of user intents that can be detected."""
    OPEN_APP = "open_app"
    OPEN_FILE = "open_file"
    OPEN_FOLDER = "open_folder"
    SEARCH_WEB = "search_web"
    SEARCH_FILES = "search_files"
    PLAY_MEDIA = "play_media"
    CALCULATE = "calculate"
    SET_TIMER = "set_timer"
    WEATHER = "weather"
    WEATHER_QUERY = "weather_query"
    REMIND = "remind"
    NOTE = "note"
    SETTING_CHANGE = "setting_change"
    POWER_ACTION = "power_action"
    LAUNCH_GAME = "launch_game"
    CODING_HELP = "coding_help"
    LEARNING = "learning"
    STUDY = "study"
    WRITE = "write"
    PROACTIVE_HINT = "proactive_hint"
    CONTEXT_QUERY = "context_query"
    GREETING = "greeting"
    FAREWELL = "farewell"
    JAVASCRIPT_EXECUTE = "javascript_execute"
    PYTHON_EXECUTE = "python_execute"
    UNKNOWN = "unknown"


@dataclass
class UserRequest:
    """A processed user request with all metadata."""
    raw_text: str
    timestamp: float
    normalized_text: str
    source: str = "voice"
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass 
class DetectedIntent:
    """Result of intent detection."""
    intent: IntentType
    target: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_match: Optional[str] = None
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if intent confidence meets threshold."""
        return self.confidence >= threshold


@dataclass
class ContextSnapshot:
    """Complete context at a moment in time."""
    timestamp: float = field(default_factory=time.time)
    
    # System context
    active_window: Optional[str] = None
    active_process: Optional[str] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    battery_level: Optional[int] = None
    is_battery_powered: bool = False
    wifi_connected: bool = False
    idle_minutes: float = 0.0
    
    # User context
    time_of_day: int = field(default_factory=lambda: datetime.now().hour)
    day_of_week: int = field(default_factory=lambda: datetime.now().weekday())
    
    # Engagement context
    is_processing: bool = False
    is_voice_active: bool = False
    conversation_count: int = 0
    
    # Environment
    has_multiple_displays: bool = False
    headphones_connected: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "active_window": self.active_window,
            "active_process": self.active_process,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "battery_level": self.battery_level,
            "is_battery_powered": self.is_battery_powered,
            "wifi_connected": self.wifi_connected,
            "idle_minutes": self.idle_minutes,
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "is_processing": self.is_processing,
            "is_voice_active": self.is_voice_active,
            "conversation_count": self.conversation_count,
            "has_multiple_displays": self.has_multiple_displays,
            "headphones_connected": self.headphones_connected,
        }


@dataclass
class ActionPlan:
    """A structured plan for executing actions."""
    steps: List[Dict[str, Any]]
    priority: int = 5
    estimated_duration: float = 0.0
    requires_confirmation: bool = False
    context_needed: List[str] = field(default_factory=lambda: ["context"])
    
    def add_step(self, skill_name: str, action: str, params: Dict = None):
        """Add an action step to the plan."""
        import time
        self.steps.append({
            "skill": skill_name,
            "action": action,
            "params": params or {},
            "timestamp": time.time(),
        })
    
    def is_valid(self) -> bool:
        """Check if the plan is valid."""
        return len(self.steps) > 0


@dataclass
class ExecutionResult:
    """Result of plan execution."""
    success: bool
    message: str
    actions_taken: List[str]
    duration: float
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligenceEngine:
    """
    Central AI pipeline that processes user requests end-to-end.
    
    Coordinates:
    - Request intake and normalization
    - Intent detection via pattern matching and AI
    - Context collection from live system state
    - Memory retrieval for personalization
    - Reasoning and plan generation
    - Skill orchestration for execution
    - Response generation with personality
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._app_data_dir = APP_DATA_DIR
        self._app_data_dir.mkdir(parents=True, exist_ok=True)
        
        self._state_file = self._app_data_dir / "engine_state.json"
        self._state = self._load_state()
        
        self._request_count = 0
        self._session_id = None
        
        self._thread_local = threading.local()
        
        self._intent_cache: Dict[str, DetectedIntent] = {}
        
        self._start_time = time.time()
        
        logger.info("Intelligence Engine initialized")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load engine state from disk."""
        if self._state_file.exists():
            try:
                with open(self._state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "session_start": time.time(),
            "total_requests": 0,
            "last_request_time": 0,
        }
    
    def _save_state(self):
        """Save engine state to disk."""
        try:
            self._state["total_requests"] = self._request_count
            self._state["last_request_time"] = time.time()
            with open(self._state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except IOError as e:
            logger.debug(f"State save error: {e}")
    
    def process_request(self, user_input: str, 
                        context: Optional[ContextSnapshot] = None,
                        source: str = "voice") -> Dict[str, Any]:
        """
        Process a user request through the complete pipeline.
        
        Args:
            user_input: Raw user text
            context: Pre-collected context (if not provided, will collect)
            source: Source of request (voice, text, hotkey, etc.)
            
        Returns:
            Dict with response text and optional actions
        """
        start_time = time.time()
        
        self._request_count += 1
        self._state["total_requests"] = self._request_count
        
        request = UserRequest(
            raw_text=user_input,
            timestamp=start_time,
            normalized_text=self._normalize(user_input),
            source=source,
            session_id=self._session_id,
        )
        
        logger.debug(f"Processing request: {request.raw_text}")
        
        detected_intent = self._detect_intent(request, context)
        
        if detected_intent is None or detected_intent.intent == IntentType.UNKNOWN:
            response = self._handle_unknown_intent(request, context)
            self._save_state()
            return response
        
        if context is None:
            context = self._collect_context()
        
        plan = self._plan_action(detected_intent, context, request)
        
        result = self._execute_plan(plan, context, request)
        
        duration = time.time() - start_time
        result["duration_seconds"] = duration
        
        self._save_state()
        
        logger.debug(f"Request processed in {duration:.3f}s, intent={detected_intent.intent.value}")
        
        return result
    
    def _normalize(self, text: str) -> str:
        """Normalize text for processing with security sanitization."""
        if not text:
            return ""
        text = str(text).lower().strip()
        
        # Limit input length to prevent DoS
        if len(text) > 500:
            text = text[:500]
        
        # Remove dangerous characters for safety
        dangerous_chars = ['`', '$', ';', '|', '&', '\n', '\r', '\x00']
        for char in dangerous_chars:
            text = text.replace(char, ' ')
        
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    def _detect_intent(self, request: UserRequest, 
                       context: Optional[ContextSnapshot] = None) -> Optional[DetectedIntent]:
        """
        Detect user intent from the request.
        
        This is the first major step in the pipeline.
        Uses pattern matching for common intents, can extend to AI-based detection.
        """
        normalized = request.normalized_text
        
        patterns = [
            (r"^(open|launch|start)\s+(?:my\s+|the\s+)?(.+)$", IntentType.OPEN_APP),
            (r"^(open|start)\s+(?:the\s+)?file\s+(.+)$", IntentType.OPEN_FILE),
            (r"^(open|start)\s+(?:the\s+)?folder\s+(.+)$", IntentType.OPEN_FOLDER),
            (r"^(search|look\s+up|google)\s+(?:for\s+)?(.+)$", IntentType.SEARCH_WEB),
            (r"^(what\s+is|calculate|what's\s+the\s+)?(.+?)\s*=\s*(.+)$", IntentType.CALCULATE),
            (r"^(set\s+)?(?:timer|reminder)\s+(?:for\s+)?(\d+)\s*(second|minute|hour)s?", IntentType.SET_TIMER),
            (r"^(weather|how\s+is\s+the\s+weather)\s*(?:in\s+(.+))?", IntentType.WEATHER_QUERY),
            (r"^(shutdown|restart|sleep|lock)\s+(?:my\s+)?computer", IntentType.POWER_ACTION),
            (r"^(open|launch|start)\s+(?:the\s+)?(?:game|games?\s+(.+))", IntentType.LAUNCH_GAME),
            (r"^(define|meaning of|what is)\s+(.+)", IntentType.LEARNING),
            (r"^(remind|remember|note)\s+(.+)", IntentType.NOTE),
        ]
        
        for pattern, intent_type in patterns:
            match = re.search(pattern, normalized)
            if match:
                return DetectedIntent(
                    intent=intent_type,
                    target=match.group(2) if match.lastindex >= 2 else "",
                    confidence=0.85,
                    entities={"regex_group_1": match.group(1), "regex_group_2": match.group(2) if match.lastindex >= 2 else None},
                )
        
        if any(word in normalized for word in ["python", "python script", ".py"]):
            return DetectedIntent(
                intent=IntentType.PYTHON_EXECUTE,
                target=normalized,
                confidence=0.7,
            )
        
        if any(word in normalized for word in ["javascript", "js", ".js"]):
            return DetectedIntent(
                intent=IntentType.JAVASCRIPT_EXECUTE,
                target=normalized,
                confidence=0.7,
            )
        
        if normalized in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]:
            return DetectedIntent(
                intent=IntentType.GREETING,
                target=normalized,
                confidence=0.9,
            )
        
        if normalized in ["bye", "goodbye", "see you", "bye bye"]:
            return DetectedIntent(
                intent=IntentType.FAREWELL,
                target=normalized,
                confidence=0.9,
            )
        
        return DetectedIntent(
            intent=IntentType.UNKNOWN,
            target=normalized,
            confidence=0.3,
        )
    
    def _collect_context(self) -> ContextSnapshot:
        """Collect current system context."""
        return ContextSnapshot()
    
    def _plan_action(self, intent: DetectedIntent, 
                      context: ContextSnapshot,
                      request: UserRequest) -> ActionPlan:
        """
        Create an action plan based on the detected intent.
        
        This is where multi-step planning happens.
        """
        plan = ActionPlan(steps=[], priority=5, requires_confirmation=False)
        
        skill_mapping = {
            IntentType.OPEN_APP: ("launcher_skill", "open_application"),
            IntentType.OPEN_FILE: ("files_skill", "open_file"),
            IntentType.OPEN_FOLDER: ("files_skill", "open_folder"),
            IntentType.SEARCH_WEB: ("browser_skill", "search"),
            IntentType.CALCULATE: ("calculator_skill", "calculate"),
            IntentType.SET_TIMER: ("timer_skill", "set_timer"),
            IntentType.WEATHER_QUERY: ("weather_skill", "get_weather"),
            IntentType.POWER_ACTION: ("power_skill", "execute_power_action"),
            IntentType.LAUNCH_GAME: ("games_skill", "launch_game"),
            IntentType.LEARNING: ("learning_skill", "answer_question"),
            IntentType.NOTE: ("memory_skill", "create_note"),
            IntentType.PYTHON_EXECUTE: ("coding_skill", "execute_python"),
            IntentType.JAVASCRIPT_EXECUTE: ("coding_skill", "execute_javascript"),
            IntentType.GREETING: ("personality_skill", "greet"),
            IntentType.FAREWELL: ("personality_skill", "farewell"),
        }
        
        skill_info = skill_mapping.get(intent.intent, ("core_skill", "handle_unknown"))
        
        plan.add_step(
            skill_name=skill_info[0],
            action=skill_info[1],
            params={
                "target": intent.target,
                "entities": intent.entities,
                "confidence": intent.confidence,
                "context": context.to_dict() if context else {},
            }
        )
        
        return plan
    
    def _execute_plan(self, plan: ActionPlan, 
                      context: ContextSnapshot,
                      request: UserRequest) -> Dict[str, Any]:
        """
        Execute the action plan step by step.
        
        This coordinates skill execution and error handling.
        """
        if not plan.is_valid():
            return {
                "success": False,
                "message": "Invalid or empty action plan.",
                "actions_taken": [],
            }
        
        results = []
        actions_taken = []
        
        for step in plan.steps:
            skill_name = step.get("skill", "core_skill")
            action = step.get("action", "execute")
            params = step.get("params", {})
            
            try:
                result = self._execute_action(skill_name, action, params)
                results.append(result)
                
                if isinstance(result, dict):
                    actions_taken.append(result.get("action", action))
                    if not result.get("success", True) and "success" in result:
                        return result
                else:
                    actions_taken.append(action)
                    
            except Exception as e:
                logger.error(f"Action execution error: {e}")
                return {
                    "success": False,
                    "message": f"Execution error: {str(e)}",
                    "actions_taken": actions_taken,
                    "error": e,
                }
        
        message = self._generate_response(results, plan)
        
        return {
            "success": True,
            "message": message,
            "actions_taken": actions_taken,
            "intent": plan.steps[0].get("params", {}).get("target", "") if plan.steps else "",
        }
    
    def _execute_action(self, skill_name: str, action: str, 
                        params: Dict) -> Dict[str, Any]:
        """Execute a single action via the skill system."""
        
        try:
            from skills import SKILL_REGISTRY
            
            if skill_name in SKILL_REGISTRY:
                skill = SKILL_REGISTRY[skill_name]
                
                if hasattr(skill, action):
                    method = getattr(skill, action)
                    result = method(**params)
                    return result if isinstance(result, dict) else {
                        "success": True,
                        "action": action,
                        "result": result,
                    }
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Skill execution error: {e}")
        
        if skill_name == "launcher_skill" and action == "open_application":
            return self._fallback_launch(params)
        
        return {
            "success": False,
            "action": action,
            "message": f"No handler for {skill_name}.{action}",
        }
    
    def _fallback_launch(self, params: Dict) -> Dict[str, Any]:
        """Fallback launcher using existing ai_logic."""
        try:
            from ai_logic import launch_app
            
            target = params.get("target", "")
            if target:
                result = launch_app(f"open {target}")
                return {
                    "success": result is not None,
                    "action": "launch_app",
                    "message": result or f"Could not launch {target}",
                }
        except ImportError:
            pass
        
        return {
            "success": False,
            "action": "launch_app",
            "message": "Launcher not available",
        }
    
    def _generate_response(self, results: List[Dict], 
                          plan: ActionPlan) -> str:
        """Generate the response message."""
        if not results:
            return "Done."
        
        messages = []
        for r in results:
            if isinstance(r, dict):
                msg = r.get("message", "")
                if msg:
                    messages.append(msg)
        
        return " ".join(messages) if messages else "Completed."
    
    def _handle_unknown_intent(self, request: UserRequest,
                               context: Optional[ContextSnapshot]) -> Dict[str, Any]:
        """Handle requests where intent is unclear."""
        return {
            "success": False,
            "message": f"I'm not sure what you mean by '{request.raw_text}'. Can you clarify?",
            "actions_taken": [],
            "requires_clarification": True,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_requests": self._request_count,
            "session_duration": time.time() - self._state.get("session_start", time.time()),
            "last_request_time": self._state.get("last_request_time", 0),
        }


_engine = None

def get_intelligence_engine() -> IntelligenceEngine:
    """Get the singleton intelligence engine."""
    global _engine
    if _engine is None:
        _engine = IntelligenceEngine()
    return _engine


__all__ = [
    "IntelligenceEngine",
    "get_intelligence_engine",
    "IntentType",
    "UserRequest",
    "DetectedIntent",
    "ContextSnapshot",
    "ActionPlan",
    "ExecutionResult",
]