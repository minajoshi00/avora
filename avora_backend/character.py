# ============================================================
# CHARACTER / EMOTION INTEGRATION — AVORA AGENT MODE
# ============================================================
# Maps agent outcomes to an emotional state that a host UI can
# surface on the animated companion (expression), and attaches
# a natural-language "tone" to responses.
#
# Aligns with the existing AVORA CompanionMood vocabulary so the
# host character renders consistently (idle/happy/excited/...).
# This module is self-contained and does NOT depend on the Qt
# companion widget; it produces the data the widget consumes.
# ============================================================

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, Optional


class AgentMood(Enum):
    """Emotional states an agent can express, aligned with AVORA."""
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


# Map AgentMood -> character.py expression name (same vocab as AVORA)
_MOOD_TO_EXPRESSION = {
    AgentMood.NEUTRAL: "idle",
    AgentMood.HAPPY: "happy",
    AgentMood.EXCITED: "excited",
    AgentMood.CURIOUS: "curious",
    AgentMood.CONCERNED: "thinking",
    AgentMood.PROUD: "happy",
    AgentMood.FRUSTRATED: "angry",
    AgentMood.SYMPATHETIC: "sad",
    AgentMood.PLAYFUL: "happy",
    AgentMood.CALM: "idle",
    AgentMood.THOUGHTFUL: "thinking",
    AgentMood.SLEEPY: "sleepy",
    AgentMood.SURPRISED: "surprised",
}


class CharacterState:
    """Tracks the agent's emotional state over the course of a goal."""

    _DEFAULT_TONE = {
        AgentMood.NEUTRAL: "Let me take care of that.",
        AgentMood.HAPPY: "All set!",
        AgentMood.EXCITED: "Done — that was smooth!",
        AgentMood.CURIOUS: "Let me look into that.",
        AgentMood.CONCERNED: "Let me handle that carefully.",
        AgentMood.PROUD: "Nice, that worked out well.",
        AgentMood.FRUSTRATED: "Hmm, that didn't go as planned.",
        AgentMood.SYMPATHETIC: "No worries, let me sort this out.",
        AgentMood.PLAYFUL: "Easy peasy.",
        AgentMood.CALM: "No problem.",
        AgentMood.THOUGHTFUL: "Let me think about this.",
        AgentMood.SLEEPY: "Alright, taking it easy.",
        AgentMood.SURPRISED: "Interesting — let me look closer.",
    }

    def __init__(self, mood: AgentMood = AgentMood.NEUTRAL) -> None:
        self.mood: AgentMood = mood
        self.intensity: float = 0.5
        self.transitions: list[Dict[str, Any]] = []
        self.history: list[Dict[str, Any]] = []
        self._max_history = 30

    def set_mood(self, mood: AgentMood, intensity: Optional[float] = None) -> None:
        """Transition to a new emotional state, logged for the host."""
        old = self.mood
        self.mood = mood
        if intensity is not None:
            self.intensity = max(0.0, min(1.0, intensity))
        else:
            self.intensity = min(1.0, self.intensity + 0.2)

        entry = {
            "mood": mood.value,
            "expression": _MOOD_TO_EXPRESSION.get(mood, "idle"),
            "intensity": round(self.intensity, 3),
            "timestamp": time.time(),
        }
        self.transitions.append(entry)
        self.history.append(entry)
        if len(self.history) > self._max_history:
            self.history.pop(0)

    # -----------------------------------------------------------------
    # Outcome -> emotion mapping
    # -----------------------------------------------------------------

    def on_task_completed(self) -> None:
        self.set_mood(AgentMood.HAPPY, 0.8)

    def on_task_failed(self) -> None:
        self.set_mood(AgentMood.CONCERNED, 0.7)

    def on_task_cancelled(self) -> None:
        self.set_mood(AgentMood.NEUTRAL, 0.4)

    def on_task_waiting(self) -> None:
        self.set_mood(AgentMood.CURIOUS, 0.5)

    def on_step_success(self) -> None:
        if self.mood == AgentMood.NEUTRAL:
            self.set_mood(AgentMood.CALM, 0.5)

    def on_step_failure(self) -> None:
        if self.mood not in (AgentMood.CONCERNED, AgentMood.FRUSTRATED):
            self.set_mood(AgentMood.THOUGHTFUL, 0.5)

    # -----------------------------------------------------------------
    # Output helpers
    # -----------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Serializable state for the host UI / character driver."""
        return {
            "mood": self.mood.value,
            "expression": _MOOD_TO_EXPRESSION.get(self.mood, "idle"),
            "intensity": round(self.intensity, 3),
        }

    def tone(self, fallback: str = "") -> str:
        """Natural-language tone for the current mood."""
        base = self._DEFAULT_TONE.get(self.mood, "")
        return base or fallback

    def decorate(self, message: str) -> str:
        """Attach emotional tone to a final message (no secrets)."""
        tone = self.tone()
        if tone and tone not in message:
            return f"{message} {tone}"
        return message


# Module-level convenience — share one character state per process.
_shared_state: Optional[CharacterState] = None


def get_character_state() -> CharacterState:
    """Return the shared CharacterState instance."""
    global _shared_state
    if _shared_state is None:
        _shared_state = CharacterState()
    return _shared_state
