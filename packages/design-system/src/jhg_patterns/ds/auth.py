"""
Databricks Apps authentication for Flask applications.

In Databricks Apps, user identity comes from X-Forwarded-Preferred-Username header.
For local development, uses Databricks SDK to get current user.

Usage:
    from jhg_patterns.ds.auth import init_auth, login_required, get_current_user

    app = Flask(__name__)
    init_auth(app)

    @app.route('/protected')
    @login_required
    def protected_route():
        user = get_current_user()
        return f"Hello, {user}"
"""

import logging
import os
from functools import wraps
from typing import Callable, List, Optional

from flask import Flask, current_app, g, request, session

logger = logging.getLogger(__name__)


def get_current_user() -> Optional[str]:
    """
    Get the current authenticated user's email.

    Returns:
        User email or None if not authenticated
    """
    return session.get("user_email")


def is_databricks_app() -> bool:
    """
    Check if running as a Databricks App.

    Returns:
        True if running in Databricks Apps environment
    """
    return (
        os.environ.get("DATABRICKS_RUNTIME_VERSION") is not None
        or os.environ.get("DATABRICKS_APP_NAME") is not None
        or "/app/python/source_code" in os.getcwd()
    )


def _is_auth_bypass_allowed(app: Flask) -> bool:
    """Check if auth bypass is allowed (only in non-production environments)."""
    if app.config.get("ENABLE_AUTH", True):
        return False  # Auth is enabled, no bypass

    # Only allow bypass in development/testing
    env = app.config.get("ENV", "production")
    if env == "production":
        logger.error(
            "ENABLE_AUTH=False is not allowed in production! Forcing auth enabled."
        )
        return False
    return True


def init_auth(
    app: Flask,
    skip_paths: Optional[List[str]] = None,
    dev_fallback_user: str = "dev@jhg.com.au",
) -> None:
    """
    Initialize authentication for the Flask app.

    Registers before_request handler that captures authenticated user
    from Databricks Apps headers or SDK.

    Args:
        app: Flask application instance
        skip_paths: Paths to skip auth (e.g., ['/health', '/static/'])
        dev_fallback_user: User email for local dev without Databricks connection
    """
    skip_paths = skip_paths or ["/health", "/static/", "/favicon.ico"]

    # Check if auth is enabled (bypass only allowed in non-production)
    if _is_auth_bypass_allowed(app):
        logger.warning(
            "Authentication disabled via ENABLE_AUTH config (non-production only)"
        )
        return

    @app.before_request
    def capture_authenticated_user():
        """
        Capture user email from Databricks App headers or SDK.

        Production (Databricks Apps): X-Forwarded-Preferred-Username header
        Local development: Databricks SDK current_user.me()
        """
        # Skip for configured paths
        for path in skip_paths:
            if request.path.startswith(path):
                return

        # Try to get user from Databricks Apps header
        user_email = request.headers.get("X-Forwarded-Preferred-Username")

        if user_email:
            # Production: user from Databricks Apps proxy
            if session.get("user_email") != user_email:
                logger.info(f"User authenticated via header: {user_email}")
                session["user_email"] = user_email
            g.user_email = user_email
            return

        # Already have user in session - no need to call SDK again
        if session.get("user_email"):
            g.user_email = session["user_email"]
            return

        # Local development: get user from Databricks SDK
        try:
            from databricks.sdk import WorkspaceClient

            w = WorkspaceClient()
            current_user = w.current_user.me()
            user_email = current_user.user_name
            session["user_email"] = user_email
            g.user_email = user_email
            logger.info(f"User authenticated via SDK: {user_email}")
        except Exception as e:
            logger.warning(f"Could not get user from SDK: {e}")
            # For local dev without Databricks connection, use fallback
            if app.config.get("ENV") == "development" or app.debug:
                session["user_email"] = dev_fallback_user
                g.user_email = dev_fallback_user
                logger.info(f"Using development fallback user: {dev_fallback_user}")

    logger.info("Databricks Apps authentication initialized")


def login_required(f: Callable) -> Callable:
    """
    Decorator to require authentication.

    In Databricks Apps, users are authenticated by Databricks
    before reaching the app, so this mainly catches edge cases.

    Usage:
        @app.route('/projects/')
        @login_required
        def list_projects():
            return render_template('projects/list.html')
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if auth bypass is allowed (non-production only)
        if _is_auth_bypass_allowed(current_app):
            return f(*args, **kwargs)

        if not session.get("user_email"):
            logger.warning(f"Unauthenticated access attempt to {request.path}")
            return "Please access this application through Databricks.", 401
        return f(*args, **kwargs)

    return decorated_function


def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific roles for access.

    Roles are checked against GLOBAL_ADMINS config and an optional
    role_checker function in app config.

    Args:
        allowed_roles: List of role names that can access this route

    Usage:
        @app.route('/admin/')
        @require_role(['admin'])
        def admin_page():
            return render_template('admin.html')
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if auth bypass is allowed
            if _is_auth_bypass_allowed(current_app):
                return f(*args, **kwargs)

            user_email = get_current_user()
            if not user_email:
                return "Authentication required", 401

            user_email = user_email.lower()

            # Check if user is global admin
            global_admins = current_app.config.get("GLOBAL_ADMINS", [])
            if user_email in [email.lower() for email in global_admins]:
                return f(*args, **kwargs)

            # Check custom role checker if configured
            role_checker = current_app.config.get("ROLE_CHECKER")
            if role_checker and callable(role_checker):
                user_roles = role_checker(user_email)
                if any(role in user_roles for role in allowed_roles):
                    return f(*args, **kwargs)

            logger.warning(
                f"Access denied for {user_email} - required roles: {allowed_roles}"
            )
            return "Access denied", 403

        return decorated_function

    return decorator


def get_user_display_name() -> str:
    """
    Get a display-friendly name for the current user.

    Returns email username part (before @) with proper casing.
    """
    email = get_current_user()
    if not email:
        return "Guest"

    # Extract name from email (before @)
    name_part = email.split("@")[0]

    # Convert jdowzard or j.dowzard to J Dowzard
    if "." in name_part:
        parts = name_part.split(".")
        return " ".join(p.title() for p in parts)
    else:
        # Try to split by common patterns (jdowzard -> J Dowzard is hard)
        # Just title case the whole thing
        return name_part.title()
