"""
Phase 6 - Learn User Working Preferences test suite.

Covers:
  * Set preference -> restart -> verify -> update -> verify
  * Forget preference
  * Sensitive attributes never stored
  * Detection from user messages
  * AI context injection
  * Empty preferences

Run from repo root:
    python "avora backend/tests/test_user_preferences.py"
"""

import subprocess
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


def make_module(tmp_dir):
    import importlib

    import app_paths
    import settings as settings_mod

    app_paths.APP_DATA_DIR = Path(tmp_dir)
    settings_mod.SETTINGS_FILE = Path(tmp_dir) / "settings.json"

    import memory

    importlib.reload(memory)
    memory.MEMORY_FILE = Path(tmp_dir) / "memories.json"
    memory._preferences_cache = None
    return memory


def main():
    print("=" * 60)
    print("PHASE 6 - USER PREFERENCES TESTS")
    print("=" * 60)

    tmp = tempfile.mkdtemp(prefix="avora_pref_test_")
    memory = make_module(tmp)

    # --------------------------------------------------------
    section("1. Set preference")
    # --------------------------------------------------------
    ok = memory.set_user_preference("response_style", "concise explanations")
    check("preference stored", ok is True)
    value = memory.get_user_preference("response_style")
    check("preference retrieved", value == "concise explanations")

    # --------------------------------------------------------
    section("2. Update preference")
    # --------------------------------------------------------
    updated = memory.set_user_preference("response_style", "very concise answers")
    check("update succeeds", updated is True)
    new_value = memory.get_user_preference("response_style")
    check("update applied", new_value == "very concise answers")

    all_prefs = memory.get_all_preferences()
    check(
        "no duplicate keys",
        list(all_prefs.keys()).count("response_style") == 1,
    )

    # --------------------------------------------------------
    section("3. Persistence across restart (fresh process)")
    # --------------------------------------------------------
    child_lines = [
        "import sys",
        f"sys.path.insert(0, r'{BACKEND_DIR}')",
        "import app_paths, pathlib",
        f"app_paths.APP_DATA_DIR = pathlib.Path(r'{tmp}')",
        "import settings",
        f"settings.SETTINGS_FILE = pathlib.Path(r'{tmp}') / 'settings.json'",
        "import memory",
        f"memory.MEMORY_FILE = pathlib.Path(r'{tmp}') / 'memories.json'",
        "v = memory.get_user_preference('response_style')",
        "print('CHILD_RESULT', v)",
    ]
    newline = chr(10)
    child_script = (
        "; ".join(child_lines)
        .replace("; import", newline + "import")
        .replace("; v =", newline + "v =")
        .replace("; print(", newline + "print(")
    )

    result = subprocess.run(
        [sys.executable, "-c", child_script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    persisted_ok = "concise" in result.stdout and "very concise" in result.stdout
    check(
        "preferences persist across restart",
        persisted_ok,
        detail=result.stdout + result.stderr,
    )

    # --------------------------------------------------------
    section("4. Forget preference")
    # --------------------------------------------------------
    forgotten = memory.forget_user_preference("response_style")
    check("forget works", forgotten is True)
    gone = memory.get_user_preference("response_style")
    check("preference gone", gone is None)

    again = memory.forget_user_preference("response_style")
    check("double forget returns False", again is False)

    # --------------------------------------------------------
    section("5. Sensitive attributes rejected")
    # --------------------------------------------------------
    sensitive_tests = [
        ("age", "25 years old"),
        ("health", "diagnosed with something"),
        ("salary", "50000 per year"),
        ("password", "hunter2"),
    ]

    for key, value in sensitive_tests:
        stored = memory.set_user_preference(key, value)
        check(f"sensitive '{key}' rejected", stored is False)

    check(
        "no sensitive prefs stored",
        all(k not in memory.get_all_preferences() for k, _ in sensitive_tests),
    )

    # --------------------------------------------------------
    section("6. Detection from messages")
    # --------------------------------------------------------
    detected = memory.detect_preferences("I prefer short responses please")
    check("detects 'prefer' statement", len(detected) >= 1)

    detected_no_emoji = memory.detect_preferences("no emojis in replies")
    check("detects no-emoji preference", len(detected_no_emoji) >= 1)

    not_detected = memory.detect_preferences("what is the weather today?")
    check("plain question detects nothing", len(not_detected) == 0)

    captured = memory.capture_preferences("I prefer fixing one problem at a time")
    check("capture stores preference", len(captured) >= 1)
    check(
        "captured preference retrievable",
        any("problem" in str(v).lower() for v in memory.get_all_preferences().values()),
    )

    # --------------------------------------------------------
    section("7. AI context injection")
    # --------------------------------------------------------
    context = memory.get_preferences_context_for_ai()
    check(
        "preferences context non-empty", isinstance(context, str) and len(context) > 0
    )
    check(
        "context includes learned pref",
        "one problem at a time" in context.lower(),
    )

    # Clear and verify empty handling
    for key in list(memory.get_all_preferences().keys()):
        memory.forget_user_preference(key)

    empty_context = memory.get_preferences_context_for_ai()
    check("empty prefs -> empty context", empty_context == "")

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
