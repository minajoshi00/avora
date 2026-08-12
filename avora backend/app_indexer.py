"""
============================================================
AVORA App Indexer
============================================================

Indexes installed applications on the system.

Scans:
- Start Menu shortcuts (.lnk)
- Common install directories
- Windows system applications
- Desktop shortcuts

Populates the SQLite database for fast launcher search.
"""

import os
import re
import json
import glob
import logging
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from app_paths import APP_DATA_DIR
from app_database import get_database

logger = logging.getLogger("AppIndexer")


class AppIndexer:
    """Indexes and manages application data."""

    def __init__(self):
        self._db = get_database()
        self._lock = threading.RLock()
        self._indexed_paths = set()

    # ========================================================
    # INDEXING
    # ========================================================

    def index_applications(self) -> int:
        """Index all applications. Returns count of indexed apps."""
        try:
            count = self._db.get_app_count()
            if count > 0:
                return count

            # Scan the system for applications
            apps = self._scan_system_apps()
            self._store_apps(apps)
            return self._db.get_app_count()
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return 0

    def refresh_index(self):
        """Refresh the application index."""
        try:
            apps = self._scan_system_apps()
            self._store_apps(apps, replace=True)
            logger.info(f"Index refreshed: {len(apps)} apps")
        except Exception as e:
            logger.error(f"Index refresh error: {e}")

    def _scan_system_apps(self) -> List[Dict[str, Any]]:
        """Scan the system for installed applications."""
        apps = []
        seen_paths = set()

        # 1. Start Menu shortcuts
        start_menu_dirs = [
            Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
            Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs",
        ]
        for start_dir in start_menu_dirs:
            if start_dir.exists():
                for lnk in start_dir.rglob("*.lnk"):
                    try:
                        name = lnk.stem
                        path = str(lnk)
                        if path not in seen_paths:
                            seen_paths.add(path)
                            apps.append({
                                "name": name,
                                "path": path,
                                "source": "start_menu",
                                "app_type": "shortcut",
                                "extension": ".lnk",
                            })
                    except Exception:
                        continue

        # 2. Common install directories
        install_dirs = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        ]
        for install_dir in install_dirs:
            if not install_dir.exists():
                continue
            for exe in install_dir.rglob("*.exe"):
                try:
                    # Skip if too deep (avoid huge recursion)
                    rel_parts = exe.relative_to(install_dir).parts
                    if len(rel_parts) > 3:
                        continue
                    name = exe.stem
                    path = str(exe)
                    if path not in seen_paths:
                        seen_paths.add(path)
                        apps.append({
                            "name": name,
                            "path": path,
                            "source": "install_dir",
                            "app_type": "executable",
                            "extension": ".exe",
                        })
                except Exception:
                    continue

        # 3. Windows system apps
        system_apps = {
            "notepad": "C:\\Windows\\System32\\notepad.exe",
            "calculator": "C:\\Windows\\System32\\calc.exe",
            "paint": ["C:\\Windows\\System32\\mspaint.exe", "C:\\Windows\\SystemApps\\Microsoft.WindowsPaint_8wekyb3d8bbwe\\PaintApp.exe"],
            "mspaint": ["C:\\Windows\\System32\\mspaint.exe", "C:\\Windows\\SystemApps\\Microsoft.WindowsPaint_8wekyb3d8bbwe\\PaintApp.exe"],
            "explorer": "C:\\Windows\\explorer.exe",
            "taskmgr": "C:\\Windows\\System32\\Taskmgr.exe",
            "cmd": "C:\\Windows\\System32\\cmd.exe",
            "control panel": "C:\\Windows\\System32\\control.exe",
            "snipping tool": "C:\\Windows\\System32\\SnippingTool.exe",
            "powershell": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "settings": "C:\\Windows\\ImmersiveControlPanel\\SystemSettings.exe",
            "regedit": "C:\\Windows\\regedit.exe",
            "msconfig": "C:\\Windows\\System32\\msconfig.exe",
            "services": "C:\\Windows\\System32\\services.msc",
            "device manager": "C:\\Windows\\System32\\devmgmt.msc",
            "disk management": "C:\\Windows\\System32\\diskmgmt.msc",
            "event viewer": "C:\\Windows\\System32\\eventvwr.msc",
            "performance monitor": "C:\\Windows\\System32\\perfmon.msc",
            "resource monitor": "C:\\Windows\\System32\\resmon.exe",
            "system info": "C:\\Windows\\System32\\msinfo32.exe",
            "character map": "C:\\Windows\\System32\\charmap.exe",
            "on-screen keyboard": "C:\\Windows\\System32\\osk.exe",
            "magnifier": "C:\\Windows\\System32\\Magnify.exe",
            "narrator": "C:\\Windows\\System32\\Narrator.exe",
            "windows media player": "C:\\Windows\\System32\\wmplayer.exe",
            "wordpad": "C:\\Windows\\System32\\write.exe",
        }
        for name, path in system_apps.items():
            paths_to_try = [path] if isinstance(path, str) else path
            for p in paths_to_try:
                if os.path.exists(p) and p not in seen_paths:
                    seen_paths.add(p)
                    apps.append({
                        "name": name,
                        "path": p,
                        "source": "system",
                        "app_type": "executable",
                        "extension": Path(p).suffix,
                    })
                    break

        # 4. Desktop shortcuts
        desktop_dirs = [
            Path.home() / "Desktop",
            Path(os.environ.get("PUBLIC", "C:\\Users\\Public")) / "Desktop",
        ]
        for desktop_dir in desktop_dirs:
            if not desktop_dir.exists():
                continue
            for lnk in desktop_dir.glob("*.lnk"):
                try:
                    name = lnk.stem
                    path = str(lnk)
                    if path not in seen_paths:
                        seen_paths.add(path)
                        apps.append({
                            "name": name,
                            "path": path,
                            "source": "desktop",
                            "app_type": "shortcut",
                            "extension": ".lnk",
                        })
                except Exception:
                    continue

        return apps

    def _store_apps(self, apps: List[Dict[str, Any]], replace: bool = False):
        """Store apps in the database."""
        if not apps:
            return

        try:
            cursor = self._db._conn.cursor()
            if replace:
                cursor.execute("DELETE FROM applications")

            now = time.time()
            for app in apps:
                try:
                    cursor.execute(
                        """INSERT OR IGNORE INTO applications
                           (name, path, source, app_type, extension, created_at, last_indexed)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            app["name"],
                            app["path"],
                            app["source"],
                            app["app_type"],
                            app.get("extension", ""),
                            now,
                            now,
                        ),
                    )
                except Exception:
                    continue

            self._db._conn.commit()
        except Exception as e:
            logger.error(f"Store apps error: {e}")

    # ========================================================
    # SEARCH
    # ========================================================

    def search_apps(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for applications by name. Auto-indexes if database is empty."""
        try:
            # Auto-index if database is empty
            count = self._db.get_app_count()
            if count == 0:
                logger.info("Auto-indexing applications on first search...")
                apps = self._scan_system_apps()
                self._store_apps(apps)

            cursor = self._db._conn.cursor()
            cursor.execute(
                "SELECT id, name, path, source, app_type FROM applications WHERE name LIKE ? LIMIT ?",
                (f"%{query}%", limit),
            )
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "path": row[2],
                    "source": row[3],
                    "app_type": row[4],
                })
            
            # If no results, try a fallback scan for common system apps
            if not results:
                fallback_paths = {
                    "paint": ["C:\\Windows\\System32\\mspaint.exe", "C:\\Windows\\SystemApps\\Microsoft.WindowsPaint_8wekyb3d8bbwe\\PaintApp.exe"],
                    "notepad": ["C:\\Windows\\System32\\notepad.exe"],
                    "calculator": ["C:\\Windows\\System32\\calc.exe"],
                }
                query_lower = query.lower()
                for name, paths in fallback_paths.items():
                    if query_lower in name:
                        for path in paths:
                            if os.path.exists(path):
                                results.append({
                                    "id": 0,
                                    "name": name,
                                    "path": path,
                                    "source": "system",
                                    "app_type": "executable",
                                })
                                break
            
            return results
        except Exception:
            return []

    def get_all_apps(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all indexed applications."""
        try:
            cursor = self._db._conn.cursor()
            cursor.execute("SELECT id, name, path, source, app_type FROM applications LIMIT ?", (limit,))
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "path": row[2],
                    "source": row[3],
                    "app_type": row[4],
                })
            return results
        except Exception:
            return []


_instance = None


def get_app_indexer() -> AppIndexer:
    """Get the singleton app indexer."""
    global _instance
    if _instance is None:
        _instance = AppIndexer()
    return _instance


__all__ = ["AppIndexer", "get_app_indexer"]