"""
Video Builder Module

High-level video production orchestrator that integrates:
- Script parsing
- Voiceover generation
- Caption generation
- Remotion rendering

Usage:
    builder = VideoBuilder(project)
    result = await builder.build("mvp-demo.yaml")
"""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from .quality import (
    VideoQuality,
    get_filename_suffix,
    get_preset,
)
from .voiceover import (
    VoiceoverResult,
    clean_text,
    generate_voiceover,
)
from .camera_capture import CameraConfig, CaptureResult
from .camera_path import CameraPathGenerator

if TYPE_CHECKING:
    from ..core.project import Project


@dataclass
class VideoConfig:
    """Video production configuration."""

    width: int = 1920
    height: int = 1080
    fps: int = 60
    format: str = "mp4"
    codec: str = "h264"
    crf: int = 18  # Quality (lower = better, 0-51)
    quality: VideoQuality = VideoQuality.PRODUCTION

    @classmethod
    def from_quality(cls, quality: VideoQuality) -> "VideoConfig":
        """Create config from a quality preset."""
        preset = get_preset(quality)
        return cls(
            width=preset.width,
            height=preset.height,
            fps=preset.fps,
            crf=preset.crf,
            quality=quality,
        )

    @property
    def is_releasable(self) -> bool:
        """Check if output from this config can be released."""
        preset = get_preset(self.quality)
        return preset.is_releasable


@dataclass
class CaptionEntry:
    """A caption entry with timing."""

    id: str
    text: str
    start_time: float
    end_time: float
    style: str = "default"


@dataclass
class VideoScene:
    """A scene in the video."""

    id: str
    type: str  # intro, content, demo, transition, outro
    title: Optional[str] = None
    text: Optional[str] = None
    duration: Optional[float] = None  # Will be calculated from voiceover
    visual: dict = field(default_factory=dict)
    audio_start: Optional[float] = None
    audio_end: Optional[float] = None
    # Frame-accurate timing (primary source of truth)
    start_frame: int = 0
    end_frame: int = 0
    duration_frames: int = 0
    # Scene-based demo capture
    demo_clip_path: Optional[Path] = None  # Path to captured clip for this scene
    # Camera animation data
    camera_data: Optional[dict] = None  # Camera animation data for Remotion


