"""Combined monitoring: web API (primary) + local logs (supplementary)."""

from datetime import datetime, timezone
from typing import Any

from monitor.auth import get_auth_manager
from monitor.web_monitor import WebMonitor, WebMonitorError
from monitor.log_monitor import LogMonitor


class CombinedMonitor:
    """Fetches real usage data from claude.ai, supplemented by local logs."""

    def __init__(self):
        self._web_monitor = WebMonitor()
        self._log_monitor = LogMonitor()
        self._auth_manager = get_auth_manager()
        self._last_result: dict[str, Any] | None = None

    def refresh(self) -> dict[str, Any]:
        """Fetch fresh data from claude.ai API and local logs.

        Returns:
            Unified dict with all monitoring data.
        """
        error_parts: list[str] = []

        # --- Primary: real usage from claude.ai API ---
        web_data: dict[str, Any] = {}
        try:
            web_data = self._web_monitor.get_usage()
        except WebMonitorError as e:
            error_parts.append(f"Web: {e}")
        except Exception as e:
            error_parts.append(f"Web: {e}")

        # --- Supplementary: local log data ---
        local_data: dict[str, Any] = {}
        try:
            local_data = self._log_monitor.get_usage()
        except Exception as e:
            error_parts.append(f"Logs: {e}")

        # --- Subscription info from keychain ---
        subscription_type = ""
        rate_tier = ""
        try:
            subscription_type = self._auth_manager.subscription_type
            rate_tier = self._auth_manager.rate_limit_tier
        except Exception as e:
            error_parts.append(f"Keychain: {e}")

        result = {
            # Real usage from claude.ai (percentages)
            "session_pct": web_data.get("session_pct", 0),
            "session_resets_at": web_data.get("session_resets_at"),
            "weekly_pct": web_data.get("weekly_pct", 0),
            "weekly_resets_at": web_data.get("weekly_resets_at"),
            "sonnet_pct": web_data.get("sonnet_pct", 0),
            "sonnet_resets_at": web_data.get("sonnet_resets_at"),
            # Extra usage (if available)
            "extra_spent": web_data.get("extra_spent"),
            "extra_limit": web_data.get("extra_limit"),
            "extra_pct": web_data.get("extra_pct"),
            # Local log data (supplementary detail)
            "input_tokens": local_data.get("input_tokens", 0),
            "output_tokens": local_data.get("output_tokens", 0),
            "cache_creation": local_data.get("cache_creation_input_tokens", 0),
            "cache_read": local_data.get("cache_read_input_tokens", 0),
            "record_count": local_data.get("record_count", 0),
            "session_count": local_data.get("session_count", 0),
            # Subscription
            "subscription_type": subscription_type,
            "rate_tier": rate_tier,
            # Metadata
            "error": "; ".join(error_parts) if error_parts else None,
            "last_updated": datetime.now(tz=timezone.utc),
        }

        self._last_result = result
        return result

    @property
    def last_result(self) -> dict[str, Any] | None:
        return self._last_result
