"""Claude Token Monitor - macOS status bar application entry point."""

import sys
import os
import warnings

# Suppress harmless PyObjC pointer warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="PyObjCPointer")

# Ensure the project root is on the import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor.combined import CombinedMonitor
from ui.menubar import TokenMenuBarApp
from ui.floating_panel import FloatingPanel


def main():
    # Initialize monitoring backend
    monitor = CombinedMonitor()

    # Create the floating detail panel
    panel = FloatingPanel()

    # Create the status bar app
    app = TokenMenuBarApp()
    app.set_monitor(monitor)
    app.set_panel(panel)

    # Run the rumps event loop (blocks until quit)
    # The first data fetch happens via the rumps timer on startup
    app.run()


if __name__ == "__main__":
    main()
