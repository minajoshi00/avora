"""
===============================================================
                    SCREEN CONTEXT TRACKER
===============================================================

Maintains recent screen context for the companion intelligence system.
Tracks:
  - Current active application
  - Previous active application
  - Current activity type
  - Time spent in current activity
  - Focus session duration
  - Recent context transitions
  - User habits and patterns
  - Smart memory for personalization

Designed to be lightweight and thread-safe.
===============================================================
"""

import time
import threading
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ScreenContext:
    """A snapshot of screen context at a point in time."""
    timestamp: float = 0.0
    active_app: str = ""
    window_title: str = ""
    process_name: str = ""
    activity_type: str = "unknown"
    visible_content: str = ""
    is_gaming: bool = False
    is_idle: bool = False
    confidence: float = 0.0
    
    # Enhanced fields
    intent: str = "unknown"
    coding_language: str = ""
    coding_file: str = ""
    coding_project: str = ""
    has_error: bool = False
    error_type: str = ""
    game_name: str = ""
    study_subject: str = ""


class ScreenContextTracker:
    """
    Tracks screen context over time.
    Maintains history and detects transitions.
    Learns user habits for better personalization.
    """

    def __init__(self, max_history: int = 50):
        self._lock = threading.RLock()
        self._current: ScreenContext = ScreenContext()
        self._previous: Optional[ScreenContext] = None
        self._history: List[ScreenContext] = []
        self._max_history = max_history
        
        # Activity tracking
        self._activity_start_time: float = time.time()
        self._session_start_time: float = time.time()
        self._activity_durations: Dict[str, float] = {}
        
        # Transition tracking
        self._last_transition_time: float = 0.0
        self._transition_count: int = 0
        
        # Habit learning
        self._app_frequency: Dict[str, int] = defaultdict(int)
        self._time_patterns: Dict[str, List[float]] = defaultdict(list)
        self._activity_sequences: List[tuple] = []
        self._max_sequences: int = 100
        
        # Focus session tracking
        self._focus_session_start: float = 0.0
        self._focus_session_type: str = ""
        self._focus_breaks: int = 0

    def update(self, context: ScreenContext):
        """Update with new screen context."""
        with self._lock:
            now = time.time()
            
            # Store previous
            self._previous = self._current
            
            # Update current
            self._current = context
            self._current.timestamp = now
            
            # Check for activity transition
            prev_activity = self._previous.activity_type if self._previous else "unknown"
            if prev_activity != context.activity_type:
                self._last_transition_time = now
                self._transition_count += 1
                
                # Record duration of previous activity
                if prev_activity != "unknown" and self._previous:
                    duration = (now - self._activity_start_time) / 60.0
                    self._activity_durations[prev_activity] = self._activity_durations.get(prev_activity, 0.0) + duration
                
                self._activity_start_time = now
                
                # Track activity sequences for habit learning
                if self._previous:
                    seq = (prev_activity, context.activity_type)
                    self._activity_sequences.append(seq)
                    if len(self._activity_sequences) > self._max_sequences:
                        self._activity_sequences.pop(0)
            
            # Update app frequency
            if context.active_app:
                self._app_frequency[context.active_app] += 1
            
            # Track time patterns (hour of day)
            hour = datetime.now().hour if hasattr(self, '_datetime') else time.localtime().tm_hour
            self._time_patterns[context.activity_type].append(hour)
            
            # Focus session tracking
            if context.activity_type in ["coding", "studying", "working"]:
                if self._focus_session_type != context.activity_type:
                    # New focus session
                    self._focus_session_start = now
                    self._focus_session_type = context.activity_type
                    self._focus_breaks = 0
            else:
                # Break from focus
                if self._focus_session_type:
                    self._focus_breaks += 1
                    self._focus_session_type = ""
            
            # Add to history
            self._history.append(context)
            if len(self._history) > self._max_history:
                self._history.pop(0)

    def get_current(self) -> ScreenContext:
        """Get current context (thread-safe copy)."""
        with self._lock:
            return self._current

    def get_previous(self) -> Optional[ScreenContext]:
        """Get previous context."""
        with self._lock:
            return self._previous

    def get_history(self, count: int = 10) -> List[ScreenContext]:
        """Get recent context history."""
        with self._lock:
            return list(self._history[-count:])

    def get_activity_duration_minutes(self) -> float:
        """How long in current activity."""
        with self._lock:
            return (time.time() - self._activity_start_time) / 60.0

    def get_session_duration_minutes(self) -> float:
        """Total session duration."""
        with self._lock:
            return (time.time() - self._session_start_time) / 60.0

    def get_time_since_transition_minutes(self) -> float:
        """Minutes since last activity transition."""
        with self._lock:
            return (time.time() - self._last_transition_time) / 60.0

    def get_transition_count(self) -> int:
        """Total transitions this session."""
        with self._lock:
            return self._transition_count

    def get_activity_summary(self) -> Dict[str, float]:
        """Get summary of time spent in each activity."""
        with self._lock:
            # Add current activity
            summary = dict(self._activity_durations)
            current_duration = (time.time() - self._activity_start_time) / 60.0
            if self._current.activity_type != "unknown":
                summary[self._current.activity_type] = summary.get(self._current.activity_type, 0.0) + current_duration
            return summary

    def has_transitioned(self) -> bool:
        """Check if there was a recent transition (within last 2 seconds)."""
        with self._lock:
            return (time.time() - self._last_transition_time) < 2.0

    def get_focus_session_duration_minutes(self) -> float:
        """Get current focus session duration."""
        with self._lock:
            if self._focus_session_type:
                return (time.time() - self._focus_session_start) / 60.0
            return 0.0

    def get_focus_session_type(self) -> str:
        """Get current focus session type."""
        with self._lock:
            return self._focus_session_type

    def get_focus_break_count(self) -> int:
        """Get number of breaks in current session."""
        with self._lock:
            return self._focus_breaks

    def get_most_frequent_apps(self, count: int = 5) -> List[tuple]:
        """Get most frequently used apps."""
        with self._lock:
            sorted_apps = sorted(self._app_frequency.items(), key=lambda x: x[1], reverse=True)
            return sorted_apps[:count]

    def get_habitual_sequence(self) -> Optional[tuple]:
        """Predict next activity based on habits."""
        with self._lock:
            if len(self._activity_sequences) < 3:
                return None
            
            # Get last 2 activities
            recent = self._activity_sequences[-2:]
            if len(recent) < 2:
                return None
            
            # Find most common next activity after this sequence
            seq_counts = defaultdict(int)
            for i in range(len(self._activity_sequences) - 1):
                if self._activity_sequences[i] == tuple(recent):
                    next_activity = self._activity_sequences[i + 1][1]
                    seq_counts[next_activity] += 1
            
            if seq_counts:
                most_common = max(seq_counts.items(), key=lambda x: x[1])
                return most_common
            return None

    def should_suggest_break(self, threshold_minutes: float = 45.0) -> bool:
        """Check if user should take a break."""
        with self._lock:
            if self._focus_session_type:
                focus_duration = (time.time() - self._focus_session_start) / 60.0
                return focus_duration >= threshold_minutes
            return False

    def clear(self):
        """Reset tracker state."""
        with self._lock:
            self._current = ScreenContext()
            self._previous = None
            self._history.clear()
            self._activity_start_time = time.time()
            self._session_start_time = time.time()
            self._activity_durations.clear()
            self._last_transition_time = 0.0
            self._transition_count = 0
            self._app_frequency.clear()
            self._time_patterns.clear()
            self._activity_sequences.clear()
            self._focus_session_start = 0.0
            self._focus_session_type = ""
            self._focus_breaks = 0


# Add datetime import
from datetime import datetime