"""
Media Engine Video Module

Provides video production tools:
    - VideoBuilder: High-level video orchestrator
    - Timeline: Frame-accurate video sequencing
    - Capture: Playwright-based screen recording
    - Voiceover: ElevenLabs TTS integration with caching
    - Captions: WebVTT caption generation
"""

from .builder import (
    VideoBuilder,
    VideoBuildResult,
    VideoConfig,
    VideoScene,
    VideoScript,
    build_video,
)
from .timeline import (
    TimelineClip,
    TimelineTrack,
    TrackType,
    TransitionType,
    VideoTimeline,
)
from .voiceover import (
    AudioSegment,
    VoiceoverResult,
    generate_voiceover,
    generate_voiceover_for_script,
    generate_voiceover_macos,
)

__all__ = [
    # Builder
    "VideoBuilder",
    "VideoConfig",
    "VideoScript",
    "VideoScene",
    "VideoBuildResult",
    "build_video",
    # Timeline
    "VideoTimeline",
    "TimelineClip",
    "TimelineTrack",
    "TrackType",
    "TransitionType",
    # Voiceover
    "generate_voiceover",
    "generate_voiceover_for_script",
    "generate_voiceover_macos",
    "AudioSegment",
    "VoiceoverResult",
]
