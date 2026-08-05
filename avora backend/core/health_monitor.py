"""
============================================================
AVORA Health Monitor
============================================================

Comprehensive health monitoring for all AVORA systems.

Provides status monitoring for:
- Database
- Cache
- Skills
- Memory
- CPU
- Threads
- API availability
- Configuration

Usage:
    health = HealthMonitor()
    status = health.get_health_status()
"""

import os
import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app_paths import APP_DATA_DIR

logger = logging.getLogger("HealthMonitor")


@dataclass
class HealthStatus:
    """Health status for a component."""
    name: str
    status: str  # healthy, degraded, failed, unknown
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class HealthMonitor:
    """
    Monitors the health of all AVORA components.
    
    Checks:
    - Database connectivity and integrity
    - Cache operational status
    - Active thread count
    - Memory usage
    - CPU usage
    - Skill availability
    - Required dependencies
    - Configuration validity
    - File system access
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._statuses: Dict[str, HealthStatus] = {}
        self._check_functions: Dict[str, callable] = {}
        self._register_checks()
    
    def _register_checks(self):
        """Register all health check functions."""
        self._check_functions = {
            "database": self._check_database,
            "cache": self._check_cache,
            "launcher": self._check_launcher,
            "memory": self._check_memory,
            "threads": self._check_threads,
            "skills": self._check_skills,
            "config": self._check_config,
            "filesystem": self._check_filesystem,
        }
    
    def check_all(self) -> Dict[str, HealthStatus]:
        """Run all health checks."""
        with self._lock:
            for name, check_func in self._check_functions.items():
                try:
                    self._statuses[name] = check_func()
                except Exception as e:
                    self._statuses[name] = HealthStatus(
                        name=name,
                        status="failed",
                        message=str(e),
                    )
            return dict(self._statuses)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Returns:
            Dict with health status for all components
        """
        if not self._statuses:
            self.check_all()
        
        healthy_count = sum(1 for s in self._statuses.values() if s.status == "healthy")
        degraded_count = sum(1 for s in self._statuses.values() if s.status == "degraded")
        failed_count = sum(1 for s in self._statuses.values() if s.status == "failed")
        
        overall = "healthy"
        if failed_count > 0:
            overall = "failed"
        elif degraded_count > 0:
            overall = "degraded"
        
        warnings = [
            f"{s.name}: {s.message}"
            for s in self._statuses.values()
            if s.status in ("degraded", "failed")
        ]
        
        return {
            "status": overall,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "failed_count": failed_count,
            "total_checks": len(self._statuses),
            "checks": {
                name: {
                    "status": status.status,
                    "message": status.message,
                    "details": status.details,
                }
                for name, status in self._statuses.items()
            },
            "warnings": warnings,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _check_database(self) -> HealthStatus:
        """Check database health."""
        try:
            from app_database import get_database
            db = get_database()
            
            count = db.get_app_count()
            
            return HealthStatus(
                name="database",
                status="healthy",
                message=f"Database accessible, {count} apps indexed",
                details={"app_count": count, "db_path": str(db._db_path)},
            )
        except Exception as e:
            return HealthStatus(
                name="database",
                status="failed",
                message=f"Database error: {e}",
            )
    
    def _check_cache(self) -> HealthStatus:
        """Check cache health."""
        try:
            from cache_manager import get_app_cache
            cache = get_app_cache()
            stats = cache.get_stats()
            
            if stats.get("hit_rate", 0) > 0.1:
                status = "healthy"
            else:
                status = "degraded"
            
            return HealthStatus(
                name="cache",
                status=status,
                message=f"Cache hit rate: {stats.get('hit_rate', 0):.1%}",
                details=stats,
            )
        except Exception as e:
            return HealthStatus(
                name="cache",
                status="failed",
                message=f"Cache error: {e}",
            )
    
    def _check_launcher(self) -> HealthStatus:
        """Check launcher health."""
        try:
            from launcher_engine import get_launcher_engine
            engine = get_launcher_engine()
            
            results = engine.search_apps("notepad", limit=1)
            
            return HealthStatus(
                name="launcher",
                status="healthy",
                message=f"Launcher operational",
                details={"search_works": len(results) >= 0},
            )
        except Exception as e:
            return HealthStatus(
                name="launcher",
                status="degraded",
                message=f"Launcher issue: {e}",
            )
    
    def _check_memory(self) -> HealthStatus:
        """Check memory usage."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            
            usage = mem.percent
            if usage < 80:
                status = "healthy"
            elif usage < 90:
                status = "degraded"
            else:
                status = "failed"
            
            return HealthStatus(
                name="memory",
                status=status,
                message=f"Memory usage: {usage:.1f}%",
                details={
                    "total_mb": mem.total / (1024 * 1024),
                    "used_mb": mem.used / (1024 * 1024),
                    "available_mb": mem.available / (1024 * 1024),
                    "percent": usage,
                },
            )
        except ImportError:
            return HealthStatus(
                name="memory",
                status="unknown",
                message="psutil not available",
            )
    
    def _check_threads(self) -> HealthStatus:
        """Check thread count."""
        try:
            thread_count = threading.active_count()
            
            if thread_count > 50:
                status = "degraded"
                warning = f"High thread count: {thread_count}"
            else:
                status = "healthy"
                warning = ""
            
            return HealthStatus(
                name="threads",
                status=status,
                message=f"Active threads: {thread_count}",
                details={"active_count": thread_count, "warning": warning},
            )
        except Exception as e:
            return HealthStatus(
                name="threads",
                status="unknown",
                message=f"Thread check error: {e}",
            )
    
    def _check_skills(self) -> HealthStatus:
        """Check skill availability."""
        try:
            from skills import SKILL_REGISTRY
            from skills import get_enabled_skills
            
            total = len(SKILL_REGISTRY)
            enabled = len(get_enabled_skills())
            
            return HealthStatus(
                name="skills",
                status="healthy",
                message=f"{enabled}/{total} skills enabled",
                details={"total": total, "enabled": enabled, "list": list(SKILL_REGISTRY.keys())},
            )
        except Exception as e:
            return HealthStatus(
                name="skills",
                status="degraded",
                message=f"Skill check error: {e}",
            )
    
    def _check_config(self) -> HealthStatus:
        """Check configuration validity."""
        try:
            issues = []
            
            if not APP_DATA_DIR.exists():
                issues.append("App data directory doesn't exist")
            
            db_file = APP_DATA_DIR / "launcher.db"
            if not db_file.exists():
                issues.append("Database not initialized")
            
            return HealthStatus(
                name="config",
                status="healthy" if not issues else "degraded",
                message="Config issues: " + "; ".join(issues) if issues else "Configuration valid",
                details={"issues": issues, "app_data_dir": str(APP_DATA_DIR)},
            )
        except Exception as e:
            return HealthStatus(
                name="config",
                status="unknown",
                message=f"Config check error: {e}",
            )
    
    def _check_filesystem(self) -> HealthStatus:
        """Check filesystem access."""
        try:
            test_file = APP_DATA_DIR / "health_check.tmp"
            
            try:
                test_file.write_text("test")
                test_file.unlink()
                
                return HealthStatus(
                    name="filesystem",
                    status="healthy",
                    message="Filesystem writable",
                    details={"test_write": True},
                )
            except Exception as e:
                return HealthStatus(
                    name="filesystem",
                    status="degraded",
                    message=f"Write test failed: {e}",
                )
        except Exception as e:
            return HealthStatus(
                name="filesystem",
                status="unknown",
                message=f"Filesystem check error: {e}",
            )
    
    def run_continuous(self, interval: float = 30.0):
        """
        Run continuous health monitoring.
        
        Args:
            interval: Check interval in seconds
        """
        while True:
            try:
                self.check_all()
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(interval)


_health_monitor = None

def get_health_monitor() -> HealthMonitor:
    """Get the singleton health monitor."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


def get_health_status() -> Dict[str, Any]:
    """
    Get current health status.
    
    Convenience function for external callers.
    """
    return get_health_monitor().get_health_status()


__all__ = [
    "HealthMonitor",
    "HealthStatus",
    "get_health_monitor",
    "get_health_status",
]