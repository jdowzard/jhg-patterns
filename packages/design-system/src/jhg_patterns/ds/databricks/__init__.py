"""
Databricks utilities for JHG Design System.

Provides:
- SQL connector wrapper with connection management
- Configuration with environment variable support
- Audit logging to Delta tables
- TTL caching with decorator support
"""

from jhg_patterns.ds.databricks.connector import (
    DatabricksConnector,
    DatabricksConfig,
    get_connector,
    init_connector,
)
from jhg_patterns.ds.databricks.audit import AuditLogger
from jhg_patterns.ds.databricks.cache import TTLCache

__all__ = [
    "DatabricksConnector",
    "DatabricksConfig",
    "get_connector",
    "init_connector",
    "AuditLogger",
    "TTLCache",
]
