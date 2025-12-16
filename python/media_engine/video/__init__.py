"""
Media Engine Video Module

Provides video production tools:
    - Timeline: Frame-accurate video sequencing
    - Capture: Playwright-based screen recording
    - Voiceover: ElevenLabs TTS integration
    - Captions: WebVTT caption generation
"""

from .timeline import (
    VideoTimeline,
    TimelineClip,
    TimelineTrack,
    TrackType,
    TransitionType,
)

__all__ = [
    # Timeline
    "VideoTimeline",
    "TimelineClip",
    "TimelineTrack",
    "TrackType",
    "TransitionType",
]
