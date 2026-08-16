"""
===============================================================
                    AI FRIEND FILES SKILL
===============================================================

Handles file and folder operations for AI Friend.

Features:
    • Read text files
    • Open files
    • Create files
    • Create folders
    • List folder contents
    • Find files
    • Delete files
    • Get file information
    • Move files
    • Rename files
    • Settings-based permissions
    • Safe path handling
    • Windows-friendly behavior

Settings used:

    files.enabled
    files.default_folder
    files.allow_create
    files.allow_open
    files.allow_delete
    files.allow_move
    files.allow_rename
    files.confirm_delete

IMPORTANT:

    This module does NOT ask for confirmation.

    Confirmation should be handled by ai_logic.py
    before dangerous operations such as deletion.

===============================================================
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


# =============================================================
# SETTINGS IMPORT
# =============================================================

try:

    from ..settings import get_setting

except ImportError:

    def get_setting(
        path: str,
        default=None,
    ):

        return default
        


# =============================================================
# INTERNAL SETTINGS HELPERS
# =============================================================


def _files_enabled() -> bool:

    return bool(
        get_setting(
            "files.enabled",
            True
        )
    )


def _allow_create() -> bool:

    return bool(
        get_setting(
            "files.allow_create",
            True
        )
    )


def _allow_open() -> bool:

    return bool(
        get_setting(
            "files.allow_open",
            True
        )
    )


def _allow_delete() -> bool:

    return bool(
        get_setting(
            "files.allow_delete",
            False
        )
    )


def _allow_move() -> bool:

    return bool(
        get_setting(
            "files.allow_move",
            True
        )
    )


def _allow_rename() -> bool:

    return bool(
        get_setting(
            "files.allow_rename",
            True
        )
    )


def _confirm_delete() -> bool:

    return bool(
        get_setting(
            "files.confirm_delete",
            True
        )
    )


def _default_folder() -> str:

    return str(
        get_setting(
            "files.default_folder",
            str(
                Path.home()
                / "Documents"
            )
        )
    )


# =============================================================
# INTERNAL VALIDATION
# =============================================================


def _check_files_enabled():

    if not _files_enabled():

        return (
            False,
            "📁 File operations are currently disabled "
            "in AI Friend Settings."
        )

    return True, ""


def _expand_path(
    file_path: str | Path,
) -> Path:

    return Path(
        os.path.expandvars(
            os.path.expanduser(
                str(file_path)
            )
        )
    )


def _validate_path(
    file_path: Path,
) -> tuple[bool, str]:
    """
    Validate a file path for security.
    
    Returns:
        (is_valid, error_message)
    """
    if not file_path:
        return False, "Empty path"
    
    # Normalize the path (resolves .. and .)
    try:
        normalized = file_path.resolve()
    except (OSError, RuntimeError):
        return False, "Invalid path"
    
    # Get allowed base directory (user's home by default)
    try:
        allowed_base = Path(_default_folder()).resolve()
    except Exception:
        allowed_base = Path.home().resolve()
    
    # Check if path is within allowed base or common safe locations
    safe_locations = [
        allowed_base,
        Path.home().resolve(),
        Path.cwd().resolve() if hasattr(Path, 'cwd') else None,
    ]
    
    # Allow all user directories (Documents, Desktop, Downloads, etc.)
    user_dirs = ["Documents", "Desktop", "Downloads", "Pictures", "Videos", "Music"]
    for user_dir in user_dirs:
        safe_locations.append((Path.home() / user_dir).resolve())
    
    # Check if path is within any safe location
    for safe_loc in safe_locations:
        if safe_loc and str(normalized).startswith(str(safe_loc)):
            return True, ""
    
    # For files operations, also allow temp directory
    import tempfile
    temp_dir = Path(tempfile.gettempdir()).resolve()
    if str(normalized).startswith(str(temp_dir)):
        return True, ""
    
    return False, f"Access denied: Path outside allowed directories ({normalized})"


def _resolve_path(
    file_path: str | Path,
) -> Path:

    path = _expand_path(
        file_path
    )

    if not path.is_absolute():

        path = (
            Path(
                _default_folder()
            )
            / path
        )

    # Validate path security
    is_valid, error_msg = _validate_path(path)
    if not is_valid:
        raise ValueError(error_msg)

    return path


def _format_size(
    size_bytes: int,
) -> str:

    if size_bytes < 1024:

        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:

        return (
            f"{size_bytes / 1024:.2f} KB"
        )

    if size_bytes < 1024 ** 3:

        return (
            f"{size_bytes / (1024 ** 2):.2f} MB"
        )

    return (
        f"{size_bytes / (1024 ** 3):.2f} GB"
    )


# =============================================================
# READ TEXT FILE
# =============================================================


def read_file(
    file_path: str | Path,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not file_path:

        return (
            "Brooo, you didn't provide "
            "a file path 📄"
        )


    file_path = _resolve_path(
        file_path
    )


    if not file_path.exists():

        return (
            f"Brooo, I couldn't find this file:\n"
            f"{file_path}"
        )


    if not file_path.is_file():

        return (
            "Brooo, that is not a file 📁"
        )


    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            content = file.read()


        if not content.strip():

            return (
                "Brooo, this file is empty 📄"
            )


        return content


    except UnicodeDecodeError:

        return (
            "Brooo, I can't read this file "
            "as a text file. "
            "It may be a binary file 📦"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't read the file 😭\n"
            f"{error}"
        )


# =============================================================
# OPEN FILE
# =============================================================


def open_file(
    file_path: str | Path,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not _allow_open():

        return (
            "🔒 Opening files is disabled "
            "in AI Friend Settings."
        )


    if not file_path:

        return (
            "Brooo, you didn't provide "
            "a file path 📄"
        )


    file_path = _resolve_path(
        file_path
    )


    if not file_path.exists():

        return (
            f"Brooo, I couldn't find:\n"
            f"{file_path}"
        )


    try:

        if hasattr(
            os,
            "startfile"
        ):

            os.startfile(
                str(file_path)
            )

        else:

            subprocess.Popen(
                [
                    "xdg-open",
                    str(file_path)
                ]
            )


        return (
            f"Opening "
            f"{file_path.name} 🚀"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't open "
            f"the file 😭\n"
            f"{error}"
        )


# =============================================================
# CREATE FILE
# =============================================================


def create_file(
    file_path: str | Path,
    content: str = "",
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not _allow_create():

        return (
            "🔒 File creation is disabled "
            "in AI Friend Settings."
        )


    if not file_path:

        return (
            "Brooo, you didn't provide "
            "a file name 📄"
        )


    file_path = _resolve_path(
        file_path
    )


    if file_path.exists():

        return (
            "Brooo, that file already exists 😅"
        )


    try:

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                content
            )


        return (
            f"Created "
            f"{file_path.name} "
            f"successfully 📄✅"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't create "
            f"the file 😭\n"
            f"{error}"
        )


# =============================================================
# CREATE FOLDER
# =============================================================


def create_folder(
    folder_path: str | Path,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not _allow_create():

        return (
            "🔒 Folder creation is disabled "
            "in AI Friend Settings."
        )


    if not folder_path:

        return (
            "Brooo, you didn't provide "
            "a folder name 📁"
        )


    folder_path = _resolve_path(
        folder_path
    )


    if folder_path.exists():

        return (
            "Brooo, that folder already exists 😅"
        )


    try:

        folder_path.mkdir(
            parents=True,
            exist_ok=False
        )


        return (
            f"Created folder "
            f"{folder_path.name} "
            f"📁✅"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't create "
            f"the folder 😭\n"
            f"{error}"
        )


# =============================================================
# LIST FOLDER CONTENTS
# =============================================================


def list_folder(
    folder_path: Optional[str | Path] = None,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not folder_path:

        folder_path = _default_folder()


    folder_path = _resolve_path(
        folder_path
    )


    if not folder_path.exists():

        return (
            f"Brooo, I couldn't find "
            f"this folder:\n"
            f"{folder_path}"
        )


    if not folder_path.is_dir():

        return (
            "Brooo, that is not a folder 📁"
        )


    try:

        items = sorted(
            folder_path.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower()
            )
        )


        if not items:

            return (
                "Brooo, this folder is empty 📁"
            )


        result = (
            f"📁 Contents of:\n"
            f"{folder_path}\n\n"
        )


        for item in items:

            if item.is_dir():

                result += (
                    f"📁 {item.name}\n"
                )

            else:

                result += (
                    f"📄 {item.name}\n"
                )


        return result


    except Exception as error:

        return (
            f"Brooo, I couldn't read "
            f"this folder 😭\n"
            f"{error}"
        )


# =============================================================
# FIND FILES
# =============================================================


def find_files(
    filename: str,
    search_path: Optional[str | Path] = None,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not filename:

        return (
            "Brooo, tell me the file name "
            "you want me to find 🔍"
        )


    if not search_path:

        search_path = Path.home()


    search_path = _resolve_path(
        search_path
    )


    if not search_path.exists():

        return (
            f"Brooo, I couldn't find "
            f"this search location:\n"
            f"{search_path}"
        )


    try:

        pattern = os.path.join(
            str(search_path),
            "**",
            filename
        )


        results = glob.glob(
            pattern,
            recursive=True
        )


        if not results:

            return (
                f"Brooo, I couldn't find "
                f"{filename} 🔍"
            )


        result = (
            "🔍 I found these files:\n\n"
        )


        for path in results[:20]:

            result += (
                f"📄 {path}\n"
            )


        if len(results) > 20:

            result += (
                f"\n...and "
                f"{len(results) - 20} "
                f"more."
            )


        return result


    except Exception as error:

        return (
            f"Brooo, file search failed 😭\n"
            f"{error}"
        )


# =============================================================
# DELETE FILE
# =============================================================


def delete_file(
    file_path: str | Path,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not _allow_delete():

        return (
            "🔒 File deletion is disabled "
            "in AI Friend Settings."
        )


    if not file_path:

        return (
            "Brooo, you didn't provide "
            "a file path 📄"
        )


    file_path = _resolve_path(
        file_path
    )


    if not file_path.exists():

        return (
            "Brooo, I couldn't find "
            "that file 😅"
        )


    if not file_path.is_file():

        return (
            "Brooo, that is not a file 📁"
        )


    try:

        file_path.unlink()


        return (
            f"Deleted "
            f"{file_path.name} "
            f"🗑️✅"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't delete "
            f"the file 😭\n"
            f"{error}"
        )


# =============================================================
# MOVE FILE
# =============================================================


def move_file(
    source_path: str | Path,
    destination_path: str | Path,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not _allow_move():

        return (
            "🔒 Moving files is disabled "
            "in AI Friend Settings."
        )


    if not source_path:

        return (
            "Brooo, you didn't provide "
            "the source file 📄"
        )


    if not destination_path:

        return (
            "Brooo, you didn't provide "
            "the destination 📁"
        )


    source_path = _resolve_path(
        source_path
    )

    destination_path = _resolve_path(
        destination_path
    )


    if not source_path.exists():

        return (
            "Brooo, I couldn't find "
            "the source file 😅"
        )


    try:

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        shutil.move(
            str(source_path),
            str(destination_path)
        )


        return (
            f"Moved "
            f"{source_path.name} "
            f"successfully 📦✅"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't move "
            f"the file 😭\n"
            f"{error}"
        )


# =============================================================
# RENAME FILE
# =============================================================


def rename_file(
    file_path: str | Path,
    new_name: str,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not _allow_rename():

        return (
            "🔒 Renaming files is disabled "
            "in AI Friend Settings."
        )


    if not file_path:

        return (
            "Brooo, you didn't provide "
            "a file path 📄"
        )


    if not new_name:

        return (
            "Brooo, you didn't provide "
            "a new name 📄"
        )


    file_path = _resolve_path(
        file_path
    )


    if not file_path.exists():

        return (
            "Brooo, I couldn't find "
            "that file 😅"
        )


    new_path = (
        file_path.parent
        / Path(new_name).name
    )


    if new_path.exists():

        return (
            "Brooo, a file or folder "
            "with that name already exists 😅"
        )


    try:

        file_path.rename(
            new_path
        )


        return (
            f"Renamed "
            f"{file_path.name} "
            f"to "
            f"{new_path.name} "
            f"✏️✅"
        )


    except Exception as error:

        return (
            f"Brooo, I couldn't rename "
            f"the file 😭\n"
            f"{error}"
        )


# =============================================================
# GET FILE INFORMATION
# =============================================================


def get_file_info(
    file_path: str | Path,
):

    enabled, message = _check_files_enabled()

    if not enabled:

        return message


    if not file_path:

        return (
            "Brooo, you didn't provide "
            "a file path 📄"
        )


    file_path = _resolve_path(
        file_path
    )


    if not file_path.exists():

        return (
            "Brooo, I couldn't find "
            "that file 😅"
        )


    try:

        file_size = file_path.stat().st_size

        modified_time = datetime.fromtimestamp(
            file_path.stat().st_mtime
        )


        item_type = (
            "Folder"
            if file_path.is_dir()
            else "File"
        )


        extension = (
            file_path.suffix
            if file_path.is_file()
            else "Folder"
        )


        return (

            f"📄 {item_type}: "
            f"{file_path.name}\n\n"

            f"📍 Location:\n"
            f"{file_path.resolve()}\n\n"

            f"📦 Size: "
            f"{_format_size(file_size)}\n\n"

            f"🗂️ Type: "
            f"{extension or 'No extension'}\n\n"

            f"🕒 Modified: "
            f"{modified_time.strftime('%Y-%m-%d %I:%M:%S %p')}"

        )


    except Exception as error:

        return (
            f"Brooo, I couldn't get "
            f"file information 😭\n"
            f"{error}"
        )


# =============================================================
# PUBLIC API
# =============================================================


__all__ = [

    "read_file",

    "open_file",

    "create_file",

    "create_folder",

    "list_folder",

    "find_files",

    "delete_file",

    "move_file",

    "rename_file",

    "get_file_info",

]