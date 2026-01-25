"""
Design System class - main entry point for theme and component integration.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from flask import Blueprint, Response, send_from_directory
from markupsafe import Markup

from jhg_patterns.ds.theme import Theme

# Blueprint for design system routes (CSS endpoint, assets)
ds_bp = Blueprint(
    "ds",
    __name__,
    static_folder=str(Path(__file__).parent / "assets"),
    static_url_path="/assets",
)


class DesignSystem:
    """
    JHG Design System - manages theme and provides Flask integration.

    Usage:
        ds = DesignSystem()  # JHG default
        ds = DesignSystem(theme=Theme.from_yaml("theme.yaml"))

        # Flask integration
        ds.init_app(app)
    """

    def __init__(self, theme: Optional[Theme] = None):
        """
        Initialize design system.

        Args:
            theme: Custom theme, or None for JHG default
        """
        self.theme = theme or Theme.jhg()
        self._app = None

    def init_app(self, app):
        """
        Initialize Flask application with design system.

        Registers:
        - Context processor for theme variables
        - Template loader for component macros
        - Static file handling for CSS/JS assets
        - CSS endpoint at /ds/css

        Args:
            app: Flask application
        """
        self._app = app

        # Store reference on app
        app.extensions = getattr(app, "extensions", {})
        app.extensions["design_system"] = self

        # Register context processor
        app.context_processor(self._context_processor)

        # Add template folder for macros
        templates_path = Path(__file__).parent / "templates"
        if templates_path.exists():
            # Add to Jinja loader
            from jinja2 import ChoiceLoader, FileSystemLoader

            if app.jinja_loader is None:
                app.jinja_loader = FileSystemLoader(str(templates_path))
            else:
                app.jinja_loader = ChoiceLoader([
                    app.jinja_loader,
                    FileSystemLoader(str(templates_path)),
                ])

        # Register CSS endpoint
        @ds_bp.route("/css")
        def css():
            return Response(self.generate_css(), mimetype="text/css")

        # Register favicon endpoint at root
        @app.route("/favicon.ico")
        def favicon():
            assets_path = Path(__file__).parent / "assets" / "images"
            return send_from_directory(str(assets_path), "favicon.ico", mimetype="image/x-icon")

        app.register_blueprint(ds_bp, url_prefix="/ds")

    def _context_processor(self) -> Dict[str, Any]:
        """Inject theme variables into all templates."""
        return {
            "theme": self.theme,
            "ds": self,
            "ds_css_variables": self.theme.get_css_variables(),
            "ds_tailwind_config": self.theme.get_tailwind_config(),
            "ds_gradient_css": self.theme.get_gradient_css(),
            "ds_fonts_url": self.theme.typography.google_fonts_url,
            "ds_chart_colors": self.theme.get_chart_colors(),
        }

    def generate_css(self) -> str:
        """
        Generate complete CSS for the design system.

        Returns:
            CSS string with variables, utilities, and component styles
        """
        parts = []

        # CSS Variables
        parts.append(":root {")
        parts.append(self.theme.get_css_variables())
        parts.append("}")
        parts.append("")

        # Gradient bar
        parts.append(".ds-gradient-bar {")
        parts.append(f"    background: {self.theme.get_gradient_css()};")
        parts.append("}")
        parts.append("")

        # Utility classes
        parts.append(self._generate_utility_classes())

        # Component styles
        parts.append(self._generate_component_styles())

        return "\n".join(parts)

    def _generate_utility_classes(self) -> str:
        """Generate utility classes for colors."""
        lines = ["/* Utility Classes */", ""]

        # Text colors
        for name in ["primary", "secondary", "tertiary", "success", "warning", "error", "info"]:
            lines.append(f".text-{name} {{ color: var(--{name}); }}")
            lines.append(f".text-{name}-dark {{ color: var(--{name}-dark); }}")

        lines.append("")

        # Background colors
        for name in ["primary", "secondary", "tertiary", "success", "warning", "error", "info"]:
            lines.append(f".bg-{name} {{ background-color: var(--{name}); }}")
            lines.append(f".bg-{name}-light {{ background-color: var(--{name}-bg); }}")

        lines.append("")

        # Border colors
        for name in ["primary", "secondary", "tertiary"]:
            lines.append(f".border-{name} {{ border-color: var(--{name}); }}")

        return "\n".join(lines)

    def _generate_component_styles(self) -> str:
        """Generate component CSS."""
        return """
