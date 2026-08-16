"""
============================================================
AVORA Cache Manager
============================================================

File-based cache system with TTL, LRU eviction, and tagging.

Features:
- File-based caching with JSON persistence
- TTL support
- LRU eviction
- Tag-based invalidation
- Statistics tracking
"""

import json
import time
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .app_paths import APP_DATA_DIR

logger = logging.getLogger("CacheManager")

_CACHE_DIR = APP_DATA_DIR / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_app_cache = None
_cache_lock = threading.Lock()


class CacheManager:
    """Thread-safe file-based cache manager."""

    def __init__(self, max_size_mb: int = 50, default_ttl: float = 3600.0):
        self._cache_dir = _CACHE_DIR
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._sizes: Dict[str, int] = {}
        self._access_times: Dict[str, float] = {}
        self._current_size = 0
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidation_events": 0,
        }

    def _get_cache_path(self, name: str) -> Path:
        """Get the file path for a cache entry."""
        safe_name = name.replace("/", "_").replace("\\", "_")
        return self._cache_dir / f"{safe_name}.json"

    def get(self, name: str, default=None):
        """Get a cached value."""
        with self._lock:
            if name not in self._cache:
                self._stats["misses"] += 1
                return default

            entry = self._cache[name]
            ttl = entry.get("_ttl", self._default_ttl)
            timestamp = entry.get("_timestamp", 0)

            if time.time() - timestamp > ttl:
                self.delete(name)
                self._stats["misses"] += 1
                return default

            self._access_times[name] = time.time()
            self._stats["hits"] += 1
            return entry.get("value", default)

    def set(self, name: str, value: Any, ttl: Optional[float] = None, persist: bool = True, tags: Optional[List[str]] = None):
        """Set a cached value."""
        with self._lock:
            size = len(json.dumps(value, default=str).encode("utf-8"))

            if name in self._cache:
                old_size = self._sizes.get(name, 0)
                self._current_size -= old_size

            self._cache[name] = {
                "value": value,
                "_timestamp": time.time(),
                "_ttl": ttl if ttl is not None else self._default_ttl,
                "_tags": tags or [],
            }
            self._sizes[name] = size
            self._access_times[name] = time.time()
            self._current_size += size

            self._evict_lru()

            if persist:
                try:
                    self._persist_entry(name, value, ttl, tags)
                except Exception as e:
                    logger.debug(f"Cache write error for {name}: {e}")

    def _persist_entry(self, name: str, value: Any, ttl: Optional[float], tags: Optional[List[str]]):
        """Persist a cache entry to disk."""
        file_path = self._get_cache_path(name)
        ttl_value = {
            "_timestamp": time.time(),
            "_ttl": ttl if ttl is not None else self._default_ttl,
            "value": value,
            "_tags": tags or [],
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ttl_value, f, indent=2, default=str)

    def _evict_lru(self):
        """Evict least recently used entries if over size limit."""
        if not self._access_times:
            return

        while self._current_size > self._max_size_bytes and self._access_times:
            lru_name = min(self._access_times, key=self._access_times.get)
            old_size = self._sizes.pop(lru_name, 0)
            self._current_size -= old_size
            self._cache.pop(lru_name, None)
            self._access_times.pop(lru_name, None)
            file_path = self._get_cache_path(lru_name)
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass
            self._stats["evictions"] += 1

    def delete(self, name: str):
        """Delete a cache entry."""
        with self._lock:
            result = False
            if name in self._cache:
                self._cache.pop(name)
                self._sizes.pop(name, None)
                self._access_times.pop(name, None)
                result = True

            file_path = self._get_cache_path(name)
            if file_path.exists():
                try:
                    file_path.unlink()
                    result = True
                except OSError:
                    pass
            return result

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._sizes.clear()
            self._access_times.clear()
            self._current_size = 0

            for file_path in self._cache_dir.glob("*.json"):
                try:
                    file_path.unlink()
                except OSError:
                    pass

            logger.debug("Cache cleared")

    def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern."""
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self.clear()
                self._stats["invalidation_events"] += count
                return

            names_to_delete = []
            for name in list(self._cache.keys()):
                if pattern in name or name.startswith(pattern):
                    names_to_delete.append(name)

            for name in names_to_delete:
                self.delete(name)

            self._stats["invalidation_events"] += len(names_to_delete)

    def invalidate_by_tag(self, tag: str):
        """Invalidate all cache entries with a specific tag."""
        with self._lock:
            invalidated = 0
            for name in list(self._cache.keys()):
                entry = self._cache.get(name, {})
                entry_tags = entry.get("_tags", [])
                if tag in entry_tags or name.startswith(tag):
                    self.delete(name)
                    invalidated += 1

            self._stats["invalidation_events"] += invalidated

    def warm_up(self, keys: List[str]):
        """Pre-load cache entries."""
        for key in keys:
            if key not in self._cache:
                self.get(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "invalidation_events": self._stats["invalidation_events"],
                "hit_rate": hit_rate,
                "size_bytes": self._current_size,
                "size_mb": round(self._current_size / 1048576, 2),
                "max_size_mb": round(self._max_size_bytes / 1048576, 2),
                "entry_count": len(self._cache),
            }

    def cleanup_expired(self, max_age_seconds: Optional[int] = None):
        """Remove expired cache entries."""
        if max_age_seconds is None:
            max_age_seconds = int(self._default_ttl * 2)

        with self._lock:
            now = time.time()
            expired = []
            for name, access_time in list(self._access_times.items()):
                if now - access_time > max_age_seconds:
                    expired.append(name)

            for name in expired:
                self.delete(name)


def get_app_cache() -> CacheManager:
    """Get the singleton cache manager."""
    global _app_cache
    if _app_cache is None:
        with _cache_lock:
            if _app_cache is None:
                _app_cache = CacheManager()
    return _app_cache


__all__ = ["CacheManager", "get_app_cache"]
