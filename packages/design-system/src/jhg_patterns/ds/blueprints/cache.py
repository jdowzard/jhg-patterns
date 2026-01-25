"""
Cache management blueprint.

Provides API endpoints for cache statistics and management.
"""

import logging
from flask import Blueprint, jsonify, request, current_app

logger = logging.getLogger(__name__)

cache_bp = Blueprint("cache", __name__)


def _get_cache():
    """Get cache from app extensions."""
    return current_app.extensions.get("cache")


@cache_bp.route("/cache/stats")
def cache_stats():
    """
    Get cache statistics.

    Returns:
        JSON with cache status and statistics.
    """
    cache = _get_cache()
    if not cache:
        return jsonify({"error": "Cache not configured"}), 404

    stats = {
        "enabled": getattr(cache, "_enabled", True),
        "default_ttl": getattr(cache, "_default_ttl", 600),
        "entries": {},
    }

    # Get cache entries info
    cache_data = getattr(cache, "_cache", {})
    for key, entry in cache_data.items():
        stats["entries"][key] = {
            "has_data": entry.get("data") is not None,
            "expires_at": entry.get("expires_at"),
            "ttl": entry.get("ttl"),
        }

    return jsonify(stats)


@cache_bp.route("/cache/refresh", methods=["POST"])
def cache_refresh():
    """
    Refresh cache for a specific key.

    Request body:
        {"key": "cache_key_name"}

    Returns:
        JSON with refresh status.
    """
    cache = _get_cache()
    if not cache:
        return jsonify({"error": "Cache not configured"}), 404

    data = request.get_json() or {}
    key = data.get("key")

    if not key:
        return jsonify({"error": "Key required"}), 400

    # Invalidate the key to trigger refresh on next access
    cache_data = getattr(cache, "_cache", {})
    if key in cache_data:
        del cache_data[key]
        logger.info(f"Cache key '{key}' invalidated for refresh")
        return jsonify({"status": "invalidated", "key": key})

    return jsonify({"status": "not_found", "key": key}), 404


@cache_bp.route("/cache/invalidate", methods=["POST"])
def cache_invalidate():
    """
    Invalidate cache entries.

    Request body:
        {"key": "specific_key"} - invalidate specific key
        {"pattern": "prefix_*"} - invalidate by pattern
        {} - invalidate all

    Returns:
        JSON with invalidation results.
    """
    cache = _get_cache()
    if not cache:
        return jsonify({"error": "Cache not configured"}), 404

    data = request.get_json() or {}
    key = data.get("key")
    pattern = data.get("pattern")

    cache_data = getattr(cache, "_cache", {})
    invalidated = []

    if key:
        # Invalidate specific key
        if key in cache_data:
            del cache_data[key]
            invalidated.append(key)
    elif pattern:
        # Invalidate by pattern (simple prefix matching)
        prefix = pattern.rstrip("*")
        keys_to_remove = [k for k in cache_data if k.startswith(prefix)]
        for k in keys_to_remove:
            del cache_data[k]
            invalidated.append(k)
    else:
        # Invalidate all
        invalidated = list(cache_data.keys())
        cache_data.clear()

    logger.info(f"Cache invalidated: {len(invalidated)} entries")

    return jsonify({
        "status": "invalidated",
        "count": len(invalidated),
        "keys": invalidated,
    })


@cache_bp.route("/cache/enable", methods=["POST"])
def cache_enable():
    """Enable or disable caching."""
    cache = _get_cache()
    if not cache:
        return jsonify({"error": "Cache not configured"}), 404

    data = request.get_json() or {}
    enabled = data.get("enabled", True)

    cache._enabled = enabled
    logger.info(f"Cache {'enabled' if enabled else 'disabled'}")

    return jsonify({"status": "ok", "enabled": enabled})
