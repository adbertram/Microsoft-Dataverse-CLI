"""Dataverse API client factory and wrapper."""
import requests
from typing import Optional, Dict, Any
from msal import ConfidentialClientApplication, PublicClientApplication
from .config import get_config


# Global client instance
_client: Optional['DataverseClient'] = None


class ClientError(Exception):
    """Exception raised for client initialization or API errors."""
    pass


class DataverseClient:
    """
    Client for interacting with Microsoft Dataverse Web API.

    Handles authentication, API requests, and response handling.
    """

    def __init__(self, dataverse_url: str, access_token: str):
        """
        Initialize Dataverse client.

        Args:
            dataverse_url: Base URL for Dataverse environment
            access_token: OAuth access token for authentication
        """
        self.dataverse_url = dataverse_url.rstrip('/')
        self.access_token = access_token
        self.api_base = f"{self.dataverse_url}/api/data/v9.2"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
        })

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the Dataverse API.

        Args:
            endpoint: API endpoint (e.g., 'workflows', 'solutions')
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            ClientError: If the request fails
        """
        url = f"{self.api_base}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            raise ClientError(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise ClientError(f"Request failed: {e}")

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the Dataverse API.

        Args:
            endpoint: API endpoint
            data: JSON data to send

        Returns:
            JSON response as dictionary

        Raises:
            ClientError: If the request fails
        """
        url = f"{self.api_base}/{endpoint}"
        self.session.headers["Content-Type"] = "application/json"
        self.session.headers["Prefer"] = "return=representation"

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()

            # Handle 204 No Content responses
            if response.status_code == 204:
                # Extract entity ID from OData-EntityId header
                entity_id_header = response.headers.get("OData-EntityId", "")
                if entity_id_header and "(" in entity_id_header:
                    entity_id = entity_id_header.split("(")[1].split(")")[0]
                    return {"id": entity_id}
                return {}

            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            raise ClientError(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise ClientError(f"Request failed: {e}")

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PATCH request to the Dataverse API.

        Args:
            endpoint: API endpoint
            data: JSON data to send

        Returns:
            JSON response as dictionary

        Raises:
            ClientError: If the request fails
        """
        url = f"{self.api_base}/{endpoint}"
        self.session.headers["Content-Type"] = "application/json"

        try:
            response = self.session.patch(url, json=data)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            raise ClientError(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise ClientError(f"Request failed: {e}")

    def delete(self, endpoint: str) -> None:
        """
        Make a DELETE request to the Dataverse API.

        Args:
            endpoint: API endpoint

        Raises:
            ClientError: If the request fails
        """
        url = f"{self.api_base}/{endpoint}"

        try:
            response = self.session.delete(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ClientError(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise ClientError(f"Request failed: {e}")


def _get_service_principal_token(config) -> str:
    """
    Get access token using service principal (client credentials flow).

    Args:
        config: Configuration object

    Returns:
        Access token string

    Raises:
        ClientError: If authentication fails
    """
    authority = f"https://login.microsoftonline.com/{config.tenant_id}"
    app = ConfidentialClientApplication(
        config.client_id,
        authority=authority,
        client_credential=config.client_secret,
    )

    scope = [config.get_auth_scope()]
    result = app.acquire_token_for_client(scopes=scope)

    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise ClientError(f"Failed to acquire token: {error}")

    return result["access_token"]


def _get_user_token(config) -> str:
    """
    Get access token using username/password (resource owner password credentials flow).

    Args:
        config: Configuration object

    Returns:
        Access token string

    Raises:
        ClientError: If authentication fails
    """
    authority = f"https://login.microsoftonline.com/{config.tenant_id}"
    app = PublicClientApplication(
        config.client_id,
        authority=authority,
    )

    scope = [config.get_auth_scope()]
    result = app.acquire_token_by_username_password(
        config.username,
        config.password,
        scopes=scope
    )

    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise ClientError(f"Failed to acquire token: {error}")

    return result["access_token"]


def get_client() -> DataverseClient:
    """
    Get or create the global Dataverse API client.

    Returns:
        DataverseClient: Authenticated Dataverse API client

    Raises:
        ClientError: If credentials are missing or authentication fails
    """
    global _client

    if _client is not None:
        return _client

    config = get_config()

    # Check for missing credentials
    missing = config.get_missing_credentials()
    if missing:
        error_msg = (
            "Missing required Dataverse credentials. Please set the following "
            "environment variables:\n\n"
        )
        for cred in missing:
            error_msg += f"  - {cred}\n"

        error_msg += "\nFor service principal authentication (recommended for CLI):\n"
        error_msg += "  DATAVERSE_URL, DATAVERSE_CLIENT_ID, DATAVERSE_CLIENT_SECRET, DATAVERSE_TENANT_ID\n"
        error_msg += "\nFor user authentication:\n"
        error_msg += "  DATAVERSE_URL, DATAVERSE_CLIENT_ID, DATAVERSE_TENANT_ID, DATAVERSE_USERNAME, DATAVERSE_PASSWORD\n"
        error_msg += "\nFor token authentication (if you already have a token):\n"
        error_msg += "  DATAVERSE_URL, DATAVERSE_ACCESS_TOKEN\n"

        raise ClientError(error_msg)

    # Try token authentication first (simplest)
    if config.has_token_auth():
        _client = DataverseClient(config.dataverse_url, config.access_token)
        return _client

    # Try service principal authentication (recommended for CLI)
    if config.has_service_principal_auth():
        try:
            access_token = _get_service_principal_token(config)
            _client = DataverseClient(config.dataverse_url, access_token)
            return _client
        except Exception as e:
            raise ClientError(f"Failed to authenticate with service principal: {e}")

    # Try user authentication
    if config.has_user_auth():
        try:
            access_token = _get_user_token(config)
            _client = DataverseClient(config.dataverse_url, access_token)
            return _client
        except Exception as e:
            raise ClientError(f"Failed to authenticate with user credentials: {e}")

    # This shouldn't happen if get_missing_credentials() works correctly
    raise ClientError("No valid authentication method available")


def reset_client():
    """Reset the global client instance (useful for testing)."""
    global _client
    _client = None
