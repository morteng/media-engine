"""
Configuration Management

Load and validate project configuration from YAML files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


@dataclass
class VoiceoverConfig:
    """Voiceover generation settings."""
    provider: str = "elevenlabs"
    voice_id: str = ""
    stability: float = 0.5
    similarity_boost: float = 0.75
    language: str = "en"


@dataclass
class VideoConfig:
    """Video output settings."""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "h264"


@dataclass
class PathsConfig:
    """Project paths."""
    output: Path = field(default_factory=lambda: Path("output"))
    assets: Path = field(default_factory=lambda: Path("assets"))
    content: Path = field(default_factory=lambda: Path("content"))


@dataclass
class Config:
    """Project configuration."""
    name: str = "Untitled Project"
    description: str = ""
    voiceover: VoiceoverConfig = field(default_factory=VoiceoverConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        project = data.get("project", {})
        voiceover = data.get("voiceover", {})
        video = data.get("video", {})
        paths = data.get("paths", {})

        return cls(
            name=project.get("name", "Untitled Project"),
            description=project.get("description", ""),
            voiceover=VoiceoverConfig(
                provider=voiceover.get("provider", "elevenlabs"),
                voice_id=voiceover.get("voice_id", ""),
                stability=voiceover.get("stability", 0.5),
                similarity_boost=voiceover.get("similarity_boost", 0.75),
                language=voiceover.get("language", "en"),
            ),
            video=VideoConfig(
                width=video.get("width", 1920),
                height=video.get("height", 1080),
                fps=video.get("fps", 30),
                codec=video.get("codec", "h264"),
            ),
            paths=PathsConfig(
                output=Path(paths.get("output", "output")),
                assets=Path(paths.get("assets", "assets")),
                content=Path(paths.get("content", "content")),
            ),
            extra={k: v for k, v in data.items()
                   if k not in ("project", "voiceover", "video", "paths")},
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
