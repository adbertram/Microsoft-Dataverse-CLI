"""Configuration management for Dataverse CLI."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration for Dataverse API client."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file from current directory or project root
        load_dotenv()

        # Dataverse environment details
        self.dataverse_url = os.getenv("DATAVERSE_URL")
        self.environment_id = os.getenv("DATAVERSE_ENVIRONMENT_ID")

        # Azure AD / Service Principal authentication
        self.client_id = os.getenv("DATAVERSE_CLIENT_ID")
        self.client_secret = os.getenv("DATAVERSE_CLIENT_SECRET")
        self.tenant_id = os.getenv("DATAVERSE_TENANT_ID")

        # Optional: User authentication (delegated permissions)
        self.username = os.getenv("DATAVERSE_USERNAME")
        self.password = os.getenv("DATAVERSE_PASSWORD")

        # Optional: Access token (if already obtained)
        self.access_token = os.getenv("DATAVERSE_ACCESS_TOKEN")

    def has_service_principal_auth(self) -> bool:
        """Check if service principal authentication credentials are available."""
        return all([
            self.dataverse_url,
            self.client_id,
            self.client_secret,
            self.tenant_id
        ])

    def has_user_auth(self) -> bool:
        """Check if user authentication credentials are available."""
        return all([
            self.dataverse_url,
            self.client_id,
            self.tenant_id,
            self.username,
            self.password
        ])

    def has_token_auth(self) -> bool:
        """Check if access token is available."""
        return bool(self.access_token and self.dataverse_url)

    def get_missing_credentials(self) -> list[str]:
        """
        Get list of missing required credentials.

        Returns:
            List of missing environment variable names
        """
        missing = []

        # Check for token authentication first (simplest)
        if self.access_token and self.dataverse_url:
            return []  # Token auth is complete

        # Check for service principal authentication (recommended for CLI)
        if not self.dataverse_url:
            missing.append("DATAVERSE_URL")
        if not self.client_id:
            missing.append("DATAVERSE_CLIENT_ID")
        if not self.client_secret:
            missing.append("DATAVERSE_CLIENT_SECRET")
        if not self.tenant_id:
            missing.append("DATAVERSE_TENANT_ID")

        return missing

    def get_auth_scope(self) -> str:
        """Get the OAuth scope for authentication."""
        if not self.dataverse_url:
            raise ValueError("DATAVERSE_URL not configured")
        return f"{self.dataverse_url}/.default"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the global configuration instance.

    Returns:
        Config: Global configuration object
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config():
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None
