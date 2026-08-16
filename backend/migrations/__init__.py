"""
============================================================
AVORA Database Migrations
============================================================

Database version management and automatic migration system.

Version History:
    v1.0.0 - Initial schema with applications, launch_history, app_aliases
    v1.1.0 - Added index_metadata, running_processes tables
    
Auto-migration ensures:
- Database is always compatible with code
- Existing data is preserved
- Backup is created before migration
- Rollback capability
"""

import os
import json
import shutil
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from app_paths import APP_DATA_DIR

logger = logging.getLogger("Migrations")


CURRENT_VERSION = "1.1.0"
CURRENT_SCHEMA = """
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
"""


class MigrationManager:
    """
    Manages database schema migrations.
    
    Features:
    - Version tracking
    - Automatic migration
    - Backup before migration
    - Rollback support
    """
    
    def __init__(self):
        self._db_path = APP_DATA_DIR / "launcher.db"
        self._meta_path = APP_DATA_DIR / "migration_metadata.json"
        self._version = self._get_current_version()
    
    def _get_current_version(self) -> str:
        """Get current database version."""
        if self._meta_path.exists():
            try:
                with open(self._meta_path, "r") as f:
                    data = json.load(f)
                    return data.get("version", "1.0.0")
            except (json.JSONDecodeError, IOError):
                pass
        
        if self._db_path.exists():
            return "1.0.0"
        
        return "1.0.0"
    
    def _set_version(self, version: str):
        """Set database version."""
        with open(self._meta_path, "w") as f:
            json.dump({"version": version, "updated": datetime.now().isoformat()}, f, indent=2)
    
    def get_version(self) -> str:
        """Get current migration version."""
        return self._version
    
    def migrate(self) -> bool:
        """
        Run all pending migrations.
        
        Returns:
            True if migration successful
        """
        if self._version == CURRENT_VERSION:
            logger.debug("Database at current version")
            return True
        
        logger.info(f"Migrating database from {self._version} to {CURRENT_VERSION}")
        
        backup_path = self._create_backup()
        
        try:
            self._apply_migrations()
            
            self._version = CURRENT_VERSION
            self._set_version(CURRENT_VERSION)
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            
            if backup_path and backup_path.exists():
                self._restore_backup(backup_path)
                logger.info("Restored from backup")
            
            return False
    
    def _create_backup(self) -> Optional[Path]:
        """Create backup of database."""
        if not self._db_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._db_path.with_suffix(f".db.{timestamp}.backup")
        
        try:
            shutil.copy2(self._db_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def _restore_backup(self, backup_path: Path):
        """Restore database from backup."""
        try:
            shutil.copy2(backup_path, self._db_path)
        except Exception as e:
            logger.error(f"Restore failed: {e}")
    
    def _apply_migrations(self):
        """Apply all pending migrations."""
        migrations = {
            "1.0.0": self._migrate_1_0_0,
            "1.1.0": self._migrate_1_1_0,
        }
        
        if self._version < "1.1.0":
            self._migrate_1_1_0()
            self._version = "1.1.0"
    
    def _migrate_1_0_0(self):
        """Initial schema creation."""
        if not self._db_path.exists():
            self._create_initial_schema()
    
    def _migrate_1_1_0(self):
        """Add new tables for v1.1.0."""
        conn = None
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS index_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at REAL NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS running_processes (
                    pid INTEGER PRIMARY KEY,
                    app_id INTEGER,
                    window_title TEXT,
                    started_at REAL NOT NULL,
                    FOREIGN KEY (app_id) REFERENCES applications(id)
                )
            """)
            
            conn.commit()
            logger.info("Applied migration 1.1.0")
            
        except Exception as e:
            logger.error(f"Migration 1.1.0 failed: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _create_initial_schema(self):
        """Create initial database schema."""
        conn = None
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self._db_path))
            
            conn.executescript(CURRENT_SCHEMA)
            conn.commit()
            
            logger.info("Created initial database schema")
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()


def run_migrations() -> Dict[str, Any]:
    """
    Run pending migrations.
    
    Returns:
        Dict with migration results
    """
    manager = MigrationManager()
    old_version = manager.get_version()
    
    success = manager.migrate()
    new_version = manager.get_version()
    
    return {
        "success": success,
        "old_version": old_version,
        "new_version": new_version,
        "migration_performed": old_version != new_version,
    }


__all__ = [
    "MigrationManager",
    "CURRENT_VERSION",
    "run_migrations",
]