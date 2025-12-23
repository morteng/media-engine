"""
Brand Typography System

Font definitions, type scale, line heights, and letter spacing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FontAsset:
    """Individual font family configuration."""

    family: str = "Inter"
    weights: List[int] = field(default_factory=lambda: [400, 500, 600, 700])
    source: str = "google"  # "google", "local", or "url"
    fallback: List[str] = field(default_factory=lambda: ["system-ui", "sans-serif"])
    local_path: Optional[str] = None  # Path to local font files

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FontAsset":
        if isinstance(data, str):
            # Simple string format: just the family name
            return cls(family=data)
        return cls(
            family=data.get("family", "Inter"),
            weights=data.get("weights", [400, 500, 600, 700]),
            source=data.get("source", "google"),
            fallback=data.get("fallback", ["system-ui", "sans-serif"]),
            local_path=data.get("local_path"),
        )

    def get_font_stack(self) -> str:
        """Get complete CSS font stack with fallbacks."""
        fonts = [f'"{self.family}"'] + [f'"{f}"' if " " in f else f for f in self.fallback]
        return ", ".join(fonts)

    def get_system_font(self) -> str:
        """Map to system font for Office applications."""
        system_map = {
            "Inter": "Helvetica Neue",
            "Fraunces": "Georgia",
            "Source Sans 3": "Helvetica Neue",
            "JetBrains Mono": "Menlo",
            "Roboto": "Helvetica",
            "Open Sans": "Helvetica Neue",
            "Lato": "Helvetica Neue",
            "Montserrat": "Helvetica Neue",
            "Playfair Display": "Georgia",
            "Merriweather": "Georgia",
            "Fira Code": "Menlo",
            "Source Code Pro": "Menlo",
        }
        return system_map.get(self.family, self.family)


@dataclass
class FontScale:
    """Type scale definitions in pixels."""

    xs: int = 12
    sm: int = 14
    base: int = 16
    lg: int = 18
    xl: int = 20
    xxl: int = 24  # 2xl
    xxxl: int = 30  # 3xl
    xxxxl: int = 36  # 4xl
    xxxxxl: int = 48  # 5xl
    xxxxxxl: int = 60  # 6xl
    display: int = 72

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FontScale":
        return cls(
            xs=data.get("xs", 12),
            sm=data.get("sm", 14),
            base=data.get("base", 16),
            lg=data.get("lg", 18),
            xl=data.get("xl", 20),
            xxl=data.get("2xl", data.get("xxl", 24)),
            xxxl=data.get("3xl", data.get("xxxl", 30)),
            xxxxl=data.get("4xl", data.get("xxxxl", 36)),
            xxxxxl=data.get("5xl", data.get("xxxxxl", 48)),
            xxxxxxl=data.get("6xl", data.get("xxxxxxl", 60)),
            display=data.get("display", 72),
        )

    def get(self, size: str) -> int:
        """Get size by name."""
        size_map = {
            "xs": self.xs,
            "sm": self.sm,
            "base": self.base,
            "lg": self.lg,
            "xl": self.xl,
            "2xl": self.xxl,
            "3xl": self.xxxl,
            "4xl": self.xxxxl,
            "5xl": self.xxxxxl,
            "6xl": self.xxxxxxl,
            "display": self.display,
        }
        return size_map.get(size, self.base)


@dataclass
class LineHeight:
    """Line height definitions."""

    tight: float = 1.25
    normal: float = 1.5
    relaxed: float = 1.75

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineHeight":
        return cls(
            tight=data.get("tight", 1.25),
            normal=data.get("normal", 1.5),
            relaxed=data.get("relaxed", 1.75),
        )


@dataclass
class LetterSpacing:
    """Letter spacing definitions."""

    tight: str = "-0.025em"
    normal: str = "0"
    wide: str = "0.025em"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LetterSpacing":
        return cls(
            tight=data.get("tight", "-0.025em"),
            normal=data.get("normal", "0"),
            wide=data.get("wide", "0.025em"),
        )


@dataclass
class Typography:
    """Complete typography system."""

    heading: FontAsset = field(
        default_factory=lambda: FontAsset(
            family="Inter",
            weights=[500, 600, 700],
        )
    )
    body: FontAsset = field(
        default_factory=lambda: FontAsset(
            family="Inter",
            weights=[400, 500],
        )
    )
    code: FontAsset = field(
        default_factory=lambda: FontAsset(
            family="JetBrains Mono",
            weights=[400, 500],
            fallback=["SF Mono", "Monaco", "monospace"],
        )
    )
    scale: FontScale = field(default_factory=FontScale)
    lineHeight: LineHeight = field(default_factory=LineHeight)
    letterSpacing: LetterSpacing = field(default_factory=LetterSpacing)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Typography":
        fonts = data.get("fonts", {})
        return cls(
            heading=FontAsset.from_dict(fonts.get("heading", data.get("heading", {}))),
            body=FontAsset.from_dict(fonts.get("body", data.get("body", {}))),
            code=FontAsset.from_dict(fonts.get("code", data.get("code", {}))),
            scale=FontScale.from_dict(data.get("scale", {})),
            lineHeight=LineHeight.from_dict(data.get("lineHeight", {})),
            letterSpacing=LetterSpacing.from_dict(data.get("letterSpacing", {})),
        )

    def get_font(self, role: str) -> FontAsset:
        """Get font by role."""
        fonts = {
            "heading": self.heading,
            "body": self.body,
            "code": self.code,
        }
        return fonts.get(role, self.body)

    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        variables = {}

        # Font families
        variables["--font-heading"] = self.heading.get_font_stack()
        variables["--font-body"] = self.body.get_font_stack()
        variables["--font-code"] = self.code.get_font_stack()

        # Font scale
        variables["--font-size-xs"] = f"{self.scale.xs}px"
        variables["--font-size-sm"] = f"{self.scale.sm}px"
        variables["--font-size-base"] = f"{self.scale.base}px"
        variables["--font-size-lg"] = f"{self.scale.lg}px"
        variables["--font-size-xl"] = f"{self.scale.xl}px"
        variables["--font-size-2xl"] = f"{self.scale.xxl}px"
        variables["--font-size-3xl"] = f"{self.scale.xxxl}px"
        variables["--font-size-4xl"] = f"{self.scale.xxxxl}px"
        variables["--font-size-5xl"] = f"{self.scale.xxxxxl}px"
        variables["--font-size-6xl"] = f"{self.scale.xxxxxxl}px"
        variables["--font-size-display"] = f"{self.scale.display}px"

        # Line heights
        variables["--line-height-tight"] = str(self.lineHeight.tight)
        variables["--line-height-normal"] = str(self.lineHeight.normal)
        variables["--line-height-relaxed"] = str(self.lineHeight.relaxed)

        # Letter spacing
        variables["--letter-spacing-tight"] = self.letterSpacing.tight
        variables["--letter-spacing-normal"] = self.letterSpacing.normal
        variables["--letter-spacing-wide"] = self.letterSpacing.wide

        return variables
