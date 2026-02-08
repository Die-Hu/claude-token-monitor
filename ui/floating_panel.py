"""Native macOS floating panel using PyObjC."""

import objc
from AppKit import (
    NSPanel,
    NSView,
    NSTextField,
    NSColor,
    NSFont,
    NSProgressIndicator,
    NSTimer,
    NSMakeRect,
    NSApp,
    NSUtilityWindowMask,
    NSClosableWindowMask,
    NSTitledWindowMask,
    NSFloatingWindowLevel,
    NSBackingStoreBuffered,
    NSProgressIndicatorBarStyle,
)
from Foundation import NSObject
from datetime import datetime, timezone

from monitor.api_monitor import format_tokens

# Layout
PANEL_WIDTH = 340
PANEL_HEIGHT = 460
PAD = 16
LBL_H = 18
BAR_H = 14
GAP = 8


class FloatingPanel:
    """Always-on-top floating panel showing Claude usage."""

    def __init__(self):
        self._data = None
        self._countdown_timer = None
        self._visible = False

        style = NSTitledWindowMask | NSClosableWindowMask | NSUtilityWindowMask
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, PANEL_WIDTH, PANEL_HEIGHT),
            style,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setTitle_("Claude Token Monitor")
        self.panel.setLevel_(NSFloatingWindowLevel)
        self.panel.setMovableByWindowBackground_(True)
        self.panel.setReleasedWhenClosed_(False)
        self.panel.center()

        cv = self.panel.contentView()
        cv.setWantsLayer_(True)
        layer = cv.layer()
        bg = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08, 0.08, 0.12, 0.95)
        layer.setBackgroundColor_(bg.CGColor())
        layer.setCornerRadius_(12)

        self._build_ui(cv)

    # ---- helpers ----

    def _label(self, text, x, y, w, h=LBL_H, size=12.0, bold=False, mono=False, color=None):
        lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
        lbl.setStringValue_(text)
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        lbl.setSelectable_(False)
        lbl.setTextColor_(color or NSColor.whiteColor())
        if mono:
            lbl.setFont_(NSFont.monospacedSystemFontOfSize_weight_(size, 0.0))
        elif bold:
            lbl.setFont_(NSFont.boldSystemFontOfSize_(size))
        else:
            lbl.setFont_(NSFont.systemFontOfSize_(size))
        return lbl

    def _section(self, text, y, parent):
        c = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.55, 0.65, 1.0, 1.0)
        lbl = self._label(text, PAD, y, PANEL_WIDTH - 2 * PAD, size=11.0, bold=True, color=c)
        parent.addSubview_(lbl)
        return lbl

    def _bar(self, x, y, w, parent):
        bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(x, y, w, BAR_H))
        bar.setStyle_(NSProgressIndicatorBarStyle)
        bar.setMinValue_(0)
        bar.setMaxValue_(100)
        bar.setDoubleValue_(0)
        bar.setIndeterminate_(False)
        parent.addSubview_(bar)
        return bar

    # ---- layout ----

    def _build_ui(self, parent):
        w = PANEL_WIDTH - 2 * PAD
        y = PANEL_HEIGHT - 42

        # Title
        t = self._label("Claude Token Monitor", PAD, y, w, h=24, size=16.0, bold=True)
        parent.addSubview_(t)
        y -= (GAP + LBL_H + 4)

        # -- 当前会话 (Session 5h) --
        self._section("当前会话 (5h 滚动窗口)", y, parent)
        y -= (BAR_H + 4)
        self.session_bar = self._bar(PAD, y, w, parent)
        y -= (LBL_H + 2)
        self.session_label = self._label("0%", PAD, y, w, mono=True, size=13.0)
        parent.addSubview_(self.session_label)
        y -= (LBL_H)
        dim = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.6, 0.6, 0.6, 1.0)
        self.session_reset_label = self._label("重置: --", PAD, y, w, size=11.0, color=dim)
        parent.addSubview_(self.session_reset_label)
        y -= (GAP + LBL_H)

        # -- 每周限额 · 全部模型 --
        self._section("每周限额 · 全部模型", y, parent)
        y -= (BAR_H + 4)
        self.weekly_bar = self._bar(PAD, y, w, parent)
        y -= (LBL_H + 2)
        self.weekly_label = self._label("0%", PAD, y, w, mono=True, size=13.0)
        parent.addSubview_(self.weekly_label)
        y -= (LBL_H)
        self.weekly_reset_label = self._label("重置: --", PAD, y, w, size=11.0, color=dim)
        parent.addSubview_(self.weekly_reset_label)
        y -= (GAP + LBL_H)

        # -- 每周限额 · Sonnet --
        self._section("每周限额 · Sonnet", y, parent)
        y -= (BAR_H + 4)
        self.sonnet_bar = self._bar(PAD, y, w, parent)
        y -= (LBL_H + 2)
        self.sonnet_label = self._label("0%", PAD, y, w, mono=True, size=13.0)
        parent.addSubview_(self.sonnet_label)
        y -= (LBL_H)
        self.sonnet_reset_label = self._label("重置: --", PAD, y, w, size=11.0, color=dim)
        parent.addSubview_(self.sonnet_reset_label)
        y -= (GAP + LBL_H)

        # -- Claude Code 本地统计 --
        self._section("Claude Code 本地统计", y, parent)
        y -= (LBL_H + 2)
        self.local_tokens_label = self._label("输入: -- / 输出: --", PAD, y, w, mono=True)
        parent.addSubview_(self.local_tokens_label)
        y -= (LBL_H + 2)
        green = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0.8, 0.5, 1.0)
        self.local_cache_label = self._label("缓存: --", PAD, y, w, mono=True, color=green)
        parent.addSubview_(self.local_cache_label)
        y -= (LBL_H + 2)
        self.local_sessions_label = self._label("会话: --", PAD, y, w, mono=True)
        parent.addSubview_(self.local_sessions_label)
        y -= (GAP + LBL_H)

        # -- 订阅 --
        self._section("订阅", y, parent)
        y -= (LBL_H + 2)
        self.sub_label = self._label("--", PAD, y, w, mono=True)
        parent.addSubview_(self.sub_label)
        y -= (GAP + LBL_H)

        # -- 上次更新 --
        dim2 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0.5, 0.5, 1.0)
        self.updated_label = self._label("上次更新: --:--:--", PAD, max(y, 6), w, size=10.0, color=dim2)
        parent.addSubview_(self.updated_label)

    # ---- data update ----

    def update_data(self, data):
        if data is None:
            return
        self._data = data

        session_pct = data.get("session_pct") or 0
        weekly_pct = data.get("weekly_pct") or 0
        sonnet_pct = data.get("sonnet_pct") or 0

        # Session bar
        self.session_bar.setDoubleValue_(session_pct)
        self.session_label.setStringValue_(f"{session_pct:.0f}% 已使用")
        self._color_bar(self.session_bar, session_pct)
        session_reset = data.get("session_resets_at")
        if session_reset and isinstance(session_reset, datetime):
            self._update_session_countdown(session_reset)
        else:
            self.session_reset_label.setStringValue_("重置: --")

        # Weekly bar
        self.weekly_bar.setDoubleValue_(weekly_pct)
        self.weekly_label.setStringValue_(f"{weekly_pct:.0f}% 已使用")
        self._color_bar(self.weekly_bar, weekly_pct)
        weekly_reset = data.get("weekly_resets_at")
        if weekly_reset and isinstance(weekly_reset, datetime):
            self.weekly_reset_label.setStringValue_(
                f"重置: {self._format_reset_day(weekly_reset)}"
            )
        else:
            self.weekly_reset_label.setStringValue_("重置: --")

        # Sonnet bar
        self.sonnet_bar.setDoubleValue_(sonnet_pct)
        self.sonnet_label.setStringValue_(f"{sonnet_pct:.0f}% 已使用")
        self._color_bar(self.sonnet_bar, sonnet_pct)
        sonnet_reset = data.get("sonnet_resets_at")
        if sonnet_reset and isinstance(sonnet_reset, datetime):
            self.sonnet_reset_label.setStringValue_(
                f"重置: {self._format_reset_day(sonnet_reset)}"
            )
        else:
            self.sonnet_reset_label.setStringValue_("重置: --")

        # Local stats
        inp = data.get("input_tokens", 0)
        out = data.get("output_tokens", 0)
        cache_create = data.get("cache_creation", 0)
        cache_read = data.get("cache_read", 0)
        record_count = data.get("record_count", 0)
        session_count = data.get("session_count", 0)

        self.local_tokens_label.setStringValue_(
            f"输入: {format_tokens(inp)} / 输出: {format_tokens(out)}"
        )
        self.local_cache_label.setStringValue_(
            f"缓存创建: {format_tokens(cache_create)} / "
            f"读取: {format_tokens(cache_read)}"
        )
        self.local_sessions_label.setStringValue_(
            f"请求 {record_count} 次 / {session_count} 个会话"
        )

        # Subscription
        subscription_type = data.get("subscription_type", "--")
        rate_tier = data.get("rate_tier", "--")
        tier_label = "Max 5x" if "5x" in rate_tier else rate_tier
        self.sub_label.setStringValue_(f"{subscription_type} ({tier_label})")

        # Updated timestamp
        last_updated = data.get("last_updated")
        if last_updated and isinstance(last_updated, datetime):
            self.updated_label.setStringValue_(
                f"上次更新: {last_updated.strftime('%H:%M:%S')}"
            )

    def _update_session_countdown(self, reset_at: datetime):
        """Update the session countdown display."""
        now = datetime.now(timezone.utc)
        delta = reset_at - now
        total_secs = max(0, int(delta.total_seconds()))
        h = total_secs // 3600
        m = (total_secs % 3600) // 60
        s = total_secs % 60
        self.session_reset_label.setStringValue_(f"重置: {h:02d}:{m:02d}:{s:02d}")

    @staticmethod
    def _format_reset_day(dt: datetime) -> str:
        """Format a reset datetime as day/time."""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        local_dt = dt.astimezone()
        day_name = days[local_dt.weekday()]
        return f"{day_name} {local_dt.strftime('%I:%M %p')}"

    @staticmethod
    def _color_bar(bar, pct):
        bar.setWantsLayer_(True)
        layer = bar.layer()
        if layer is None:
            return
        if pct < 40:
            c = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.7, 0.4, 1.0)
        elif pct < 70:
            c = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.85, 0.75, 0.1, 1.0)
        else:
            c = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.9, 0.25, 0.2, 1.0)
        layer.setBackgroundColor_(c.CGColor())

    # ---- countdown timer ----

    def _tick_countdown(self):
        """Called every second to update the session countdown."""
        if self._data:
            reset_at = self._data.get("session_resets_at")
            if reset_at and isinstance(reset_at, datetime):
                self._update_session_countdown(reset_at)

    def _start_countdown_timer(self):
        if self._countdown_timer is not None:
            return
        self._countdown_timer = NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0, True, lambda timer: self._tick_countdown(),
        )

    def _stop_countdown_timer(self):
        if self._countdown_timer is not None:
            self._countdown_timer.invalidate()
            self._countdown_timer = None

    # ---- show / hide ----

    def show(self):
        self.panel.orderFront_(None)
        self._visible = True
        self._start_countdown_timer()

    def hide(self):
        self.panel.orderOut_(None)
        self._visible = False
        self._stop_countdown_timer()

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()
