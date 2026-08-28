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
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from app_paths import APP_DATA_DIR

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
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_type TEXT NOT NULL,  -- "project", "problem", "decision", "idea", "preference", "milestone", "task", "conversation"
                    title TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT,  -- JSON string for additional info
                    importance REAL DEFAULT 0.5,  -- 0.0 to 1.0, higher = more important
                    created_at REAL NOT NULL,
                    last_mentioned REAL,
                    times_mentioned INTEGER DEFAULT 1,
                    associated_goal TEXT,  -- goal description this memory is linked to
                    UNIQUE(title, memory_type)
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

# ============================================================
# MEMORY MANAGEMENT
# ============================================================

    MEMORY_TYPES = {"project", "problem", "decision", "idea", "preference", "milestone", "task", "conversation"}

    def create_memory(self, memory_type: str, title: str, content: str = "",
                      metadata: dict = None, importance: float = 0.5,
                      associated_goal: str = "") -> Optional[int]:
        """Create a new memory. Returns memory id or None if duplicate."""
        if memory_type not in self.MEMORY_TYPES:
            logger.error(f"Invalid memory type: {memory_type}")
            return None
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            cursor = self._conn.cursor()
            cursor.execute(
                """INSERT OR IGNORE INTO memories 
                   (memory_type, title, content, metadata, importance, created_at, last_mentioned, times_mentioned, associated_goal)
                   VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?)""",
                (memory_type, title, content, metadata_json, importance, time.time(), associated_goal)
            )
            self._conn.commit()
            # Check if inserted or ignored (duplicate)
            if cursor.rowcount > 0:
                return cursor.lastrowid
            # Already exists - increment times_mentioned and return existing id
            cursor.execute("SELECT id FROM memories WHERE title = ? AND memory_type = ?", (title, memory_type))
            row = cursor.fetchone()
            if row:
                # Increment mention count
                cursor.execute("UPDATE memories SET times_mentioned = times_mentioned + 1, last_mentioned = ? WHERE id = ?",
                              (time.time(), row[0]))
                self._conn.commit()
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Create memory failed: {e}")
            return None

    def get_memory(self, memory_id: int) -> Optional[dict]:
        """Get a memory by id."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if row:
                cols = [desc[0] for desc in cursor.description]
                return dict(zip(cols, row))
            return None
        except Exception as e:
            logger.error(f"Get memory failed: {e}")
            return None

    def get_memories(self, memory_type: str = None, limit: int = 50,
                     min_importance: float = 0.0) -> list[dict]:
        """Get memories, optionally filtered by type and importance."""
        try:
            cursor = self._conn.cursor()
            if memory_type:
                if memory_type not in self.MEMORY_TYPES:
                    return []
                cursor.execute(
                    """SELECT * FROM memories WHERE memory_type = ? 
                       AND importance >= ? ORDER BY importance DESC, times_mentioned DESC LIMIT ?""",
                    (memory_type, min_importance, limit)
                )
            else:
                cursor.execute(
                    """SELECT * FROM memories 
                       WHERE importance >= ? ORDER BY importance DESC, times_mentioned DESC LIMIT ?""",
                    (min_importance, limit)
                )
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(f"Get memories failed: {e}")
            return []

    def update_memory_importance(self, memory_id: int, importance: float) -> bool:
        """Update memory importance."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("UPDATE memories SET importance = ? WHERE id = ?",
                          (max(0.0, min(1.0, importance)), memory_id))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update memory importance failed: {e}")
            return False

    def increment_memory_mentions(self, memory_id: int) -> bool:
        """Increment how many times a memory has been referenced."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("UPDATE memories SET times_mentioned = times_mentioned + 1, last_mentioned = ? WHERE id = ?",
                          (time.time(), memory_id))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Increment memory mentions failed: {e}")
            return False

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by id."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete memory failed: {e}")
            return False

    def get_recent_memories(self, minutes: int = 60) -> list[dict]:
        """Get memories mentioned recently."""
        try:
            cutoff = time.time() - (minutes * 60)
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT * FROM memories WHERE last_mentioned > ? ORDER BY last_mentioned DESC""",
                (cutoff,)
            )
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(f"Get recent memories failed: {e}")
            return []


__all__ = ["AppDatabase", "get_database"]