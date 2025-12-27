"""
Brand Context

Unified interface for builders to access brand assets.
This is the primary facade that builders should use.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from .colors import hex_to_argb as _hex_to_argb
from .colors import hex_to_rgb as _hex_to_rgb
from .profile import BrandProfile

if TYPE_CHECKING:
    from ..core.theme import Theme


@dataclass
class BrandContext:
    """
    Unified interface for builders to access brand assets.

    Provides convenience methods for:
    - Getting colors by path (with dark mode support)
    - Getting logos in specific formats (auto-converts SVG to PNG)
    - Getting font families and system font mappings
    - Generating CSS variables and @font-face rules
    """

    profile: BrandProfile
    output_dir: Optional[Path] = None
    dark_mode: bool = False

    # Cache for generated assets
    _css_cache: Optional[str] = field(default=None, repr=False)

    # === COLOR ACCESS ===

    def get_color(self, path: str, dark_mode: Optional[bool] = None) -> Optional[str]:
        """
        Get a color by dot-notation path.

        Args:
            path: Color path like "brand.primary", "semantic.success", "text.muted"
            dark_mode: Override dark mode setting (uses context default if None)

        Returns:
            Color value as hex string or None if not found

        Examples:
            ctx.get_color("brand.primary")      # "#6366f1"
            ctx.get_color("semantic.success")   # "#10b981"
            ctx.get_color("text.primary", dark_mode=True)  # "#f9fafb"
        """
        use_dark = dark_mode if dark_mode is not None else self.dark_mode
        return self.profile.colors.get(path, use_dark)

    def get_brand_color(self, name: str = "primary") -> str:
        """Get a brand color by name."""
        colors = {
            "primary": self.profile.colors.brand.primary,
            "secondary": self.profile.colors.brand.secondary,
            "accent": self.profile.colors.brand.accent,
        }
        return colors.get(name, self.profile.colors.brand.primary)

    def get_semantic_color(self, name: str) -> str:
        """Get a semantic color by name."""
        colors = {
            "success": self.profile.colors.semantic.success,
            "warning": self.profile.colors.semantic.warning,
            "error": self.profile.colors.semantic.error,
            "info": self.profile.colors.semantic.info,
        }
        return colors.get(name, self.profile.colors.brand.accent)

    # === LOGO ACCESS ===

    def get_logo(
        self,
        variant: str = "primary",
        format: str = "auto",
        size: Optional[int] = None,
    ) -> Optional[Path]:
        """
        Get logo in requested format.

        Args:
            variant: Logo variant ("primary", "dark", "square", "icon", "watermark")
            format: Output format ("svg", "png", "auto")
            size: Size for PNG conversion (height in pixels)

        Returns:
            Path to logo file or None if not available

        Examples:
            ctx.get_logo()                      # Primary logo, original format
            ctx.get_logo("dark", "svg")         # Dark variant, SVG format
            ctx.get_logo("primary", "png", 200) # Primary logo, 200px PNG
        """
        logo_asset = self.profile.logos.get(variant)
        if not logo_asset or not logo_asset.exists():
            # Try fallback to primary
            logo_asset = self.profile.logos.get_best_available(variant)
            if not logo_asset:
                return None

        return logo_asset.get_for_format(format, size)

    def has_logo(self, variant: str = "primary") -> bool:
        """Check if a logo variant exists."""
        logo_asset = self.profile.logos.get(variant)
        return logo_asset is not None and logo_asset.exists()

    # === FONT ACCESS ===

    def get_font_family(self, role: str = "body") -> str:
        """
        Get font family name for a role.

        Args:
            role: Font role ("heading", "body", "code")

        Returns:
            Font family name
        """
        font = self.profile.typography.get_font(role)
        return font.family

    def get_font_stack(self, role: str = "body") -> str:
        """
        Get complete CSS font stack with fallbacks.

        Args:
            role: Font role ("heading", "body", "code")

        Returns:
            CSS font-family string with fallbacks
        """
        font = self.profile.typography.get_font(role)
        return font.get_font_stack()

    def get_system_font(self, role: str = "body") -> str:
        """
        Get system font equivalent for Office applications.

        Maps web fonts to safe system fonts for PPTX/XLSX.

        Args:
            role: Font role ("heading", "body", "code")

        Returns:
            System font name
        """
        font = self.profile.typography.get_font(role)
        return font.get_system_font()

    # === SPACING & TOKENS ===

    def get_spacing(self, key: int) -> int:
        """Get spacing value by key."""
        return self.profile.spacing.get(key)

    def get_radius(self, size: str = "md") -> int:
        """Get border radius by size."""
        return self.profile.borders.radius.get(size)

    def get_shadow(self, size: str = "md") -> str:
        """Get shadow by size."""
        return self.profile.shadows.get(size)

    def get_z_index(self, layer: str) -> int:
        """Get z-index by layer name."""
        return self.profile.zIndex.get(layer)

    def get_breakpoint(self, size: str) -> int:
        """Get breakpoint value by size."""
        return self.profile.breakpoints.get(size)

    def get_font_size(self, size: str = "base") -> int:
        """Get font size by scale name."""
        return self.profile.typography.scale.get(size)

    def get_component_token(self, component: str, property: str) -> Optional[Any]:
        """Get component-level token."""
        return self.profile.components.get(component, property)

    # === COLOR CONVERSION ===

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (with or without #)

        Returns:
            Tuple of (r, g, b) values 0-255
        """
        return _hex_to_rgb(hex_color)

    def hex_to_argb(self, hex_color: str) -> str:
        """
        Convert hex color to ARGB format for openpyxl.

        Args:
            hex_color: Hex color string

        Returns:
            ARGB string (e.g., "FF6366f1")
        """
        return _hex_to_argb(hex_color)

    # === CSS GENERATION ===

    def generate_css_variables(self, dark_mode: Optional[bool] = None) -> str:
        """
        Generate complete CSS custom property definitions.

        Args:
            dark_mode: Override dark mode setting

        Returns:
            CSS string with :root block
        """
        use_dark = dark_mode if dark_mode is not None else self.dark_mode
        return self.profile.generate_css_variables(use_dark)

    def generate_font_faces(self, fonts_path: str = "../fonts") -> str:
        """
        Generate @font-face CSS declarations.

        Requires fonts to be downloaded first via ensure_fonts().

        Args:
            fonts_path: Relative path from CSS file to fonts directory

        Returns:
            CSS string with @font-face declarations
        """
        return self.profile.fonts.generate_font_faces(fonts_path)

    def ensure_fonts(self, output_dir: Optional[Path] = None) -> Dict[str, Dict[int, Path]]:
        """
        Ensure all fonts are available (download if needed).

        Args:
            output_dir: Directory to store fonts (uses self.output_dir if not provided)

        Returns:
            Dict mapping font family to weight to file path
        """
        fonts_dir = output_dir or self.output_dir
        if not fonts_dir:
            raise ValueError("No output directory specified for fonts")

        return self.profile.fonts.ensure_fonts(fonts_dir / "fonts")

    def generate_complete_css(
        self,
        include_fonts: bool = True,
        fonts_path: str = "../fonts",
        dark_mode: Optional[bool] = None,
    ) -> str:
        """
        Generate complete CSS with variables and font faces.

        Args:
            include_fonts: Whether to include @font-face declarations
            fonts_path: Relative path to fonts directory
            dark_mode: Override dark mode setting

        Returns:
            Complete CSS string
        """
        parts = []

        # Font faces
        if include_fonts:
            font_css = self.generate_font_faces(fonts_path)
            if font_css:
                parts.append(font_css)

        # CSS variables
        parts.append(self.generate_css_variables(dark_mode))

        # Dark mode media query
        if not dark_mode:
            dark_vars = self.generate_css_variables(dark_mode=True)
            # Extract just the variable declarations (remove :root wrapper)
            dark_lines = dark_vars.split("\n")[1:-1]  # Remove :root { and }
            if dark_lines:
                parts.append(
                    f"@media (prefers-color-scheme: dark) {{\n    :root {{\n    {'    '.join(dark_lines)}\n    }}\n}}"
                )

        return "\n\n".join(parts)

    # === LEGACY COMPATIBILITY ===

    def to_legacy_theme(self) -> "Theme":
        """
        Convert BrandProfile back to legacy Theme for backward compatibility.

        This allows using BrandContext with builders that still expect Theme.
        """
        from ..core.theme import ColorPalette, DarkColors, Theme
        from ..core.theme import Typography as LegacyTypography

        return Theme(
            name=self.profile.name,
            colors=ColorPalette(
                primary=self.profile.colors.brand.primary,
                secondary=self.profile.colors.brand.secondary,
                accent=self.profile.colors.brand.accent,
                background=self.profile.colors.background.primary,
                surface=self.profile.colors.surface.default,
                text=self.profile.colors.text.primary,
                muted=self.profile.colors.text.muted,
                border=self.profile.colors.border.default,
            ),
            dark=DarkColors(
                background=self.profile.colors.dark.background.primary,
                surface=self.profile.colors.dark.surface.default,
                text=self.profile.colors.dark.text.primary,
                accent=self.profile.colors.brand.accent,
                muted=self.profile.colors.dark.text.muted,
                border=self.profile.colors.dark.border.default,
            ),
            typography=LegacyTypography(
                heading=self.profile.typography.heading.family,
                body=self.profile.typography.body.family,
                code=self.profile.typography.code.family,
                base_size=self.profile.typography.scale.base,
                scale=1.25,  # Default scale ratio
            ),
        )

    @classmethod
    def from_legacy_theme(
        cls,
        theme: "Theme",
        project_root: Optional[Path] = None,
    ) -> "BrandContext":
        """
        Create BrandContext from legacy Theme.

        This provides backward compatibility for existing code.
        """
        profile = BrandProfile.from_legacy_theme(theme, project_root)
        return cls(profile=profile)
