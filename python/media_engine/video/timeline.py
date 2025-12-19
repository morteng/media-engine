#!/usr/bin/env python3
"""
Video Timeline - Master Sequencer for ROP Video Production

Orchestrates all video production elements with frame-accurate timing:
- Voiceover audio
- Screen recordings (demos)
- Motion graphics overlays
- Transitions
- Captions

The timeline is the single source of truth for video timing.

Usage:
    from video_timeline import VideoTimeline, TimelineBuilder

    # Build timeline from script and timing manifest
    builder = TimelineBuilder()
    timeline = builder.from_script(script, timing_manifest)

    # Export to various formats
    timeline.to_ffmpeg_script()  # FFmpeg filter complex
    timeline.to_premiere_xml()   # Adobe Premiere import
    timeline.to_resolve_edl()    # DaVinci Resolve EDL
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class TrackType(Enum):
    """Types of timeline tracks."""

    VIDEO = "video"  # Main video (screen recording)
    GRAPHICS = "graphics"  # Motion graphics overlay
    AUDIO = "audio"  # Voiceover audio
    MUSIC = "music"  # Background music
    CAPTION = "caption"  # Subtitles/captions


class TransitionType(Enum):
    """Types of transitions between clips."""

    CUT = "cut"
    CROSSFADE = "crossfade"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    WIPE = "wipe"
    COPPER_SWEEP = "copper_sweep"


@dataclass
class TimelineClip:
    """A single clip on the timeline."""

    id: str
    track: TrackType
    source_path: Optional[Path]  # None for generated clips
    start_time: float  # Timeline position (seconds)
    end_time: float  # End position (seconds)
    source_in: float = 0  # Source clip in point
    source_out: Optional[float] = None  # Source clip out point

    # Transform properties
    position: Tuple[int, int] = (0, 0)  # x, y offset
    scale: float = 1.0
    opacity: float = 1.0
    rotation: float = 0

    # Transitions
    transition_in: Optional[TransitionType] = None
    transition_in_duration: float = 0.3
    transition_out: Optional[TransitionType] = None
    transition_out_duration: float = 0.3

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Clip duration on timeline."""
        return self.end_time - self.start_time

    @property
    def source_duration(self) -> float:
        """Source clip duration."""
        if self.source_out is None:
            return self.duration
        return self.source_out - self.source_in

    def to_dict(self) -> Dict[str, Any]:
        """Export clip as dictionary."""
        return {
            "id": self.id,
            "track": self.track.value,
            "source": str(self.source_path) if self.source_path else None,
            "start": self.start_time,
            "end": self.end_time,
            "source_in": self.source_in,
            "source_out": self.source_out,
            "position": list(self.position),
            "scale": self.scale,
            "opacity": self.opacity,
            "rotation": self.rotation,
            "transition_in": self.transition_in.value if self.transition_in else None,
            "transition_in_duration": self.transition_in_duration,
            "transition_out": self.transition_out.value if self.transition_out else None,
            "transition_out_duration": self.transition_out_duration,
            "metadata": self.metadata,
        }


@dataclass
class TimelineTrack:
    """A track in the timeline."""

    name: str
    type: TrackType
    clips: List[TimelineClip] = field(default_factory=list)
    muted: bool = False
    locked: bool = False

    def add_clip(self, clip: TimelineClip):
        """Add a clip to the track."""
        self.clips.append(clip)
        # Sort clips by start time
        self.clips.sort(key=lambda c: c.start_time)

    def get_clip_at(self, time: float) -> Optional[TimelineClip]:
        """Get the clip at a specific time."""
        for clip in self.clips:
            if clip.start_time <= time < clip.end_time:
                return clip
        return None

    @property
    def duration(self) -> float:
        """Total track duration."""
        if not self.clips:
            return 0
        return max(c.end_time for c in self.clips)


