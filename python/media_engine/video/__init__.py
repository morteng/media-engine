"""
Media Engine Video Module

Provides video production tools:
    - VideoBuilder: High-level video orchestrator
    - Timeline: Frame-accurate video sequencing
    - Capture: Playwright-based screen recording
    - Voiceover: ElevenLabs TTS integration with caching
    - Captions: WebVTT caption generation
"""

from .timeline import (
    VideoTimeline,
    TimelineClip,
    TimelineTrack,
    TrackType,
    TransitionType,
)
from .voiceover import (
    generate_voiceover,
    generate_voiceover_for_script,
    generate_voiceover_macos,
    AudioSegment,
    VoiceoverResult,
)
from .builder import (
    VideoBuilder,
    VideoConfig,
    VideoScript,
    VideoScene,
    VideoBuildResult,
    build_video,
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
