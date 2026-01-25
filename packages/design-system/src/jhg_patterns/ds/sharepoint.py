"""
SharePoint REST API patterns for JHG Flask applications.

Provides access to SharePoint lists, files, and folders via MS Graph.

Usage:
    from jhg_patterns.ds.sharepoint import SharePointClient

    # From Graph client
    client = SharePointClient.from_graph(graph_client, site_url="https://johnholland.sharepoint.com/sites/MySite")

    # List items
    items = client.get_list_items("MyList")

    # Download file
    content = client.download_file("/Shared Documents/report.xlsx")

    # Using refresh token (for Databricks notebooks)
    client = SharePointClient.from_refresh_token(
        refresh_token=dbutils.secrets.get("scope", "refresh_token"),
        client_id="...",
        site_url="https://johnholland.sharepoint.com/sites/MySite"
    )
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .graph import GraphClient, GraphConfig, GraphError

logger = logging.getLogger(__name__)


class SharePointError(GraphError):
    """Base exception for SharePoint errors."""

    pass


class SharePointNotFoundError(SharePointError):
    """Raised when a SharePoint resource is not found."""

    pass


@dataclass
class SharePointFile:
    """Represents a SharePoint file."""

    name: str
    server_relative_url: str
    modified: str
    size: int
    web_url: Optional[str] = None

    @classmethod
    def from_graph(cls, data: Dict) -> "SharePointFile":
        """Create from Graph API response."""
        return cls(
            name=data.get("name", ""),
            server_relative_url=data.get("webUrl", ""),
            modified=data.get("lastModifiedDateTime", ""),
            size=int(data.get("size", 0)),
            web_url=data.get("webUrl"),
        )

    @classmethod
    def from_rest(cls, data: Dict) -> "SharePointFile":
        """Create from SharePoint REST API response."""
        return cls(
            name=data.get("Name", ""),
            server_relative_url=data.get("ServerRelativeUrl", ""),
            modified=data.get("TimeLastModified", ""),
            size=int(data.get("Length", 0)),
        )


@dataclass
class SharePointFolder:
    """Represents a SharePoint folder."""

    name: str
    server_relative_url: str

    @classmethod
    def from_graph(cls, data: Dict) -> "SharePointFolder":
        """Create from Graph API response."""
        return cls(
            name=data.get("name", ""),
            server_relative_url=data.get("webUrl", ""),
        )

    @classmethod
    def from_rest(cls, data: Dict) -> "SharePointFolder":
        """Create from SharePoint REST API response."""
        return cls(
            name=data.get("Name", ""),
            server_relative_url=data.get("ServerRelativeUrl", ""),
        )


class SharePointClient:
    """
    SharePoint client using MS Graph API.

    Provides high-level access to SharePoint sites, lists, and files.
    """

    def __init__(self, graph_client: GraphClient, site_url: str):
        """
        Initialize SharePoint client.

        Args:
            graph_client: Authenticated GraphClient instance
            site_url: SharePoint site URL (e.g., https://tenant.sharepoint.com/sites/MySite)
        """
        self.graph = graph_client
        self.site_url = site_url.rstrip("/")
        self._site_id: Optional[str] = None
        self._drive_id: Optional[str] = None

    @classmethod
    def from_graph(cls, graph_client: GraphClient, site_url: str) -> "SharePointClient":
        """Create client from existing Graph client."""
        return cls(graph_client, site_url)

    @classmethod
    def from_env(cls, site_url: str, graph_prefix: str = "MS_GRAPH") -> "SharePointClient":
        """
        Create client from environment variables.

        Args:
            site_url: SharePoint site URL
            graph_prefix: Prefix for MS Graph env vars
        """
        graph = GraphClient.from_env(graph_prefix)
        return cls(graph, site_url)

    @classmethod
    def from_refresh_token(
        cls,
        refresh_token: str,
        client_id: str,
        site_url: str,
    ) -> "SharePointClient":
        """
        Create client from refresh token (useful for Databricks notebooks).

        Args:
            refresh_token: OAuth refresh token
            client_id: Application client ID
            site_url: SharePoint site URL
        """
        graph = GraphClient.from_refresh_token(refresh_token, client_id)
        return cls(graph, site_url)

    @property
    def site_id(self) -> str:
        """Get SharePoint site ID (cached)."""
        if self._site_id is None:
            self._site_id = self._get_site_id()
        return self._site_id

    @property
    def drive_id(self) -> str:
        """Get default document library drive ID (cached)."""
        if self._drive_id is None:
            self._drive_id = self._get_drive_id()
        return self._drive_id

    def _get_site_id(self) -> str:
        """Resolve site URL to site ID."""
        # Extract hostname and path from site URL
        # https://tenant.sharepoint.com/sites/MySite -> tenant.sharepoint.com:/sites/MySite
        from urllib.parse import urlparse

        parsed = urlparse(self.site_url)
        site_path = f"{parsed.netloc}:{parsed.path}"

        try:
            result = self.graph.get(f"/sites/{site_path}")
            return result["id"]
        except Exception as e:
            raise SharePointError(f"Could not resolve site: {self.site_url}") from e

    def _get_drive_id(self) -> str:
        """Get default document library drive ID."""
        result = self.graph.get(f"/sites/{self.site_id}/drive")
        return result["id"]

    # =========================================================================
    # List Operations
    # =========================================================================

    def get_lists(self) -> List[Dict[str, Any]]:
        """Get all lists in the site."""
        result = self.graph.get(f"/sites/{self.site_id}/lists")
        return result.get("value", [])

    def get_list(self, list_name: str) -> Dict[str, Any]:
        """Get list metadata by name."""
        result = self.graph.get(f"/sites/{self.site_id}/lists/{list_name}")
        return result

    def get_list_items(
        self,
        list_name: str,
        select: Optional[List[str]] = None,
        filter_query: Optional[str] = None,
        expand: Optional[List[str]] = None,
        top: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get items from a SharePoint list.

        Args:
            list_name: Name of the list
            select: Fields to select (e.g., ["Title", "Status"])
            filter_query: OData filter (e.g., "Status eq 'Active'")
            expand: Fields to expand (e.g., ["fields"])
            top: Maximum items to return

        Returns:
            List of items with their fields
        """
        params = {}

        if select:
            params["$select"] = ",".join(select)
        if filter_query:
            params["$filter"] = filter_query
        if expand:
            params["$expand"] = ",".join(expand)
        if top:
            params["$top"] = str(top)

        # Always expand fields to get column values
        if "fields" not in (expand or []):
            params["$expand"] = params.get("$expand", "") + ",fields"
            params["$expand"] = params["$expand"].lstrip(",")

        result = self.graph.get(
            f"/sites/{self.site_id}/lists/{list_name}/items", params=params
        )
        return result.get("value", [])

    def create_list_item(self, list_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new list item.

        Args:
            list_name: Name of the list
            fields: Field values for the new item

        Returns:
            Created item data
        """
        response = self.graph.post(
            f"/sites/{self.site_id}/lists/{list_name}/items",
            {"fields": fields},
        )
        response.raise_for_status()
        return response.json()

    def update_list_item(
        self, list_name: str, item_id: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a list item.

        Args:
            list_name: Name of the list
            item_id: ID of the item to update
            fields: Field values to update

        Returns:
            Updated item data
        """
        response = self.graph.patch(
            f"/sites/{self.site_id}/lists/{list_name}/items/{item_id}/fields",
            fields,
        )
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # File Operations
    # =========================================================================

    def list_folder(
        self, folder_path: str = "/", include_subfolders: bool = False
    ) -> Dict[str, List]:
        """
        List files and folders in a SharePoint folder.

        Args:
            folder_path: Path relative to document library root (e.g., "/Reports/2024")
            include_subfolders: If True, recursively include subfolder contents

        Returns:
            Dict with 'files' and 'folders' lists
        """
        folder_path = folder_path.strip("/")

        if folder_path:
            endpoint = f"/sites/{self.site_id}/drive/root:/{folder_path}:/children"
        else:
            endpoint = f"/sites/{self.site_id}/drive/root/children"

        result = self.graph.get(endpoint)
        items = result.get("value", [])

        files = []
        folders = []

        for item in items:
            if "folder" in item:
                folders.append(SharePointFolder.from_graph(item))
            else:
                files.append(SharePointFile.from_graph(item))

        if include_subfolders:
            for folder in folders[:]:  # Copy to avoid modification during iteration
                subfolder_path = f"{folder_path}/{folder.name}" if folder_path else folder.name
                sub_result = self.list_folder(subfolder_path, include_subfolders=True)
                files.extend(sub_result["files"])
                folders.extend(sub_result["folders"])

        return {"files": files, "folders": folders}

    def list_files_recursive(
        self, folder_path: str = "/", extension_filter: Optional[str] = None
    ) -> List[SharePointFile]:
        """
        List all files in a folder recursively.

        Args:
            folder_path: Starting folder path
            extension_filter: Optional file extension filter (e.g., ".xlsx")

        Returns:
            List of SharePointFile objects
        """
        result = self.list_folder(folder_path, include_subfolders=True)
        files = result["files"]

        if extension_filter:
            ext = extension_filter.lower()
            files = [f for f in files if f.name.lower().endswith(ext)]

        return files

    def download_file(self, file_path: str) -> bytes:
        """
        Download file content from SharePoint.

        Args:
            file_path: Path relative to document library root

        Returns:
            File content as bytes
        """
        file_path = file_path.strip("/")
        endpoint = f"/sites/{self.site_id}/drive/root:/{file_path}:/content"

        # Use raw request to get bytes
        import requests

        response = requests.get(
            f"{self.graph.GRAPH_BASE_URL}{endpoint}",
            headers=self.graph._headers(),
            timeout=60,
        )
        response.raise_for_status()
        return response.content

    def upload_file(
        self, file_path: str, content: bytes, conflict_behavior: str = "replace"
    ) -> Dict[str, Any]:
        """
        Upload file to SharePoint.

        Args:
            file_path: Destination path relative to document library root
            content: File content as bytes
            conflict_behavior: "replace", "rename", or "fail"

        Returns:
            Upload result with file metadata
        """
        file_path = file_path.strip("/")
        endpoint = f"/sites/{self.site_id}/drive/root:/{file_path}:/content"

        import requests

        params = {"@microsoft.graph.conflictBehavior": conflict_behavior}

        response = requests.put(
            f"{self.graph.GRAPH_BASE_URL}{endpoint}",
            headers={
                **self.graph._headers(),
                "Content-Type": "application/octet-stream",
            },
            params=params,
            data=content,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    def folder_exists(self, folder_path: str) -> bool:
        """
        Check if a folder exists.

        Args:
            folder_path: Path relative to document library root

        Returns:
            True if folder exists
        """
        folder_path = folder_path.strip("/")

        try:
            self.graph.get(f"/sites/{self.site_id}/drive/root:/{folder_path}")
            return True
        except Exception:
            return False

    def create_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Create a folder (including parent folders if needed).

        Args:
            folder_path: Path relative to document library root

        Returns:
            Folder metadata
        """
        folder_path = folder_path.strip("/")
        parts = folder_path.split("/")

        # Create each folder in the path
        current_path = ""
        result = None

        for part in parts:
            parent_path = current_path or "root"
            current_path = f"{current_path}/{part}" if current_path else part

            if not self.folder_exists(current_path):
                if parent_path == "root":
                    endpoint = f"/sites/{self.site_id}/drive/root/children"
                else:
                    endpoint = f"/sites/{self.site_id}/drive/root:/{parent_path}:/children"

                response = self.graph.post(
                    endpoint,
                    {
                        "name": part,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "fail",
                    },
                )
                result = response.json() if response.ok else None

        return result or self.graph.get(f"/sites/{self.site_id}/drive/root:/{folder_path}")

    def check_connection(self) -> bool:
        """
        Check if SharePoint is accessible.

        Returns:
            True if connection is healthy
        """
        try:
            self._get_site_id()
            return True
        except Exception as e:
            logger.warning(f"SharePoint health check failed: {e}")
            return False
