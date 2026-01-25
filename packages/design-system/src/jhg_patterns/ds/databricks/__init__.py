"""
Databricks utilities for JHG Design System.

Provides:
- SQL connector wrapper with connection pooling
- Audit logging to Delta tables
- Permission helpers for Unity Catalog
"""

from jhg_patterns.ds.databricks.connector import DatabricksConnector, get_connector
from jhg_patterns.ds.databricks.audit import AuditLogger
from jhg_patterns.ds.databricks.cache import TTLCache

__all__ = [
    "DatabricksConnector",
    "get_connector",
    "AuditLogger",
    "TTLCache",
]
