"""macOS status bar application using rumps."""

import rumps
from datetime import datetime, timezone

from monitor.api_monitor import format_tokens, make_bar

# Try to import i18n; fall back to simple passthrough if unavailable
try:
    from claude_token_monitor.i18n import T, init as i18n_init
    i18n_init()
except ImportError:
    # Fallback: load i18n from relative path
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from claude_token_monitor.i18n import T, init as i18n_init
        i18n_init()
    except ImportError:
        def T(key: str) -> str:
            """Fallback: return key as-is."""
            return key


class TokenMenuBarApp(rumps.App):
    """Claude Token Monitor status bar application."""

    def __init__(self):
        super().__init__("☁ ...", quit_button=None)

        self.monitor = None
        self.panel = None

        # Menu items
        self.header_item = rumps.MenuItem(T("claude_usage"))
        self.header_item.set_callback(None)

        # Session (5h rolling window)
        self.session_header = rumps.MenuItem(f"⏱ {T('session_header')}")
        self.session_header.set_callback(None)
        self.session_bar = rumps.MenuItem("  ░░░░░░░░░░░░░░░ 0%")
        self.session_reset = rumps.MenuItem(f"  {T('reset_label')}: {T('no_data')}")

        # Weekly - All models
        self.weekly_header = rumps.MenuItem(f"📊 {T('weekly_all_header')}")
        self.weekly_header.set_callback(None)
        self.weekly_bar = rumps.MenuItem("  ░░░░░░░░░░░░░░░ 0%")
        self.weekly_reset = rumps.MenuItem(f"  {T('reset_label')}: {T('no_data')}")

        # Weekly - Sonnet only
        self.sonnet_header = rumps.MenuItem(f"📊 {T('weekly_sonnet_header')}")
        self.sonnet_header.set_callback(None)
        self.sonnet_bar = rumps.MenuItem("  ░░░░░░░░░░░░░░░ 0%")
        self.sonnet_reset = rumps.MenuItem(f"  {T('reset_label')}: {T('no_data')}")

        # Local Claude Code stats
        self.local_header = rumps.MenuItem(f"🖥 {T('local_stats_header')}")
        self.local_header.set_callback(None)
        self.local_tokens = rumps.MenuItem(f"  {T('token_label')}: {T('no_data')}")
        self.local_cache = rumps.MenuItem(f"  {T('cache_label')}: {T('no_data')}")
        self.local_sessions = rumps.MenuItem(
            f"  {T('requests_sessions_format').format(req_count=T('no_data'), sess_count=T('no_data'))}"
        )

        # Subscription
        self.sub_item = rumps.MenuItem(f"{T('subscription_label')}: {T('no_data')}")

        self.menu = [
            self.header_item,
            None,
            self.session_header,
            self.session_bar,
            self.session_reset,
            None,
            self.weekly_header,
            self.weekly_bar,
            self.weekly_reset,
            None,
            self.sonnet_header,
            self.sonnet_bar,
            self.sonnet_reset,
            None,
            self.local_header,
            self.local_tokens,
            self.local_cache,
            self.local_sessions,
            None,
            self.sub_item,
            None,
            rumps.MenuItem(f"📊 {T('show_detail')}", callback=self.toggle_panel),
            rumps.MenuItem(f"🔄 {T('refresh_now')}", callback=self.manual_refresh),
            None,
            rumps.MenuItem(T("quit"), callback=self.quit_app),
        ]

    def set_monitor(self, monitor):
        self.monitor = monitor
        self._init_timer = rumps.Timer(self._initial_fetch, 2)
        self._init_timer.start()

    def _initial_fetch(self, _):
        self._init_timer.stop()
        self.refresh_data(None)

    def set_panel(self, panel):
        self.panel = panel

    @rumps.timer(60)
    def refresh_data(self, _):
        if self.monitor is None:
            return
        try:
            data = self.monitor.refresh()
            self.update_display(data)
        except Exception as e:
            self.title = "☁ ⚠"
            self.header_item.title = T("error_format").format(msg=e)

    def update_display(self, data):
        if data is None:
            return

        session_pct = data.get("session_pct") or 0
        weekly_pct = data.get("weekly_pct") or 0
        sonnet_pct = data.get("sonnet_pct") or 0

        # Status bar title: show most important usage
        self.title = f"☁ {session_pct:.0f}%"

        # --- Session (5h) ---
        self.session_bar.title = f"  {make_bar(session_pct / 100)} {session_pct:.0f}%"
        session_reset = data.get("session_resets_at")
        if session_reset and isinstance(session_reset, datetime):
            self.session_reset.title = f"  {T('reset_label')}: {self._format_countdown(session_reset)}"
        else:
            self.session_reset.title = f"  {T('reset_label')}: {T('no_data')}"

        # --- Weekly All Models ---
        self.weekly_bar.title = f"  {make_bar(weekly_pct / 100)} {weekly_pct:.0f}%"
        weekly_reset = data.get("weekly_resets_at")
        if weekly_reset and isinstance(weekly_reset, datetime):
            self.weekly_reset.title = f"  {T('reset_label')}: {self._format_reset_day(weekly_reset)}"
        else:
            self.weekly_reset.title = f"  {T('reset_label')}: {T('no_data')}"

        # --- Weekly Sonnet ---
        self.sonnet_bar.title = f"  {make_bar(sonnet_pct / 100)} {sonnet_pct:.0f}%"
        sonnet_reset = data.get("sonnet_resets_at")
        if sonnet_reset and isinstance(sonnet_reset, datetime):
            self.sonnet_reset.title = f"  {T('reset_label')}: {self._format_reset_day(sonnet_reset)}"
        else:
            self.sonnet_reset.title = f"  {T('reset_label')}: {T('no_data')}"

        # --- Local Claude Code stats ---
        inp = data.get("input_tokens", 0)
        out = data.get("output_tokens", 0)
        cache_create = data.get("cache_creation", 0)
        cache_read = data.get("cache_read", 0)
        record_count = data.get("record_count", 0)
        session_count = data.get("session_count", 0)

        self.local_tokens.title = (
            f"  {T('input_label')}: {format_tokens(inp)} / "
            f"{T('output_label')}: {format_tokens(out)}"
        )
        self.local_cache.title = (
            f"  {T('cache_create_label')}: {format_tokens(cache_create)} / "
            f"{T('cache_read_label')}: {format_tokens(cache_read)}"
        )
        self.local_sessions.title = (
            f"  {T('requests_sessions_format').format(req_count=record_count, sess_count=session_count)}"
        )

        # Subscription
        subscription_type = data.get("subscription_type") or T("no_data")
        rate_tier = data.get("rate_tier") or T("no_data")
        tier_label = "Max 5x" if "5x" in rate_tier else rate_tier
        self.sub_item.title = (
            f"{T('subscription_label')}: "
            f"{T('subscription_format').format(type=subscription_type, tier=tier_label)}"
        )

        # Update floating panel if visible
        if self.panel is not None:
            try:
                self.panel.update_data(data)
            except Exception:
                pass

    @staticmethod
    def _format_countdown(dt: datetime) -> str:
        """Format a datetime as a countdown string."""
        now = datetime.now(timezone.utc)
        delta = dt - now
        total_secs = max(0, int(delta.total_seconds()))
        hours = total_secs // 3600
        mins = (total_secs % 3600) // 60
        if hours > 0:
            return f"{hours}h {mins}min"
        return f"{mins}min"

    @staticmethod
    def _format_reset_day(dt: datetime) -> str:
        """Format a reset datetime as a human-readable day/time."""
        day_keys = [
            "day_mon", "day_tue", "day_wed", "day_thu",
            "day_fri", "day_sat", "day_sun",
        ]
        local_dt = dt.astimezone()
        day_name = T(day_keys[local_dt.weekday()])
        return f"{day_name} {local_dt.strftime('%I:%M %p')}"

    def toggle_panel(self, _):
        if self.panel is not None:
            self.panel.toggle()

    def manual_refresh(self, _):
        self.refresh_data(None)

    @staticmethod
    def quit_app(_):
        rumps.quit_application()
