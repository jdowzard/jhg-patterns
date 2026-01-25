"""
Health check blueprint.

Provides /health endpoint for monitoring and load balancer health checks.
"""

import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON with status and component health information.
        HTTP 200 if healthy, 503 if unhealthy.
    """
    status = {
        "status": "healthy",
        "components": {
            "app": "healthy",
        },
    }

    # Check cache if available
    cache = current_app.extensions.get("cache")
    if cache:
        status["components"]["cache"] = "healthy"
        status["cache_stats"] = {
            "enabled": getattr(cache, "_enabled", True),
            "entries": len(getattr(cache, "_cache", {})),
        }

    # Check Databricks if configured
    app_config = current_app.config.get("APP_CONFIG")
    if app_config and app_config.databricks.host:
        db_status = _check_databricks(app_config.databricks)
        status["components"]["databricks"] = db_status
        if db_status != "healthy":
            status["status"] = "degraded"

    # Overall health
    is_healthy = status["status"] in ("healthy", "degraded")

    return jsonify(status), 200 if is_healthy else 503


def _check_databricks(config):
    """Check Databricks connection health."""
    try:
        from databricks import sql

        with sql.connect(
            server_hostname=config.host,
            http_path=config.sql_path,
            access_token=config.token,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return "healthy"
    except ImportError:
        logger.debug("databricks-sql-connector not installed")
        return "not_configured"
    except Exception as e:
        logger.warning(f"Databricks health check failed: {e}")
        return "unhealthy"
