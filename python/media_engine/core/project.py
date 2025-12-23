"""
Project Management

A Project is the main entry point for media-engine. It loads project.yaml,
manages content, and coordinates builds.

Uses centralized settings from media_engine.settings for paths and defaults.
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml

from ..settings import CACHE, CLI, DIRS, ENV
from .config import Config
from .theme import Theme, load_theme

if TYPE_CHECKING:
    from ..brand import BrandContext, BrandProfile


@dataclass
class LanguageConfig:
    """Configuration for a single language."""

    code: str
    name: str
    voice_id: str = ""
    locale: str = ""

    @classmethod
    def from_dict(cls, code: str, data: dict) -> "LanguageConfig":
        if not isinstance(data, dict):
            data = {}
        return cls(
            code=code,
            name=data.get("name") or code.upper(),
            voice_id=data.get("voice_id") or "",
            locale=data.get("locale") or f"{code}-{code.upper()}",
        )


@dataclass
class Project:
    """
    A media-engine project.

    Loads from project.yaml and provides access to configuration,
    theme, content, and build operations.
    """

    root: Path
    config: Config
    theme: Theme
    languages: dict[str, LanguageConfig] = field(default_factory=dict)
    source_language: str = CLI.default_language
    _cache_manifest: dict = field(default_factory=dict)
    _brand_profile: Optional["BrandProfile"] = field(default=None, repr=False)
    _brand_context: Optional["BrandContext"] = field(default=None, repr=False)

    @classmethod
    def load(cls, project_dir: Path) -> "Project":
        """
        Load a project from a directory.

        Args:
            project_dir: Path to project root (containing project.yaml)

        Returns:
            Project instance
        """
        project_dir = Path(project_dir).resolve()

        # Load project.yaml
        project_yaml = project_dir / "project.yaml"
        if project_yaml.exists():
            with open(project_yaml, "r") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        # Load config
        config = Config.from_dict(data)

        # Load theme
        theme_file = data.get("design", {}).get("theme", "theme.yaml")
        theme_path = project_dir / theme_file
        theme = load_theme(theme_path)

        # Parse languages
        languages = {}
        loc_data = data.get("localization", {})
        source_language = loc_data.get("source_language", "en")

        for code, lang_data in loc_data.get("languages", {}).items():
            if isinstance(lang_data, dict):
                languages[code] = LanguageConfig.from_dict(code, lang_data)
            elif isinstance(code, str):
                languages[code] = LanguageConfig(code=code, name=code.upper())

        # Ensure source language exists
        if source_language not in languages:
            languages[source_language] = LanguageConfig(
                code=source_language,
                name="English" if source_language == "en" else source_language.upper(),
            )

        project = cls(
            root=project_dir,
            config=config,
            theme=theme,
            languages=languages,
            source_language=source_language,
        )

        # Load cache manifest
        project._load_cache_manifest()

        return project

    # === Convenience Properties ===

    @property
    def name(self) -> str:
        """Project name."""
        return self.config.name

    # === Brand System ===

    @property
    def brand(self) -> "BrandProfile":
        """
        Get the brand profile for this project.

        Lazy-loads from brand.yaml or falls back to theme.yaml.
        """
        if self._brand_profile is None:
            from ..brand import load_brand_profile

            self._brand_profile = load_brand_profile(self.root)
        return self._brand_profile

    @property
    def brand_context(self) -> "BrandContext":
        """
        Get a BrandContext for builder integration.

        This is the recommended way to access brand assets in builders.
        """
        if self._brand_context is None:
            from ..brand import BrandContext

            self._brand_context = BrandContext(
                profile=self.brand,
                output_dir=self.output_dir,
            )
        return self._brand_context

    # === Path Properties ===

    @property
    def content_dir(self) -> Path:
        """Directory containing content (documents, scripts)."""
        return self.root / self.config.paths.content

    @property
    def assets_dir(self) -> Path:
        """Directory containing assets (images, logos, etc)."""
        return self.root / self.config.paths.assets

    @property
    def output_dir(self) -> Path:
        """Directory for generated outputs."""
        return self.root / self.config.paths.output

    @property
    def cache_dir(self) -> Path:
        """Directory for build cache."""
        return self.root / DIRS.cache

    @property
    def publish_dir(self) -> Path:
        """
        Directory for final published deliverables.

        Priority:
        1. Environment variable MEDIA_ENGINE_PUBLISH_DIR
        2. Configured paths.publish in project.yaml
        3. Default: {project_root}/dist/{project-name}
        """
        import os

        # Check environment variable first (uses centralized ENV var name)
        env_publish = os.environ.get(ENV.publish_dir)
        if env_publish:
            return Path(env_publish) / self.config.name.lower().replace(" ", "-")

        # Check project config
        if self.config.paths.publish:
            publish_path = self.config.paths.publish
            # Support both absolute and relative paths
            if publish_path.is_absolute():
                return publish_path
            return self.root / publish_path

        # Default to project/dist/project-name
        return self.root / "dist" / self.config.name.lower().replace(" ", "-")

    @property
    def deliverables_dir(self) -> Path:
        """
        Directory for final video deliverables (release-quality only).

        Priority:
        1. Environment variable MEDIA_ENGINE_DELIVERABLES_DIR
        2. Configured paths.deliverables in project.yaml (supports ~)
        3. Default: {project_root}/deliverables

        Preview videos are never copied to this directory.
        """
        import os

        # Check environment variable first
        env_deliverables = os.environ.get("MEDIA_ENGINE_DELIVERABLES_DIR")
        if env_deliverables:
            return Path(env_deliverables).expanduser()

        # Check project config
        if self.config.paths.deliverables:
            return Path(self.config.paths.deliverables).expanduser()

        # Default to project/deliverables
        return self.root / "deliverables"

    # === Content Access ===

    def get_content_path(self, language: str, *parts: str) -> Path:
        """Get path to content for a language."""
        return self.content_dir / language / Path(*parts)

    def get_chapters_dir(self, language: str) -> Path:
        """Get chapters directory for a language."""
        return self.get_content_path(language, "chapters")

    def get_scripts_dir(self, language: str) -> Path:
        """Get scripts directory for a language."""
        return self.get_content_path(language, "scripts")

    def list_chapters(self, language: str = None) -> list[Path]:
        """List all chapter files for a language."""
        lang = language or self.source_language
        chapters_dir = self.get_chapters_dir(lang)
        if not chapters_dir.exists():
            return []
        return sorted(chapters_dir.glob("*.md"))

    def list_scripts(self, language: str = None) -> list[Path]:
        """List all video script files for a language."""
        lang = language or self.source_language
        scripts_dir = self.get_scripts_dir(lang)
        if not scripts_dir.exists():
            return []
        return sorted(scripts_dir.glob("*.yaml"))

    # === Caching ===

    def _load_cache_manifest(self) -> None:
        """Load the cache manifest."""
        manifest_path = self.cache_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                self._cache_manifest = json.load(f)
        else:
            self._cache_manifest = {
                "content_hashes": {},
                "builds": {},
                "voiceover": {},
            }

    def _save_cache_manifest(self) -> None:
        """Save the cache manifest."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.cache_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(self._cache_manifest, f, indent=2)

    def hash_file(self, path: Path) -> str:
        """Compute SHA256 hash of a file."""
        if not path.exists():
            return ""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(CACHE.chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[: CACHE.hash_length]

    def hash_content(self, content: str) -> str:
        """Compute SHA256 hash of string content."""
        return hashlib.sha256(content.encode()).hexdigest()[: CACHE.hash_length]

    def is_cached(self, key: str, current_hash: str) -> bool:
        """Check if a cached item is still valid."""
        cached = self._cache_manifest.get("content_hashes", {}).get(key)
        return cached == current_hash

    def update_cache(self, key: str, content_hash: str) -> None:
        """Update cache entry for a key."""
        if "content_hashes" not in self._cache_manifest:
            self._cache_manifest["content_hashes"] = {}
        self._cache_manifest["content_hashes"][key] = content_hash
        self._save_cache_manifest()

    def get_cached_voiceover(self, script_hash: str) -> Optional[Path]:
        """Get cached voiceover audio if available."""
        cache_info = self._cache_manifest.get("voiceover", {}).get(script_hash)
        if cache_info:
            audio_path = self.cache_dir / "voiceover" / cache_info["filename"]
            if audio_path.exists():
                return audio_path
        return None

    def cache_voiceover(self, script_hash: str, audio_path: Path, duration: float) -> Path:
        """Cache voiceover audio and return cache path."""
        cache_vo_dir = self.cache_dir / "voiceover"
        cache_vo_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{script_hash}.mp3"
        cache_path = cache_vo_dir / filename

        # Copy to cache
        import shutil

        shutil.copy2(audio_path, cache_path)

        # Update manifest
        if "voiceover" not in self._cache_manifest:
            self._cache_manifest["voiceover"] = {}
        self._cache_manifest["voiceover"][script_hash] = {
            "filename": filename,
            "duration": duration,
        }
        self._save_cache_manifest()

        return cache_path

    # === Build Tracking ===

    def should_rebuild(self, output_key: str, dependencies: list[Path]) -> bool:
        """
        Determine if an output needs rebuilding.

        Args:
            output_key: Unique identifier for the output
            dependencies: List of source files this output depends on

        Returns:
            True if rebuild is needed
        """
        builds = self._cache_manifest.get("builds", {})
        last_build = builds.get(output_key)

        if not last_build:
            return True

        # Check each dependency
        for dep in dependencies:
            current_hash = self.hash_file(dep)
            cached_hash = last_build.get("deps", {}).get(str(dep))
            if current_hash != cached_hash:
                return True

        # Check if output exists
        output_path = last_build.get("output_path")
        if output_path and not Path(output_path).exists():
            return True

        return False

    def record_build(self, output_key: str, output_path: Path, dependencies: list[Path]) -> None:
        """Record a successful build."""
        if "builds" not in self._cache_manifest:
            self._cache_manifest["builds"] = {}

        self._cache_manifest["builds"][output_key] = {
            "output_path": str(output_path),
            "deps": {str(dep): self.hash_file(dep) for dep in dependencies},
            "built_at": __import__("datetime").datetime.now().isoformat(),
        }
        self._save_cache_manifest()

    def clear_cache(self, cache_type: str = None) -> int:
        """
        Clear cached data.

        Args:
            cache_type: Specific cache to clear (voiceover, builds, all)

        Returns:
            Number of items cleared
        """
        import shutil

        count = 0

        if cache_type in (None, "all", "voiceover"):
            vo_dir = self.cache_dir / "voiceover"
            if vo_dir.exists():
                count += len(list(vo_dir.glob("*")))
                shutil.rmtree(vo_dir)
            self._cache_manifest["voiceover"] = {}

        if cache_type in (None, "all", "builds"):
            count += len(self._cache_manifest.get("builds", {}))
            self._cache_manifest["builds"] = {}

        if cache_type in (None, "all"):
            self._cache_manifest["content_hashes"] = {}

        self._save_cache_manifest()
        return count

    # === Status ===

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive project status.

        Returns:
            Dictionary with project status information
        """
        status = {
            "project": {
                "name": self.config.name,
                "root": str(self.root),
            },
            "languages": list(self.languages.keys()),
            "source_language": self.source_language,
            "content": {},
            "cache": {},
        }

        # Count content per language
        for lang in self.languages:
            chapters = self.list_chapters(lang)
            scripts = self.list_scripts(lang)
            status["content"][lang] = {
                "chapters": len(chapters),
                "scripts": len(scripts),
            }

        # Cache stats
        status["cache"] = {
            "voiceover_items": len(self._cache_manifest.get("voiceover", {})),
            "builds_tracked": len(self._cache_manifest.get("builds", {})),
        }

        return status

    def __repr__(self) -> str:
        return f"Project({self.config.name!r}, root={self.root})"


def find_project(start_dir: Path = None) -> Optional[Project]:
    """
    Find and load a project by searching up the directory tree.

    Args:
        start_dir: Directory to start searching from (default: cwd)

    Returns:
        Project if found, None otherwise
    """
    current = Path(start_dir or Path.cwd()).resolve()

    while current != current.parent:
        if (current / "project.yaml").exists():
            return Project.load(current)
        current = current.parent

    return None
