"""
============================================================
AVORA Alias Manager
============================================================

Manages application name aliases for the launcher.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional

from .app_paths import APP_DATA_DIR

logger = logging.getLogger("AliasManager")

_ALIAS_FILE = APP_DATA_DIR / "aliases.json"
_alias_lock = threading.RLock()
_aliases: Dict[str, str] = {}


def _load_aliases():
    global _aliases
    try:
        if _ALIAS_FILE.exists():
            with open(_ALIAS_FILE, "r", encoding="utf-8") as f:
                _aliases = json.load(f)
    except Exception:
        _aliases = {}


def _save_aliases():
    try:
        _ALIAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_ALIAS_FILE, "w", encoding="utf-8") as f:
            json.dump(_aliases, f, indent=2)
    except Exception as e:
        logger.debug(f"Alias save error: {e}")


def add_alias(canonical_name: str, alias: str, source: str = "user"):
    """Add an alias for an application."""
    with _alias_lock:
        _aliases[alias.lower()] = canonical_name
        _save_aliases()


def get_alias(alias: str) -> Optional[str]:
    """Get the canonical name for an alias."""
    with _alias_lock:
        return _aliases.get(alias.lower())


def remove_alias(alias: str):
    """Remove an alias."""
    with _alias_lock:
        _aliases.pop(alias.lower(), None)
        _save_aliases()


def get_all_aliases() -> Dict[str, str]:
    """Get all aliases."""
    with _alias_lock:
        return dict(_aliases)


class AliasManager:
    """Alias management class."""

    def __init__(self):
        _load_aliases()

    def add(self, canonical_name: str, alias: str, source: str = "user"):
        add_alias(canonical_name, alias, source)

    def get(self, alias: str) -> Optional[str]:
        return get_alias(alias)

    def remove(self, alias: str):
        remove_alias(alias)

    def get_all(self) -> Dict[str, str]:
        return get_all_aliases()


_instance = None


def get_alias_manager() -> AliasManager:
    """Get the singleton alias manager."""
    global _instance
    if _instance is None:
        _instance = AliasManager()
    return _instance


__all__ = ["AliasManager", "get_alias_manager", "add_alias", "get_alias", "remove_alias", "get_all_aliases"]
