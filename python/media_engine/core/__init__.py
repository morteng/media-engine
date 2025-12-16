"""
Media Engine Core Module

Shared utilities for configuration, theming, and project management.
"""

from .config import Config, VoiceoverConfig, VideoConfig, load_config
from .theme import Theme, ColorPalette, Typography, load_theme, COPPER_AND_CREAM
from .project import Project, LanguageConfig, find_project

__all__ = [
    # Config
    "Config",
    "VoiceoverConfig",
    "VideoConfig",
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
