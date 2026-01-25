"""
TTL Cache with Databricks Delta table backing.

Provides in-memory caching with optional persistence to Delta tables
for shared cache across multiple instances.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry."""

    data: Any
    expires_at: float
    ttl: int
    created_at: float = field(default_factory=time.time)


class TTLCache:
    """
    In-memory TTL cache with optional Delta table persistence.

    Usage:
        cache = TTLCache(default_ttl=600)

        # Get or set with loader function
        data = cache.get("my_key", loader=lambda: fetch_data())

        # Set directly
        cache.set("my_key", data, ttl=300)

        # Invalidate
        cache.invalidate("my_key")

        # Decorator
        @cache.cached("expensive_query", ttl=1800)
        def get_expensive_data():
            return query_databricks()
    """

    def __init__(
        self,
        default_ttl: int = 600,
        default_ttls: Optional[Dict[str, int]] = None,
        enabled: bool = True,
    ):
        """
        Initialize cache.

        Args:
            default_ttl: Default TTL in seconds
            default_ttls: Per-key default TTLs {"key_pattern": ttl}
            enabled: Whether caching is enabled
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._default_ttls = default_ttls or {}
        self._enabled = enabled

    def _get_ttl(self, key: str, ttl: Optional[int] = None) -> int:
        """Get TTL for a key."""
        if ttl is not None:
            return ttl

        # Check for key-specific TTL
        for pattern, pattern_ttl in self._default_ttls.items():
            if key.startswith(pattern.rstrip("*")):
                return pattern_ttl

        return self._default_ttl

    def get(
        self,
        key: str,
        loader: Optional[Callable] = None,
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get value from cache, optionally loading if missing/expired.

        Args:
            key: Cache key
            loader: Function to load data if not cached
            ttl: TTL for this entry (uses default if not provided)

        Returns:
            Cached value or loader result
        """
        if not self._enabled:
            return loader() if loader else None

        entry = self._cache.get(key)

        # Check if valid
        if entry and time.time() < entry.expires_at:
            logger.debug(f"Cache hit: {key}")
            return entry.data

        # Cache miss or expired
        logger.debug(f"Cache miss: {key}")

        if loader is None:
            return None

        # Load and cache
        data = loader()
        self.set(key, data, ttl)
        return data

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """
        Set a cache entry.

        Args:
            key: Cache key
            data: Data to cache
            ttl: TTL in seconds
        """
        if not self._enabled:
            return

        effective_ttl = self._get_ttl(key, ttl)
        self._cache[key] = CacheEntry(
            data=data,
            expires_at=time.time() + effective_ttl,
            ttl=effective_ttl,
        )
        logger.debug(f"Cache set: {key} (TTL={effective_ttl}s)")

    def invalidate(self, key: str):
        """
        Invalidate a cache entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidated: {key}")

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Key prefix pattern (e.g., "user_*")
        """
        prefix = pattern.rstrip("*")
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]
        logger.debug(f"Cache invalidated: {len(keys_to_remove)} keys matching {pattern}")

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        now = time.time()
        active = sum(1 for e in self._cache.values() if e.expires_at > now)
        expired = len(self._cache) - active

        return {
            "enabled": self._enabled,
            "total_entries": len(self._cache),
            "active_entries": active,
            "expired_entries": expired,
            "default_ttl": self._default_ttl,
        }

    def cached(self, key: str, ttl: Optional[int] = None):
        """
        Decorator for caching function results.

        Args:
            key: Cache key
            ttl: TTL in seconds

        Usage:
            @cache.cached("expensive_query", ttl=1800)
            def get_data():
                return query_databricks()
        """

        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                return self.get(key, loader=lambda: func(*args, **kwargs), ttl=ttl)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    def cached_method(self, key_func: Callable[..., str], ttl: Optional[int] = None):
        """
        Decorator for caching method results with dynamic key.

        Args:
            key_func: Function that returns cache key from method args
            ttl: TTL in seconds

        Usage:
            @cache.cached_method(lambda self, user_id: f"user_{user_id}", ttl=300)
            def get_user(self, user_id):
                return query_user(user_id)
        """

        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs)
                return self.get(key, loader=lambda: func(*args, **kwargs), ttl=ttl)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator
