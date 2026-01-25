"""
TTL Cache Layer for Flask Applications.

Provides in-memory caching with configurable time-to-live (TTL) for each key.
Designed for Flask apps that read from external data sources with infrequent updates.

Usage:
    from jhg_patterns.flask import TTLCache

    cache = TTLCache()

    # Get data (fetches from source if cache expired)
    projects = cache.get('projects', fetch_fn=lambda: db.query("SELECT * FROM ..."))

    # Invalidate on write
    cache.invalidate('projects')

    # Get cache stats
    stats = cache.stats()

Configuration (environment variables):
    CACHE_ENABLED=true          # Enable/disable caching (default: true)
    CACHE_TTL_DEFAULT=600       # Default TTL in seconds (default: 10 minutes)
    CACHE_TTL_<KEY>=1800        # Per-key TTL override (e.g., CACHE_TTL_PROJECTS=1800)
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


def _env_bool(key: str, default: bool = True) -> bool:
    """Get boolean from environment variable."""
    val = os.getenv(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default


def _env_int(key: str, default: int) -> int:
    """Get integer from environment variable."""
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        return default


@dataclass
class CacheEntry:
    """Single cache entry with data and metadata."""

    data: Any
    fetched_at: float  # Unix timestamp
    ttl: int  # TTL in seconds
    fetch_count: int = 0  # How many times this was fetched from source
    hit_count: int = 0  # How many times served from cache

    @property
    def expires_at(self) -> float:
        return self.fetched_at + self.ttl

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> int:
        """Seconds until expiry (0 if expired)."""
        remaining = self.expires_at - time.time()
        return max(0, int(remaining))

    @property
    def fetched_at_iso(self) -> str:
        """ISO formatted fetch timestamp."""
        return datetime.fromtimestamp(self.fetched_at).isoformat()


class TTLCache:
    """
    Thread-safe TTL cache for external data sources.

    Features:
    - Configurable TTL per key via environment variables or defaults dict
    - Thread-safe access with RLock
    - Cache statistics for monitoring
    - Manual invalidation for write-through patterns
    - Stale-on-error fallback

    Example:
        cache = TTLCache(default_ttls={'users': 3600, 'posts': 300})
        users = cache.get('users', fetch_fn=lambda: api.get_users())

    Environment variables:
        CACHE_ENABLED: Enable/disable cache (default: true)
        CACHE_TTL_DEFAULT: Default TTL in seconds (default: 600)
        CACHE_TTL_<KEY>: Per-key TTL override (e.g., CACHE_TTL_USERS=3600)
    """

    def __init__(self, default_ttls: Dict[str, int] = None):
        """
        Initialize the cache.

        Args:
            default_ttls: Optional dict mapping keys to default TTL in seconds.
                         Can be overridden by environment variables.
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._enabled = _env_bool("CACHE_ENABLED", default=True)
        self._default_ttl = _env_int("CACHE_TTL_DEFAULT", 600)
        self._default_ttls = default_ttls or {}

    def _get_ttl(self, key: str) -> int:
        """Get TTL for a key (env var > default mapping > global default)."""
        # Check for env var override: CACHE_TTL_PROJECTS=1800
        env_key = f"CACHE_TTL_{key.upper()}"
        env_ttl = os.getenv(env_key)
        if env_ttl:
            try:
                return int(env_ttl)
            except ValueError:
                pass

        # Fall back to default mapping
        return self._default_ttls.get(key, self._default_ttl)

    def get(
        self,
        key: str,
        fetch_fn: Callable[[], Any],
        ttl: int = None,
        force_refresh: bool = False,
    ) -> Any:
        """
        Get data from cache, fetching from source if expired.

        Args:
            key: Cache key (e.g., 'projects', 'users')
            fetch_fn: Function to call to fetch fresh data
            ttl: Optional TTL override in seconds
            force_refresh: If True, bypass cache and fetch fresh

        Returns:
            Cached or freshly fetched data

        Raises:
            Exception: If fetch fails and no stale data is available
        """
        if not self._enabled:
            logger.debug(f"Cache disabled, fetching {key} directly")
            return fetch_fn()

        ttl = ttl or self._get_ttl(key)

        with self._lock:
            entry = self._cache.get(key)

            # Cache hit - return cached data
            if entry and not entry.is_expired and not force_refresh:
                entry.hit_count += 1
                logger.debug(f"Cache hit for {key} (TTL: {entry.ttl_remaining}s remaining)")
                return entry.data

            # Cache miss or expired
            logger.info(f"Cache {'miss' if not entry else 'expired'} for {key}, fetching fresh")

        # Fetch outside lock to avoid blocking other cache access
        try:
            start = time.time()
            data = fetch_fn()
            elapsed = time.time() - start
            logger.info(f"Fetched {key} in {elapsed:.2f}s")
        except Exception as e:
            # On fetch error, return stale data if available
            if entry:
                logger.warning(f"Fetch failed for {key}, returning stale data: {e}")
                return entry.data
            raise

        # Update cache
        with self._lock:
            fetch_count = (entry.fetch_count + 1) if entry else 1
            self._cache[key] = CacheEntry(
                data=data,
                fetched_at=time.time(),
                ttl=ttl,
                fetch_count=fetch_count,
                hit_count=0,
            )

        return data

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry (call after writes).

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry existed and was removed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"Cache invalidated: {key}")
                return True
            return False

    def invalidate_all(self) -> int:
        """
        Invalidate all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries")
            return count

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache stats including:
            - enabled: Whether cache is enabled
            - default_ttl: Default TTL in seconds
            - entry_count: Number of cached entries
            - total_hits: Total cache hits
            - total_fetches: Total fetches from source
            - hit_rate: Cache hit rate (0-1)
            - entries: Per-entry statistics
        """
        with self._lock:
            entries = {}
            total_hits = 0
            total_fetches = 0

            for key, entry in self._cache.items():
                entries[key] = {
                    "fetched_at": entry.fetched_at_iso,
                    "ttl": entry.ttl,
                    "ttl_remaining": entry.ttl_remaining,
                    "is_expired": entry.is_expired,
                    "hit_count": entry.hit_count,
                    "fetch_count": entry.fetch_count,
                }
                total_hits += entry.hit_count
                total_fetches += entry.fetch_count

            return {
                "enabled": self._enabled,
                "default_ttl": self._default_ttl,
                "entry_count": len(self._cache),
                "total_hits": total_hits,
                "total_fetches": total_fetches,
                "hit_rate": (
                    total_hits / (total_hits + total_fetches)
                    if (total_hits + total_fetches) > 0
                    else 0
                ),
                "entries": entries,
            }

    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific cache entry."""
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            return {
                "fetched_at": entry.fetched_at_iso,
                "ttl": entry.ttl,
                "ttl_remaining": entry.ttl_remaining,
                "is_expired": entry.is_expired,
                "hit_count": entry.hit_count,
                "fetch_count": entry.fetch_count,
            }
