"""
Brand Profile Loader

Load brand configuration from brand.yaml with fallback to legacy theme.yaml.
"""

import warnings
from pathlib import Path
from typing import Optional

import yaml

from .context import BrandContext
from .logos import discover_logos
from .profile import BrandProfile


def load_brand(path: Path) -> BrandProfile:
    """
    Load brand profile from a YAML file.

    Args:
        path: Path to brand.yaml file

    Returns:
        BrandProfile instance
    """
    if not path.exists():
        return BrandProfile()

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    project_root = path.parent
    return BrandProfile.from_dict(data, project_root)


def load_brand_profile(project_root: Path) -> BrandProfile:
    """
    Load brand profile with fallback chain.

    Order of precedence:
    1. brand.yaml if exists
    2. theme.yaml wrapped in BrandProfile (with deprecation warning)
    3. Default brand profile

    Args:
        project_root: Project root directory

    Returns:
        BrandProfile instance
    """
    brand_path = project_root / "brand.yaml"
    theme_path = project_root / "theme.yaml"

    # Try brand.yaml first
    if brand_path.exists():
        profile = load_brand(brand_path)

        # Discover logos if not specified
        if not profile.logos.primary.exists():
            brand_dir = project_root / "brand"
            if brand_dir.exists():
                discovered = discover_logos(brand_dir)
                profile.identity.logos = discovered
            else:
                # Try legacy assets/brand location
                legacy_brand_dir = project_root / "assets" / "brand"
                if legacy_brand_dir.exists():
                    discovered = discover_logos(legacy_brand_dir)
                    profile.identity.logos = discovered

        return profile

    # Fall back to theme.yaml with deprecation warning
    if theme_path.exists():
        warnings.warn(
            "theme.yaml is deprecated. Run 'media-engine brand migrate' to convert to brand.yaml",
            DeprecationWarning,
            stacklevel=2,
        )

        from ..core.theme import load_theme

        theme = load_theme(theme_path)
        profile = BrandProfile.from_legacy_theme(theme, project_root)

        # Discover logos from legacy locations
        for logo_dir in [
            project_root / "brand",
            project_root / "assets" / "brand",
            project_root / "assets",
        ]:
            if logo_dir.exists():
                discovered = discover_logos(logo_dir)
                if discovered.primary.exists():
                    profile.identity.logos = discovered
                    break

        return profile

    # Default profile
    return BrandProfile()


def load_brand_context(
    project_root: Path,
    output_dir: Optional[Path] = None,
    dark_mode: bool = False,
) -> BrandContext:
    """
    Load brand context for a project.

    This is the recommended way to get brand assets for builders.

    Args:
        project_root: Project root directory
        output_dir: Output directory for generated assets (fonts, etc.)
        dark_mode: Whether to use dark mode colors by default

    Returns:
        BrandContext instance ready for use
    """
    profile = load_brand_profile(project_root)
    return BrandContext(
        profile=profile,
        output_dir=output_dir,
        dark_mode=dark_mode,
    )


