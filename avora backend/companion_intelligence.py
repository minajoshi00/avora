"""
================================================================
          AI FRIEND - COMPANION INTELLIGENCE SYSTEM
================================================================

Unified "Companion Intelligence" that makes AI Friend feel like
a genuinely alive, context-aware companion rather than a chatbot.

Integrates:
  • Context tracking (from ActivityMonitor + deeper inference)
  • Emotion engine (natural transitions, not random)
  • Goal tracking & progress awareness
  • Achievement recognition & celebration
  • Proactive suggestion engine (local-first, AI-only for complex)
  • Anti-annoyance (confidence scoring, cooldowns, personality)
  • Silent awareness mode (reacts through animations, not messages)
  • Break detection, stuck detection, focus detection, success detection

Design Philosophy:
  - Local logic first. AI API calls only for complex reasoning.
  - Every intervention is scored for confidence before happening.
  - The companion remembers context and learns from interactions.
  - Natural silence is valued—not every moment needs a message.
  - Emotional state evolves naturally from accumulated context.

================================================================
"""

import math
import random
import time
import logging
import threading
from enum import Enum
from typing import Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger("CompanionIntelligence")


# =============================================================
# COMPANION STATE ENUMS
# =============================================================

class CompanionMood(Enum):
    """Core emotional states the companion can be in."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    CONCERNED = "concerned"
    PROUD = "proud"
    FRUSTRATED = "frustrated"
    SYMPATHETIC = "sympathetic"
    PLAYFUL = "playful"
    CALM = "calm"
    THOUGHTFUL = "thoughtful"
    SLEEPY = "sleepy"
    SURPRISED = "surprised"


class UserState(Enum):
    """Inferred user states from context analysis."""
    FOCUSED = "focused"
    STUCK = "stuck"
    SUCCEEDING = "succeeding"
    IDLE = "idle"
    ON_BREAK = "on_break"
    EXPLORING = "exploring"
    FRUSTRATED = "frustrated"
    DISTRACTED = "distracted"
    LEARNING = "learning"
    CREATING = "creating"
    UNKNOWN = "unknown"


class InterventionType(Enum):
    """Types of companion actions."""
    SILENT_AWARENESS = "silent_awareness"       # animation change only
    SUBTLE_HINT = "subtle_hint"                  # small notification bubble
    PROACTIVE_SUGGESTION = "proactive_suggestion" # chat message
    CELEBRATION = "celebration"                   # excited reaction
    ENCOURAGEMENT = "encouragement"               # support message
    CHECK_IN = "check_in"                         # "you ok?" type
    BREAK_REMINDER = "break_reminder"             # take a break
    CONTEXT_QUERY = "context_query"              # "need help with that?"


# =============================================================
# ANTI-ANNOYANCE CONFIG
# =============================================================

_COOLDOWN_DEFAULTS = {
    InterventionType.SILENT_AWARENESS: 30,         # 30s between silent reacts
    InterventionType.SUBTLE_HINT: 120,             # 2 min between hints
    InterventionType.PROACTIVE_SUGGESTION: 600,    # 10 min between suggestions
    InterventionType.CELEBRATION: 300,             # 5 min between celebrations
    InterventionType.ENCOURAGEMENT: 180,           # 3 min between encouragements
    InterventionType.CHECK_IN: 600,                # 10 min between check-ins
    InterventionType.BREAK_REMINDER: 900,          # 15 min between break reminders
    InterventionType.CONTEXT_QUERY: 300,           # 5 min between context queries
}

_CONFIDENCE_THRESHOLDS = {
    InterventionType.SILENT_AWARENESS: 0.3,
    InterventionType.SUBTLE_HINT: 0.5,
    InterventionType.PROACTIVE_SUGGESTION: 0.7,
    InterventionType.CELEBRATION: 0.8,
    InterventionType.ENCOURAGEMENT: 0.6,
    InterventionType.CHECK_IN: 0.6,
    InterventionType.BREAK_REMINDER: 0.5,
    InterventionType.CONTEXT_QUERY: 0.6,
}

_MAX_INTERVENTIONS_PER_HOUR = {
    InterventionType.SILENT_AWARENESS: 20,
    InterventionType.SUBTLE_HINT: 10,
    InterventionType.PROACTIVE_SUGGESTION: 4,
    InterventionType.CELEBRATION: 3,
    InterventionType.ENCOURAGEMENT: 6,
    InterventionType.CHECK_IN: 3,
    InterventionType.BREAK_REMINDER: 2,
    InterventionType.CONTEXT_QUERY: 5,
}

# Hours after which a goal is considered "stale" if no activity
_GOAL_STALE_HOURS = 4


# =============================================================
# CONTEXT TRACKER
# =============================================================

class ContextSnapshot:
    """
    A snapshot of everything the companion knows at a moment in time.
    This is the unified context object.
    """
    __slots__ = (
        "timestamp", "activity_type", "window_title", "process_name",
        "activity_duration_minutes", "session_duration_minutes",
        "idle_minutes", "user_state", "companion_mood",
        "active_goals", "recent_achievements",
        "conversation_count", "last_interaction_time",
        "is_processing", "is_voice_active",
        "hour_of_day", "day_of_week",
        # Mission context
        "active_missions", "current_mission", "mission_progress",
        "mission_next_action", "mission_deadline_soon",
    )

    def __init__(self):
        self.timestamp: float = time.time()
        self.activity_type: str = "unknown"
        self.window_title: str = ""
        self.process_name: str = ""
        self.activity_duration_minutes: float = 0.0
        self.session_duration_minutes: float = 0.0
        self.idle_minutes: float = 0.0
        self.user_state: UserState = UserState.UNKNOWN
        self.companion_mood: CompanionMood = CompanionMood.NEUTRAL
        self.active_goals: list = []
        self.recent_achievements: list = []
        self.conversation_count: int = 0
        self.last_interaction_time: float = 0.0
        self.is_processing: bool = False
        self.is_voice_active: bool = False
        self.hour_of_day: int = 0
        self.day_of_week: int = 0
        # Mission context
        self.active_missions: list = []
        self.current_mission: dict = None
        self.mission_progress: float = 0.0
        self.mission_next_action: dict = None
        self.mission_deadline_soon: bool = False

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "activity_type": self.activity_type,
            "window_title": self.window_title[:100] if self.window_title else "",
            "activity_duration_minutes": round(self.activity_duration_minutes, 1),
            "session_duration_minutes": round(self.session_duration_minutes, 1),
            "idle_minutes": round(self.idle_minutes, 1),
            "user_state": self.user_state.value,
            "companion_mood": self.companion_mood.value,
            "active_goals": self.active_goals[:5],
            "recent_achievements": self.recent_achievements[:3],
            "conversation_count": self.conversation_count,
            "hour_of_day": self.hour_of_day,
        }


class ContextTracker:
    """
    Tracks and maintains context over time.
    Uses the ActivityMonitor as input but adds higher-level inference.
    """

    def __init__(self, activity_monitor=None):
        self._activity_monitor = activity_monitor
        self._lock = threading.RLock()

        # Context history (ring buffer, last 100 snapshots)
        self._history: list[ContextSnapshot] = []
        self._max_history = 100

        # Current snapshot (updated every cycle)
        self._current: ContextSnapshot = ContextSnapshot()

        # Accumulated stats
        self._activity_log: list[dict] = []          # activity transitions
        self._max_activity_log = 50
        self._session_activities: dict[str, float] = {}  # activity -> total minutes
        self._session_start: float = time.time()
        self._last_interaction: float = time.time()
        self._conversation_count: int = 0

        # User state inference
        self._user_state_history: list[tuple[float, UserState]] = []
        self._stuck_counters: dict[str, int] = {}
        self._break_start: Optional[float] = None

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, activity_type: str, window_title: str = "",
               process_name: str = "", idle_minutes: float = 0.0,
               is_processing: bool = False, is_voice_active: bool = False):
        """
        Main update call - called every monitor cycle.
        Analyzes new input and updates the context snapshot.
        """
        with self._lock:
            now = time.time()
            snapshot = ContextSnapshot()
            snapshot.timestamp = now
            snapshot.activity_type = activity_type
            snapshot.window_title = window_title
            snapshot.process_name = process_name
            snapshot.idle_minutes = idle_minutes
            snapshot.session_duration_minutes = (now - self._session_start) / 60.0
            snapshot.is_processing = is_processing
            snapshot.is_voice_active = is_voice_active
            snapshot.hour_of_day = datetime.now().hour
            snapshot.day_of_week = datetime.now().weekday()
            snapshot.conversation_count = self._conversation_count
            snapshot.last_interaction_time = self._last_interaction

            # Compute activity duration
            snapshot.activity_duration_minutes = self._compute_activity_duration(
                activity_type, now
            )

            # Update session activity totals
            if activity_type not in self._session_activities:
                self._session_activities[activity_type] = 0.0
            self._session_activities[activity_type] += 0.1  # ~ per cycle

            # Track activity transitions
            prev_type = self._current.activity_type if self._current else None
            if prev_type and prev_type != activity_type:
                self._activity_log.append({
                    "from": prev_type,
                    "to": activity_type,
                    "time": now,
                })
                if len(self._activity_log) > self._max_activity_log:
                    self._activity_log.pop(0)

            # Infer user state
            snapshot.user_state = self._infer_user_state(
                activity_type, idle_minutes, window_title, process_name
            )

            # Carry over goals and achievements
            snapshot.active_goals = list(self._current.active_goals) if self._current else []
            snapshot.recent_achievements = list(self._current.recent_achievements) if self._current else []

            # =========================================================
            # MISSION CONTEXT INTEGRATION
            # =========================================================
            try:
                from mission_tracker import get_mission_tracker
                tracker = get_mission_tracker()
                active_missions = tracker.get_active_missions()
                snapshot.active_missions = [m.title for m in active_missions[:3]]

                if active_missions:
                    # Get highest priority mission as current
                    current = max(active_missions, key=lambda m: m.priority)
                    snapshot.current_mission = {
                        "id": current.id,
                        "title": current.title,
                        "progress": current.calculate_progress(),
                    }
                    snapshot.mission_progress = current.calculate_progress()

                    # Get next action
                    next_action = tracker.get_next_action(current.id)
                    if next_action:
                        snapshot.mission_next_action = next_action

                    # Check if deadline is approaching
                    if current.deadline:
                        hours_until = (current.deadline - now) / 3600
                        if hours_until < 24:
                            snapshot.mission_deadline_soon = True
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"Mission context error: {e}")

            # Store in history
            self._history.append(snapshot)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            self._current = snapshot

    def _compute_activity_duration(self, activity_type: str, now: float) -> float:
        """How long the user has been in this activity."""
        if not self._activity_log:
            return (now - self._session_start) / 60.0

        # Find when current activity started
        for entry in reversed(self._activity_log):
            if entry["to"] == activity_type:
                return (now - entry["time"]) / 60.0

        # Fallback: from session start
        return (now - self._session_start) / 60.0

    def _infer_user_state(self, activity_type: str, idle_minutes: float,
                          window_title: str, process_name: str) -> UserState:
        """
        Locally infer the user's state from context.
        No AI calls needed.
        """
        # Idle detection
        if idle_minutes > 1.0:
            if idle_minutes > 5.0:
                # Been away for a while - likely on break or stepped away
                self._break_start = self._break_start or time.time()
                return UserState.ON_BREAK
            self._break_start = None
            return UserState.IDLE

        self._break_start = None

        # Activity-based inference
        if activity_type == "coding":
            combined = (window_title + " " + process_name).lower()

            # Check for stuck indicators (debugger, error, etc.)
            stuck_keywords = ["error", "exception", "failed", "bug", "fix",
                              "debug", "stack trace", "crash", "not working",
                              "why", "problem", "issue", "broken"]
            if any(kw in combined for kw in stuck_keywords):
                self._stuck_counters["coding"] = self._stuck_counters.get("coding", 0) + 1
                if self._stuck_counters["coding"] > 3:
                    return UserState.STUCK
            else:
                self._stuck_counters["coding"] = max(0, self._stuck_counters.get("coding", 0) - 1)

            # Check for focus indicators
            if not any(kw in combined for kw in ["youtube", "music", "browser"]):
                if self._compute_activity_duration("coding", time.time()) > 10:
                    return UserState.FOCUSED
                return UserState.CREATING

        elif activity_type == "browsing":
            combined = (window_title + " " + process_name).lower()
            research_keywords = ["documentation", "docs", "tutorial", "guide",
                                 "learn", "how to", "reference", "api",
                                 "stackoverflow", "github", "wiki"]
            if any(kw in combined for kw in research_keywords):
                return UserState.LEARNING
            return UserState.EXPLORING

        elif activity_type == "studying":
            return UserState.LEARNING

        elif activity_type == "watching_videos":
            return UserState.EXPLORING

        elif activity_type == "gaming":
            return UserState.FOCUSED

        elif activity_type == "working":
            return UserState.FOCUSED

        elif activity_type == "idle":
            return UserState.IDLE

        return UserState.UNKNOWN

    # =========================================================
    # INTERACTION TRACKING
    # =========================================================

    def record_interaction(self):
        """Called when user sends a message or interacts."""
        with self._lock:
            self._last_interaction = time.time()
            self._conversation_count += 1

    def get_snapshot(self) -> ContextSnapshot:
        """Get the current context snapshot (thread-safe copy)."""
        with self._lock:
            return self._current

    def get_history(self, count: int = 10) -> list[ContextSnapshot]:
        """Get recent context history."""
        with self._lock:
            return list(self._history[-count:])

    def get_session_summary(self) -> dict:
        """Get a summary of the current session."""
        with self._lock:
            duration = (time.time() - self._session_start) / 60.0
            top_activities = sorted(
                self._session_activities.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            return {
                "duration_minutes": round(duration, 1),
                "activities": {k: round(v, 1) for k, v in top_activities},
                "conversations": self._conversation_count,
                "transitions": len(self._activity_log),
            }


# =============================================================
# EMOTION ENGINE
# =============================================================

class EmotionEngine:
    """
    Drives the companion's emotional state based on context.
    Emotions evolve naturally—not randomly. They have:
      - Intensity (0.0 to 1.0)
      - Decay over time
      - Transitions based on context changes
      - Personality influence
    """

    # Mood transition rules: (current_mood, context_trigger) -> new_mood
    _TRANSITION_RULES = {
        # User is coding/focused -> companion is calm or curious
        (CompanionMood.NEUTRAL, UserState.FOCUSED): CompanionMood.CALM,
        (CompanionMood.HAPPY, UserState.FOCUSED): CompanionMood.CALM,
        (CompanionMood.EXCITED, UserState.FOCUSED): CompanionMood.THOUGHTFUL,
        (CompanionMood.PLAYFUL, UserState.FOCUSED): CompanionMood.THOUGHTFUL,

        # User is stuck -> companion is concerned or thoughtful
        (CompanionMood.NEUTRAL, UserState.STUCK): CompanionMood.THOUGHTFUL,
        (CompanionMood.CALM, UserState.STUCK): CompanionMood.CONCERNED,
        (CompanionMood.HAPPY, UserState.STUCK): CompanionMood.CONCERNED,
        (CompanionMood.THOUGHTFUL, UserState.STUCK): CompanionMood.CONCERNED,

        # User is succeeding -> companion is proud or happy
        (CompanionMood.NEUTRAL, UserState.SUCCEEDING): CompanionMood.PROUD,
        (CompanionMood.THOUGHTFUL, UserState.SUCCEEDING): CompanionMood.HAPPY,
        (CompanionMood.CONCERNED, UserState.SUCCEEDING): CompanionMood.HAPPY,
        (CompanionMood.CALM, UserState.SUCCEEDING): CompanionMood.PROUD,

        # User is learning -> companion is curious
        (CompanionMood.NEUTRAL, UserState.LEARNING): CompanionMood.CURIOUS,
        (CompanionMood.CALM, UserState.LEARNING): CompanionMood.CURIOUS,
        (CompanionMood.THOUGHTFUL, UserState.LEARNING): CompanionMood.CURIOUS,

        # User is creating -> companion is excited or curious
        (CompanionMood.NEUTRAL, UserState.CREATING): CompanionMood.CURIOUS,
        (CompanionMood.CALM, UserState.CREATING): CompanionMood.CURIOUS,
        (CompanionMood.THOUGHTFUL, UserState.CREATING): CompanionMood.EXCITED,

        # User on break -> companion is neutral/calm
        (CompanionMood.NEUTRAL, UserState.ON_BREAK): CompanionMood.SLEEPY,
        (CompanionMood.CALM, UserState.ON_BREAK): CompanionMood.SLEEPY,
        (CompanionMood.CURIOUS, UserState.ON_BREAK): CompanionMood.NEUTRAL,

        # User idle -> companion goes neutral/sleepy over time
        (CompanionMood.NEUTRAL, UserState.IDLE): CompanionMood.NEUTRAL,
        (CompanionMood.CALM, UserState.IDLE): CompanionMood.SLEEPY,

        # User frustrated -> companion is sympathetic
        (CompanionMood.NEUTRAL, UserState.FRUSTRATED): CompanionMood.SYMPATHETIC,
        (CompanionMood.CALM, UserState.FRUSTRATED): CompanionMood.SYMPATHETIC,
        (CompanionMood.CONCERNED, UserState.FRUSTRATED): CompanionMood.SYMPATHETIC,

        # User exploring/browsing -> companion is curious or playful
        (CompanionMood.NEUTRAL, UserState.EXPLORING): CompanionMood.CURIOUS,
        (CompanionMood.CALM, UserState.EXPLORING): CompanionMood.CURIOUS,
        (CompanionMood.THOUGHTFUL, UserState.EXPLORING): CompanionMood.PLAYFUL,

        # User distracted -> companion is thoughtful
        (CompanionMood.NEUTRAL, UserState.DISTRACTED): CompanionMood.THOUGHTFUL,
        (CompanionMood.CALM, UserState.DISTRACTED): CompanionMood.CURIOUS,
    }

    def __init__(self, personality: str = "friendly"):
        self._lock = threading.RLock()
        self._current_mood: CompanionMood = CompanionMood.NEUTRAL
        self._previous_mood: CompanionMood = CompanionMood.NEUTRAL
        self._intensity: float = 0.5
        self._personality = personality

        # Mood history for decay
        self._mood_history: list[tuple[float, CompanionMood, float]] = []
        self._max_mood_history = 50

        # Decay settings
        self._decay_rate = 0.02          # per update
        self._intensity_decay = 0.01     # per update
        self._minimum_intensity = 0.1

        # Sustained mood tracking (to avoid rapid flickering)
        self._mood_stability_counter: dict[CompanionMood, int] = {}
        self._stability_threshold = 3     # cycles before mood change applies

        # Personality influence
        self._personality_bias = self._get_personality_bias(personality)

    def _get_personality_bias(self, personality: str) -> dict:
        """Get personality-driven mood biases."""
        biases = {
            "friendly": {"base_mood": CompanionMood.HAPPY, "bounce_back": 0.7},
            "professional": {"base_mood": CompanionMood.CALM, "bounce_back": 0.4},
            "funny": {"base_mood": CompanionMood.PLAYFUL, "bounce_back": 0.8},
            "calm": {"base_mood": CompanionMood.CALM, "bounce_back": 0.3},
            "friendly_bro": {"base_mood": CompanionMood.EXCITED, "bounce_back": 0.9},
        }
        return biases.get(personality, {"base_mood": CompanionMood.NEUTRAL, "bounce_back": 0.6})

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, user_state: UserState, context: ContextSnapshot) -> CompanionMood:
        """
        Update emotional state based on user state and context.
        Returns the current mood after update.
        """
        with self._lock:
            # Natural decay
            self._intensity = max(
                self._minimum_intensity,
                self._intensity - self._intensity_decay
            )

            # If intensity is very low, drift toward base mood
            if self._intensity < 0.2 and self._current_mood != self._personality_bias["base_mood"]:
                self._current_mood = self._personality_bias["base_mood"]
                self._intensity = 0.3

            # Check for transition
            transition_key = (self._current_mood, user_state)
            if transition_key in self._TRANSITION_RULES:
                new_mood = self._TRANSITION_RULES[transition_key]

                # Stability check: don't flicker
                self._mood_stability_counter[new_mood] = self._mood_stability_counter.get(new_mood, 0) + 1

                if self._mood_stability_counter[new_mood] >= self._stability_threshold:
                    if new_mood != self._current_mood:
                        self._previous_mood = self._current_mood
                        self._current_mood = new_mood
                        self._intensity = min(1.0, self._intensity + 0.3)

                        # Log transition
                        self._mood_history.append((time.time(), new_mood, self._intensity))
                        if len(self._mood_history) > self._max_mood_history:
                            self._mood_history.pop(0)

                    # Reset stability counter for other moods
                    for mood in list(self._mood_stability_counter.keys()):
                        if mood != new_mood:
                            self._mood_stability_counter[mood] = 0
            else:
                # No rule matches — drift toward base mood if not already there
                if self._current_mood != self._personality_bias["base_mood"]:
                    base = self._personality_bias["base_mood"]
                    # Gradually drift
                    if random.random() < 0.1:
                        self._previous_mood = self._current_mood
                        self._current_mood = base
                        self._intensity = max(0.3, self._intensity)

            # Time-of-day influence
            hour = context.hour_of_day
            if hour >= 22 or hour <= 5:
                # Night time - drift toward sleepy/calm
                if self._current_mood not in (CompanionMood.SLEEPY, CompanionMood.CALM, CompanionMood.NEUTRAL):
                    if random.random() < 0.05:
                        self._current_mood = CompanionMood.CALM
                        self._intensity = max(0.2, self._intensity * 0.8)

            return self._current_mood

    # =========================================================
    # QUERIES
    # =========================================================

    @property
    def mood(self) -> CompanionMood:
        with self._lock:
            return self._current_mood

    @property
    def intensity(self) -> float:
        with self._lock:
            return self._intensity

    def get_mood_history(self) -> list:
        with self._lock:
            return list(self._mood_history[-20:])

    def boost(self, amount: float = 0.3):
        """Temporarily boost emotional intensity (e.g., on achievement)."""
        with self._lock:
            self._intensity = min(1.0, self._intensity + amount)

    def set_mood(self, mood: CompanionMood, intensity: float = 0.7):
        """Directly set mood (for external events like user praise)."""
        with self._lock:
            self._previous_mood = self._current_mood
            self._current_mood = mood
            self._intensity = max(0.3, min(1.0, intensity))
            self._mood_stability_counter = {mood: self._stability_threshold}

    def map_to_character_expression(self) -> str:
        """Map companion mood to character.py expression name."""
        mapping = {
            CompanionMood.NEUTRAL: "idle",
            CompanionMood.HAPPY: "happy",
            CompanionMood.EXCITED: "excited",
            CompanionMood.CURIOUS: "curious",
            CompanionMood.CONCERNED: "thinking",
            CompanionMood.PROUD: "happy",
            CompanionMood.FRUSTRATED: "angry",
            CompanionMood.SYMPATHETIC: "sad",
            CompanionMood.PLAYFUL: "happy",
            CompanionMood.CALM: "idle",
            CompanionMood.THOUGHTFUL: "thinking",
            CompanionMood.SLEEPY: "sleepy",
            CompanionMood.SURPRISED: "surprised",
        }
        return mapping.get(self._current_mood, "idle")

    def map_to_activity_emotion(self) -> str:
        """Map companion mood to an emotion name for character.react()."""
        mapping = {
            CompanionMood.NEUTRAL: "idle",
            CompanionMood.HAPPY: "happy",
            CompanionMood.EXCITED: "excited",
            CompanionMood.CURIOUS: "curious",
            CompanionMood.CONCERNED: "thinking",
            CompanionMood.PROUD: "excited",
            CompanionMood.FRUSTRATED: "frustrated",
            CompanionMood.SYMPATHETIC: "sad",
            CompanionMood.PLAYFUL: "happy",
            CompanionMood.CALM: "idle",
            CompanionMood.THOUGHTFUL: "thinking",
            CompanionMood.SLEEPY: "sleepy",
            CompanionMood.SURPRISED: "surprised",
        }
        return mapping.get(self._current_mood, "idle")


# =============================================================
# GOAL TRACKER
# =============================================================

class GoalTracker:
    """
    Tracks what the user is working on and detects progress.
    Goals can be:
      - Explicit (user says "I'm working on X")
      - Implicit (detected from persistent coding/browsing patterns)
      - Self-correcting (goals expire after inactivity)
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._goals: list[dict] = []
        self._max_goals = 10
        self._achievements: list[dict] = []
        self._max_achievements = 50

    # =========================================================
    # GOAL MANAGEMENT
    # =========================================================

    def set_active_goal(self, description: str, category: str = "general",
                        context: Optional[dict] = None):
        """Set or update the current active goal."""
        with self._lock:
            now = time.time()

            # Check if this goal already exists
            for goal in self._goals:
                if goal["description"].lower() == description.lower():
                    goal["last_active"] = now
                    goal["updated_count"] = goal.get("updated_count", 0) + 1
                    goal["context"] = context or goal.get("context", {})
                    return

            # Add new goal
            self._goals.append({
                "description": description,
                "category": category,
                "created_at": now,
                "last_active": now,
                "progress": 0.0,         # 0.0 to 1.0
                "updated_count": 1,
                "context": context or {},
                "milestones": [],
                "completed": False,
            })

            # Enforce limit
            if len(self._goals) > self._max_goals:
                # Remove oldest inactive goal
                self._goals.sort(key=lambda g: g["last_active"])
                self._goals.pop(0)

    def update_goal_progress(self, description: str, progress_delta: float = 0.05):
        """Increment progress on a goal."""
        with self._lock:
            for goal in self._goals:
                if goal["description"].lower() == description.lower():
                    goal["progress"] = min(1.0, goal["progress"] + progress_delta)
                    goal["last_active"] = time.time()

                    # Check for milestones
                    old_milestone = int((goal["progress"] - progress_delta) * 10)
                    new_milestone = int(goal["progress"] * 10)
                    if new_milestone > old_milestone and new_milestone in (3, 5, 8, 10):
                        goal["milestones"].append({
                            "level": new_milestone,
                            "time": time.time(),
                        })

                    # Check completion
                    if goal["progress"] >= 1.0 and not goal["completed"]:
                        goal["completed"] = True
                        goal["completed_at"] = time.time()
                        return True  # signal achievement
                    return False

    def complete_goal(self, description: str) -> bool:
        """Mark a goal as completed."""
        with self._lock:
            for goal in self._goals:
                if goal["description"].lower() == description.lower():
                    if not goal["completed"]:
                        goal["completed"] = True
                        goal["completed_at"] = time.time()
                        goal["progress"] = 1.0
                        return True
                    return False
            return False

    def get_active_goals(self) -> list[dict]:
        """Get goals that are not completed and not stale."""
        with self._lock:
            now = time.time()
            active = []
            for goal in self._goals:
                if goal["completed"]:
                    continue
                # Check staleness
                hours_since = (now - goal["last_active"]) / 3600.0
                if hours_since > _GOAL_STALE_HOURS:
                    continue
                active.append(dict(goal))
            return active

    def get_goal_by_index(self, index: int = 0) -> Optional[dict]:
        """Get the most recent active goal, or by index."""
        goals = self.get_active_goals()
        if not goals:
            return None
        if index < len(goals):
            return goals[-1 - index]  # newest first
        return None

    # =========================================================
    # ACHIEVEMENTS
    # =========================================================

    def add_achievement(self, title: str, description: str,
                        category: str = "general", importance: float = 0.5):
        """Record an achievement."""
        with self._lock:
            self._achievements.append({
                "title": title,
                "description": description,
                "category": category,
                "importance": max(0.0, min(1.0, importance)),
                "time": time.time(),
            })
            if len(self._achievements) > self._max_achievements:
                self._achievements.pop(0)

    def get_recent_achievements(self, count: int = 5) -> list[dict]:
        """Get most recent achievements."""
        with self._lock:
            return list(self._achievements[-count:])

    def has_recent_achievement(self, minutes: int = 5) -> bool:
        """Check if there's a very recent achievement."""
        with self._lock:
            if not self._achievements:
                return False
            cutoff = time.time() - (minutes * 60)
            return self._achievements[-1]["time"] >= cutoff


