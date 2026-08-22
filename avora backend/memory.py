# ============================================================
# memory.py
# AI Friend - Advanced Long-Term Memory System
# ============================================================

import json
import os
import re
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from app_paths import APP_DATA_DIR
from settings import get_setting

# ============================================================
# MEMORY FILE
# ============================================================

MEMORY_FILE = APP_DATA_DIR / "memories.json"

_memory_lock = threading.RLock()


# ============================================================
# SETTINGS HELPERS
# ============================================================


def _memory_enabled():
    return bool(
        get_setting(
            "memory.enabled",
            True,
        )
    )


def _auto_save_enabled():
    return bool(
        get_setting(
            "memory.auto_save",
            True,
        )
    )


def _max_memories():
    value = get_setting(
        "memory.max_memories",
        500,
    )

    try:
        return max(
            1,
            int(value),
        )

    except (TypeError, ValueError):
        return 500


# ============================================================
# SAFE FILE SAVE
# ============================================================


def _save_file(memories):
    """
    Saves memories atomically to prevent file corruption.
    """

    try:
        MEMORY_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=MEMORY_FILE.parent,
            delete=False,
            suffix=".tmp",
        ) as file:
            json.dump(
                memories,
                file,
                indent=4,
                ensure_ascii=False,
            )

            temporary_file = Path(file.name)

        os.replace(
            temporary_file,
            MEMORY_FILE,
        )

        return True

    except Exception as error:
        print(
            "MEMORY SAVE ERROR:",
            error,
        )

        return False


# ============================================================
# LOAD MEMORIES
# ============================================================


