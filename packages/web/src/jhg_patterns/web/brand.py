"""
JHG Brand Design System - Colors, Typography, Components.

This module provides the standardised JHG color palette and design tokens
that can be used across all JHG web applications.

Colors are provided as:
- Python dictionaries for programmatic access
- CSS variable definitions for stylesheets
- Tailwind config for utility class generation
- JavaScript constants for charts (Plotly, Chart.js, etc.)
"""

from typing import Dict, Any

# =============================================================================
# PRIMARY BRAND COLORS
# =============================================================================

BRAND_COLORS = {
    "red": {
        "DEFAULT": "#E63946",
        "dark": "#C5303C",
        "light": "#F5A3A9",
        "bg": "#FEF2F2",
    },
    "cyan": {
        "DEFAULT": "#5BC0DE",
        "dark": "#3AA8C7",
        "light": "#A8DFF0",
        "bg": "#ECFEFF",
    },
    "purple": {
        "DEFAULT": "#8B5CF6",
        "dark": "#7C3AED",
        "light": "#C4B5FD",
        "bg": "#F5F3FF",
    },
}

# =============================================================================
# SEMANTIC COLORS
# =============================================================================

SEMANTIC_COLORS = {
    "success": {
        "DEFAULT": "#10B981",
        "dark": "#059669",
        "light": "#6EE7B7",
        "bg": "#ECFDF5",
    },
    "warning": {
        "DEFAULT": "#F59E0B",
        "dark": "#D97706",
        "light": "#FCD34D",
        "bg": "#FFFBEB",
    },
    "error": {
        "DEFAULT": "#EF4444",
        "dark": "#DC2626",
        "light": "#FCA5A5",
        "bg": "#FEF2F2",
    },
    "info": {
        "DEFAULT": "#5BC0DE",  # Uses JH Cyan
        "dark": "#3AA8C7",
        "light": "#A8DFF0",
        "bg": "#ECFEFF",
    },
}

# =============================================================================
# GRAY SCALE
# =============================================================================

GRAY_SCALE = {
    "900": "#111827",
    "800": "#1F2937",
    "700": "#374151",
    "600": "#4B5563",
    "500": "#6B7280",
    "400": "#9CA3AF",
    "300": "#D1D5DB",
    "200": "#E5E7EB",
    "100": "#F3F4F6",
    "50": "#F9FAFB",
}

# =============================================================================
# CHART COLORS (for Plotly, Chart.js, etc.)
# =============================================================================

CHART_COLORS = {
    "primary": ["#E63946", "#5BC0DE", "#8B5CF6"],  # Red, Cyan, Purple
    "status": {
        "met": "#5BC0DE",  # Cyan
        "not_met": "#E63946",  # Red
        "escalated": "#F59E0B",  # Warning
    },
    "series": {
        "series1": "#6B7280",  # Gray 500
        "series2": "#5BC0DE",  # Cyan
        "series3": "#8B5CF6",  # Purple
    },
    "progress_thresholds": {
        "high": "#10B981",  # >= 80%
        "medium": "#F59E0B",  # >= 50%
        "low": "#E63946",  # < 50%
    },
}

# =============================================================================
# UI DEFAULTS
# =============================================================================

UI_COLORS = {
    "nav_bg": GRAY_SCALE["700"],
    "nav_text": "#FFFFFF",
    "nav_hover": BRAND_COLORS["cyan"]["DEFAULT"],
    "footer_bg": GRAY_SCALE["700"],
    "footer_text": GRAY_SCALE["300"],
    "page_bg": GRAY_SCALE["100"],
    "card_bg": "#FFFFFF",
    "card_border": GRAY_SCALE["200"],
    "text_primary": GRAY_SCALE["900"],
    "text_secondary": GRAY_SCALE["600"],
    "text_muted": GRAY_SCALE["500"],
}

# =============================================================================
# TYPOGRAPHY
# =============================================================================

TYPOGRAPHY = {
    "font_family": {
        "sans": ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        "mono": ["JetBrains Mono", "Consolas", "monospace"],
    },
    "google_fonts_url": (
        "https://fonts.googleapis.com/css2?"
        "family=Inter:wght@400;500;600;700&"
        "family=JetBrains+Mono:wght@400;500&display=swap"
    ),
}

# =============================================================================
# DESIGN TOKENS
# =============================================================================

