"""
Media Engine Core Module

Shared utilities for configuration, theming, and project management.
"""

from .config import Config, FreshnessConfig, VideoConfig, VoiceoverConfig, load_config
from .project import LanguageConfig, Project, find_project
from .theme import COPPER_AND_CREAM, ColorPalette, Theme, Typography, load_theme


# Lazy imports for brand module (to avoid circular imports)
def __getattr__(name: str):
    """Lazy import brand module types."""
    if name in ("BrandProfile", "BrandContext", "load_brand_profile"):
        from ..brand import BrandContext, BrandProfile, load_brand_profile

        return {
            "BrandProfile": BrandProfile,
            "BrandContext": BrandContext,
            "load_brand_profile": load_brand_profile,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Config
    "Config",
    "VoiceoverConfig",
    "VideoConfig",
    "FreshnessConfig",
    "load_config",
    # Theme
    "Theme",
    "ColorPalette",
    "Typography",
    "load_theme",
    "COPPER_AND_CREAM",
    # Project
    "Project",
    "LanguageConfig",
    "find_project",
    # Brand (lazy loaded)
    "BrandProfile",
    "BrandContext",
    "load_brand_profile",
]
