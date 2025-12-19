"""
Centralized path constants and resolution for Media Engine.

All path templates, directory names, and path resolution logic should be here.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# =============================================================================
# DIRECTORY NAMES
# =============================================================================

@dataclass(frozen=True)
class DirectoryNames:
    """Standard directory names used throughout the project."""
    # Project structure
    content: str = "content"
    assets: str = "assets"
    output: str = "output"

    # Cache and metadata
    cache: str = ".cache"
    media_engine: str = ".media-engine"

    # Content subdirectories
    chapters: str = "chapters"
    scripts: str = "scripts"
    diagrams: str = "diagrams"
    slides: str = "slides"
    demos: str = "demos"
    data: str = "data"

    # Output subdirectories
    videos: str = "videos"
    audio: str = "audio"

    # Legacy paths (for backwards compatibility)
    docs: str = "docs"
    deliverables: str = "deliverables"


DIRS = DirectoryNames()


# =============================================================================
# FILE NAMES
# =============================================================================

@dataclass(frozen=True)
class FileNames:
    """Standard file names used throughout the project."""
    # Project config files
    project_config: str = "project.yaml"
    theme_config: str = "theme.yaml"
    schema_config: str = "schema.yaml"

    # Registry and manifest files
    content_registry: str = "content_registry.json"
    cache_manifest: str = "manifest.json"
    audit_log: str = "audit.log"
    search_index: str = "search_index.json"

    # Video files
    video_manifest: str = "video_manifest.yaml"
    video_props_suffix: str = ".props.json"

    # Ignore files
    media_ignore: str = ".mediaignore"

    # Environment
    env_file: str = ".env"
    env_example: str = ".env.example"


FILES = FileNames()


# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

@dataclass(frozen=True)
class EnvVars:
    """Environment variable names."""
    # Paths
    publish_dir: str = "MEDIA_ENGINE_PUBLISH_DIR"
    project_dir: str = "MEDIA_ENGINE_PROJECT_DIR"

    # API Keys
    elevenlabs_key: str = "ELEVEN_LABS_API_KEY"
    elevenlabs_key_alt: str = "ELEVENLABS_API_KEY"

    # User info
    user: str = "USER"
    username: str = "USERNAME"

    # Debug
    debug: str = "MEDIA_ENGINE_DEBUG"
    log_level: str = "MEDIA_ENGINE_LOG_LEVEL"


ENV = EnvVars()


# =============================================================================
# IGNORE PATTERNS
# =============================================================================

DEFAULT_IGNORE_PATTERNS: tuple[str, ...] = (
    "**/.cache/**",
    "**/__pycache__/**",
    "**/.git/**",
    "**/.media-engine/**",
    "**/node_modules/**",
    "**/*.pyc",
    "**/*-poster.jpg",
    "**/*-poster.png",
    "**/videos/audio/**",
    "**/audio/**/*.mp3",
)


# =============================================================================
# PATH RESOLUTION
# =============================================================================

class PathResolver:
    """Resolves paths relative to project root."""

    def __init__(self, project_root: Path):
        self.root = project_root

    # --- Core directories ---

    @property
    def content_dir(self) -> Path:
        """Content directory (content/)."""
        return self.root / DIRS.content

    @property
    def assets_dir(self) -> Path:
        """Assets directory (assets/)."""
        return self.root / DIRS.assets

    @property
    def output_dir(self) -> Path:
        """Output directory (output/)."""
        return self.root / DIRS.output

    @property
    def cache_dir(self) -> Path:
        """Cache directory (.cache/)."""
        return self.root / DIRS.cache

    @property
    def media_engine_dir(self) -> Path:
        """Media Engine metadata directory (.media-engine/)."""
        return self.root / DIRS.media_engine

    # --- Config files ---

    @property
    def project_config(self) -> Path:
        """Project config file (project.yaml)."""
        return self.root / FILES.project_config

    @property
    def theme_config(self) -> Path:
        """Theme config file (theme.yaml)."""
        return self.root / FILES.theme_config

    @property
    def schema_config(self) -> Path:
        """Schema config file (schema.yaml)."""
        return self.root / FILES.schema_config

    # --- Registry and cache files ---

    @property
    def content_registry(self) -> Path:
        """Content registry file (.media-engine/content_registry.json)."""
        return self.media_engine_dir / FILES.content_registry

    @property
    def cache_manifest(self) -> Path:
        """Cache manifest file (.cache/manifest.json)."""
        return self.cache_dir / FILES.cache_manifest

    @property
    def audit_log(self) -> Path:
        """Audit log file (.media-engine/audit.log)."""
        return self.media_engine_dir / FILES.audit_log

    @property
    def search_index(self) -> Path:
        """Search index file (.cache/search_index.json)."""
        return self.cache_dir / FILES.search_index

    # --- Language-specific paths ---

    def language_dir(self, language: str) -> Path:
        """Content directory for a specific language."""
        return self.content_dir / language

    def chapters_dir(self, language: str) -> Path:
        """Chapters directory for a language."""
        return self.language_dir(language) / DIRS.chapters

    def scripts_dir(self, language: str) -> Path:
        """Scripts directory for a language."""
        return self.language_dir(language) / DIRS.scripts

    def diagrams_dir(self, language: str) -> Path:
        """Diagrams directory for a language."""
        return self.language_dir(language) / DIRS.diagrams

    def slides_dir(self, language: str) -> Path:
        """Slides directory for a language."""
        return self.language_dir(language) / DIRS.slides

    def demos_dir(self, language: str) -> Path:
        """Demos directory for a language."""
        return self.language_dir(language) / DIRS.demos

    def data_dir(self, language: str) -> Path:
        """Data directory for a language."""
        return self.language_dir(language) / DIRS.data

    # --- Output paths ---

    def output_language_dir(self, language: str) -> Path:
        """Output directory for a specific language."""
        return self.output_dir / language

    def videos_dir(self, language: str) -> Path:
        """Videos output directory for a language."""
        return self.output_language_dir(language) / DIRS.videos

    def audio_dir(self, language: str) -> Path:
        """Audio output directory for a language."""
        return self.output_language_dir(language) / DIRS.audio

    # --- Publish directory ---

    def publish_dir(self, project_name: str, configured_path: Optional[str] = None) -> Path:
        """
        Resolve publish directory with priority:
        1. Environment variable MEDIA_ENGINE_PUBLISH_DIR
        2. Configured path from project.yaml
        3. Default: dist/{project-name}
        """
        # 1. Environment variable (highest priority)
        env_publish = os.environ.get(ENV.publish_dir)
        if env_publish:
            return Path(env_publish)

        # 2. Configured path
        if configured_path:
            path = Path(configured_path)
            if path.is_absolute():
                return path
            return self.root / path

        # 3. Default
        return self.root / "dist" / project_name

    # --- Utility methods ---

    def ensure_dir(self, path: Path) -> Path:
        """Ensure a directory exists and return it."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    def relative_to_root(self, path: Path) -> Path:
        """Get path relative to project root."""
        try:
            return path.relative_to(self.root)
        except ValueError:
            return path


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find project root by searching for project.yaml.

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Project root path or None if not found
    """
    current = start_path or Path.cwd()

    while current != current.parent:
        if (current / FILES.project_config).exists():
            return current
        current = current.parent

    # Check root
    if (current / FILES.project_config).exists():
        return current

    return None


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with fallback."""
    return os.environ.get(name, default)


def get_user() -> str:
    """Get current user from environment."""
    return os.environ.get(ENV.user) or os.environ.get(ENV.username) or "unknown"
