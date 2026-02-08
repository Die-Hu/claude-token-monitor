"""OS-aware paths for Chrome, Claude config, and credentials."""

import os
import sys


def chrome_user_data_dir() -> str:
    """Return the Chrome User Data directory for the current platform."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif sys.platform == "win32":
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    else:
        # Linux
        return os.path.expanduser("~/.config/google-chrome")


def chrome_cookie_file(profile: str = "Default") -> str:
    """Return the path to Chrome's Cookies database for a given profile."""
    return os.path.join(chrome_user_data_dir(), profile, "Cookies")


def chrome_profiles() -> list[str]:
    """Return list of Chrome profile directory names to scan."""
    return ["Default", "Profile 1", "Profile 2", "Profile 3",
            "Profile 4", "Profile 5", "Profile 6"]


def claude_config_dir() -> str:
    """Return the Claude CLI config directory."""
    # Claude CLI uses ~/.claude on all platforms
    return os.path.expanduser("~/.claude")
