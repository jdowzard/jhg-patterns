"""
Custom logging configuration for JHG patterns design system.

Provides color-coded formatted logging, structured JSON logging for production,
and Flask integration utilities.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from flask import Flask
except ImportError:
    Flask = None


# ANSI color codes for terminal output
ANSI_COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
}

# Level emojis for visual distinction
LEVEL_EMOJIS = {
    "DEBUG": "⚙",
    "INFO": "►",
    "WARNING": "⚠",
    "ERROR": "✗",
    "CRITICAL": "‼",
}

RESET_COLOR = "\033[0m"


class JHGFormatter(logging.Formatter):
    """
    Custom formatter with color-coded levels and optional emojis.

    Formats log records with:
    - Color-coded level names
    - Optional emoji indicators
    - Timestamps
    - Module names
    - Clear message content

    Examples:
        >>> formatter = JHGFormatter(use_colors=True, use_emojis=True)
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: bool = True,
        use_emojis: bool = False,
    ):
        """
        Initialize the formatter.

        Args:
            fmt: Format string for the log record. Defaults to a standard format.
            datefmt: Date format string. Defaults to "%Y-%m-%d %H:%M:%S".
            use_colors: Whether to use ANSI color codes. Defaults to True.
            use_emojis: Whether to include emoji indicators. Defaults to False.
        """
        if fmt is None:
            fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt)
        self.use_colors = use_colors
        self.use_emojis = use_emojis

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with colors and optional emojis.

        Args:
            record: The log record to format.

        Returns:
            Formatted log message string.
        """
        # Add emoji if enabled
        if self.use_emojis:
            emoji = LEVEL_EMOJIS.get(record.levelname, "")
            record.msg = f"{emoji} {record.msg}"

        # Format the record using parent formatter
        formatted = super().format(record)

        # Add color codes if enabled
        if self.use_colors:
            color = ANSI_COLORS.get(record.levelname, "")
            if color:
                formatted = f"{color}{formatted}{RESET_COLOR}"

        return formatted


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for production logging.

    Outputs structured logs in JSON format suitable for log aggregation
    systems like ELK, Splunk, or CloudWatch.

    The JSON output includes:
    - timestamp: ISO 8601 format
    - level: Log level name
    - logger: Logger name
    - message: Log message
    - module: Module name where log originated
    - function: Function name where log originated
    - line: Line number
    - extra fields: Additional context from LogRecord

    Examples:
        >>> formatter = JSONFormatter()
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        include_extra: bool = True,
    ):
        """
        Initialize the JSON formatter.

        Args:
            fmt: Unused, kept for compatibility.
            datefmt: Unused, kept for compatibility.
            include_extra: Whether to include extra fields from LogRecord. Defaults to True.
        """
        super().__init__(fmt, datefmt)
        self.include_extra = include_extra
        # Standard fields that should not be included in extras
        self._standard_fields = {
            "name",
            "msg",
            "args",
            "created",
            "msecs",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "exc_info",
            "exc_text",
            "stack_info",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "asctime",
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log message string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add stack trace if present
        if record.stack_info:
            log_data["stack_trace"] = record.stack_info

        # Add extra fields if enabled and present
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in self._standard_fields and not key.startswith("_"):
                    try:
                        # Ensure the value is JSON serializable
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        # If not serializable, convert to string
                        log_data[key] = str(value)

        return json.dumps(log_data, default=str)


def get_logger(
    name: str,
    level: str = "INFO",
    use_colors: bool = True,
    use_emojis: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Get a configured logger with JHG formatting.

    Creates or retrieves a logger with the specified configuration. Multiple calls
    with the same name return the same logger instance.

    Args:
        name: The name of the logger, typically __name__.
        level: Logging level as string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
                Defaults to "INFO".
        use_colors: Whether to use ANSI color codes in console output. Defaults to True.
        use_emojis: Whether to include emoji indicators. Defaults to False.
        log_file: Optional file path to write logs to. If None, logs only go to stderr.

    Returns:
        Configured logging.Logger instance.

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")

        >>> debug_logger = get_logger(__name__, level="DEBUG", use_emojis=True)
        >>> debug_logger.debug("Detailed debug information")

        >>> file_logger = get_logger(__name__, log_file="/var/log/app.log")
        >>> file_logger.error("An error occurred")
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured (check if handlers exist)
    if not logger.handlers:
        # Set the logger level
        logger.setLevel(level.upper())

        # Create formatter
        formatter = JHGFormatter(
            use_colors=use_colors,
            use_emojis=use_emojis,
        )

        # Console handler (stderr)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level.upper())
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional file handler
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level.upper())
            # Use JSON formatter for file output
            json_formatter = JSONFormatter()
            file_handler.setFormatter(json_formatter)
            logger.addHandler(file_handler)

    return logger


def get_json_logger(
    name: str,
    level: str = "INFO",
) -> logging.Logger:
    """
    Get a logger configured for JSON output.

    Useful for production environments where structured logging is required.

    Args:
        name: The name of the logger, typically __name__.
        level: Logging level as string. Defaults to "INFO".

    Returns:
        Configured logging.Logger instance with JSON formatting.

    Examples:
        >>> logger = get_json_logger(__name__)
        >>> logger.info("Event occurred", extra={"user_id": 123, "action": "login"})
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level.upper())

        formatter = JSONFormatter()
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level.upper())
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def configure_flask_logging(
    app: Flask,
    level: str = "INFO",
    use_colors: bool = True,
) -> None:
    """
    Configure Flask app logging with JHG formatter.

    Replaces Flask's default logging configuration with the JHG formatter,
    providing consistent colored output across the application and its extensions.

    Args:
        app: Flask application instance.
        level: Logging level as string. Defaults to "INFO".
        use_colors: Whether to use ANSI color codes. Defaults to True.

    Raises:
        ValueError: If Flask is not installed.

    Examples:
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> configure_flask_logging(app, level="DEBUG")
        >>> app.logger.info("Flask app configured with JHG logging")
    """
    if Flask is None:
        raise ValueError("Flask must be installed to use configure_flask_logging")

    # Remove default Flask handlers
    if app.logger.handlers:
        app.logger.handlers.clear()

    # Set the logger level
    app.logger.setLevel(level.upper())

    # Create formatter
    formatter = JHGFormatter(use_colors=use_colors, use_emojis=False)

    # Add console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level.upper())
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Propagate to prevent duplicate logs
    app.logger.propagate = True


