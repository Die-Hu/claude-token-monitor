"""Cross-platform tkinter detail window for Claude Token Monitor."""

import tkinter as tk
from datetime import datetime, timezone

from claude_token_monitor.i18n import T
from claude_token_monitor.monitor.api_monitor import format_tokens
from claude_token_monitor.ui.theme import (
    BG_COLOR,
    ACCENT_COLOR,
    TEXT_COLOR,
    DIM_COLOR,
    GREEN,
    BAR_BG,
    CACHE_COLOR,
    FONT_FAMILY,
    MONO_FONT_FAMILY,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    FONT_SIZE_TITLE,
    FONT_SIZE_SECTION,
    FONT_SIZE_PCT,
    PANEL_WIDTH,
    PANEL_HEIGHT,
    PAD,
    GAP,
    bar_color,
)


class DetailWindow:
    """Always-on-top detail window showing Claude usage stats."""

    def __init__(self, root: tk.Tk):
        self._root = root
        self._data = None
        self._visible = False
        self._countdown_after_id = None

        self._win = tk.Toplevel(root)
        self._win.title(T("app_title"))
        self._win.geometry(f"{PANEL_WIDTH}x{PANEL_HEIGHT}")
        self._win.configure(bg=BG_COLOR)
        self._win.resizable(False, False)
        self._win.attributes("-topmost", True)
        self._win.protocol("WM_DELETE_WINDOW", self.hide)
        self._win.withdraw()

        self._bar_width = PANEL_WIDTH - 2 * PAD

        # StringVars for dynamic labels
        self._session_pct_var = tk.StringVar(value=f"0% {T('used_label')}")
        self._session_reset_var = tk.StringVar(value=f"{T('reset_label')}: {T('no_data')}")
        self._weekly_pct_var = tk.StringVar(value=f"0% {T('used_label')}")
        self._weekly_reset_var = tk.StringVar(value=f"{T('reset_label')}: {T('no_data')}")
        self._sonnet_pct_var = tk.StringVar(value=f"0% {T('used_label')}")
        self._sonnet_reset_var = tk.StringVar(value=f"{T('reset_label')}: {T('no_data')}")
        self._tokens_var = tk.StringVar(
            value=f"{T('input_label')}: {T('no_data')} / {T('output_label')}: {T('no_data')}"
        )
        self._cache_var = tk.StringVar(
            value=f"{T('cache_create_label')}: {T('no_data')} / {T('cache_read_label')}: {T('no_data')}"
        )
        self._sessions_var = tk.StringVar(
            value=T('requests_sessions_format').format(
                req_count=T('no_data'), sess_count=T('no_data')
            )
        )
        self._sub_var = tk.StringVar(value=T("no_data"))
        self._updated_var = tk.StringVar(value=f"{T('last_updated')}: {T('no_data')}")

        self._build_ui()

    def _build_ui(self):
        """Build the dark-themed UI with all sections."""
        main = tk.Frame(self._win, bg=BG_COLOR)
        main.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=PAD)

        # Title
        tk.Label(
            main, text=T("app_title"), bg=BG_COLOR, fg=TEXT_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"), anchor="w",
        ).pack(fill=tk.X, pady=(0, GAP))

        # --- Session (5h) section ---
        self._section_header(main, T("session_header_detail"))
        self._session_canvas, self._session_fill = self._create_progress_bar(main, self._bar_width)
        self._session_canvas.pack(fill=tk.X, pady=(2, 2))
        tk.Label(
            main, textvariable=self._session_pct_var, bg=BG_COLOR, fg=TEXT_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_PCT), anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            main, textvariable=self._session_reset_var, bg=BG_COLOR, fg=DIM_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_SECTION), anchor="w",
        ).pack(fill=tk.X, pady=(0, GAP))

        # --- Weekly All Models section ---
        self._section_header(main, T("weekly_all_header"))
        self._weekly_canvas, self._weekly_fill = self._create_progress_bar(main, self._bar_width)
        self._weekly_canvas.pack(fill=tk.X, pady=(2, 2))
        tk.Label(
            main, textvariable=self._weekly_pct_var, bg=BG_COLOR, fg=TEXT_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_PCT), anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            main, textvariable=self._weekly_reset_var, bg=BG_COLOR, fg=DIM_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_SECTION), anchor="w",
        ).pack(fill=tk.X, pady=(0, GAP))

        # --- Weekly Sonnet section ---
        self._section_header(main, T("weekly_sonnet_header"))
        self._sonnet_canvas, self._sonnet_fill = self._create_progress_bar(main, self._bar_width)
        self._sonnet_canvas.pack(fill=tk.X, pady=(2, 2))
        tk.Label(
            main, textvariable=self._sonnet_pct_var, bg=BG_COLOR, fg=TEXT_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_PCT), anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            main, textvariable=self._sonnet_reset_var, bg=BG_COLOR, fg=DIM_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_SECTION), anchor="w",
        ).pack(fill=tk.X, pady=(0, GAP))

        # --- Local stats section ---
        self._section_header(main, T("local_stats_header"))
        tk.Label(
            main, textvariable=self._tokens_var, bg=BG_COLOR, fg=TEXT_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_NORMAL), anchor="w",
        ).pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            main, textvariable=self._cache_var, bg=BG_COLOR, fg=CACHE_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_NORMAL), anchor="w",
        ).pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            main, textvariable=self._sessions_var, bg=BG_COLOR, fg=TEXT_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_NORMAL), anchor="w",
        ).pack(fill=tk.X, pady=(2, GAP))

        # --- Subscription section ---
        self._section_header(main, T("subscription_label"))
        tk.Label(
            main, textvariable=self._sub_var, bg=BG_COLOR, fg=TEXT_COLOR,
            font=(MONO_FONT_FAMILY, FONT_SIZE_NORMAL), anchor="w",
        ).pack(fill=tk.X, pady=(2, GAP))

        # --- Last updated ---
        tk.Label(
            main, textvariable=self._updated_var, bg=BG_COLOR, fg=DIM_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_SMALL), anchor="w",
        ).pack(fill=tk.X, side=tk.BOTTOM)

    def _section_header(self, parent, text):
        """Create a colored section header label."""
        tk.Label(
            parent, text=text, bg=BG_COLOR, fg=ACCENT_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_SECTION, "bold"), anchor="w",
        ).pack(fill=tk.X, pady=(2, 0))

    def _create_progress_bar(self, parent, width):
        """Create a canvas-based progress bar. Returns (canvas, fill_rect_id)."""
        canvas = tk.Canvas(
            parent, width=width, height=14, bg=BAR_BG,
            highlightthickness=0, bd=0,
        )
        fill = canvas.create_rectangle(0, 0, 0, 14, fill=GREEN, outline="")
        return canvas, fill

    def _update_bar(self, canvas, fill_id, pct, width):
        """Update a progress bar's fill width and color."""
        fill_width = int(pct / 100 * width)
        color = bar_color(pct)
        canvas.coords(fill_id, 0, 0, fill_width, 14)
        canvas.itemconfig(fill_id, fill=color)

    def update_data(self, data: dict):
        """Update all UI elements with new data."""
        if data is None:
            return
        self._data = data

        session_pct = data.get("session_pct") or 0
        weekly_pct = data.get("weekly_pct") or 0
        sonnet_pct = data.get("sonnet_pct") or 0

        # Session bar
        self._update_bar(self._session_canvas, self._session_fill, session_pct, self._bar_width)
        self._session_pct_var.set(f"{session_pct:.0f}% {T('used_label')}")
        session_reset = data.get("session_resets_at")
        if session_reset and isinstance(session_reset, datetime):
            self._update_session_countdown(session_reset)
        else:
            self._session_reset_var.set(f"{T('reset_label')}: {T('no_data')}")

        # Weekly bar
        self._update_bar(self._weekly_canvas, self._weekly_fill, weekly_pct, self._bar_width)
        self._weekly_pct_var.set(f"{weekly_pct:.0f}% {T('used_label')}")
        weekly_reset = data.get("weekly_resets_at")
        if weekly_reset and isinstance(weekly_reset, datetime):
            self._weekly_reset_var.set(
                f"{T('reset_label')}: {self._format_reset_day(weekly_reset)}"
            )
        else:
            self._weekly_reset_var.set(f"{T('reset_label')}: {T('no_data')}")

        # Sonnet bar
        self._update_bar(self._sonnet_canvas, self._sonnet_fill, sonnet_pct, self._bar_width)
        self._sonnet_pct_var.set(f"{sonnet_pct:.0f}% {T('used_label')}")
        sonnet_reset = data.get("sonnet_resets_at")
        if sonnet_reset and isinstance(sonnet_reset, datetime):
            self._sonnet_reset_var.set(
                f"{T('reset_label')}: {self._format_reset_day(sonnet_reset)}"
            )
        else:
            self._sonnet_reset_var.set(f"{T('reset_label')}: {T('no_data')}")

        # Local stats
        inp = data.get("input_tokens", 0)
        out = data.get("output_tokens", 0)
        cache_create = data.get("cache_creation", 0)
        cache_read = data.get("cache_read", 0)
        record_count = data.get("record_count", 0)
        session_count = data.get("session_count", 0)

        self._tokens_var.set(
            f"{T('input_label')}: {format_tokens(inp)} / {T('output_label')}: {format_tokens(out)}"
        )
        self._cache_var.set(
            f"{T('cache_create_label')}: {format_tokens(cache_create)} / "
            f"{T('cache_read_label')}: {format_tokens(cache_read)}"
        )
        self._sessions_var.set(
            T('requests_sessions_format').format(
                req_count=record_count, sess_count=session_count
            )
        )

        # Subscription
        subscription_type = data.get("subscription_type") or T("no_data")
        rate_tier = data.get("rate_tier") or T("no_data")
        tier_label = "Max 5x" if "5x" in rate_tier else rate_tier
        self._sub_var.set(
            T('subscription_format').format(type=subscription_type, tier=tier_label)
        )

        # Last updated
        last_updated = data.get("last_updated")
        if last_updated and isinstance(last_updated, datetime):
            self._updated_var.set(
                f"{T('last_updated')}: {last_updated.strftime('%H:%M:%S')}"
            )

        # Restart countdown if visible
        if self._visible:
            self._start_countdown()

    def _update_session_countdown(self, reset_at: datetime):
        """Update the session countdown display text."""
        now = datetime.now(timezone.utc)
        delta = reset_at - now
        total_secs = max(0, int(delta.total_seconds()))
        h = total_secs // 3600
        m = (total_secs % 3600) // 60
        s = total_secs % 60
        self._session_reset_var.set(f"{T('reset_label')}: {h:02d}:{m:02d}:{s:02d}")

    def _tick_countdown(self):
        """Update session countdown every second."""
        if self._data and self._visible:
            reset_at = self._data.get("session_resets_at")
            if reset_at and isinstance(reset_at, datetime):
                self._update_session_countdown(reset_at)
            self._countdown_after_id = self._root.after(1000, self._tick_countdown)

    def _start_countdown(self):
        """Start the 1-second countdown timer."""
        self._stop_countdown()
        self._tick_countdown()

    def _stop_countdown(self):
        """Cancel the countdown timer."""
        if self._countdown_after_id is not None:
            self._root.after_cancel(self._countdown_after_id)
            self._countdown_after_id = None

    def show(self):
        """Show the detail window."""
        self._win.deiconify()
        self._visible = True
        self._start_countdown()

    def hide(self):
        """Hide the detail window."""
        self._win.withdraw()
        self._visible = False
        self._stop_countdown()

    def toggle(self):
        """Toggle window visibility."""
        if self._visible:
            self.hide()
        else:
            self.show()

    @staticmethod
    def _format_reset_day(dt: datetime) -> str:
        """Format a reset datetime as 'Day HH:MM AM/PM'."""
        day_keys = [
            "day_mon", "day_tue", "day_wed", "day_thu",
            "day_fri", "day_sat", "day_sun",
        ]
        local_dt = dt.astimezone()
        day_name = T(day_keys[local_dt.weekday()])
        return f"{day_name} {local_dt.strftime('%I:%M %p')}"
