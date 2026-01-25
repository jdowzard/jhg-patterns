"""
JHG Databricks Patterns - Utilities for working with Databricks.

Includes:
- Unity Catalog helpers
- SQL connector wrappers
- Delta table utilities

Note: This package has optional dependencies:
- pip install jhg-patterns-databricks[sql] for SQL connector
- pip install jhg-patterns-databricks[sdk] for Databricks SDK
- pip install jhg-patterns-databricks[all] for everything
"""

from jhg_patterns.databricks.unity import (
    get_catalog_schema,
    get_table_path,
)

__all__ = ["get_catalog_schema", "get_table_path"]
__version__ = "0.1.0"
