"""
Databricks SQL connector wrapper with connection management.
"""

import logging
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Generator

logger = logging.getLogger(__name__)

# Regex for valid Delta table identifiers: catalog.schema.table or schema.table or table
# Allows letters, digits, underscores. Each segment must start with letter or underscore.
_TABLE_NAME_PATTERN = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*){0,2}$"
)


def _validate_table_name(table: str) -> str:
    """
    Validate table name to prevent SQL injection.

    Args:
        table: Table name (catalog.schema.table, schema.table, or table)

    Returns:
        The validated table name

    Raises:
        ValueError: If table name contains invalid characters
    """
    if not table or not _TABLE_NAME_PATTERN.match(table):
        raise ValueError(
            f"Invalid table name: '{table}'. "
            "Must be alphanumeric with underscores, in format: "
            "table, schema.table, or catalog.schema.table"
        )
    return table

# Global connector instance
_connector: Optional["DatabricksConnector"] = None


@dataclass
class DatabricksConfig:
    """Databricks connection configuration."""

    host: str
    token: str
    sql_path: str
    catalog: str = "main"
    schema: str = "default"

    @classmethod
    def from_env(cls) -> "DatabricksConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.environ["DATABRICKS_HOST"],
            token=os.environ["DATABRICKS_TOKEN"],
            sql_path=os.environ["DATABRICKS_SQL_PATH"],
            catalog=os.getenv("DATABRICKS_CATALOG", "main"),
            schema=os.getenv("DATABRICKS_SCHEMA", "default"),
        )


class DatabricksConnector:
    """
    Databricks SQL connector wrapper.

    Provides connection management, query execution, and error handling.

    Usage:
        connector = DatabricksConnector(config)

        # Execute query
        rows = connector.query("SELECT * FROM users WHERE id = :id", {"id": 123})

        # Execute with context manager
        with connector.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        # Bulk operations
        connector.execute_many(
            "INSERT INTO logs (message) VALUES (:message)",
            [{"message": "log1"}, {"message": "log2"}]
        )
    """

    def __init__(self, config: DatabricksConfig):
        """
        Initialize connector.

        Args:
            config: Databricks connection configuration
        """
        self.config = config
        self._connection = None

    @property
    def connection(self):
        """Get or create connection."""
        if self._connection is None:
            try:
                from databricks import sql

                self._connection = sql.connect(
                    server_hostname=self.config.host,
                    http_path=self.config.sql_path,
                    access_token=self.config.token,
                    catalog=self.config.catalog,
                    schema=self.config.schema,
                )
                logger.info(f"Connected to Databricks: {self.config.host}")
            except ImportError:
                raise ImportError(
                    "databricks-sql-connector not installed. "
                    "Install with: pip install jhg-patterns-ds[databricks]"
                )
        return self._connection

    def close(self):
        """Close the connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Databricks connection closed")

    @contextmanager
    def cursor(self) -> Generator:
        """
        Get a cursor context manager.

        Yields:
            Databricks cursor
        """
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_all: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as dictionaries.

        Args:
            sql: SQL query with optional :param placeholders
            params: Query parameters
            fetch_all: If True, fetch all results; if False, return cursor

        Returns:
            List of dictionaries with column names as keys
        """
        with self.cursor() as cursor:
            cursor.execute(sql, params or {})

            if not fetch_all:
                return cursor

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    def query_one(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return first result.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Dictionary with column names as keys, or None if no results
        """
        results = self.query(sql, params)
        return results[0] if results else None

    def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Execute a statement (INSERT, UPDATE, DELETE).

        Args:
            sql: SQL statement
            params: Statement parameters

        Returns:
            Number of affected rows
        """
        with self.cursor() as cursor:
            cursor.execute(sql, params or {})
            return cursor.rowcount

    def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]],
    ) -> int:
        """
        Execute a statement with multiple parameter sets.

        Uses batch execution for better performance (single round-trip
        instead of N separate queries).

        Args:
            sql: SQL statement
            params_list: List of parameter dictionaries

        Returns:
            Total number of affected rows
        """
        if not params_list:
            return 0

        with self.cursor() as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount

    def table_exists(self, table: str) -> bool:
        """
        Check if a table exists.

        Args:
            table: Table name (can include catalog.schema.table)

        Returns:
            True if table exists

        Raises:
            ValueError: If table name contains invalid characters
        """
        _validate_table_name(table)
        try:
            self.query(f"SELECT 1 FROM {table} LIMIT 0")
            return True
        except Exception:
            return False

    def get_table_schema(self, table: str) -> List[Dict[str, str]]:
        """
        Get table schema information.

        Args:
            table: Table name

        Returns:
            List of column definitions

        Raises:
            ValueError: If table name contains invalid characters
        """
        _validate_table_name(table)
        return self.query(f"DESCRIBE {table}")


def get_connector(config: Optional[DatabricksConfig] = None) -> DatabricksConnector:
    """
    Get the global connector instance.

    Args:
        config: Configuration (uses environment if not provided on first call)

    Returns:
        DatabricksConnector instance
    """
    global _connector

    if _connector is None:
        if config is None:
            config = DatabricksConfig.from_env()
        _connector = DatabricksConnector(config)

    return _connector


def init_connector(config: DatabricksConfig) -> DatabricksConnector:
    """
    Initialize the global connector with specific config.

    Args:
        config: Databricks configuration

    Returns:
        DatabricksConnector instance
    """
    global _connector
    _connector = DatabricksConnector(config)
    return _connector
