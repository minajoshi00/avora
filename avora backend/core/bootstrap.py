"""
============================================================
AVORA System Bootstrap
============================================================

Integration layer that connects the modular core engines
to the running application.

Responsibilities:
- Auto-discover and register all skill modules
- Initialize core engine singletons
- Provide a unified startup/shutdown API
- Log health status on startup

This module is additive: it never replaces or overrides
existing subsystems (companion, activity monitor, etc.).
"""

import importlib
import logging
import pkgutil
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CoreBootstrap")

# Skill modules that register themselves via register_skill()
_SKILL_MODULES = [
    "skills.launcher_skill",
    "skills.browser_skill",
    "skills.system_skill",
]

# Core engine getters keyed by name: name -> (module, getter)
_ENGINE_GETTERS = {
    "intelligence": ("core.intelligence_engine", "get_intelligence_engine"),
    "context": ("core.context_engine", "get_context_engine"),
    "recovery": ("core.recovery_manager", "get_recovery_manager"),
    "health": ("core.health_monitor", "get_health_monitor"),
}


class CoreBootstrap:
    """
    Central bootstrap for AVORA core systems.

    Usage:
        from core.bootstrap import CoreBootstrap
        bootstrap = CoreBootstrap()
        bootstrap.start()

    Safe to call multiple times (idempotent).
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._started = False
        self._engines: Dict[str, Any] = {}

    # ========================================================
    # PUBLIC API
    # ========================================================

    def start(self) -> Dict[str, Any]:
        """Start all core systems."""
        if self._started:
            return self._started

        results = {}

        # 1. Register all skills
        results["skills_registered"] = self.load_skills()

        # 1b. Index applications for launcher
        try:
            from app_indexer import get_app_indexer
            indexer = get_app_indexer()
            app_count = indexer.index_applications()
            results["apps_indexed"] = app_count
            logger.info(f"App index: {app_count} applications")
        except Exception as e:
            logger.warning(f"App indexing failed: {e}")

        # 2. Initialize core engines
        for name, (module_name, getter) in _ENGINE_GETTERS.items():
            try:
                module = importlib.import_module(module_name)
                engine = getattr(module, getter)()
                self._engines[name] = engine
                logger.info(f"{name} engine initialized")
            except Exception as e:
                logger.warning(f"{name} engine init failed: {e}")

        # 3. Collect health status
        health = self._engines.get("health")
        if health is not None:
            try:
                status = health.get_health_status()
                results["health"] = status
            except Exception as e:
                logger.warning(f"Health check failed: {e}")

        self._started = results
        return results

    def stop(self):
        """Shut down core systems gracefully."""
        context = self._engines.get("context")
        if context is not None:
            try:
                context.stop()
                logger.info("Context engine stopped")
            except Exception as e:
                logger.debug(f"Context stop error: {e}")
        self._started = False

    def load_skills(self) -> int:
        """
        Import all skill modules so they register themselves.
        Returns the number of skills registered.
        """
        count = 0
        for module_name in _SKILL_MODULES:
            try:
                importlib.import_module(module_name)
                count += 1
                logger.debug(f"Loaded skill module: {module_name}")
            except Exception as e:
                logger.warning(f"Failed to load skill module {module_name}: {e}")

        try:
            from skills import SKILL_REGISTRY
            return len(SKILL_REGISTRY)
        except Exception:
            return count

    def get_engines(self) -> Dict[str, Any]:
        """Get initialized engine instances."""
        return dict(self._engines)

    def get_engine(self, name: str) -> Optional[Any]:
        """Get a specific engine by name."""
        return self._engines.get(name)

    def apply_context_to_snapshot(self, snapshot) -> Dict[str, Any]:
        """
        Bridge between Context Engine and Intelligence Engine.

        Copies live context data from the ContextEngine into the
        Intelligence Engine's ContextSnapshot-compatible dict.
        """
        context = self._engines.get("context")
        if context is None:
            return {}

        try:
            data = context.get_context()
            return {
                "active_window": (data.get("desktop") or {}).get("active_window_title"),
                "active_process": (data.get("desktop") or {}).get("active_process_name"),
                "cpu_usage": (data.get("system") or {}).get("cpu_usage", 0.0),
                "memory_usage": (data.get("system") or {}).get("memory_usage_percent", 0.0),
                "battery_level": (data.get("system") or {}).get("battery_level"),
                "is_battery_powered": (data.get("system") or {}).get("is_battery_powered", False),
                "wifi_connected": (data.get("system") or {}).get("wifi_connected", False),
                "idle_minutes": (data.get("user") or {}).get("idle_minutes", 0.0),
                "time_of_day": (data.get("user") or {}).get("time_of_day"),
                "day_of_week": (data.get("user") or {}).get("day_of_week"),
            }
        except Exception as e:
            logger.debug(f"Context snapshot error: {e}")
            return {}


_bootstrap = None


def get_bootstrap() -> CoreBootstrap:
    """Get the singleton bootstrap."""
    global _bootstrap
    if _bootstrap is None:
        _bootstrap = CoreBootstrap()
    return _bootstrap


__all__ = ["CoreBootstrap", "get_bootstrap"]