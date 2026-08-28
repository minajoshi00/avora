"""
Phase 3 - Contextual Awareness test suite.

Covers:
  * Context available (with permissions enabled)
  * Context unavailable (sources missing / raising)
  * Permission disabled (activity_awareness.enabled=False)
  * Privacy mode (window titles hidden)
  * Graceful fallback (no crash, local time always present)
  * AI context injection (get_context includes provider output)

Run from repo root:
    python "avora backend/tests/test_contextual_awareness.py"
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
    """Set up isolated settings for testing."""
    import app_paths
    import settings as settings_mod

    app_paths.APP_DATA_DIR = Path(tmp_dir)
    # Point settings at a non-existent file so defaults apply;
    # set_setting writes to the temp file during the test.
    settings_mod.SETTINGS_FILE = Path(tmp_dir) / "settings.json"

    return settings_mod


def main():
    print("=" * 60)
    print("PHASE 3 - CONTEXTUAL AWARENESS TESTS")
    print("=" * 60)

    tmp = tempfile.mkdtemp(prefix="avora_ctx_test_")
    settings_mod = make_env(tmp)

    from core import context_provider

    # --------------------------------------------------------
    section("1. Context unavailable (all sources off)")
    # --------------------------------------------------------
    settings_mod.set_setting("activity_awareness.enabled", False)
    settings_mod.set_setting("screen_awareness.enabled", False)
    settings_mod.set_setting("memory.enabled", False)

    context = context_provider.get_current_context()
    check("returns dict", isinstance(context, dict))
    check("local time always present", "time_of_day" in context)
    check("no activity when disabled", "current_activity" not in context)
    check("no window title when disabled", "window_title" not in context)

    summary = context_provider.get_context_summary_text()
    check("summary still has local time", "Local time" in summary)

    # --------------------------------------------------------
    section("2. Permission disabled mid-flight")
    # --------------------------------------------------------
    settings_mod.set_setting("activity_awareness.enabled", True)
    settings_mod.set_setting("memory.enabled", True)

    # Note: get_companion_intelligence() lazily creates a real instance,
    # so context may include fresh default data - the key requirement
    # is that collection does not crash and stays permission-gated.
    context = context_provider.get_current_context()
    check("no crash without companion", isinstance(context, dict))
    check(
        "activity only present when permitted",
        ("current_activity" in context)
        == bool(settings_mod.get_setting("activity_awareness.enabled", True)),
    )

    # --------------------------------------------------------
    section("3. Context available (fake companion source)")

    # --------------------------------------------------------
    class FakeUserState:
        value = "focused"

    class FakeSnapshot:
        activity_type = "coding"
        window_title = "main.py - Visual Studio Code"
        process_name = "Code.exe"
        session_duration_minutes = 42.5
        idle_minutes = 0.5
        user_state = FakeUserState()

    class FakeContextTracker:
        def get_snapshot(self):
            return FakeSnapshot()

    class FakeGoals:
        def get_active_goals(self):
            return [
                {
                    "description": "learn Python",
                    "progress": 0.4,
                }
            ]

    class FakeCompanion:
        context = FakeContextTracker()
        goals = FakeGoals()

    import companion_intelligence as ci

    original_get = ci.get_companion_intelligence
    # The provider imports get_companion_intelligence at call time,
    # so patching the module attribute directly is sufficient.
    ci.get_companion_intelligence = lambda: FakeCompanion()
    try:
        context = context_provider.get_current_context()
        summary = context_provider.get_context_summary_text()
    finally:
        ci.get_companion_intelligence = original_get

    check("activity captured", context.get("current_activity") == "coding")
    check("window title captured", "main.py" in context.get("window_title", ""))
    check("user state captured", context.get("user_state") == "focused")
    check("goals captured", len(context.get("active_goals", [])) == 1)

    check("summary includes activity", "coding" in summary)
    check("summary includes goal", "learn Python" in summary)

    # --------------------------------------------------------
    section("4. Privacy mode hides window titles")
    # --------------------------------------------------------
    settings_mod.set_setting("activity_awareness.privacy_mode", True)

    ci.get_companion_intelligence = lambda: FakeCompanion()
    try:
        context = context_provider.get_current_context()
    finally:
        ci.get_companion_intelligence = original_get

    check("privacy mode hides window title", "window_title" not in context)
    check("privacy mode hides process", "process_name" not in context)
    check("activity type still visible", context.get("current_activity") == "coding")

    settings_mod.set_setting("activity_awareness.privacy_mode", False)

    # --------------------------------------------------------
    section("5. Invalid / raising sources degrade gracefully")

    # --------------------------------------------------------
    class BrokenCompanion:
        @property
        def context(self):
            raise RuntimeError("boom")

    ci.get_companion_intelligence = lambda: BrokenCompanion()
    try:
        context = context_provider.get_current_context()
    finally:
        ci.get_companion_intelligence = original_get

    check("broken source does not crash", isinstance(context, dict))
    check("local time survives broken source", "time_of_day" in context)

    # --------------------------------------------------------
    section("6. AI context injection")
    # --------------------------------------------------------
    import ai_logic

    context_text = ai_logic.get_context()
    check("get_context returns string", isinstance(context_text, str))
    check(
        "get_context includes current context section",
        "[Current Context]" in context_text,
    )
    check("get_context includes local time", "Local time" in context_text)

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
