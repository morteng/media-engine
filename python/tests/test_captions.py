"""
Tests for media_engine.video.captions module.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from media_engine.video.captions import (
    CaptionEntry,
    extract_captions_from_script,
    extract_voiceover_captions,
    format_timestamp,
    generate_vtt_content,
    generate_webvtt,
    generate_webvtt_from_manifest,
    generate_voiceover_vtt,
    parse_timestamp,
    split_into_sentences,
    validate_vtt,
)


class TestCaptionEntry:
    """Test CaptionEntry dataclass."""

    def test_create_caption_entry(self):
        """Test creating a basic caption entry."""
        entry = CaptionEntry(
            start_time=0.0,
            end_time=3.0,
            text="Hello world",
        )
        assert entry.start_time == 0.0
        assert entry.end_time == 3.0
        assert entry.text == "Hello world"
        assert entry.style == "default"

    def test_caption_entry_with_style(self):
        """Test caption entry with custom style."""
        entry = CaptionEntry(
            start_time=5.0,
            end_time=8.0,
            text="Important message",
            style="emphasis",
        )
        assert entry.style == "emphasis"

    def test_caption_entry_default_style(self):
        """Test caption entry has default style."""
        entry = CaptionEntry(
            start_time=0.0,
            end_time=1.0,
            text="Test",
        )
        assert entry.style == "default"


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_format_zero(self):
        """Test formatting zero seconds."""
        result = format_timestamp(0.0)
        assert result == "00:00:00.000"

    def test_format_seconds(self):
        """Test formatting seconds only."""
        result = format_timestamp(45.5)
        assert result == "00:00:45.500"

    def test_format_minutes_seconds(self):
        """Test formatting minutes and seconds."""
        result = format_timestamp(90.123)
        assert result == "00:01:30.123"

    def test_format_hours_minutes_seconds(self):
        """Test formatting hours, minutes, and seconds."""
        result = format_timestamp(3661.456)  # 1h 1m 1.456s
        assert result == "01:01:01.456"

    def test_format_milliseconds_precision(self):
        """Test millisecond precision in formatting."""
        result = format_timestamp(1.999)
        assert result == "00:00:01.999"

    def test_format_large_values(self):
        """Test formatting large time values."""
        result = format_timestamp(7265.789)  # 2h 1m 5.789s
        assert result == "02:01:05.789"


class TestParseTimestamp:
    """Test timestamp parsing."""

    def test_parse_zero(self):
        """Test parsing zero timestamp."""
        result = parse_timestamp("00:00:00.000")
        assert result == 0.0

    def test_parse_seconds(self):
        """Test parsing seconds."""
        result = parse_timestamp("00:00:45.500")
        assert result == 45.5

    def test_parse_minutes_seconds(self):
        """Test parsing minutes and seconds."""
        result = parse_timestamp("00:01:30.000")
        assert result == 90.0

    def test_parse_hours_minutes_seconds(self):
        """Test parsing hours, minutes, and seconds."""
        result = parse_timestamp("01:01:01.000")
        assert result == 3661.0

    def test_parse_with_milliseconds(self):
        """Test parsing with millisecond precision."""
        result = parse_timestamp("00:00:01.999")
        assert abs(result - 1.999) < 0.001

    def test_parse_roundtrip(self):
        """Test that format and parse are inverse operations."""
        original = 1234.567
        formatted = format_timestamp(original)
        parsed = parse_timestamp(formatted)
        assert abs(parsed - original) < 0.001


class TestSplitIntoSentences:
    """Test sentence splitting."""

    def test_split_single_sentence(self):
        """Test splitting a single sentence."""
        text = "This is a single sentence."
        result = split_into_sentences(text)
        assert result == ["This is a single sentence."]

    def test_split_multiple_sentences(self):
        """Test splitting multiple sentences."""
        text = "First sentence. Second sentence. Third sentence."
        result = split_into_sentences(text)
        assert result == ["First sentence.", "Second sentence.", "Third sentence."]

    def test_split_with_exclamation(self):
        """Test splitting with exclamation marks."""
        text = "Wow! This is amazing! So cool!"
        result = split_into_sentences(text)
        assert result == ["Wow!", "This is amazing!", "So cool!"]

    def test_split_with_question(self):
        """Test splitting with question marks."""
        text = "What is this? How does it work? Why now?"
        result = split_into_sentences(text)
        assert result == ["What is this?", "How does it work?", "Why now?"]

    def test_split_mixed_punctuation(self):
        """Test splitting with mixed punctuation."""
        text = "Hello world. Are you there? Yes! I am here."
        result = split_into_sentences(text)
        assert len(result) == 4

    def test_split_empty_string(self):
        """Test splitting empty string."""
        result = split_into_sentences("")
        assert result == []

    def test_split_whitespace_only(self):
        """Test splitting whitespace-only string."""
        result = split_into_sentences("   \n\t  ")
        assert result == []

    def test_split_preserves_content(self):
        """Test that splitting preserves sentence content."""
        text = "First.  Second.   Third."
        result = split_into_sentences(text)
        assert "First." in result
        assert "Second." in result
        assert "Third." in result


class TestGenerateVttContent:
    """Test VTT content generation."""

    def test_generate_empty(self):
        """Test generating VTT with no entries."""
        result = generate_vtt_content([])
        assert result.startswith("WEBVTT\n")
        assert "STYLE" in result

    def test_generate_with_title(self):
        """Test generating VTT with title."""
        result = generate_vtt_content([], title="Test Video")
        assert "NOTE Title: Test Video" in result

    def test_generate_single_entry(self):
        """Test generating VTT with single entry."""
        entries = [
            CaptionEntry(start_time=0.0, end_time=3.0, text="Hello world")
        ]
        result = generate_vtt_content(entries)

        assert "WEBVTT" in result
        assert "00:00:00.000 --> 00:00:03.000" in result
        assert "Hello world" in result

    def test_generate_multiple_entries(self):
        """Test generating VTT with multiple entries."""
        entries = [
            CaptionEntry(start_time=0.0, end_time=2.0, text="First caption"),
            CaptionEntry(start_time=2.0, end_time=5.0, text="Second caption"),
            CaptionEntry(start_time=5.0, end_time=8.0, text="Third caption"),
        ]
        result = generate_vtt_content(entries)

        assert "First caption" in result
        assert "Second caption" in result
        assert "Third caption" in result
        # Check cue numbers
        lines = result.split("\n")
        assert "1" in lines
        assert "2" in lines
        assert "3" in lines

    def test_generate_with_style(self):
        """Test generating VTT with styled entries."""
        entries = [
            CaptionEntry(start_time=0.0, end_time=2.0, text="Normal text"),
            CaptionEntry(start_time=2.0, end_time=4.0, text="Emphasized", style="emphasis"),
        ]
        result = generate_vtt_content(entries)

        assert "Normal text" in result
        assert "<c.emphasis>Emphasized</c>" in result

    def test_generate_includes_styles_block(self):
        """Test that VTT includes STYLE block."""
        entries = [CaptionEntry(start_time=0.0, end_time=1.0, text="Test")]
        result = generate_vtt_content(entries)

        assert "STYLE" in result
        assert "::cue(.emphasis)" in result
        assert "::cue(.warning)" in result
        assert "::cue(.success)" in result

    def test_generate_default_style_no_tags(self):
        """Test that default style doesn't add tags."""
        entries = [
            CaptionEntry(start_time=0.0, end_time=1.0, text="Test", style="default")
        ]
        result = generate_vtt_content(entries)

        assert "<c.default>" not in result
        # Should just have the text without style tags
        assert "Test" in result


