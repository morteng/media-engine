"""
Centralized default values for Media Engine.

All magic numbers, default strings, and configuration values should be defined here.
This provides a single source of truth for all defaults across the codebase.
"""

from dataclasses import dataclass
from typing import Any

# =============================================================================
# VIDEO SETTINGS
# =============================================================================


@dataclass(frozen=True)
class VideoDefaults:
    """Default video rendering settings."""

    width: int = 1920
    height: int = 1080
    fps: int = 60
    codec: str = "h264"

    # FFmpeg encoding presets
    ffmpeg_preset: str = "slow"
    ffmpeg_crf: int = 18  # Quality (lower = better, 18 is visually lossless)
    ffmpeg_profile: str = "high"
    ffmpeg_level: str = "5.1"  # Level 5.1 supports 1080p@60fps
    ffmpeg_pixel_format: str = "yuv420p"

    # Capture settings
    capture_duration_ms: int = 180000  # 3 minutes max
    capture_max_concurrent: int = 2
    poster_extract_time: int = 1  # seconds
    poster_quality: int = 2  # 1-31, lower is better


VIDEO = VideoDefaults()


# =============================================================================
# VOICEOVER SETTINGS
# =============================================================================


@dataclass(frozen=True)
class VoiceoverDefaults:
    """Default voiceover generation settings."""

    provider: str = "elevenlabs"
    model: str = "eleven_turbo_v2_5"
    language: str = "en"

    # Voice characteristics
    stability: float = 0.5
    similarity_boost: float = 0.75

    # Pause durations (seconds) based on punctuation
    pause_question: float = 0.9
    pause_exclamation: float = 0.6
    pause_period_long: float = 0.5  # Long sentences
    pause_period_short: float = 0.4  # Short sentences
    pause_comma: float = 0.25
    pause_default: float = 0.4
    pause_final: float = 0.0  # No pause after last segment
    pause_empty: float = 0.3  # Empty/blank text

    # Long sentence threshold (words)
    long_sentence_words: int = 15


VOICEOVER = VoiceoverDefaults()


# =============================================================================
# WEB SERVER SETTINGS
# =============================================================================


@dataclass(frozen=True)
class WebDefaults:
    """Default web server settings."""

    host: str = "127.0.0.1"
    port: int = 8080
    auto_open_browser: bool = True
    browser_open_delay: float = 1.0  # seconds

    # CORS settings
    cors_allow_origins: tuple = ("*",)
    cors_allow_credentials: bool = True
    cors_allow_methods: tuple = ("*",)
    cors_allow_headers: tuple = ("*",)


WEB = WebDefaults()


# =============================================================================
# NETWORK SETTINGS
# =============================================================================


@dataclass(frozen=True)
class NetworkDefaults:
    """Default network and HTTP settings."""

    # Timeouts (seconds)
    timeout_default: int = 10
    timeout_download: int = 10
    timeout_google_fonts: int = 30
    timeout_link_check: int = 10

    # Concurrency
    max_workers: int = 10
    max_concurrent_downloads: int = 5

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # Skip domains for link checking
    skip_domains: tuple = ("localhost", "127.0.0.1")


NETWORK = NetworkDefaults()


# =============================================================================
# QUALITY & READABILITY SETTINGS
# =============================================================================


@dataclass(frozen=True)
class QualityDefaults:
    """Default quality check thresholds."""

    # Readability
    max_sentence_words: int = 25
    max_complex_word_percent: float = 15.0
    complex_word_syllables: int = 3  # Words with 3+ syllables are complex
    reading_speed_wpm: int = 200  # Words per minute

    # Placeholders to detect
    placeholder_patterns: tuple = (
        r"\bTODO\b",
        r"\bTBD\b",
        r"\bFIXME\b",
        r"\bXXX\b",
        r"\[placeholder\]",
        r"\[TBD\]",
        r"\[TODO\]",
        r"<placeholder>",
        r"\$\{.*?\}",
        r"\{\{.*?\}\}",
    )

    # Content freshness (days)
    freshness_default_days: int = 60
    freshness_warning_days: int = 30
    freshness_critical_days: int = 90


QUALITY = QualityDefaults()


# =============================================================================
# SEARCH SETTINGS
# =============================================================================


