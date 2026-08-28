"""
Phase 4 - Proactive Suggestions test suite.

Covers:
  * Relevant context (goal continuation suggestion fires)
  * Irrelevant context (no goal/memory -> no suggestion)
  * Disabled suggestions (activity_awareness.proactive_notifications=False)
  * Missing context (no goals/memories -> None)
  * Repeated triggers (cooldown prevents spam)
  * Existing suggestion engine still works

Run from repo root:
    python "avora backend/tests/test_proactive_suggestions.py"
"""

import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name} {detail}")


def section(title):
    print()
    print(f"[{title}]")
    print("-" * 50)


def make_env(tmp_dir):
    import app_paths
    import settings as settings_mod

    app_paths.APP_DATA_DIR = Path(tmp_dir)
    settings_mod.SETTINGS_FILE = Path(tmp_dir) / "settings.json"
    return settings_mod


def main():
    print("=" * 60)
    print("PHASE 4 - PROACTIVE SUGGESTIONS TESTS")
    print("=" * 60)

    tmp = tempfile.mkdtemp(prefix="avora_sugg_test_")
    settings_mod = make_env(tmp)

    from companion_intelligence import InterventionType, ProactiveSuggester

    suggester = ProactiveSuggester("friendly")

    # --------------------------------------------------------
    section("1. Relevant context - goal continuation")
    # --------------------------------------------------------
    settings_mod.set_setting("activity_awareness.proactive_notifications", True)

    goal = {"description": "learn Python", "progress": 0.4}
    suggestion = suggester.get_goal_suggestion(goal)
    check("goal suggestion fires", suggestion is not None)
    check(
        "goal suggestion mentions goal",
        suggestion is not None and "learn Python" in suggestion["message"],
    )
    check(
        "goal suggestion is proactive type",
        suggestion is not None
        and suggestion["type"] == InterventionType.PROACTIVE_SUGGESTION,
    )

    # --------------------------------------------------------
    section("2. Repeated trigger blocked by cooldown")
    # --------------------------------------------------------
    second = suggester.get_goal_suggestion(goal)
    check("immediate repeat blocked", second is None)

    # --------------------------------------------------------
    section("3. Disabled suggestions")
    # --------------------------------------------------------
    settings_mod.set_setting("activity_awareness.proactive_notifications", False)
    disabled = suggester.get_goal_suggestion(goal)
    check("disabled -> no goal suggestion", disabled is None)

    memory = {"text": "building an AI Minecraft companion"}
    disabled_mem = suggester.get_memory_recall_suggestion(memory)
    check("disabled -> no memory suggestion", disabled_mem is None)

    settings_mod.set_setting("activity_awareness.proactive_notifications", True)

    # --------------------------------------------------------
    section("4. Memory recall suggestion")
    # --------------------------------------------------------
    # Use a fresh suggester to avoid the cooldown from section 2
    fresh = ProactiveSuggester("friendly")
    mem_suggestion = fresh.get_memory_recall_suggestion(memory)
    check("memory suggestion fires", mem_suggestion is not None)
    check(
        "memory suggestion mentions memory",
        mem_suggestion is not None and "Minecraft" in mem_suggestion["message"],
    )

    # --------------------------------------------------------
    section("5. Irrelevant / missing context")
    # --------------------------------------------------------
    empty_goal = suggester.get_goal_suggestion({})
    check("empty goal -> no suggestion", empty_goal is None)

    empty_mem = suggester.get_memory_recall_suggestion({})
    check("empty memory -> no suggestion", empty_mem is None)

    # --------------------------------------------------------
    section("6. Existing suggestion engine intact")
    # --------------------------------------------------------
    from companion_intelligence import CompanionMood, ContextSnapshot, UserState

    snapshot = ContextSnapshot()
    snapshot.activity_type = "coding"
    snapshot.user_state = UserState.STUCK
    snapshot.activity_duration_minutes = 45.0
    snapshot.session_duration_minutes = 60.0

    existing = suggester.get_suggestion(snapshot, CompanionMood.CONCERNED)
    check("existing engine still returns suggestion", existing is not None)

    break_reminder = suggester.get_break_reminder(snapshot)
    check("break reminder still works", break_reminder is not None)

    # --------------------------------------------------------
    print()
    print("=" * 60)
    print(f"RESULTS: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 60)

    if FAIL:
        print("Failed tests:")
        for name in FAIL:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
