"""Cross-platform credential reading for Claude Code OAuth tokens."""

import json
import subprocess
import sys


class CredentialError(Exception):
    """Raised when credential reading fails."""


class CredentialReader:
    """Reads Claude Code credentials from the platform keychain/credential store."""

    KEYCHAIN_SERVICE = "Claude Code-credentials"

    def read(self) -> dict:
        """Read credentials from the platform credential store.

        Returns:
            Dict with keys: accessToken, refreshToken, expiresAt,
            subscriptionType, rateLimitTier.

        Raises:
            CredentialError: If credentials cannot be read.
        """
        if sys.platform == "darwin":
            return self._read_macos()
        elif sys.platform == "win32":
            return self._read_windows()
        else:
            return self._read_linux()

    def _read_macos(self) -> dict:
        """Read from macOS Keychain using the security CLI."""
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", self.KEYCHAIN_SERVICE, "-w"],
                capture_output=True, text=True, timeout=10,
            )
        except FileNotFoundError:
            raise CredentialError("'security' command not found. Are you on macOS?")
        except subprocess.TimeoutExpired:
            raise CredentialError("Keychain read timed out")

        if result.returncode != 0:
            raise CredentialError(
                f"Keychain item '{self.KEYCHAIN_SERVICE}' not found: {result.stderr.strip()}"
            )

        raw = result.stdout.strip()
        if not raw:
            raise CredentialError("Keychain returned empty credentials")

        return self._parse_json(raw)

    def _read_windows(self) -> dict:
        """Read from Windows credential store using keyring library."""
        try:
            import keyring
        except ImportError:
            raise CredentialError("keyring not installed. Run: pip install keyring")

        raw = keyring.get_password(self.KEYCHAIN_SERVICE, "credentials")
        if not raw:
            # Fallback: try reading from Claude config file
            return self._read_config_file()

        return self._parse_json(raw)

    def _read_linux(self) -> dict:
        """Read from Linux keyring using keyring library."""
        try:
            import keyring
        except ImportError:
            raise CredentialError("keyring not installed. Run: pip install keyring")

        raw = keyring.get_password(self.KEYCHAIN_SERVICE, "credentials")
        if not raw:
            return self._read_config_file()

        return self._parse_json(raw)

    def _read_config_file(self) -> dict:
        """Fallback: read credentials from Claude config directory."""
        import os
        from claude_token_monitor.platform.paths import claude_config_dir

        config_path = os.path.join(claude_config_dir(), ".credentials.json")
        if not os.path.exists(config_path):
            raise CredentialError(
                f"No credentials found in keyring or {config_path}"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except OSError as e:
            raise CredentialError(f"Failed to read credentials file: {e}")

        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict:
        """Parse and validate credential JSON."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CredentialError(f"Invalid JSON in credentials: {e}")

        # Unwrap nested structure: {"claudeAiOauth": {...actual creds...}}
        if "claudeAiOauth" in data and isinstance(data["claudeAiOauth"], dict):
            data = data["claudeAiOauth"]

        required = ["accessToken", "refreshToken", "expiresAt"]
        for key in required:
            if key not in data:
                raise CredentialError(f"Missing required field '{key}' in credentials")

        return data
