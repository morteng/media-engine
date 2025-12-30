"""
Media Engine Video Module

Provides video production tools:
    - VideoProject: Video project management with component tracking
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
from .quality import (
    PREVIEW_PRESET,
    PRODUCTION_PRESET,
    QualityPreset,
    VideoQuality,
    get_filename_suffix,
    get_preset,
    is_preview_video,
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
from .camera_capture import (
    CameraCaptureEngine,
    CameraConfig,
    CameraKeyframe,
    CaptureResult,
    ElementBounds,
    capture_demo_for_camera,
)
from .camera_effects import (
    CameraEffectsConfig,
    CameraShakeConfig,
    DepthOfFieldConfig,
    MotionBlurConfig,
    ParallaxConfig,
    PerspectiveTiltConfig,
    VignetteConfig,
    calculate_shake_offset,
    get_effect_preset,
)
from .camera_path import (
    CameraPathGenerator,
    CameraState,
    ResolvedKeyframe,
    catmull_rom_point,
    get_easing,
    lerp,
)
from .camera_presets import (
    CAMERA_PRESETS,
    CameraPreset,
    PresetResolver,
    get_preset as get_camera_preset,
    list_presets as list_camera_presets,
    resolve_preset,
)
from .project import (
    COMPONENT_DEPENDENCIES,
    ComponentStatus,
    ComponentType,
    ProjectStatus,
    VideoComponent,
    VideoProject,
    VideoProjectRegistry,
    generate_project_id,
)
from .review import (
    CommentPriority,
    CommentStatus,
    VideoReviewComment,
    VideoReviewStore,
)
from .video_capture import (
    CaptureResult as VideoCaptureResult,
    RecordingConfig,
    VideoCaptureEngine,
    capture_video,
)
from .cascade import (
    CascadeRegenerator,
    RegenerationResult,
    RegenerationStatus,
    RegenerationTask,
    cascade_regenerate,
)

__all__ = [
    # Video Project
    "VideoProject",
    "VideoProjectRegistry",
    "VideoComponent",
    "ProjectStatus",
    "ComponentType",
    "ComponentStatus",
    "COMPONENT_DEPENDENCIES",
    "generate_project_id",
    # Video Review
    "VideoReviewComment",
    "VideoReviewStore",
    "CommentStatus",
    "CommentPriority",
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
    # Quality
    "VideoQuality",
    "QualityPreset",
    "get_preset",
    "get_filename_suffix",
    "is_preview_video",
    "PREVIEW_PRESET",
    "PRODUCTION_PRESET",
    # Voiceover
    "generate_voiceover",
    "generate_voiceover_for_script",
    "generate_voiceover_macos",
    "AudioSegment",
    "VoiceoverResult",
    # Camera Capture
    "CameraCaptureEngine",
    "CameraConfig",
    "CameraKeyframe",
    "CaptureResult",
    "ElementBounds",
    "capture_demo_for_camera",
    # Camera Effects
    "CameraEffectsConfig",
    "CameraShakeConfig",
    "DepthOfFieldConfig",
    "MotionBlurConfig",
    "ParallaxConfig",
    "PerspectiveTiltConfig",
    "VignetteConfig",
    "calculate_shake_offset",
    "get_effect_preset",
    # Camera Path
    "CameraPathGenerator",
    "CameraState",
    "ResolvedKeyframe",
    "catmull_rom_point",
    "get_easing",
    "lerp",
    # Camera Presets
    "CAMERA_PRESETS",
    "CameraPreset",
    "PresetResolver",
    "get_camera_preset",
    "list_camera_presets",
    "resolve_preset",
    # Video Capture
    "VideoCaptureEngine",
    "VideoCaptureResult",
    "RecordingConfig",
    "capture_video",
    # Cascade Regeneration
    "CascadeRegenerator",
    "RegenerationResult",
    "RegenerationStatus",
    "RegenerationTask",
    "cascade_regenerate",
]
