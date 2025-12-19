"""
Media Engine Video Module

Provides video production tools:
    - VideoBuilder: High-level video orchestrator
    - Timeline: Frame-accurate video sequencing
    - Capture: Playwright-based screen recording
    - SceneCapture: Per-scene demo clip capture
    - DemoRegistry: Named demo state management
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
from .demo_registry import (
    DemoDefinition,
    DemoRegistry,
    DemoState,
)
from .scene_capture import (
    SceneCaptureConfig,
    SceneCaptureEngine,
    SceneCaptureResult,
    capture_scene_clips,
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
    # Demo Registry
    "DemoRegistry",
    "DemoDefinition",
    "DemoState",
    # Scene Capture
    "SceneCaptureEngine",
    "SceneCaptureConfig",
    "SceneCaptureResult",
    "capture_scene_clips",
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
