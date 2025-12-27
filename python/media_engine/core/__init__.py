"""
Media Engine Core Module

Shared utilities for configuration, theming, and project management.
"""

from .config import Config, FreshnessConfig, VideoConfig, VoiceoverConfig, load_config
from .exceptions import (
    # Base
    MediaEngineError,
    # Configuration
    ConfigurationError,
    ProjectNotFoundError,
    InvalidConfigError,
    MissingDependencyError,
    # Documents
    DocumentError,
    DocumentNotFoundError,
    DocumentLockedError,
    DocumentValidationError,
    DocumentParseError,
    # Build
    BuildError,
    BuildDependencyError,
    BuildOutputError,
    # Sessions
    SessionError,
    SessionNotFoundError,
    SessionConflictError,
    CheckpointError,
    # Translation
    TranslationError,
    TranslationOutdatedError,
    TranslationMissingError,
    # Quality
    QualityError,
    SecurityViolationError,
    LinkValidationError,
    # Approval
    ApprovalError,
    ApprovalRequiredError,
    ApprovalRejectedError,
    ApprovalTimeoutError,
    # Utilities
    error_from_dict,
    is_recoverable,
    get_error_suggestions,
)
from .hashing import (
    compute_content_hash,
    compute_document_hash,
    compute_file_hash,
    compute_raw_hash,
    compute_short_hash,
    verify_file_hash,
    verify_hash,
)
from .project import LanguageConfig, Project, find_project
from .sections import (
    ChangeType,
    DocumentSections,
    Section,
    SectionChangeReport,
    SectionDiff,
    analyze_changes,
    compare_sections,
    parse_document_sections,
    parse_sections,
)
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
    # Hashing
    "compute_content_hash",
    "compute_document_hash",
    "compute_file_hash",
    "compute_raw_hash",
    "compute_short_hash",
    "verify_hash",
    "verify_file_hash",
    # Brand (lazy loaded)
    "BrandProfile",
    "BrandContext",
    "load_brand_profile",
    # Section-level tracking
    "Section",
    "SectionDiff",
    "DocumentSections",
    "SectionChangeReport",
    "ChangeType",
    "parse_sections",
    "parse_document_sections",
    "compare_sections",
    "analyze_changes",
    # Exceptions
    "MediaEngineError",
    "ConfigurationError",
    "ProjectNotFoundError",
    "InvalidConfigError",
    "MissingDependencyError",
    "DocumentError",
    "DocumentNotFoundError",
    "DocumentLockedError",
    "DocumentValidationError",
    "DocumentParseError",
    "BuildError",
    "BuildDependencyError",
    "BuildOutputError",
    "SessionError",
    "SessionNotFoundError",
    "SessionConflictError",
    "CheckpointError",
    "TranslationError",
    "TranslationOutdatedError",
    "TranslationMissingError",
    "QualityError",
    "SecurityViolationError",
    "LinkValidationError",
    "ApprovalError",
    "ApprovalRequiredError",
    "ApprovalRejectedError",
    "ApprovalTimeoutError",
    "error_from_dict",
    "is_recoverable",
    "get_error_suggestions",
]
