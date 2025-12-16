"""
Theme Management

Load and apply design system themes from YAML files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


@dataclass
class ColorPalette:
    """Color palette definition."""
    primary: str = "#000000"
    secondary: str = "#333333"
    accent: str = "#0066cc"
    background: str = "#ffffff"
    text: str = "#000000"
    muted: str = "#666666"
    border: str = "#e0e0e0"


@dataclass
class DarkColors:
    """Dark mode color overrides."""
    background: str = "#1a1a1a"
    text: str = "#f0f0f0"
    accent: str = "#3399ff"
    muted: str = "#999999"
    border: str = "#333333"


@dataclass
class Typography:
    """Typography settings."""
    heading: str = "sans-serif"
    body: str = "sans-serif"
    code: str = "monospace"
    base_size: int = 16
    scale: float = 1.25


@dataclass
class Theme:
    """Complete design system theme."""
    name: str = "default"
    colors: ColorPalette = field(default_factory=ColorPalette)
    dark: DarkColors = field(default_factory=DarkColors)
    typography: Typography = field(default_factory=Typography)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Theme":
        """Create Theme from dictionary."""
        colors = data.get("colors", {})
        dark = colors.get("dark", {})
        typography = data.get("typography", {})

        return cls(
            name=data.get("name", "default"),
            colors=ColorPalette(
                primary=colors.get("primary", "#000000"),
                secondary=colors.get("secondary", "#333333"),
                accent=colors.get("accent", "#0066cc"),
                background=colors.get("background", "#ffffff"),
                text=colors.get("text", colors.get("primary", "#000000")),
                muted=colors.get("muted", "#666666"),
                border=colors.get("border", "#e0e0e0"),
            ),
            dark=DarkColors(
                background=dark.get("background", "#1a1a1a"),
                text=dark.get("text", "#f0f0f0"),
                accent=dark.get("accent", colors.get("accent", "#3399ff")),
                muted=dark.get("muted", "#999999"),
                border=dark.get("border", "#333333"),
            ),
            typography=Typography(
                heading=typography.get("heading", "sans-serif"),
                body=typography.get("body", "sans-serif"),
                code=typography.get("code", "monospace"),
                base_size=typography.get("base_size", 16),
                scale=typography.get("scale", 1.25),
            ),
            extra={k: v for k, v in data.items()
                   if k not in ("name", "colors", "typography")},
        )

    def get_color(self, name: str, dark_mode: bool = False) -> str:
        """Get color by name, with dark mode support."""
        if dark_mode:
            if hasattr(self.dark, name):
                return getattr(self.dark, name)
        if hasattr(self.colors, name):
            return getattr(self.colors, name)
        return self.colors.primary


def load_theme(path: Path) -> Theme:
    """
    Load theme from YAML file.

    Args:
        path: Path to theme.yaml file

    Returns:
        Theme object with loaded settings
    """
    if not path.exists():
        return Theme()

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    return Theme.from_dict(data)


# Predefined themes
COPPER_AND_CREAM = Theme(
    name="Copper & Cream",
    colors=ColorPalette(
        primary="#2c2522",
        secondary="#4a4340",
        accent="#c45c3c",
        background="#fdfbf9",
        text="#2c2522",
        muted="#6b6461",
        border="#e8e4e0",
    ),
    dark=DarkColors(
        background="#1a1816",
        text="#f5f2ef",
        accent="#d4775a",
        muted="#9a9592",
        border="#3d3835",
    ),
    typography=Typography(
        heading="Fraunces",
        body="Source Sans 3",
        code="JetBrains Mono",
        base_size=16,
        scale=1.25,
    ),
)
