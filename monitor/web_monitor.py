"""Fetch real usage data from claude.ai API using Chrome session cookies."""

import json
import os
import glob
import urllib.request
import urllib.error
import http.cookiejar
from datetime import datetime, timezone
from typing import Any


class WebMonitorError(Exception):
    """Raised when web monitoring fails."""


class WebMonitor:
    """Fetches usage data from claude.ai using Chrome session cookies."""

    CHROME_DIR = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome"
    )
    PROFILES = ["Default", "Profile 1", "Profile 2", "Profile 3",
                "Profile 4", "Profile 5", "Profile 6"]
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self):
        self._cookie_jar: http.cookiejar.CookieJar | None = None
        self._opener: urllib.request.OpenerDirector | None = None
        self._org_uuid: str | None = None
        self._cookie_profile: str | None = None

    def _find_chrome_profile(self) -> str | None:
        """Find the Chrome profile that has a claude.ai sessionKey cookie."""
        try:
            import browser_cookie3
        except ImportError:
            raise WebMonitorError(
                "browser_cookie3 not installed. Run: pip install browser_cookie3"
            )

        for profile in self.PROFILES:
            cookie_file = os.path.join(self.CHROME_DIR, profile, "Cookies")
            if not os.path.exists(cookie_file):
                continue
            try:
                cj = browser_cookie3.chrome(
                    domain_name="claude.ai", cookie_file=cookie_file
                )
                for c in cj:
                    if c.name == "sessionKey" and c.value:
                        return profile
            except Exception:
                continue
        return None

    def _load_cookies(self) -> None:
        """Load cookies from the detected Chrome profile."""
        try:
            import browser_cookie3
        except ImportError:
            raise WebMonitorError(
                "browser_cookie3 not installed. Run: pip install browser_cookie3"
            )

        if self._cookie_profile is None:
            self._cookie_profile = self._find_chrome_profile()
        if self._cookie_profile is None:
            raise WebMonitorError(
                "No Chrome profile found with claude.ai session. "
                "Please log in to claude.ai in Chrome first."
            )

        cookie_file = os.path.join(
            self.CHROME_DIR, self._cookie_profile, "Cookies"
        )
        self._cookie_jar = browser_cookie3.chrome(
            domain_name="claude.ai", cookie_file=cookie_file
        )
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )

    def _api_get(self, path: str) -> Any:
        """Make an authenticated GET request to claude.ai API."""
        if self._opener is None:
            self._load_cookies()

        url = f"https://claude.ai{path}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json",
            },
        )
        try:
            with self._opener.open(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                # Session expired — try reloading cookies
                self._cookie_profile = None
                self._opener = None
                raise WebMonitorError(
                    f"Session expired (HTTP {e.code}). "
                    "Please refresh claude.ai in Chrome."
                )
            raise WebMonitorError(f"API error (HTTP {e.code})")
        except urllib.error.URLError as e:
            raise WebMonitorError(f"Network error: {e.reason}")

    def _detect_org_uuid(self) -> str:
        """Auto-detect the organization UUID."""
        if self._org_uuid:
            return self._org_uuid

        orgs = self._api_get("/api/organizations")
        if isinstance(orgs, list) and len(orgs) > 0:
            self._org_uuid = orgs[0]["uuid"]
            return self._org_uuid
        raise WebMonitorError("No organizations found")

    def get_usage(self) -> dict[str, Any]:
        """Fetch usage data from claude.ai API.

        Returns:
            Dict with usage utilization percentages and reset times.
        """
        org_uuid = self._detect_org_uuid()
        data = self._api_get(f"/api/organizations/{org_uuid}/usage")

        result: dict[str, Any] = {"source": "claude.ai"}

        # Parse five_hour (current session)
        five_hour = data.get("five_hour")
        if five_hour:
            result["session_pct"] = five_hour.get("utilization", 0)
            result["session_resets_at"] = self._parse_dt(
                five_hour.get("resets_at")
            )

        # Parse seven_day (all models weekly)
        seven_day = data.get("seven_day")
        if seven_day:
            result["weekly_pct"] = seven_day.get("utilization", 0)
            result["weekly_resets_at"] = self._parse_dt(
                seven_day.get("resets_at")
            )

        # Parse seven_day_sonnet (sonnet-only weekly)
        sonnet = data.get("seven_day_sonnet")
        if sonnet:
            result["sonnet_pct"] = sonnet.get("utilization", 0)
            result["sonnet_resets_at"] = self._parse_dt(
                sonnet.get("resets_at")
            )

        # Parse extra_usage if present
        extra = data.get("extra_usage")
        if extra and isinstance(extra, dict):
            result["extra_spent"] = extra.get("spent", 0)
            result["extra_limit"] = extra.get("limit", 0)
            result["extra_pct"] = extra.get("utilization", 0)

        return result

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        """Parse an ISO datetime string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
