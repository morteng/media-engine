"""
Tests for media_engine.video module.
"""

import pytest
from pathlib import Path

from media_engine.video.timeline import (
    VideoTimeline,
    TimelineClip,
    TimelineTrack,
    TrackType,
    TransitionType,
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
        track.add_clip(TimelineClip(
            id="clip-1",
            track=TrackType.VIDEO,
            source_path=Path("a.mp4"),
            start_time=0.0,
            end_time=5.0,
        ))
        track.add_clip(TimelineClip(
            id="clip-2",
            track=TrackType.VIDEO,
            source_path=Path("b.mp4"),
            start_time=5.0,
            end_time=12.0,
        ))
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
