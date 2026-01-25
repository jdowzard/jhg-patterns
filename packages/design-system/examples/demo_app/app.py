"""
Demo Flask application showcasing JHG Design System with Databricks integration.

Run with:
    # Set Databricks credentials
    export DATABRICKS_HOST=adb-xxx.azuredatabricks.net
    export DATABRICKS_TOKEN=dapi...
    export DATABRICKS_SQL_PATH=/sql/1.0/warehouses/xxx

    # Run app
    cd examples/demo_app
    uv run flask run --debug
"""

import os
from pathlib import Path
from flask import render_template, request, flash, redirect, url_for, g

import yaml
from jhg_patterns.ds import create_app
from jhg_patterns.ds.databricks import TTLCache

# Load app from YAML config
config_path = Path(__file__).parent / "config.yaml"
app = create_app(str(config_path))

# =============================================================================
# TTL CACHE SETUP
# =============================================================================
# Initialize cache from YAML config - this is how all JHG Flask apps should work.
# The cache settings in config.yaml define:
#   - default_ttl: Default cache duration (600s = 10 minutes)
#   - ttls: Per-key-prefix TTLs (dashboard_: 300s, users_: 120s, reports_: 1800s)
#
# This means:
#   - cache.get("dashboard_stats", ...) uses 300s TTL
#   - cache.get("users_list", ...) uses 120s TTL
#   - cache.get("reports_monthly", ...) uses 1800s TTL
#   - cache.get("anything_else", ...) uses 600s TTL

with open(config_path) as f:
    _config = yaml.safe_load(f)

cache_config = _config.get("cache", {})
cache = TTLCache(
    default_ttl=cache_config.get("default_ttl", 600),
    default_ttls=cache_config.get("ttls", {}),
    enabled=cache_config.get("enabled", True),
)

# Store cache in app for access in blueprints/extensions
app.cache = cache


# =============================================================================
# DATABRICKS INTEGRATION
# =============================================================================
# The design system provides utilities for Databricks. Here's how to use them:

def get_db():
    """Get Databricks connector (cached per request)."""
    if "db" not in g:
        try:
            from jhg_patterns.ds.databricks import DatabricksConnector, DatabricksConfig
            config = DatabricksConfig(
                host=os.environ.get("DATABRICKS_HOST", ""),
                token=os.environ.get("DATABRICKS_TOKEN", ""),
                sql_path=os.environ.get("DATABRICKS_SQL_PATH", ""),
                catalog="ai_a",
                schema="ds_template",
            )
            if config.host and config.token:
                g.db = DatabricksConnector(config)
            else:
                g.db = None
        except ImportError:
            g.db = None
    return g.db


def get_audit():
    """Get audit logger."""
    if "audit" not in g:
        db = get_db()
        if db:
            from jhg_patterns.ds.databricks import AuditLogger
            g.audit = AuditLogger(db, app_name="ds-demo", table="ai_a.ds_template.audit_log")
        else:
            g.audit = None
    return g.audit


