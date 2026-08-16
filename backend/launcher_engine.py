"""
============================================================
AVORA Launcher Engine
============================================================

Main application launcher with search, ranking, and execution.
"""

import os
import re
import json
import time
import logging
import threading
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .app_database import get_database
from .app_indexer import get_app_indexer
from .alias_manager import get_alias_manager
from .launch_history import get_launch_history
from .cache_manager get_app_cache

logger = logging.getLogger("LauncherEngine")

_engine = None
_engine_lock = threading.Lock()


class LauncherEngine:
    """Main launcher engine for finding and opening applications."""

    def __init__(self):
        self._db = get_database()
        self._indexer = get_app_indexer()
        self._alias_mgr = get_alias_manager()
        self._ranker = get_ranking_engine()
        self._history = get_launch_history()
        self._cache = get_app_cache()
        self._lock = threading.RLock()

    def search_apps(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for applications matching the query."""
        if not query:
            return []

        cache_key = f"search:{query}:{limit}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            apps = self._indexer.search_apps(query, limit * 2)
            ranked = self._ranker.rank_apps(apps, query)
            results = ranked[:limit]

            self._cache.set(cache_key, results, ttl=60.0)
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def find_app(self, query: str) -> Optional[Dict[str, Any]]:
        """Find the best matching application for a query."""
        results = self.search_apps(query, limit=1)
        if results:
            return results[0]
        return None

    def launch_app(self, app_path: str, app_name: str = "") -> bool:
        """Launch an application."""
        try:
            if not Path(app_path).exists():
                return False

            subprocess.Popen(
                [app_path],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            self._history.record(app_name or Path(app_path).name, app_path, success=True)
            return True
        except Exception as e:
            logger.error(f"Launch error for {app_path}: {e}")
            self._history.record(app_name or Path(app_path).name, app_path, success=False, error_message=str(e))
            return False

    def get_installed_apps(self) -> List[Dict[str, Any]]:
        """Get all installed applications."""
        try:
            return self._indexer.get_all_apps()
        except Exception:
            return []


def get_launcher_engine() -> LauncherEngine:
    """Get the singleton launcher engine."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = LauncherEngine()
    return _engine


__all__ = ["LauncherEngine", "get_launcher_engine"]
