"""Tests for video module."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for video testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "scripts").mkdir(parents=True)
    (content_dir / "en" / "slides").mkdir(parents=True)
    (tmp_path / "assets").mkdir()
    (tmp_path / "dist").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Video Test Project",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestVideoTimeline:
    """Tests for VideoTimeline class."""

    def test_video_timeline_import(self):
        """Test VideoTimeline can be imported."""
        from media_engine.video import VideoTimeline

        assert VideoTimeline is not None

    def test_video_timeline_creation(self):
        """Test VideoTimeline creation."""
        from media_engine.video import VideoTimeline

        timeline = VideoTimeline(id="timeline-1", name="Test Timeline", duration=60.0)
        assert timeline is not None
        assert timeline.id == "timeline-1"
        assert timeline.duration == 60.0


class TestTimelineClip:
    """Tests for TimelineClip class."""

    def test_timeline_clip_import(self):
        """Test TimelineClip can be imported."""
        from media_engine.video import TimelineClip

        assert TimelineClip is not None


class TestVideoBuilder:
    """Tests for VideoBuilder."""

    def test_video_builder_import(self):
        """Test VideoBuilder can be imported."""
        from media_engine.video import VideoBuilder

        assert VideoBuilder is not None


class TestDemoRegistry:
    """Tests for DemoRegistry class."""

    def test_demo_registry_import(self):
        """Test DemoRegistry can be imported."""
        from media_engine.video import DemoRegistry

        assert DemoRegistry is not None

    def test_demo_registry_creation(self, project):
        """Test DemoRegistry creation."""
        from media_engine.video import DemoRegistry

        registry = DemoRegistry(project)
        assert registry is not None

    def test_list_demos(self, project):
        """Test listing demos."""
        from media_engine.video import DemoRegistry

        registry = DemoRegistry(project)
        demos = registry.list_demos()

        assert isinstance(demos, list)


class TestVideoQuality:
    """Tests for video quality classes."""

    def test_video_quality_import(self):
        """Test VideoQuality can be imported."""
        from media_engine.video import VideoQuality

        assert VideoQuality is not None

    def test_quality_preset_import(self):
        """Test QualityPreset can be imported."""
        from media_engine.video import QualityPreset

        assert QualityPreset is not None

    def test_get_preset(self):
        """Test get_preset function."""
        from media_engine.video import (
            PREVIEW_PRESET,
            PRODUCTION_PRESET,
            VideoQuality,
            get_preset,
        )

        # PREVIEW_PRESET and PRODUCTION_PRESET are constants
        assert PREVIEW_PRESET is not None
        assert PRODUCTION_PRESET is not None

        # get_preset should work with VideoQuality enum values
        preview = get_preset(VideoQuality.PREVIEW)
        assert preview == PREVIEW_PRESET

        production = get_preset(VideoQuality.PRODUCTION)
        assert production == PRODUCTION_PRESET


class TestVoiceover:
    """Tests for voiceover functionality."""

    def test_voiceover_import(self):
        """Test voiceover imports."""
        from media_engine.video import AudioSegment, VoiceoverResult

        assert AudioSegment is not None
        assert VoiceoverResult is not None


class TestTrackType:
    """Tests for TrackType enum."""

    def test_track_type_import(self):
        """Test TrackType can be imported."""
        from media_engine.video import TrackType

        assert TrackType is not None


class TestTransitionType:
    """Tests for TransitionType enum."""

    def test_transition_type_import(self):
        """Test TransitionType can be imported."""
        from media_engine.video import TransitionType

        assert TransitionType is not None


class TestVideoModule:
    """General tests for video module."""

    def test_video_module_exports(self):
        """Test video module exports."""
        from media_engine import video

        assert hasattr(video, "VideoTimeline")
        assert hasattr(video, "VideoBuilder")
        assert hasattr(video, "DemoRegistry")
        assert hasattr(video, "VideoQuality")
        assert hasattr(video, "QualityPreset")
        assert hasattr(video, "TimelineClip")
        assert hasattr(video, "TimelineTrack")
        assert hasattr(video, "TrackType")
        assert hasattr(video, "TransitionType")