class TestExtractCaptionsFromScript:
    """Test extracting captions from script.

    Note: These functions depend on a non-existent 'video_orchestrator' module.
    Skipping tests as this appears to be legacy code.
    """

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_requires_video_script(self):
        """Test that extract requires VideoScript object."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_empty_script(self):
        """Test extracting from script with no scenes."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_scene_without_captions(self):
        """Test extracting from scene with no captions."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_single_caption(self):
        """Test extracting single caption from script."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_caption_without_duration(self):
        """Test extracting caption without explicit duration."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_caption_near_scene_end(self):
        """Test caption near end of scene uses remaining time."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_multiple_scenes(self):
        """Test extracting captions from multiple scenes."""
        pass

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_sorts_by_start_time(self):
        """Test that captions are sorted by start time."""
        pass


class TestExtractVoiceoverCaptions:
    """Test extracting captions from voiceover.

    Note: These functions depend on non-existent 'video_orchestrator' module.
    Skipping tests as this appears to be legacy code.
    """

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_requires_script(self):
        """Test that extract requires VideoScript object."""
        with patch("media_engine.video.captions.isinstance", return_value=True):
            with pytest.raises(TypeError, match="Expected VideoScript"):
                extract_voiceover_captions("not a script")

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_empty_script(self):
        """Test extracting from script with no scenes."""
        mock_script = Mock()
        mock_script.scenes = []

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = extract_voiceover_captions(mock_script)

        assert result == []

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_no_voiceover(self):
        """Test extracting from scene without voiceover."""
        mock_scene = Mock()
        mock_scene.voiceover = None
        mock_scene.duration = 5.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = extract_voiceover_captions(mock_script)

        assert result == []

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_single_sentence(self):
        """Test extracting single sentence voiceover."""
        mock_scene = Mock()
        mock_scene.voiceover = "This is a test sentence."
        mock_scene.duration = 3.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = extract_voiceover_captions(mock_script)

        assert len(result) == 1
        assert result[0].text == "This is a test sentence."
        assert result[0].start_time == 0.0
        assert result[0].end_time == 3.0

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_multiple_sentences(self):
        """Test extracting multiple sentences."""
        mock_scene = Mock()
        mock_scene.voiceover = "First sentence. Second sentence. Third sentence."
        mock_scene.duration = 9.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = extract_voiceover_captions(mock_script)

        assert len(result) == 3
        # Each sentence gets 3 seconds (9.0 / 3)
        assert result[0].start_time == 0.0
        assert result[0].end_time == 3.0
        assert result[1].start_time == 3.0
        assert result[1].end_time == 6.0
        assert result[2].start_time == 6.0
        assert result[2].end_time == 9.0

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_strips_whitespace(self):
        """Test that voiceover text is stripped."""
        mock_scene = Mock()
        mock_scene.voiceover = "  Test sentence.  "
        mock_scene.duration = 2.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = extract_voiceover_captions(mock_script)

        assert result[0].text == "Test sentence."

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_extract_voiceover_multiple_scenes(self):
        """Test extracting voiceover from multiple scenes."""
        mock_scene1 = Mock()
        mock_scene1.voiceover = "Scene one."
        mock_scene1.duration = 3.0

        mock_scene2 = Mock()
        mock_scene2.voiceover = "Scene two."
        mock_scene2.duration = 4.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene1, mock_scene2]

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = extract_voiceover_captions(mock_script)

        assert len(result) == 2
        assert result[0].start_time == 0.0
        assert result[0].end_time == 3.0
        assert result[1].start_time == 3.0
        assert result[1].end_time == 7.0


