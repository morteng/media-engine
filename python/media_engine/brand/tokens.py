"""
Design Tokens

Spacing, shadows, borders, transitions, z-index, breakpoints, and component tokens.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SpacingScale:
    """Spacing scale based on a base unit."""

    unit: int = 4  # Base unit in pixels
    scale: Dict[int, int] = field(
        default_factory=lambda: {
            0: 0,
            1: 4,
            2: 8,
            3: 12,
            4: 16,
            5: 20,
            6: 24,
            8: 32,
            10: 40,
            12: 48,
            16: 64,
            20: 80,
            24: 96,
        }
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpacingScale":
        scale_data = data.get("scale", {})
        if isinstance(scale_data, list):
            # Convert list to dict: [0, 4, 8, 12] -> {0: 0, 1: 4, 2: 8, 3: 12}
            scale_data = {i: v for i, v in enumerate(scale_data)}
        # If no scale provided, create with defaults by omitting scale param
        if scale_data:
            return cls(unit=data.get("unit", 4), scale=scale_data)
        return cls(unit=data.get("unit", 4))

    def get(self, key: int) -> int:
        """Get spacing value by key."""
        if key in self.scale:
            return self.scale[key]
        # Calculate based on unit if not in scale
        return key * self.unit

    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        variables = {}
        for key, value in self.scale.items():
            variables[f"--spacing-{key}"] = f"{value}px"
        return variables


@dataclass
class BorderRadius:
    """Border radius tokens."""

    none: int = 0
    sm: int = 2
    md: int = 4
    lg: int = 8
    xl: int = 12
    xxl: int = 16  # 2xl
    full: int = 9999

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BorderRadius":
        return cls(
            none=data.get("none", 0),
            sm=data.get("sm", 2),
            md=data.get("md", 4),
            lg=data.get("lg", 8),
            xl=data.get("xl", 12),
            xxl=data.get("2xl", data.get("xxl", 16)),
            full=data.get("full", 9999),
        )

    def get(self, size: str) -> int:
        """Get radius by name."""
        sizes = {
            "none": self.none,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
            "2xl": self.xxl,
            "full": self.full,
        }
        return sizes.get(size, self.md)


@dataclass
class BorderWidth:
    """Border width tokens."""

    thin: int = 1
    default: int = 1
    medium: int = 2
    thick: int = 4

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BorderWidth":
        return cls(
            thin=data.get("thin", 1),
            default=data.get("default", 1),
            medium=data.get("medium", 2),
            thick=data.get("thick", 4),
        )


@dataclass
class BorderTokens:
    """Complete border configuration."""

    radius: BorderRadius = field(default_factory=BorderRadius)
    width: BorderWidth = field(default_factory=BorderWidth)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BorderTokens":
        return cls(
            radius=BorderRadius.from_dict(data.get("radius", {})),
            width=BorderWidth.from_dict(data.get("width", {})),
        )

    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        variables = {}

        # Radius
        variables["--radius-none"] = f"{self.radius.none}px"
        variables["--radius-sm"] = f"{self.radius.sm}px"
        variables["--radius-md"] = f"{self.radius.md}px"
        variables["--radius-lg"] = f"{self.radius.lg}px"
        variables["--radius-xl"] = f"{self.radius.xl}px"
        variables["--radius-2xl"] = f"{self.radius.xxl}px"
        variables["--radius-full"] = f"{self.radius.full}px"

        # Width
        variables["--border-thin"] = f"{self.width.thin}px"
        variables["--border-default"] = f"{self.width.default}px"
        variables["--border-medium"] = f"{self.width.medium}px"
        variables["--border-thick"] = f"{self.width.thick}px"

        return variables


@dataclass
class ShadowTokens:
    """Shadow definitions."""

    xs: str = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    sm: str = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)"
    md: str = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
    lg: str = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)"
    xl: str = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"
    xxl: str = "0 25px 50px -12px rgba(0, 0, 0, 0.25)"  # 2xl
    inner: str = "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)"
    none: str = "none"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShadowTokens":
        return cls(
            xs=data.get("xs", cls.xs),
            sm=data.get("sm", cls.sm),
            md=data.get("md", cls.md),
            lg=data.get("lg", cls.lg),
            xl=data.get("xl", cls.xl),
            xxl=data.get("2xl", data.get("xxl", cls.xxl)),
            inner=data.get("inner", cls.inner),
            none=data.get("none", cls.none),
        )

    def get(self, size: str) -> str:
        """Get shadow by name."""
        shadows = {
            "xs": self.xs,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
            "2xl": self.xxl,
            "inner": self.inner,
            "none": self.none,
        }
        return shadows.get(size, self.md)

    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        return {
            "--shadow-xs": self.xs,
            "--shadow-sm": self.sm,
            "--shadow-md": self.md,
            "--shadow-lg": self.lg,
            "--shadow-xl": self.xl,
            "--shadow-2xl": self.xxl,
            "--shadow-inner": self.inner,
            "--shadow-none": self.none,
        }


@dataclass
class TransitionDuration:
    """Transition duration tokens."""

    fast: str = "150ms"
    normal: str = "200ms"
    slow: str = "300ms"
    slower: str = "500ms"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionDuration":
        return cls(
            fast=data.get("fast", cls.fast),
            normal=data.get("normal", cls.normal),
            slow=data.get("slow", cls.slow),
            slower=data.get("slower", cls.slower),
        )


@dataclass
class TransitionEasing:
    """Transition easing functions."""

    linear: str = "linear"
    ease: str = "ease"
    easeIn: str = "cubic-bezier(0.4, 0, 1, 1)"
    easeOut: str = "cubic-bezier(0, 0, 0.2, 1)"
    easeInOut: str = "cubic-bezier(0.4, 0, 0.2, 1)"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionEasing":
        return cls(
            linear=data.get("linear", cls.linear),
            ease=data.get("ease", cls.ease),
            easeIn=data.get("easeIn", cls.easeIn),
            easeOut=data.get("easeOut", cls.easeOut),
            easeInOut=data.get("easeInOut", cls.easeInOut),
        )


@dataclass
class TransitionTokens:
    """Complete transition configuration."""

    duration: TransitionDuration = field(default_factory=TransitionDuration)
    easing: TransitionEasing = field(default_factory=TransitionEasing)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionTokens":
        return cls(
            duration=TransitionDuration.from_dict(data.get("duration", {})),
            easing=TransitionEasing.from_dict(data.get("easing", {})),
        )

    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        return {
            "--transition-fast": self.duration.fast,
            "--transition-normal": self.duration.normal,
            "--transition-slow": self.duration.slow,
            "--transition-slower": self.duration.slower,
            "--ease-linear": self.easing.linear,
            "--ease-ease": self.easing.ease,
            "--ease-in": self.easing.easeIn,
            "--ease-out": self.easing.easeOut,
            "--ease-in-out": self.easing.easeInOut,
        }


@dataclass
class ZIndexScale:
    """Z-index layer definitions."""

    hide: int = -1
    base: int = 0
    raised: int = 10
    dropdown: int = 100
    sticky: int = 200
    overlay: int = 300
    modal: int = 400
    popover: int = 500
    tooltip: int = 600

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ZIndexScale":
        return cls(
            hide=data.get("hide", cls.hide),
            base=data.get("base", cls.base),
            raised=data.get("raised", cls.raised),
            dropdown=data.get("dropdown", cls.dropdown),
            sticky=data.get("sticky", cls.sticky),
            overlay=data.get("overlay", cls.overlay),
            modal=data.get("modal", cls.modal),
            popover=data.get("popover", cls.popover),
            tooltip=data.get("tooltip", cls.tooltip),
        )

    def get(self, layer: str) -> int:
        """Get z-index by layer name."""
        layers = {
            "hide": self.hide,
            "base": self.base,
            "raised": self.raised,
            "dropdown": self.dropdown,
            "sticky": self.sticky,
            "overlay": self.overlay,
            "modal": self.modal,
            "popover": self.popover,
            "tooltip": self.tooltip,
        }
        return layers.get(layer, self.base)

    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom property definitions."""
        return {
            "--z-hide": str(self.hide),
            "--z-base": str(self.base),
            "--z-raised": str(self.raised),
            "--z-dropdown": str(self.dropdown),
            "--z-sticky": str(self.sticky),
            "--z-overlay": str(self.overlay),
            "--z-modal": str(self.modal),
            "--z-popover": str(self.popover),
            "--z-tooltip": str(self.tooltip),
        }


