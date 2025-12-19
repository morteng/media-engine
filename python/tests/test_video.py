"""
Tests for media_engine.video module.
"""

from pathlib import Path

from media_engine.video.timeline import (
    TimelineClip,
    TimelineTrack,
    TrackType,
    TransitionType,
    VideoTimeline,
)


class TestVideoTimeline:
    """Tests for VideoTimeline class."""

    def test_create_timeline(self):
        """Test creating a new timeline."""
        timeline = VideoTimeline(
            id="test-timeline",
            name="Test Timeline",
            duration=60.0,
            fps=30,
        )
        assert timeline.fps == 30
        assert timeline.duration == 60.0
        assert timeline.width == 1920
        assert timeline.height == 1080

    def test_add_track(self):
        """Test adding tracks to timeline."""
        timeline = VideoTimeline(
            id="test",
            name="Test",
            duration=30.0,
        )
        track = timeline.add_track("video", TrackType.VIDEO)
        assert track.name == "video"
        assert track.type == TrackType.VIDEO
        assert "video" in timeline.tracks

    def test_get_track(self):
        """Test getting track by name."""
        timeline = VideoTimeline(
            id="test",
            name="Test",
            duration=30.0,
        )
        timeline.add_track("main", TrackType.VIDEO)
        track = timeline.get_track("main")
        assert track is not None
        assert track.name == "main"

    def test_get_tracks_by_type(self):
        """Test getting tracks by type."""
        timeline = VideoTimeline(
            id="test",
            name="Test",
            duration=30.0,
        )
        timeline.add_track("video1", TrackType.VIDEO)
        timeline.add_track("audio1", TrackType.AUDIO)
        timeline.add_track("video2", TrackType.VIDEO)

        video_tracks = timeline.get_tracks_by_type(TrackType.VIDEO)
        assert len(video_tracks) == 2


class TestTimelineClip:
    """Tests for TimelineClip class."""

    def test_clip_properties(self):
        """Test clip property access."""
        clip = TimelineClip(
            id="clip-1",
            track=TrackType.VIDEO,
            source_path=Path("test.mp4"),
            start_time=1.0,
            end_time=5.0,
        )
        assert clip.id == "clip-1"
        assert clip.source_path == Path("test.mp4")
        assert clip.start_time == 1.0
        assert clip.end_time == 5.0
        assert clip.duration == 4.0

    def test_clip_with_transition(self):
        """Test clip with transition."""
        clip = TimelineClip(
            id="clip-1",
            track=TrackType.VIDEO,
            source_path=Path("test.mp4"),
            start_time=0.0,
            end_time=5.0,
            transition_in=TransitionType.FADE_IN,
            transition_in_duration=0.5,
        )
        assert clip.transition_in == TransitionType.FADE_IN
        assert clip.transition_in_duration == 0.5

    def test_clip_transforms(self):
        """Test clip transform properties."""
        clip = TimelineClip(
            id="clip-1",
            track=TrackType.GRAPHICS,
            source_path=None,
            start_time=0.0,
            end_time=3.0,
            position=(100, 50),
            scale=1.5,
            opacity=0.8,
        )
        assert clip.position == (100, 50)
        assert clip.scale == 1.5
        assert clip.opacity == 0.8

    def test_clip_to_dict(self):
        """Test clip serialization."""
        clip = TimelineClip(
            id="clip-1",
            track=TrackType.VIDEO,
            source_path=Path("test.mp4"),
            start_time=0.0,
            end_time=5.0,
        )
        data = clip.to_dict()
        assert data["id"] == "clip-1"
        assert data["track"] == "video"
        assert data["start"] == 0.0
        assert data["end"] == 5.0


