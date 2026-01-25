"""
JHG Web Patterns - Standardised styling for JHG web applications.

Includes:
- Brand colors and CSS variables
- Tailwind CSS configuration
- Jinja2 template helpers
- Component classes (buttons, badges, cards, etc.)

Usage:
    from jhg_patterns.web import BRAND_COLORS, get_tailwind_config
    from jhg_patterns.web.templates import copy_base_templates
"""

from jhg_patterns.web.brand import (
    BRAND_COLORS,
    CHART_COLORS,
    SEMANTIC_COLORS,
    GRAY_SCALE,
    get_tailwind_config,
    get_css_variables,
)

__all__ = [
    "BRAND_COLORS",
    "CHART_COLORS",
    "SEMANTIC_COLORS",
    "GRAY_SCALE",
    "get_tailwind_config",
    "get_css_variables",
]
__version__ = "0.1.0"
