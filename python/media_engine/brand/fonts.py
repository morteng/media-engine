"""
Font Registry

Manage font assets with support for Google Fonts and local files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .typography import FontAsset

if TYPE_CHECKING:
    from .typography import Typography

# Common fonts with their weight configurations
COMMON_FONTS: Dict[str, List[int]] = {
    "Fraunces": [300, 400, 600, 700],
    "Source Sans 3": [300, 400, 500, 600, 700],
    "JetBrains Mono": [400, 500, 600],
    "Inter": [300, 400, 500, 600, 700],
    "Roboto": [300, 400, 500, 700],
    "Open Sans": [300, 400, 600, 700],
    "Lato": [300, 400, 700],
    "Montserrat": [300, 400, 500, 600, 700],
    "Playfair Display": [400, 500, 600, 700],
    "Merriweather": [300, 400, 700],
    "Fira Code": [300, 400, 500, 600, 700],
    "Source Code Pro": [400, 500, 600, 700],
}


@dataclass
class FontConfig:
    """Configuration for a single font family."""

    name: str
    weights: List[int] = field(default_factory=lambda: [400, 600, 700])
    italic: bool = False

    @classmethod
    def from_font_asset(cls, asset: FontAsset) -> "FontConfig":
        """Create FontConfig from a FontAsset."""
        weights = asset.weights
        if not weights:
            weights = COMMON_FONTS.get(asset.family, [400, 600, 700])
        return cls(name=asset.family, weights=weights)


@dataclass
class FontRegistry:
    """Registry of all font assets in the brand."""

    heading: FontAsset = field(default_factory=FontAsset)
    body: FontAsset = field(default_factory=FontAsset)
    code: FontAsset = field(default_factory=FontAsset)

    # Downloaded font file paths (populated after download)
    _font_files: Dict[str, Dict[int, Path]] = field(default_factory=dict, repr=False)
    _fonts_dir: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FontRegistry":
        return cls(
            heading=FontAsset.from_dict(data.get("heading", {})),
            body=FontAsset.from_dict(data.get("body", {})),
            code=FontAsset.from_dict(data.get("code", {})),
        )

    @classmethod
    def from_typography(cls, typography: "Typography") -> "FontRegistry":
        """Create FontRegistry from Typography config."""
        return cls(
            heading=typography.heading,
            body=typography.body,
            code=typography.code,
        )

    def get_font_configs(self) -> List[FontConfig]:
        """Get font configurations for downloading."""
        configs = []
        seen = set()

        for font in [self.heading, self.body, self.code]:
            if font.family not in seen:
                seen.add(font.family)
                configs.append(FontConfig.from_font_asset(font))

        return configs

    def get_unique_families(self) -> List[str]:
        """Get list of unique font family names."""
        families = set()
        for font in [self.heading, self.body, self.code]:
            families.add(font.family)
        return list(families)

    def ensure_fonts(self, output_dir: Path) -> Dict[str, Dict[int, Path]]:
        """
        Ensure all fonts are available.

        For Google fonts, downloads them.
        For local fonts, verifies they exist.

        Args:
            output_dir: Directory to store downloaded fonts

        Returns:
            Dict mapping font family to weight to file path
        """
        self._fonts_dir = output_dir
        font_files: Dict[str, Dict[int, Path]] = {}

        for role, font in [("heading", self.heading), ("body", self.body), ("code", self.code)]:
            if font.family in font_files:
                continue

            if font.source == "google":
                files = self._download_google_font(font, output_dir)
                if files:
                    font_files[font.family] = files
            elif font.source == "local" and font.local_path:
                files = self._find_local_fonts(font)
                if files:
                    font_files[font.family] = files

        self._font_files = font_files
        return font_files

    def _download_google_font(self, font: FontAsset, output_dir: Path) -> Dict[int, Path]:
        """Download font from Google Fonts."""
        # Import here to avoid circular dependency
        try:
            from ..assets.fonts import FontConfig as AssetFontConfig
            from ..assets.fonts import download_google_fonts
        except ImportError:
            return {}

        config = AssetFontConfig(
            name=font.family,
            weights=font.weights or COMMON_FONTS.get(font.family, [400, 600, 700]),
        )

        try:
            result = download_google_fonts([config], output_dir)
            return result.get(font.family, {})
        except Exception:
            return {}

    def _find_local_fonts(self, font: FontAsset) -> Dict[int, Path]:
        """Find local font files."""
        if not font.local_path:
            return {}

        local_dir = Path(font.local_path)
        if not local_dir.exists():
            return {}

        files: Dict[int, Path] = {}

        # Look for woff2 files with weight in name
        for woff2 in local_dir.glob("*.woff2"):
            # Try to extract weight from filename
            name = woff2.stem.lower()
            for weight in font.weights:
                if str(weight) in name:
                    files[weight] = woff2
                    break
            else:
                # Check for weight names
                weight_names = {
                    "thin": 100,
                    "extralight": 200,
                    "light": 300,
                    "regular": 400,
                    "medium": 500,
                    "semibold": 600,
                    "bold": 700,
                    "extrabold": 800,
                    "black": 900,
                }
                for weight_name, weight_value in weight_names.items():
                    if weight_name in name:
                        files[weight_value] = woff2
                        break

        return files

    def generate_font_faces(self, base_path: str = "../fonts") -> str:
        """
        Generate @font-face CSS declarations.

        Args:
            base_path: Relative path from CSS file to fonts directory

        Returns:
            CSS string with @font-face declarations
        """
        css_parts = []

        for font in [self.heading, self.body, self.code]:
            family = font.family
            if family not in self._font_files:
                continue

            for weight, file_path in sorted(self._font_files[family].items()):
                # Calculate relative path
                if self._fonts_dir:
                    rel_path = file_path.relative_to(self._fonts_dir.parent)
                    font_url = f"{base_path}/{rel_path}"
                else:
                    font_url = f"{base_path}/{file_path.name}"

                css_parts.append(f"""@font-face {{
    font-family: '{family}';
    font-style: normal;
    font-weight: {weight};
    font-display: swap;
    src: url('{font_url}') format('woff2');
}}""")

        return "\n\n".join(css_parts)

    def get_system_font(self, role: str) -> str:
        """Get system font equivalent for Office applications."""
        font = getattr(self, role, self.body)
        return font.get_system_font()

    def get_font_stack(self, role: str) -> str:
        """Get complete CSS font stack with fallbacks."""
        font = getattr(self, role, self.body)
        return font.get_font_stack()
