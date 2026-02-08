"""macOS status bar application using rumps."""

import rumps
from datetime import datetime, timezone

from monitor.api_monitor import format_tokens, make_bar


class TokenMenuBarApp(rumps.App):
    """Claude Token Monitor status bar application."""

    def __init__(self):
        super().__init__("☁ ...", quit_button=None)

        self.monitor = None
        self.panel = None

        # Menu items
        self.header_item = rumps.MenuItem("Claude 用量")
        self.header_item.set_callback(None)

        # Session (5h rolling window)
        self.session_header = rumps.MenuItem("⏱ 当前会话 (5h 窗口)")
        self.session_header.set_callback(None)
        self.session_bar = rumps.MenuItem("  ░░░░░░░░░░░░░░░ 0%")
        self.session_reset = rumps.MenuItem("  重置: --")

        # Weekly - All models
        self.weekly_header = rumps.MenuItem("📊 每周限额 · 全部模型")
        self.weekly_header.set_callback(None)
        self.weekly_bar = rumps.MenuItem("  ░░░░░░░░░░░░░░░ 0%")
        self.weekly_reset = rumps.MenuItem("  重置: --")

        # Weekly - Sonnet only
        self.sonnet_header = rumps.MenuItem("📊 每周限额 · Sonnet")
        self.sonnet_header.set_callback(None)
        self.sonnet_bar = rumps.MenuItem("  ░░░░░░░░░░░░░░░ 0%")
        self.sonnet_reset = rumps.MenuItem("  重置: --")

        # Local Claude Code stats
        self.local_header = rumps.MenuItem("🖥 Claude Code 本地统计")
        self.local_header.set_callback(None)
        self.local_tokens = rumps.MenuItem("  Token: --")
        self.local_cache = rumps.MenuItem("  缓存: --")
        self.local_sessions = rumps.MenuItem("  会话: --")

        # Subscription
        self.sub_item = rumps.MenuItem("订阅: --")

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
            rumps.MenuItem("📊 显示详情窗口", callback=self.toggle_panel),
            rumps.MenuItem("🔄 立即刷新", callback=self.manual_refresh),
            None,
            rumps.MenuItem("退出", callback=self.quit_app),
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
            self.header_item.title = f"错误: {e}"

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
            self.session_reset.title = f"  重置: {self._format_countdown(session_reset)}"
        else:
            self.session_reset.title = "  重置: --"

        # --- Weekly All Models ---
        self.weekly_bar.title = f"  {make_bar(weekly_pct / 100)} {weekly_pct:.0f}%"
        weekly_reset = data.get("weekly_resets_at")
        if weekly_reset and isinstance(weekly_reset, datetime):
            self.weekly_reset.title = f"  重置: {self._format_reset_day(weekly_reset)}"
        else:
            self.weekly_reset.title = "  重置: --"

        # --- Weekly Sonnet ---
        self.sonnet_bar.title = f"  {make_bar(sonnet_pct / 100)} {sonnet_pct:.0f}%"
        sonnet_reset = data.get("sonnet_resets_at")
        if sonnet_reset and isinstance(sonnet_reset, datetime):
            self.sonnet_reset.title = f"  重置: {self._format_reset_day(sonnet_reset)}"
        else:
            self.sonnet_reset.title = "  重置: --"

        # --- Local Claude Code stats ---
        inp = data.get("input_tokens", 0)
        out = data.get("output_tokens", 0)
        cache_create = data.get("cache_creation", 0)
        cache_read = data.get("cache_read", 0)
        record_count = data.get("record_count", 0)
        session_count = data.get("session_count", 0)

        self.local_tokens.title = (
            f"  输入: {format_tokens(inp)} / 输出: {format_tokens(out)}"
        )
        self.local_cache.title = (
            f"  缓存创建: {format_tokens(cache_create)} / "
            f"读取: {format_tokens(cache_read)}"
        )
        self.local_sessions.title = f"  请求 {record_count} 次 / {session_count} 个会话"

        # Subscription
        subscription_type = data.get("subscription_type", "--")
        rate_tier = data.get("rate_tier", "--")
        tier_label = "Max 5x" if "5x" in rate_tier else rate_tier
        self.sub_item.title = f"订阅: {subscription_type} ({tier_label})"

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
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        local_dt = dt.astimezone()
        day_name = days[local_dt.weekday()]
        return f"{day_name} {local_dt.strftime('%I:%M %p')}"

    def toggle_panel(self, _):
        if self.panel is not None:
            self.panel.toggle()

    def manual_refresh(self, _):
        self.refresh_data(None)

    @staticmethod
    def quit_app(_):
        rumps.quit_application()
