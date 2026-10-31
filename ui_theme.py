"""
UI Theme & Design Tokens for Music Player.
Centralized styling ensures the UI is 100% customizable, extensible, and switchable.
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict


def hex_to_rgb(hex_str: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    """Convert hex string (e.g. '#1A1D27') to Kivy RGBA tuple (0.0 to 1.0)."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return (r, g, b, alpha)
    elif len(hex_str) == 8:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        a = int(hex_str[6:8], 16) / 255.0
        return (r, g, b, a)
    return (1.0, 1.0, 1.0, alpha)


@dataclass
class ThemeColors:
    # Backgrounds
    bg_primary: Tuple[float, float, float, float] = hex_to_rgb("#0E1118")
    bg_secondary: Tuple[float, float, float, float] = hex_to_rgb("#161B26")
    bg_card: Tuple[float, float, float, float] = hex_to_rgb("#1F2636")
    bg_card_hover: Tuple[float, float, float, float] = hex_to_rgb("#293247")
    bg_modal: Tuple[float, float, float, float] = hex_to_rgb("#0C0E14", 0.96)
    
    # Accent & Vibrant Highlights
    accent_primary: Tuple[float, float, float, float] = hex_to_rgb("#7C4DFF")       # Electric Violet
    accent_secondary: Tuple[float, float, float, float] = hex_to_rgb("#00E5FF")     # Cyber Cyan
    accent_gradient_end: Tuple[float, float, float, float] = hex_to_rgb("#FF4081")  # Neon Pink
    accent_active: Tuple[float, float, float, float] = hex_to_rgb("#651FFF")
    
    # Text colors
    text_primary: Tuple[float, float, float, float] = hex_to_rgb("#FFFFFF")
    text_secondary: Tuple[float, float, float, float] = hex_to_rgb("#A0ABC0")
    text_muted: Tuple[float, float, float, float] = hex_to_rgb("#5C667A")
    
    # Player Controls & Indicators
    progress_bar_bg: Tuple[float, float, float, float] = hex_to_rgb("#2A3347")
    progress_bar_fill: Tuple[float, float, float, float] = hex_to_rgb("#7C4DFF")
    slider_thumb: Tuple[float, float, float, float] = hex_to_rgb("#00E5FF")
    
    # Status & Badges
    badge_album: Tuple[float, float, float, float] = hex_to_rgb("#304FFE")
    badge_single: Tuple[float, float, float, float] = hex_to_rgb("#00B0FF")
    divider: Tuple[float, float, float, float] = hex_to_rgb("#202738")


@dataclass
class ThemeMetrics:
    # Corner Radii
    radius_sm: float = 8.0
    radius_md: float = 14.0
    radius_lg: float = 22.0
    radius_pill: float = 999.0
    
    # Padding & Spacing
    padding_screen: float = 14.0
    spacing_items: float = 10.0
    mini_player_height: float = 72.0
    header_height: float = 56.0
    bottom_nav_height: float = 58.0


# Pre-defined customizable themes
THEMES: Dict[str, ThemeColors] = {
    "neon_dark": ThemeColors(),
    "amoled_pure": ThemeColors(
        bg_primary=hex_to_rgb("#000000"),
        bg_secondary=hex_to_rgb("#080808"),
        bg_card=hex_to_rgb("#121212"),
        bg_card_hover=hex_to_rgb("#1E1E1E"),
        accent_primary=hex_to_rgb("#1DB954"),       # Emerald Spotify green
        accent_secondary=hex_to_rgb("#1ED760"),
        progress_bar_fill=hex_to_rgb("#1DB954"),
        slider_thumb=hex_to_rgb("#1ED760")
    ),
    "sunset_glow": ThemeColors(
        bg_primary=hex_to_rgb("#181124"),
        bg_secondary=hex_to_rgb("#231834"),
        bg_card=hex_to_rgb("#312247"),
        bg_card_hover=hex_to_rgb("#402D5C"),
        accent_primary=hex_to_rgb("#FF6B6B"),       # Coral Orange
        accent_secondary=hex_to_rgb("#FFA07A"),
        progress_bar_fill=hex_to_rgb("#FF6B6B"),
        slider_thumb=hex_to_rgb("#FFD166")
    )
}

# Current active theme singleton
current_theme_name = "neon_dark"
current_theme: ThemeColors = THEMES[current_theme_name]
current_metrics: ThemeMetrics = ThemeMetrics()


def set_theme(name: str) -> None:
    """Dynamically switch themes at runtime."""
    global current_theme_name, current_theme
    if name in THEMES:
        current_theme_name = name
        current_theme = THEMES[name]
