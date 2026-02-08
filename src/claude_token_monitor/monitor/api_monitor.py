"""Rate limit estimation based on subscription tier and local usage data.

The Anthropic API does not support OAuth tokens for rate limit queries.
Claude Max uses a "unified" rate limit system with 5-hour rolling windows.
Exact limits are not publicly documented, so we show usage data directly.

Key insight from docs:
- Only uncached input_tokens + cache_creation_input_tokens count toward ITPM
- cache_read_input_tokens do NOT count toward rate limits
"""

from datetime import datetime, timezone, timedelta
from typing import Any


def format_tokens(n: int) -> str:
    """Format token count in human-readable form: 1.2K, 3.5M, etc."""
    if n < 0:
        return f"-{format_tokens(-n)}"
    if n < 1_000:
        return str(n)
    if n < 10_000:
        return f"{n / 1_000:.1f}K"
    if n < 1_000_000:
        return f"{n / 1_000:.0f}K"
    if n < 10_000_000:
        return f"{n / 1_000_000:.2f}M"
    return f"{n / 1_000_000:.1f}M"


def make_bar(pct: float, width: int = 15) -> str:
    """Create a Unicode progress bar string.

    Args:
        pct: Percentage (0.0 - 1.0).
        width: Number of characters for the bar.

    Returns:
        String like "▓▓▓▓▓▓▓░░░░░░░░ 47%"
    """
    pct = max(0.0, min(1.0, pct))
    filled = round(pct * width)
    empty = width - filled
    bar = "▓" * filled + "░" * empty
    return f"{bar} {pct:.0%}"


def estimate_from_local_usage(
    local_usage: dict[str, Any],
    rate_tier: str = "",
) -> dict[str, Any]:
    """Build usage summary from local log data.

    Since exact Max subscription limits are not published,
    we report raw usage numbers and let the UI display them visually.
    """
    total_input = local_usage.get("input_tokens", 0)
    total_output = local_usage.get("output_tokens", 0)
    billable_input = local_usage.get("billable_input", total_input)
    billable_total = local_usage.get("billable_total", total_input + total_output)
    cache_creation = local_usage.get("cache_creation_input_tokens", 0)
    cache_read = local_usage.get("cache_read_input_tokens", 0)
    record_count = local_usage.get("record_count", 0)
    session_count = local_usage.get("session_count", 0)

    # Window timing
    window_hours = local_usage.get("window_hours", 5.0)
    window_start_str = local_usage.get("window_start")
    if window_start_str:
        try:
            window_start = datetime.fromisoformat(window_start_str)
            window_end = window_start + timedelta(hours=window_hours)
        except (ValueError, TypeError):
            window_end = datetime.now(timezone.utc) + timedelta(hours=window_hours)
    else:
        window_end = datetime.now(timezone.utc) + timedelta(hours=window_hours)

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "billable_input": billable_input,
        "billable_total": billable_total,
        "cache_creation": cache_creation,
        "cache_read": cache_read,
        "record_count": record_count,
        "session_count": session_count,
        "window_end": window_end,
        "window_hours": window_hours,
        "status": "ok",
        "source": "local_logs",
    }
