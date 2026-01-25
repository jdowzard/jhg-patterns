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

from jhg_patterns.ds import create_app

# Load app from YAML config
config_path = Path(__file__).parent / "config.yaml"
app = create_app(str(config_path))


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
    """Check if a feature flag is enabled in Databricks."""
    db = get_db()
    if not db:
        return False
    try:
        result = db.query_one(
            "SELECT is_enabled, rollout_percentage FROM ai_a.ds_template.feature_flags WHERE flag_name = :flag",
            {"flag": flag_name}
        )
        return result and result.get("is_enabled", False)
    except Exception:
        return False


def get_config_value(key: str, default=None):
    """Get config value from Databricks."""
    db = get_db()
    if not db:
        return default
    try:
        result = db.query_one(
            "SELECT config_value FROM ai_a.ds_template.app_config WHERE config_key = :key",
            {"key": key}
        )
        return result["config_value"] if result else default
    except Exception:
        return default


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

@app.route("/")
def dashboard():
    """Dashboard page with summary cards."""
    db = get_db()

    # Try to get stats from Databricks, fall back to sample data
    if db:
        try:
            # Get feature flags count
            flags = db.query("SELECT COUNT(*) as cnt FROM ai_a.ds_template.feature_flags")
            enabled_flags = db.query("SELECT COUNT(*) as cnt FROM ai_a.ds_template.feature_flags WHERE is_enabled = true")

            stats = {
                "total_users": SAMPLE_STATS["total_users"],  # Would come from your users table
                "active_sessions": SAMPLE_STATS["active_sessions"],
                "feature_flags": f"{enabled_flags[0]['cnt']}/{flags[0]['cnt']}",
                "db_status": "Connected",
            }
        except Exception as e:
            stats = SAMPLE_STATS
            stats["db_status"] = f"Error: {str(e)[:30]}"
    else:
        stats = SAMPLE_STATS
        stats["db_status"] = "Not configured"

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
    """API endpoint to list feature flags from Databricks."""
    from flask import jsonify

    db = get_db()
    if not db:
        return jsonify({"error": "Databricks not configured"}), 503

    try:
        flags = db.query("SELECT * FROM ai_a.ds_template.feature_flags ORDER BY flag_name")
        return jsonify(flags)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config")
def api_config():
    """API endpoint to list app config from Databricks."""
    from flask import jsonify

    db = get_db()
    if not db:
        return jsonify({"error": "Databricks not configured"}), 503

    try:
        config = db.query("SELECT config_key, config_value, description FROM ai_a.ds_template.app_config WHERE is_secret = false ORDER BY config_key")
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
