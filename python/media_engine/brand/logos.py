"""
Logo Asset Management

Handle logo variants with automatic format conversion (SVG to PNG).
"""

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LogoAsset:
    """Single logo asset with format variants."""

    path: Optional[str] = None  # Primary path (usually SVG)
    alt: str = ""
    sizes: List[int] = field(default_factory=list)  # For icon generation

    # Resolved paths (set after loading)
    _resolved_path: Optional[Path] = field(default=None, repr=False)
    _project_root: Optional[Path] = field(default=None, repr=False)
    _png_cache: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogoAsset":
        if isinstance(data, str):
            return cls(path=data)
        return cls(
            path=data.get("path"),
            alt=data.get("alt", ""),
            sizes=data.get("sizes", []),
        )

    def resolve(self, project_root: Path) -> "LogoAsset":
        """Resolve relative paths against project root."""
        self._project_root = project_root
        if self.path:
            resolved = project_root / self.path
            if resolved.exists():
                self._resolved_path = resolved
        return self

    def exists(self) -> bool:
        """Check if the logo file exists."""
        return self._resolved_path is not None and self._resolved_path.exists()

    def get_path(self) -> Optional[Path]:
        """Get the resolved file path."""
        return self._resolved_path

    def get_svg(self) -> Optional[Path]:
        """Get SVG version of the logo."""
        if self._resolved_path and self._resolved_path.suffix.lower() == ".svg":
            return self._resolved_path
        return None

    def get_png(self, size: Optional[int] = None) -> Optional[Path]:
        """
        Get PNG version of the logo.

        If the source is SVG, converts to PNG on demand.
        Uses caching to avoid repeated conversions.

        Args:
            size: Optional height in pixels for the PNG

        Returns:
            Path to PNG file or None if conversion fails
        """
        if not self._resolved_path:
            return None

        # If source is already PNG, return it
        if self._resolved_path.suffix.lower() == ".png":
            return self._resolved_path

        # Check cache
        if self._png_cache and self._png_cache.exists():
            return self._png_cache

        # Convert SVG to PNG
        if self._resolved_path.suffix.lower() == ".svg":
            return self._convert_svg_to_png(size)

        return None

    def _convert_svg_to_png(self, size: Optional[int] = None) -> Optional[Path]:
        """Convert SVG to PNG using cairosvg."""
        try:
            import cairosvg
        except ImportError:
            # cairosvg not available
            return None

        if not self._resolved_path:
            return None

        try:
            # Create temp file for PNG
            png_path = Path(tempfile.gettempdir()) / f"{self._resolved_path.stem}_logo.png"

            # Convert
            kwargs = {"url": str(self._resolved_path), "write_to": str(png_path)}
            if size:
                kwargs["output_height"] = size

            cairosvg.svg2png(**kwargs)

            self._png_cache = png_path
            return png_path

        except Exception:
            return None

    def get_for_format(self, format: str, size: Optional[int] = None) -> Optional[Path]:
        """
        Get logo in requested format.

        Args:
            format: "svg", "png", or "auto" (returns original)
            size: Optional size for PNG conversion

        Returns:
            Path to logo file in requested format
        """
        format = format.lower()

        if format == "svg":
            return self.get_svg()
        elif format == "png":
            return self.get_png(size)
        elif format == "auto":
            return self._resolved_path
        else:
            return self._resolved_path


@dataclass
class LogoAssets:
    """Collection of logo variants."""

    primary: LogoAsset = field(default_factory=LogoAsset)
    dark: LogoAsset = field(default_factory=LogoAsset)
    square: LogoAsset = field(default_factory=LogoAsset)
    icon: LogoAsset = field(default_factory=LogoAsset)
    watermark: LogoAsset = field(default_factory=LogoAsset)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogoAssets":
        return cls(
            primary=LogoAsset.from_dict(data.get("primary", {})),
            dark=LogoAsset.from_dict(data.get("dark", {})),
            square=LogoAsset.from_dict(data.get("square", {})),
            icon=LogoAsset.from_dict(data.get("icon", {})),
            watermark=LogoAsset.from_dict(data.get("watermark", {})),
        )

    def resolve(self, project_root: Path) -> "LogoAssets":
        """Resolve all logo paths against project root."""
        self.primary.resolve(project_root)
        self.dark.resolve(project_root)
        self.square.resolve(project_root)
        self.icon.resolve(project_root)
        self.watermark.resolve(project_root)
        return self

    def get(self, variant: str = "primary") -> LogoAsset:
        """Get logo by variant name."""
        variants = {
            "primary": self.primary,
            "dark": self.dark,
            "light": self.primary,  # Alias
            "square": self.square,
            "icon": self.icon,
            "watermark": self.watermark,
        }
        return variants.get(variant, self.primary)

    def get_best_available(self, variant: str = "primary") -> Optional[LogoAsset]:
        """
        Get the best available logo, with fallbacks.

        Falls back to primary if requested variant doesn't exist.
        """
        requested = self.get(variant)
        if requested.exists():
            return requested

        # Fallback chain
        if self.primary.exists():
            return self.primary

        return None


def discover_logos(brand_dir: Path) -> LogoAssets:
    """
    Discover logos in a brand directory.

    Searches for common logo patterns:
    - logo.svg, logo.png
    - logo-dark.svg, logo-dark.png
    - logo-square.svg, logo-square.png
    - icon.svg, icon.png
    - watermark.svg, watermark.png

    Args:
        brand_dir: Path to brand/logos directory

    Returns:
        LogoAssets with discovered logos
    """
    logos = LogoAssets()

    if not brand_dir.exists():
        return logos

    logos_dir = brand_dir / "logos" if (brand_dir / "logos").exists() else brand_dir

    # Discovery patterns
    patterns = {
        "primary": ["logo.svg", "logo.png", "logo-full.svg", "logo-primary.svg"],
        "dark": ["logo-dark.svg", "logo-dark.png", "logo-light.svg"],
        "square": ["logo-square.svg", "logo-square.png", "square.svg"],
        "icon": ["icon.svg", "icon.png", "favicon.svg", "favicon.png"],
        "watermark": ["watermark.svg", "watermark.png"],
    }

    for variant, filenames in patterns.items():
        for filename in filenames:
            path = logos_dir / filename
            if path.exists():
                logo_asset = LogoAsset(path=str(path.relative_to(brand_dir.parent)))
                logo_asset._resolved_path = path
                logo_asset._project_root = brand_dir.parent
                setattr(logos, variant, logo_asset)
                break

    return logos
