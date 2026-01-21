"""
Embedded OAuth credentials for public use with rate limiting.

Set these environment variables on your hosting platform:
  GOOGLE_CLIENT_ID - Your OAuth client ID
  GOOGLE_CLIENT_SECRET - Your OAuth client secret
"""

import os

# Load from environment variables
_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

EMBEDDED_CLIENT_CONFIG = {
    "installed": {
        "client_id": _client_id,
        "client_secret": _client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
    }
}

# Check if credentials are configured
CREDENTIALS_CONFIGURED = bool(_client_id and _client_secret)

# Rate limiting settings
RATE_LIMIT_PER_IP = 30  # requests per day
RATE_LIMIT_WINDOW = 86400  # 24 hours in seconds
