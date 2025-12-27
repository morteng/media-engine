"""
Brand Adapter Module

Provides color and font resolution from BrandContext/Theme for diagram engines.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..brand import BrandContext
    from ..core.theme import Theme


# Default color palettes
DEFAULT_LIGHT_COLORS = {
    "background": "#ffffff",
    "text": "#1f2937",
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "accent": "#06b6d4",
    "box_fill": "#f9fafb",
    "box_border": "#6366f1",
    "arrow": "#9ca3af",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
}

DEFAULT_DARK_COLORS = {
    "background": "#111827",
    "text": "#f9fafb",
    "primary": "#818cf8",
    "secondary": "#a78bfa",
    "accent": "#22d3ee",
    "box_fill": "#1f2937",
    "box_border": "#818cf8",
    "arrow": "#6b7280",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#f87171",
    "info": "#60a5fa",
}


def get_engine_colors(
    brand: Optional["BrandContext"],
    theme: Optional["Theme"],
    dark_mode: bool = False,
) -> dict[str, str]:
    """
    Get standardized color palette for diagram engines.

    Returns a dict with keys:
        background, text, primary, secondary, accent,
        box_fill, box_border, arrow, success, warning, error, info

    Args:
        brand: BrandContext instance (preferred)
        theme: Legacy Theme instance (fallback)
        dark_mode: Whether to use dark mode colors

    Returns:
        Dictionary of color name to hex color value
    """
    if brand:
        return _colors_from_brand(brand, dark_mode)
    elif theme:
        return _colors_from_theme(theme, dark_mode)
    else:
        return DEFAULT_DARK_COLORS if dark_mode else DEFAULT_LIGHT_COLORS


def _colors_from_brand(brand: "BrandContext", dark_mode: bool) -> dict[str, str]:
    """Extract colors from BrandContext."""
    return {
        "background": brand.get_color("background.primary", dark_mode) or (
            DEFAULT_DARK_COLORS["background"] if dark_mode else DEFAULT_LIGHT_COLORS["background"]
        ),
        "text": brand.get_color("text.primary", dark_mode) or (
            DEFAULT_DARK_COLORS["text"] if dark_mode else DEFAULT_LIGHT_COLORS["text"]
        ),
        "primary": brand.get_brand_color("primary") or DEFAULT_LIGHT_COLORS["primary"],
        "secondary": brand.get_brand_color("secondary") or DEFAULT_LIGHT_COLORS["secondary"],
        "accent": brand.get_brand_color("accent") or DEFAULT_LIGHT_COLORS["accent"],
        "box_fill": brand.get_color("surface.default", dark_mode) or (
            DEFAULT_DARK_COLORS["box_fill"] if dark_mode else DEFAULT_LIGHT_COLORS["box_fill"]
        ),
        "box_border": brand.get_brand_color("primary") or DEFAULT_LIGHT_COLORS["primary"],
        "arrow": brand.get_color("text.muted", dark_mode) or (
            DEFAULT_DARK_COLORS["arrow"] if dark_mode else DEFAULT_LIGHT_COLORS["arrow"]
        ),
        "success": brand.get_semantic_color("success") or DEFAULT_LIGHT_COLORS["success"],
        "warning": brand.get_semantic_color("warning") or DEFAULT_LIGHT_COLORS["warning"],
        "error": brand.get_semantic_color("error") or DEFAULT_LIGHT_COLORS["error"],
        "info": brand.get_semantic_color("info") or DEFAULT_LIGHT_COLORS["info"],
    }


def _colors_from_theme(theme: "Theme", dark_mode: bool) -> dict[str, str]:
    """Extract colors from legacy Theme."""
    if dark_mode:
        return {
            "background": getattr(theme.dark, "background", DEFAULT_DARK_COLORS["background"]),
            "text": getattr(theme.dark, "text", DEFAULT_DARK_COLORS["text"]),
            "primary": getattr(theme.colors, "primary", DEFAULT_LIGHT_COLORS["primary"]),
            "secondary": getattr(theme.colors, "secondary", DEFAULT_LIGHT_COLORS["secondary"]),
            "accent": getattr(theme.dark, "accent", DEFAULT_DARK_COLORS["accent"]),
            "box_fill": getattr(theme.dark, "surface", DEFAULT_DARK_COLORS["box_fill"]),
            "box_border": getattr(theme.dark, "accent", DEFAULT_DARK_COLORS["box_border"]),
            "arrow": getattr(theme.dark, "muted", DEFAULT_DARK_COLORS["arrow"]),
            "success": DEFAULT_DARK_COLORS["success"],
            "warning": DEFAULT_DARK_COLORS["warning"],
            "error": DEFAULT_DARK_COLORS["error"],
            "info": DEFAULT_DARK_COLORS["info"],
        }
    else:
        return {
            "background": getattr(theme.colors, "background", DEFAULT_LIGHT_COLORS["background"]),
            "text": getattr(theme.colors, "text", DEFAULT_LIGHT_COLORS["text"]),
            "primary": getattr(theme.colors, "primary", DEFAULT_LIGHT_COLORS["primary"]),
            "secondary": getattr(theme.colors, "secondary", DEFAULT_LIGHT_COLORS["secondary"]),
            "accent": getattr(theme.colors, "accent", DEFAULT_LIGHT_COLORS["accent"]),
            "box_fill": getattr(theme.colors, "surface", DEFAULT_LIGHT_COLORS["box_fill"]),
            "box_border": getattr(theme.colors, "primary", DEFAULT_LIGHT_COLORS["box_border"]),
            "arrow": getattr(theme.colors, "muted", DEFAULT_LIGHT_COLORS["arrow"]),
            "success": DEFAULT_LIGHT_COLORS["success"],
            "warning": DEFAULT_LIGHT_COLORS["warning"],
            "error": DEFAULT_LIGHT_COLORS["error"],
            "info": DEFAULT_LIGHT_COLORS["info"],
        }


def resolve_color(
    color_value: Optional[str],
    brand: Optional["BrandContext"],
    theme: Optional["Theme"],
    dark_mode: bool = False,
    default_key: str = "primary",
) -> str:
    """
    Resolve a color value which may be:
    - Hex color: "#ff0000"
    - Brand token: "brand.primary", "semantic.success"
    - None: returns default

    Args:
        color_value: Color specification (hex or token)
        brand: BrandContext instance
        theme: Legacy Theme instance
        dark_mode: Whether to use dark mode colors
        default_key: Key from engine colors to use as default

    Returns:
        Resolved hex color value
    """
    colors = get_engine_colors(brand, theme, dark_mode)

    if not color_value:
        return colors.get(default_key, colors["primary"])

    # Direct hex color
    if color_value.startswith("#"):
        return color_value

    # Try to resolve as brand token
    if brand:
        resolved = brand.get_color(color_value, dark_mode)
        if resolved:
            return resolved

    # Check if it's a semantic shorthand
    semantic_map = {
        "primary": colors["primary"],
        "secondary": colors["secondary"],
        "accent": colors["accent"],
        "success": colors["success"],
        "warning": colors["warning"],
        "error": colors["error"],
        "info": colors["info"],
    }

    if color_value in semantic_map:
        return semantic_map[color_value]

    # Return as-is (might be a color name like "red")
    return color_value


def get_font_family(
    brand: Optional["BrandContext"],
    theme: Optional["Theme"],
    role: str = "body",
) -> str:
    """
    Get font family for diagrams.

    Args:
        brand: BrandContext instance
        theme: Legacy Theme instance
        role: Font role - "heading", "body", or "code"

    Returns:
        Font family name suitable for the rendering engine
    """
    if brand:
        # Use system font for compatibility with various engines
        return brand.get_system_font(role) or "sans-serif"
    elif theme:
        font_map = {
            "heading": getattr(theme.typography, "heading", "sans-serif"),
            "body": getattr(theme.typography, "body", "sans-serif"),
            "code": getattr(theme.typography, "code", "monospace"),
        }
        return font_map.get(role, "sans-serif")
    else:
        default_fonts = {
            "heading": "sans-serif",
            "body": "sans-serif",
            "code": "monospace",
        }
        return default_fonts.get(role, "sans-serif")


def get_font_size(
    brand: Optional["BrandContext"],
    size_name: str = "base",
    scale: float = 1.0,
) -> float:
    """
    Get font size in points.

    Args:
        brand: BrandContext instance
        size_name: Size name from scale (xs, sm, base, lg, xl, etc.)
        scale: Additional scale factor

    Returns:
        Font size in points
    """
    if brand:
        size = brand.get_font_size(size_name)
        if size:
            return size * scale

    # Default font sizes
    default_sizes = {
        "xs": 10,
        "sm": 12,
        "base": 14,
        "lg": 16,
        "xl": 18,
        "2xl": 20,
        "3xl": 24,
    }
    return default_sizes.get(size_name, 14) * scale


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#ff0000" or "ff0000")

    Returns:
        Tuple of (r, g, b) values (0-255)
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB tuple to hex color.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Hex color string (e.g., "#ff0000")
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Lighten a hex color by a factor.

    Args:
        hex_color: Hex color string
        factor: Lightening factor (0-1)

    Returns:
        Lightened hex color
    """
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)


def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Darken a hex color by a factor.

    Args:
        hex_color: Hex color string
        factor: Darkening factor (0-1)

    Returns:
        Darkened hex color
    """
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return rgb_to_hex(r, g, b)