class TestTimelineTrack:
    """Tests for TimelineTrack class."""

    def test_create_track(self):
        """Test creating a track."""
        track = TimelineTrack(name="main", type=TrackType.VIDEO)
        assert track.name == "main"
        assert track.type == TrackType.VIDEO
        assert len(track.clips) == 0

    def test_add_clip_to_track(self):
        """Test adding clips to track."""
        track = TimelineTrack(name="main", type=TrackType.VIDEO)
        clip = TimelineClip(
            id="clip-1",
            track=TrackType.VIDEO,
            source_path=Path("test.mp4"),
            start_time=0.0,
            end_time=5.0,
        )
        track.add_clip(clip)
        assert len(track.clips) == 1

    def test_track_duration(self):
        """Test track duration calculation."""
        track = TimelineTrack(name="main", type=TrackType.VIDEO)
        track.add_clip(
            TimelineClip(
                id="clip-1",
                track=TrackType.VIDEO,
                source_path=Path("a.mp4"),
                start_time=0.0,
                end_time=5.0,
            )
        )
        track.add_clip(
            TimelineClip(
                id="clip-2",
                track=TrackType.VIDEO,
                source_path=Path("b.mp4"),
                start_time=5.0,
                end_time=12.0,
            )
        )
        assert track.duration == 12.0

    def test_get_clip_at_time(self):
        """Test getting clip at specific time."""
        track = TimelineTrack(name="main", type=TrackType.VIDEO)
        clip1 = TimelineClip(
            id="clip-1",
            track=TrackType.VIDEO,
            source_path=Path("a.mp4"),
            start_time=0.0,
            end_time=5.0,
        )
        clip2 = TimelineClip(
            id="clip-2",
            track=TrackType.VIDEO,
            source_path=Path("b.mp4"),
            start_time=5.0,
            end_time=10.0,
        )
        track.add_clip(clip1)
        track.add_clip(clip2)

        found = track.get_clip_at(2.5)
        assert found is not None
        assert found.id == "clip-1"

        found = track.get_clip_at(7.0)
        assert found is not None
        assert found.id == "clip-2"


class TestTransitionType:
    """Tests for TransitionType enum."""

    def test_transition_values(self):
        """Test transition type values."""
        assert TransitionType.CUT.value == "cut"
        assert TransitionType.FADE_IN.value == "fade_in"
        assert TransitionType.CROSSFADE.value == "crossfade"
        assert TransitionType.COPPER_SWEEP.value == "copper_sweep"


# Video Builder Tests
from media_engine.video.builder import (
    VideoBuilder,
    VideoBuildResult,
    VideoConfig,
    VideoScene,
    VideoScript,
)
from media_engine.video.quality import (
    VideoQuality,
    QualityPreset,
    get_preset,
    is_preview_video,
    PREVIEW_PRESET,
    PRODUCTION_PRESET,
)


class TestVideoConfig:
    """Tests for VideoConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values (production quality)."""
        config = VideoConfig()
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 60  # Production default
        assert config.format == "mp4"
        assert config.codec == "h264"
        assert config.crf == 18  # Production default

    def test_custom_values(self):
        """Test custom configuration values."""
        config = VideoConfig(
            width=1280,
            height=720,
            fps=60,
            format="webm",
            codec="vp9",
            crf=18,
        )
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 60
        assert config.format == "webm"

    def test_from_quality_preview(self):
        """Test creating config from preview quality preset."""
        config = VideoConfig.from_quality(VideoQuality.PREVIEW)
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 24
        assert config.crf == 28
        assert config.quality == VideoQuality.PREVIEW
        assert config.is_releasable is False

    def test_from_quality_production(self):
        """Test creating config from production quality preset."""
        config = VideoConfig.from_quality(VideoQuality.PRODUCTION)
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 60
        assert config.crf == 18
        assert config.quality == VideoQuality.PRODUCTION
        assert config.is_releasable is True


