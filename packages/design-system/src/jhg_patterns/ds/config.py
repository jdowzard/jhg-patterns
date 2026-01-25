"""
Configuration management for JHG applications.

Provides Pydantic-based settings management with environment variable
support and YAML configuration file loading.

Usage:
    from jhg_patterns.ds.config import AppSettings, load_config

    # Load from environment variables
    settings = AppSettings()

    # Load from YAML file
    settings = load_config("config.yaml", AppSettings)

    # Or define custom settings class
    from pydantic import BaseModel, Field

    class CustomSettings(BaseModel):
        app_name: str
        debug: bool = False
        # etc.

    settings = load_config("config.yaml", CustomSettings)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AppSettings(BaseModel):
    """
    Base application settings with environment variable support.

    Environment variables can override any field using the pattern:
    {prefix}_{FIELD_NAME}

    For example, with default prefix "", the field "databricks_host"
    can be overridden by the environment variable "DATABRICKS_HOST".

    Example:
        export DATABRICKS_HOST=https://...
        export DEBUG=true
        settings = AppSettings()  # Loads from environment
    """

    app_name: str = Field(default="app", description="Application name")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Databricks settings
    databricks_host: str = Field(
        default="",
        description="Databricks workspace URL (https://dbc-*.cloud.databricks.com)",
    )
    databricks_token: str = Field(default="", description="Databricks personal access token")
    databricks_sql_path: str = Field(
        default="",
        description="Databricks SQL warehouse HTTP path",
    )
    databricks_catalog: str = Field(
        default="main", description="Unity Catalog name"
    )
    databricks_schema: str = Field(default="default", description="Schema name")

    # API settings
    api_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        ge=1,
        le=300,
    )
    api_retries: int = Field(
        default=3,
        description="Number of API retry attempts",
        ge=0,
        le=10,
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(
        default=600,
        description="Default cache time-to-live in seconds",
        ge=0,
    )

    model_config = ConfigDict(
        env_prefix="",
        case_sensitive=False,
        validate_default=True,
        extra="allow",  # Allow additional fields
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a standard logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got {v}"
            )
        return v_upper

    @field_validator("databricks_host")
    @classmethod
    def validate_databricks_host(cls, v: str) -> str:
        """Validate Databricks host format if provided."""
        if v and not v.startswith("https://"):
            raise ValueError("databricks_host must start with 'https://'")
        return v

    @classmethod
    def from_env(cls) -> "AppSettings":
        """
        Create settings from environment variables.

        Returns:
            AppSettings instance with values loaded from environment

        Example:
            settings = AppSettings.from_env()
        """
        return cls()

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppSettings":
        """
        Load settings from YAML file.

        Environment variables still override YAML values.

        Args:
            path: Path to YAML configuration file

        Returns:
            AppSettings instance with values from YAML and environment

        Example:
            settings = AppSettings.from_yaml("config.yaml")
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        logger.info(f"Loaded configuration from {path}")
        return cls(**data)


def load_config(
    path: Optional[str | Path] = None,
    settings_class: Type[T] = AppSettings,  # type: ignore
) -> T:
    """
    Load configuration from YAML file or environment.

    If a path is provided, loads from YAML file with environment
    variable overrides. If no path is provided, loads from environment
    variables only.

    Args:
        path: Path to YAML configuration file (optional)
        settings_class: Settings class to use (default: AppSettings)

    Returns:
        Instance of settings_class with loaded configuration

    Raises:
        FileNotFoundError: If YAML file path is provided but doesn't exist
        ValidationError: If configuration values don't pass validation

    Example:
        # Load from environment only
        settings = load_config()

        # Load from YAML with environment overrides
        settings = load_config("config.yaml")

        # Use custom settings class
        settings = load_config("config.yaml", CustomSettings)
    """
    if path:
        logger.info(f"Loading configuration from {path}")
        return settings_class.from_yaml(path)
    else:
        logger.info("Loading configuration from environment variables")
        return settings_class.from_env()


class DatabaseSettings(BaseModel):
    """Settings for database connections."""

    host: str = Field(description="Database host or connection URL")
    port: int = Field(default=5432, description="Database port")
    username: str = Field(description="Database username")
    password: str = Field(default="", description="Database password")
    database: str = Field(description="Database name")
    ssl: bool = Field(default=True, description="Use SSL for connection")
    timeout: int = Field(
        default=30,
        description="Connection timeout in seconds",
        ge=1,
    )

    model_config = ConfigDict(
        env_prefix="DB_",
        case_sensitive=False,
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v.strip():
            raise ValueError("host cannot be empty")
        return v


class AuthSettings(BaseModel):
    """Settings for authentication."""

    enabled: bool = Field(default=True, description="Enable authentication")
    secret_key: str = Field(
        description="Secret key for session management",
        min_length=32,
    )
    token_expiry: int = Field(
        default=3600,
        description="Token expiry time in seconds",
        ge=60,
    )
    refresh_token_expiry: int = Field(
        default=86400,
        description="Refresh token expiry time in seconds",
        ge=3600,
    )
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="List of allowed email domains for authentication",
    )

    model_config = ConfigDict(
        env_prefix="AUTH_",
        case_sensitive=False,
    )


class CORSSettings(BaseModel):
    """Settings for CORS (Cross-Origin Resource Sharing)."""

    enabled: bool = Field(default=False, description="Enable CORS")
    origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed origins (list or ['*'] for all)",
    )
    methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"],
        description="Allowed HTTP methods",
    )
    allow_credentials: bool = Field(
        default=False,
        description="Allow credentials in CORS requests",
    )
    max_age: int = Field(
        default=3600,
        description="Cache time for CORS preflight in seconds",
        ge=0,
    )

    model_config = ConfigDict(
        env_prefix="CORS_",
        case_sensitive=False,
    )

    @field_validator("origins")
    @classmethod
    def validate_origins(cls, v: list[str]) -> list[str]:
        """Validate origins list is not empty."""
        if not v:
            raise ValueError("origins list cannot be empty")
        return v
