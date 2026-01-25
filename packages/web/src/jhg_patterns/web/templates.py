"""
Jinja2 template helpers and Flask integration for JHG web styling.

Provides:
- Template context processors for Flask
- Asset copying utilities
- Component rendering helpers
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from jhg_patterns.web.brand import (
    BRAND_COLORS,
    CHART_COLORS,
    SEMANTIC_COLORS,
    GRAY_SCALE,
    TYPOGRAPHY,
    get_tailwind_config,
    get_css_variables,
    get_gradient_bar_css,
    get_chart_js_config,
)


def get_flask_context_processor():
    """
    Get a context processor function for Flask that injects brand variables.

    Usage in Flask:
        from jhg_patterns.web.templates import get_flask_context_processor

        app = Flask(__name__)

        @app.context_processor
        def inject_brand():
            return get_flask_context_processor()()

    Returns:
        Function that returns dict of template variables
    """

    def context_processor():
        return {
            "jhg_brand": BRAND_COLORS,
            "jhg_semantic": SEMANTIC_COLORS,
            "jhg_gray": GRAY_SCALE,
            "jhg_tailwind_config": get_tailwind_config(),
            "jhg_css_variables": get_css_variables(),
            "jhg_gradient_bar": get_gradient_bar_css(),
            "jhg_chart_config": get_chart_js_config(),
            "jhg_fonts_url": TYPOGRAPHY["google_fonts_url"],
        }

    return context_processor


def init_flask_app(app):
    """
    Initialize a Flask app with JHG brand context processor.

    Usage:
        from flask import Flask
        from jhg_patterns.web.templates import init_flask_app

        app = Flask(__name__)
        init_flask_app(app)

    Args:
        app: Flask application instance
    """
    app.context_processor(get_flask_context_processor())


def get_static_assets_dir() -> Path:
    """
    Get the path to the static assets directory in this package.

    Returns:
        Path to the assets directory
    """
    return Path(__file__).parent / "assets"


def copy_static_assets(destination: str, overwrite: bool = False) -> Dict[str, str]:
    """
    Copy JHG brand static assets to a Flask app's static directory.

    Args:
        destination: Path to the Flask app's static directory
        overwrite: Whether to overwrite existing files

    Returns:
        Dict mapping asset names to destination paths

    Example:
        copy_static_assets('./static')
        # Creates:
        #   ./static/css/jhg-brand.css
        #   ./static/js/jhg-brand.js
    """
    assets_dir = get_static_assets_dir()
    dest_path = Path(destination)
    copied = {}

    # Create destination directories
    (dest_path / "css").mkdir(parents=True, exist_ok=True)
    (dest_path / "js").mkdir(parents=True, exist_ok=True)

    # Copy CSS
    css_src = assets_dir / "css" / "jhg-brand.css"
    css_dest = dest_path / "css" / "jhg-brand.css"
    if css_src.exists():
        if overwrite or not css_dest.exists():
            shutil.copy2(css_src, css_dest)
            copied["css"] = str(css_dest)

    # Copy JS
    js_src = assets_dir / "js" / "jhg-brand.js"
    js_dest = dest_path / "js" / "jhg-brand.js"
    if js_src.exists():
        if overwrite or not js_dest.exists():
            shutil.copy2(js_src, js_dest)
            copied["js"] = str(js_dest)

    return copied


# =============================================================================
# COMPONENT HELPERS
# =============================================================================


def badge_classes(variant: str = "default") -> str:
    """
    Get CSS classes for a badge component.

    Args:
        variant: Badge variant (met, not_met, escalated, current, archived, info)

    Returns:
        Space-separated CSS class string
    """
    base = "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"

    variants = {
        "met": "bg-emerald-100 text-emerald-800",
        "success": "bg-emerald-100 text-emerald-800",
        "not_met": "bg-red-100 text-red-800",
        "error": "bg-red-100 text-red-800",
        "escalated": "bg-orange-100 text-orange-800",
        "warning": "bg-orange-100 text-orange-800",
        "current": "bg-cyan-100 text-cyan-800",
        "info": "bg-cyan-100 text-cyan-800",
        "archived": "bg-gray-100 text-gray-800",
        "default": "bg-gray-100 text-gray-800",
        "purple": "bg-purple-100 text-purple-800",
    }

    variant_classes = variants.get(variant, variants["default"])
    return f"{base} {variant_classes}"


def button_classes(variant: str = "primary", size: str = "md") -> str:
    """
    Get CSS classes for a button component.

    Args:
        variant: Button variant (primary, secondary, outline, success, danger)
        size: Button size (sm, md, lg)

    Returns:
        Space-separated CSS class string
    """
    base = "inline-flex items-center justify-center font-medium rounded-lg transition-colors"

    sizes = {
        "sm": "px-3 py-1.5 text-sm",
        "md": "px-4 py-2 text-base",
        "lg": "px-6 py-3 text-lg",
    }

    variants = {
        "primary": "bg-jh-red text-white hover:bg-jh-red-dark",
        "secondary": "bg-gray-600 text-white hover:bg-gray-700",
        "outline": "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50",
        "success": "bg-emerald-500 text-white hover:bg-emerald-600",
        "danger": "bg-red-500 text-white hover:bg-red-600",
        "ghost": "text-gray-600 hover:bg-gray-100",
    }

    size_classes = sizes.get(size, sizes["md"])
    variant_classes = variants.get(variant, variants["primary"])
    return f"{base} {size_classes} {variant_classes}"


def card_classes(hover: bool = False) -> str:
    """
    Get CSS classes for a card component.

    Args:
        hover: Whether to include hover effect

    Returns:
        Space-separated CSS class string
    """
    base = "bg-white border border-gray-200 rounded-xl shadow-sm"
    if hover:
        return f"{base} hover:shadow-md transition-shadow"
    return base


def alert_classes(variant: str = "info") -> str:
    """
    Get CSS classes for an alert component.

    Args:
        variant: Alert variant (success, warning, error, info)

    Returns:
        Space-separated CSS class string
    """
    base = "p-4 rounded-lg border"

    variants = {
        "success": "bg-emerald-50 text-emerald-800 border-emerald-200",
        "warning": "bg-amber-50 text-amber-800 border-amber-200",
        "error": "bg-red-50 text-red-800 border-red-200",
        "info": "bg-cyan-50 text-cyan-800 border-cyan-200",
    }

    variant_classes = variants.get(variant, variants["info"])
    return f"{base} {variant_classes}"
