"""
Media Engine Core Module

Shared utilities for configuration, theming, and project management.
"""

from .config import Config, FreshnessConfig, VideoConfig, VoiceoverConfig, load_config
from .project import LanguageConfig, Project, find_project
from .theme import COPPER_AND_CREAM, ColorPalette, Theme, Typography, load_theme

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
]