@dataclass(frozen=True)
class SearchDefaults:
    """Default search and indexing settings."""

    results_limit: int = 20
    excerpt_length: int = 200  # characters
    min_query_length: int = 2
    highlight_tag: str = "mark"


SEARCH = SearchDefaults()


# =============================================================================
# CACHE SETTINGS
# =============================================================================


@dataclass(frozen=True)
class CacheDefaults:
    """Default cache settings."""

    # TTL (seconds)
    mcp_cache_ttl: int = 30
    link_cache_ttl: int = 900  # 15 minutes

    # File handling
    hash_length: int = 16  # Characters of SHA256 to use
    chunk_size: int = 8192  # Bytes for file reading


CACHE = CacheDefaults()


# =============================================================================
# THEME & COLORS
# =============================================================================


@dataclass(frozen=True)
class ThemeDefaults:
    """Default theme and color settings."""

    # Light mode colors
    primary: str = "#000000"
    secondary: str = "#333333"
    accent: str = "#0066cc"
    background: str = "#ffffff"
    surface: str = "#f8fafc"
    text: str = "#000000"
    muted: str = "#666666"
    border: str = "#e0e0e0"

    # Dark mode colors
    dark_background: str = "#1a1a1a"
    dark_surface: str = "#242424"
    dark_text: str = "#f0f0f0"
    dark_accent: str = "#3399ff"
    dark_muted: str = "#999999"
    dark_border: str = "#333333"

    # Typography
    heading_font: str = "sans-serif"
    body_font: str = "sans-serif"
    code_font: str = "monospace"
    base_font_size: int = 16  # pixels
    font_scale: float = 1.25


THEME = ThemeDefaults()


# =============================================================================
# PROVENANCE SETTINGS
# =============================================================================


@dataclass(frozen=True)
class ProvenanceDefaults:
    """Default provenance and tracking settings."""

    default_source_type: str = "internal"
    expiry_days: int = 365
    review_stale_days: int = 14  # Days before in_review is considered stale


PROVENANCE = ProvenanceDefaults()


# =============================================================================
# CLI SETTINGS
# =============================================================================


@dataclass(frozen=True)
class CLIDefaults:
    """Default CLI behavior settings."""

    default_language: str = "en"
    missing_translation_lang: str = "no"
    verbose: bool = False


CLI = CLIDefaults()


# =============================================================================
# FILE EXTENSIONS
# =============================================================================


@dataclass(frozen=True)
class FileExtensions:
    """File extension mappings by content type."""

    documents: frozenset = frozenset({".md"})
    configs: frozenset = frozenset({".yaml", ".yml"})
    videos: frozenset = frozenset({".mp4", ".webm"})
    audio: frozenset = frozenset({".mp3", ".wav"})
    images: frozenset = frozenset({".png", ".jpg", ".jpeg", ".svg", ".gif"})
    web: frozenset = frozenset({".html", ".css", ".js"})
    data: frozenset = frozenset({".json", ".csv"})
    deliverables: frozenset = frozenset({".html", ".pdf", ".pptx", ".xlsx"})


EXTENSIONS = FileExtensions()


# =============================================================================
# ALL DEFAULTS (for easy access)
# =============================================================================

ALL_DEFAULTS: dict[str, Any] = {
    "video": VIDEO,
    "voiceover": VOICEOVER,
    "web": WEB,
    "network": NETWORK,
    "quality": QUALITY,
    "search": SEARCH,
    "cache": CACHE,
    "theme": THEME,
    "provenance": PROVENANCE,
    "cli": CLI,
    "extensions": EXTENSIONS,
}


def get_default(category: str, key: str, fallback: Any = None) -> Any:
    """
    Get a default value by category and key.

    Args:
        category: The settings category (e.g., 'video', 'web')
        key: The setting key (e.g., 'width', 'port')
        fallback: Value to return if not found

    Returns:
        The default value or fallback

    Example:
        >>> get_default('video', 'width')
        1920
        >>> get_default('web', 'port')
        8080
    """
    if category not in ALL_DEFAULTS:
        return fallback

    defaults_obj = ALL_DEFAULTS[category]
    return getattr(defaults_obj, key, fallback)
