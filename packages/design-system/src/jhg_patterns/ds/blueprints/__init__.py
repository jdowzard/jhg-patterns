"""
Flask blueprints for JHG Design System.

Provides:
- health_bp: Health check endpoint (/health)
- cache_bp: Cache management API (/api/cache/*)
"""

from jhg_patterns.ds.blueprints.health import health_bp
from jhg_patterns.ds.blueprints.cache import cache_bp

__all__ = ["health_bp", "cache_bp"]
