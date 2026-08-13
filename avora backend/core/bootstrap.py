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
        if getattr(self, "_init_done", False):
            return
        self._init_done = True
        self._started = False
        self._results: Dict[str, Any] = {}
        self._engines: Dict[str, Any] = {}

    # ========================================================
    # PUBLIC API
    # ========================================================

    def start(self) -> Dict[str, Any]:
        """Start all core systems and return status dict."""
        if self._started:
            return self._results

        results: Dict[str, Any] = {}

        # 1. Register all skills
        results["skills_registered"] = self.load_skills()

        # 1b. Index applications for launcher
        try:
            from app_indexer import get_app_indexer
            indexer = get_app_indexer()
            app_count = indexer.index_applications()
            results["apps_indexed"] = app_count
            logger.info("App index: %s applications", app_count)
        except Exception as e:
            logger.warning("App indexing failed: %s", e)

        # 2. Initialize core engines
        for name, (module_name, getter) in _ENGINE_GETTERS.items():
            try:
                module = importlib.import_module(module_name)
                engine = getattr(module, getter)()
                self._engines[name] = engine
                logger.info("%s engine initialized", name)
            except Exception as e:
                logger.warning("%s engine init failed: %s", name, e)

        # 3. Collect health status
        health = self._engines.get("health")
        if health is not None:
            try:
                status = health.get_health_status()
                results["health"] = status
            except Exception as e:
                logger.warning("Health check failed: %s", e)

        self._started = True
        self._results = results
        return results

    def load_skills(self) -> List[str]:
        """Discover and register all available skills."""
        registered: List[str] = []
        try:
            import skills
            for module_info in pkgutil.iter_modules(skills.__path__):
                mod_name = module_info.name
                if mod_name.startswith("_"):
                    continue
                try:
                    full_name = f"skills.{mod_name}"
                    importlib.import_module(full_name)
                    registered.append(full_name)
                except Exception as e:
                    logger.debug("Skill registration skipped %s: %s", mod_name, e)
        except ImportError:
            logger.warning("skills package not available")
        return registered

    def stop(self):
        """Shut down core systems gracefully."""
        for name, engine in self._engines.items():
            stop_method = getattr(engine, "stop", None)
            if callable(stop_method):
                try:
                    stop_method()
                    logger.info("%s engine stopped", name)
                except Exception as e:
                    logger.debug("%s engine stop error: %s", name, e)


__all__ = ["CoreBootstrap"]
