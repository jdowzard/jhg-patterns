"""
JHG Design System - Complete UI framework for JHG Flask applications.

Provides:
- Theme system with customizable colors and tokens
- Jinja2 component macros (buttons, cards, tables, modals, forms)
- JavaScript behaviors (Alpine.js based)
- Flask integration (app factory, blueprints, middleware)
- Databricks utilities (connection, audit logging, caching)
- Authentication (Databricks Apps, MS Graph, SharePoint)

Usage:
    from jhg_patterns.ds import DesignSystem, Theme, create_app

    # Quick start with defaults
    app = create_app("my-app")

    # Or customize
    theme = Theme.from_yaml("theme.yaml")
    ds = DesignSystem(theme=theme)
    app = create_app("my-app", design_system=ds)

    # With authentication
    from jhg_patterns.ds.auth import init_auth, login_required
    init_auth(app)

    @app.route('/protected')
    @login_required
    def protected():
        return "Hello"
"""

from jhg_patterns.ds.theme import Theme, ColorPalette
from jhg_patterns.ds.system import DesignSystem
from jhg_patterns.ds.app import create_app, AppConfig

# Auth exports (lazy import to avoid msal dependency if not used)
from jhg_patterns.ds.auth import (
    init_auth,
    login_required,
    require_role,
    get_current_user,
    is_databricks_app,
)

__all__ = [
    # Theme & Design System
    "Theme",
    "ColorPalette",
    "DesignSystem",
    # Flask integration
    "create_app",
    "AppConfig",
    # Authentication
    "init_auth",
    "login_required",
    "require_role",
    "get_current_user",
    "is_databricks_app",
]
__version__ = "0.1.0"
