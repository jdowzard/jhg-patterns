"""
Microsoft Graph API client for JHG Flask applications.

Provides authenticated access to MS Graph for:
- Sending emails
- Accessing user/group info
- SharePoint integration (see sharepoint.py for higher-level patterns)

Usage:
    from jhg_patterns.ds.graph import GraphClient

    # Client credentials flow (app-only, for background jobs)
    client = GraphClient.from_env()
    client.send_email(to=["user@jhg.com.au"], subject="Test", body_html="<p>Hello</p>")

    # Delegated flow (user context, for interactive apps)
    client = GraphClient.from_refresh_token(refresh_token)
    me = client.get_current_user()
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import msal
import requests

logger = logging.getLogger(__name__)

# Status codes for retry logic
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
CLIENT_ERROR_CODES = {400, 401, 403, 404}


class GraphError(Exception):
    """Base exception for MS Graph errors."""

    pass


class GraphConnectionError(GraphError):
    """Raised when MS Graph API is unreachable."""

    pass


class GraphAuthError(GraphError):
    """Raised when authentication fails."""

    pass


def retry_on_transient_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator that retries on transient MS Graph errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry: 1s, 2s, 4s)
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"MS Graph connection error, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"MS Graph connection failed after {max_retries} retries"
                        )
                        raise GraphConnectionError(
                            f"Unable to connect to MS Graph after {max_retries} retries"
                        ) from e
                except requests.exceptions.Timeout as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"MS Graph timeout, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"MS Graph timeout after {max_retries} retries")
                        raise GraphConnectionError(
                            f"MS Graph request timed out after {max_retries} retries"
                        ) from e
            raise last_exception

        return wrapper

    return decorator


@dataclass
class GraphConfig:
    """Configuration for MS Graph client."""

    client_id: str
    tenant_id: str
    client_secret: Optional[str] = None  # For client credentials flow
    refresh_token: Optional[str] = None  # For delegated flow
    cache_file: Optional[Path] = None  # Token cache location

    @classmethod
    def from_env(cls, prefix: str = "MS_GRAPH") -> "GraphConfig":
        """Load configuration from environment variables."""
        cache_path = os.getenv(f"{prefix}_CACHE_FILE")
        return cls(
            client_id=os.environ.get(f"{prefix}_CLIENT_ID", ""),
            tenant_id=os.environ.get(f"{prefix}_TENANT_ID", ""),
            client_secret=os.environ.get(f"{prefix}_CLIENT_SECRET"),
            cache_file=Path(cache_path) if cache_path else None,
        )


class GraphClient:
    """
    Microsoft Graph API client with token management.

    Supports both client credentials (app-only) and delegated (user) flows.
    """

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, config: GraphConfig):
        """
        Initialize Graph client.

        Args:
            config: GraphConfig with credentials
        """
        self.config = config
        self._token_cache = msal.SerializableTokenCache()
        self._app: Optional[msal.ClientApplication] = None

        # Load token cache if file exists
        if config.cache_file and config.cache_file.exists():
            with open(config.cache_file) as f:
                self._token_cache.deserialize(f.read())

        # Validate we have credentials
        if not config.client_id:
            raise GraphAuthError("MS Graph client_id is required")

    @classmethod
    def from_env(cls, prefix: str = "MS_GRAPH") -> "GraphClient":
        """
        Create client from environment variables.

        Expected variables:
            {prefix}_CLIENT_ID
            {prefix}_TENANT_ID
            {prefix}_CLIENT_SECRET (for client credentials flow)
            {prefix}_CACHE_FILE (optional token cache path)
        """
        config = GraphConfig.from_env(prefix)
        return cls(config)

    @classmethod
    def from_refresh_token(
        cls,
        refresh_token: str,
        client_id: str,
        authority: str = "https://login.microsoftonline.com/organizations",
    ) -> "GraphClient":
        """
        Create client from a refresh token (delegated flow).

        Args:
            refresh_token: OAuth refresh token
            client_id: Application client ID
            authority: Azure AD authority URL
        """
        config = GraphConfig(
            client_id=client_id,
            tenant_id="organizations",  # Embedded in refresh token
            refresh_token=refresh_token,
        )
        client = cls(config)
        client._authority = authority
        return client

    @property
    def _msal_app(self) -> msal.ClientApplication:
        """Get or create MSAL application."""
        if self._app is None:
            authority = f"https://login.microsoftonline.com/{self.config.tenant_id}"

            if self.config.client_secret:
                # Confidential client (client credentials flow)
                self._app = msal.ConfidentialClientApplication(
                    self.config.client_id,
                    authority=authority,
                    client_credential=self.config.client_secret,
                    token_cache=self._token_cache,
                )
            else:
                # Public client (delegated flow with refresh token)
                self._app = msal.PublicClientApplication(
                    self.config.client_id,
                    authority=getattr(
                        self, "_authority", "https://login.microsoftonline.com/organizations"
                    ),
                    token_cache=self._token_cache,
                )

        return self._app

    def _save_cache(self):
        """Persist token cache to disk."""
        if self.config.cache_file and self._token_cache.has_state_changed:
            self.config.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.cache_file, "w") as f:
                f.write(self._token_cache.serialize())

    def _get_token(self, scopes: Optional[List[str]] = None, force_refresh: bool = False) -> str:
        """
        Get OAuth2 token for MS Graph API.

        Args:
            scopes: OAuth scopes (defaults to Graph default)
            force_refresh: Skip cache and acquire new token
        """
        scopes = scopes or ["https://graph.microsoft.com/.default"]
        result = None

        # Try cache first (unless force refresh)
        if not force_refresh:
            result = self._msal_app.acquire_token_silent(scopes, account=None)

        if not result:
            # Cache miss - acquire new token
            if self.config.client_secret:
                # Client credentials flow
                logger.info("Acquiring MS Graph token via client credentials")
                result = self._msal_app.acquire_token_for_client(scopes=scopes)
            elif self.config.refresh_token:
                # Delegated flow with refresh token
                logger.info("Acquiring MS Graph token via refresh token")
                result = self._msal_app.acquire_token_by_refresh_token(
                    self.config.refresh_token, scopes=scopes
                )
            else:
                raise GraphAuthError(
                    "No client_secret or refresh_token configured for token acquisition"
                )

        if "access_token" in result:
            self._save_cache()
            return result["access_token"]
        else:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            logger.error(f"Failed to acquire token: {error_msg}")
            raise GraphAuthError(f"MS Graph authentication failed: {error_msg}")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get HTTP headers for Graph API requests."""
        token = token or self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        _retry_auth: bool = True,
    ) -> requests.Response:
        """
        Make authenticated request to Graph API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., '/me' or '/users/{id}')
            json_data: JSON body for POST/PATCH
            params: Query parameters
            _retry_auth: Whether to retry on 401 with fresh token
        """
        url = f"{self.GRAPH_BASE_URL}{endpoint}"
        headers = self._headers()

        response = requests.request(
            method, url, headers=headers, json=json_data, params=params, timeout=30
        )

        # Handle token expiry
        if response.status_code == 401 and _retry_auth:
            logger.warning("MS Graph token expired, refreshing and retrying")
            self._get_token(force_refresh=True)
            return self._request(
                method, endpoint, json_data, params, _retry_auth=False
            )

        # Handle transient errors (let decorator retry)
        if response.status_code in RETRYABLE_STATUS_CODES:
            raise requests.exceptions.ConnectionError(
                f"HTTP {response.status_code}: {response.text}"
            )

        return response

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request to Graph API."""
        response = self._request("GET", endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict) -> requests.Response:
        """POST request to Graph API."""
        return self._request("POST", endpoint, json_data=data)

    def patch(self, endpoint: str, data: Dict) -> requests.Response:
        """PATCH request to Graph API."""
        return self._request("PATCH", endpoint, json_data=data)

    def delete(self, endpoint: str) -> requests.Response:
        """DELETE request to Graph API."""
        return self._request("DELETE", endpoint)

    # =========================================================================
    # Common API operations
    # =========================================================================

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user profile (delegated flow only)."""
        return self.get("/me")

    def get_user(self, user_id_or_email: str) -> Dict[str, Any]:
        """Get user by ID or email."""
        return self.get(f"/users/{user_id_or_email}")

    def get_user_groups(self, user_id_or_email: str) -> List[Dict[str, Any]]:
        """Get groups a user belongs to."""
        result = self.get(f"/users/{user_id_or_email}/memberOf")
        return result.get("value", [])

    def send_email(
        self,
        to: List[str],
        subject: str,
        body_html: str,
        cc: Optional[List[str]] = None,
        sender: Optional[str] = None,
        save_to_sent: bool = True,
    ) -> Dict[str, Any]:
        """
        Send an email via MS Graph API.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body_html: HTML body content
            cc: Optional CC recipients
            sender: Sender email (required for client credentials flow)
            save_to_sent: Whether to save to Sent Items

        Returns:
            Dict with 'success', 'recipients', 'error' (if failed)
        """
        sender = sender or os.getenv("MS_GRAPH_SENDER")
        if not sender:
            return {
                "success": False,
                "error": "Sender email required (set MS_GRAPH_SENDER or pass sender=)",
                "recipients": to,
            }

        message = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            },
            "saveToSentItems": save_to_sent,
        }

        if cc:
            message["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]

        try:
            response = self.post(f"/users/{sender}/sendMail", message)

            if response.status_code == 202:
                logger.info(f"Email sent successfully to {len(to)} recipients")
                return {"success": True, "recipients": to, "cc": cc or []}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to send email: {error_msg}")
                return {"success": False, "error": error_msg, "recipients": to}

        except (GraphAuthError, GraphConnectionError) as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e), "recipients": to}

    def check_connection(self) -> bool:
        """
        Check if MS Graph API is accessible and authentication works.

        Returns:
            True if connection is healthy
        """
        try:
            self._get_token()
            return True
        except (GraphAuthError, GraphConnectionError) as e:
            logger.warning(f"MS Graph health check failed: {e}")
            return False
