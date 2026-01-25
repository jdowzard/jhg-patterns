"""
Standardized API response helpers, error handlers, and middleware for Flask applications.

This module provides a consistent pattern for API responses across JHG applications,
including success/error formatting, error handling, and request logging.
"""

import logging
import json
from typing import Any, Dict, Optional, Tuple, Callable
from functools import wraps
from datetime import datetime

from flask import Flask, jsonify, request, g

logger = logging.getLogger(__name__)


# =============================================================================
# Response Helpers
# =============================================================================

def api_success(data: Any = None, message: Optional[str] = None, status: int = 200) -> Tuple:
    """Return a standardized success response for API endpoints.

    Formats successful API responses with a consistent structure containing
    success flag, optional data payload, and optional message.

    Args:
        data: Response data (can be any JSON-serializable type: dict, list, string, etc.)
              If None, returns empty data field
        message: Optional success message (e.g., "Project created successfully")
        status: HTTP status code (default 200)

    Returns:
        Tuple of (Flask response object, HTTP status code)

    Example:
        >>> api_success({'id': 123, 'name': 'Project'}, message='Created', status=201)
        (Response: {"success": true, "data": {"id": 123, "name": "Project"}, "message": "Created"}, 201)

        >>> api_success(data=[1, 2, 3])
        (Response: {"success": true, "data": [1, 2, 3], "message": null}, 200)

        >>> api_success()
        (Response: {"success": true, "data": null, "message": null}, 200)
    """
    response_body = {
        "success": True,
        "data": data,
        "message": message
    }
    return jsonify(response_body), status


def api_error(
    message: str,
    status: int = 400,
    errors: Optional[Dict[str, Any]] = None
) -> Tuple:
    """Return a standardized error response for API endpoints.

    Formats error API responses with a consistent structure containing
    success flag, error message, and optional detailed error information.

    Args:
        message: Human-readable error message
        status: HTTP status code (default 400 for client errors)
        errors: Optional dictionary of detailed errors (e.g., field validation errors)
                Example: {'email': 'Invalid format', 'phone': 'Required field'}

    Returns:
        Tuple of (Flask response object, HTTP status code)

    Example:
        >>> api_error('Invalid project code')
        (Response: {"success": false, "error": "Invalid project code", "errors": null}, 400)

        >>> api_error('Validation failed', status=422, errors={'email': 'Invalid format'})
        (Response: {"success": false, "error": "Validation failed", "errors": {"email": "Invalid format"}}, 422)

        >>> api_error('Unauthorized', status=401)
        (Response: {"success": false, "error": "Unauthorized", "errors": null}, 401)
    """
    response_body = {
        "success": False,
        "error": message,
        "errors": errors
    }
    return jsonify(response_body), status


# =============================================================================
# Error Handlers
# =============================================================================

