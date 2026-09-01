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

from .task import (
    TaskEntity,
    TaskAction,
    TaskContext,
    TaskPlan,
    DetectedIntent,
    TaskResult,
    IntentType as TaskIntentType,
    logger,
)

# Intent types now come from task.py TaskIntentType
# We define local aliases for backward compatibility
IntentType = TaskIntentType  # Alias for the task.py IntentType


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
    context_needed: Optional[str] = None
    
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
                        context: Optional[TaskContext] = None,
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
                           context: Optional[TaskContext] = None) -> Optional[DetectedIntent]:
        """
        Detect user intent from the request.
        
        This is the first major step in the pipeline.
        Uses pattern matching for common intents, can extend to AI-based detection.
        Returns a structured DetectedIntent with entities and context needs.
        """
        normalized = request.normalized_text
        
        # Extract entities and intent from pattern matching
        entities: Dict[str, Any] = {}
        intent: Optional[IntentType] = None
        target = ""
        context_needed: List[str] = []
        
        # Pattern: "open <application>" — handles "Open X and <do Y>" syntax
        match = re.search(r"^(open|launch|start)\s+(?:my\s+|the\s+)?(.+)$", normalized)
        if match:
            raw_target = match.group(2).strip()
            # ---------------------------------------------------------
            # GENERAL SEMANTIC SPLIT — "Open X and <do Y>"
            # An "and"-joined sentence describes MULTIPLE intents, not a
            # single application name. The part after "and" carries its own
            # verb (search/find/check/play/message...), so the whole
            # remainder must NEVER be launched as an application
            # (e.g. OPEN_APPLICATION("check for Atharba Bhandari")).
            # We plan the leading OPEN step here; the follow-up intent is
            # detected separately below so a second action can be chained.
            # ---------------------------------------------------------
            and_parts = re.split(r"\s+and\s+|,\s*then\s+|,\s+then\s+", raw_target, maxsplit=1)
            if len(and_parts) == 2:
                intent = IntentType.OPEN_APP
                target = and_parts[0].strip()
                follow_up = and_parts[1].strip()
                entities["raw_target"] = target
                entities["follow_up"] = follow_up
                context_needed.append("application_resolution")
                # Classify the follow-up clause by its own verb phrase.
                # We use a broader set of verbs to correctly route the
                # follow-up to the right capability (browser search, media,
                # more app actions, or inspection).
                fu = follow_up.lower().strip()
                # Media/play actions
                if re.match(r"^(play|watch)\b", fu):
                    entities["follow_up_intent"] = "play_media"
                # Browser/web inspection actions — this is the key fix:
                # "check who got first msg", "read the latest message",
                # "find my friend", etc. should ALL route to web search
                # so the user can inspect the result, NOT to open_application.
                elif re.match(r"^(find|check|look|read|inspect|verify)\b", fu):
                    # Broadly route all inspection-type follow-ups to search_web
                    # so the user can browse/inspect the results.
                    entities["follow_up_intent"] = "search_web"
                # Open/navigate follow-ups
                elif re.match(r"^(open|go to|visit)\b", fu):
                    entities["follow_up_intent"] = "open"
                # Search/web search follow-ups
                elif re.match(r"^(search|lookup|google)\b", fu):
                    entities["follow_up_intent"] = "search_web"
                # Media actions
                elif re.match(r"^(play|watch)\b", fu):
                    entities["follow_up_intent"] = "play_media"
                # Default: route to search_web for inspection
                else:
                    entities["follow_up_intent"] = "search_web"
            else:
                intent = IntentType.OPEN_APP
                target = raw_target
                entities["raw_target"] = target
                context_needed.append("application_resolution")
        
        # Pattern: "open <file>"
        match = re.search(r"^(open|start)\s+(?:the\s+)?file\s+(.+)$", normalized)
        if match:
            intent = IntentType.OPEN_FILE
            target = match.group(2).strip()
            entities["raw_target"] = target
            context_needed.append("file_resolution")
        
        # Pattern: "open <folder>"
        match = re.search(r"^(open|start)\s+(?:the\s+)?folder\s+(.+)$", normalized)
        if match:
            intent = IntentType.OPEN_FOLDER
            target = match.group(2).strip()
            entities["raw_target"] = target
            context_needed.append("folder_resolution")
        
        # Pattern: "search web for <query>"
        match = re.search(r"^(search|look\s+up|google)\s+(?:for\s+)?(.+)$", normalized)
        if match:
            intent = IntentType.SEARCH_WEB
            target = match.group(2).strip()
            entities["raw_target"] = target
            context_needed.append("web_search")
        
        # Pattern: "calculate <expr>"
        match = re.search(r"^(what\s+is|calculate|what's\s+the\s+)?(.+?)\s*=\s*(.+)$", normalized)
        if match:
            intent = IntentType.CALCULATE
            target = f"{match.group(2).strip()} = {match.group(3).strip()}"
            entities["expression"] = match.group(2).strip()
            entities["result"] = match.group(3).strip()
            context_needed.append("calculation")
        
        # Pattern: "set timer <duration>"
        match = re.search(r"^(set\s+)?(?:timer|reminder)\s+(?:for\s+)?(\d+)\s*(second|minute|hour)s?", normalized)
        if match:
            intent = IntentType.SET_TIMER
            duration = match.group(2).strip()
            unit = match.group(3).strip()
            target = f"timer for {duration} {unit}"
            entities["duration"] = duration
            entities["unit"] = unit
            context_needed.append("timer_setup")
        
        # Pattern: "weather in <location>"
        match = re.search(r"^(weather|how\s+is\s+the\s+weather)\s*(?:in\s+(.+))?", normalized)
        if match:
            intent = IntentType.WEATHER_QUERY
            location = match.group(2).strip() if match.group(2) else ""
            target = f"weather in {location}"
            entities["location"] = location
            context_needed.append("weather_lookup")
        
        # Pattern: "shutdown/restart/sleep/lock computer"
        match = re.search(r"^(shutdown|restart|sleep|lock)\s+(?:my\s+)?computer", normalized)
        if match:
            intent = IntentType.POWER_ACTION
            target = match.group(1).strip()
            entities["action"] = target
            context_needed.append("power_action")
        
        # Pattern: "open <game>"
        match = re.search(r"^(open|launch|start)\s+(?:the\s+)?(?:game|games?\s+(.+))", normalized)
        if match:
            intent = IntentType.LAUNCH_GAME
            target = match.group(2).strip() if match.group(2) else ""
            entities["raw_target"] = target
            context_needed.append("game_resolution")
        
        # Pattern: "define <term>" or "what is <term>"
        match = re.search(r"^(define|meaning of|what is)\s+(.+)", normalized)
        if match:
            intent = IntentType.LEARNING
            target = match.group(2).strip()
            entities["term"] = target
            context_needed.append("learning_lookup")
        
        # Pattern: "remind/remember/note <thing>"
        match = re.search(r"^(remind|remember|note)\s+(.+)", normalized)
        if match:
            intent = IntentType.NOTE
            target = match.group(2).strip()
            entities["note_content"] = target
            context_needed.append("note_creation")
        
        # If no pattern matched, check for known keywords
        if intent is None:
            lower = normalized
            if any(word in lower for word in ["python", "python script", ".py"]):
                intent = IntentType.PYTHON_EXECUTE
                target = normalized
                entities["code"] = normalized
                context_needed.append("code_execution")
            elif any(word in lower for word in ["javascript", "js", ".js"]):
                intent = IntentType.JAVASCRIPT_EXECUTE
                target = normalized
                entities["code"] = normalized
                context_needed.append("code_execution")
            elif normalized in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]:
                intent = IntentType.GREETING
                target = normalized
                context_needed.append("greeting")
            elif normalized in ["bye", "goodbye", "see you", "bye bye"]:
                intent = IntentType.FAREWELL
                target = normalized
                context_needed.append("farewell")
            else:
                intent = IntentType.UNKNOWN
                target = normalized
        
        # Build entities dict with normalized values
        normalized_entities: Dict[str, Any] = {}
        for key, value in entities.items():
            if isinstance(value, str):
                normalized_entities[key] = value.lower().strip()
            else:
                normalized_entities[key] = value
        
        # Use the target from the matched pattern, or fall back to normalized
        final_target = target if target else normalized
        
        return DetectedIntent(
            intent=intent,
            target=final_target,
            confidence=0.85 if intent else 0.3,
            entities=normalized_entities,
            raw_match=normalized,
            context_needed=context_needed,
        )

    def _collect_context(self) -> TaskContext:
        """Collect current system context."""
        return TaskContext()
    
    def _plan_action(self, intent: DetectedIntent,
                     context: TaskContext,
                     request: UserRequest) -> TaskPlan:
        """
        Create a structured action plan based on the detected intent.
        
        This creates a proper TaskPlan with TaskActions, including
        prerequisites, dependencies, expected results, and verification.
        """
        plan = TaskPlan(
            goal=request.normalized_text,
            intent=intent.intent,
            entities=[TaskEntity(type=et, value=val) for et, val in intent.entities.items()],
            context=context,
        )
        
        # Map intent to actions based on the intent type and entities
        intent_mapping = {
            IntentType.OPEN_APP: self._plan_open_app,
            IntentType.OPEN_FILE: self._plan_open_file,
            IntentType.OPEN_FOLDER: self._plan_open_folder,
            IntentType.SEARCH_WEB: self._plan_search_web,
            IntentType.CALCULATE: self._plan_calculate,
            IntentType.SET_TIMER: self._plan_set_timer,
            IntentType.WEATHER_QUERY: self._plan_weather_query,
            IntentType.POWER_ACTION: self._plan_power_action,
            IntentType.LAUNCH_GAME: self._plan_launch_game,
            IntentType.LEARNING: self._plan_learning,
            IntentType.NOTE: self._plan_note,
            IntentType.PYTHON_EXECUTE: self._plan_code_execute,
            IntentType.JAVASCRIPT_EXECUTE: self._plan_code_execute,
            IntentType.GREETING: self._plan_greeting,
            IntentType.FAREWELL: self._plan_farewell,
        }
        
        mapper = intent_mapping.get(intent.intent)
        if mapper:
            mapper(plan, intent, request)
        
        # If no specific mapper matched, create a default plan
        if not plan.is_valid():
            plan.add_action(TaskAction(
                action="handle_unknown",
                target=intent.target,
            ))
        
        return plan
    
    def _plan_open_app(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for opening an application."""
        target = intent.target
        entities = intent.entities
        
        # Check if target is a known application or needs resolution
        plan.add_action(TaskAction(
            action="open",
            target=target,
            context=entities.get("application_context"),
            expected_result=f"Application '{target}' is running",
            verification=f"Check that {target} window is active",
        ))
        
        # Add prerequisite: application must be installed
        plan.prerequisites.append(f"Application '{target}' must be installed")
        
        # Set dependency on application resolution
        if "application" in entities:
            plan.dependencies["application_resolution"] = [target]
        
        # -------------------------------------------------------------
        # GENERAL SEMANTIC CHAINING — the follow-up clause of
        # "Open X and <do Y>" becomes a SECOND plan action that consumes
        # the first step's output (the opened application as context).
        # This is intent-driven, not tied to any specific application.
        # -------------------------------------------------------------
        follow_up_intent = entities.get("follow_up_intent")
        if follow_up_intent:
            fu_target = entities.get("follow_up", "")
            # A third chained clause ("..., then open the first result")
            # is split off so the final step can consume step 2's output.
            then_parts = re.split(r",\s*then\s+|,\s+then\s+|\s+then\s+", fu_target, maxsplit=1)
            if len(then_parts) == 2:
                fu_target = then_parts[0].strip()
                third_clause = then_parts[1].strip()
            else:
                third_clause = None
            if follow_up_intent == "search_web":
                # Strip the verb from "search for X"
                fu_target = re.sub(r"^(search|look\s+up|google)\s*(?:for\s+)?", "", fu_target, flags=re.IGNORECASE).strip()
                plan.add_action(TaskAction(
                    action="search_web",
                    target=fu_target,
                    params={"skill": "browser_skill", "query": fu_target},
                    context=entities.get("raw_target"),
                    expected_result=f"Search results for '{fu_target}'",
                    verification="Check that search results page loaded",
                ))
            elif follow_up_intent == "play_media":
                fu_target = re.sub(r"^(play|watch)\s+", "", fu_target, flags=re.IGNORECASE).strip()
                plan.add_action(TaskAction(
                    action="play_media",
                    target=fu_target,
                    params={"skill": "browser_skill", "target": fu_target},
                    context=entities.get("raw_target"),
                    expected_result=f"Media '{fu_target}' playing",
                    verification="Check that media playback started",
                ))
            elif follow_up_intent == "open":
                fu_target = re.sub(r"^(open|go\s+to)\s+", "", fu_target, flags=re.IGNORECASE).strip()
                plan.add_action(TaskAction(
                    action="open",
                    target=fu_target,
                    context=entities.get("raw_target"),
                    expected_result=f"'{fu_target}' opened",
                    verification=f"Check that '{fu_target}' opened",
                ))
            else:  # find_entity (person/file/entity) — route to search_web
                # since browser_skill.find_entity is not implemented; use
                # web search instead so the user can inspect results.
                fu_target = re.sub(r"^(find|check|look)\s*(?:for\s+|up\s+)?", "", fu_target, flags=re.IGNORECASE).strip()
                plan.add_action(TaskAction(
                    action="search_web",
                    target=fu_target,
                    params={"skill": "browser_skill", "query": fu_target},
                    context=entities.get("raw_target"),
                    expected_result=f"Search results for '{fu_target}' appear",
                    verification="Check that search results page loaded",
                ))
            # ---------------------------------------------------------
            # THIRD CHAINED STEP — consumes the PREVIOUS step's output as
            # its context (e.g. "open the first result" acts on the search
            # step's results, not on a fresh query).
            # ---------------------------------------------------------
            if third_clause:
                third_verb = re.match(r"^(open|go\s+to|click)\s+(.*)", third_clause, flags=re.IGNORECASE)
                if third_verb:
                    third_target = third_verb.group(2).strip()
                    plan.add_action(TaskAction(
                        action="open",
                        target=third_target,
                        params={"consume_previous_output": True},
                        # context = the SECOND step's target (the search/entity
                        # result) — this is the context-propagation contract.
                        context=fu_target,
                        expected_result=f"'{third_target}' opened from previous step's output",
                        verification=f"Check that '{third_target}' opened",
                    ))
    
    def _plan_open_file(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for opening a file."""
        target = intent.target
        entities = intent.entities
        
        plan.add_action(TaskAction(
            action="open_file",
            target=target,
            expected_result=f"File '{target}' is opened",
            verification=f"Check that file '{target}' is accessible",
        ))
        
        # Determine location/context
        location = entities.get("file_location", "current")
        plan.prerequisites.append(f"File '{target}' must exist at location: {location}")
    
    def _plan_open_folder(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for opening a folder."""
        target = intent.target
        
        plan.add_action(TaskAction(
            action="open_folder",
            target=target,
            expected_result=f"Folder '{target}' is opened",
            verification=f"Check that folder '{target}' is accessible",
        ))
        
        plan.prerequisites.append(f"Folder '{target}' must exist")
    
    def _plan_search_web(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for searching the web."""
        target = intent.target
        entities = intent.entities
        query = target
        
        plan.add_action(TaskAction(
            action="search_web",
            target=query,
            context=entities.get("search_context"),
            expected_result=f"Search results for '{query}' appear",
            verification=f"Check that search results for '{query}' are displayed",
        ))
        
        plan.prerequisites.append(f"Internet access required for web search")
    
    def _plan_calculate(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for calculation."""
        target = intent.target
        entities = intent.entities
        expression = entities.get("expression", target)
        
        plan.add_action(TaskAction(
            action="calculate",
            target=expression,
            expected_result=f"Calculation '{expression}' completed",
            verification=f"Check calculation result is correct",
        ))
    
    def _plan_set_timer(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for setting a timer."""
        target = intent.target
        entities = intent.entities
        duration = entities.get("duration", "")
        unit = entities.get("unit", "minutes")
        
        plan.add_action(TaskAction(
            action="set_timer",
            target=f"{duration} {unit}",
            expected_result=f"Timer set for {duration} {unit}",
            verification=f"Check that timer is running for {duration} {unit}",
        ))
    
    def _plan_weather_query(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for weather query."""
        target = intent.target
        entities = intent.entities
        location = entities.get("location", "")
        
        plan.add_action(TaskAction(
            action="get_weather",
            target=location,
            expected_result=f"Weather information for '{location}' retrieved",
            verification=f"Check weather display for '{location}'",
        ))
        
        plan.prerequisites.append(f"Internet access required for weather lookup")
    
    def _plan_power_action(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for power action."""
        target = intent.target
        entities = intent.entities
        action = entities.get("action", target)
        
        plan.add_action(TaskAction(
            action=f"execute_{action}",
            target=f"{action} computer",
            expected_result=f"{action.title()} computer completed",
            verification=f"Check that {action} action completed",
        ))
    
    def _plan_launch_game(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for launching a game."""
        target = intent.target
        
        plan.add_action(TaskAction(
            action="launch_game",
            target=target,
            expected_result=f"Game '{target}' is launched",
            verification=f"Check that game '{target}' is running",
        ))
        
        plan.prerequisites.append(f"Game '{target}' must be installed")
    
    def _plan_learning(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for learning/query."""
        target = intent.target
        
        plan.add_action(TaskAction(
            action="answer_question",
            target=target,
            expected_result=f"Answer to '{target}' provided",
            verification=f"Check that answer was given",
        ))
    
    def _plan_note(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for creating a note."""
        target = intent.target
        
        plan.add_action(TaskAction(
            action="create_note",
            target=target,
            expected_result=f"Note '{target}' created",
            verification=f"Check that note '{target}' exists",
        ))
    
    def _plan_code_execute(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for code execution."""
        target = intent.target
        
        plan.add_action(TaskAction(
            action="execute_code",
            target=target,
            expected_result=f"Code executed successfully",
            verification=f"Check code execution output",
        ))
    
    def _plan_greeting(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for greeting."""
        plan.add_action(TaskAction(
            action="respond_greeting",
            target="",
            expected_result="Friendly greeting responded",
            verification=f"Check greeting was delivered",
        ))
    
    def _plan_farewell(self, plan: TaskPlan, intent: DetectedIntent, request: UserRequest):
        """Plan for farewell."""
        plan.add_action(TaskAction(
            action="respond_farewell",
            target="",
            expected_result="Farewell responded",
            verification=f"Check farewell was delivered",
        ))
    
    def _execute_plan(self, plan: TaskPlan, 
                  context: TaskContext,
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
        
        for i, step in enumerate(plan.actions):
            skill_name = step.params.get("skill", "core_skill") if step.params else "core_skill"
            action = step.action
            params = step.params or {}
            
            # Check prerequisites
            self._check_prerequisites(plan, step, context)
            
            # Check dependencies - ensure prerequisite actions are complete
            self._check_dependencies(plan, step, context, request)
            
            try:
                result = self._execute_action(skill_name, action, params)
                results.append(result)
                
                if isinstance(result, dict):
                    actions_taken.append(result.get("action", action))
                    if not result.get("success", True) and "success" in result:
                        # Handle failure - try recovery or stop
                        if i + 1 < len(plan.actions):
                            # Don't continue with dependent actions
                            break
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
        
        # Generate response based on results
        message = self._generate_response(results, plan)
        
        # Update context with last results
        if results and plan.context:
            plan.context.last_result = results[-1] if results else None
        
        return {
            "success": True,
            "message": message,
            "actions_taken": actions_taken,
            "intent": plan.actions[0].target if plan.actions else "",
            "context_updates": plan.context,
        }
    
    def _check_prerequisites(self, plan: TaskPlan, step: TaskAction, context: TaskContext):
        """Check if prerequisites are met before executing a step."""
        for prereq in plan.prerequisites:
            # Simple prerequisite check - in a full implementation
            # this would verify the actual state
            pass
    
    def _check_dependencies(self, plan: TaskPlan, step: TaskAction, context: TaskContext, request: UserRequest):
        """Check if action dependencies are satisfied."""
        depends_on = step.depends_on
        if depends_on and depends_on in plan.dependencies:
            # Check if dependent actions completed successfully
            deps = plan.dependencies[depends_on]
            for dep in deps:
                # In a full implementation, check if dep action completed
                pass
    
    def _execute_action(self, skill_name: str, action: str, 
                        params: Dict) -> Dict[str, Any]:
        """Execute a single action via the skill system."""
        
        try:
            from skills import SKILL_REGISTRY
            
            if skill_name in SKILL_REGISTRY:
                skill = SKILL_REGISTRY[skill_name]
                
                # Build an Action object so the skill's execute() method
                # can dispatch based on action_type (e.g. SEARCH_WB, CLICK, etc.)
                from avora_backend.action_model import Action, ActionType
                action_obj = Action(
                    action_type=ActionType(action),
                    target=params.get("target", ""),
                    parameters=params,
                )
                
                # Skills handle action routing internally via their execute() method.
                # Use asyncio.run() to execute the async execute method.
                if hasattr(skill, 'execute') and callable(skill.execute):
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        # If we're already in an async context, use spawn
                        result = asyncio.run(skill.execute(action_obj))
                        return result if isinstance(result, dict) else {
                            "success": True,
                            "action": action,
                            "result": result,
                    }
                    except RuntimeError:
                        # No running loop — safe to use asyncio.run()
                        result = asyncio.run(skill.execute(action_obj))
                        return result if isinstance(result, dict) else {
                            "success": True,
                            "action": action,
                            "result": result,
                        }
                else:
                    # Fallback: try direct method call if execute not available
                    if hasattr(skill, action):
                        method = getattr(skill, action)
                        # If the method is async, try to run it
                        import asyncio
                        if asyncio.iscoroutinefunction(method):
                            try:
                                loop = asyncio.get_running_loop()
                                result = loop.run_until_complete(method(**params))
                                return result if isinstance(result, dict) else {
                                    "success": True,
                                    "action": action,
                                    "result": result,
                                }
                            except RuntimeError:
                                result = asyncio.run(method(**params))
                                return result if isinstance(result, dict) else {
                                    "success": True,
                                    "action": action,
                                    "result": result,
                                }
                        else:
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
        
        # Handle search_web for browser_skill as fallback
        if skill_name == "browser_skill" and action == "search_web":
            from avora_backend.skills.browser_skill import BrowserSkill
            skill = SKILL_REGISTRY.get("browser_skill")
            if skill:
                query = params.get("query", "")
                if query:
                    # Direct synchronous search call as fallback
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        result = loop.run_until_complete(skill.search(query))
                        return result if isinstance(result, dict) else {
                            "success": True,
                            "action": action,
                            "result": result,
                        }
                    except RuntimeError:
                        result = asyncio.run(skill.search(query))
                        return result if isinstance(result, dict) else {
                            "success": True,
                            "action": action,
                            "result": result,
                        }
        
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
                          plan: TaskPlan) -> str:
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
                               context: Optional[TaskContext]) -> Dict[str, Any]:
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
    "TaskContext",
    "TaskPlan",
    "TaskEntity",
    "TaskAction",
    "TaskResult",
]