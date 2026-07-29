# ============================================================
# AVORA Application Paths
# ============================================================

import sys
import os
from pathlib import Path


def _get_frozen_base() -> Path:
    if getattr(sys, "_MEIPASS", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _get_app_data_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "AVORA"
    return Path.home() / ".config" / "AVORA"


BASE_DIR = Path(__file__).resolve().parent
APP_DATA_DIR = _get_app_data_dir()
ICON_PATH = _get_frozen_base() / "avora.ico"