def migrate_theme_to_brand(project_root: Path, dry_run: bool = False) -> Optional[Path]:
    """
    Migrate theme.yaml to brand.yaml.

    Creates a new brand.yaml file and optionally brand/ directory structure.
    Does not delete theme.yaml (user should do that manually after verifying).

    Args:
        project_root: Project root directory
        dry_run: If True, don't write files, just return what would be created

    Returns:
        Path to created brand.yaml or None if migration not needed
    """
    theme_path = project_root / "theme.yaml"
    brand_path = project_root / "brand.yaml"

    if not theme_path.exists():
        return None

    if brand_path.exists():
        warnings.warn("brand.yaml already exists, skipping migration")
        return None

    # Load theme
    from ..core.theme import load_theme

    theme = load_theme(theme_path)

    # Load colors.json if it exists (for semantic colors)
    colors_json_path = project_root / "assets" / "brand" / "colors.json"
    semantic_colors = {}
    if colors_json_path.exists():
        import json

        with open(colors_json_path, "r") as f:
            colors_data = json.load(f)
            semantic_colors = colors_data.get("semantic", {})

    # Discover logos
    logos_data = {}
    for logo_dir in [project_root / "assets" / "brand", project_root / "assets"]:
        if logo_dir.exists():
            logos = discover_logos(logo_dir)
            if logos.primary.exists():
                logos_data = {
                    "primary": {"path": logos.primary.path},
                    "dark": {"path": logos.dark.path} if logos.dark.exists() else None,
                    "square": {"path": logos.square.path} if logos.square.exists() else None,
                    "icon": {"path": logos.icon.path} if logos.icon.exists() else None,
                }
                # Remove None entries
                logos_data = {k: v for k, v in logos_data.items() if v}
                break

    # Build brand.yaml content
    brand_data = {
        "name": theme.name,
        "identity": {
            "logos": logos_data,
            "legal": {
                "copyright": "",
                "tagline": "",
            },
        },
        "colors": {
            "brand": {
                "primary": theme.colors.primary,
                "secondary": theme.colors.secondary,
                "accent": theme.colors.accent,
            },
            "semantic": semantic_colors
            or {
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "info": "#3b82f6",
            },
            "text": {
                "primary": theme.colors.text,
                "secondary": theme.colors.secondary,
                "muted": theme.colors.muted,
                "inverse": "#ffffff",
            },
            "background": {
                "primary": theme.colors.background,
                "secondary": theme.colors.surface,
                "tertiary": theme.colors.border,
            },
            "surface": {
                "default": theme.colors.surface,
                "raised": theme.colors.background,
                "overlay": "rgba(0,0,0,0.5)",
            },
            "border": {
                "default": theme.colors.border,
                "subtle": theme.colors.border,
                "strong": theme.colors.muted,
            },
            "dark": {
                "text": {
                    "primary": theme.dark.text,
                    "muted": theme.dark.muted,
                },
                "background": {
                    "primary": theme.dark.background,
                    "secondary": theme.dark.surface,
                },
                "surface": {
                    "default": theme.dark.surface,
                },
                "border": {
                    "default": theme.dark.border,
                },
            },
        },
        "typography": {
            "fonts": {
                "heading": {
                    "family": theme.typography.heading,
                    "weights": [500, 600, 700],
                    "source": "google",
                    "fallback": ["system-ui", "sans-serif"],
                },
                "body": {
                    "family": theme.typography.body,
                    "weights": [400, 500],
                    "source": "google",
                    "fallback": ["system-ui", "sans-serif"],
                },
                "code": {
                    "family": theme.typography.code,
                    "weights": [400, 500],
                    "source": "google",
                    "fallback": ["SF Mono", "Monaco", "monospace"],
                },
            },
            "scale": {
                "xs": 12,
                "sm": 14,
                "base": theme.typography.base_size,
                "lg": 18,
                "xl": 20,
                "2xl": 24,
                "3xl": 30,
                "4xl": 36,
                "5xl": 48,
                "6xl": 60,
                "display": 72,
            },
        },
        # Include other default tokens
        "spacing": {
            "unit": 4,
            "scale": {0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48},
        },
        "borders": {
            "radius": {"none": 0, "sm": 2, "md": 4, "lg": 8, "xl": 12, "2xl": 16, "full": 9999},
            "width": {"thin": 1, "default": 1, "medium": 2, "thick": 4},
        },
        "shadows": {
            "xs": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "sm": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)",
            "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
        },
        "transitions": {
            "duration": {"fast": "150ms", "normal": "200ms", "slow": "300ms"},
            "easing": {"easeInOut": "cubic-bezier(0.4, 0, 0.2, 1)"},
        },
        "zIndex": {
            "base": 0,
            "dropdown": 100,
            "sticky": 200,
            "modal": 400,
            "tooltip": 600,
        },
        "breakpoints": {"sm": 640, "md": 768, "lg": 1024, "xl": 1280, "2xl": 1536},
    }

    if dry_run:
        return brand_path

    # Write brand.yaml
    with open(brand_path, "w") as f:
        yaml.dump(brand_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Create brand/ directory structure if logos exist
    if logos_data:
        brand_dir = project_root / "brand"
        logos_dir = brand_dir / "logos"
        fonts_dir = brand_dir / "fonts"

        logos_dir.mkdir(parents=True, exist_ok=True)
        fonts_dir.mkdir(parents=True, exist_ok=True)

        # Note: We don't move logos here - user should do that manually
        # This just creates the directory structure

    return brand_path
