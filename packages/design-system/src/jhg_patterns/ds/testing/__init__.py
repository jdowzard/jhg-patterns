"""
Testing utilities for JHG Design System.

Provides pytest fixtures, mocks, and factories for testing Flask applications
that use the JHG Design System.

Available fixtures:
    - app: Flask test application with design system
    - client: Flask test client
    - mock_databricks: Mocked Databricks connector

Available factories:
    - make_user: Create test user objects
    - make_databricks_config: Create test Databricks configurations
    - make_app_config: Create test app configurations

Example:
    from jhg_patterns.ds.testing import app, client, mock_databricks
    from jhg_patterns.ds.testing.factories import make_user

    def test_home_page(client):
        response = client.get("/")
        assert response.status_code == 200

    def test_with_mock_db(mock_databricks):
        mock_databricks.return_value.query.return_value = [
            {"id": 1, "name": "Test"}
        ]
"""

from jhg_patterns.ds.testing.fixtures import (
    app,
    client,
    mock_databricks,
)

__all__ = [
    "app",
    "client",
    "mock_databricks",
]
