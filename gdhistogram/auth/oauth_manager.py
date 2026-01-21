"""OAuth 2.0 manager for Google APIs."""

import json
import webbrowser
from pathlib import Path
from typing import Optional, Tuple, Callable
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from gdhistogram.config import SCOPES
from gdhistogram.auth.token_storage import TokenStorage


@dataclass
class OAuthClientInfo:
    """Information about an OAuth client configuration."""
    client_id: str
    project_id: str
    is_desktop_app: bool
    
    @property
    def is_valid(self) -> bool:
        """Check if this is a valid desktop OAuth client."""
        return bool(self.client_id and self.project_id and self.is_desktop_app)


class OAuthValidationError(Exception):
    """Error during OAuth client validation."""
    pass


class OAuthManager:
    """
    Manages OAuth 2.0 authentication for Google APIs.
    
    This class handles:
    - Validating user-provided OAuth client credentials
    - Running the OAuth flow (browser-based)
    - Storing and refreshing tokens
    - Providing valid credentials for API calls
    """
    
    def __init__(self, token_storage: Optional[TokenStorage] = None):
        """
        Initialize OAuth manager.
        
        Args:
            token_storage: Token storage instance. Creates default if not provided.
        """
        self.token_storage = token_storage or TokenStorage()
        self._credentials: Optional[Credentials] = None
        self._client_config: Optional[dict] = None
        self._client_secrets_path: Optional[Path] = None
    
    @staticmethod
    def validate_client_secrets(file_path: Path) -> Tuple[bool, str, Optional[OAuthClientInfo]]:
        """
        Validate an OAuth client secrets file.
        
        Args:
            file_path: Path to the client_secret.json file.
        
        Returns:
            Tuple of (is_valid, message, client_info)
        """
        if not file_path.exists():
            return False, "File not found", None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}", None
        except Exception as e:
            return False, f"Cannot read file: {e}", None
        
        # Check for installed app configuration
        if "installed" not in data:
            if "web" in data:
                return False, "This is a web application OAuth client. Please create a Desktop application client.", None
            return False, "Invalid OAuth client file. Missing 'installed' configuration.", None
        
        installed = data["installed"]
        
        # Validate required fields
        required_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
        missing = [f for f in required_fields if f not in installed]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}", None
        
        # Extract info
        client_info = OAuthClientInfo(
            client_id=installed.get("client_id", ""),
            project_id=installed.get("project_id", "unknown"),
            is_desktop_app=True
        )
        
        # Validate client ID format
        if not client_info.client_id.endswith(".apps.googleusercontent.com"):
            return False, "Invalid client ID format", None
        
        return True, "Valid OAuth client configuration", client_info
    
    def set_client_secrets(self, file_path: Path) -> None:
        """
        Set the client secrets file to use.
        
        Args:
            file_path: Path to validated client_secret.json file.
        
        Raises:
            OAuthValidationError: If the file is invalid.
        """
        is_valid, message, _ = self.validate_client_secrets(file_path)
        if not is_valid:
            raise OAuthValidationError(message)
        
        self._client_secrets_path = file_path
        
        with open(file_path, "r", encoding="utf-8") as f:
            self._client_config = json.load(f)
    
    def has_valid_credentials(self) -> bool:
        """
        Check if we have valid (non-expired) credentials.
        
        Returns:
            True if credentials exist and are valid.
        """
        creds = self._get_cached_credentials()
        return creds is not None and creds.valid
    
    def needs_refresh(self) -> bool:
        """
        Check if credentials need to be refreshed.
        
        Returns:
            True if credentials exist but are expired (and can be refreshed).
        """
        creds = self._get_cached_credentials()
        if creds is None:
            return False
        return creds.expired and creds.refresh_token is not None
    
    def _get_cached_credentials(self) -> Optional[Credentials]:
        """Load credentials from storage."""
        if self._credentials is not None:
            return self._credentials
        
        token_data = self.token_storage.load_tokens()
        if token_data is None:
            return None
        
        try:
            self._credentials = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes"),
            )
            return self._credentials
        except Exception:
            return None
    
    def get_credentials(self) -> Optional[Credentials]:
        """
        Get valid credentials, refreshing if necessary.
        
        Returns:
            Valid Credentials object, or None if not authenticated.
        """
        creds = self._get_cached_credentials()
        
        if creds is None:
            return None
        
        if creds.valid:
            return creds
        
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
                return creds
            except RefreshError:
                # Refresh token revoked or expired
                self.logout()
                return None
        
        return None
    
    def _save_credentials(self, creds: Credentials) -> None:
        """Save credentials to storage."""
        self._credentials = creds
        
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }
        
        self.token_storage.store_tokens(token_data)
    
    def run_oauth_flow(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Run the OAuth authorization flow.
        
        This will open a browser for the user to authorize the application.
        
        Args:
            progress_callback: Optional callback for status updates.
        
        Returns:
            True if authorization succeeded, False otherwise.
        
        Raises:
            OAuthValidationError: If client secrets not configured.
        """
        if self._client_config is None:
            raise OAuthValidationError("Client secrets not configured. Call set_client_secrets() first.")
        
        if progress_callback:
            progress_callback("Starting OAuth flow...")
        
        try:
            flow = InstalledAppFlow.from_client_config(
                self._client_config,
                scopes=SCOPES
            )
            
            if progress_callback:
                progress_callback("Opening browser for authorization...")
            
            # Run local server flow
            # This opens the browser and waits for the callback
            creds = flow.run_local_server(
                port=0,  # Use any available port
                prompt="consent",  # Always show consent screen
                open_browser=True
            )
            
            if progress_callback:
                progress_callback("Authorization successful!")
            
            self._save_credentials(creds)
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Authorization failed: {e}")
            return False
    
    def get_scopes_display(self) -> list[str]:
        """
        Get human-readable scope descriptions.
        
        Returns:
            List of scope descriptions.
        """
        scope_descriptions = {
            "https://www.googleapis.com/auth/drive.readonly": "View files in Google Drive (read-only)",
            "https://www.googleapis.com/auth/documents.readonly": "View Google Docs documents (read-only)",
        }
        
        return [scope_descriptions.get(s, s) for s in SCOPES]
    
    def logout(self) -> None:
        """Clear stored credentials and log out."""
        self.token_storage.clear_tokens()
        self._credentials = None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.
        
        Returns:
            True if authenticated with valid credentials.
        """
        return self.get_credentials() is not None