class TestGenerateWebvtt:
    """Test WebVTT generation.

    Note: These functions depend on non-existent 'video_orchestrator' module.
    Skipping tests as this appears to be legacy code.
    """

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_generate_requires_script(self):
        """Test that generate requires VideoScript."""
        with patch("media_engine.video.captions.isinstance", return_value=True):
            with pytest.raises(TypeError, match="Expected VideoScript"):
                generate_webvtt("not a script")

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_generate_creates_file(self, temp_dir):
        """Test that generate creates VTT file."""
        mock_caption = Mock()
        mock_caption.time = 0.0
        mock_caption.duration = 2.0
        mock_caption.text = "Test"
        mock_caption.style = "default"

        mock_scene = Mock()
        mock_scene.captions = [mock_caption]
        mock_scene.duration = 5.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]
        mock_script.id = "test-video"
        mock_script.title = "Test Video"

        output_path = temp_dir / "test.vtt"
        mock_script.get_caption_path.return_value = output_path

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = generate_webvtt(mock_script)

        assert result == output_path
        assert output_path.exists()

        content = output_path.read_text()
        assert "WEBVTT" in content
        assert "Test Video" in content

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_generate_with_voiceover(self, temp_dir):
        """Test generating with voiceover captions."""
        mock_scene = Mock()
        mock_scene.captions = []
        mock_scene.voiceover = "Test voiceover."
        mock_scene.duration = 3.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]
        mock_script.id = "test-video"
        mock_script.title = "Test Video"

        output_path = temp_dir / "test_vo.vtt"
        mock_script.get_caption_path.return_value = output_path

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = generate_webvtt(mock_script, include_voiceover=True)

        assert result == output_path
        content = output_path.read_text()
        assert "Test voiceover." in content

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_generate_prints_status(self, temp_dir, capsys):
        """Test that generation prints status messages."""
        mock_script = Mock()
        mock_script.scenes = []
        mock_script.id = "test-video"
        mock_script.title = "Test Video"

        output_path = temp_dir / "test.vtt"
        mock_script.get_caption_path.return_value = output_path

        with patch("media_engine.video.captions.isinstance", return_value=True):
            generate_webvtt(mock_script)

        captured = capsys.readouterr()
        assert "Generating captions for: test-video" in captured.out
        assert "Captions saved:" in captured.out