@dataclass
class VideoTimeline:
    """Master timeline for video production."""

    id: str
    name: str
    duration: float
    width: int = 1920
    height: int = 1080
    fps: int = 30

    tracks: Dict[str, TimelineTrack] = field(default_factory=dict)

    # Output settings
    output_path: Optional[Path] = None
    output_format: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = "5M"
    audio_bitrate: str = "192k"

    def add_track(self, name: str, track_type: TrackType) -> TimelineTrack:
        """Add a new track to the timeline."""
        track = TimelineTrack(name=name, type=track_type)
        self.tracks[name] = track
        return track

    def get_track(self, name: str) -> Optional[TimelineTrack]:
        """Get a track by name."""
        return self.tracks.get(name)

    def get_tracks_by_type(self, track_type: TrackType) -> List[TimelineTrack]:
        """Get all tracks of a specific type."""
        return [t for t in self.tracks.values() if t.type == track_type]

    def add_clip(self, track_name: str, clip: TimelineClip) -> TimelineClip:
        """Add a clip to a specific track."""
        track = self.get_track(track_name)
        if track is None:
            raise ValueError(f"Track not found: {track_name}")
        track.add_clip(clip)
        return clip

    @property
    def calculated_duration(self) -> float:
        """Calculate duration from track contents."""
        if not self.tracks:
            return self.duration
        return max(t.duration for t in self.tracks.values())

    def to_dict(self) -> Dict[str, Any]:
        """Export timeline as dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "tracks": {
                name: {
                    "type": track.type.value,
                    "muted": track.muted,
                    "locked": track.locked,
                    "clips": [c.to_dict() for c in track.clips],
                }
                for name, track in self.tracks.items()
            },
            "output": {
                "path": str(self.output_path) if self.output_path else None,
                "format": self.output_format,
                "video_codec": self.video_codec,
                "audio_codec": self.audio_codec,
                "video_bitrate": self.video_bitrate,
                "audio_bitrate": self.audio_bitrate,
            },
        }

    def save(self, path: Path) -> Path:
        """Save timeline to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, sort_keys=False)
        return path

    @classmethod
    def load(cls, path: Path) -> "VideoTimeline":
        """Load timeline from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        timeline = cls(
            id=data["id"],
            name=data["name"],
            duration=data["duration"],
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            fps=data.get("fps", 30),
        )

        # Load tracks
        for name, track_data in data.get("tracks", {}).items():
            track = timeline.add_track(name, TrackType(track_data["type"]))
            track.muted = track_data.get("muted", False)
            track.locked = track_data.get("locked", False)

            for clip_data in track_data.get("clips", []):
                clip = TimelineClip(
                    id=clip_data["id"],
                    track=TrackType(clip_data["track"]),
                    source_path=Path(clip_data["source"]) if clip_data.get("source") else None,
                    start_time=clip_data["start"],
                    end_time=clip_data["end"],
                    source_in=clip_data.get("source_in", 0),
                    source_out=clip_data.get("source_out"),
                    position=tuple(clip_data.get("position", [0, 0])),
                    scale=clip_data.get("scale", 1.0),
                    opacity=clip_data.get("opacity", 1.0),
                    metadata=clip_data.get("metadata", {}),
                )
                track.add_clip(clip)

        return timeline

    def to_ffmpeg_script(self) -> str:
        """
        Generate FFmpeg filter_complex script.

        This creates a single FFmpeg command that:
        1. Loads all input files
        2. Applies transformations
        3. Composites layers
        4. Outputs final video
        """
        inputs = []
        input_index = 0
        input_map = {}

        # Collect all input files
        for track in self.tracks.values():
            for clip in track.clips:
                if clip.source_path and clip.source_path not in input_map:
                    input_map[clip.source_path] = input_index
                    inputs.append(f'-i "{clip.source_path}"')
                    input_index += 1

        # Build filter_complex
        filter_parts = []
        layer_refs = []

        # Process video track first (base layer)
        video_tracks = self.get_tracks_by_type(TrackType.VIDEO)
        for track in video_tracks:
            for clip in track.clips:
                if clip.source_path:
                    idx = input_map[clip.source_path]
                    # Trim and scale
                    ref = f"v{len(layer_refs)}"
                    filter_parts.append(
                        f"[{idx}:v]trim={clip.source_in}:{clip.source_out or clip.duration},"
                        f"setpts=PTS-STARTPTS,scale={self.width}:{self.height}[{ref}]"
                    )
                    layer_refs.append(ref)

        # Process graphics tracks (overlay layers)
        graphics_tracks = self.get_tracks_by_type(TrackType.GRAPHICS)
        for track in graphics_tracks:
            for clip in track.clips:
                if clip.source_path:
                    idx = input_map.get(clip.source_path)
                    if idx is not None:
                        ref = f"g{len(layer_refs)}"
                        x, y = clip.position
                        # Create graphics overlay with timing
                        filter_parts.append(f"[{idx}:v]setpts=PTS-STARTPTS[{ref}]")
                        layer_refs.append(ref)

        # Build overlay chain
        if len(layer_refs) > 1:
            base = layer_refs[0]
            for i, ref in enumerate(layer_refs[1:], 1):
                next_ref = f"comp{i}"
                filter_parts.append(
                    f"[{base}][{ref}]overlay=0:0:enable='between(t,0,{self.duration})'[{next_ref}]"
                )
                base = next_ref
            final_video = base
        elif layer_refs:
            final_video = layer_refs[0]
        else:
            final_video = "0:v"

        # Build command
        filter_complex = ";".join(filter_parts)

        command = (
            f"ffmpeg -y {' '.join(inputs)} "
            f'-filter_complex "{filter_complex}" '
            f'-map "[{final_video}]" -map 0:a? '
            f"-c:v {self.video_codec} -b:v {self.video_bitrate} "
            f"-c:a {self.audio_codec} -b:a {self.audio_bitrate} "
            f'"{self.output_path}"'
        )

        return command


class TimelineBuilder:
    """
    Builds timelines from video scripts.

    Converts VideoScript + TimingManifest into a VideoTimeline
    with proper clips and timing.
    """

    def from_script(
        self, script: Any, timing_manifest: Any, graphics_manifest: Optional[Any] = None
    ) -> VideoTimeline:
        """
        Build timeline from video script and timing manifest.

        Args:
            script: VideoScript object
            timing_manifest: TimingManifest with scene timing
            graphics_manifest: Optional GraphicsManifest with overlays

        Returns:
            VideoTimeline ready for rendering
        """
        # Create timeline
        timeline = VideoTimeline(
            id=script.id,
            name=script.title,
            duration=timing_manifest.total_duration,
        )

        # Add standard tracks
        video_track = timeline.add_track("V1-Demo", TrackType.VIDEO)
        graphics_track = timeline.add_track("G1-Graphics", TrackType.GRAPHICS)
        audio_track = timeline.add_track("A1-Voiceover", TrackType.AUDIO)
        caption_track = timeline.add_track("C1-Captions", TrackType.CAPTION)

        # Add voiceover audio
        audio_clip = TimelineClip(
            id="voiceover",
            track=TrackType.AUDIO,
            source_path=timing_manifest.audio_path,
            start_time=0,
            end_time=timing_manifest.total_duration,
        )
        audio_track.add_clip(audio_clip)

        # Process each scene
        for scene in script.scenes:
            scene_timing = timing_manifest.get_scene_timing(scene.id)

            # Add scene video clip
            # (In reality, this would be the screen recording for this scene)
            video_clip = TimelineClip(
                id=f"scene-{scene.id}",
                track=TrackType.VIDEO,
                source_path=script.get_video_path(),  # Full recording
                start_time=scene_timing.cumulative_start,
                end_time=scene_timing.cumulative_start + scene_timing.total_duration,
                source_in=scene_timing.cumulative_start,
                source_out=scene_timing.cumulative_start + scene_timing.total_duration,
                metadata={
                    "scene_id": scene.id,
                    "voiceover": scene.voiceover,
                },
            )
            video_track.add_clip(video_clip)

            # Add captions
            for caption in scene.captions:
                caption_clip = TimelineClip(
                    id=f"caption-{scene.id}-{caption.time}",
                    track=TrackType.CAPTION,
                    source_path=None,
                    start_time=scene_timing.cumulative_start + caption.time,
                    end_time=scene_timing.cumulative_start
                    + caption.time
                    + (caption.duration or 3.0),
                    metadata={
                        "text": caption.text,
                        "style": caption.style,
                    },
                )
                caption_track.add_clip(caption_clip)

        # Add motion graphics from manifest
        if graphics_manifest:
            for graphic in graphics_manifest.graphics:
                graphics_clip = TimelineClip(
                    id=f"graphic-{graphic.type.value}-{graphic.start_time}",
                    track=TrackType.GRAPHICS,
                    source_path=graphic.output_path,
                    start_time=graphic.start_time,
                    end_time=graphic.start_time + graphic.duration,
                    position=self._position_to_coords(graphic.position),
                    transition_in=TransitionType.FADE_IN,
                    transition_out=TransitionType.FADE_OUT,
                    metadata={
                        "type": graphic.type.value,
                        "params": graphic.params,
                    },
                )
                graphics_track.add_clip(graphics_clip)

        # Set output path
        timeline.output_path = script.get_video_path()

        return timeline

    def _position_to_coords(self, position: str) -> Tuple[int, int]:
        """Convert position name to pixel coordinates."""
        positions = {
            "center": (960, 540),
            "top": (960, 100),
            "bottom": (960, 980),
            "top-left": (200, 100),
            "top-right": (1720, 100),
            "bottom-left": (200, 980),
            "bottom-right": (1720, 980),
        }
        return positions.get(position, (960, 540))


def print_timeline_summary(timeline: VideoTimeline):
    """Print a human-readable timeline summary."""
    print(f"\n{'=' * 60}")
    print(f"TIMELINE: {timeline.name}")
    print(
        f"Duration: {timeline.duration:.1f}s | {timeline.width}x{timeline.height} @ {timeline.fps}fps"
    )
    print(f"{'=' * 60}")

    for track_name, track in timeline.tracks.items():
        print(f"\n[{track.type.value.upper()}] {track_name}")
        print("-" * 40)

        for clip in track.clips:
            duration = clip.end_time - clip.start_time
            print(
                f"  {clip.start_time:6.1f}s - {clip.end_time:6.1f}s ({duration:.1f}s) | {clip.id}"
            )
            if clip.metadata.get("text"):
                print(f'           └─ "{clip.metadata["text"][:40]}..."')

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    # Demo: Create a sample timeline
    timeline = VideoTimeline(
        id="demo-timeline",
        name="ROP Demo Video",
        duration=60.0,
    )

    # Add tracks
    video_track = timeline.add_track("V1", TrackType.VIDEO)
    graphics_track = timeline.add_track("G1", TrackType.GRAPHICS)
    audio_track = timeline.add_track("A1", TrackType.AUDIO)

    # Add demo clips
    video_track.add_clip(
        TimelineClip(
            id="intro",
            track=TrackType.VIDEO,
            source_path=Path("demo.mp4"),
            start_time=0,
            end_time=60,
        )
    )

    graphics_track.add_clip(
        TimelineClip(
            id="stat-30percent",
            track=TrackType.GRAPHICS,
            source_path=Path("stat_counter.webm"),
            start_time=10,
            end_time=14,
            position=(1720, 980),
        )
    )

    audio_track.add_clip(
        TimelineClip(
            id="voiceover",
            track=TrackType.AUDIO,
            source_path=Path("voiceover.mp3"),
            start_time=0,
            end_time=60,
        )
    )

    # Print summary
    print_timeline_summary(timeline)

    # Save timeline
    save_path = Path("/tmp/demo_timeline.yaml")
    timeline.save(save_path)
    print(f"Saved to: {save_path}")

    # Generate FFmpeg command
    print("\nFFmpeg command:")
    print(timeline.to_ffmpeg_script())
