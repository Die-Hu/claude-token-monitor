"""OAuth credential management with auto-refresh."""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from claude_token_monitor.platform.auth import CredentialReader, CredentialError


# Re-export CredentialError as AuthError for backward compatibility
AuthError = CredentialError


class AuthManager:
    """Manages OAuth tokens with auto-refresh."""

    REFRESH_URL = "https://console.anthropic.com/v1/oauth/token"

    def __init__(self):
        self._cached_token: str | None = None
        self._cached_refresh_token: str | None = None
        self._expires_at: float = 0
        self._subscription_type: str = ""
        self._rate_limit_tier: str = ""
        self._credential_reader = CredentialReader()

    def _is_expired(self) -> bool:
        """Check if the cached token is expired (with 60s buffer)."""
        if not self._cached_token:
            return True
        return time.time() >= (self._expires_at - 60)

    def _refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._cached_refresh_token:
            raise CredentialError("No refresh token available")

        body = json.dumps(
            {
                "grant_type": "refresh_token",
                "refresh_token": self._cached_refresh_token,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self.REFRESH_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise CredentialError(
                f"Token refresh failed (HTTP {e.code}): {e.read().decode()}"
            )
        except urllib.error.URLError as e:
            raise CredentialError(f"Token refresh network error: {e.reason}")
        except json.JSONDecodeError:
            raise CredentialError("Token refresh returned invalid JSON")

        if "access_token" in data:
            self._cached_token = data["access_token"]
            self._cached_refresh_token = data.get(
                "refresh_token", self._cached_refresh_token
            )
            expires_in = data.get("expires_in", 3600)
            self._expires_at = time.time() + expires_in
        elif "accessToken" in data:
            self._cached_token = data["accessToken"]
            self._cached_refresh_token = data.get(
                "refreshToken", self._cached_refresh_token
            )
            self._expires_at = data.get("expiresAt", time.time() + 3600)
        else:
            raise CredentialError("Token refresh response missing access token")

    def _load_credentials(self) -> None:
        """Load credentials from the platform credential store."""
        data = self._credential_reader.read()
        self._cached_token = data["accessToken"]
        self._cached_refresh_token = data["refreshToken"]
        self._subscription_type = data.get("subscriptionType", "")
        self._rate_limit_tier = data.get("rateLimitTier", "")

        expires_at = data["expiresAt"]
        if isinstance(expires_at, str):
            try:
                dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                self._expires_at = dt.timestamp()
            except ValueError:
                self._expires_at = float(expires_at)
        else:
            ts = float(expires_at)
            # If timestamp > 1e12, it's milliseconds — convert to seconds
            if ts > 1e12:
                ts = ts / 1000.0
            self._expires_at = ts

    def get_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        if self._is_expired():
            try:
                self._load_credentials()
            except CredentialError:
                if self._cached_refresh_token:
                    self._refresh_token()
                    return self._cached_token
                raise

            if self._is_expired() and self._cached_refresh_token:
                self._refresh_token()

        return self._cached_token

    @property
    def subscription_type(self) -> str:
        if not self._subscription_type:
            try:
                self._load_credentials()
            except CredentialError:
                pass
        return self._subscription_type

    @property
    def rate_limit_tier(self) -> str:
        if not self._rate_limit_tier:
            try:
                self._load_credentials()
            except CredentialError:
                pass
        return self._rate_limit_tier


# Module-level singleton
_auth_manager = AuthManager()


def get_token() -> str:
    """Get a valid OAuth access token (module-level convenience function)."""
    return _auth_manager.get_token()


def get_auth_manager() -> AuthManager:
    """Get the singleton AuthManager instance."""
    return _auth_manager
