# ============================================================
# Companion message layer regression tests
# (character communication — friend tone, no spam, no clipping)
# ============================================================

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from companion_messages import (
    CompanionEvent,
    CompanionMessenger,
    companion_message,
    _MAX_BUBBLE_CHARS,
)


class FakeBubbleController:
    """Records what would be shown via the existing speech bubble."""

    def __init__(self):
        self.shown = []

    def show_speech_bubble(self, text, duration_ms=5000):
        self.shown.append(text)


# --- 1. character can receive a companion message -------------

def test_messenger_delivers_message():
    ctrl = FakeBubbleController()
    m = CompanionMessenger(ctrl)
    msg = m.announce(CompanionEvent.TASK_STARTED, force=True)
    assert msg is not None
    assert ctrl.shown == [msg]


# --- 2/7. natural tone; internal technical names never shown --

@pytest.mark.parametrize("event", list(CompanionEvent))
def test_no_internal_identifiers(event):
    text = companion_message(event, "ActionType.OPEN_URL browser_skill verification_status")
    for bad in ("ActionType", "OPEN_URL", "browser_skill", "verification_status",
                "confidence=", "{", "}", "[", "]", "<", ">"):
        assert bad not in text


# --- 3. long messages wrap / never exceed bubble budget -------

def test_long_message_truncated_to_bubble_budget():
    text = companion_message(
        CompanionEvent.TASK_STARTED,
        "x" * 400,  # huge detail must never enter the bubble
        0,
    )
    assert len(text) <= _MAX_BUBBLE_CHARS


# --- 4. anti-spam: multiple rapid messages do not overlap -----

def test_rapid_messages_rate_limited():
    ctrl = FakeBubbleController()
    m = CompanionMessenger(ctrl)
    m.announce(CompanionEvent.MEANINGFUL_STEP_STARTED, force=True)  # 1st passes
    m.announce(CompanionEvent.MEANINGFUL_STEP_COMPLETED)            # skipped
    m.announce(CompanionEvent.MEANINGFUL_STEP_STARTED)              # skipped
    assert len(ctrl.shown) == 1  # no stacking / overlap


def test_important_events_bypass_rate_limit():
    ctrl = FakeBubbleController()
    m = CompanionMessenger(ctrl)
    m.announce(CompanionEvent.TASK_STARTED, force=True)
    m.announce(CompanionEvent.RECOVERY_STARTED)     # important
    m.announce(CompanionEvent.USER_CONFIRMATION_REQUIRED)  # important
    assert len(ctrl.shown) == 3


# --- 5. disabled/absent controller is safe --------------------

def test_disabled_messenger_shows_nothing():
    ctrl = FakeBubbleController()
    m = CompanionMessenger(ctrl, enabled=False)
    assert m.announce(CompanionEvent.TASK_STARTED, force=True) is None
    assert ctrl.shown == []
    m2 = CompanionMessenger(None)
    assert m2.announce(CompanionEvent.TASK_COMPLETED, force=True) is None


# --- 6. lifecycle: start -> progress -> completion ------------

def test_task_lifecycle_produces_sensible_sequence():
    ctrl = FakeBubbleController()
    m = CompanionMessenger(ctrl)
    m.announce(CompanionEvent.TASK_STARTED, force=True)
    m.announce(CompanionEvent.MEANINGFUL_STEP_COMPLETED, force=True)
    m.announce(CompanionEvent.TASK_COMPLETED, force=True)
    assert len(ctrl.shown) == 3
    assert all(isinstance(s, str) and s for s in ctrl.shown)


# --- 7. recovery produces a natural recovery message ----------

def test_recovery_flow_messages():
    ctrl = FakeBubbleController()
    m = CompanionMessenger(ctrl)
    m.announce(CompanionEvent.RECOVERY_STARTED, force=True)
    m.announce(CompanionEvent.RECOVERY_SUCCEEDED, force=True)
    assert "didn't work" in ctrl.shown[0] or "another way" in ctrl.shown[0] \
        or "Hiccup" in ctrl.shown[0]
    assert "Fixed it" in ctrl.shown[1] or "sorted" in ctrl.shown[1]


# --- 8. generic: no app/task hardcoding -----------------------

def test_templates_are_generic():
    for templates in [
        companion_message(e, variant=v)
        for e in CompanionEvent
        for v in range(4)
    ]:
        low = templates.lower()
        for app in ("instagram", "youtube", "github", "chrome", "exe", "installer"):
            assert app not in low
