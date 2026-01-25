"""
Audit logging to Databricks Delta tables.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from jhg_patterns.ds.databricks.connector import (
    DatabricksConnector,
    get_connector,
    _validate_table_name,
)

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger that writes to a Delta table.

    Usage:
        audit = AuditLogger(connector, "my_app")

        # Log an action
        audit.log("user_login", user_id="123", ip_address="192.168.1.1")

        # Log with additional context
        audit.log("data_export", user_id="123", metadata={"rows": 1000, "format": "csv"})
    """

    DEFAULT_TABLE = "audit_log"
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS {table} (
        id BIGINT GENERATED ALWAYS AS IDENTITY,
        timestamp TIMESTAMP,
        app_name STRING,
        action STRING,
        user_id STRING,
        session_id STRING,
        ip_address STRING,
        metadata STRING,
        created_at TIMESTAMP
    )
    USING DELTA
    TBLPROPERTIES (
        delta.autoOptimize.optimizeWrite = true,
        delta.autoOptimize.autoCompact = true
    )
    """

    def __init__(
        self,
        connector: Optional[DatabricksConnector] = None,
        app_name: str = "app",
        table: str = DEFAULT_TABLE,
        auto_create: bool = True,
    ):
        """
        Initialize audit logger.

        Args:
            connector: Databricks connector (uses global if not provided)
            app_name: Application name for log entries
            table: Audit log table name
            auto_create: Create table if it doesn't exist

        Raises:
            ValueError: If table name contains invalid characters
        """
        self.connector = connector or get_connector()
        self.app_name = app_name
        self.table = _validate_table_name(table)  # Validate to prevent SQL injection
        self._table_checked = False

        if auto_create:
            self._ensure_table()

    def _ensure_table(self):
        """Create audit table if it doesn't exist."""
        if self._table_checked:
            return

        try:
            if not self.connector.table_exists(self.table):
                self.connector.execute(
                    self.CREATE_TABLE_SQL.format(table=self.table)
                )
                logger.info(f"Created audit table: {self.table}")
            self._table_checked = True
        except Exception as e:
            logger.warning(f"Could not check/create audit table: {e}")

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an audit event.

        Args:
            action: Action identifier (e.g., "user_login", "data_export")
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP address
            metadata: Additional metadata (stored as JSON)
        """
        import json

        try:
            self.connector.execute(
                f"""
                INSERT INTO {self.table}
                (timestamp, app_name, action, user_id, session_id, ip_address, metadata, created_at)
                VALUES
                (:timestamp, :app_name, :action, :user_id, :session_id, :ip_address, :metadata, :created_at)
                """,
                {
                    "timestamp": datetime.utcnow(),
                    "app_name": self.app_name,
                    "action": action,
                    "user_id": user_id,
                    "session_id": session_id,
                    "ip_address": ip_address,
                    "metadata": json.dumps(metadata) if metadata else None,
                    "created_at": datetime.utcnow(),
                },
            )
            logger.debug(f"Audit logged: {action}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def log_request(
        self,
        action: str,
        request=None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an audit event from a Flask request.

        Args:
            action: Action identifier
            request: Flask request object
            user_id: User identifier (extracted from request if not provided)
            metadata: Additional metadata
        """
        if request is None:
            from flask import request

        # Extract info from request
        ip_address = request.remote_addr
        session_id = request.cookies.get("session_id")

        # Try to get user_id from various sources
        if user_id is None:
            user_id = getattr(request, "user_id", None)
            if user_id is None and hasattr(request, "user"):
                user_id = getattr(request.user, "id", None)

        # Build metadata
        meta = {
            "method": request.method,
            "path": request.path,
            "user_agent": request.user_agent.string if request.user_agent else None,
        }
        if metadata:
            meta.update(metadata)

        self.log(
            action=action,
            user_id=str(user_id) if user_id else None,
            session_id=session_id,
            ip_address=ip_address,
            metadata=meta,
        )

    def query_logs(
        self,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ):
        """
        Query audit logs.

        Args:
            action: Filter by action
            user_id: Filter by user
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum rows to return

        Returns:
            List of audit log entries
        """
        conditions = ["app_name = :app_name"]
        params = {"app_name": self.app_name, "limit": limit}

        if action:
            conditions.append("action = :action")
            params["action"] = action

        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id

        if start_date:
            conditions.append("timestamp >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("timestamp <= :end_date")
            params["end_date"] = end_date

        sql = f"""
            SELECT * FROM {self.table}
            WHERE {" AND ".join(conditions)}
            ORDER BY timestamp DESC
            LIMIT :limit
        """

        return self.connector.query(sql, params)