/* ========================================
   BADGES
   ======================================== */

.ds-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-full);
    font-size: 0.875rem;
    font-weight: 500;
}

.ds-badge-success {
    background-color: var(--success-bg);
    color: var(--success-dark);
}

.ds-badge-error {
    background-color: var(--error-bg);
    color: var(--error-dark);
}

.ds-badge-warning {
    background-color: var(--warning-bg);
    color: var(--warning-dark);
}

.ds-badge-info {
    background-color: var(--info-bg);
    color: var(--info-dark);
}

.ds-badge-neutral {
    background-color: var(--gray-100);
    color: var(--gray-700);
}

/* ========================================
   BUTTONS
   ======================================== */

.ds-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    font-weight: 500;
    font-size: 0.875rem;
    line-height: 1.25rem;
    transition: all 0.15s ease;
    cursor: pointer;
    border: none;
}

.ds-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.ds-btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
}

.ds-btn-lg {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
}

.ds-btn-primary {
    background-color: var(--primary);
    color: white;
}

.ds-btn-primary:hover:not(:disabled) {
    background-color: var(--primary-dark);
}

.ds-btn-secondary {
    background-color: var(--gray-600);
    color: white;
}

.ds-btn-secondary:hover:not(:disabled) {
    background-color: var(--gray-700);
}

.ds-btn-outline {
    background-color: white;
    color: var(--gray-700);
    border: 1px solid var(--gray-300);
}

.ds-btn-outline:hover:not(:disabled) {
    background-color: var(--gray-50);
}

.ds-btn-danger {
    background-color: var(--error);
    color: white;
}

.ds-btn-danger:hover:not(:disabled) {
    background-color: var(--error-dark);
}

.ds-btn-success {
    background-color: var(--success);
    color: white;
}

.ds-btn-success:hover:not(:disabled) {
    background-color: var(--success-dark);
}

.ds-btn-ghost {
    background-color: transparent;
    color: var(--gray-600);
}

.ds-btn-ghost:hover:not(:disabled) {
    background-color: var(--gray-100);
}

/* ========================================
   CARDS
   ======================================== */

.ds-card {
    background-color: white;
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
}

.ds-card-hover:hover {
    box-shadow: var(--shadow-md);
    transition: box-shadow 0.15s ease;
}

.ds-card-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--gray-200);
}

.ds-card-body {
    padding: 1.5rem;
}

.ds-card-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--gray-200);
    background-color: var(--gray-50);
}

/* ========================================
   SUMMARY CARDS
   ======================================== */

.ds-summary-card {
    background-color: white;
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    box-shadow: var(--shadow);
}

.ds-summary-card-label {
    font-size: 0.875rem;
    color: var(--gray-500);
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

.ds-summary-card-value {
    font-size: 1.875rem;
    font-weight: 700;
    margin-top: 0.25rem;
}

/* ========================================
   ALERTS
   ======================================== */

.ds-alert {
    padding: 1rem;
    border-radius: var(--radius);
    margin-bottom: 1rem;
    border: 1px solid;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}

.ds-alert-success {
    background-color: var(--success-bg);
    color: var(--success-dark);
    border-color: var(--success-light);
}

.ds-alert-warning {
    background-color: var(--warning-bg);
    color: var(--warning-dark);
    border-color: var(--warning-light);
}

.ds-alert-error {
    background-color: var(--error-bg);
    color: var(--error-dark);
    border-color: var(--error-light);
}

.ds-alert-info {
    background-color: var(--info-bg);
    color: var(--info-dark);
    border-color: var(--info-light);
}

/* ========================================
   NAVIGATION
   ======================================== */

.ds-nav {
    background-color: var(--gray-700);
    color: white;
    box-shadow: var(--shadow-md);
}

.ds-nav-container {
    max-width: 80rem;
    margin: 0 auto;
    padding: 0 1rem;
}

.ds-nav-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 4rem;
}