DESIGN_TOKENS = {
    "radius": {
        "sm": "0.25rem",
        "DEFAULT": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
        "full": "9999px",
    },
    "shadow": {
        "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "DEFAULT": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        "md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_tailwind_config() -> Dict[str, Any]:
    """
    Get Tailwind CSS configuration object for extending the default theme.

    Usage in HTML:
        <script>
            tailwind.config = {{ get_tailwind_config() | tojson }};
        </script>

    Returns:
        Dict suitable for tailwind.config
    """
    return {
        "theme": {
            "extend": {
                "colors": {
                    "jh-red": BRAND_COLORS["red"],
                    "jh-cyan": BRAND_COLORS["cyan"],
                    "jh-purple": BRAND_COLORS["purple"],
                },
                "fontFamily": {
                    "sans": TYPOGRAPHY["font_family"]["sans"],
                    "mono": TYPOGRAPHY["font_family"]["mono"],
                },
            }
        }
    }


def get_css_variables() -> str:
    """
    Generate CSS custom properties (variables) for the brand colors.

    Usage:
        <style>
            :root {
                {{ get_css_variables() }}
            }
        </style>

    Returns:
        CSS variable declarations as a string
    """
    lines = []

    # Brand colors
    for name, shades in BRAND_COLORS.items():
        prefix = f"--jh-{name}"
        lines.append(f"{prefix}: {shades['DEFAULT']};")
        lines.append(f"{prefix}-dark: {shades['dark']};")
        lines.append(f"{prefix}-light: {shades['light']};")
        lines.append(f"{prefix}-bg: {shades['bg']};")

    lines.append("")

    # Gray scale
    for shade, value in GRAY_SCALE.items():
        lines.append(f"--gray-{shade}: {value};")

    lines.append("")

    # Semantic colors
    for name, shades in SEMANTIC_COLORS.items():
        lines.append(f"--{name}: {shades['DEFAULT']};")
        lines.append(f"--{name}-dark: {shades['dark']};")
        lines.append(f"--{name}-light: {shades['light']};")
        lines.append(f"--{name}-bg: {shades['bg']};")

    return "\n".join(lines)


def get_gradient_bar_css() -> str:
    """
    Get CSS for the JHG signature gradient bar.

    The gradient is: Red (60%) | Cyan (20%) | Purple (20%)

    Returns:
        CSS background property value
    """
    return (
        "linear-gradient(90deg, "
        f"{BRAND_COLORS['red']['DEFAULT']} 0%, {BRAND_COLORS['red']['DEFAULT']} 60%, "
        f"{BRAND_COLORS['cyan']['DEFAULT']} 60%, {BRAND_COLORS['cyan']['DEFAULT']} 80%, "
        f"{BRAND_COLORS['purple']['DEFAULT']} 80%, {BRAND_COLORS['purple']['DEFAULT']} 100%)"
    )


def get_progress_color(percentage: float) -> str:
    """
    Get appropriate color for a progress percentage.

    Args:
        percentage: Value from 0-100

    Returns:
        Hex color code
    """
    if percentage >= 80:
        return CHART_COLORS["progress_thresholds"]["high"]
    if percentage >= 50:
        return CHART_COLORS["progress_thresholds"]["medium"]
    return CHART_COLORS["progress_thresholds"]["low"]


def get_chart_js_config() -> Dict[str, Any]:
    """
    Get JavaScript object for chart libraries (Plotly, Chart.js).

    Returns:
        Dict with color constants for charts
    """
    return {
        "colors": {
            "red": BRAND_COLORS["red"]["DEFAULT"],
            "redDark": BRAND_COLORS["red"]["dark"],
            "cyan": BRAND_COLORS["cyan"]["DEFAULT"],
            "cyanDark": BRAND_COLORS["cyan"]["dark"],
            "purple": BRAND_COLORS["purple"]["DEFAULT"],
            "purpleDark": BRAND_COLORS["purple"]["dark"],
        },
        "gray": GRAY_SCALE,
        "semantic": {
            "success": SEMANTIC_COLORS["success"]["DEFAULT"],
            "warning": SEMANTIC_COLORS["warning"]["DEFAULT"],
            "error": SEMANTIC_COLORS["error"]["DEFAULT"],
        },
        "charts": CHART_COLORS,
    }