def register_api_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for common HTTP error codes on a Flask app.

    Registers error handlers that return consistent JSON responses for API routes
    while maintaining backward compatibility for non-API routes (returning HTML).

    Handlers register for:
    - 400: Bad Request (client error)
    - 401: Unauthorized (authentication required)
    - 403: Forbidden (permission denied)
    - 404: Not Found (resource not found)
    - 500: Internal Server Error (server error)
    - 503: Service Unavailable (temporary outage)

    Args:
        app: Flask application instance to register handlers on

    Example:
        >>> app = Flask(__name__)
        >>> register_api_error_handlers(app)
        >>> # Now /api/* routes get JSON errors, other routes get HTML
    """

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors.

        Returns JSON for API routes, HTML for regular routes.
        """
        if request.path.startswith('/api/'):
            return api_error('Bad request', status=400)
        # For non-API routes, Flask will use default HTML error page
        return {"error": "Bad request"}, 400

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors.

        Typically raised when authentication is required but missing or invalid.
        Returns JSON for API routes, HTML for regular routes.
        """
        if request.path.startswith('/api/'):
            return api_error('Unauthorized', status=401)
        return {"error": "Unauthorized"}, 401

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors.

        Returned when user is authenticated but lacks permission for the resource.
        Returns JSON for API routes, HTML for regular routes.
        """
        if request.path.startswith('/api/'):
            return api_error('Forbidden', status=403)
        return {"error": "Forbidden"}, 403

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors.

        Returned when a requested resource does not exist.
        Returns JSON for API routes, HTML for regular routes.
        """
        if request.path.startswith('/api/'):
            return api_error('Not found', status=404)
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error.

        Logs the error for debugging. Returns JSON for API routes, HTML for regular routes.
        """
        logger.error(f"Internal server error: {error}", exc_info=True)
        if request.path.startswith('/api/'):
            return api_error('Internal server error', status=500)
        return {"error": "Internal server error"}, 500

    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle 503 Service Unavailable errors.

        Typically raised when a critical dependency (e.g., database) is unavailable.
        Returns JSON for API routes, HTML for regular routes.
        """
        if request.path.startswith('/api/'):
            return api_error('Service unavailable', status=503)
        return {"error": "Service unavailable"}, 503

    logger.debug("API error handlers registered on Flask app")


# =============================================================================
# Request Logging Middleware
# =============================================================================

def log_api_request() -> None:
    """Log API request details before route processing.

    Should be called via Flask's before_request hook. Logs:
    - HTTP method and path
    - Request headers (sanitized)
    - Query parameters
    - Request body (for POST/PUT/PATCH, first 1000 chars)

    Can be registered with: app.before_request(log_api_request)

    Stores request metadata in Flask's g object for use in response logging:
    - g.request_start_time: Request timestamp (datetime)
    - g.request_method: HTTP method (str)
    - g.request_path: Request path (str)

    Example:
        >>> app = Flask(__name__)
        >>> app.before_request(log_api_request)
    """
    # Store timing info for response logging
    g.request_start_time = datetime.utcnow()
    g.request_method = request.method
    g.request_path = request.path

    # Skip logging for health checks and static files
    if request.path in ['/health', '/metrics'] or request.path.startswith('/static/'):
        return

    # Build log message
    log_parts = [f"{request.method} {request.path}"]

    # Add query string if present
    if request.args:
        log_parts.append(f"query={dict(request.args)}")

    # Add request headers (sanitized - exclude auth tokens)
    headers_to_log = {}
    sanitized_headers = {
        'Authorization', 'X-API-Key', 'X-Auth-Token', 'Cookie',
        'X-CSRF-Token', 'X-Access-Token'
    }
    for header_name, header_value in request.headers:
        if header_name not in sanitized_headers:
            headers_to_log[header_name] = header_value

    if headers_to_log and request.method in ['POST', 'PUT', 'PATCH']:
        log_parts.append(f"headers={headers_to_log}")

    # Add request body for POST/PUT/PATCH
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            if request.is_json:
                body_data = request.get_json(silent=True)
                # Sanitize sensitive fields
                sanitized_body = _sanitize_dict(body_data)
                body_str = json.dumps(sanitized_body)
                if len(body_str) > 1000:
                    body_str = body_str[:1000] + "... (truncated)"
                log_parts.append(f"body={body_str}")
            elif request.form:
                form_data = dict(request.form)
                sanitized_form = _sanitize_dict(form_data)
                log_parts.append(f"form={sanitized_form}")
        except Exception as e:
            logger.debug(f"Could not parse request body: {e}")

    # Remote address
    remote_addr = request.remote_addr
    if 'X-Forwarded-For' in request.headers:
        remote_addr = request.headers['X-Forwarded-For'].split(',')[0].strip()
    log_parts.append(f"from={remote_addr}")

    logger.info(" | ".join(log_parts))


def _sanitize_dict(data: Any) -> Any:
    """Recursively sanitize a dictionary by removing sensitive field values.

    Replaces values for known sensitive field names with '[REDACTED]' to prevent
    logging of passwords, tokens, and PII.

    Args:
        data: Dictionary or other data structure to sanitize

    Returns:
        Sanitized copy of the input data

    Sensitive fields: password, token, key, secret, api_key, access_token, etc.
    """
    if not isinstance(data, dict):
        return data

    sensitive_fields = {
        'password', 'passwd', 'pwd',
        'token', 'api_token', 'access_token', 'refresh_token',
        'key', 'api_key', 'secret', 'client_secret',
        'authorization', 'auth', 'bearer',
        'apikey', 'token_', 'oauth_token',
        'credential', 'credentials', 'session_key'
    }

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_fields):
            sanitized[key] = '[REDACTED]'
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def register_request_logging(app: Flask) -> None:
    """Register request logging middleware on a Flask app.

    Registers the log_api_request function to run before each request,
    enabling comprehensive request logging for debugging and monitoring.

    Args:
        app: Flask application instance

    Example:
        >>> app = Flask(__name__)
        >>> register_request_logging(app)
        >>> # Now all requests are logged with details
    """
    app.before_request(log_api_request)
    logger.debug("Request logging middleware registered")


# =============================================================================
# Decorators
# =============================================================================

def api_route(
    *route_args,
    methods: list = None,
    json_required: bool = False,
    **route_kwargs
) -> Callable:
    """Decorator for API routes with automatic error handling and JSON parsing.

    Combines Flask's route decorator with common API patterns:
    - Automatic JSON parsing and validation
    - Standardized error handling
    - Request/response logging

    Args:
        *route_args: Positional arguments to pass to Flask's route()
        methods: HTTP methods allowed (default ['GET'])
        json_required: If True, returns 400 if Content-Type is not application/json
        **route_kwargs: Keyword arguments to pass to Flask's route()

    Returns:
        Decorated function that returns api_success/api_error responses

    Example:
        >>> @app.route('/api/users', methods=['POST'])
        >>> def create_user():
        >>>     data = request.get_json()
        >>>     return api_success({'id': 1}, status=201)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate JSON content type if required
            if json_required:
                if not request.is_json:
                    return api_error(
                        'Content-Type must be application/json',
                        status=400
                    )

            # Call the route handler
            try:
                result = func(*args, **kwargs)
                # If result is already a response tuple, return as-is
                if isinstance(result, tuple):
                    return result
                # Otherwise wrap in api_success
                return api_success(result)
            except ValueError as e:
                # Validation errors from route handler
                return api_error(str(e), status=422)
            except Exception as e:
                # Unexpected errors
                logger.exception(f"Error in {func.__name__}: {e}")
                return api_error('Internal server error', status=500)

        return wrapper
    return decorator
