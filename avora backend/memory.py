# ============================================================
# memory.py
# AI Friend - Advanced Long-Term Memory System
# ============================================================

import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH
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

            temporary_file = Path(
                file.name
            )

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

            _save_file(
                []
            )

            return []

        try:

            with open(
                MEMORY_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                memories = json.load(
                    file
                )

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

            print(
                "MEMORY FILE ERROR: "
                "Could not read memories.json"
            )

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

        return _save_file(
            memories
        )


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

    return max(
        ids,
        default=0,
    ) + 1


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

        return (
            "Long-term memory is disabled."
        )

    memories = load_memories()

    if not memories:

        return (
            "No memories stored yet."
        )

    memory_lines = []

    for memory in memories:

        text = memory.get(
            "text",
            "",
        )

        category = memory.get(
            "category",
            "general",
        )

        memory_lines.append(
            f"- [{category}] {text}"
        )

    return "\n".join(
        memory_lines
    )


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

    keyword = str(
        keyword
    ).lower().strip()

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

        if (
            keyword in text
            or keyword in category
        ):

            results.append(
                memory
            )

    return results


# ============================================================
# GET MEMORIES BY CATEGORY
# ============================================================

def get_memories_by_category(
    category,
):

    if not _memory_enabled():

        return []

    category = str(
        category
    ).lower().strip()

    return [

        memory

        for memory in load_memories()

        if str(
            memory.get(
                "category",
                "",
            )
        ).lower() == category

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
        ) != str(
            memory_id
        )

    ]

    if len(
        updated_memories
    ) == len(
        memories
    ):

        return False

    return _save_file(
        updated_memories
    )


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

    target = str(
        memory_text
    ).strip().lower()

    memories = load_memories()

    updated_memories = [

        memory

        for memory in memories

        if str(
            memory.get(
                "text",
                "",
            )
        ).strip().lower() != target

    ]

    if len(
        updated_memories
    ) == len(
        memories
    ):

        return False

    return _save_file(
        updated_memories
    )


# ============================================================
# CLEAR ALL MEMORIES
# ============================================================

def clear_memories():

    if not _memory_enabled():

        return False

    return _save_file(
        []
    )


# ============================================================
# MEMORY COUNT
# ============================================================

def memory_count():

    if not _memory_enabled():

        return 0

    return len(
        load_memories()
    )


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

            memories = json.load(
                file
            )

        if not isinstance(
            memories,
            list,
        ):

            return False

        memories = memories[
            -_max_memories():
        ]

        return _save_file(
            memories
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return False


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [

    "load_memories",
    "save_memories",
    "add_memory",
    "get_memories",
    "get_memory_text",
    "search_memory",
    "get_memories_by_category",
    "delete_memory",
    "delete_memory_by_text",
    "clear_memories",
    "memory_count",
    "export_memories",
    "import_memories",

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

    print(
        "\nAI FRIEND MEMORIES:\n"
    )

    print(
        get_memory_text()
    )

    print(
        "\nTotal memories:",
        memory_count()
    )