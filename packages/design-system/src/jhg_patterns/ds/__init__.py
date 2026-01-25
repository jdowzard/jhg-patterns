"""
JHG Design System - Complete UI framework for JHG Flask applications.

Provides:
- Theme system with customizable colors and tokens
- Jinja2 component macros (buttons, cards, tables, modals, forms)
- JavaScript behaviors (Alpine.js based)
- Flask integration (app factory, blueprints, middleware)
- Databricks utilities (connection, audit logging, permissions)

Usage:
    from jhg_patterns.ds import DesignSystem, Theme, create_app

    # Quick start with defaults
    app = create_app("my-app")

    # Or customize
    theme = Theme.from_yaml("theme.yaml")
    ds = DesignSystem(theme=theme)
    app = create_app("my-app", design_system=ds)
"""

from jhg_patterns.ds.theme import Theme, ColorPalette
from jhg_patterns.ds.system import DesignSystem
from jhg_patterns.ds.app import create_app, AppConfig

__all__ = [
    "Theme",
    "ColorPalette",
    "DesignSystem",
    "create_app",
    "AppConfig",
]
__version__ = "0.1.0"
