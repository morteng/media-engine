"""
Brand Profile

The main container class that holds all brand configuration.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .colors import ColorSystem
from .fonts import FontRegistry
from .logos import LogoAssets
from .tokens import (
    BorderTokens,
    Breakpoints,
    ComponentTokens,
    ShadowTokens,
    SpacingScale,
    TransitionTokens,
    ZIndexScale,
)
from .typography import Typography
from .voice import VoiceProfile


@dataclass
class LegalInfo:
    """Legal and copyright information."""

    copyright: str = ""
    tagline: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LegalInfo":
        return cls(
            copyright=data.get("copyright", ""),
            tagline=data.get("tagline", ""),
        )


@dataclass
class Identity:
    """Brand identity including logos and legal info."""

    logos: LogoAssets = field(default_factory=LogoAssets)
    legal: LegalInfo = field(default_factory=LegalInfo)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Identity":
        return cls(
            logos=LogoAssets.from_dict(data.get("logos", {})),
            legal=LegalInfo.from_dict(data.get("legal", {})),
        )

    def resolve(self, project_root: Path) -> "Identity":
        """Resolve logo paths against project root."""
        self.logos.resolve(project_root)
        return self


@dataclass
class BrandProfile:
    """
    Complete brand configuration.

    This is the single source of truth for all visual identity,
    replacing the legacy theme.yaml with a comprehensive design system.
    """

    name: str = "Default Brand"
    identity: Identity = field(default_factory=Identity)
    colors: ColorSystem = field(default_factory=ColorSystem)
    typography: Typography = field(default_factory=Typography)
    spacing: SpacingScale = field(default_factory=SpacingScale)
    borders: BorderTokens = field(default_factory=BorderTokens)
    shadows: ShadowTokens = field(default_factory=ShadowTokens)
    transitions: TransitionTokens = field(default_factory=TransitionTokens)
    zIndex: ZIndexScale = field(default_factory=ZIndexScale)
    breakpoints: Breakpoints = field(default_factory=Breakpoints)
    components: ComponentTokens = field(default_factory=ComponentTokens)
    voice: Optional[VoiceProfile] = None  # Voice and tone profile

    # Internal state
    _project_root: Optional[Path] = field(default=None, repr=False)
    _font_registry: Optional[FontRegistry] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Optional[Path] = None) -> "BrandProfile":
        """Create BrandProfile from dictionary (parsed YAML)."""
        # Load voice profile if present
        voice = None
        if "voice" in data:
            voice = VoiceProfile.from_dict(data["voice"])

        profile = cls(
            name=data.get("name", "Default Brand"),
            identity=Identity.from_dict(data.get("identity", {})),
            colors=ColorSystem.from_dict(data.get("colors", {})),
            typography=Typography.from_dict(data.get("typography", {})),
            spacing=SpacingScale.from_dict(data.get("spacing", {})),
            borders=BorderTokens.from_dict(data.get("borders", {})),
            shadows=ShadowTokens.from_dict(data.get("shadows", {})),
            transitions=TransitionTokens.from_dict(data.get("transitions", {})),
            zIndex=ZIndexScale.from_dict(data.get("zIndex", data.get("zindex", {}))),
            breakpoints=Breakpoints.from_dict(data.get("breakpoints", {})),
            components=ComponentTokens.from_dict(data.get("components", {})),
            voice=voice,
        )

        if project_root:
            profile._project_root = project_root
            profile.identity.resolve(project_root)

        return profile

    @classmethod
    def from_legacy_theme(
        cls, theme: "Theme", project_root: Optional[Path] = None
    ) -> "BrandProfile":
        """
        Create BrandProfile from legacy Theme object.

        This provides backward compatibility with existing theme.yaml files.
        """

        # Map legacy colors to new color system
        colors = ColorSystem(
            brand=cls._map_legacy_brand_colors(theme),
            text=cls._map_legacy_text_colors(theme),
            background=cls._map_legacy_background_colors(theme),
            dark=cls._map_legacy_dark_colors(theme),
        )

        # Map legacy typography
        typography = cls._map_legacy_typography(theme)

        profile = cls(
            name=theme.name,
            colors=colors,
            typography=typography,
        )

        profile._project_root = project_root
        return profile

    @classmethod
    def _map_legacy_brand_colors(cls, theme: "Theme") -> "BrandColors":
        from .colors import BrandColors

        return BrandColors(
            primary=theme.colors.primary,
            secondary=theme.colors.secondary,
            accent=theme.colors.accent,
        )

    @classmethod
    def _map_legacy_text_colors(cls, theme: "Theme") -> "TextColors":
        from .colors import TextColors

        return TextColors(
            primary=theme.colors.text,
            muted=theme.colors.muted,
        )

    @classmethod
    def _map_legacy_background_colors(cls, theme: "Theme") -> "BackgroundColors":
        from .colors import BackgroundColors

        return BackgroundColors(
            primary=theme.colors.background,
            secondary=theme.colors.surface,
        )

    @classmethod
    def _map_legacy_dark_colors(cls, theme: "Theme") -> "DarkModeColors":
        from .colors import BackgroundColors, DarkModeColors, TextColors

        return DarkModeColors(
            text=TextColors(
                primary=theme.dark.text,
                muted=theme.dark.muted,
            ),
            background=BackgroundColors(
                primary=theme.dark.background,
                secondary=theme.dark.surface,
            ),
        )

    @classmethod
    def _map_legacy_typography(cls, theme: "Theme") -> Typography:
        from .typography import FontAsset

        return Typography(
            heading=FontAsset(family=theme.typography.heading),
            body=FontAsset(family=theme.typography.body),
            code=FontAsset(family=theme.typography.code),
        )

    @property
    def fonts(self) -> FontRegistry:
        """Get font registry for this brand."""
        if self._font_registry is None:
            self._font_registry = FontRegistry(
                heading=self.typography.heading,
                body=self.typography.body,
                code=self.typography.code,
            )
        return self._font_registry

    @property
    def logos(self) -> LogoAssets:
        """Shortcut to identity.logos."""
        return self.identity.logos

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "identity": {
                "logos": {
                    "primary": {"path": self.logos.primary.path, "alt": self.logos.primary.alt},
                    "dark": {"path": self.logos.dark.path},
                    "square": {"path": self.logos.square.path},
                    "icon": {"path": self.logos.icon.path, "sizes": self.logos.icon.sizes},
                },
                "legal": {
                    "copyright": self.identity.legal.copyright,
                    "tagline": self.identity.legal.tagline,
                },
            },
            "colors": {
                "brand": {
                    "primary": self.colors.brand.primary,
                    "secondary": self.colors.brand.secondary,
                    "accent": self.colors.brand.accent,
                },
                "semantic": {
                    "success": self.colors.semantic.success,
                    "warning": self.colors.semantic.warning,
                    "error": self.colors.semantic.error,
                    "info": self.colors.semantic.info,
                },
                # ... other color sections
            },
            "typography": {
                "fonts": {
                    "heading": {
                        "family": self.typography.heading.family,
                        "weights": self.typography.heading.weights,
                        "source": self.typography.heading.source,
                    },
                    "body": {
                        "family": self.typography.body.family,
                        "weights": self.typography.body.weights,
                        "source": self.typography.body.source,
                    },
                    "code": {
                        "family": self.typography.code.family,
                        "weights": self.typography.code.weights,
                        "source": self.typography.code.source,
                    },
                },
                "scale": {
                    "xs": self.typography.scale.xs,
                    "sm": self.typography.scale.sm,
                    "base": self.typography.scale.base,
                    "lg": self.typography.scale.lg,
                    "xl": self.typography.scale.xl,
                    "2xl": self.typography.scale.xxl,
                    "3xl": self.typography.scale.xxxl,
                    "4xl": self.typography.scale.xxxxl,
                    "5xl": self.typography.scale.xxxxxl,
                    "6xl": self.typography.scale.xxxxxxl,
                    "display": self.typography.scale.display,
                },
            },
            "spacing": {
                "unit": self.spacing.unit,
                "scale": self.spacing.scale,
            },
            "borders": {
                "radius": {
                    "none": self.borders.radius.none,
                    "sm": self.borders.radius.sm,
                    "md": self.borders.radius.md,
                    "lg": self.borders.radius.lg,
                    "xl": self.borders.radius.xl,
                    "2xl": self.borders.radius.xxl,
                    "full": self.borders.radius.full,
                },
                "width": {
                    "thin": self.borders.width.thin,
                    "default": self.borders.width.default,
                    "medium": self.borders.width.medium,
                    "thick": self.borders.width.thick,
                },
            },
            "shadows": {
                "xs": self.shadows.xs,
                "sm": self.shadows.sm,
                "md": self.shadows.md,
                "lg": self.shadows.lg,
                "xl": self.shadows.xl,
                "2xl": self.shadows.xxl,
                "inner": self.shadows.inner,
            },
            "transitions": {
                "duration": {
                    "fast": self.transitions.duration.fast,
                    "normal": self.transitions.duration.normal,
                    "slow": self.transitions.duration.slow,
                    "slower": self.transitions.duration.slower,
                },
                "easing": {
                    "linear": self.transitions.easing.linear,
                    "ease": self.transitions.easing.ease,
                    "easeIn": self.transitions.easing.easeIn,
                    "easeOut": self.transitions.easing.easeOut,
                    "easeInOut": self.transitions.easing.easeInOut,
                },
            },
            "zIndex": {
                "hide": self.zIndex.hide,
                "base": self.zIndex.base,
                "raised": self.zIndex.raised,
                "dropdown": self.zIndex.dropdown,
                "sticky": self.zIndex.sticky,
                "overlay": self.zIndex.overlay,
                "modal": self.zIndex.modal,
                "popover": self.zIndex.popover,
                "tooltip": self.zIndex.tooltip,
            },
            "breakpoints": {
                "sm": self.breakpoints.sm,
                "md": self.breakpoints.md,
                "lg": self.breakpoints.lg,
                "xl": self.breakpoints.xl,
                "2xl": self.breakpoints.xxl,
            },
            "components": {
                "button": self.components.button,
                "card": self.components.card,
                "input": self.components.input,
                "modal": self.components.modal,
                "badge": self.components.badge,
            },
        }

    def generate_css_variables(self, dark_mode: bool = False) -> str:
        """Generate complete CSS custom properties."""
        all_vars: Dict[str, str] = {}

        # Collect all CSS variables
        all_vars.update(self.colors.to_css_variables(dark_mode))
        all_vars.update(self.typography.to_css_variables())
        all_vars.update(self.spacing.to_css_variables())
        all_vars.update(self.borders.to_css_variables())
        all_vars.update(self.shadows.to_css_variables())
        all_vars.update(self.transitions.to_css_variables())
        all_vars.update(self.zIndex.to_css_variables())

        # Format as CSS
        lines = [":root {"]
        for name, value in sorted(all_vars.items()):
            lines.append(f"    {name}: {value};")
        lines.append("}")

        return "\n".join(lines)
