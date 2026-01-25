"""
Databricks SQL connector utilities.

Requires: pip install jhg-patterns-databricks[sql]
"""

import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def get_connection_params(
    host_env: str = "DATABRICKS_HOST",
    token_env: str = "DATABRICKS_TOKEN",
    warehouse_env: str = "DATABRICKS_SQL_PATH",
) -> Dict[str, str]:
    """
    Get Databricks SQL connection parameters from environment.

    Args:
        host_env: Environment variable for Databricks host
        token_env: Environment variable for PAT token
        warehouse_env: Environment variable for SQL warehouse path

    Returns:
        Dict with connection parameters

    Raises:
        ValueError: If required environment variables are not set
    """
    host = os.getenv(host_env)
    token = os.getenv(token_env)
    warehouse = os.getenv(warehouse_env)

    missing = []
    if not host:
        missing.append(host_env)
    if not token:
        missing.append(token_env)
    if not warehouse:
        missing.append(warehouse_env)

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return {
        "server_hostname": host.replace("https://", ""),
        "http_path": warehouse,
        "access_token": token,
    }


@contextmanager
def get_connection(**kwargs):
    """
    Context manager for Databricks SQL connection.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()

    Args:
        **kwargs: Override connection parameters

    Yields:
        databricks.sql.Connection
    """
    try:
        from databricks import sql
    except ImportError:
        raise ImportError(
            "databricks-sql-connector not installed. "
            "Install with: pip install jhg-patterns-databricks[sql]"
        )

    params = get_connection_params()
    params.update(kwargs)

    conn = sql.connect(**params)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    fetch: bool = True,
) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return results as list of dicts.

    Args:
        query: SQL query string
        params: Optional query parameters
        fetch: Whether to fetch results (False for INSERT/UPDATE)

    Returns:
        List of dicts (one per row) if fetch=True, else empty list

    Example:
        users = execute_query("SELECT * FROM users WHERE active = :active", {"active": True})
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if not fetch:
                return []

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()


def check_connection() -> bool:
    """
    Check if Databricks SQL connection is working.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        execute_query("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Databricks connection check failed: {e}")
        return False