def load_memories():

    if not _memory_enabled():
        return []

    with _memory_lock:
        if not MEMORY_FILE.exists():
            _save_file([])

            return []

        try:
            with open(
                MEMORY_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                memories = json.load(file)

            if not isinstance(
                memories,
                list,
            ):
                return []

            return memories

        except (
            json.JSONDecodeError,
            OSError,
        ):
            print("MEMORY FILE ERROR: Could not read memories.json")

            return []


# ============================================================
# SAVE MEMORIES
# ============================================================


def save_memories(
    memories,
):

    if not _memory_enabled():
        return False

    if not _auto_save_enabled():
        return False

    if not isinstance(
        memories,
        list,
    ):
        return False

    with _memory_lock:
        return _save_file(memories)


# ============================================================
# ADD MEMORY
# ============================================================


def add_memory(
    memory_text,
    category="general",
):
    """Add a memory entry with optional category."""
    if not _memory_enabled():
        print("Memory is disabled in Settings.")
        return False

    if not _auto_save_enabled():
        print("Automatic memory saving is disabled.")
        return False

    if not memory_text:
        return False

    memory_text = str(memory_text).strip()
    category = str(category).strip().lower()

    if not memory_text:
        return False

    with _memory_lock:
        memories = load_memories()

        # Prevent duplicates
        normalized_text = memory_text.lower()
        for memory in memories:
            existing_text = str(memory.get("text", "")).strip().lower()
            if existing_text == normalized_text:
                return False

        # Max memory limit
        maximum = _max_memories()
        if len(memories) >= maximum:
            memories.pop(0)

        # Create memory
        new_memory = {
            "id": _generate_memory_id(memories),
            "text": memory_text,
            "category": category,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        memories.append(new_memory)
        return _save_file(memories)


# ============================================================
# GENERATE MEMORY ID
# ============================================================


def _generate_memory_id(
    memories,
):

    if not memories:
        return 1

    ids = []

    for memory in memories:
        try:
            ids.append(
                int(
                    memory.get(
                        "id",
                        0,
                    )
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

    return (
        max(
            ids,
            default=0,
        )
        + 1
    )


# ============================================================
# GET ALL MEMORIES
# ============================================================


def get_memories():

    if not _memory_enabled():
        return []

    return load_memories()


# ============================================================
# GET MEMORY TEXT FOR AI
# ============================================================


def get_memory_text():

    if not _memory_enabled():
        return "Long-term memory is disabled."

    memories = load_memories()

    if not memories:
        return "No memories stored yet."

    # Split journey memories (structured long-term context) from
    # regular memories. Journey memories are shown first, sorted by
    # importance, so the AI understands ongoing projects/goals.
    journey = []
    regular = []

    for memory in memories:
        category = str(
            memory.get(
                "category",
                "general",
            )
        )

        if category.startswith(_JOURNEY_CATEGORY_PREFIX):
            journey.append(memory)
        else:
            regular.append(memory)

    journey.sort(
        key=lambda m: (
            float(m.get("importance", 0.5)),
            int(m.get("times_mentioned", 1)),
        ),
        reverse=True,
    )

    memory_lines = []

    if journey:
        memory_lines.append("Ongoing journey (projects, problems, goals):")
        for memory in journey[:12]:
            jtype = str(memory.get("category", "")).replace(
                _JOURNEY_CATEGORY_PREFIX,
                "",
            )
            status = str(memory.get("status", "active"))
            suffix = " (completed)" if status == "completed" else ""
            memory_lines.append(f"- [{jtype}] {memory.get('text', '')}{suffix}")
        if regular:
            memory_lines.append("")

    for memory in regular:
        text = memory.get(
            "text",
            "",
        )

        category = memory.get(
            "category",
            "general",
        )

        memory_lines.append(f"- [{category}] {text}")

    return "\n".join(memory_lines)


# ============================================================
# SEARCH MEMORY
# ============================================================


def search_memory(
    keyword,
):

    if not _memory_enabled():
        return []

    if not keyword:
        return []

    keyword = str(keyword).lower().strip()

    memories = load_memories()

    results = []

    for memory in memories:
        text = str(
            memory.get(
                "text",
                "",
            )
        ).lower()

        category = str(
            memory.get(
                "category",
                "",
            )
        ).lower()

        if keyword in text or keyword in category:
            results.append(memory)

    return results


# ============================================================
# GET MEMORIES BY CATEGORY
# ============================================================


def get_memories_by_category(
    category,
):

    if not _memory_enabled():
        return []

    category = str(category).lower().strip()

    return [
        memory
        for memory in load_memories()
        if str(
            memory.get(
                "category",
                "",
            )
        ).lower()
        == category
    ]


# ============================================================
# DELETE ONE MEMORY
# ============================================================


def delete_memory(
    memory_id,
):

    if not _memory_enabled():
        return False

    memories = load_memories()

    updated_memories = [
        memory
        for memory in memories
        if str(
            memory.get(
                "id",
            )
        )
        != str(memory_id)
    ]

    if len(updated_memories) == len(memories):
        return False

    return _save_file(updated_memories)


# ============================================================
# DELETE MEMORY BY TEXT
# ============================================================


def delete_memory_by_text(
    memory_text,
):

    if not _memory_enabled():
        return False

    if not memory_text:
        return False

    target = str(memory_text).strip().lower()

    memories = load_memories()

    updated_memories = [
        memory
        for memory in memories
        if str(
            memory.get(
                "text",
                "",
            )
        )
        .strip()
        .lower()
        != target
    ]

    if len(updated_memories) == len(memories):
        return False

    return _save_file(updated_memories)


# ============================================================
# CLEAR ALL MEMORIES
# ============================================================


def clear_memories():

    if not _memory_enabled():
        return False

    return _save_file([])


# ============================================================
# MEMORY COUNT
# ============================================================


def memory_count():

    if not _memory_enabled():
        return 0

    return len(load_memories())


# ============================================================
# EXPORT MEMORIES
# ============================================================


def export_memories(
    file_path,
):

    if not _memory_enabled():
        return False

    try:
        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                load_memories(),
                file,
                indent=4,
                ensure_ascii=False,
            )

        return True

    except OSError:
        return False


# ============================================================
# IMPORT MEMORIES
# ============================================================


def import_memories(
    file_path,
):

    if not _memory_enabled():
        return False

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:
            memories = json.load(file)

        if not isinstance(
            memories,
            list,
        ):
            return False

        memories = memories[-_max_memories() :]

        return _save_file(memories)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return False


# ============================================================
# JOURNEY MEMORY (V2)
# ============================================================
# Structured long-term memory for meaningful context:
# projects, problems, decisions, ideas, preferences,
# milestones, and ongoing tasks.
#
# Journey memories live in the SAME memories.json file
# (single memory system, no duplicates) using the
# "journey:<type>" category. They carry importance,
# mention counts, and status so AVORA can recall them
# naturally over time.
# ============================================================

JOURNEY_TYPES = (
    "project",
    "problem",
    "decision",
    "idea",
    "preference",
    "milestone",
    "task",
)

_JOURNEY_CATEGORY_PREFIX = "journey:"

# Patterns used to auto-detect journey-worthy statements.
_JOURNEY_PATTERNS = (
    (
        "project",
        re.compile(
            r"\b(?:i(?:'m| am)|we(?:'re| are))\s+"
            r"(?:building|making|creating|developing|working on)\s+(.{3,120})"
        ),
    ),
    (
        "task",
        re.compile(
            r"\b(?:i\s+)?(?:want|need|plan)\s+to\s+"
            r"(?:learn|study|build|make|create|finish|complete)\s+(.{3,120})"
        ),
    ),
    (
        "problem",
        re.compile(
            r"\b(?:stuck on|struggling with|debugging|fixing|"
            r"having trouble with|can'?t\s+(?:figure out|solve))\s+(.{3,120})"
        ),
    ),
    (
        "decision",
        re.compile(
            r"\b(?:i|we)\s+(?:decided|chose|switched to|moved to)\s+"
            r"(?:to\s+)?(.{3,120})"
        ),
    ),
    (
        "milestone",
        re.compile(
            r"\b(?:i|we)\s+(?:finished|completed|shipped|launched|"
            r"finally\s+(?:fixed|solved))\s+(.{3,120})"
        ),
    ),
)

# Sensitive patterns that must never be stored.
_SENSITIVE_PATTERN = re.compile(
    r"(?:password|passwd|api[_\s-]?key|secret|token|credit[_\s-]?card|"
    r"\b\d{3}-\d{2}-\d{4}\b)",
    re.IGNORECASE,
)


def _is_sensitive(text):
    """Return True if the text looks like sensitive information."""

    if not text:
        return False

    return bool(_SENSITIVE_PATTERN.search(str(text)))


def add_journey_memory(
    memory_type,
    title,
    content="",
    importance=0.5,
):
    """
    Add or reinforce a structured journey memory.

    Returns True if stored/reinforced, False otherwise.
    Duplicate (type, title) entries reinforce the existing
    memory instead of creating duplicates.
    """

    if not _memory_enabled():
        return False

    if not _auto_save_enabled():
        return False

    memory_type = str(memory_type).strip().lower()

    if memory_type not in JOURNEY_TYPES:
        return False

    title = str(title).strip()

    if not title:
        return False

    if _is_sensitive(title):
        return False

    if len(title) > 200:
        title = title[:200]

    category = _JOURNEY_CATEGORY_PREFIX + memory_type

    with _memory_lock:
        memories = load_memories()

        normalized = title.lower()

        for memory in memories:
            if (
                str(
                    memory.get(
                        "category",
                        "",
                    )
                )
                != category
            ):
                continue

            if (
                str(
                    memory.get(
                        "text",
                        "",
                    )
                )
                .strip()
                .lower()
                == normalized
            ):
                # Reinforce the existing memory
                memory["times_mentioned"] = (
                    int(
                        memory.get(
                            "times_mentioned",
                            1,
                        )
                    )
                    + 1
                )

                memory["last_mentioned"] = datetime.now().isoformat(timespec="seconds")

                memory["importance"] = min(
                    1.0,
                    float(
                        memory.get(
                            "importance",
                            0.5,
                        )
                    )
                    + 0.05,
                )

                return _save_file(memories)

        maximum = _max_memories()

        if len(memories) >= maximum:
            memories.pop(0)

        new_memory = {
            "id": _generate_memory_id(memories),
            "text": title,
            "category": category,
            "content": str(content).strip()[:500],
            "importance": max(0.0, min(1.0, float(importance))),
            "times_mentioned": 1,
            "last_mentioned": datetime.now().isoformat(timespec="seconds"),
            "status": "active",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        memories.append(new_memory)

        return _save_file(memories)


def get_journey_memories(
    memory_type=None,
    min_importance=0.0,
    status=None,
):
    """Get journey memories, optionally filtered by type/importance/status."""

    if not _memory_enabled():
        return []

    memories = load_memories()

    results = []

    for memory in memories:
        category = str(
            memory.get(
                "category",
                "",
            )
        )

        if not category.startswith(_JOURNEY_CATEGORY_PREFIX):
            continue

        if memory_type is not None:
            expected = _JOURNEY_CATEGORY_PREFIX + str(memory_type).strip().lower()

            if category != expected:
                continue

        try:
            importance = float(
                memory.get(
                    "importance",
                    0.5,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            importance = 0.5

        if importance < min_importance:
            continue

        if status is not None:
            if str(
                memory.get(
                    "status",
                    "active",
                )
            ) != str(status):
                continue

        results.append(memory)

    results.sort(
        key=lambda m: (
            float(
                m.get(
                    "importance",
                    0.5,
                )
            ),
            int(
                m.get(
                    "times_mentioned",
                    1,
                )
            ),
        ),
        reverse=True,
    )

    return results


def search_journey_memories(
    keyword,
):
    """Search journey memories by keyword."""

    if not _memory_enabled():
        return []

    if not keyword:
        return []

    keyword = str(keyword).lower().strip()

    if not keyword:
        return []

    results = []

    for memory in get_journey_memories():
        text = str(
            memory.get(
                "text",
                "",
            )
        ).lower()

        if keyword in text:
            results.append(memory)

    return results


def complete_journey_memory(
    title,
):
    """Mark a journey memory as completed. Returns True on success."""

    if not _memory_enabled():
        return False

    title = str(title).strip().lower()

    if not title:
        return False

    with _memory_lock:
        memories = load_memories()

        for memory in memories:
            category = str(
                memory.get(
                    "category",
                    "",
                )
            )

            if not category.startswith(_JOURNEY_CATEGORY_PREFIX):
                continue

            if (
                str(
                    memory.get(
                        "text",
                        "",
                    )
                )
                .strip()
                .lower()
                == title
            ):
                memory["status"] = "completed"

                memory["last_mentioned"] = datetime.now().isoformat(timespec="seconds")

                return _save_file(memories)

    return False


def get_journey_context_for_ai(
    max_items=8,
):
    """
    Format journey memories for AI prompt injection.
    Returns an empty string when there is nothing meaningful.
    """

    if not _memory_enabled():
        return ""

    memories = get_journey_memories(
        min_importance=0.3,
    )[:max_items]

    if not memories:
        return ""

    lines = []

    for memory in memories:
        jtype = str(
            memory.get(
                "category",
                "",
            )
        ).replace(
            _JOURNEY_CATEGORY_PREFIX,
            "",
        )

        text = str(
            memory.get(
                "text",
                "",
            )
        )

        status = str(
            memory.get(
                "status",
                "active",
            )
        )

        line = f"- [{jtype}] {text}"

        if status == "completed":
            line += " (completed)"

        lines.append(line)

    return "\n".join(lines)


def extract_journey_memories(
    message,
):
    """
    Auto-detect journey-worthy statements in a user message.

    Returns a list of (memory_type, title) tuples.
    Does NOT store anything - storage is explicit.
    """

    if not message:
        return []

    text = str(message).strip()

    if len(text) < 8:
        return []

    if _is_sensitive(text):
        return []

    lower = text.lower()

    found = []

    for memory_type, pattern in _JOURNEY_PATTERNS:
        match = pattern.search(lower)

        if not match:
            continue

        title = match.group(1).strip().rstrip(".,!?;:")

        if len(title) < 3:
            continue

        if _is_sensitive(title):
            continue

        found.append(
            (
                memory_type,
                title,
            )
        )

        if len(found) >= 2:
            break

    return found


def capture_journey_memories(
    message,
):
    """
    Extract and store journey memories from a user message.
    Respects memory.enabled and memory.auto_save settings.
    Returns the list of (memory_type, title) that were stored.
    """

    stored = []

    for memory_type, title in extract_journey_memories(message):
        if add_journey_memory(
            memory_type,
            title,
            importance=0.6,
        ):
            stored.append(
                (
                    memory_type,
                    title,
                )
            )

    return stored


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "add_journey_memory",
    "add_memory",
    "capture_journey_memories",
    "clear_memories",
    "complete_journey_memory",
    "delete_memory",
    "delete_memory_by_text",
    "export_memories",
    "extract_journey_memories",
    "get_journey_context_for_ai",
    "get_journey_memories",
    "get_memories",
    "get_memories_by_category",
    "get_memory_text",
    "import_memories",
    "load_memories",
    "memory_count",
    "save_memories",
    "search_journey_memories",
    "search_memory",
]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    add_memory(
        "User is building an AI Friend app",
        "project",
    )

    add_memory(
        "User likes coding",
        "preference",
    )

    print("\nAI FRIEND MEMORIES:\n")

    print(get_memory_text())

    print("\nTotal memories:", memory_count())
