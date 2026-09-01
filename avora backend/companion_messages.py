# ============================================================
# companion_messages.py
# Friend-tone companion communication layer.
#
# Maps meaningful task-state events to short, natural companion
# messages and delivers them through the existing speech bubble
# WITHOUT spamming: rate-limited, queued/replace-only, and never
# dumps long technical content into the bubble.
#
# 100% additive. Does not touch Agent Mode, planner, perception,
# verification, recovery, confirmation gates, or the chat UI.
# ============================================================

import time
from enum import Enum
from typing import Optional


class CompanionEvent(Enum):
    """Meaningful task-state events the character can react to."""
    TASK_STARTED = "task_started"
    PLANNING_STARTED = "planning_started"
    MEANINGFUL_STEP_STARTED = "meaningful_step_started"
    MEANINGFUL_STEP_COMPLETED = "meaningful_step_completed"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_SUCCEEDED = "recovery_succeeded"
    USER_CONFIRMATION_REQUIRED = "user_confirmation_required"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


# Events important enough to bypass rate limiting.
_IMPORTANT = {
    CompanionEvent.RECOVERY_STARTED,
    CompanionEvent.RECOVERY_SUCCEEDED,
    CompanionEvent.USER_CONFIRMATION_REQUIRED,
    CompanionEvent.TASK_FAILED,
    CompanionEvent.TASK_COMPLETED,
}

# Max characters a speech bubble should ever carry. Longer content
# belongs in the chat panel, not the character bubble.
_MAX_BUBBLE_CHARS = 120

# Minimum seconds between spontaneous (non-important) messages.
_MIN_INTERVAL = 4.0


# Natural, friend-tone templates. Deliberately generic — never tied
# to specific apps (Instagram/EXE/GitHub) and never containing
# internal identifiers (action names, skills, JSON, confidence).
_TEMPLATES = {
    CompanionEvent.TASK_STARTED: [
        "Got you bro, I'm on it 👀",
        "Yep bro, give me a sec.",
        "On it — let me take a look.",
    ],
    CompanionEvent.PLANNING_STARTED: [
        "Let me figure out the best way to do this…",
        "Thinking about how to approach this 🤔",
    ],
    CompanionEvent.MEANINGFUL_STEP_STARTED: [
        "I'm checking it now…",
        "Working on this part 👀",
        "Give me a sec, almost there.",
    ],
    CompanionEvent.MEANINGFUL_STEP_COMPLETED: [
        "Found it.",
        "Nice, that part's done.",
        "Okay, that worked.",
    ],
    CompanionEvent.RECOVERY_STARTED: [
        "Hmm, that didn't work. Let me figure out what went wrong.",
        "Hiccup — let me try another way 👀",
    ],
    CompanionEvent.RECOVERY_SUCCEEDED: [
        "Fixed it. Trying again.",
        "Okay, sorted. Continuing 🔥",
    ],
    CompanionEvent.USER_CONFIRMATION_REQUIRED: [
        "I need your confirmation before I continue.",
        "Your call bro — confirm and I'll proceed.",
    ],
    CompanionEvent.TASK_COMPLETED: [
        "Done bro 🔥",
        "We're good ✅",
        "All set bro.",
    ],
    CompanionEvent.TASK_FAILED: [
        "Couldn't get it done this time — sorry bro 😭",
        "That one beat me. Want me to try again?",
    ],
}


def companion_message(event: CompanionEvent, detail: str = "",
                      variant: int = 0) -> str:
    """Return a short natural companion message for a task event.

    `detail` is intentionally NOT echoed raw — internal identifiers,
    JSON, action names or long logs never reach the bubble.
    """
    templates = _TEMPLATES.get(event, ["On it 👀"])
    base = templates[variant % len(templates)]
    if detail and len(detail) <= 40 and not any(
        ch in detail for ch in "{}[]<>="
    ):
        # Only tiny, plain hints are woven in; anything longer or
        # technical stays out of the character's mouth.
        base = f"{base} ({detail})"
    return base[:_MAX_BUBBLE_CHARS]


class CompanionMessenger:
    """Rate-limited bridge between task events and the speech bubble.

    Uses the EXISTING CompanionBehaviorController.show_speech_bubble —
    the bubble replaces its content in place, so messages never overlap.
    """

    def __init__(self, behavior_controller=None, enabled: bool = True):
        self.controller = behavior_controller
        self.enabled = enabled
        self._last_shown = 0.0
        self._variant = 0

    def announce(self, event: CompanionEvent, detail: str = "",
                 force: bool = False) -> Optional[str]:
        """Show a companion message for `event` (rate-limited unless
        `force` or the event is important). Returns the message shown."""
        if not self.enabled or self.controller is None:
            return None
        now = time.monotonic()
        important = event in _IMPORTANT
        if not force and not important and (now - self._last_shown) < _MIN_INTERVAL:
            return None  # anti-spam: silently skip tiny rapid events
        self._variant += 1
        message = companion_message(event, detail, self._variant)
        try:
            self.controller.show_speech_bubble(message)
        except Exception:
            return None
        self._last_shown = now
        return message