@dataclass
class VideoScript:
    """Complete video script definition."""

    name: str
    title: str
    language: str
    scenes: list[VideoScene] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "VideoScript":
        """Load script from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        metadata = data.get("metadata", {})
        scenes = []

        for scene_data in data.get("scenes", []):
            content = scene_data.get("content", {})
            if isinstance(content, str):
                content = {"text": content}

            # Support multiple voiceover field names
            text = (
                scene_data.get("voiceover")  # New format
                or content.get("text")
                or content.get("narration")
            )
            # Handle multiline voiceover
            if isinstance(text, str):
                text = text.strip()

            # Parse visual with demo reference
            visual = scene_data.get("visual", {})

            # Support demo reference at scene level or in visual
            demo_ref = scene_data.get("demo") or visual.get("demo")
            if demo_ref:
                visual["demo"] = demo_ref

            scenes.append(
                VideoScene(
                    id=scene_data.get("id", f"scene_{len(scenes)}"),
                    type=scene_data.get("type", scene_data.get("scene_type", "content")),
                    title=scene_data.get("title") or scene_data.get("name"),
                    text=text,
                    duration=scene_data.get("duration"),
                    visual=visual,
                )
            )

        return cls(
            name=path.stem,
            title=metadata.get("title", path.stem),
            language=metadata.get("language", "en"),
            scenes=scenes,
            metadata=metadata,
        )


@dataclass
class VideoBuildResult:
    """Result of video build process."""

    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    captions_path: Optional[Path] = None
    props_path: Optional[Path] = None
    duration: float = 0.0
    success: bool = False
    error: Optional[str] = None
    # Quality tracking
    quality: VideoQuality = VideoQuality.PRODUCTION
    is_releasable: bool = True


class VideoBuilder:
    """
    High-level video production orchestrator.

    Workflow:
    1. Parse script YAML
    2. Generate voiceover audio with timing
    3. Generate captions from voiceover
    4. Export Remotion props or render directly
    """

    def __init__(
        self,
        project: "Project" = None,
        config: VideoConfig = None,
    ):
        self.project = project
        self.config = config or VideoConfig()

        # Set config from project if available
        if project and project.config.video:
            video_cfg = project.config.video
            if hasattr(video_cfg, "width"):
                self.config.width = video_cfg.width
            if hasattr(video_cfg, "height"):
                self.config.height = video_cfg.height
            if hasattr(video_cfg, "fps"):
                self.config.fps = video_cfg.fps

    async def build(
        self,
        script_path: Path,
        output_dir: Optional[Path] = None,
        render: bool = False,
        remotion_project: Optional[Path] = None,
        capture_demos: bool = True,
        mock_voiceover: bool = False,
    ) -> VideoBuildResult:
        """
        Build video from script.

        Args:
            script_path: Path to video script YAML
            output_dir: Output directory (default: project output dir)
            render: Whether to render video with Remotion
            remotion_project: Path to Remotion project for rendering
            capture_demos: Whether to capture per-scene demo clips
            mock_voiceover: Use silent mock audio instead of TTS (for testing)

        Returns:
            VideoBuildResult with paths to generated files
        """
        result = VideoBuildResult(
            quality=self.config.quality,
            is_releasable=self.config.is_releasable,
        )

        # Get filename suffix based on quality (.preview for preview mode)
        suffix = get_filename_suffix(self.config.quality)

        try:
            # Parse script
            script = VideoScript.from_yaml(script_path)

            # Determine output directory
            if output_dir is None:
                if self.project:
                    output_dir = self.project.output_dir / script.language / "videos"
                else:
                    output_dir = script_path.parent / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate voiceover (always full quality - audio doesn't need preview)
            audio_path = output_dir / f"{script.name}.mp3"
            voiceover = await self._generate_voiceover(script, audio_path, mock=mock_voiceover)
            result.audio_path = audio_path
            result.duration = voiceover.total_duration

            # Update scene timings from voiceover
            self._update_scene_timings(script, voiceover)

            # Capture per-scene demo clips (after timing is set)
            demo_clips = {}
            if capture_demos and self._has_scene_demos(script):
                demo_clips = await self._capture_scene_demos(script, output_dir)

            # Process camera animation scenes (after timing is set)
            camera_data = {}
            if self._has_camera_scenes(script):
                camera_data = await self._process_camera_scenes(script, output_dir)

            # Generate captions (reuse for all quality levels)
            captions_path = output_dir / f"{script.name}.vtt"
            self._generate_captions(script, voiceover, captions_path)
            result.captions_path = captions_path

            # Export Remotion props with quality suffix
            props_path = output_dir / f"{script.name}{suffix}.props.json"
            self._export_remotion_props(script, voiceover, props_path, demo_clips)
            result.props_path = props_path

            # Optionally render with Remotion
            if render and remotion_project:
                video_path = output_dir / f"{script.name}{suffix}.mp4"
                self._render_with_remotion(
                    remotion_project,
                    props_path,
                    audio_path,
                    video_path,
                )
                result.video_path = video_path

            result.success = True

        except Exception as e:
            result.error = str(e)
            result.success = False

        return result

    async def _generate_voiceover(
        self,
        script: VideoScript,
        output_path: Path,
        mock: bool = False,
    ) -> VoiceoverResult:
        """Generate voiceover audio from script."""
        from .voiceover import generate_voiceover_mock

        # Collect text segments
        texts = []
        for scene in script.scenes:
            if scene.text:
                texts.append((scene.id, scene.text))

        if not texts:
            raise ValueError("No voiceover text in script")

        # Use mock voiceover if requested (silent audio with estimated timing)
        if mock:
            return await generate_voiceover_mock(
                texts=texts,
                output_path=output_path,
            )

        # Get voice configuration
        voice_id = None
        cache_dir = None
        stability = 0.5
        similarity_boost = 0.75

        if self.project:
            lang_config = self.project.languages.get(script.language)
            if lang_config:
                voice_id = lang_config.voice_id

            if not voice_id:
                voice_id = self.project.config.voiceover.voice_id

            cache_dir = self.project.cache_dir / "voiceover"
            stability = self.project.config.voiceover.stability
            similarity_boost = self.project.config.voiceover.similarity_boost

        if not voice_id:
            raise ValueError(
                f"No voice_id configured for language '{script.language}'. "
                "Set it in project.yaml under languages or voiceover.voice_id"
            )

        return await generate_voiceover(
            texts=texts,
            output_path=output_path,
            voice_id=voice_id,
            cache_dir=cache_dir,
            language=script.language,
            stability=stability,
            similarity_boost=similarity_boost,
        )

    def _update_scene_timings(
        self,
        script: VideoScript,
        voiceover: VoiceoverResult,
    ):
        """
        Update scene timings from voiceover segments.

        Uses frame-based cumulative calculation to prevent timing drift.
        Frames are the primary source of truth; float times are computed.
        """
        # Create lookup by scene ID
        segment_lookup = {seg.id: seg for seg in voiceover.segments}
        fps = self.config.fps

        # Cumulative frame counter (prevents drift)
        current_frame = 0

        for scene in script.scenes:
            segment = segment_lookup.get(scene.id)

            scene.start_frame = current_frame

            if segment:
                # Calculate frames from duration, rounding properly
                duration_frames = round(segment.duration * fps)
                pause_frames = round(segment.pause_after * fps)
                scene.duration_frames = duration_frames + pause_frames
            elif scene.duration:
                # Scene has explicit duration but no voiceover
                scene.duration_frames = round(scene.duration * fps)
            else:
                # Default 2 seconds for non-voiced scenes
                scene.duration_frames = round(2.0 * fps)

            scene.end_frame = current_frame + scene.duration_frames
            current_frame = scene.end_frame

            # Compute float times from frames (for backwards compatibility)
            scene.audio_start = scene.start_frame / fps
            scene.audio_end = scene.end_frame / fps
            scene.duration = scene.duration_frames / fps

        # Validate total frames match voiceover duration (within 1 frame tolerance)
        expected_frames = round(voiceover.total_duration * fps)
        if abs(current_frame - expected_frames) > 1:
            # Log warning but don't fail - voiceover timing may include rounding
            import logging

            logging.warning(
                f"Frame timing mismatch: scenes={current_frame} frames, "
                f"audio={expected_frames} frames (diff={current_frame - expected_frames})"
            )

    def _generate_captions(
        self,
        script: VideoScript,
        voiceover: VoiceoverResult,
        output_path: Path,
    ):
        """Generate WebVTT captions from voiceover."""
        entries = []
        current_time = 0.0

        for segment in voiceover.segments:
            if segment.text and clean_text(segment.text):
                entries.append(
                    CaptionEntry(
                        id=segment.id,
                        text=clean_text(segment.text),
                        start_time=current_time,
                        end_time=current_time + segment.duration,
                    )
                )
            current_time += segment.duration + segment.pause_after

        # Generate VTT content
        vtt_content = self._format_vtt(entries, script.title)
        output_path.write_text(vtt_content)

    def _format_vtt(self, entries: list[CaptionEntry], title: str = "") -> str:
        """Format caption entries as WebVTT."""
        lines = ["WEBVTT", ""]

        if title:
            lines.append(f"NOTE Title: {title}")
            lines.append("")

        for i, entry in enumerate(entries, 1):
            lines.append(str(i))
            start = self._format_timestamp(entry.start_time)
            end = self._format_timestamp(entry.end_time)
            lines.append(f"{start} --> {end}")
            lines.append(entry.text)
            lines.append("")

        return "\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as WebVTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def _has_scene_demos(self, script: VideoScript) -> bool:
        """Check if any scene has a demo reference."""
        for scene in script.scenes:
            demo_ref = scene.visual.get("demo")
            if demo_ref and isinstance(demo_ref, dict):
                if "source" in demo_ref and "state" in demo_ref:
                    return True
        return False

    async def _capture_scene_demos(
        self,
        script: VideoScript,
        output_dir: Path,
    ) -> dict[str, Path]:
        """Capture per-scene demo clips using SceneCaptureEngine."""
        from .scene_capture import SceneCaptureEngine

        engine = SceneCaptureEngine(project=self.project)
        clips = await engine.capture_all_scenes(script, output_dir)

        # Store clip paths on scenes for reference
        for scene in script.scenes:
            if scene.id in clips:
                scene.demo_clip_path = clips[scene.id]

        return clips

    def _has_camera_scenes(self, script: VideoScript) -> bool:
        """Check if any scene has camera animation config."""
        for scene in script.scenes:
            camera_config = scene.visual.get("camera", {})
            if camera_config.get("mode") == "animated":
                return True
        return False

    async def _process_camera_scenes(
        self,
        script: VideoScript,
        output_dir: Path,
    ) -> dict[str, dict]:
        """
        Process scenes with camera animation.

        For each scene with camera config:
        1. Capture high-res screenshot with element bounds
        2. Generate resolved camera keyframes
        3. Store camera data for props export

        Returns:
            Dict mapping scene_id to camera data
        """
        from .camera_capture import CameraCaptureEngine, capture_demo_for_camera
        from .camera_path import CameraPathGenerator
        from .camera_presets import resolve_preset

        camera_data = {}

        for scene in script.scenes:
            camera_config_dict = scene.visual.get("camera", {})
            if camera_config_dict.get("mode") != "animated":
                continue

            # Get demo reference
            demo_ref = scene.visual.get("demo", {})
            if not demo_ref or not isinstance(demo_ref, dict):
                continue

            demo_source = demo_ref.get("source")
            demo_state = demo_ref.get("state")
            if not demo_source or not demo_state:
                continue

            # Parse camera config
            camera_config = CameraConfig.from_dict(camera_config_dict)

            # Handle preset-based focus sequence
            if camera_config.preset and not camera_config.focus_sequence:
                selectors = camera_config.get_all_selectors()
                camera_config.focus_sequence = resolve_preset(
                    camera_config.preset,
                    selectors,
                )

            # Find demo definition file
            demo_path = None
            if self.project:
                # Look in demo folder
                demo_path = self.project.content_dir / "demos" / f"{demo_source}.yaml"
                if not demo_path.exists():
                    demo_path = self.project.root / "content" / "en" / "demos" / f"{demo_source}.yaml"

            if not demo_path or not demo_path.exists():
                import logging
                logging.warning(f"Demo definition not found for {demo_source}")
                continue

            # Capture high-res screenshot with element bounds
            try:
                capture_output = output_dir / "camera_captures"
                capture_result = await capture_demo_for_camera(
                    demo_path=demo_path,
                    state_id=demo_state,
                    output_dir=capture_output,
                    camera_config=camera_config,
                    headless=True,
                )

                # Generate camera path data
                path_generator = CameraPathGenerator(
                    viewport_width=self.config.width,
                    viewport_height=self.config.height,
                    capture_scale=camera_config.capture_scale,
                )

                scene_camera_data = path_generator.generate_camera_data(
                    camera_config=camera_config,
                    element_bounds=capture_result.element_bounds,
                    total_frames=scene.duration_frames,
                    fps=self.config.fps,
                )

                # Add image path
                rel_path = capture_result.image_path.relative_to(output_dir)
                scene_camera_data["image_path"] = str(rel_path)

                # Store on scene
                scene.camera_data = scene_camera_data
                camera_data[scene.id] = scene_camera_data

            except Exception as e:
                import logging
                logging.error(f"Camera capture failed for {scene.id}: {e}")
                continue

        return camera_data

    def _export_remotion_props(
        self,
        script: VideoScript,
        voiceover: VoiceoverResult,
        output_path: Path,
        demo_clips: dict[str, Path] = None,
    ):
        """Export Remotion-compatible props JSON with quality metadata."""
        demo_clips = demo_clips or {}

        props = {
            "title": script.title,
            "name": script.name,
            "language": script.language,
            "duration": voiceover.total_duration,
            "fps": self.config.fps,
            "width": self.config.width,
            "height": self.config.height,
            # Quality metadata
            "quality": self.config.quality.value,
            "is_releasable": self.config.is_releasable,
            "resolution": {
                "width": self.config.width,
                "height": self.config.height,
            },
            "scenes": [],
        }

        for scene in script.scenes:
            # Use frame properties directly (no conversion needed)
            scene_props = {
                "id": scene.id,
                "type": scene.type,
                "title": scene.title,
                "text": clean_text(scene.text) if scene.text else None,
                "startFrame": scene.start_frame,
                "endFrame": scene.end_frame,
                "durationFrames": scene.duration_frames,
                "visual": scene.visual,
            }

            # Add demo clip info if captured
            if scene.id in demo_clips:
                clip_path = demo_clips[scene.id]
                # Use relative path from output directory
                rel_path = clip_path.relative_to(output_path.parent)
                scene_props["demo"] = {
                    "clipPath": str(rel_path),
                    "state": scene.visual.get("demo", {}).get("state", ""),
                }

            # Add camera animation data if present
            if scene.camera_data:
                scene_props["cameraData"] = scene.camera_data

            props["scenes"].append(scene_props)

        output_path.write_text(json.dumps(props, indent=2))

    def _render_with_remotion(
        self,
        remotion_project: Path,
        props_path: Path,
        audio_path: Path,
        output_path: Path,
    ):
        """Render video using Remotion CLI with quality settings."""
        # Check if Remotion is available (check node_modules since --version exits with 1)
        remotion_cli_path = remotion_project / "node_modules" / "@remotion" / "cli"
        if not remotion_cli_path.exists():
            raise RuntimeError("Remotion not available. Install with: npm install @remotion/cli")

        # Render video with quality settings
        cmd = [
            "npx",
            "remotion",
            "render",
            "Main",  # Composition ID
            str(output_path),
            "--props",
            str(props_path),
            "--audio-file",
            str(audio_path),
            "--codec",
            self.config.codec,
            "--audio-codec",
            "aac",  # Use built-in AAC (system ffmpeg lacks libfdk_aac)
            "--crf",
            str(self.config.crf),
            # Apply quality settings
            "--width",
            str(self.config.width),
            "--height",
            str(self.config.height),
            "--fps",
            str(self.config.fps),
            # Suppress per-frame progress output
            "--log",
            "error",
        ]

        # Use system ffmpeg to avoid macOS compatibility issues
        env = os.environ.copy()
        env["REMOTION_FFMPEG_EXECUTABLE"] = "/usr/local/bin/ffmpeg"
        env["REMOTION_FFPROBE_EXECUTABLE"] = "/usr/local/bin/ffprobe"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=remotion_project,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed: {result.stderr}")


async def build_video(
    script_path: Path,
    output_dir: Optional[Path] = None,
    project: "Project" = None,
    render: bool = False,
    remotion_project: Optional[Path] = None,
    quality: VideoQuality = VideoQuality.PRODUCTION,
) -> VideoBuildResult:
    """
    Convenience function to build a video.

    Args:
        script_path: Path to video script YAML
        output_dir: Output directory
        project: Optional Project for configuration
        render: Whether to render with Remotion
        remotion_project: Path to Remotion project
        quality: Video quality level (PREVIEW or PRODUCTION)

    Returns:
        VideoBuildResult
    """
    config = VideoConfig.from_quality(quality)
    builder = VideoBuilder(project=project, config=config)
    return await builder.build(
        script_path=script_path,
        output_dir=output_dir,
        render=render,
        remotion_project=remotion_project,
    )
