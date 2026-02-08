"""Claude Token Monitor - Cross-platform entry point.

Architecture:
  - tkinter on main thread (hidden root window)
  - pystray in daemon thread
  - Data refresh every 60s via root.after(), first fetch at 2s
  - Thread-safe UI updates via root.after(0, callback)
"""

import sys
import threading
import tkinter as tk

from claude_token_monitor import i18n
from claude_token_monitor.monitor.combined import CombinedMonitor
from claude_token_monitor.ui.tray import TrayIcon
from claude_token_monitor.ui.detail_window import DetailWindow

REFRESH_INTERVAL_MS = 60_000  # 60 seconds
FIRST_FETCH_DELAY_MS = 2_000  # 2 seconds


class App:
    """Main application wiring tkinter, pystray, and the monitor backend."""

    def __init__(self):
        i18n.init()

        self._monitor = CombinedMonitor()

        # Hidden root window (tkinter must run on main thread)
        self._root = tk.Tk()
        self._root.withdraw()

        # Detail window (tkinter Toplevel, initially hidden)
        self._detail = DetailWindow(self._root)

        # System tray (runs in daemon thread)
        self._tray = TrayIcon(
            on_show_detail=lambda *_: self._root.after(0, self._detail.toggle),
            on_refresh=lambda *_: self._root.after(0, self._do_refresh),
            on_quit=lambda *_: self._root.after(0, self._quit),
        )

        # Schedule first data fetch
        self._root.after(FIRST_FETCH_DELAY_MS, self._do_refresh)

    def run(self):
        """Start the application."""
        # Start tray in daemon thread
        tray_thread = threading.Thread(target=self._tray.run, daemon=True)
        tray_thread.start()

        # Run tkinter main loop (blocks until quit)
        self._root.mainloop()

    def _do_refresh(self):
        """Fetch data in a background thread, then update UI on main thread."""
        thread = threading.Thread(target=self._fetch_and_update, daemon=True)
        thread.start()

    def _fetch_and_update(self):
        """Run in background thread: fetch data, then schedule UI update."""
        try:
            data = self._monitor.refresh()
        except Exception as e:
            data = {"error": str(e), "session_pct": 0}

        # Schedule UI update on main thread
        self._root.after(0, self._update_ui, data)

    def _update_ui(self, data):
        """Update both tray and detail window (must run on main thread)."""
        try:
            self._tray.update_data(data)
        except Exception:
            pass

        try:
            self._detail.update_data(data)
        except Exception:
            pass

        # Schedule next refresh
        self._root.after(REFRESH_INTERVAL_MS, self._do_refresh)

    def _quit(self):
        """Clean shutdown."""
        self._tray.stop()
        self._root.quit()
        self._root.destroy()


def main():
    """Application entry point."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
