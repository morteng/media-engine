"""
Configuration Management

Load and validate project configuration from YAML files.
Uses centralized settings from media_engine.settings for all defaults.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Import centralized settings
from ..settings import DIRS, QUALITY, VIDEO, VOICEOVER


@dataclass
class VoiceoverConfig:
    """Voiceover generation settings."""

    provider: str = VOICEOVER.provider
    voice_id: str = ""
    stability: float = VOICEOVER.stability
    similarity_boost: float = VOICEOVER.similarity_boost
    language: str = VOICEOVER.language


@dataclass
class VideoConfig:
    """Video output settings."""

    width: int = VIDEO.width
    height: int = VIDEO.height
    fps: int = VIDEO.fps
    codec: str = VIDEO.codec


@dataclass
class PathsConfig:
    """Project paths."""

    output: Path = field(default_factory=lambda: Path(DIRS.output))
    assets: Path = field(default_factory=lambda: Path(DIRS.assets))
    content: Path = field(default_factory=lambda: Path(DIRS.content))
    publish: Optional[Path] = None  # None means use default: {project}/dist
    deliverables: Optional[str] = None  # None means use default: {project}/deliverables


@dataclass
class FreshnessConfig:
    """Freshness tracking settings."""

    ignore_patterns: list = field(default_factory=list)
    default_freshness_days: int = QUALITY.freshness_default_days
    scan_dirs: list = field(default_factory=list)  # Additional dirs to scan


@dataclass
class QualityConfig:
    """Quality and readability settings."""

    target_reading_level: str = QUALITY.target_reading_level  # elementary, middle_school, high_school, college, graduate
    target_lix_level: str = QUALITY.target_lix_level  # very_easy, easy, medium, difficult, very_difficult (Norwegian)
    max_sentence_words: int = QUALITY.max_sentence_words


@dataclass
class Config:
    """Project configuration."""

    name: str = "Untitled Project"
    description: str = ""
    voiceover: VoiceoverConfig = field(default_factory=VoiceoverConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    freshness: FreshnessConfig = field(default_factory=FreshnessConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        project = data.get("project", {})
        voiceover = data.get("voiceover", {})
        video = data.get("video", {})
        paths = data.get("paths", {})
        freshness = data.get("freshness", {})
        quality = data.get("quality", {})

        return cls(
            name=project.get("name", "Untitled Project"),
            description=project.get("description", ""),
            voiceover=VoiceoverConfig(
                provider=voiceover.get("provider", VOICEOVER.provider),
                voice_id=voiceover.get("voice_id", ""),
                stability=voiceover.get("stability", VOICEOVER.stability),
                similarity_boost=voiceover.get("similarity_boost", VOICEOVER.similarity_boost),
                language=voiceover.get("language", VOICEOVER.language),
            ),
            video=VideoConfig(
                width=video.get("width", VIDEO.width),
                height=video.get("height", VIDEO.height),
                fps=video.get("fps", VIDEO.fps),
                codec=video.get("codec", VIDEO.codec),
            ),
            paths=PathsConfig(
                output=Path(paths.get("output", DIRS.output)),
                assets=Path(paths.get("assets", DIRS.assets)),
                content=Path(paths.get("content", DIRS.content)),
                publish=Path(paths["publish"]) if paths.get("publish") else None,
                deliverables=paths.get("deliverables"),  # String path or None
            ),
            freshness=FreshnessConfig(
                ignore_patterns=freshness.get("ignore_patterns", []),
                default_freshness_days=freshness.get(
                    "default_freshness_days", QUALITY.freshness_default_days
                ),
                scan_dirs=freshness.get("scan_dirs", []),
            ),
            quality=QualityConfig(
                target_reading_level=quality.get(
                    "target_reading_level", QUALITY.target_reading_level
                ),
                target_lix_level=quality.get(
                    "target_lix_level", QUALITY.target_lix_level
                ),
                max_sentence_words=quality.get(
                    "max_sentence_words", QUALITY.max_sentence_words
                ),
            ),
            extra={
                k: v
                for k, v in data.items()
                if k not in ("project", "voiceover", "video", "paths", "freshness", "quality")
            },
        )


def load_config(path: Path) -> Config:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config.yaml file

    Returns:
        Config object with loaded settings
    """
    if not path.exists():
        return Config()

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    return Config.from_dict(data)
