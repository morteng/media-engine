"""
Media Engine Brand Module

Unified brand/design system for consistent visual identity across all outputs.

This module provides:
- BrandProfile: Complete brand configuration
- BrandContext: Builder interface for accessing brand assets
- Color, typography, and design token dataclasses
- Logo asset management with format conversion
- Font registry with Google Fonts and local file support
"""

from .colors import (
    BackgroundColors,
    BorderColors,
    # Color dataclasses
    BrandColors,
    ColorSystem,
    DarkModeColors,
    SemanticColors,
    SurfaceColors,
    TextColors,
    darken_color,
    hex_to_argb,
    # Color utilities
    hex_to_rgb,
    lighten_color,
    rgb_to_hex,
)
from .context import (
    BrandContext,
)
from .fonts import (
    FontConfig,
    FontRegistry,
)
from .loader import (
    load_brand,
    load_brand_profile,
)
from .logos import (
    LogoAsset,
    LogoAssets,
)
from .profile import (
    BrandProfile,
    Identity,
    LegalInfo,
)
from .resolver import (
    BrandContextResolver,
    ResolutionStep,
    ResolvedBrandContext,
    resolve_brand_context,
)
from .tokens import (
    BorderTokens,
    Breakpoints,
    ComponentTokens,
    ShadowTokens,
    SpacingScale,
    TransitionTokens,
    ZIndexScale,
)
from .typography import (
    FontAsset,
    FontScale,
    LetterSpacing,
    LineHeight,
    Typography,
)
from .voice import (
    DEFAULT_VOICE_PROFILE,
    AudioVoice,
    AudioVoiceProfile,
    AudioVoiceSettings,
    TermPreference,
    VoiceProfile,
    VoiceProfileOverride,
    VoiceStyle,
)
from .voice_checker import (
    VoiceCheckResult,
    VoiceConsistencyChecker,
    VoiceIssue,
    check_document_voice,
)

__all__ = [
    # Color utilities
    "hex_to_rgb",
    "hex_to_argb",
    "rgb_to_hex",
    "lighten_color",
    "darken_color",
    # Color dataclasses
    "BrandColors",
    "SemanticColors",
    "TextColors",
    "BackgroundColors",
    "SurfaceColors",
    "BorderColors",
    "DarkModeColors",
    "ColorSystem",
    # Typography
    "FontAsset",
    "FontScale",
    "LineHeight",
    "LetterSpacing",
    "Typography",
    # Tokens
    "SpacingScale",
    "BorderTokens",
    "ShadowTokens",
    "TransitionTokens",
    "ZIndexScale",
    "Breakpoints",
    "ComponentTokens",
    # Logos
    "LogoAsset",
    "LogoAssets",
    # Fonts
    "FontConfig",
    "FontRegistry",
    # Profile
    "Identity",
    "LegalInfo",
    "BrandProfile",
    # Context
    "BrandContext",
    # Loader
    "load_brand",
    "load_brand_profile",
    # Voice
    "VoiceStyle",
    "TermPreference",
    "VoiceProfile",
    "VoiceProfileOverride",
    "DEFAULT_VOICE_PROFILE",
    # Audio Voice
    "AudioVoiceSettings",
    "AudioVoice",
    "AudioVoiceProfile",
    # Voice Checker
    "VoiceIssue",
    "VoiceCheckResult",
    "VoiceConsistencyChecker",
    "check_document_voice",
    # Brand Context Resolver
    "BrandContextResolver",
    "ResolvedBrandContext",
    "ResolutionStep",
    "resolve_brand_context",
]
