"""
Pytest fixtures and factories for testing JHG Design System applications.

Provides:
    - Flask app and test client fixtures
    - Mocked Databricks connector
    - Sample data factories for common test objects
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Flask Fixtures
# ============================================================================


@pytest.fixture
def app():
    """
    Create a Flask test application with JHG Design System.

    Returns a configured Flask app in testing mode with:
    - Design system initialized
    - Testing mode enabled
    - All security checks disabled
    - No actual Databricks connections

    Returns:
        Flask: Configured test application

    Example:
        def test_app_creation(app):
            assert app.config["TESTING"]
            assert app is not None
    """
    from jhg_patterns.ds import create_app

    app = create_app("test-app")
    app.config["TESTING"] = True

    yield app


@pytest.fixture
def client(app):
    """
    Create a Flask test client for making requests to the test app.

    Automatically uses the app fixture and provides a test client
    that can make HTTP requests without a server.

    Args:
        app: Flask app fixture

    Returns:
        FlaskClient: Test client for making requests

    Example:
        def test_health_endpoint(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    return app.test_client()


# ============================================================================
# Databricks Mocks
# ============================================================================


@pytest.fixture
def mock_databricks():
    """
    Mock the Databricks connector for unit tests.

    Returns a patched DatabricksConnector class that can be configured
    to return mock data. By default, returns empty results for queries.

    The mock is automatically cleaned up after the test.

    Returns:
        MagicMock: Mocked DatabricksConnector class

    Example:
        def test_with_mock_databricks(mock_databricks):
            # Configure mock response
            mock_databricks.return_value.query.return_value = [
                {"id": 1, "name": "Test User"}
            ]

            # Use in test
            from jhg_patterns.ds.databricks import DatabricksConnector
            connector = DatabricksConnector()
            rows = connector.query("SELECT * FROM users")
            assert len(rows) == 1
            assert rows[0]["name"] == "Test User"
    """
    with patch("jhg_patterns.ds.databricks.connector.DatabricksConnector") as mock:
        # Default mock behavior
        mock.return_value.query.return_value = []
        mock.return_value.execute.return_value = None

        yield mock


@pytest.fixture
def mock_databricks_config():
    """
    Mock Databricks configuration for testing.

    Provides a complete DatabricksConfig object with test values
    that don't require actual environment variables.

    Returns:
        dict: Configuration dictionary with test Databricks credentials

    Example:
        def test_connector_creation(mock_databricks_config):
            from jhg_patterns.ds.databricks import DatabricksConnector
            connector = DatabricksConnector(**mock_databricks_config)
            assert connector is not None
    """
    return {
        "host": "test-workspace.cloud.databricks.com",
        "token": "dapi123456789testtoken",
        "sql_path": "/sql/1.0/warehouses/test-warehouse",
        "catalog": "test_catalog",
        "schema": "test_schema",
    }


# ============================================================================
# Sample Data Factories
# ============================================================================


def make_user(
    id: int = 1,
    name: str = "Test User",
    email: str = "test@jhg.com.au",
    role: str = "user",
    active: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Factory for creating test user objects.

    Generates a user dictionary with sensible defaults that can be
    overridden with keyword arguments.

    Args:
        id: User ID (default: 1)
        name: User full name (default: "Test User")
        email: User email address (default: "test@jhg.com.au")
        role: User role (default: "user")
        active: Whether user is active (default: True)
        **kwargs: Additional fields to include in user object

    Returns:
        dict: User object with id, name, email, role, active, and any extra fields

    Example:
        # Default user
        user = make_user()
        assert user["name"] == "Test User"

        # Custom user
        admin = make_user(id=2, name="Admin", role="admin")
        assert admin["role"] == "admin"

        # With extra fields
        user = make_user(created_at="2024-01-01", department="Engineering")
        assert user["department"] == "Engineering"
    """
    user = {
        "id": id,
        "name": name,
        "email": email,
        "role": role,
        "active": active,
    }
    user.update(kwargs)
    return user


def make_databricks_config(
    host: str = "test-workspace.cloud.databricks.com",
    token: str = "dapi123456789testtoken",
    sql_path: str = "/sql/1.0/warehouses/test-warehouse",
    catalog: str = "test_catalog",
    schema: str = "test_schema",
    **kwargs,
) -> Dict[str, str]:
    """
    Factory for creating test Databricks configuration objects.

    Generates a complete configuration dictionary with test values.

    Args:
        host: Databricks workspace hostname
        token: Databricks authentication token
        sql_path: SQL warehouse HTTP path
        catalog: Unity Catalog name
        schema: Schema name
        **kwargs: Additional configuration parameters

    Returns:
        dict: Databricks configuration dictionary

    Example:
        config = make_databricks_config(catalog="prod_catalog")
        assert config["catalog"] == "prod_catalog"
    """
    config = {
        "host": host,
        "token": token,
        "sql_path": sql_path,
        "catalog": catalog,
        "schema": schema,
    }
    config.update(kwargs)
    return config


def make_app_config(
    name: str = "test-app",
    theme: Optional[str] = None,
    debug: bool = False,
    cache_enabled: bool = True,
    cache_ttl: int = 600,
    csrf_enabled: bool = False,
    rate_limiting_enabled: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Factory for creating test application configuration objects.

    Generates an AppConfig dictionary suitable for testing,
    with security features disabled by default.

    Args:
        name: Application name (default: "test-app")
        theme: Theme name or path (default: None, uses JHG default)
        debug: Debug mode (default: False)
        cache_enabled: Enable caching (default: True)
        cache_ttl: Default cache TTL in seconds (default: 600)
        csrf_enabled: Enable CSRF protection (default: False)
        rate_limiting_enabled: Enable rate limiting (default: False)
        **kwargs: Additional configuration parameters

    Returns:
        dict: Application configuration dictionary

    Example:
        # Default test config
        config = make_app_config()
        assert config["name"] == "test-app"

        # With custom values
        config = make_app_config(name="my-app", debug=True)
        assert config["debug"] is True
    """
    config = {
        "name": name,
        "debug": debug,
        "cache": {
            "enabled": cache_enabled,
            "default_ttl": cache_ttl,
            "ttls": {},
        },
        "security": {
            "csrf_enabled": csrf_enabled,
            "rate_limiting_enabled": rate_limiting_enabled,
            "cors_enabled": True,
            "cors_origins": "*",
        },
        "enable_health_check": True,
        "enable_cache_api": False,  # Disabled by default in tests
        "enable_error_pages": True,
    }

    if theme:
        config["theme"] = theme

    config.update(kwargs)
    return config


def make_query_result(
    id: int = 1,
    name: str = "Result",
    value: Optional[Any] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Factory for creating test Databricks query result rows.

    Generates a dictionary representing a row returned from a database query.

    Args:
        id: Row ID (default: 1)
        name: Row name field (default: "Result")
        value: Row value field (default: None)
        **kwargs: Additional fields to include in result row

    Returns:
        dict: Query result row with id, name, value, and any extra fields

    Example:
        # Basic result
        row = make_query_result()
        assert row["id"] == 1

        # Custom result with extra fields
        row = make_query_result(
            id=42,
            name="Report",
            value=99.5,
            timestamp="2024-01-01T00:00:00Z"
        )
        assert row["timestamp"] == "2024-01-01T00:00:00Z"
    """
    result = {
        "id": id,
        "name": name,
    }

    if value is not None:
        result["value"] = value

    result.update(kwargs)
    return result


def make_databricks_error(
    error_code: str = "RESOURCE_NOT_FOUND",
    message: str = "Resource not found",
    **kwargs,
) -> Dict[str, str]:
    """
    Factory for creating test Databricks error responses.

    Generates a dictionary representing a Databricks API error response.

    Args:
        error_code: Databricks error code
        message: Error message
        **kwargs: Additional error fields

    Returns:
        dict: Databricks error response dictionary

    Example:
        error = make_databricks_error()
        assert error["error_code"] == "RESOURCE_NOT_FOUND"

        error = make_databricks_error(
            error_code="PERMISSION_DENIED",
            message="User does not have permission"
        )
        assert error["error_code"] == "PERMISSION_DENIED"
    """
    error = {
        "error_code": error_code,
        "message": message,
    }
    error.update(kwargs)
    return error
