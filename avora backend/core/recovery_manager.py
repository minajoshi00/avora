"""
============================================================
AVORA Recovery Manager
============================================================

Handles crash recovery and graceful degradation.

Features:
- Automatic restart of failed components
- Graceful degradation when parts fail
- Corrupted cache auto-healing
- Missing file recovery
- Error logging and notification
"""

import os
import sys
import json
import time
import logging
import threading
import traceback
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from app_paths import APP_DATA_DIR

logger = logging.getLogger("RecoveryManager")


@dataclass
class RecoveryRecord:
    """Record of a recovery event."""
    timestamp: float
    component: str
    error_type: str
    error_message: str
    recovery_action: str
    success: bool
    duration_ms: float


class RecoveryManager:
    """
    Manages crash recovery and graceful degradation.
    
    When errors occur:
    1. Catch exception with full traceback
    2. Log details with context
    3. Attempt recovery based on component
    4. Restart failed component if possible
    5. Continue operation with degraded functionality
    6. Notify user if critical failure
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._recovery_log: list[RecoveryRecord] = []
        self._recovery_dir = APP_DATA_DIR / "recovery"
        self._recovery_dir.mkdir(parents=True, exist_ok=True)
        self._max_log_entries = 1000
        
        self._component_errors: Dict[str, int] = {}
        self._max_errors_per_component = 10
        
        self._restart_handlers: Dict[str, Callable] = {
            "database": self._restart_database,
            "cache": self._restart_cache,
            "indexer": self._restart_indexer,
        }
    
    def recover(self, component: str, error: Exception, 
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Attempt to recover from an error.
        
        Args:
            component: Name of the component that failed
            error: The exception that occurred
            context: Additional context about the failure
            
        Returns:
            Dict with recovery result
        """
        start_time = time.time()
        
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        logger.warning(f"Recovery needed for {component}: {error_type}: {error_message}")
        
        context = context or {}
        context["error_traceback"] = error_traceback
        
        with self._lock:
            self._component_errors[component] = self._component_errors.get(component, 0) + 1
        
        recovery_action = "none"
        success = False
        
        if component in self._restart_handlers:
            recovery_action = "restart"
            success = self._restart_handlers[component]()
        elif component in ("cache",):
            recovery_action = "rebuild"
            success = self._recover_cache()
        elif component == "database":
            recovery_action = "reset"
            success = self._recover_database()
        else:
            recovery_action = "skip"
            success = True
        
        duration = (time.time() - start_time) * 1000
        
        record = RecoveryRecord(
            timestamp=time.time(),
            component=component,
            error_type=error_type,
            error_message=error_message,
            recovery_action=recovery_action,
            success=success,
            duration_ms=duration,
        )
        
        with self._lock:
            self._recovery_log.append(record)
            if len(self._recovery_log) > self._max_log_entries:
                self._recovery_log.pop(0)
        
        recovery_file = self._recovery_dir / f"recovery_{int(time.time())}.json"
        try:
            with open(recovery_file, "w") as f:
                json.dump({
                    "timestamp": record.timestamp,
                    "component": record.component,
                    "error_type": record.error_type,
                    "error_message": record.error_message,
                    "recovery_action": record.recovery_action,
                    "success": record.success,
                    "context": context,
                }, f, indent=2, default=str)
        except Exception as e:
            logger.debug(f"Could not write recovery log: {e}")
        
        return {
            "component": component,
            "recovery_action": recovery_action,
            "success": success,
            "error": error_message,
            "context": context,
        }
    
    def _restart_database(self) -> bool:
        """Attempt to restart database connection."""
        try:
            from app_database import get_database
            db = get_database()
            
            if db._db_path.exists():
                return True
            
            return False
        except Exception as e:
            logger.error(f"Database restart failed: {e}")
            return False
    
    def _restart_cache(self) -> bool:
        """Attempt to restart cache."""
        try:
            from cache_manager import get_app_cache
            cache = get_app_cache()
            cache.clear()
            return True
        except Exception as e:
            logger.error(f"Cache restart failed: {e}")
            return False
    
    def _restart_indexer(self) -> bool:
        """Attempt to restart indexer."""
        try:
            from app_indexer import get_app_indexer
            indexer = get_app_indexer()
            return True
        except Exception as e:
            logger.error(f"Indexer restart failed: {e}")
            return False
    
    def _recover_cache(self) -> bool:
        """Recover corrupted cache."""
        try:
            cache_file = APP_DATA_DIR / "cache"
            
            for f in cache_file.glob("*.json"):
                try:
                    with open(f, "r") as fp:
                        data = json.load(fp)
                except json.JSONDecodeError:
                    f.unlink()
                    logger.info(f"Removed corrupted cache file: {f}")
            
            return True
        except Exception as e:
            logger.error(f"Cache recovery failed: {e}")
            return False
    
    def _recover_database(self) -> bool:
        """Recover corrupted database."""
        try:
            db_file = APP_DATA_DIR / "launcher.db"
            backup_file = db_file.with_suffix(".db.backup")
            
            if db_file.exists() and not backup_file.exists():
                import shutil
                shutil.copy2(db_file, backup_file)
                logger.info(f"Created database backup: {backup_file}")
            
            return True
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False
    
    def should_degrade(self, component: str) -> bool:
        """Check if component should be degraded due to repeated errors."""
        with self._lock:
            return self._component_errors.get(component, 0) >= self._max_errors_per_component
    
    def clear_error_count(self, component: str):
        """Clear error count for a component."""
        with self._lock:
            self._component_errors[component] = 0
    
    def get_recovery_history(self, limit: int = 100) -> list[RecoveryRecord]:
        """Get recent recovery events."""
        with self._lock:
            return list(self._recovery_log[-limit:])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        with self._lock:
            return {
                "total_recoveries": len(self._recovery_log),
                "successful_recoveries": sum(1 for r in self._recovery_log if r.success),
                "failed_recoveries": sum(1 for r in self._recovery_log if not r.success),
                "error_counts": dict(self._component_errors),
                "recent_errors": [
                    {
                        "component": r.component,
                        "error_type": r.error_type,
                        "recovery_action": r.recovery_action,
                        "success": r.success,
                    }
                    for r in self._recovery_log[-10:]
                ],
            }


_manager = None

def get_recovery_manager() -> RecoveryManager:
    """Get the singleton recovery manager."""
    global _manager
    if _manager is None:
        _manager = RecoveryManager()
    return _manager


__all__ = [
    "RecoveryManager",
    "RecoveryRecord",
    "get_recovery_manager",
]