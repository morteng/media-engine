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
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from .voiceover import (
    VoiceoverResult,
    clean_text,
    generate_voiceover,
)

if TYPE_CHECKING:
    from ..core.project import Project


@dataclass
class VideoConfig:
    """Video production configuration."""

    width: int = 1920
    height: int = 1080
    fps: int = 30
    format: str = "mp4"
    codec: str = "h264"
    crf: int = 23  # Quality (lower = better, 0-51)


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

            scenes.append(
                VideoScene(
                    id=scene_data.get("id", f"scene_{len(scenes)}"),
                    type=scene_data.get("type", "content"),
                    title=scene_data.get("title"),
                    text=content.get("text") or content.get("narration"),
                    duration=scene_data.get("duration"),
                    visual=scene_data.get("visual", {}),
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
    ) -> VideoBuildResult:
        """
        Build video from script.

        Args:
            script_path: Path to video script YAML
            output_dir: Output directory (default: project output dir)
            render: Whether to render video with Remotion
            remotion_project: Path to Remotion project for rendering

        Returns:
            VideoBuildResult with paths to generated files
        """
        result = VideoBuildResult()

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

            # Generate voiceover
            audio_path = output_dir / f"{script.name}.mp3"
            voiceover = await self._generate_voiceover(script, audio_path)
            result.audio_path = audio_path
            result.duration = voiceover.total_duration

            # Update scene timings from voiceover
            self._update_scene_timings(script, voiceover)

            # Generate captions
            captions_path = output_dir / f"{script.name}.vtt"
            self._generate_captions(script, voiceover, captions_path)
            result.captions_path = captions_path

            # Export Remotion props
            props_path = output_dir / f"{script.name}.props.json"
            self._export_remotion_props(script, voiceover, props_path)
            result.props_path = props_path

            # Optionally render with Remotion
            if render and remotion_project:
                video_path = output_dir / f"{script.name}.mp4"
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
    ) -> VoiceoverResult:
        """Generate voiceover audio from script."""
        # Collect text segments
        texts = []
        for scene in script.scenes:
            if scene.text:
                texts.append((scene.id, scene.text))

        if not texts:
            raise ValueError("No voiceover text in script")

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
        """Update scene timings from voiceover segments."""
        # Create lookup by scene ID
        segment_lookup = {seg.id: seg for seg in voiceover.segments}

        current_time = 0.0
        for scene in script.scenes:
            segment = segment_lookup.get(scene.id)

            if segment:
                scene.audio_start = current_time
                scene.duration = segment.duration + segment.pause_after
                scene.audio_end = current_time + scene.duration
                current_time = scene.audio_end
            elif scene.duration:
                # Scene has explicit duration but no voiceover
                scene.audio_start = current_time
                scene.audio_end = current_time + scene.duration
                current_time = scene.audio_end
            else:
                # Default duration for non-voiced scenes
                scene.audio_start = current_time
                scene.duration = 2.0
                scene.audio_end = current_time + 2.0
                current_time += 2.0

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

    def _export_remotion_props(
        self,
        script: VideoScript,
        voiceover: VoiceoverResult,
        output_path: Path,
    ):
        """Export Remotion-compatible props JSON."""
        props = {
            "title": script.title,
            "name": script.name,
            "language": script.language,
            "duration": voiceover.total_duration,
            "fps": self.config.fps,
            "width": self.config.width,
            "height": self.config.height,
            "scenes": [],
        }

        for scene in script.scenes:
            props["scenes"].append(
                {
                    "id": scene.id,
                    "type": scene.type,
                    "title": scene.title,
                    "text": clean_text(scene.text) if scene.text else None,
                    "startFrame": int((scene.audio_start or 0) * self.config.fps),
                    "endFrame": int((scene.audio_end or 0) * self.config.fps),
                    "durationFrames": int((scene.duration or 0) * self.config.fps),
                    "visual": scene.visual,
                }
            )

        output_path.write_text(json.dumps(props, indent=2))

    def _render_with_remotion(
        self,
        remotion_project: Path,
        props_path: Path,
        audio_path: Path,
        output_path: Path,
    ):
        """Render video using Remotion CLI."""
        # Check if Remotion is available
        result = subprocess.run(
            ["npx", "remotion", "--version"],
            capture_output=True,
            cwd=remotion_project,
        )
        if result.returncode != 0:
            raise RuntimeError("Remotion not available. Install with: npm install @remotion/cli")

        # Render video
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
            "--crf",
            str(self.config.crf),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=remotion_project,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed: {result.stderr}")


async def build_video(
    script_path: Path,
    output_dir: Optional[Path] = None,
    project: "Project" = None,
    render: bool = False,
    remotion_project: Optional[Path] = None,
) -> VideoBuildResult:
    """
    Convenience function to build a video.

    Args:
        script_path: Path to video script YAML
        output_dir: Output directory
        project: Optional Project for configuration
        render: Whether to render with Remotion
        remotion_project: Path to Remotion project

    Returns:
        VideoBuildResult
    """
    builder = VideoBuilder(project=project)
    return await builder.build(
        script_path=script_path,
        output_dir=output_dir,
        render=render,
        remotion_project=remotion_project,
    )
