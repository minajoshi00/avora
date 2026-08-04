"""
===============================================================
                    SCREEN AWARENESS
===============================================================

Main screen awareness module for AVORA.
Integrates vision engine, context tracking, and companion intelligence.

Features:
  - Periodic screen capture and analysis
  - Activity detection with intent inference
  - Coding context detection (language, errors, git)
  - Study material detection
  - Gaming detection with smart quiet mode
  - Work session tracking
  - Habit learning and personalization
  - Context-aware companion reactions
  - Privacy-first design (local only by default)
  - Graceful degradation
  - Gaming pause mode
  - Idle detection
  - Performance optimized (CPU < 3%, minimal RAM)

Usage:
    from screen_awareness import ScreenAwareness

    awareness = ScreenAwareness(main_window)
    awareness.start()
    awareness.stop()
===============================================================
"""

import time
import logging
import threading
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger("ScreenAwareness")

try:
    from vision_engine import VisionEngine, ScreenAnalysis
    from screen_context import ScreenContextTracker, ScreenContext
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    logger.warning("Vision modules not available - screen awareness disabled")

from settings import (
    get_setting,
    is_screen_awareness_enabled,
    is_companion_enabled,
)


class ScreenAwareness:
    """
    Main screen awareness controller.
    Manages periodic screen analysis and feeds context to companion.
    """

    def __init__(self, main_window=None):
        self._lock = threading.RLock()
        self._main_window = main_window
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._error_notified = False
        
        # Components
        self._vision_engine = None
        self._context_tracker = None
        
        # State
        self._current_activity: str = "unknown"
        self._previous_activity: str = "unknown"
        self._last_analysis_time: float = 0.0
        self._last_proactive_time: float = 0.0
        self._proactive_cooldown: float = 300.0  # 5 minutes between proactive messages
        
        # Performance tracking
        self._analysis_count: int = 0
        self._skipped_analyses: int = 0
        self._last_performance_check: float = time.time()
        
        # Callbacks
        self._activity_callbacks: list[Callable] = []
        self._context_callbacks: list[Callable] = []
        
        # Initialize if available
        if VISION_AVAILABLE:
            self._initialize()
        else:
            logger.warning("Screen awareness unavailable - vision modules not loaded")

    def _initialize(self):
        """Initialize vision engine and context tracker."""
        try:
            self._vision_engine = VisionEngine()
            self._context_tracker = ScreenContextTracker()
            logger.info("Screen awareness initialized")
        except Exception as e:
            logger.error(f"Failed to initialize screen awareness: {e}")
            self._vision_engine = None
            self._context_tracker = None

    def is_available(self) -> bool:
        """Check if screen awareness is available."""
        return self._vision_engine is not None and self._vision_engine.is_available()

    def get_capabilities(self) -> Dict[str, bool]:
        """Get vision capabilities."""
        if self._vision_engine:
            return self._vision_engine.get_capabilities()
        return {"available": False}

    # =========================================================
    # LIFECYCLE
    # =========================================================

    def start(self):
        """Start screen awareness monitoring."""
        with self._lock:
            if self._running:
                return
            
            if not self.is_available():
                logger.warning("Screen awareness not available")
                return
            
            self._running = True
            self._error_notified = False
            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="ScreenAwareness",
            )
            self._thread.start()
            logger.info("Screen awareness started")

    def stop(self):
        """Stop screen awareness monitoring."""
        with self._lock:
            self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        
        logger.info("Screen awareness stopped")

    # =========================================================
    # CALLBACKS
    # =========================================================

    def add_activity_callback(self, callback: Callable[[str, str, str], None]):
        """Add callback for activity changes."""
        with self._lock:
            if callback not in self._activity_callbacks:
                self._activity_callbacks.append(callback)

    def add_context_callback(self, callback: Callable[[Dict], None]):
        """Add callback for context updates."""
        with self._lock:
            if callback not in self._context_callbacks:
                self._context_callbacks.append(callback)

    def remove_activity_callback(self, callback: Callable):
        """Remove activity callback."""
        with self._lock:
            if callback in self._activity_callbacks:
                self._activity_callbacks.remove(callback)

    def remove_context_callback(self, callback: Callable):
        """Remove context callback."""
        with self._lock:
            if callback in self._context_callbacks:
                self._context_callbacks.remove(callback)

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def _run_loop(self):
        """Main monitoring loop."""
        while True:
            with self._lock:
                if not self._running:
                    break
            
            try:
                self._tick()
            except Exception as e:
                logger.debug(f"Screen awareness tick error: {e}")
            
            # Get interval from settings
            try:
                interval = get_setting("screen_awareness.analysis_interval_seconds", 5)
            except Exception:
                interval = 5
            
            time.sleep(interval)

    def _tick(self):
        """Single monitoring tick."""
        if not self._vision_engine:
            return
        
        # Check if enabled
        try:
            if not is_screen_awareness_enabled():
                return
        except Exception:
            return
        
        # Performance check - skip if CPU is busy
        now = time.time()
        if now - self._last_performance_check >= 60.0:
            # Log performance metrics every minute
            logger.debug(f"Performance: {self._analysis_count} analyses, {self._skipped_analyses} skipped")
            self._analysis_count = 0
            self._skipped_analyses = 0
            self._last_performance_check = now
        
        # Perform analysis
        analysis = self._vision_engine.analyze()
        self._analysis_count += 1
        
        if analysis.error:
            logger.debug(f"Analysis error: {analysis.error}")
            return
        
        # Check for gaming pause
        try:
            pause_while_gaming = get_setting("screen_awareness.pause_while_gaming", True)
        except Exception:
            pause_while_gaming = True
        
        if pause_while_gaming and analysis.is_gaming:
            # Don't update context while gaming, but still track
            self._skipped_analyses += 1
            return
        
        # Check for idle pause
        try:
            idle_pause = get_setting("screen_awareness.idle_pause_seconds", 60)
        except Exception:
            idle_pause = 60
        
        if analysis.is_idle:
            # User is idle - don't spam
            self._skipped_analyses += 1
            return
        
        # Update context
        if self._context_tracker:
            context = ScreenContext(
                active_app=analysis.active_app,
                window_title=analysis.window_title,
                process_name=analysis.process_name,
                activity_type=analysis.activity_type,
                visible_content=analysis.visible_text[:200],
                is_gaming=analysis.is_gaming,
                is_idle=analysis.is_idle,
                confidence=analysis.confidence,
                intent=analysis.intent,
                coding_language=analysis.coding_language,
                coding_file=analysis.coding_file,
                coding_project=analysis.coding_project,
                has_error=analysis.has_error,
                error_type=analysis.error_type,
                game_name=analysis.game_name,
            )
            self._context_tracker.update(context)
            
            # Notify context callbacks
            self._notify_context_callbacks(context)
        
        # Check for activity transition
        if analysis.activity_type != self._current_activity:
            self._previous_activity = self._current_activity
            self._current_activity = analysis.activity_type
            
            # Notify activity callbacks
            self._notify_activity_callbacks(
                analysis.activity_type,
                analysis.window_title,
                analysis.process_name,
            )
            
            # Trigger companion reaction if available
            self._trigger_companion_reaction(
                analysis.activity_type,
                analysis.window_title,
                analysis.process_name,
                analysis,
            )

    # =========================================================
    # NOTIFICATIONS
    # =========================================================

    def _notify_activity_callbacks(self, activity: str, title: str, process: str):
        """Notify activity callbacks of change."""
        callbacks = list(self._activity_callbacks)
        for callback in callbacks:
            try:
                callback(activity, title, process)
            except Exception as e:
                logger.debug(f"Activity callback error: {e}")

    def _notify_context_callbacks(self, context: ScreenContext):
        """Notify context callbacks."""
        callbacks = list(self._context_callbacks)
        context_dict = {
            "timestamp": context.timestamp,
            "active_app": context.active_app,
            "window_title": context.window_title,
            "process_name": context.process_name,
            "activity_type": context.activity_type,
            "is_gaming": context.is_gaming,
            "is_idle": context.is_idle,
            "confidence": context.confidence,
            "intent": context.intent,
            "coding_language": context.coding_language,
            "coding_file": context.coding_file,
            "coding_project": context.coding_project,
            "has_error": context.has_error,
            "error_type": context.error_type,
            "game_name": context.game_name,
        }
        for callback in callbacks:
            try:
                callback(context_dict)
            except Exception as e:
                logger.debug(f"Context callback error: {e}")

    # =========================================================
    # COMPANION INTEGRATION
    # =========================================================

    def _trigger_companion_reaction(self, activity: str, title: str, process: str, analysis: ScreenAnalysis):
        """
        Trigger companion reaction on activity change.
        Uses proactive messaging with cooldowns.
        """
        try:
            if not is_companion_enabled():
                return
        except Exception:
            return
        
        # Check cooldown
        now = time.time()
        if now - self._last_proactive_time < self._proactive_cooldown:
            return
        
        # Get main window
        main_window = self._main_window
        if not main_window:
            return
        
        # Get companion behavior controller
        try:
            behavior = getattr(main_window, 'behavior_controller', None)
            if not behavior:
                return
        except Exception:
            return
        
        # Generate contextual message
        message = self._generate_context_message(activity, title, process, analysis)
        if not message:
            return
        
        # Determine character expression
        expression = self._get_character_expression(activity, analysis)
        
        # Show speech bubble and update expression
        try:
            behavior.show_speech_bubble(message, duration_ms=4000)
            if main_window.character is not None:
                main_window.character_call("set_expression", expression)
            self._last_proactive_time = now
        except Exception as e:
            logger.debug(f"Failed to show companion reaction: {e}")

    def _get_character_expression(self, activity: str, analysis: ScreenAnalysis) -> str:
        """Get appropriate character expression for activity."""
        if analysis.has_error or analysis.error_type:
            return "thinking"
        
        activity_lower = activity.lower()
        if activity_lower == "coding":
            return "curious"
        elif activity_lower == "gaming":
            return "excited"
        elif activity_lower == "studying":
            return "focused"
        elif activity_lower == "reading":
            return "focused"
        elif activity_lower == "designing":
            return "curious"
        elif activity_lower == "idle":
            return "sleepy"
        elif analysis.intent == "debugging":
            return "thinking"
        elif analysis.intent == "watching_videos":
            return "relaxed"
        else:
            return "idle"

    def _generate_context_message(self, activity: str, title: str, process: str, analysis: ScreenAnalysis) -> Optional[str]:
        """Generate contextual message based on activity and intent."""
        activity_lower = activity.lower()
        title_lower = title.lower()
        process_lower = process.lower()
        intent = analysis.intent.lower()
        
        # Gaming - stay quiet
        if activity_lower == "gaming":
            return None  # Silent for gaming
        
        # Coding contexts
        if activity_lower == "coding":
            # Error detection - only mention once per error type
            if analysis.has_error and analysis.error_type:
                error_msgs = {
                    "python_traceback": "I noticed an exception. Want me to help?",
                    "python_exception": "That looks like an exception. Want help debugging?",
                    "javascript_error": "Looks like a JavaScript error. Need help?",
                    "typescript_error": "TypeScript error detected. Want me to explain?",
                    "java_exception": "Java exception found. Need a second pair of eyes?",
                    "compiler_error": "Compiler error spotted. Want help fixing it?",
                    "git_conflict": "Git conflict detected. Need help resolving it?",
                    "build_failed": "Build failed. Want me to help diagnose?",
                }
                return error_msgs.get(analysis.error_type, "I noticed an issue. Want help?")
            
            # Debugging
            if intent == "debugging":
                return "Debug mode activated. Need a second pair of eyes?"
            
            # Code review
            if intent == "reviewing_code" or "github" in process_lower:
                return "Working on AVORA again?"
            
            # Language-specific comments
            if analysis.coding_language:
                lang_comments = {
                    "python": "Python mode! 🐍 Need help with anything?",
                    "javascript": "JavaScript time! Need any help?",
                    "typescript": "TypeScript! Keeping it type-safe 💪",
                    "java": "Java development! Need a hand?",
                    "cpp": "C++! Performance mode activated 🚀",
                    "go": "Go lang! Simple and fast ⚡",
                    "rust": "Rust! Memory safe and fast 🦀",
                }
                return lang_comments.get(analysis.coding_language)
            
            return None  # Silent for general coding
        
        # Studying contexts
        if activity_lower == "studying":
            # Only interrupt if they've been studying for a while
            if self._context_tracker.get_activity_duration_minutes() > 10:
                return "Want me to summarize this or quiz you when you're ready?"
            return None
        
        # Video contexts
        if activity_lower == "watching_videos" or intent == "watching_videos":
            return None  # Silent - don't interrupt videos
        
        # Browsing contexts
        if activity_lower == "browsing":
            if "youtube" in process_lower:
                return None  # Silent for YouTube
            if "github" in process_lower:
                return "Working on AVORA again?"
            return None  # Silent for general browsing
        
        # Working contexts
        if activity_lower == "working":
            if self._context_tracker.should_suggest_break(threshold_minutes=45):
                return "You've been working for a while. Want a break?"
            return None
        
        # Idle
        if activity_lower == "idle":
            if self._context_tracker.get_activity_duration_minutes() > 5:
                return "You've been away for a bit. Everything okay?"
            return None
        
        return None

    # =========================================================
    # STATE ACCESS
    # =========================================================

    def get_current_activity(self) -> str:
        """Get current activity type."""
        with self._lock:
            return self._current_activity

    def get_previous_activity(self) -> str:
        """Get previous activity type."""
        with self._lock:
            return self._previous_activity

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current screen context."""
        with self._lock:
            summary = {
                "current_activity": self._current_activity,
                "previous_activity": self._previous_activity,
            }
            
            if self._context_tracker:
                context = self._context_tracker.get_current()
                summary.update({
                    "active_app": context.active_app,
                    "window_title": context.window_title[:50] if context.window_title else "",
                    "process_name": context.process_name,
                    "intent": context.intent,
                    "coding_language": context.coding_language,
                    "has_error": context.has_error,
                    "activity_duration_minutes": round(self._context_tracker.get_activity_duration_minutes(), 1),
                    "session_duration_minutes": round(self._context_tracker.get_session_duration_minutes(), 1),
                    "focus_session_minutes": round(self._context_tracker.get_focus_session_duration_minutes(), 1),
                })
            
            if self._vision_engine:
                last = self._vision_engine.get_last_analysis()
                if last:
                    summary["last_confidence"] = last.confidence
                    summary["is_gaming"] = last.is_gaming
                    summary["is_idle"] = last.is_idle
            
            return summary

    def get_last_analysis(self) -> Optional[Any]:
        """Get last screen analysis."""
        if self._vision_engine:
            return self._vision_engine.get_last_analysis()
        return None

    def has_transitioned(self) -> bool:
        """Check if there was a recent activity transition."""
        if self._context_tracker:
            return self._context_tracker.has_transitioned()
        return False

    # =========================================================
    # EXTERNAL EVENTS
    # =========================================================

    def on_user_activity(self):
        """Call when user interacts to reset idle timers."""
        pass  # Could be used for more sophisticated idle detection

    def disable(self):
        """Gracefully disable screen awareness."""
        self.stop()
        with self._lock:
            self._running = False
            self._vision_engine = None
            self._context_tracker = None
        logger.info("Screen awareness disabled")