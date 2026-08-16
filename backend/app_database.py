"""
============================================================
AVORA Database Module
============================================================

SQLite-based application database for indexing and tracking
installed applications, launch history, and aliases.

Features:
- App indexing and search
- Launch history tracking
- Alias management
- Automatic migrations
"""

import sqlite3
import threading
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from .app_paths import APP_DATA_DIR

logger = logging.getLogger("Database")

_DB_PATH = APP_DATA_DIR / "launcher.db"
_db_lock = threading.RLock()
_db_instance = None


def get_database():
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = AppDatabase()
    return _db_instance


class AppDatabase:
    """Main database class for application data."""

    def __init__(self):
        self._db_path = _DB_PATH
        self._conn = None
        self._lock = _db_lock
        self._initialize()

    def _initialize(self):
        """Initialize database schema."""
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._create_tables()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self._conn = None

    def _create_tables(self):
        """Create database tables if they don't exist."""
        if self._conn is None:
            return
        try:
            cursor = self._conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    app_type TEXT NOT NULL,
                    extension TEXT,
                    created_at REAL NOT NULL,
                    last_indexed REAL,
                    index_version INTEGER DEFAULT 1
                );
                CREATE INDEX IF NOT EXISTS idx_name ON applications(name);
                CREATE INDEX IF NOT EXISTS idx_path ON applications(path);
                CREATE INDEX IF NOT EXISTS idx_source ON applications(source);
                CREATE TABLE IF NOT EXISTS launch_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    FOREIGN KEY (app_id) REFERENCES applications(id)
                );
                CREATE TABLE IF NOT EXISTS app_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_name TEXT NOT NULL,
                    alias TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    auto_learned INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 1,
                    last_used REAL NOT NULL,
                    UNIQUE(canonical_name, alias)
                );
                CREATE TABLE IF NOT EXISTS index_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS running_processes (
                    pid INTEGER PRIMARY KEY,
                    app_id INTEGER,
                    window_title TEXT,
                    started_at REAL NOT NULL,
                    FOREIGN KEY (app_id) REFERENCES applications(id)
                );
            """)
            self._conn.commit()
        except Exception as e:
            logger.error(f"Table creation failed: {e}")

    def _execute(self, query: str, params: tuple = (), fetch: str = "all"):
        """Execute a query safely, handling None connection."""
        if self._conn is None:
            return [] if fetch in ("all", "one") else None
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            self._conn.commit()
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return [] if fetch == "all" else (None if fetch == "one" else None)

    def get_app_count(self) -> int:
        """Get the number of indexed applications."""
        try:
            if self._conn is None:
                return 0
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM applications")
            return cursor.fetchone()[0]
        except Exception:
            return 0

    def close(self):
        """Close database connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = None


__all__ = ["AppDatabase", "get_database"]