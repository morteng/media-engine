"""
Brand Color System

Comprehensive color definitions for brand identity, semantic states,
text hierarchy, backgrounds, surfaces, and borders.

Also includes color conversion utilities for use across builders.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

# =============================================================================
# COLOR CONVERSION UTILITIES
# =============================================================================


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (with or without #)

    Returns:
        Tuple of (red, green, blue) values 0-255
    """
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def hex_to_argb(hex_color: str) -> str:
    """
    Convert hex color to ARGB format for openpyxl.

    Args:
        hex_color: Hex color string

    Returns:
        ARGB string with FF prefix
    """
    hex_color = hex_color.lstrip("#")
    return f"FF{hex_color.upper()}"


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color string.

    Args:
        r: Red value 0-255
        g: Green value 0-255
        b: Blue value 0-255

    Returns:
        Hex color string with # prefix
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Lighten a hex color by the specified factor.

    Args:
        hex_color: Hex color string
        factor: Amount to lighten (0.0-1.0)

    Returns:
        Lightened hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)


def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Darken a hex color by the specified factor.

    Args:
        hex_color: Hex color string
        factor: Amount to darken (0.0-1.0)

    Returns:
        Darkened hex color string
    """
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return rgb_to_hex(r, g, b)


# =============================================================================
# COLOR DATACLASSES
# =============================================================================


@dataclass
class BrandColors:
    """Primary brand color palette."""

    primary: str = "#6366f1"
    secondary: str = "#8b5cf6"
    accent: str = "#06b6d4"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrandColors":
        return cls(
            primary=data.get("primary", cls.primary),
            secondary=data.get("secondary", cls.secondary),
            accent=data.get("accent", cls.accent),
        )


@dataclass
class SemanticColors:
    """Semantic colors for UI states and feedback."""

    success: str = "#10b981"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#3b82f6"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticColors":
        return cls(
            success=data.get("success", cls.success),
            warning=data.get("warning", cls.warning),
            error=data.get("error", cls.error),
            info=data.get("info", cls.info),
        )


@dataclass
class TextColors:
    """Text color hierarchy."""

    primary: str = "#1f2937"
    secondary: str = "#4b5563"
    muted: str = "#9ca3af"
    inverse: str = "#ffffff"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextColors":
        return cls(
            primary=data.get("primary", cls.primary),
            secondary=data.get("secondary", cls.secondary),
            muted=data.get("muted", cls.muted),
            inverse=data.get("inverse", cls.inverse),
        )


@dataclass
class BackgroundColors:
    """Background color hierarchy."""

    primary: str = "#ffffff"
    secondary: str = "#f9fafb"
    tertiary: str = "#f3f4f6"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackgroundColors":
        return cls(
            primary=data.get("primary", cls.primary),
            secondary=data.get("secondary", cls.secondary),
            tertiary=data.get("tertiary", cls.tertiary),
        )


@dataclass
class SurfaceColors:
    """Surface colors for cards, modals, and overlays."""

    default: str = "#ffffff"
    raised: str = "#f9fafb"
    overlay: str = "rgba(0,0,0,0.5)"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SurfaceColors":
        return cls(
            default=data.get("default", cls.default),
            raised=data.get("raised", cls.raised),
            overlay=data.get("overlay", cls.overlay),
        )


@dataclass
class BorderColors:
    """Border color hierarchy."""

    default: str = "#e5e7eb"
    subtle: str = "#f3f4f6"
    strong: str = "#d1d5db"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BorderColors":
        return cls(
            default=data.get("default", cls.default),
            subtle=data.get("subtle", cls.subtle),
            strong=data.get("strong", cls.strong),
        )


@dataclass
class DarkModeColors:
    """Dark mode color overrides."""

    text: TextColors = field(
        default_factory=lambda: TextColors(
            primary="#f9fafb",
            secondary="#e5e7eb",
            muted="#9ca3af",
            inverse="#111827",
        )
    )
    background: BackgroundColors = field(
        default_factory=lambda: BackgroundColors(
            primary="#111827",
            secondary="#1f2937",
            tertiary="#374151",
        )
    )
    surface: SurfaceColors = field(
        default_factory=lambda: SurfaceColors(
            default="#1f2937",
            raised="#374151",
            overlay="rgba(0,0,0,0.7)",
        )
    )
    border: BorderColors = field(
        default_factory=lambda: BorderColors(
            default="#374151",
            subtle="#4b5563",
            strong="#6b7280",
        )
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DarkModeColors":
        return cls(
            text=TextColors.from_dict(data.get("text", {})),
            background=BackgroundColors.from_dict(data.get("background", {})),
            surface=SurfaceColors.from_dict(data.get("surface", {})),
            border=BorderColors.from_dict(data.get("border", {})),
        )


@dataclass
class ColorSystem:
    """Complete color system for the brand."""

    brand: BrandColors = field(default_factory=BrandColors)
    semantic: SemanticColors = field(default_factory=SemanticColors)
    text: TextColors = field(default_factory=TextColors)
    background: BackgroundColors = field(default_factory=BackgroundColors)
    surface: SurfaceColors = field(default_factory=SurfaceColors)
    border: BorderColors = field(default_factory=BorderColors)
    dark: DarkModeColors = field(default_factory=DarkModeColors)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorSystem":
        return cls(
            brand=BrandColors.from_dict(data.get("brand", {})),
            semantic=SemanticColors.from_dict(data.get("semantic", {})),
            text=TextColors.from_dict(data.get("text", {})),
            background=BackgroundColors.from_dict(data.get("background", {})),
            surface=SurfaceColors.from_dict(data.get("surface", {})),
            border=BorderColors.from_dict(data.get("border", {})),
            dark=DarkModeColors.from_dict(data.get("dark", {})),
        )

    def get(self, path: str, dark_mode: bool = False) -> Optional[str]:
        """
        Get a color by dot-notation path.

        Args:
            path: Color path like "brand.primary", "semantic.success", "text.muted"
            dark_mode: If True, use dark mode overrides where applicable

        Returns:
            Color value as hex string or None if not found
        """
        parts = path.split(".")
        if len(parts) < 2:
            return None

        category, name = parts[0], parts[1]

        # Dark mode overrides
        if dark_mode and category in ("text", "background", "surface", "border"):
            dark_obj = getattr(self.dark, category, None)
            if dark_obj and hasattr(dark_obj, name):
                return getattr(dark_obj, name)

        # Regular colors
        category_obj = getattr(self, category, None)
        if category_obj and hasattr(category_obj, name):
            return getattr(category_obj, name)

        return None

    def to_css_variables(self, dark_mode: bool = False) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        variables = {}

        # Brand colors
        variables["--color-brand-primary"] = self.brand.primary
        variables["--color-brand-secondary"] = self.brand.secondary
        variables["--color-brand-accent"] = self.brand.accent

        # Semantic colors
        variables["--color-success"] = self.semantic.success
        variables["--color-warning"] = self.semantic.warning
        variables["--color-error"] = self.semantic.error
        variables["--color-info"] = self.semantic.info

        # Text, background, surface, border (with dark mode support)
        text = self.dark.text if dark_mode else self.text
        bg = self.dark.background if dark_mode else self.background
        surface = self.dark.surface if dark_mode else self.surface
        border = self.dark.border if dark_mode else self.border

        variables["--color-text-primary"] = text.primary
        variables["--color-text-secondary"] = text.secondary
        variables["--color-text-muted"] = text.muted
        variables["--color-text-inverse"] = text.inverse

        variables["--color-bg-primary"] = bg.primary
        variables["--color-bg-secondary"] = bg.secondary
        variables["--color-bg-tertiary"] = bg.tertiary

        variables["--color-surface-default"] = surface.default
        variables["--color-surface-raised"] = surface.raised
        variables["--color-surface-overlay"] = surface.overlay

        variables["--color-border-default"] = border.default
        variables["--color-border-subtle"] = border.subtle
        variables["--color-border-strong"] = border.strong

        return variables