def configure_flask_json_logging(app: Flask, level: str = "INFO") -> None:
    """
    Configure Flask app logging for JSON output.

    Useful for production deployments using log aggregation systems.

    Args:
        app: Flask application instance.
        level: Logging level as string. Defaults to "INFO".

    Raises:
        ValueError: If Flask is not installed.

    Examples:
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> configure_flask_json_logging(app)
        >>> app.logger.info("JSON logs for production")
    """
    if Flask is None:
        raise ValueError("Flask must be installed to use configure_flask_json_logging")

    # Remove default Flask handlers
    if app.logger.handlers:
        app.logger.handlers.clear()

    # Set the logger level
    app.logger.setLevel(level.upper())

    # Create JSON formatter
    formatter = JSONFormatter()

    # Add handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Propagate to prevent duplicate logs
    app.logger.propagate = True


def set_log_level(logger: logging.Logger, level: str) -> None:
    """
    Update the logging level for an existing logger and all its handlers.

    Args:
        logger: The logger to update.
        level: New logging level as string.

    Examples:
        >>> logger = get_logger(__name__)
        >>> set_log_level(logger, "DEBUG")
    """
    level_upper = level.upper()
    logger.setLevel(level_upper)

    for handler in logger.handlers:
        handler.setLevel(level_upper)


__all__ = [
    "JHGFormatter",
    "JSONFormatter",
    "get_logger",
    "get_json_logger",
    "configure_flask_logging",
    "configure_flask_json_logging",
    "set_log_level",
    "ANSI_COLORS",
    "LEVEL_EMOJIS",
]