class TestVideoQuality:
    """Tests for VideoQuality enum and presets."""

    def test_quality_enum_values(self):
        """Test VideoQuality enum has correct values."""
        assert VideoQuality.PREVIEW.value == "preview"
        assert VideoQuality.PRODUCTION.value == "production"

    def test_preview_preset_values(self):
        """Test preview preset has fast iteration values."""
        assert PREVIEW_PRESET.width == 1280
        assert PREVIEW_PRESET.height == 720
        assert PREVIEW_PRESET.fps == 24
        assert PREVIEW_PRESET.crf == 28
        assert PREVIEW_PRESET.is_releasable is False

    def test_production_preset_values(self):
        """Test production preset has full quality values."""
        assert PRODUCTION_PRESET.width == 1920
        assert PRODUCTION_PRESET.height == 1080
        assert PRODUCTION_PRESET.fps == 60
        assert PRODUCTION_PRESET.crf == 18
        assert PRODUCTION_PRESET.is_releasable is True

    def test_get_preset_preview(self):
        """Test getting preview preset."""
        preset = get_preset(VideoQuality.PREVIEW)
        assert preset == PREVIEW_PRESET

    def test_get_preset_production(self):
        """Test getting production preset."""
        preset = get_preset(VideoQuality.PRODUCTION)
        assert preset == PRODUCTION_PRESET

    def test_is_preview_video_true(self):
        """Test detecting preview videos by filename."""
        assert is_preview_video("demo.preview.mp4") is True
        assert is_preview_video("my-video.preview.mp4") is True
        assert is_preview_video("test.preview.webm") is True

    def test_is_preview_video_false(self):
        """Test production videos are not detected as preview."""
        assert is_preview_video("demo.mp4") is False
        assert is_preview_video("my-video.mp4") is False
        assert is_preview_video("preview-demo.mp4") is False  # 'preview' in name but not .preview.


class TestVideoScene:
    """Tests for VideoScene dataclass."""

    def test_scene_creation(self):
        """Test creating a scene."""
        scene = VideoScene(
            id="intro",
            type="intro",
            title="Introduction",
            text="Welcome to the demo.",
        )
        assert scene.id == "intro"
        assert scene.type == "intro"
        assert scene.title == "Introduction"
        assert scene.text == "Welcome to the demo."

    def test_scene_defaults(self):
        """Test scene default values."""
        scene = VideoScene(id="test", type="content")
        assert scene.title is None
        assert scene.text is None
        assert scene.duration is None
        assert scene.visual == {}
        assert scene.audio_start is None


class TestVideoScript:
    """Tests for VideoScript class."""

    def test_from_yaml(self, temp_dir):
        """Test loading script from YAML."""
        yaml_content = """
metadata:
  title: "Test Video"
  language: "en"

scenes:
  - id: intro
    type: intro
    title: "Intro"
    content:
      text: "Welcome to the test."
  - id: main
    type: content
    content: "Main content here."
"""
        yaml_path = temp_dir / "script.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert script.title == "Test Video"
        assert script.language == "en"
        assert len(script.scenes) == 2
        assert script.scenes[0].id == "intro"
        assert script.scenes[0].text == "Welcome to the test."
        assert script.scenes[1].text == "Main content here."

    def test_script_defaults(self, temp_dir):
        """Test script with minimal YAML."""
        yaml_content = """
scenes:
  - id: scene1
    type: content
"""
        yaml_path = temp_dir / "minimal.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert script.name == "minimal"
        assert script.language == "en"
        assert len(script.scenes) == 1


class TestVideoBuilder:
    """Tests for VideoBuilder class."""

    def test_create_builder(self):
        """Test creating a builder with production defaults."""
        builder = VideoBuilder()
        assert builder.config.width == 1920
        assert builder.config.fps == 60  # Production default

    def test_create_with_config(self):
        """Test creating builder with custom config."""
        config = VideoConfig(width=1280, height=720, fps=60)
        builder = VideoBuilder(config=config)
        assert builder.config.width == 1280
        assert builder.config.fps == 60


class TestVideoBuildResult:
    """Tests for VideoBuildResult dataclass."""

    def test_default_values(self):
        """Test default result values."""
        result = VideoBuildResult()
        assert result.video_path is None
        assert result.audio_path is None
        assert result.captions_path is None
        assert result.duration == 0.0
        assert result.success is False
        assert result.error is None

    def test_successful_result(self, temp_dir):
        """Test successful result values."""
        result = VideoBuildResult(
            video_path=temp_dir / "video.mp4",
            audio_path=temp_dir / "audio.mp3",
            captions_path=temp_dir / "captions.vtt",
            duration=120.5,
            success=True,
        )
        assert result.success is True
        assert result.duration == 120.5