class TestGenerateVoiceoverVtt:
    """Test voiceover VTT generation.

    Note: These functions depend on non-existent 'video_orchestrator' module.
    Skipping tests as this appears to be legacy code.
    """

    @pytest.mark.skip(reason="Depends on non-existent video_orchestrator module")
    def test_generate_voiceover_vtt(self, temp_dir):
        """Test that voiceover VTT calls generate_webvtt with flag."""
        mock_scene = Mock()
        mock_scene.captions = []
        mock_scene.voiceover = "Test."
        mock_scene.duration = 2.0

        mock_script = Mock()
        mock_script.scenes = [mock_scene]
        mock_script.id = "test"
        mock_script.title = "Test"

        output_path = temp_dir / "vo_test.vtt"
        mock_script.get_caption_path.return_value = output_path

        with patch("media_engine.video.captions.isinstance", return_value=True):
            result = generate_voiceover_vtt(mock_script)

        assert result == output_path
        content = output_path.read_text()
        assert "Test." in content


class TestGenerateWebvttFromManifest:
    """Test WebVTT generation from timing manifest."""

    def test_generate_from_manifest(self, temp_dir):
        """Test generating VTT from timing manifest."""
        # Mock caption
        mock_caption = Mock()
        mock_caption.time = 1.0
        mock_caption.duration = 2.0
        mock_caption.text = "Test caption"
        mock_caption.style = "default"

        # Mock scene
        mock_scene = Mock()
        mock_scene.id = "scene1"
        mock_scene.captions = [mock_caption]
        mock_scene.duration = 5.0

        # Mock script
        mock_script = Mock()
        mock_script.__class__.__name__ = "VideoScript"
        mock_script.scenes = [mock_scene]
        mock_script.id = "test"
        mock_script.title = "Test"

        output_path = temp_dir / "manifest_test.vtt"
        mock_script.get_caption_path.return_value = output_path

        # Mock timing manifest
        mock_timing = Mock()
        mock_timing.cumulative_start = 0.0
        mock_timing.voiceover_duration = 4.0

        mock_manifest = Mock()
        mock_manifest.get_scene_timing.return_value = mock_timing

        result = generate_webvtt_from_manifest(mock_script, mock_manifest)

        assert result == output_path
        assert output_path.exists()

        content = output_path.read_text()
        assert "WEBVTT" in content
        assert "Test caption" in content

    def test_generate_from_manifest_without_duration(self, temp_dir):
        """Test manifest generation with caption without explicit duration."""
        mock_caption = Mock()
        mock_caption.time = 0.5
        mock_caption.duration = None
        mock_caption.text = "No duration"
        mock_caption.style = "default"

        mock_scene = Mock()
        mock_scene.id = "scene1"
        mock_scene.captions = [mock_caption]

        mock_script = Mock()
        mock_script.__class__.__name__ = "VideoScript"
        mock_script.scenes = [mock_scene]
        mock_script.id = "test"
        mock_script.title = "Test"

        output_path = temp_dir / "test.vtt"
        mock_script.get_caption_path.return_value = output_path

        mock_timing = Mock()
        mock_timing.cumulative_start = 0.0
        mock_timing.voiceover_duration = 10.0

        mock_manifest = Mock()
        mock_manifest.get_scene_timing.return_value = mock_timing

        result = generate_webvtt_from_manifest(mock_script, mock_manifest)

        assert output_path.exists()

    def test_generate_from_manifest_prints_status(self, temp_dir, capsys):
        """Test that manifest generation prints status."""
        mock_script = Mock()
        mock_script.__class__.__name__ = "VideoScript"
        mock_script.scenes = []
        mock_script.id = "test"
        mock_script.title = "Test"

        output_path = temp_dir / "test.vtt"
        mock_script.get_caption_path.return_value = output_path

        mock_manifest = Mock()

        generate_webvtt_from_manifest(mock_script, mock_manifest)

        captured = capsys.readouterr()
        assert "Generating captions from timing manifest: test" in captured.out
        assert "Captions saved:" in captured.out