@dataclass
class Breakpoints:
    """Responsive breakpoint definitions in pixels."""

    sm: int = 640
    md: int = 768
    lg: int = 1024
    xl: int = 1280
    xxl: int = 1536  # 2xl

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Breakpoints":
        return cls(
            sm=data.get("sm", cls.sm),
            md=data.get("md", cls.md),
            lg=data.get("lg", cls.lg),
            xl=data.get("xl", cls.xl),
            xxl=data.get("2xl", data.get("xxl", cls.xxl)),
        )

    def get(self, size: str) -> int:
        """Get breakpoint by name."""
        sizes = {
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
            "2xl": self.xxl,
        }
        return sizes.get(size, self.md)

    def media_query(self, size: str, type: str = "min") -> str:
        """Generate media query string."""
        value = self.get(size)
        return f"@media ({type}-width: {value}px)"


@dataclass
class ComponentTokens:
    """Component-level design tokens."""

    button: Dict[str, Any] = field(
        default_factory=lambda: {
            "borderRadius": "md",
            "paddingX": 4,
            "paddingY": 2,
            "fontSize": "base",
        }
    )
    card: Dict[str, Any] = field(
        default_factory=lambda: {
            "borderRadius": "lg",
            "padding": 6,
            "shadow": "md",
        }
    )
    input: Dict[str, Any] = field(
        default_factory=lambda: {
            "borderRadius": "md",
            "borderWidth": "thin",
            "paddingX": 3,
            "paddingY": 2,
        }
    )
    modal: Dict[str, Any] = field(
        default_factory=lambda: {
            "borderRadius": "xl",
            "padding": 6,
            "shadow": "xl",
        }
    )
    badge: Dict[str, Any] = field(
        default_factory=lambda: {
            "borderRadius": "full",
            "paddingX": 2,
            "paddingY": 1,
            "fontSize": "xs",
        }
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentTokens":
        instance = cls()
        if "button" in data:
            instance.button = {**instance.button, **data["button"]}
        if "card" in data:
            instance.card = {**instance.card, **data["card"]}
        if "input" in data:
            instance.input = {**instance.input, **data["input"]}
        if "modal" in data:
            instance.modal = {**instance.modal, **data["modal"]}
        if "badge" in data:
            instance.badge = {**instance.badge, **data["badge"]}
        return instance

    def get(self, component: str, property: str) -> Optional[Any]:
        """Get component token value."""
        component_tokens = getattr(self, component, None)
        if component_tokens and isinstance(component_tokens, dict):
            return component_tokens.get(property)
        return None
