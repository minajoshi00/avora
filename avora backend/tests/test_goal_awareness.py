"""
Phase 2 - Goal Awareness test suite.

Covers:
  * Goal creation
  * Goal updates (progress)
  * Goal completion
  * Goal status query
  * Goal history
  * Persistence across restart (subprocess)
  * Corrupted / missing goals file handling
  * Continuation candidate selection (for contextual reminders)
  * Existing GoalTracker functionality intact (achievements)

Run from repo root:
    python "avora backend/tests/test_goal_awareness.py"
"""

import json
import os
import subprocess
import sys
import tempfile
import time
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
    """Import companion_intelligence with goals file in temp dir."""
    import importlib

    import app_paths
    import settings as settings_mod

    app_paths.APP_DATA_DIR = Path(tmp_dir)
    settings_mod.SETTINGS_FILE = Path(tmp_dir) / "settings.json"

    import companion_intelligence as ci

    importlib.reload(ci)
    return ci


def main():
    print("=" * 60)
    print("PHASE 2 - GOAL AWARENESS TESTS")
    print("=" * 60)

    tmp = tempfile.mkdtemp(prefix="avora_goal_test_")
    ci = make_module(tmp)
    goals_file = Path(tmp) / "goals.json"

    # --------------------------------------------------------
    section("1. Goal creation")
    # --------------------------------------------------------
    tracker = ci.GoalTracker()
    tracker.set_active_goal("learn Python", category="learning")
    status = tracker.get_goal_status("learn Python")
    check("goal created", status is not None)
    check("goal not completed", status is not None and status["completed"] is False)
    check("goals file persisted", goals_file.exists())

    # --------------------------------------------------------
    section("2. Goal updates")
    # --------------------------------------------------------
    completed_signal = tracker.update_goal_progress("learn Python", 0.3)
    status = tracker.get_goal_status("learn Python")
    check(
        "progress updated",
        status is not None and abs(status["progress"] - 0.3) < 1e-6,
    )
    check("not complete yet", completed_signal is False)

    # --------------------------------------------------------
    section("3. Goal completion")
    # --------------------------------------------------------
    done = tracker.complete_goal("learn Python")
    check("complete returns True", done is True)
    again = tracker.complete_goal("learn Python")
    check("double complete returns False", again is False)
    history = tracker.get_goal_history()
    check("completed goal in history", len(history) == 1)
    active = tracker.get_active_goals()
    check(
        "completed goal not in active list",
        all(g["description"] != "learn Python" for g in active),
    )

    # --------------------------------------------------------
    section("4. Goal re-activation")
    # --------------------------------------------------------
    tracker.set_active_goal("learn Python", category="learning")
    status = tracker.get_goal_status("learn Python")
    check(
        "re-activated goal is incomplete again",
        status is not None and status["completed"] is False,
    )

    # --------------------------------------------------------
    section("5. Continuation candidate (contextual reminders)")
    # --------------------------------------------------------
    # Make a goal look idle by backdating last_active
    tracker.set_active_goal("build a rocket", category="project")
    raw = json.loads(goals_file.read_text(encoding="utf-8"))
    for goal in raw["goals"]:
        if goal["description"] == "build a rocket":
            goal["last_active"] = time.time() - 3 * 3600  # idle 3h
    goals_file.write_text(json.dumps(raw), encoding="utf-8")

    fresh_tracker = ci.GoalTracker()  # reload from disk
    candidate = fresh_tracker.get_continuation_candidate()
    check(
        "idle goal becomes continuation candidate",
        candidate is not None and candidate["description"] == "build a rocket",
    )

    recent = fresh_tracker.get_continuation_candidate(max_idle_hours=2.0)
    check(
        "recently-active goal excluded when window small",
        recent is None or recent["description"] != "build a rocket",
    )

    # --------------------------------------------------------
    section("6. Persistence across restart (fresh process)")
    # --------------------------------------------------------
    # Re-complete "learn Python" so history has an entry to verify
    tracker.complete_goal("learn Python")

    child_lines = [
        "import sys",
        f"sys.path.insert(0, r'{BACKEND_DIR}')",
        "import app_paths, pathlib",
        f"app_paths.APP_DATA_DIR = pathlib.Path(r'{tmp}')",
        "import settings",
        f"settings.SETTINGS_FILE = pathlib.Path(r'{tmp}') / 'settings.json'",
        "import companion_intelligence as ci",
        "t = ci.GoalTracker()",
        "s = t.get_goal_status('build a rocket')",
        "h = t.get_goal_history()",
        "print('CHILD_RESULT', s is not None, len(h) >= 1)",
    ]
    newline = chr(10)
    child_script = (
        "; ".join(child_lines)
        .replace("; import", newline + "import")
        .replace("; t =", newline + "t =")
        .replace("; s =", newline + "s =")
        .replace("; h =", newline + "h =")
        .replace("; print(", newline + "print(")
    )

    result = subprocess.run(
        [sys.executable, "-c", child_script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    child_line = ""
    for line in result.stdout.splitlines():
        if line.startswith("CHILD_RESULT"):
            child_line = line
            break
    parts = child_line.split()
    persisted_ok = len(parts) == 3 and parts[1] == "True" and parts[2] == "True"
    check(
        "goals persist across restart",
        persisted_ok,
        detail=result.stdout + result.stderr,
    )

    # --------------------------------------------------------
    section("7. Corrupted / missing goals file")
    # --------------------------------------------------------
    goals_file.write_text("{ corrupted !!!", encoding="utf-8")
    corrupt_tracker = ci.GoalTracker()
    check("corrupted file -> empty goals safely", corrupt_tracker._goals == [])

    os.remove(goals_file)
    missing_tracker = ci.GoalTracker()
    check("missing file -> no crash", missing_tracker._goals == [])
    missing_tracker.set_active_goal("post corruption goal")
    check(
        "works after recovery",
        missing_tracker.get_goal_status("post corruption goal") is not None,
    )

    # --------------------------------------------------------
    section("8. Existing functionality intact (achievements)")
    # --------------------------------------------------------
    tracker.add_achievement("Test Win", "did a thing", importance=0.5)
    achievements = tracker.get_recent_achievements(5)
    check(
        "achievements still work", any(a["title"] == "Test Win" for a in achievements)
    )
    check("has_recent_achievement works", tracker.has_recent_achievement(minutes=5))

    # Stale-goal behavior still applies (default 4h)
    stale_tracker = ci.GoalTracker()
    stale_tracker.set_active_goal("old goal")
    raw = json.loads(goals_file.read_text(encoding="utf-8"))
    for goal in raw["goals"]:
        if goal["description"] == "old goal":
            goal["last_active"] = time.time() - 10 * 3600  # 10h old
    goals_file.write_text(json.dumps(raw), encoding="utf-8")
    reloaded = ci.GoalTracker()
    check(
        "stale goal filtered from active list",
        all(g["description"] != "old goal" for g in reloaded.get_active_goals()),
    )

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
