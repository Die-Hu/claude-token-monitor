"""Dark theme constants for Claude Token Monitor UI."""

# Colors
BG_COLOR = "#14141e"
ACCENT_COLOR = "#8ca5ff"
TEXT_COLOR = "#ffffff"
DIM_COLOR = "#999999"
GREEN = "#33b366"
YELLOW = "#d9c01a"
RED = "#e64033"
BAR_BG = "#333344"
CACHE_COLOR = "#80cc80"

# Thresholds
GREEN_THRESHOLD = 40
YELLOW_THRESHOLD = 70

# Fonts
FONT_FAMILY = "Helvetica"
MONO_FONT_FAMILY = "Courier"
FONT_SIZE_NORMAL = 12
FONT_SIZE_SMALL = 10
FONT_SIZE_TITLE = 16
FONT_SIZE_SECTION = 11
FONT_SIZE_PCT = 13

# Layout
PANEL_WIDTH = 340
PANEL_HEIGHT = 460
PAD = 16
GAP = 8


def bar_color(pct: float) -> str:
    """Return color hex for a usage percentage."""
    if pct < GREEN_THRESHOLD:
        return GREEN
    elif pct < YELLOW_THRESHOLD:
        return YELLOW
    return RED
