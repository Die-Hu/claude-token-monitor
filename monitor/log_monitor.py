"""Local JSONL log parsing for Claude Code usage data."""

import json
import os
import glob
from datetime import datetime, timezone, timedelta
from typing import Any


class LogMonitor:
    """Parses local Claude Code logs for token usage data."""

    CLAUDE_DIR = os.path.expanduser("~/.claude")
    PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")
    STATS_CACHE = os.path.join(CLAUDE_DIR, "stats-cache.json")
    DEFAULT_WINDOW_HOURS = 5.0

    def _parse_jsonl_file(
        self, filepath: str, cutoff: datetime
    ) -> list[dict[str, Any]]:
        """Parse a JSONL file and extract usage records after cutoff time."""
        records = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Look for entries with usage data
                    usage = None
                    timestamp = None

                    # Direct usage field on the entry
                    if isinstance(entry, dict):
                        usage = entry.get("usage")
                        ts_str = entry.get("timestamp") or entry.get("ts")
                        if ts_str:
                            timestamp = self._parse_timestamp(ts_str)

                        # Check nested message -> usage
                        if not usage:
                            message = entry.get("message")
                            if isinstance(message, dict):
                                usage = message.get("usage")

                        # Check result -> usage (for API responses)
                        if not usage:
                            result = entry.get("result")
                            if isinstance(result, dict):
                                usage = result.get("usage")

                    if not usage or not isinstance(usage, dict):
                        continue

                    # Check if within time window
                    if timestamp and timestamp < cutoff:
                        continue

                    input_tokens = usage.get("input_tokens", 0) or 0
                    output_tokens = usage.get("output_tokens", 0) or 0
                    cache_creation = usage.get("cache_creation_input_tokens", 0) or 0
                    cache_read = usage.get("cache_read_input_tokens", 0) or 0

                    if input_tokens or output_tokens or cache_creation or cache_read:
                        records.append(
                            {
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "cache_creation_input_tokens": cache_creation,
                                "cache_read_input_tokens": cache_read,
                                "timestamp": timestamp,
                                "file": filepath,
                            }
                        )
        except (OSError, IOError):
            pass
        return records

    def _parse_timestamp(self, value: Any) -> datetime | None:
        """Parse a timestamp from various formats."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            try:
                # Unix timestamp (seconds or milliseconds)
                if value > 1e12:
                    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
                return datetime.fromtimestamp(value, tz=timezone.utc)
            except (OSError, ValueError, OverflowError):
                return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return None

    def _read_stats_cache(self) -> dict[str, Any] | None:
        """Read the stats-cache.json file if it exists."""
        try:
            with open(self.STATS_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, IOError, json.JSONDecodeError):
            return None

    def get_usage(self, window_hours: float | None = None) -> dict[str, Any]:
        """Get local token usage within the rolling time window.

        Args:
            window_hours: Number of hours for the rolling window.
                         Defaults to DEFAULT_WINDOW_HOURS (5).

        Returns:
            Dict with aggregated usage data.
        """
        if window_hours is None:
            window_hours = self.DEFAULT_WINDOW_HOURS

        now = datetime.now(tz=timezone.utc)
        cutoff = now - timedelta(hours=window_hours)

        # Find all JSONL files
        pattern = os.path.join(self.PROJECTS_DIR, "**", "*.jsonl")
        jsonl_files = glob.glob(pattern, recursive=True)

        all_records = []
        sessions: dict[str, dict[str, int]] = {}

        for filepath in jsonl_files:
            # Skip very large files (> 50MB) to avoid slow parsing
            try:
                if os.path.getsize(filepath) > 50 * 1024 * 1024:
                    continue
            except OSError:
                continue

            records = self._parse_jsonl_file(filepath, cutoff)
            all_records.extend(records)

            if records:
                session_key = os.path.basename(os.path.dirname(filepath))
                if session_key not in sessions:
                    sessions[session_key] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 0,
                    }
                for r in records:
                    sessions[session_key]["input_tokens"] += r["input_tokens"]
                    sessions[session_key]["output_tokens"] += r["output_tokens"]
                    sessions[session_key]["cache_creation_input_tokens"] += r[
                        "cache_creation_input_tokens"
                    ]
                    sessions[session_key]["cache_read_input_tokens"] += r[
                        "cache_read_input_tokens"
                    ]

        total_input = sum(r["input_tokens"] for r in all_records)
        total_output = sum(r["output_tokens"] for r in all_records)
        total_cache_creation = sum(
            r["cache_creation_input_tokens"] for r in all_records
        )
        total_cache_read = sum(r["cache_read_input_tokens"] for r in all_records)

        # Read stats cache for supplementary data
        stats_cache = self._read_stats_cache()

        # Billable tokens: uncached input + cache creation count toward limits
        # cache_read does NOT count toward rate limits
        billable_input = total_input + total_cache_creation
        billable_total = billable_input + total_output

        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total": total_input + total_output,
            "billable_input": billable_input,
            "billable_total": billable_total,
            "cache_creation_input_tokens": total_cache_creation,
            "cache_read_input_tokens": total_cache_read,
            "window_hours": window_hours,
            "window_start": cutoff.isoformat(),
            "window_end": now.isoformat(),
            "session_count": len(sessions),
            "sessions": sessions,
            "record_count": len(all_records),
            "files_scanned": len(jsonl_files),
            "stats_cache": stats_cache,
        }


# Module-level singleton
_log_monitor = LogMonitor()


def get_local_usage(window_hours: float | None = None) -> dict[str, Any]:
    """Get local token usage (module-level convenience function)."""
    return _log_monitor.get_usage(window_hours=window_hours)
