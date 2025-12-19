"""
Media Engine Settings Module

Centralized configuration management for all Media Engine settings.
This module provides a single source of truth for defaults, paths, and environment variables.

Usage:
    from media_engine.settings import (
        VIDEO, VOICEOVER, WEB, NETWORK, QUALITY,  # Default value groups
        DIRS, FILES, ENV,                          # Path/file/env constants
        PathResolver,                              # Path resolution
        get_default,                               # Get any default value
        get_elevenlabs_api_key,                    # Environment helpers
    )

    # Access defaults directly
    width = VIDEO.width  # 1920
    port = WEB.port      # 8080

    # Or use get_default for dynamic access
    width = get_default('video', 'width')

    # Path resolution
    paths = PathResolver(project_root)
    cache_dir = paths.cache_dir

Examples:
    >>> from media_engine.settings import VIDEO, WEB
    >>> VIDEO.width
    1920
    >>> WEB.port
    8080

    >>> from media_engine.settings import get_default
    >>> get_default('network', 'timeout_default')
    10
"""

# Default value groups
from .defaults import (
    VIDEO,
    VOICEOVER,
    WEB,
    NETWORK,
    QUALITY,
    SEARCH,
    CACHE,
    THEME,
    PROVENANCE,
    CLI,
    EXTENSIONS,
    ALL_DEFAULTS,
    get_default,
    # Dataclasses (for type hints)
    VideoDefaults,
    VoiceoverDefaults,
    WebDefaults,
    NetworkDefaults,
    QualityDefaults,
    SearchDefaults,
    CacheDefaults,
    ThemeDefaults,
    ProvenanceDefaults,
    CLIDefaults,
    FileExtensions,
)

# Path constants and resolution
from .paths import (
    DIRS,
    FILES,
    ENV,
    DEFAULT_IGNORE_PATTERNS,
    DirectoryNames,
    FileNames,
    EnvVars,
    PathResolver,
    find_project_root,
    get_env_var,
    get_user,
)

# Environment variable handling
from .env import (
    EnvVar,
    PUBLISH_DIR,
    PROJECT_DIR,
    ELEVENLABS_API_KEY,
    DEBUG,
    LOG_LEVEL,
    ALL_ENV_VARS,
    get_elevenlabs_api_key,
    get_current_user,
    is_debug_mode,
    get_log_level,
    validate_required_env_vars,
    get_env_summary,
    generate_env_example,
)


__all__ = [
    # Default value groups
    "VIDEO",
    "VOICEOVER",
    "WEB",
    "NETWORK",
    "QUALITY",
    "SEARCH",
    "CACHE",
    "THEME",
    "PROVENANCE",
    "CLI",
    "EXTENSIONS",
    "ALL_DEFAULTS",
    "get_default",
    # Dataclasses
    "VideoDefaults",
    "VoiceoverDefaults",
    "WebDefaults",
    "NetworkDefaults",
    "QualityDefaults",
    "SearchDefaults",
    "CacheDefaults",
    "ThemeDefaults",
    "ProvenanceDefaults",
    "CLIDefaults",
    "FileExtensions",
    # Path constants
    "DIRS",
    "FILES",
    "ENV",
    "DEFAULT_IGNORE_PATTERNS",
    "DirectoryNames",
    "FileNames",
    "EnvVars",
    "PathResolver",
    "find_project_root",
    "get_env_var",
    "get_user",
    # Environment handling
    "EnvVar",
    "PUBLISH_DIR",
    "PROJECT_DIR",
    "ELEVENLABS_API_KEY",
    "DEBUG",
    "LOG_LEVEL",
    "ALL_ENV_VARS",
    "get_elevenlabs_api_key",
    "get_current_user",
    "is_debug_mode",
    "get_log_level",
    "validate_required_env_vars",
    "get_env_summary",
    "generate_env_example",
]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_video_resolution() -> tuple[int, int]:
    """Get default video resolution as (width, height) tuple."""
    return (VIDEO.width, VIDEO.height)


def get_voiceover_settings() -> dict:
    """Get voiceover settings as a dictionary."""
    return {
        "provider": VOICEOVER.provider,
        "model": VOICEOVER.model,
        "stability": VOICEOVER.stability,
        "similarity_boost": VOICEOVER.similarity_boost,
    }


def get_ffmpeg_settings() -> dict:
    """Get FFmpeg encoding settings as a dictionary."""
    return {
        "preset": VIDEO.ffmpeg_preset,
        "crf": VIDEO.ffmpeg_crf,
        "profile": VIDEO.ffmpeg_profile,
        "level": VIDEO.ffmpeg_level,
        "pixel_format": VIDEO.ffmpeg_pixel_format,
    }


def get_network_timeouts() -> dict:
    """Get all network timeout settings."""
    return {
        "default": NETWORK.timeout_default,
        "download": NETWORK.timeout_download,
        "google_fonts": NETWORK.timeout_google_fonts,
        "link_check": NETWORK.timeout_link_check,
    }


def get_quality_thresholds() -> dict:
    """Get all quality threshold settings."""
    return {
        "max_sentence_words": QUALITY.max_sentence_words,
        "max_complex_word_percent": QUALITY.max_complex_word_percent,
        "freshness_default_days": QUALITY.freshness_default_days,
        "freshness_warning_days": QUALITY.freshness_warning_days,
        "freshness_critical_days": QUALITY.freshness_critical_days,
    }


def print_settings_summary():
    """Print a summary of all settings (for debugging)."""
    print("=" * 60)
    print("MEDIA ENGINE SETTINGS SUMMARY")
    print("=" * 60)

    categories = [
        ("Video", VIDEO),
        ("Voiceover", VOICEOVER),
        ("Web Server", WEB),
        ("Network", NETWORK),
        ("Quality", QUALITY),
        ("Search", SEARCH),
        ("Cache", CACHE),
        ("Theme", THEME),
        ("Provenance", PROVENANCE),
        ("CLI", CLI),
    ]

    for name, defaults in categories:
        print(f"\n{name}:")
        for key, value in defaults.__dict__.items():
            if not key.startswith("_"):
                print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Environment Variables:")
    for name, var in ALL_ENV_VARS.items():
        status = "SET" if var.is_set() else "not set"
        print(f"  {var.name}: {status}")
