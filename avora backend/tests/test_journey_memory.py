"""
Phase 1 - Journey Memory test suite.

Covers:
  * Create journey memories (all types)
  * Persistence across restart (subprocess re-import)
  * Retrieval correctness
  * Unrelated memories are not incorrectly injected
  * Empty memory handling
  * Corrupted / missing memory file handling
  * Sensitive information rejection
  * Deduplication / reinforcement
  * Completion status
  * AI context formatting

Run from repo root:
    python "avora backend/tests/test_journey_memory.py"
"""

import os
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
    """Import memory.py with MEMORY_FILE pointed at a temp location."""
    import importlib

    import app_paths
    import settings as settings_mod

    # Point APP_DATA_DIR at the temp dir before importing memory
    app_paths.APP_DATA_DIR = Path(tmp_dir)

    # Force settings to use defaults (no user settings.json interference)
    settings_mod.SETTINGS_FILE = Path(tmp_dir) / "settings.json"

    import memory

    importlib.reload(memory)
    memory.MEMORY_FILE = Path(tmp_dir) / "memories.json"
    return memory


def main():
    print("=" * 60)
    print("PHASE 1 - JOURNEY MEMORY TESTS")
    print("=" * 60)

    tmp = tempfile.mkdtemp(prefix="avora_mem_test_")
    memory = make_module(tmp)

    # --------------------------------------------------------
    section("1. Create journey memories")
    # --------------------------------------------------------
    ok1 = memory.add_journey_memory("project", "building an AI Minecraft companion")
    ok2 = memory.add_journey_memory("task", "learn Python")
    ok3 = memory.add_journey_memory("problem", "fixing the analytics system")
    ok4 = memory.add_journey_memory("decision", "chose SQLite for storage")
    ok5 = memory.add_journey_memory("milestone", "finished the login screen")
    check("create project memory", ok1 is True)
    check("create task memory", ok2 is True)
    check("create problem memory", ok3 is True)
    check("create decision memory", ok4 is True)
    check("create milestone memory", ok5 is True)

    invalid_type = memory.add_journey_memory("banana", "not a type")
    check("reject invalid memory type", invalid_type is False)

    # --------------------------------------------------------
    section("2. Deduplication / reinforcement")
    # --------------------------------------------------------
    reinforce = memory.add_journey_memory(
        "project", "building an AI Minecraft companion"
    )
    check("duplicate reinforces instead of duplicating", reinforce is True)
    projects = memory.get_journey_memories("project")
    matching = [p for p in projects if "minecraft" in str(p.get("text", "")).lower()]
    check("only one minecraft project entry", len(matching) == 1)
    if matching:
        check(
            "mention count incremented",
            int(matching[0].get("times_mentioned", 0)) == 2,
        )

    # --------------------------------------------------------
    section("3. Retrieval")
    # --------------------------------------------------------
    tasks = memory.get_journey_memories("task")
    check(
        "task retrieval returns learn python",
        any("python" in str(t.get("text", "")).lower() for t in tasks),
    )
    problems = memory.get_journey_memories("problem")
    check(
        "problem retrieval returns analytics",
        any("analytics" in str(p.get("text", "")).lower() for p in problems),
    )

    search_results = memory.search_journey_memories("minecraft")
    check("keyword search finds minecraft project", len(search_results) == 1)

    empty_search = memory.search_journey_memories("quantum flux capacitor")
    check("unrelated keyword returns nothing", len(empty_search) == 0)

    # --------------------------------------------------------
    section("4. Completion")
    # --------------------------------------------------------
    completed = memory.complete_journey_memory("finished the login screen")
    check("complete milestone works", completed is True)
    active_milestones = memory.get_journey_memories("milestone", status="active")
    done_milestones = memory.get_journey_memories("milestone", status="completed")
    check("completed milestone no longer active", len(active_milestones) == 0)
    check(
        "completed milestone appears with completed status",
        len(done_milestones) == 1,
    )

    # --------------------------------------------------------
    section("5. Auto-extraction from messages")
    # --------------------------------------------------------
    extracted = memory.extract_journey_memories(
        "I'm building an AI Minecraft companion"
    )
    check(
        "extracts project statement",
        len(extracted) >= 1 and extracted[0][0] == "project",
    )

    extracted_task = memory.extract_journey_memories("I want to learn Rust this year")
    check(
        "extracts task statement",
        len(extracted_task) >= 1 and extracted_task[0][0] == "task",
    )

    extracted_problem = memory.extract_journey_memories(
        "I'm stuck on the database migration"
    )
    check(
        "extracts problem statement",
        len(extracted_problem) >= 1 and extracted_problem[0][0] == "problem",
    )

    none_extracted = memory.extract_journey_memories("what is the weather today?")
    check("plain question extracts nothing", len(none_extracted) == 0)

    stored = memory.capture_journey_memories("I'm working on a rocket physics engine")
    check(
        "capture stores extracted memory",
        len(stored) == 1 and stored[0][0] == "project",
    )

    # --------------------------------------------------------
    section("6. Sensitive information rejection")
    # --------------------------------------------------------
    sensitive = memory.add_journey_memory("decision", "my password is hunter2secret")
    check("rejects sensitive content", sensitive is False)

    sensitive_extract = memory.extract_journey_memories(
        "my api key is sk-abc123def456ghi789"
    )
    check("extraction skips sensitive message", len(sensitive_extract) == 0)

    # --------------------------------------------------------
    section("7. AI context formatting")
    # --------------------------------------------------------
    context = memory.get_journey_context_for_ai()
    check("journey context non-empty", isinstance(context, str) and len(context) > 0)
    check("journey context includes project", "minecraft" in context.lower())
    check("completed milestone marked", "(completed)" in context)

    full_text = memory.get_memory_text()
    check("get_memory_text includes journey section", "Ongoing journey" in full_text)

    # Add a regular memory and verify both sections render
    memory.add_memory("User likes coffee", "preference")
    full_text2 = memory.get_memory_text()
    check("regular memory still rendered", "coffee" in full_text2.lower())

    # --------------------------------------------------------
    section("8. Empty memory handling")
    # --------------------------------------------------------
    memory.clear_memories()
    check("clear empties store", memory.memory_count() == 0)
    check("empty journey list returns []", memory.get_journey_memories() == [])
    check(
        "empty context returns empty string", memory.get_journey_context_for_ai() == ""
    )
    check("empty search returns []", memory.search_journey_memories("x") == [])
    check(
        "empty get_memory_text handled",
        memory.get_memory_text() == "No memories stored yet.",
    )

    # --------------------------------------------------------
    section("9. Missing / corrupted memory file")
    # --------------------------------------------------------
    mem_file = Path(tmp) / "memories.json"
    if mem_file.exists():
        os.remove(mem_file)
    check("missing file -> load returns []", memory.load_memories() == [])
    check("missing file -> count 0", memory.memory_count() == 0)

    mem_file.write_text("{ this is not valid json !!!", encoding="utf-8")
    check("corrupted file -> load returns [] safely", memory.load_memories() == [])

    mem_file.write_text('{"not": "a list"}', encoding="utf-8")
    check("wrong structure -> load returns [] safely", memory.load_memories() == [])

    # Recovery: after corruption, adding a memory must work again
    recovered = memory.add_journey_memory("idea", "add dark mode toggle")
    check("recovers after corruption", recovered is True)
    check("memory usable after recovery", memory.memory_count() == 1)

    # --------------------------------------------------------
    section("10. Persistence across restart (fresh process)")
    # --------------------------------------------------------
    memory.clear_memories()
    memory.add_journey_memory("project", "persistence probe alpha")
    memory.add_journey_memory("task", "persistence probe beta")

    child_lines = [
        "import sys",
        f"sys.path.insert(0, r'{BACKEND_DIR}')",
        "import app_paths, pathlib",
        f"app_paths.APP_DATA_DIR = pathlib.Path(r'{tmp}')",
        "import settings",
        f"settings.SETTINGS_FILE = pathlib.Path(r'{tmp}') / 'settings.json'",
        "import memory",
        f"memory.MEMORY_FILE = pathlib.Path(r'{tmp}') / 'memories.json'",
        "projects = memory.get_journey_memories('project')",
        "tasks = memory.get_journey_memories('task')",
        "ok_a = any('alpha' in str(p.get('text','')) for p in projects)",
        "ok_b = any('beta' in str(t.get('text','')) for t in tasks)",
        "print('CHILD_RESULT', ok_a, ok_b)",
    ]
    child_script = "; ".join(child_lines).replace("; import", "\nimport")

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
        "memories persist across restart",
        persisted_ok,
        detail=result.stdout + result.stderr,
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
