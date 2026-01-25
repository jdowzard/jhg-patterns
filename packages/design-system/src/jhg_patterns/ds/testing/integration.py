"""Integration testing helpers for Databricks and Microsoft Graph API.

This module provides decorators and base classes for integration tests that require
external service connectivity, including Databricks and Microsoft Graph API.

Examples:
    Using the Databricks test decorator:
        @requires_databricks
        def test_query_table(self):
            result = self.connector.query("SELECT * FROM table LIMIT 1")
            assert len(result) > 0

    Using the Graph API test decorator:
        @requires_graph
        def test_read_calendar(self):
            calendar = self.graph_client.me.calendar.get()
            assert calendar is not None

    Using the Databricks test base class:
        class TestDatabricksQueries(DatabricksTestCase):
            def test_table_exists(self):
                tables = self.connector.list_tables("catalog.schema")
                assert len(tables) > 0
"""

import os
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import pytest

# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


def requires_databricks(func: F) -> F:
    """Skip test if Databricks credentials are not available.

    This decorator checks for the DATABRICKS_HOST environment variable
    to determine if Databricks credentials are configured. If not present,
    the test is skipped with an informative message.

    Args:
        func: The test function to be decorated.

    Returns:
        Wrapped function that skips if Databricks is not configured.

    Example:
        @requires_databricks
        def test_databricks_connection(self):
            assert self.connector is not None
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not os.getenv("DATABRICKS_HOST"):
            pytest.skip("Databricks credentials not configured (DATABRICKS_HOST not set)")
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def requires_graph(func: F) -> F:
    """Skip test if Microsoft Graph API credentials are not available.

    This decorator checks for the GRAPH_CLIENT_ID and GRAPH_CLIENT_SECRET
    environment variables to determine if Graph API credentials are configured.
    If not present, the test is skipped with an informative message.

    Args:
        func: The test function to be decorated.

    Returns:
        Wrapped function that skips if Graph API is not configured.

    Example:
        @requires_graph
        def test_graph_connection(self):
            assert self.graph_client is not None
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not os.getenv("GRAPH_CLIENT_ID") or not os.getenv("GRAPH_CLIENT_SECRET"):
            pytest.skip(
                "Graph API credentials not configured "
                "(GRAPH_CLIENT_ID and/or GRAPH_CLIENT_SECRET not set)"
            )
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def requires_databricks_and_graph(func: F) -> F:
    """Skip test if either Databricks or Graph API credentials are unavailable.

    This decorator checks for both Databricks and Graph API credentials.
    If either is missing, the test is skipped with an informative message.

    Args:
        func: The test function to be decorated.

    Returns:
        Wrapped function that skips if either service is not configured.

    Example:
        @requires_databricks_and_graph
        def test_sync_data_to_graph(self):
            data = self.connector.query("SELECT * FROM users")
            self.graph_client.batch_update(data)
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not os.getenv("DATABRICKS_HOST"):
            pytest.skip("Databricks credentials not configured (DATABRICKS_HOST not set)")
        if not os.getenv("GRAPH_CLIENT_ID") or not os.getenv("GRAPH_CLIENT_SECRET"):
            pytest.skip(
                "Graph API credentials not configured "
                "(GRAPH_CLIENT_ID and/or GRAPH_CLIENT_SECRET not set)"
            )
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


class DatabricksTestCase:
    """Base class for Databricks integration tests.

    This class provides setup and teardown methods for Databricks connections.
    Subclasses should implement test methods that use self.connector.

    The connector is initialized with configuration from environment variables:
        - DATABRICKS_HOST: Databricks workspace URL
        - DATABRICKS_TOKEN: Personal access token
        - DATABRICKS_CATALOG: Default catalog (optional)

    Attributes:
        connector: DatabricksConnector instance for database operations.

    Example:
        class TestDatabricksQueries(DatabricksTestCase):
            def test_list_catalogs(self):
                catalogs = self.connector.list_catalogs()
                assert len(catalogs) > 0

            def test_query_table(self):
                result = self.connector.query("SELECT 1")
                assert result is not None
    """

    connector: Optional[Any] = None

    @classmethod
    def setup_class(cls) -> None:
        """Set up Databricks connector for test class.

        Initializes the connector from environment configuration. This method
        is called once before any tests in the class are run.

        Raises:
            ValueError: If required Databricks credentials are not configured.
        """
        # Import here to avoid hard dependency
        try:
            from databricks.sql import connect
            from databricks.sql.client import Connection
        except ImportError:
            raise ImportError(
                "databricks-sql-connector not installed. "
                "Install with: pip install databricks-sql-connector"
            )

        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")

        if not host or not token:
            raise ValueError(
                "Databricks credentials not configured. "
                "Set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables."
            )

        cls.connector = connect(
            server_hostname=host,
            auth_type="pat",
            personal_access_token=token,
        )

    @classmethod
    def teardown_class(cls) -> None:
        """Clean up Databricks connection.

        Closes the connector after all tests in the class have run.
        """
        if cls.connector is not None:
            try:
                cls.connector.close()
            except Exception as e:
                # Log but don't raise during cleanup
                print(f"Warning: Failed to close Databricks connection: {e}")
            finally:
                cls.connector = None


class GraphAPITestCase:
    """Base class for Microsoft Graph API integration tests.

    This class provides setup and teardown methods for Graph API connections.
    Subclasses should implement test methods that use self.graph_client.

    The Graph client is initialized with configuration from environment variables:
        - GRAPH_CLIENT_ID: Azure app registration client ID
        - GRAPH_CLIENT_SECRET: Azure app registration client secret
        - GRAPH_TENANT_ID: Azure tenant ID (optional, defaults to "common")

    Attributes:
        graph_client: Authenticated Graph API client instance.

    Example:
        class TestGraphAPI(GraphAPITestCase):
            def test_get_user(self):
                user = self.graph_client.me.get()
                assert user is not None

            def test_list_groups(self):
                groups = self.graph_client.groups.get()
                assert len(groups.value) > 0
    """

    graph_client: Optional[Any] = None

    @classmethod
    def setup_class(cls) -> None:
        """Set up Microsoft Graph API client for test class.

        Initializes the client from environment configuration. This method
        is called once before any tests in the class are run.

        Raises:
            ValueError: If required Graph API credentials are not configured.
        """
        # Import here to avoid hard dependency
        try:
            from azure.identity import ClientSecretCredential
            from msgraph.core import GraphClient
        except ImportError:
            raise ImportError(
                "msgraph-core and azure-identity not installed. "
                "Install with: pip install msgraph-core azure-identity"
            )

        client_id = os.getenv("GRAPH_CLIENT_ID")
        client_secret = os.getenv("GRAPH_CLIENT_SECRET")
        tenant_id = os.getenv("GRAPH_TENANT_ID", "common")

        if not client_id or not client_secret:
            raise ValueError(
                "Graph API credentials not configured. "
                "Set GRAPH_CLIENT_ID and GRAPH_CLIENT_SECRET environment variables."
            )

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        cls.graph_client = GraphClient(credential=credential)

    @classmethod
    def teardown_class(cls) -> None:
        """Clean up Graph API client.

        Closes the client after all tests in the class have run.
        """
        if cls.graph_client is not None:
            try:
                cls.graph_client.close()
            except Exception as e:
                # Log but don't raise during cleanup
                print(f"Warning: Failed to close Graph API client: {e}")
            finally:
                cls.graph_client = None


class DatabricksGraphIntegrationTestCase(DatabricksTestCase, GraphAPITestCase):
    """Base class for tests requiring both Databricks and Graph API.

    This class combines setup and teardown for both Databricks and Graph API
    connections, allowing tests that require both services.

    Attributes:
        connector: DatabricksConnector instance for database operations.
        graph_client: Authenticated Graph API client instance.

    Example:
        class TestDataSync(DatabricksGraphIntegrationTestCase):
            def test_sync_users_to_graph(self):
                # Query users from Databricks
                users = self.connector.query("SELECT * FROM users")
                # Update in Graph API
                for user in users:
                    self.graph_client.users[user['id']].patch(user)
    """

    @classmethod
    def setup_class(cls) -> None:
        """Set up both Databricks and Graph API clients."""
        DatabricksTestCase.setup_class()
        GraphAPITestCase.setup_class()

    @classmethod
    def teardown_class(cls) -> None:
        """Clean up both Databricks and Graph API connections."""
        DatabricksTestCase.teardown_class()
        GraphAPITestCase.teardown_class()
