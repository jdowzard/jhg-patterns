"""
Demo Flask application showcasing JHG Design System.

Run with:
    cd examples/demo_app
    uv run flask run --debug
"""

from pathlib import Path
from flask import render_template, request, flash, redirect, url_for

from jhg_patterns.ds import create_app, AppConfig

# Load app from YAML config
config_path = Path(__file__).parent / "config.yaml"
app = create_app(str(config_path))


# Sample data
USERS = [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "Admin", "status": "active"},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "User", "status": "active"},
    {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "User", "status": "inactive"},
    {"id": 4, "name": "Diana Ross", "email": "diana@example.com", "role": "Manager", "status": "active"},
    {"id": 5, "name": "Eve Wilson", "email": "eve@example.com", "role": "User", "status": "pending"},
]

STATS = {
    "total_users": 1234,
    "active_sessions": 567,
    "revenue": "$125,430",
    "conversion_rate": "3.2%",
}


@app.context_processor
def inject_nav():
    """Inject navigation links into all templates."""
    return {
        "nav_links": [
            {"href": "/", "label": "Dashboard", "active": request.path == "/"},
            {"href": "/components", "label": "Components", "active": request.path == "/components"},
            {"href": "/forms", "label": "Forms", "active": request.path == "/forms"},
            {"href": "/tables", "label": "Tables", "active": request.path == "/tables"},
        ]
    }


@app.route("/")
def dashboard():
    """Dashboard page with summary cards."""
    return render_template(
        "dashboard.html",
        stats=STATS,
        recent_users=USERS[:3],
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
        return redirect(url_for("forms"))
    return render_template("forms.html")


@app.route("/tables")
def tables():
    """Table examples page."""
    page = request.args.get("page", 1, type=int)
    per_page = 3
    total_pages = (len(USERS) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page

    return render_template(
        "tables.html",
        users=USERS[start:end],
        all_users=USERS,
        page=page,
        total_pages=total_pages,
    )


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    """User detail page."""
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("tables"))
    return render_template("user_detail.html", user=user)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """Delete user (demo only)."""
    flash(f"User {user_id} would be deleted", "warning")
    return redirect(url_for("tables"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