# =============================================================
# PROACTIVE SUGGESTION ENGINE
# =============================================================

class ProactiveSuggester:
    """
    Generates contextually appropriate suggestions and messages.
    Uses local logic first. Only calls AI for complex reasoning.

    The engine works on a confidence-scoring system:
      - Each potential intervention is scored (0.0 to 1.0)
      - Only interventions above the threshold fire
      - Cooldowns prevent repetition
      - Personality modifies the message style
    """

    def __init__(self, personality: str = "friendly"):
        self._personality = personality
        self._cooldowns: dict[str, float] = {}  # key -> timestamp
        self._intervention_counts: dict[str, int] = {}  # key -> count in current hour
        self._last_hour_check: float = time.time()

        # Context-aware suggestions by activity + user state
        self._suggestion_templates = self._build_suggestion_templates()

    def _build_suggestion_templates(self) -> dict:
        """Build local suggestion templates. No AI needed for these."""
        return {
            ("coding", UserState.STUCK): {
                "message": "Looks like you're stuck on something bro. Want me to help debug that?",
                "alternatives": [
                    "I can see you're hitting a wall. Want a fresh pair of eyes?",
                    "Debugging time? I'm pretty good at catching typos 😅",
                    "Stuck on something? Describe it and I'll help figure it out!",
                ],
                "character_emotion": "thinking",
                "type": InterventionType.CONTEXT_QUERY,
            },
            ("coding", UserState.FOCUSED): {
                "message": None,  # Silent awareness when focused
                "character_emotion": "calm",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("coding", UserState.CREATING): {
                "message": None,  # Let them create
                "character_emotion": "curious",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("coding", UserState.SUCCEEDING): {
                "message": "Yo that code's looking clean! 🔥 Let me know if you need a review.",
                "alternatives": [
                    "Build is looking solid! You're on a roll 🚀",
                    "Nice work bro! That's coming together well.",
                ],
                "character_emotion": "happy",
                "type": InterventionType.CELEBRATION,
            },
            ("coding", UserState.LEARNING): {
                "message": "Learning some new coding concepts? I can help explain stuff!",
                "character_emotion": "curious",
                "type": InterventionType.SUBTLE_HINT,
            },
            ("studying", UserState.LEARNING): {
                "message": "Studying hard bro! 📚 Want me to quiz you or explain something?",
                "alternatives": [
                    "Learning mode activated! Need help summarizing?",
                    "You're putting in work! I can help with flashcards if you want.",
                ],
                "character_emotion": "curious",
                "type": InterventionType.CONTEXT_QUERY,
            },
            ("studying", UserState.FOCUSED): {
                "message": None,  # Silent
                "character_emotion": "calm",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("studying", UserState.STUCK): {
                "message": "Getting stuck on something? I can help explain it differently.",
                "character_emotion": "thinking",
                "type": InterventionType.ENCOURAGEMENT,
            },
            ("browsing", UserState.LEARNING): {
                "message": "Doing some research? Need me to summarize anything?",
                "alternatives": [
                    "Found anything interesting? I can take notes for you.",
                    "Research mode! Need help organizing what you find?",
                ],
                "character_emotion": "curious",
                "type": InterventionType.SUBTLE_HINT,
            },
            ("browsing", UserState.EXPLORING): {
                "message": None,  # Silent - just browsing
                "character_emotion": "curious",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("watching_videos", UserState.EXPLORING): {
                "message": None,  # Don't interrupt videos
                "character_emotion": "neutral",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("gaming", UserState.FOCUSED): {
                "message": None,  # Don't interrupt gaming
                "character_emotion": "excited",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("working", UserState.FOCUSED): {
                "message": None,  # Silent when working
                "character_emotion": "calm",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("idle", UserState.IDLE): {
                "message": None,
                "character_emotion": "sleepy",
                "type": InterventionType.SILENT_AWARENESS,
            },
            ("idle", UserState.ON_BREAK): {
                "message": None,  # Let them take a break
                "character_emotion": "sleepy",
                "type": InterventionType.SILENT_AWARENESS,
            },
        }

    # =========================================================
    # SCORING
    # =========================================================

    def score_intervention(self, context: ContextSnapshot,
                           mood: CompanionMood) -> tuple[Optional[InterventionType], float]:
        """
        Score potential interventions.
        Returns (best_intervention_type, confidence_score).
        """
        activity = context.activity_type
        user_state = context.user_state
        now = time.time()

        # Reset hourly counts if needed
        if now - self._last_hour_check > 3600:
            self._intervention_counts.clear()
            self._last_hour_check = now

        # Check if there's a direct template match
        template_key = (activity, user_state)
        if template_key not in self._suggestion_templates:
            # Fall back to generic
            template = self._get_generic_suggestion(user_state)
        else:
            template = self._suggestion_templates[template_key]

        intervention_type = template.get("type", InterventionType.SILENT_AWARENESS)

        # Base confidence
        base_confidence = 0.5

        # Boost from context
        if context.activity_duration_minutes > 30:
            base_confidence += 0.1  # Been at this a while
        if context.session_duration_minutes > 60:
            base_confidence += 0.05  # Long session

        # Mood influence
        mood_boost = {
            CompanionMood.HAPPY: 0.05,
            CompanionMood.EXCITED: 0.1,
            CompanionMood.CONCERNED: 0.1,
            CompanionMood.PROUD: 0.15,
            CompanionMood.THOUGHTFUL: 0.1,
            CompanionMood.SYMPATHETIC: 0.1,
            CompanionMood.CURIOUS: 0.05,
        }
        base_confidence += mood_boost.get(mood, 0.0)

        # If message is None, it's silent awareness - always allowed but lower confidence
        if template.get("message") is None:
            confidence = 0.4
            return InterventionType.SILENT_AWARENESS, confidence

        # Cooldown penalty
        cooldown_key = f"{activity}_{user_state}"
        last_time = self._cooldowns.get(cooldown_key, 0)
        time_since = now - last_time
        required_cd = _COOLDOWN_DEFAULTS.get(intervention_type, 300)

        if time_since < required_cd:
            cooldown_factor = time_since / required_cd
            base_confidence *= cooldown_factor

        # Hourly rate limiting
        type_key = intervention_type.value
        hourly_count = self._intervention_counts.get(type_key, 0)
        max_hourly = _MAX_INTERVENTIONS_PER_HOUR.get(intervention_type, 10)
        if hourly_count >= max_hourly:
            base_confidence *= 0.1  # Almost never

        # User state boost
        if user_state == UserState.STUCK:
            base_confidence += 0.2  # More likely to offer help
        elif user_state == UserState.FRUSTRATED:
            base_confidence += 0.15
        elif user_state == UserState.SUCCEEDING:
            base_confidence += 0.1

        # Idle penalty
        if user_state in (UserState.IDLE, UserState.ON_BREAK):
            base_confidence *= 0.3

        # Clamp
        confidence = max(0.0, min(1.0, base_confidence))

        return intervention_type, confidence

    def _get_generic_suggestion(self, user_state: UserState) -> dict:
        """Fallback suggestions when no specific template matches."""
        generic = {
            UserState.FOCUSED: {
                "message": None,
                "character_emotion": "calm",
                "type": InterventionType.SILENT_AWARENESS,
            },
            UserState.STUCK: {
                "message": "Everything okay? Need a hand with anything? 🤔",
                "character_emotion": "thinking",
                "type": InterventionType.CHECK_IN,
            },
            UserState.SUCCEEDING: {
                "message": "Nice! Things are going well 😄",
                "character_emotion": "happy",
                "type": InterventionType.ENCOURAGEMENT,
            },
            UserState.LEARNING: {
                "message": "Learning something new? That's awesome! 🧠",
                "character_emotion": "curious",
                "type": InterventionType.SUBTLE_HINT,
            },
            UserState.CREATING: {
                "message": None,
                "character_emotion": "curious",
                "type": InterventionType.SILENT_AWARENESS,
            },
            UserState.EXPLORING: {
                "message": "Exploring? Let me know if you need info!",
                "character_emotion": "curious",
                "type": InterventionType.SUBTLE_HINT,
            },
            UserState.IDLE: {
                "message": None,
                "character_emotion": "sleepy",
                "type": InterventionType.SILENT_AWARENESS,
            },
            UserState.ON_BREAK: {
                "message": None,
                "character_emotion": "sleepy",
                "type": InterventionType.SILENT_AWARENESS,
            },
            UserState.FRUSTRATED: {
                "message": "That looks frustrating bro 😅 Want me to help figure it out?",
                "character_emotion": "sympathetic",
                "type": InterventionType.CHECK_IN,
            },
            UserState.DISTRACTED: {
                "message": "Everything good? Need to refocus? 🎯",
                "character_emotion": "thoughtful",
                "type": InterventionType.CHECK_IN,
            },
            UserState.UNKNOWN: {
                "message": None,
                "character_emotion": "neutral",
                "type": InterventionType.SILENT_AWARENESS,
            },
        }
        return generic.get(user_state, {
            "message": None,
            "character_emotion": "neutral",
            "type": InterventionType.SILENT_AWARENESS,
        })

    # =========================================================
    # INTERVENTION
    # =========================================================

    def get_suggestion(self, context: ContextSnapshot,
                       mood: CompanionMood) -> Optional[dict]:
        """
        Get the best suggestion for the current context.
        Returns None if no intervention is appropriate.
        Returns a dict with keys: message, character_emotion, type, confidence
        """
        intervention_type, confidence = self.score_intervention(context, mood)
        threshold = _CONFIDENCE_THRESHOLDS.get(intervention_type, 0.5)

        if confidence < threshold:
            return None

        # Get the template
        template_key = (context.activity_type, context.user_state)
        if template_key not in self._suggestion_templates:
            template = self._get_generic_suggestion(context.user_state)
        else:
            template = self._suggestion_templates[template_key]

        # Pick message
        message = template.get("message")
        alternatives = template.get("alternatives", [])

        # If silent awareness or no message, return animation-only
        if message is None or intervention_type == InterventionType.SILENT_AWARENESS:
            return {
                "message": None,
                "character_emotion": template.get("character_emotion", "neutral"),
                "type": InterventionType.SILENT_AWARENESS,
                "confidence": confidence,
            }

        # Personality modify message
        message = self._apply_personality(message, alternatives)

        # Record cooldown
        cooldown_key = f"{context.activity_type}_{context.user_state}"
        self._cooldowns[cooldown_key] = time.time()
        type_key = intervention_type.value
        self._intervention_counts[type_key] = self._intervention_counts.get(type_key, 0) + 1

        return {
            "message": message,
            "character_emotion": template.get("character_emotion", "neutral"),
            "type": intervention_type,
            "confidence": confidence,
        }

    def _apply_personality(self, message: str, alternatives: list) -> str:
        """Modify message tone based on personality."""
        # Just pick from alternatives sometimes for variety
        if alternatives and random.random() < 0.5:
            return random.choice(alternatives)
        return message

    def get_break_reminder(self, context: ContextSnapshot) -> Optional[dict]:
        """
        Check if a break reminder is appropriate.
        Only for long continuous sessions.
        """
        if context.activity_duration_minutes < 45:
            return None

        # Check if they're focused on something intensive
        if context.user_state in (UserState.FOCUSED, UserState.CREATING, UserState.STUCK):
            return {
                "message": "You've been at it for a while bro! Maybe take a short break? 🧘",
                "character_emotion": "concerned",
                "type": InterventionType.BREAK_REMINDER,
                "confidence": 0.6,
            }

        return None


# =============================================================
# SESSION MEMORY
# =============================================================

class SessionMemory:
    """
    Remembers meaningful events during the current session.
    Used for natural continuity in companion reactions.
    """
    def __init__(self, max_events: int = 50):
        self._events: list[dict] = []
        self._max = max_events
        self._lock = threading.RLock()

    def record(self, event_type: str, description: str, metadata: dict = None):
        with self._lock:
            self._events.append({
                "type": event_type,
                "description": description,
                "metadata": metadata or {},
                "timestamp": time.time(),
            })
            if len(self._events) > self._max:
                self._events.pop(0)

    def get_recent(self, count: int = 5) -> list[dict]:
        with self._lock:
            return list(self._events[-count:])

    def get_by_type(self, event_type: str) -> list[dict]:
        with self._lock:
            return [e for e in self._events if e.get("type") == event_type]

    def has_recent(self, event_type: str, within_seconds: float = 600) -> bool:
        with self._lock:
            now = time.time()
            return any(
                e.get("type") == event_type and (now - e.get("timestamp", 0)) < within_seconds
                for e in self._events
            )

    def clear(self):
        with self._lock:
            self._events.clear()


# =============================================================
# COOLDOWN MANAGER
# =============================================================

class CooldownManager:
    """
    Manages cooldowns for companion interventions.
    Prevents spam and ensures natural timing.
    """
    def __init__(self):
        self._cooldowns: dict[str, float] = {}
        self._last_hour_check: float = time.time()
        self._hourly_counts: dict[str, int] = {}

    def allow(self, key: str, cooldown_seconds: float, max_per_hour: int = 10) -> bool:
        """Check if an intervention is allowed based on cooldowns."""
        now = time.time()
        if now - self._last_hour_check > 3600:
            self._hourly_counts.clear()
            self._last_hour_check = now

        last_time = self._cooldowns.get(key, 0)
        if now - last_time < cooldown_seconds:
            return False

        count = self._hourly_counts.get(key, 0)
        if count >= max_per_hour:
            return False

        self._cooldowns[key] = now
        self._hourly_counts[key] = count + 1
        return True

    def reset(self, key: str):
        """Force reset a cooldown."""
        self._cooldowns.pop(key, None)


# =============================================================
# CONTEXTUAL DIALOGUE GENERATOR
# =============================================================

class ContextualDialogueGenerator:
    """
    Generates speech based on REAL detected context, not random questions.
    Uses activity type, window title, process, errors, successes, and time.
    """
    def __init__(self, personality: str = "friendly"):
        self._personality = personality
        self._recent_contexts: list[str] = []
        self._max_recent = 20

    def generate(self, context: ContextSnapshot) -> Optional[dict]:
        """
        Generate a contextually appropriate dialogue entry.
        Returns dict with keys: message, character_emotion, type.
        """
        activity = context.activity_type
        process = context.process_name.lower()
        title = context.window_title.lower()
        state = context.user_state
        duration = context.activity_duration_minutes
        session = context.session_duration_minutes

        ctx_key = f"{activity}_{process[:20]}_{title[:20]}"
        if ctx_key in self._recent_contexts:
            return None
        self._recent_contexts.append(ctx_key)
        if len(self._recent_contexts) > self._max_recent:
            self._recent_contexts.pop(0)

        # CODING CONTEXTS
        if activity == "coding":
            if state == UserState.STUCK:
                return self._pick({
                    "message": random.choice([
                        "I see you fighting something in the code 😭 Want a hand debugging?",
                        "That error is stubborn, bro. Want me to take a look?",
                        "Stuck on a bug? Describe it and I'll help you squash it 🐛",
                    ]),
                    "emotion": "thinking",
                    "type": InterventionType.CONTEXT_QUERY,
                })
            if state == UserState.SUCCEEDING:
                return self._pick({
                    "message": random.choice([
                        "YOOOO 🔥 you fixed it! That's awesome!",
                        "Build passing? You're on fire today 🚀",
                        "Code's looking clean! Great work bro 💪",
                    ]),
                    "emotion": "happy",
                    "type": InterventionType.CELEBRATION,
                })
            if duration > 35:
                return self._pick({
                    "message": random.choice([
                        "Bro, you've been coding for a while 😭 Tiny break? 👀",
                        "Keyboard warrior! Take a 2-minute breather, you've earned it 🧘",
                        "Focus mode is strong, but don't forget to stretch! 💻🧘",
                    ]),
                    "emotion": "concerned",
                    "type": InterventionType.BREAK_REMINDER,
                })
            if "git" in process or "github" in process or "push" in title or "pull" in title:
                return self._pick({
                    "message": "Git operations detected 📦 Let me know if you need help with branches or merges!",
                    "emotion": "curious",
                    "type": InterventionType.SUBTLE_HINT,
                })
            if "error" in title or "exception" in title or "traceback" in title:
                return self._pick({
                    "message": "Error alert 🚨 Sounds painful. Want me to help figure out what's going on?",
                    "emotion": "sympathetic",
                    "type": InterventionType.CONTEXT_QUERY,
                })
            if "debug" in title or "debugging" in title:
                return self._pick({
                    "message": "Debug mode activated 🐛 I'm here if you need a second pair of eyes!",
                    "emotion": "thinking",
                    "type": InterventionType.SUBTLE_HINT,
                })

        # BROWSING CONTEXTS
        if activity == "browsing":
            if state == UserState.LEARNING:
                return self._pick({
                    "message": random.choice([
                        "Research mode? 📚 Want me to summarize anything you find?",
                        "Found anything juicy? I can help organize notes 👀",
                        "Deep dive time! Need help filtering out the noise? 🔍",
                    ]),
                    "emotion": "curious",
                    "type": InterventionType.SUBTLE_HINT,
                })
            if "youtube" in process:
                return self._pick({
                    "message": "YouTube rabbit hole? 🎬 No judgment, just let me know if you need info!",
                    "emotion": "playful",
                    "type": InterventionType.SUBTLE_HINT,
                })
            if "shopping" in title or "amazon" in process or "ebay" in process:
                return self._pick({
                    "message": "Shopping time? 🛒 Want me to compare anything or keep you company?",
                    "emotion": "playful",
                    "type": InterventionType.SUBTLE_HINT,
                })

        # STUDYING CONTEXTS
        if activity == "studying":
            if state == UserState.FOCUSED:
                return self._pick({
                    "message": None,
                    "emotion": "calm",
                    "type": InterventionType.SILENT_AWARENESS,
                })
            if state == UserState.STUCK:
                return self._pick({
                    "message": random.choice([
                        "This concept is fighting back 😤 Want me to explain it differently?",
                        "Stuck on a topic? I can break it down in a totally different way!",
                    ]),
                    "emotion": "thinking",
                    "type": InterventionType.ENCOURAGEMENT,
                })
            if "pdf" in process or "acrobat" in process or "reader" in process:
                return self._pick({
                    "message": "PDF reading time 📖 Want me to explain anything from the document?",
                    "emotion": "curious",
                    "type": InterventionType.SUBTLE_HINT,
                })
            if "quiz" in title or "flashcard" in title or "anki" in process:
                return self._pick({
                    "message": "Study session in progress! You crushing it or wanna quiz some more? 🧠",
                    "emotion": "excited",
                    "type": InterventionType.ENCOURAGEMENT,
                })

        # GAMING CONTEXTS
        if activity == "gaming":
            if state == UserState.FOCUSED:
                return self._pick({
                    "message": None,
                    "emotion": "excited",
                    "type": InterventionType.SILENT_AWARENESS,
                })
            if state == UserState.FRUSTRATED:
                return self._pick({
                    "message": "That game giving you a hard time? 😤 Tips incoming if you want!",
                    "emotion": "sympathetic",
                    "type": InterventionType.CONTEXT_QUERY,
                })
            if "minecraft" in process or "roblox" in process:
                return self._pick({
                    "message": random.choice([
                        "Building something cool? 🎮 Show me when you're done!",
                        "Gaming vibes! Just don't forget to hydrate 💧",
                    ]),
                    "emotion": "playful",
                    "type": InterventionType.SUBTLE_HINT,
                })

        # WORKING CONTEXTS
        if activity == "working":
            if state == UserState.FOCUSED:
                return self._pick({
                    "message": None,
                    "emotion": "calm",
                    "type": InterventionType.SILENT_AWARENESS,
                })
            if duration > 40:
                return self._pick({
                    "message": "Work grind is real 💼 Want me to set a focus timer or play some lo-fi?",
                    "emotion": "concerned",
                    "type": InterventionType.BREAK_REMINDER,
                })

        # IDLE / RETURN CONTEXTS
        if activity == "idle" and context.idle_minutes > 10:
            return self._pick({
                "message": random.choice([
                    "You vanished 👀 Everything okay?",
                    "Welcome back brooo 😄 What were we doing?",
                    "Back from the void! Need anything?",
                ]),
                "emotion": "happy",
                "type": InterventionType.CHECK_IN,
            })

        # LONG SESSION
        if session > 120:
            return self._pick({
                "message": "You've been at this for 2+ hours straight! 😭 I'm proud, but seriously, take a break!",
                "emotion": "concerned",
                "type": InterventionType.BREAK_REMINDER,
            })

        return None

    def _pick(self, options: list) -> dict:
        """Pick a random option from a list of possible dialogues."""
        if isinstance(options, dict):
            return options
        if not options:
            return {"message": None, "emotion": "neutral", "type": InterventionType.SILENT_AWARENESS}
        return random.choice(options)


# =============================================================
# COMPANION INTELLIGENCE - MAIN CONTROLLER
# =============================================================

class CompanionIntelligence:
    """
    The unified companion intelligence system.

    This is the main controller that ties together:
      - ContextTracker (what's happening)
      - EmotionEngine (how the companion feels)
      - GoalTracker (what the user is working on)
      - ProactiveSuggester (when/how to intervene)

    It operates on a polling cycle and produces "observations"
    that the rest of the app (character, chat, etc.) consumes.
    """

    def __init__(self, activity_monitor=None, personality: str = "friendly"):
        self._lock = threading.RLock()

        # Sub-systems
        self.context = ContextTracker(activity_monitor)
        self.emotion = EmotionEngine(personality)
        self.goals = GoalTracker()
        self.suggester = ProactiveSuggester(personality)
        self.dialogue_generator = ContextualDialogueGenerator(personality)
        self.cooldowns = CooldownManager()
        self.session_memory = SessionMemory()

        # Personality
        self._personality = personality

        # Observation callbacks
        self._emotion_callbacks: list[Callable] = []     # called on emotion change
        self._intervention_callbacks: list[Callable] = []  # called on intervention
        self._achievement_callbacks: list[Callable] = []   # called on achievement

        # Last observation
        self._last_observation: Optional[dict] = None

        # Anti-annoyance: track what we've done recently
        self._recent_interventions: list[dict] = []
        self._max_recent = 20

        # Cycle tracking
        self._cycle_count: int = 0
        self._last_detailed_analysis: float = 0
        self._detailed_analysis_interval: float = 60.0  # seconds

        # Cooldowns for specific messages we've shown
        self._shown_messages: dict[str, float] = {}
        self._message_cooldown: float = 3600.0  # Don't repeat same message in 1 hour

        # Silence mode (user can tell companion to be quiet)
        self._silent_mode: bool = False
        self._silent_until: float = 0.0

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def set_personality(self, personality: str):
        """Update personality."""
        with self._lock:
            self._personality = personality
            self.emotion = EmotionEngine(personality)
            self.suggester = ProactiveSuggester(personality)

    def set_silent_mode(self, enabled: bool, duration_minutes: float = 0):
        """Temporarily or permanently silence proactive messages."""
        with self._lock:
            if enabled:
                self._silent_mode = True
                if duration_minutes > 0:
                    self._silent_until = time.time() + (duration_minutes * 60)
            else:
                self._silent_mode = False
                self._silent_until = 0.0

    def is_silent_mode(self) -> bool:
        with self._lock:
            if self._silent_mode:
                if self._silent_until > 0 and time.time() > self._silent_until:
                    self._silent_mode = False
                    self._silent_until = 0.0
                    return False
                return True
            return False

    # =========================================================
    # CALLBACKS
    # =========================================================

    def on_emotion_change(self, callback: Callable[[CompanionMood, float], None]):
        """Register callback for when companion's emotion changes."""
        with self._lock:
            self._emotion_callbacks.append(callback)

    def on_intervention(self, callback: Callable[[dict], None]):
        """Register callback for when companion wants to intervene."""
        with self._lock:
            self._intervention_callbacks.append(callback)

    def on_achievement(self, callback: Callable[[dict], None]):
        """Register callback for when an achievement is detected."""
        with self._lock:
            self._achievement_callbacks.append(callback)

    # =========================================================
    # MAIN CYCLE
    # =========================================================

    def cycle(self, activity_type: str, window_title: str = "",
              process_name: str = "", idle_minutes: float = 0.0,
              is_processing: bool = False, is_voice_active: bool = False) -> dict:
        """
        Main update cycle - call this every monitor tick.
        Runs all sub-systems and returns an observation dict.
        """
        with self._lock:
            self._cycle_count += 1
            now = time.time()

            # 1. Update context
            self.context.update(
                activity_type=activity_type,
                window_title=window_title,
                process_name=process_name,
                idle_minutes=idle_minutes,
                is_processing=is_processing,
                is_voice_active=is_voice_active,
            )

            snapshot = self.context.get_snapshot()

            # 2. Update emotion
            previous_mood = self.emotion.mood
            current_mood = self.emotion.update(snapshot.user_state, snapshot)

            # Notify on emotion change
            if current_mood != previous_mood:
                for cb in self._emotion_callbacks:
                    try:
                        cb(current_mood, self.emotion.intensity)
                    except Exception as e:
                        logger.error(f"Emotion callback error: {e}")

            # 3. Run proactive analysis (not every cycle)
            observation = {
                "timestamp": now,
                "mood": current_mood,
                "mood_intensity": self.emotion.intensity,
                "user_state": snapshot.user_state,
                "activity_type": snapshot.activity_type,
                "intervention": None,
                "character_emotion": self.emotion.map_to_character_expression(),
                "silent_mode": self.is_silent_mode(),
            }

            # Do detailed analysis less frequently
            if now - self._last_detailed_analysis >= self._detailed_analysis_interval or self._cycle_count <= 5:
                self._last_detailed_analysis = now
                detailed = self._run_detailed_analysis(snapshot, current_mood)
                observation.update(detailed)

                # Record meaningful session events
                try:
                    if observation.get("intervention"):
                        msg = observation["intervention"].get("message", "")
                        if msg:
                            self.session_memory.record("intervention", msg, {
                                "activity": snapshot.activity_type,
                                "state": snapshot.user_state.value if hasattr(snapshot.user_state, "value") else str(snapshot.user_state),
                            })
                    if observation.get("new_achievement"):
                        title = observation["new_achievement"].get("title", "")
                        if title:
                            self.session_memory.record("achievement", title)
                except Exception:
                    pass

                # Fire callbacks if there was an intervention
                if detailed.get("intervention"):
                    self._recent_interventions.append(detailed["intervention"])
                    if len(self._recent_interventions) > self._max_recent:
                        self._recent_interventions.pop(0)

                    for cb in self._intervention_callbacks:
                        try:
                            cb(detailed["intervention"])
                        except Exception as e:
                            logger.error(f"Intervention callback error: {e}")

                # Fire achievement callbacks
                if detailed.get("new_achievement"):
                    for cb in self._achievement_callbacks:
                        try:
                            cb(detailed["new_achievement"])
                        except Exception as e:
                            logger.error(f"Achievement callback error: {e}")

            self._last_observation = observation
            return observation

    def _run_detailed_analysis(self, snapshot: ContextSnapshot,
                                mood: CompanionMood) -> dict:
        """
        Detailed analysis run periodically.
        Checks goals, achievements, and proactive suggestions.
        """
        result = {
            "intervention": None,
            "new_achievement": None,
            "active_goals": [],
            "session_summary": None,
        }

        # 1. Check for goal-related achievements
        active_goals = self.goals.get_active_goals()
        result["active_goals"] = active_goals[:3]

        if active_goals:
            # Check if current activity aligns with any goal
            for goal in active_goals:
                goal_activity = goal.get("context", {}).get("activity_type", "")
                if goal_activity == snapshot.activity_type:
                    completed = self.goals.update_goal_progress(goal["description"], 0.02)
                    if completed:
                        achievement = {
                            "title": f"Goal Complete: {goal['description']}",
                            "description": "You completed what you set out to do! 🎉",
                            "category": goal["category"],
                            "importance": 0.8,
                        }
                        self.goals.add_achievement(**achievement)
                        result["new_achievement"] = achievement

        # 2. Check for session-based achievements (every 30 min of focused work)
        if snapshot.activity_duration_minutes > 0:
            milestone_minutes = [30, 60, 120, 180]
            for mins in milestone_minutes:
                if abs(snapshot.activity_duration_minutes - mins) < 1.0:
                    if snapshot.user_state in (UserState.FOCUSED, UserState.CREATING, UserState.LEARNING):
                        achievement = {
                            "title": f"{mins} Minute Focus Streak",
                            "description": f"You've been focused for {mins} minutes straight! 🔥",
                            "category": "focus",
                            "importance": min(0.9, 0.3 + (mins / 200)),
                        }
                        # Only add if not already added (check recent achievements)
                        recent = self.goals.get_recent_achievements(3)
                        if not any(mins in str(a.get("title", "")) for a in recent):
                            self.goals.add_achievement(**achievement)
                            result["new_achievement"] = achievement

        # 3. Proactive suggestion / contextual dialogue
        if not self.is_silent_mode():
            suggestion = None

            # First try context-aware dialogue generator
            try:
                suggestion = self.dialogue_generator.generate(snapshot)
            except Exception as e:
                logger.debug(f"Contextual dialogue error: {e}")

            # Fall back to ProactiveSuggester
            if not suggestion:
                suggestion = self.suggester.get_suggestion(snapshot, mood)

            if suggestion:
                # Check message cooldown
                if suggestion.get("message"):
                    msg_hash = suggestion["message"][:50]
                    last_shown = self._shown_messages.get(msg_hash, 0)
                    if (now := time.time()) - last_shown < self._message_cooldown:
                        suggestion = None  # Already shown this recently

            if suggestion:
                if suggestion.get("message"):
                    msg_hash = suggestion["message"][:50]
                    self._shown_messages[msg_hash] = time.time()
                result["intervention"] = suggestion

            # Check for break reminder
            if not suggestion or suggestion["type"] != InterventionType.BREAK_REMINDER:
                break_reminder = self.suggester.get_break_reminder(snapshot)
                if break_reminder:
                    msg_hash = break_reminder["message"][:50]
                    last_shown = self._shown_messages.get(msg_hash, 0)
                    if time.time() - last_shown >= self._message_cooldown:
                        self._shown_messages[msg_hash] = time.time()
                        result["intervention"] = break_reminder

        # 4. Session summary (every 30 minutes of session)
        if int(snapshot.session_duration_minutes) % 30 == 0 and snapshot.session_duration_minutes > 0:
            if self._cycle_count < 10:  # Only once per milestone
                result["session_summary"] = self.context.get_session_summary()

        return result

    # =========================================================
    # EXTERNAL EVENTS
    # =========================================================

    def on_user_clicked(self, message: str = None):
        """Called when the user clicks the character."""
        self.context.record_interaction()
        self.emotion.boost(0.15)
        if random.random() < 0.3:
            self.emotion.set_mood(CompanionMood.PLAYFUL, 0.4)

    def on_user_returned(self, idle_minutes: float = 0.0):
        """Called when the user returns after being idle."""
        if idle_minutes > 30:
            self.emotion.set_mood(CompanionMood.EXCITED, 0.6)
        elif idle_minutes > 5:
            self.emotion.set_mood(CompanionMood.HAPPY, 0.5)
        else:
            self.emotion.set_mood(CompanionMood.CURIOUS, 0.4)

    def on_user_message(self, message: str):
        """Called when user sends a message."""
        self.context.record_interaction()
        self.emotion.boost(0.1)

        # Detect goals from user messages (simple pattern matching)
        goal_patterns = [
            (r"(?:working on|building|making|creating|writing)\s+(.+)", "project"),
            (r"(?:learning|studying|trying to learn)\s+(.+)", "learning"),
            (r"(?:fixing|debugging|solving)\s+(.+)", "problem_solving"),
            (r"(?:need to|have to|gotta|should)\s+(.+)", "task"),
        ]
        import re
        for pattern, category in goal_patterns:
            match = re.search(pattern, message.lower())
            if match:
                goal_desc = match.group(1).strip().capitalize()
                if len(goal_desc) > 3:
                    self.goals.set_active_goal(
                        goal_desc, category=category,
                        context={"source": "user_message", "activity_type": self.context.get_snapshot().activity_type}
                    )

    def on_ai_response(self, response: str):
        """Called after AI responds."""
        # If response was helpful, boost mood
        if any(word in response.lower() for word in ["solved", "fixed", "done", "here's how", "finished"]):
            self.emotion.boost(0.2)
            self.emotion.set_mood(CompanionMood.HAPPY, 0.6)

    def on_error(self, error_message: str):
        """Called when something goes wrong."""
        self.emotion.set_mood(CompanionMood.SYMPATHETIC, 0.5)

    def on_success(self, description: str, importance: float = 0.5):
        """Called to record a success/achievement."""
        self.goals.add_achievement(
            title="Success! 🎉",
            description=description,
            category="success",
            importance=importance,
        )
        self.emotion.set_mood(CompanionMood.HAPPY, 0.8)

    # =========================================================
    # OBSERVATION ACCESS
    # =========================================================

    def get_last_observation(self) -> Optional[dict]:
        with self._lock:
            return self._last_observation

    def get_state_summary(self) -> dict:
        """Human-readable summary of companion state."""
        with self._lock:
            snapshot = self.context.get_snapshot()
            return {
                "mood": self.emotion.mood.value,
                "mood_intensity": round(self.emotion.intensity, 2),
                "user_state": snapshot.user_state.value,
                "activity": snapshot.activity_type,
                "activity_duration": round(snapshot.activity_duration_minutes, 1),
                "session_duration": round(snapshot.session_duration_minutes, 1),
                "idle_minutes": round(snapshot.idle_minutes, 1),
                "active_goals": len(self.goals.get_active_goals()),
                "achievements_today": len(self.goals.get_recent_achievements(999)),
                "silent_mode": self.is_silent_mode(),
                "conversations": snapshot.conversation_count,
                "hour": snapshot.hour_of_day,
            }


# =============================================================
# GLOBAL INSTANCE
# =============================================================

_companion: Optional[CompanionIntelligence] = None
_companion_lock = threading.Lock()


def get_companion_intelligence() -> Optional[CompanionIntelligence]:
    """Get the global companion intelligence instance."""
    global _companion
    if _companion is None:
        with _companion_lock:
            if _companion is None:
                _companion = CompanionIntelligence()
    return _companion
