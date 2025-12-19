"""
Video Quality Presets

Defines quality levels for video rendering with appropriate settings
for preview (fast iteration) and production (final deliverable).
"""

from dataclasses import dataclass
from enum import Enum


class VideoQuality(Enum):
    """Video quality levels."""

    PREVIEW = "preview"  # Fast iteration: 720p, 24fps
    PRODUCTION = "production"  # Full quality: 1080p, 60fps


@dataclass(frozen=True)
class QualityPreset:
    """Quality preset with rendering settings."""

    quality: VideoQuality
    width: int
    height: int
    fps: int
    crf: int  # FFmpeg CRF (lower = better quality, higher file size)
    is_releasable: bool  # Can be copied to deliverables

    @property
    def resolution(self) -> tuple[int, int]:
        """Get resolution as tuple."""
        return (self.width, self.height)

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio."""
        return self.width / self.height


# Quality presets
PREVIEW_PRESET = QualityPreset(
    quality=VideoQuality.PREVIEW,
    width=1280,
    height=720,
    fps=24,
    crf=28,
    is_releasable=False,
)

PRODUCTION_PRESET = QualityPreset(
    quality=VideoQuality.PRODUCTION,
    width=1920,
    height=1080,
    fps=60,
    crf=18,
    is_releasable=True,
)

# Lookup table
_PRESETS = {
    VideoQuality.PREVIEW: PREVIEW_PRESET,
    VideoQuality.PRODUCTION: PRODUCTION_PRESET,
}


def get_preset(quality: VideoQuality) -> QualityPreset:
    """
    Get the quality preset for a given quality level.

    Args:
        quality: VideoQuality enum value

    Returns:
        QualityPreset with rendering settings
    """
    return _PRESETS[quality]


def get_filename_suffix(quality: VideoQuality) -> str:
    """
    Get the filename suffix for a quality level.

    Args:
        quality: VideoQuality enum value

    Returns:
        Suffix string (e.g., ".preview" or "")
    """
    if quality == VideoQuality.PREVIEW:
        return ".preview"
    return ""


def is_preview_video(filename: str) -> bool:
    """
    Check if a filename indicates a preview video.

    Args:
        filename: Video filename to check

    Returns:
        True if the file is a preview video
    """
    return ".preview." in filename or filename.endswith(".preview.mp4")
