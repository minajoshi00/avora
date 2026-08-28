"""
emotional_continuity.py
============================================================
AVORA V2 — Phase 7: Emotional Continuity

Maintains a persistent emotional state for the companion across
conversations and application restarts. Emotions are driven by
user message sentiment, interaction patterns, and elapsed time,
so AVORA responds with consistent emotional continuity rather
than starting fresh every session.

Design:
  * State is persisted to <APP_DATA_DIR>/emotional_state.json
  * No sensitive personal attributes are stored (only emotion
    labels + timestamps + interaction counters)
  * EmotionalState is a plain data class (no PySide dependency)
  * EmotionEngine wraps logic, exposes a simple API used by
    CompanionIntelligence and main.py
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from enum import Enum
from pathlib import Path

try:
    from app_paths import APP_DATA_DIR
except ImportError:  # pragma: no cover
    APP_DATA_DIR = Path.cwd() / "data"

try:
    from settings import get_setting
except Exception:  # pragma: no cover

    def get_setting(key, default=None):
        return default


# ============================================================
# EMOTION ENUM
# ============================================================


class EmotionState(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    THINKING = "thinking"
    CURIOUS = "curious"
    WELCOMING = "welcoming"
    CONCERNED = "concerned"
    SAD = "sad"
    PROUD = "proud"
    PLAYFUL = "playful"
    FOCUS = "focus"


# ============================================================
# EMOTIONAL STATE
# ============================================================


class EmotionalState:
    """Plain-data emotional state persisted across sessions."""

    __slots__ = (
        "current_emotion",
        "emotion_history",
        "emotion_intensity",
        "engagement_score",
        "first_interaction_time",
        "last_interaction_time",
        "previous_emotion",
        "previous_emotion_intensity",
        "total_interactions",
    )

    def __init__(self):
        self.current_emotion: str = EmotionState.NEUTRAL.value
        self.emotion_intensity: float = 0.3
        self.previous_emotion: str = EmotionState.NEUTRAL.value
        self.previous_emotion_intensity: float = 0.3
        self.engagement_score: float = 0.5
        self.total_interactions: int = 0
        self.last_interaction_time: str = ""
        self.first_interaction_time: str = ""
        self.emotion_history: list = []

    def to_dict(self) -> dict:
        return {
            "current_emotion": self.current_emotion,
            "emotion_intensity": self.emotion_intensity,
            "previous_emotion": self.previous_emotion,
            "previous_emotion_intensity": self.previous_emotion_intensity,
            "engagement_score": self.engagement_score,
            "total_interactions": self.total_interactions,
            "last_interaction_time": self.last_interaction_time,
            "first_interaction_time": self.first_interaction_time,
            "emotion_history": self.emotion_history,
        }

    def from_dict(self, data: dict) -> EmotionalState:
        if not isinstance(data, dict):
            return self

        for slot in self.__slots__:
            if slot in data:
                try:
                    setattr(self, slot, data[slot])
                except (TypeError, AttributeError):
                    pass

        # Validate enum values
        valid = {e.value for e in EmotionState}
        if self.current_emotion not in valid:
            self.current_emotion = EmotionState.NEUTRAL.value
        if self.previous_emotion not in valid:
            self.previous_emotion = EmotionState.NEUTRAL.value

        return self


# ============================================================
# STATE FILE
# ============================================================

_lock = threading.RLock()
_state_cache: EmotionalState | None = None


def _state_file():
    """Resolve the state file path at call time (app_paths may be patched)."""
    try:
        from app_paths import APP_DATA_DIR as _dir

        return _dir / "emotional_state.json"
    except Exception:
        return APP_DATA_DIR / "emotional_state.json"


def _load_state() -> EmotionalState:
    """Load persisted emotional state from disk."""
    global _state_cache
    with _lock:
        if _state_cache is not None:
            return _state_cache

        state = EmotionalState()
        path = _state_file()

        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                state.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError):
            pass

        _state_cache = state
        return state


def _save_state(state: EmotionalState | None = None) -> bool:
    """Persist emotional state to disk."""
    if state is None:
        state = _load_state()

    with _lock:
        try:
            path = _state_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(state.to_dict(), file, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError):
            return False


# ============================================================
# SENTIMENT ANALYSIS
# ============================================================

_POSITIVE_WORDS = {
    "great",
    "awesome",
    "amazing",
    "wonderful",
    "fantastic",
    "excellent",
    "good",
    "nice",
    "love",
    "like",
    "happy",
    "excited",
    "thanks",
    "thank",
    "successful",
    "success",
    "perfect",
    "brilliant",
    "cool",
    "lit",
    "fire",
    "sick",
    "dope",
    "yeet",
    "yay",
    "yayy",
    "congrats",
    "congratulations",
    "proud",
    "achievement",
    "win",
    "won",
    "celebrate",
    "solved",
    "fixed",
}

_NEGATIVE_WORDS = {
    "bad",
    "terrible",
    "awful",
    "horrible",
    "hate",
    "sad",
    "angry",
    "frustrated",
    "stuck",
    "confused",
    "wrong",
    "error",
    "fail",
    "failed",
    "broken",
    "bug",
    "annoying",
    "annoyed",
    "worst",
    "pain",
    "difficult",
    "struggling",
    "lost",
    "give up",
    "useless",
    "crash",
}


def _sentiment_score(text: str) -> float:
    """
    Lightweight rule-based sentiment.
    Returns float in [-1.0, 1.0].
    """
    if not text:
        return 0.0

    lower = text.lower()
    tokens = re.findall(r"[a-z']+", lower)

    score = 0.0
    matched = 0

    for token in tokens:
        if token in _POSITIVE_WORDS:
            score += 1.0
            matched += 1
        elif token in _NEGATIVE_WORDS:
            score -= 1.0
            matched += 1

    if "give up" in lower:
        score -= 0.8
        matched += 1

    if matched == 0:
        return 0.0

    return max(-1.0, min(1.0, score / matched))


def _classify_emotion(text: str) -> tuple[str, float]:
    """Map user message sentiment to an emotion + intensity."""
    sentiment = _sentiment_score(text)

    if sentiment > 0.5:
        if "excited" in text.lower() or "awesome" in text.lower():
            return EmotionState.EXCITED.value, min(1.0, sentiment + 0.2)
        return EmotionState.HAPPY.value, sentiment
    if sentiment > 0.15:
        return EmotionState.HAPPY.value, sentiment
    if sentiment < -0.5:
        return EmotionState.SAD.value, min(1.0, abs(sentiment) + 0.1)
    if sentiment < -0.15:
        return EmotionState.CONCERNED.value, abs(sentiment)
    if "?" in text and len(text.strip()) > 8:
        return EmotionState.CURIOUS.value, 0.5
    if any(
        w in text.lower() for w in ["think", "consider", "wonder", "ponder", "reflect"]
    ):
        return EmotionState.THINKING.value, 0.45
    if any(
        w in text.lower() for w in ["let's go", "let's start", "ready", "let's build"]
    ):
        return EmotionState.PLAYFUL.value, 0.6
    return EmotionState.NEUTRAL.value, 0.3


# ============================================================
# DECAY & ENGAGEMENT
# ============================================================


def _decay_factor(hours_elapsed: float) -> float:
    """Factor in [0,1] by which intensity decays (8h -> 0)."""
    if hours_elapsed <= 0:
        return 1.0
    if hours_elapsed >= 8.0:
        return 0.0
    return max(0.0, 1.0 - (hours_elapsed / 8.0))


def _update_engagement(state: EmotionalState, sentiment: float) -> None:
    if sentiment > 0.1:
        state.engagement_score = min(1.0, state.engagement_score + 0.08)
    elif sentiment < -0.1:
        state.engagement_score = max(0.0, state.engagement_score - 0.12)
    else:
        state.engagement_score = max(0.1, state.engagement_score - 0.02)


def _apply_time_decay(state: EmotionalState) -> EmotionalState:
    """Decay emotional intensity based on elapsed time since last interaction."""
    if not state.last_interaction_time:
        return state

    try:
        last = datetime.fromisoformat(state.last_interaction_time)
    except (ValueError, TypeError):
        return state

    now = datetime.now()
    hours_elapsed = (now - last).total_seconds() / 3600.0

    # More than 24h -> reset to welcoming default
    if hours_elapsed >= 24.0:
        state.previous_emotion = state.current_emotion
        state.previous_emotion_intensity = state.emotion_intensity
        state.current_emotion = EmotionState.WELCOMING.value
        state.emotion_intensity = 0.6
        return state

    factor = _decay_factor(hours_elapsed)
    state.emotion_intensity = max(0.1, state.emotion_intensity * factor)
    return state


# ============================================================
# EMOTION ENGINE
# ============================================================


class EmotionEngine:
    """Drives emotional continuity for the companion."""

    def __init__(self):
        self._state: EmotionalState | None = None

    @property
    def state(self) -> EmotionalState:
        if self._state is None:
            self._state = _load_state()
        return self._state

    def process_user_message(self, message: str) -> tuple[str, float]:
        """Process a user message; update + persist emotional state."""
        if not message:
            return self.state.current_emotion, self.state.emotion_intensity

        text = str(message).strip()
        if not text:
            return self.state.current_emotion, self.state.emotion_intensity

        try:
            if not get_setting("companion_widget.emotion_tracking", True):
                return self.state.current_emotion, self.state.emotion_intensity
        except Exception:
            pass

        with _lock:
            state = self.state
            state = _apply_time_decay(state)

            sentiment = _sentiment_score(text)

            state.previous_emotion = state.current_emotion
            state.previous_emotion_intensity = state.emotion_intensity

            new_emotion, intensity = _classify_emotion(text)

            state.current_emotion = new_emotion
            state.emotion_intensity = max(0.1, min(1.0, intensity))

            state.total_interactions += 1

            now = datetime.now().isoformat(timespec="seconds")
            state.last_interaction_time = now
            if not state.first_interaction_time:
                state.first_interaction_time = now

            state.emotion_history.append(
                {
                    "emotion": new_emotion,
                    "intensity": round(state.emotion_intensity, 3),
                    "sentiment": round(sentiment, 3),
                    "timestamp": now,
                }
            )
            if len(state.emotion_history) > 50:
                state.emotion_history = state.emotion_history[-50:]

            _update_engagement(state, sentiment)

            _save_state(state)

            return state.current_emotion, state.emotion_intensity

    def on_ai_response(self, response: str) -> tuple[str, float]:
        """Process the AI's own response to keep emotion in sync."""
        if not response:
            return self.state.current_emotion, self.state.emotion_intensity

        try:
            if not get_setting("companion_widget.emotion_tracking", True):
                return self.state.current_emotion, self.state.emotion_intensity
        except Exception:
            pass

        with _lock:
            state = self.state
            state = _apply_time_decay(state)

            lower = response.lower()
            if any(w in lower for w in ["awesome", "amazing", "congrats"]):
                state.previous_emotion = state.current_emotion
                state.previous_emotion_intensity = state.emotion_intensity
                state.current_emotion = EmotionState.PROUD.value
                state.emotion_intensity = min(1.0, state.emotion_intensity + 0.1)
            else:
                sentiment = _sentiment_score(response)
                if sentiment > 0.2:
                    state.emotion_intensity = min(1.0, state.emotion_intensity + 0.05)

            state.total_interactions += 1
            now = datetime.now().isoformat(timespec="seconds")
            state.last_interaction_time = now
            if not state.first_interaction_time:
                state.first_interaction_time = now

            _save_state(state)

            return state.current_emotion, state.emotion_intensity

    def get_emotion_context_for_ai(self, max_items: int = 5) -> str:
        """Format recent emotional state for AI prompt injection."""
        try:
            if not get_setting("companion_widget.emotion_tracking", True):
                return ""
        except Exception:
            pass

        state = _apply_time_decay(self.state)

        recent = list(reversed(state.emotion_history))[:max_items]
        if not recent:
            return ""

        lines = [f"- {e['emotion']} (intensity {e['intensity']:.2f})" for e in recent]

        header = (
            f"Companion emotional state: {state.current_emotion} "
            f"(intensity {state.emotion_intensity:.2f}, "
            f"engagement {state.engagement_score:.2f}, "
            f"{state.total_interactions} interactions)"
        )

        return header + "\nRecent emotions:\n" + "\n".join(lines)

    def get_emotion(self) -> str:
        """Return current emotion (after time decay)."""
        state = _apply_time_decay(self.state)
        return state.current_emotion

    def get_intensity(self) -> float:
        """Return current emotion intensity (after time decay)."""
        state = _apply_time_decay(self.state)
        return state.emotion_intensity

    def reset(self) -> None:
        """Reset emotional state to neutral defaults."""
        with _lock:
            global _state_cache
            _state_cache = None
            self._state = None
            state = EmotionalState()
            _save_state(state)

    def save(self) -> bool:
        """Explicitly persist current state."""
        with _lock:
            return _save_state(self.state)


# ============================================================
# SINGLETON
# ============================================================

_engine: EmotionEngine | None = None


def get_emotion_engine() -> EmotionEngine:
    global _engine
    if _engine is None:
        _engine = EmotionEngine()
    return _engine


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "EmotionEngine",
    "EmotionState",
    "EmotionalState",
    "get_emotion_engine",
]