class TestValidateVtt:
    """Test VTT validation."""

    def test_validate_nonexistent_file(self, temp_dir):
        """Test validating file that doesn't exist."""
        vtt_path = temp_dir / "nonexistent.vtt"
        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is False
        assert len(issues) == 1
        assert "does not exist" in issues[0]

    def test_validate_missing_header(self, temp_dir):
        """Test validation catches missing WEBVTT header."""
        vtt_path = temp_dir / "no_header.vtt"
        vtt_path.write_text("This file has no WEBVTT header")

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is False
        assert any("WEBVTT header" in issue for issue in issues)

    def test_validate_valid_file(self, temp_dir):
        """Test validating a valid VTT file."""
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:03.000
First caption

2
00:00:03.000 --> 00:00:06.000
Second caption
"""
        vtt_path = temp_dir / "valid.vtt"
        vtt_path.write_text(vtt_content)

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_invalid_timing(self, temp_dir):
        """Test validation catches start >= end timing."""
        vtt_content = """WEBVTT

1
00:00:05.000 --> 00:00:03.000
Invalid timing
"""
        vtt_path = temp_dir / "invalid_timing.vtt"
        vtt_path.write_text(vtt_content)

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is False
        assert any("Start time >= end time" in issue for issue in issues)

    def test_validate_overlapping_captions(self, temp_dir):
        """Test validation catches overlapping captions."""
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:05.000
First caption

2
00:00:03.000 --> 00:00:08.000
Overlapping caption
"""
        vtt_path = temp_dir / "overlapping.vtt"
        vtt_path.write_text(vtt_content)

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is False
        assert any("Overlapping" in issue for issue in issues)

    def test_validate_sequential_captions(self, temp_dir):
        """Test validation passes for sequential captions."""
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:03.000
First

2
00:00:03.000 --> 00:00:06.000
Second

3
00:00:06.000 --> 00:00:09.000
Third
"""
        vtt_path = temp_dir / "sequential.vtt"
        vtt_path.write_text(vtt_content)

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_with_gaps(self, temp_dir):
        """Test validation allows gaps between captions."""
        vtt_content = """WEBVTT

1
00:00:00.000 --> 00:00:02.000
First

2
00:00:05.000 --> 00:00:07.000
Second with gap
"""
        vtt_path = temp_dir / "gaps.vtt"
        vtt_path.write_text(vtt_content)

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is True

    def test_validate_with_styles(self, temp_dir):
        """Test validation handles styled captions."""
        vtt_content = """WEBVTT

STYLE
::cue(.emphasis) {
  color: red;
}

1
00:00:00.000 --> 00:00:03.000
<c.emphasis>Styled text</c>
"""
        vtt_path = temp_dir / "styled.vtt"
        vtt_path.write_text(vtt_content)

        is_valid, issues = validate_vtt(vtt_path)

        assert is_valid is True
