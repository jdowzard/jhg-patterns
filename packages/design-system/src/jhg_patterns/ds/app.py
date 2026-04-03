"""
Flask application factory with JHG Design System integration.

Provides a standardized way to create Flask applications with:
- Theme and design system
- TTL caching
- Health checks
- Error handlers
- Security middleware (CSRF, rate limiting, headers)
- Databricks integration
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from jhg_patterns.ds.theme import Theme
from jhg_patterns.ds.system import DesignSystem

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""

    enabled: bool = True
    default_ttl: int = 600
    ttls: Dict[str, int] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Security configuration."""

    csrf_enabled: bool = True
    rate_limiting_enabled: bool = True
    rate_limit_default: str = "200 per day, 50 per hour"
    cors_enabled: bool = True
    cors_origins: str = "*"


@dataclass
class DatabricksConfig:
    """Databricks connection configuration."""

    host: Optional[str] = None
    token: Optional[str] = None
    sql_path: Optional[str] = None
    catalog: str = "main"
    schema: str = "default"

    def __post_init__(self):
        # Load from environment if not provided
        self.host = self.host or os.getenv("DATABRICKS_HOST")
        self.token = self.token or os.getenv("DATABRICKS_TOKEN")
        self.sql_path = self.sql_path or os.getenv("DATABRICKS_SQL_PATH")
        self.catalog = self.catalog or os.getenv("DATABRICKS_CATALOG", "main")
        self.schema = self.schema or os.getenv("DATABRICKS_SCHEMA", "default")


@dataclass
class AppConfig:
    """
    Application configuration for create_app().

    Can be created programmatically or loaded from YAML.
    """

    name: str
    theme: Optional[Theme] = None
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    databricks: DatabricksConfig = field(default_factory=DatabricksConfig)

    # Feature flags
    enable_health_check: bool = True
    enable_cache_api: bool = True
    enable_error_pages: bool = True

    # Flask config
    secret_key: Optional[str] = None
    debug: bool = False

    def __post_init__(self):
        if self.theme is None:
            self.theme = Theme.jhg()
        if self.secret_key is None:
            self.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """Load configuration from YAML file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)

        # Load theme from separate file or inline
        theme = None
        if "theme" in data:
            if isinstance(data["theme"], str):
                # Path to theme file
                theme_path = Path(path).parent / data["theme"]
                theme = Theme.from_yaml(theme_path)
            else:
                # Inline theme
                theme = Theme.from_dict(data["theme"])

        # Parse sub-configs
        cache = CacheConfig(**data.get("cache", {}))
        security = SecurityConfig(**data.get("security", {}))
        databricks = DatabricksConfig(**data.get("databricks", {}))

        return cls(
            name=data.get("name", "app"),
            theme=theme,
            cache=cache,
            security=security,
            databricks=databricks,
            enable_health_check=data.get("enable_health_check", True),
            enable_cache_api=data.get("enable_cache_api", True),
            enable_error_pages=data.get("enable_error_pages", True),
            secret_key=data.get("secret_key"),
            debug=data.get("debug", False),
        )


def create_app(
    config: AppConfig | str | None = None,
    design_system: Optional[DesignSystem] = None,
) -> "Flask":
    """
    Create a Flask application with JHG Design System.

    Args:
        config: AppConfig, path to YAML config, app name string, or None for defaults
        design_system: Optional pre-configured DesignSystem

    Returns:
        Configured Flask application

    Example:
        # Quick start with defaults
        app = create_app("my-app")

        # From YAML config
        app = create_app("config/app.yaml")

        # Programmatic
        app = create_app(AppConfig(
            name="my-app",
            theme=Theme.jhg(),
            cache=CacheConfig(default_ttl=1800),
        ))
    """
    from flask import Flask

    # Parse config
    if config is None:
        config = AppConfig(name="app")
    elif isinstance(config, str):
        if config.endswith((".yaml", ".yml")):
            config = AppConfig.from_yaml(config)
        else:
            config = AppConfig(name=config)

    # Create Flask app
    app = Flask(config.name)
    app.config["SECRET_KEY"] = config.secret_key
    app.config["DEBUG"] = config.debug

    # Store config on app
    app.config["APP_CONFIG"] = config

    # Initialize design system
    ds = design_system or DesignSystem(theme=config.theme)
    ds.init_app(app)

    # Initialize cache
    if config.cache.enabled:
        _init_cache(app, config.cache)

    # Initialize security
    _init_security(app, config.security)

    # Register blueprints
    if config.enable_health_check:
        from jhg_patterns.ds.blueprints.health import health_bp
        app.register_blueprint(health_bp)

    if config.enable_cache_api:
        from jhg_patterns.ds.blueprints.cache import cache_bp
        app.register_blueprint(cache_bp, url_prefix="/api")

    # Register error handlers
    if config.enable_error_pages:
        _register_error_handlers(app)

    # Add security headers
    _add_security_headers(app)

    logger.info(f"Created app '{config.name}' with theme '{config.theme.name}'")

    return app


def _init_cache(app, config: CacheConfig):
    """Initialize TTL cache."""
    try:
        from jhg_patterns.flask import TTLCache
    except ImportError:
        logger.warning("jhg-patterns-flask not installed, cache disabled")
        return

    cache = TTLCache(default_ttls=config.ttls)
    cache._default_ttl = config.default_ttl
    cache._enabled = config.enabled

    app.extensions = getattr(app, "extensions", {})
    app.extensions["cache"] = cache


def _init_security(app, config: SecurityConfig):
    """Initialize security features."""
    # CSRF
    if config.csrf_enabled:
        try:
            from flask_wtf.csrf import CSRFProtect
            csrf = CSRFProtect(app)
            app.csrf = csrf
        except ImportError:
            logger.warning("flask-wtf not installed, CSRF disabled")

    # Rate limiting
    if config.rate_limiting_enabled:
        try:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address

            limiter = Limiter(
                key_func=get_remote_address,
                app=app,
                default_limits=[config.rate_limit_default],
                storage_uri="memory://",
            )
            app.limiter = limiter

            # Exempt health check
            @limiter.request_filter
            def health_check_filter():
                from flask import request
                return request.path == "/health"

        except ImportError:
            logger.warning("flask-limiter not installed, rate limiting disabled")

    # CORS
    if config.cors_enabled:
        try:
            from flask_cors import CORS
            CORS(app, origins=config.cors_origins)
        except ImportError:
            logger.warning("flask-cors not installed, CORS disabled")


def _register_error_handlers(app):
    """Register error handlers with themed templates."""
    from flask import render_template, request, jsonify

    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Bad request"}), 400
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Service unavailable"}), 503
        return render_template("errors/503.html"), 503


def _add_security_headers(app):
    """Add security headers to all responses."""
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
