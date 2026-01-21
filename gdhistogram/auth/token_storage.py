"""Secure token storage with encryption."""

import json
import os
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from gdhistogram.config import APP_DATA_DIR, TOKENS_FILE


class TokenStorage:
    """
    Secure local storage for OAuth tokens.
    
    Tokens are encrypted using Fernet symmetric encryption.
    The encryption key is derived from a machine-specific identifier.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize token storage.
        
        Args:
            storage_path: Custom path for token file. Defaults to TOKENS_FILE.
        """
        self.storage_path = storage_path or TOKENS_FILE
        self._ensure_directory()
        self._fernet = self._create_fernet()
    
    def _ensure_directory(self) -> None:
        """Ensure the storage directory exists with secure permissions."""
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Set directory permissions (owner only on Unix)
        try:
            os.chmod(APP_DATA_DIR, 0o700)
        except (OSError, AttributeError):
            pass  # Windows doesn't support chmod the same way
    
    def _get_machine_id(self) -> bytes:
        """
        Get a machine-specific identifier for key derivation.
        
        This ensures tokens are tied to this specific machine.
        """
        # Use multiple sources for machine identification
        identifiers = []
        
        # Try to get machine ID from various sources
        try:
            # Linux
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                identifiers.append(machine_id_path.read_text().strip())
        except Exception:
            pass
        
        try:
            # macOS
            import subprocess
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                identifiers.append(result.stdout)
        except Exception:
            pass
        
        try:
            # Windows
            import subprocess
            result = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                identifiers.append(result.stdout)
        except Exception:
            pass
        
        # Fallback: use username and home directory
        identifiers.append(os.getlogin() if hasattr(os, 'getlogin') else "user")
        identifiers.append(str(Path.home()))
        
        # Combine all identifiers
        combined = "|".join(identifiers)
        return combined.encode("utf-8")
    
    def _create_fernet(self) -> Fernet:
        """Create a Fernet instance with a derived key."""
        # Use a salt stored alongside tokens (or create one)
        salt_path = APP_DATA_DIR / ".salt"
        
        if salt_path.exists():
            salt = salt_path.read_bytes()
        else:
            salt = os.urandom(16)
            salt_path.write_bytes(salt)
            try:
                os.chmod(salt_path, 0o600)
            except (OSError, AttributeError):
                pass
        
        # Derive key from machine ID
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self._get_machine_id()))
        return Fernet(key)
    
    def store_tokens(self, tokens: Dict[str, Any]) -> None:
        """
        Store tokens securely.
        
        Args:
            tokens: Dictionary containing token data (access_token, refresh_token, etc.)
        """
        # Serialize tokens
        data = json.dumps(tokens).encode("utf-8")
        
        # Encrypt
        encrypted = self._fernet.encrypt(data)
        
        # Write to file
        self.storage_path.write_bytes(encrypted)
        
        # Set file permissions (owner only)
        try:
            os.chmod(self.storage_path, 0o600)
        except (OSError, AttributeError):
            pass
    
    def load_tokens(self) -> Optional[Dict[str, Any]]:
        """
        Load stored tokens.
        
        Returns:
            Token dictionary if found and valid, None otherwise.
        """
        if not self.storage_path.exists():
            return None
        
        try:
            # Read encrypted data
            encrypted = self.storage_path.read_bytes()
            
            # Decrypt
            decrypted = self._fernet.decrypt(encrypted)
            
            # Parse JSON
            return json.loads(decrypted.decode("utf-8"))
        
        except Exception:
            # Token file corrupted or from different machine
            return None
    
    def clear_tokens(self) -> None:
        """Remove stored tokens."""
        if self.storage_path.exists():
            # Overwrite with random data before deleting
            try:
                self.storage_path.write_bytes(os.urandom(1024))
            except Exception:
                pass
            
            self.storage_path.unlink(missing_ok=True)
    
    def has_tokens(self) -> bool:
        """Check if tokens are stored."""
        return self.storage_path.exists()
