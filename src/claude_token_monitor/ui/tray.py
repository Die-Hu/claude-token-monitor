"""System tray icon using pystray for Claude Token Monitor."""

from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw, ImageFont

from claude_token_monitor.i18n import T
from claude_token_monitor.ui.theme import GREEN_THRESHOLD, YELLOW_THRESHOLD


class TrayIcon:
    def __init__(
        self,
        on_show_detail: Callable,
        on_refresh: Callable,
        on_quit: Callable,
    ):
        self._on_show_detail = on_show_detail
        self._on_refresh = on_refresh
        self._on_quit = on_quit
        self._data: dict | None = None
        self._icon: pystray.Icon | None = None

    def _create_icon_image(
        self, color: tuple = (140, 165, 255)
    ) -> Image.Image:
        """Generate a 64x64 tray icon: colored circle with white 'C'."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=color)
        # Draw "C" letter
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", 36
            )
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except (OSError, IOError):
                font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "C", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (64 - tw) // 2
        y = (64 - th) // 2 - bbox[1]
        draw.text((x, y), "C", fill=(255, 255, 255), font=font)
        return img

    def _icon_color_for_pct(self, pct: float) -> tuple:
        """Return RGB tuple for icon based on usage percentage."""
        if pct >= YELLOW_THRESHOLD:
            return (230, 64, 51)  # Red
        elif pct >= GREEN_THRESHOLD:
            return (217, 192, 26)  # Yellow
        return (140, 165, 255)  # Blue (default)

    def _build_menu(self) -> pystray.Menu:
        """Build the tray context menu."""
        data = self._data or {}
        session_pct = data.get("session_pct", 0) or 0
        weekly_pct = data.get("weekly_pct", 0) or 0
        sonnet_pct = data.get("sonnet_pct", 0) or 0

        return pystray.Menu(
            pystray.MenuItem(T("claude_usage"), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"\u23f1 {T('session_header')}: {session_pct:.0f}%",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                f"\U0001f4ca {T('weekly_all_header')}: {weekly_pct:.0f}%",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                f"\U0001f4ca {T('weekly_sonnet_header')}: {sonnet_pct:.0f}%",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"\U0001f4ca {T('show_detail')}", self._on_show_detail
            ),
            pystray.MenuItem(
                f"\U0001f504 {T('refresh_now')}", self._on_refresh
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(T("quit"), self._on_quit),
        )

    def update_data(self, data: dict) -> None:
        """Update tray with new monitoring data."""
        self._data = data
        if self._icon is not None:
            session_pct = data.get("session_pct", 0) or 0
            # Update icon color
            color = self._icon_color_for_pct(session_pct)
            self._icon.icon = self._create_icon_image(color)
            # Update menu
            self._icon.menu = self._build_menu()
            # Update tooltip
            self._icon.title = f"{T('app_title')}: {session_pct:.0f}%"

    def run(self) -> None:
        """Start the tray icon. Call from a daemon thread."""
        self._icon = pystray.Icon(
            "claude-token-monitor",
            icon=self._create_icon_image(),
            title=T("app_title"),
            menu=self._build_menu(),
        )
        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon is not None:
            self._icon.stop()