.ds-nav-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.25rem;
    font-weight: 700;
    color: white;
    text-decoration: none;
}

.ds-nav-brand:hover {
    color: white;
}

.ds-nav-brand img {
    height: 2.5rem;
    width: 2.5rem;
}

.ds-nav-links {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.ds-nav-link {
    color: white;
    text-decoration: none;
    transition: color 0.15s ease;
}

.ds-nav-link:hover {
    color: var(--secondary);
}

.ds-nav-link.active {
    color: var(--secondary);
}

/* ========================================
   FOOTER
   ======================================== */

.ds-footer {
    background-color: var(--gray-700);
    color: var(--gray-300);
    padding: 1.5rem 0;
    margin-top: auto;
}

.ds-footer-container {
    max-width: 80rem;
    margin: 0 auto;
    padding: 0 1rem;
    text-align: center;
    font-size: 0.875rem;
}

.ds-footer-muted {
    color: var(--gray-400);
    margin-top: 0.25rem;
}

/* ========================================
   PAGE LAYOUT
   ======================================== */

.ds-page {
    background-color: var(--gray-100);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

.ds-page-content {
    max-width: 80rem;
    margin: 0 auto;
    padding: 2rem 1rem;
    flex-grow: 1;
    width: 100%;
}

/* ========================================
   FORMS
   ======================================== */

.ds-form-group {
    margin-bottom: 1rem;
}

.ds-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--gray-700);
    margin-bottom: 0.25rem;
}

.ds-input {
    display: block;
    width: 100%;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    line-height: 1.25rem;
    color: var(--gray-900);
    background-color: white;
    border: 1px solid var(--gray-300);
    border-radius: var(--radius);
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.ds-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-bg);
}

.ds-input:disabled {
    background-color: var(--gray-100);
    cursor: not-allowed;
}

.ds-input-error {
    border-color: var(--error);
}

.ds-input-error:focus {
    box-shadow: 0 0 0 3px var(--error-bg);
}

.ds-helper-text {
    font-size: 0.75rem;
    color: var(--gray-500);
    margin-top: 0.25rem;
}

.ds-error-text {
    font-size: 0.75rem;
    color: var(--error);
    margin-top: 0.25rem;
}

.ds-select {
    display: block;
    width: 100%;
    padding: 0.5rem 2rem 0.5rem 0.75rem;
    font-size: 0.875rem;
    line-height: 1.25rem;
    color: var(--gray-900);
    background-color: white;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236B7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 0.5rem center;
    background-repeat: no-repeat;
    background-size: 1.5em 1.5em;
    border: 1px solid var(--gray-300);
    border-radius: var(--radius);
    appearance: none;
}

.ds-select:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-bg);
}

/* ========================================
   TABLES
   ======================================== */

.ds-table-container {
    overflow-x: auto;
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-lg);
}

.ds-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.ds-table th {
    background-color: var(--gray-50);
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 600;
    color: var(--gray-700);
    border-bottom: 1px solid var(--gray-200);
}

.ds-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--gray-200);
    color: var(--gray-900);
}

.ds-table tr:last-child td {
    border-bottom: none;
}

.ds-table tr:hover {
    background-color: var(--gray-50);
}

.ds-table-sortable th {
    cursor: pointer;
    user-select: none;
}

.ds-table-sortable th:hover {
    background-color: var(--gray-100);
}

/* ========================================
   MODALS
   ======================================== */

.ds-modal-backdrop {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 50;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.2s ease, visibility 0.2s ease;
}

.ds-modal-backdrop.active {
    opacity: 1;
    visibility: visible;
}

.ds-modal {
    background-color: white;
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);
    max-width: 32rem;
    width: 100%;
    margin: 1rem;
    transform: scale(0.95);
    transition: transform 0.2s ease;
}

.ds-modal-backdrop.active .ds-modal {
    transform: scale(1);
}

.ds-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--gray-200);
}

.ds-modal-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--gray-900);
}

.ds-modal-close {
    color: var(--gray-400);
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
}

.ds-modal-close:hover {
    color: var(--gray-600);
}

.ds-modal-body {
    padding: 1.5rem;
}

