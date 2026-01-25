"""
Unity Catalog utilities for Databricks.

Provides helpers for working with Unity Catalog namespaces (catalog.schema.table).
"""

import os
from typing import Tuple, Optional


def get_catalog_schema(
    catalog_env: str = "DATABRICKS_CATALOG",
    schema_env: str = "DATABRICKS_SCHEMA",
    default_catalog: str = "main",
    default_schema: str = "default",
) -> Tuple[str, str]:
    """
    Get catalog and schema from environment variables.

    Args:
        catalog_env: Environment variable name for catalog
        schema_env: Environment variable name for schema
        default_catalog: Default catalog if env var not set
        default_schema: Default schema if env var not set

    Returns:
        Tuple of (catalog, schema)

    Example:
        catalog, schema = get_catalog_schema()
        query = f"SELECT * FROM {catalog}.{schema}.my_table"
    """
    catalog = os.getenv(catalog_env, default_catalog)
    schema = os.getenv(schema_env, default_schema)
    return catalog, schema


def get_table_path(
    table: str,
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    catalog_env: str = "DATABRICKS_CATALOG",
    schema_env: str = "DATABRICKS_SCHEMA",
) -> str:
    """
    Get fully qualified table path (catalog.schema.table).

    Args:
        table: Table name
        catalog: Optional catalog override
        schema: Optional schema override
        catalog_env: Environment variable for catalog
        schema_env: Environment variable for schema

    Returns:
        Fully qualified table path

    Example:
        path = get_table_path("users")
        # Returns: "main.default.users" (using defaults)
    """
    if catalog is None or schema is None:
        default_catalog, default_schema = get_catalog_schema(catalog_env, schema_env)
        catalog = catalog or default_catalog
        schema = schema or default_schema

    return f"{catalog}.{schema}.{table}"


def parse_table_path(path: str) -> Tuple[str, str, str]:
    """
    Parse a fully qualified table path into components.

    Args:
        path: Table path like "catalog.schema.table"

    Returns:
        Tuple of (catalog, schema, table)

    Raises:
        ValueError: If path doesn't have exactly 3 parts
    """
    parts = path.split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected catalog.schema.table format, got: {path}")
    return tuple(parts)