def is_feature_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled in Databricks.

    Uses TTL cache with 'dashboard_' prefix (300s TTL from config).
    """
    def _load_flag():
        db = get_db()
        if not db:
            return None
        try:
            return db.query_one(
                "SELECT is_enabled, rollout_percentage FROM ai_a.ds_template.feature_flags WHERE flag_name = :flag",
                {"flag": flag_name}
            )
        except Exception:
            return None

    # Cache key uses 'dashboard_' prefix -> 300s TTL from config.yaml
    result = cache.get(f"dashboard_feature_{flag_name}", loader=_load_flag)
    return result and result.get("is_enabled", False)


def get_config_value(key: str, default=None):
    """
    Get config value from Databricks.

    Uses TTL cache with default TTL (600s from config).
    """
    def _load_config():
        db = get_db()
        if not db:
            return None
        try:
            return db.query_one(
                "SELECT config_value FROM ai_a.ds_template.app_config WHERE config_key = :key",
                {"key": key}
            )
        except Exception:
            return None

    # Uses default 600s TTL
    result = cache.get(f"config_{key}", loader=_load_config)
    return result["config_value"] if result else default


# =============================================================================
# SAMPLE DATA (fallback when Databricks not connected)
# =============================================================================

SAMPLE_USERS = [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "Admin", "status": "active"},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "User", "status": "active"},
    {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "User", "status": "inactive"},
    {"id": 4, "name": "Diana Ross", "email": "diana@example.com", "role": "Manager", "status": "active"},
    {"id": 5, "name": "Eve Wilson", "email": "eve@example.com", "role": "User", "status": "pending"},
]

SAMPLE_STATS = {
    "total_users": 1234,
    "active_sessions": 567,
    "revenue": "$125,430",
    "conversion_rate": "3.2%",
}


# =============================================================================
# CONTEXT & MIDDLEWARE
# =============================================================================

@app.context_processor
def inject_context():
    """Inject common variables into all templates."""
    db_connected = get_db() is not None
    return {
        "nav_links": [
            {"href": "/", "label": "Dashboard", "active": request.path == "/"},
            {"href": "/components", "label": "Components", "active": request.path == "/components"},
            {"href": "/forms", "label": "Forms", "active": request.path == "/forms"},
            {"href": "/tables", "label": "Tables", "active": request.path == "/tables"},
        ],
        "db_connected": db_connected,
        "dark_mode_enabled": is_feature_enabled("dark_mode") if db_connected else False,
    }


@app.after_request
def log_request(response):
    """Log requests to audit log (if Databricks connected)."""
    audit = get_audit()
    if audit and response.status_code < 400:
        try:
            audit.log(
                action="page_view",
                user_id=request.remote_addr,  # Would be actual user ID in production
                ip_address=request.remote_addr,
                metadata={"path": request.path, "method": request.method}
            )
        except Exception:
            pass  # Don't fail requests if audit logging fails
    return response


# =============================================================================
# ROUTES
# =============================================================================

def _load_dashboard_stats():
    """Load dashboard stats from Databricks (called by cache on miss)."""
    db = get_db()
    if not db:
        return None
    try:
        flags = db.query("SELECT COUNT(*) as cnt FROM ai_a.ds_template.feature_flags")
        enabled_flags = db.query("SELECT COUNT(*) as cnt FROM ai_a.ds_template.feature_flags WHERE is_enabled = true")
        return {
            "total_users": SAMPLE_STATS["total_users"],  # Would come from your users table
            "active_sessions": SAMPLE_STATS["active_sessions"],
            "feature_flags": f"{enabled_flags[0]['cnt']}/{flags[0]['cnt']}",
            "db_status": "Connected",
        }
    except Exception as e:
        return {"error": str(e)[:30]}


@app.route("/")
def dashboard():
    """Dashboard page with summary cards."""
    # Uses 'dashboard_' prefix -> 300s TTL from config.yaml
    # First request hits Databricks, subsequent requests use cache for 5 minutes
    cached_stats = cache.get("dashboard_stats", loader=_load_dashboard_stats)

    if cached_stats is None:
        # Databricks not configured - use sample data
        stats = SAMPLE_STATS.copy()
        stats["db_status"] = "Not configured"
    elif "error" in cached_stats:
        # Query failed - use sample data with error
        stats = SAMPLE_STATS.copy()
        stats["db_status"] = f"Error: {cached_stats['error']}"
    else:
        stats = cached_stats

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_users=SAMPLE_USERS[:3],
    )


@app.route("/components")
def components():
    """Component showcase page."""
    return render_template("components.html")


@app.route("/forms", methods=["GET", "POST"])
def forms():
    """Form examples page."""
    if request.method == "POST":
        flash("Form submitted successfully!", "success")

        # Log form submission to audit
        audit = get_audit()
        if audit:
            audit.log("form_submit", metadata={"form": "contact"})

        return redirect(url_for("forms"))
    return render_template("forms.html")


@app.route("/tables")
def tables():
    """Table examples page."""
    page = request.args.get("page", 1, type=int)
    per_page = 3

    # In production, this would query Databricks
    users = SAMPLE_USERS

    total_pages = (len(users) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page

    return render_template(
        "tables.html",
        users=users[start:end],
        all_users=users,
        page=page,
        total_pages=total_pages,
    )


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    """User detail page."""
    user = next((u for u in SAMPLE_USERS if u["id"] == user_id), None)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("tables"))
    return render_template("user_detail.html", user=user)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """Delete user (demo only)."""
    audit = get_audit()
    if audit:
        audit.log("user_delete_attempt", metadata={"user_id": user_id})

    flash(f"User {user_id} would be deleted", "warning")
    return redirect(url_for("tables"))


# =============================================================================
# DATABRICKS DATA ROUTES (examples)
# =============================================================================

@app.route("/api/feature-flags")
def api_feature_flags():
    """
    API endpoint to list feature flags from Databricks.

    Cached with 'dashboard_' prefix (300s TTL).
    """
    from flask import jsonify

    def _load_flags():
        db = get_db()
        if not db:
            return None
        return db.query("SELECT * FROM ai_a.ds_template.feature_flags ORDER BY flag_name")

    # Uses 'dashboard_' prefix -> 300s TTL
    flags = cache.get("dashboard_feature_flags_all", loader=_load_flags)

    if flags is None:
        return jsonify({"error": "Databricks not configured"}), 503

    return jsonify(flags)


@app.route("/api/config")
def api_config():
    """
    API endpoint to list app config from Databricks.

    Cached with default TTL (600s).
    """
    from flask import jsonify

    def _load_config():
        db = get_db()
        if not db:
            return None
        return db.query(
            "SELECT config_key, config_value, description FROM ai_a.ds_template.app_config WHERE is_secret = false ORDER BY config_key"
        )

    # Uses default 600s TTL
    config = cache.get("config_all", loader=_load_config)

    if config is None:
        return jsonify({"error": "Databricks not configured"}), 503

    return jsonify(config)


@app.route("/api/cache/stats")
def api_cache_stats():
    """
    API endpoint to view cache statistics.

    Shows active entries, hit/miss info, and TTL configuration.
    """
    from flask import jsonify

    stats = cache.stats()
    stats["ttl_config"] = {
        "default": cache_config.get("default_ttl", 600),
        "per_prefix": cache_config.get("ttls", {}),
    }
    return jsonify(stats)


@app.route("/api/cache/invalidate/<key>", methods=["POST"])
def api_cache_invalidate(key):
    """
    API endpoint to invalidate a cache key.

    POST /api/cache/invalidate/dashboard_stats -> invalidates dashboard_stats
    POST /api/cache/invalidate/dashboard_* -> invalidates all dashboard_* keys
    """
    from flask import jsonify

    if key.endswith("*"):
        cache.invalidate_pattern(key)
        return jsonify({"invalidated": key, "type": "pattern"})
    else:
        cache.invalidate(key)
        return jsonify({"invalidated": key, "type": "single"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
