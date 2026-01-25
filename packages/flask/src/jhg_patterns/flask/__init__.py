"""
JHG Flask Patterns - Reusable Flask components for JHG projects.

Includes:
- TTLCache: In-memory cache with configurable TTL per key
- Health check helpers
- Auth utilities
"""

from jhg_patterns.flask.cache import TTLCache, CacheEntry

__all__ = ["TTLCache", "CacheEntry"]
__version__ = "0.1.0"