.ds-modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--gray-200);
    background-color: var(--gray-50);
}

/* ========================================
   PROGRESS BARS
   ======================================== */

.ds-progress {
    height: 0.75rem;
    background-color: var(--gray-200);
    border-radius: var(--radius-full);
    overflow: hidden;
}

.ds-progress-bar {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width 0.3s ease;
}

.ds-progress-primary { background-color: var(--primary); }
.ds-progress-secondary { background-color: var(--secondary); }
.ds-progress-tertiary { background-color: var(--tertiary); }
.ds-progress-success { background-color: var(--success); }
.ds-progress-warning { background-color: var(--warning); }
.ds-progress-error { background-color: var(--error); }

/* ========================================
   EMPTY STATE
   ======================================== */

.ds-empty-state {
    text-align: center;
    padding: 3rem 1.5rem;
}

.ds-empty-state-icon {
    width: 3rem;
    height: 3rem;
    margin: 0 auto 1rem;
    color: var(--gray-400);
}

.ds-empty-state-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--gray-900);
    margin-bottom: 0.5rem;
}

.ds-empty-state-description {
    color: var(--gray-500);
    margin-bottom: 1.5rem;
}

/* ========================================
   TOASTS
   ======================================== */

.ds-toast-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.ds-toast {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    background-color: white;
    min-width: 20rem;
    animation: ds-toast-in 0.2s ease;
}

@keyframes ds-toast-in {
    from {
        opacity: 0;
        transform: translateX(1rem);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.ds-toast-success {
    border-left: 4px solid var(--success);
}

.ds-toast-error {
    border-left: 4px solid var(--error);
}

.ds-toast-warning {
    border-left: 4px solid var(--warning);
}

.ds-toast-info {
    border-left: 4px solid var(--info);
}
"""

    def get_assets_path(self) -> Path:
        """Get path to static assets directory."""
        return Path(__file__).parent / "assets"

    def get_templates_path(self) -> Path:
        """Get path to templates directory."""
        return Path(__file__).parent / "templates"

    def render_navbar(
        self,
        title: str = "App",
        logo_url: Optional[str] = None,
        show_logo: bool = True,
        links: Optional[list] = None,
    ) -> Markup:
        """
        Render the navigation bar.

        Args:
            title: App title/name
            logo_url: Optional logo image URL (uses AIJH logo if not provided)
            show_logo: Whether to show the logo (default True)
            links: List of nav links [{"href": "/", "label": "Home", "active": True}]

        Returns:
            Safe HTML string
        """
        links = links or []

        logo_html = ""
        if show_logo:
            # Use provided logo or default AIJH logo
            src = logo_url or "/ds/assets/images/aijh-logo.png"
            logo_html = f'<img src="{src}" alt="{title}" class="h-8 w-auto">'

        links_html = ""
        for link in links:
            active_class = " active" if link.get("active") else ""
            links_html += f'<a href="{link["href"]}" class="ds-nav-link{active_class}">{link["label"]}</a>'

        gradient_bar = ""
        if self.theme.navbar.gradient_bar:
            gradient_bar = f'<div class="ds-gradient-bar h-1"></div>'

        html = f"""
        <nav class="ds-nav">
            {gradient_bar}
            <div class="ds-nav-container">
                <div class="ds-nav-content">
                    <a href="/" class="ds-nav-brand">
                        {logo_html}
                        <span>{title}</span>
                    </a>
                    <div class="ds-nav-links">
                        {links_html}
                    </div>
                </div>
            </div>
        </nav>
        """
        return Markup(html)

    def render_footer(
        self,
        text: str = "John Holland Group",
        year: Optional[int] = None,
    ) -> Markup:
        """
        Render the footer.

        Args:
            text: Footer text (company name)
            year: Copyright year (defaults to current year)

        Returns:
            Safe HTML string
        """
        from datetime import datetime
        year = year or datetime.now().year

        html = f"""
        <footer class="ds-footer">
            <div class="ds-footer-container">
                <p>&copy; {year} {text}. All rights reserved.</p>
                <p class="ds-footer-muted">Powered by JHG Design System</p>
            </div>
        </footer>
        """
        return Markup(html)
