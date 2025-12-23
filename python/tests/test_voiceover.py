"""
Tests for media_engine.video.voiceover module.

Tests cover:
- AudioSegment and VoiceoverResult dataclasses
- Text cleaning and hash calculation
- Pause calculation based on punctuation
- API key retrieval
- Duration measurement
- Segment generation with caching
- Audio concatenation
- Complete voiceover generation
- Script-based voiceover generation
- macOS fallback generation
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from media_engine.video.voiceover import (
    AudioSegment,
    VoiceoverResult,
    calculate_hash,
    calculate_pause,
    clean_text,
    concatenate_segments,
    generate_segment,
    generate_silence,
    generate_voiceover,
    generate_voiceover_for_script,
    generate_voiceover_macos,
    get_api_key,
    measure_duration,
)


class TestAudioSegment:
    """Tests for AudioSegment dataclass."""

    def test_creation_with_all_fields(self, temp_dir):
        """Test creating segment with all fields."""
        segment = AudioSegment(
            id="seg1",
            text="Hello world",
            duration=2.5,
            audio_path=temp_dir / "audio.mp3",
            pause_after=0.5,
        )
        assert segment.id == "seg1"
        assert segment.text == "Hello world"
        assert segment.duration == 2.5
        assert segment.audio_path == temp_dir / "audio.mp3"
        assert segment.pause_after == 0.5

    def test_creation_with_defaults(self):
        """Test creating segment with default values."""
        segment = AudioSegment(
            id="seg1",
            text="Hello",
            duration=1.0,
        )
        assert segment.audio_path is None
        assert segment.pause_after == 0.0


class TestVoiceoverResult:
    """Tests for VoiceoverResult dataclass."""

    def test_creation(self, temp_dir):
        """Test creating voiceover result."""
        segments = [
            AudioSegment(id="s1", text="Hello", duration=1.0),
            AudioSegment(id="s2", text="World", duration=1.5),
        ]
        result = VoiceoverResult(
            audio_path=temp_dir / "final.mp3",
            total_duration=5.5,
            segments=segments,
            cached=True,
        )
        assert result.audio_path == temp_dir / "final.mp3"
        assert result.total_duration == 5.5
        assert len(result.segments) == 2
        assert result.cached is True

    def test_default_cached_false(self, temp_dir):
        """Test that cached defaults to False."""
        result = VoiceoverResult(
            audio_path=temp_dir / "test.mp3",
            total_duration=10.0,
            segments=[],
        )
        assert result.cached is False


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_get_api_key_from_eleven_labs_var(self):
        """Test getting API key from ELEVEN_LABS_API_KEY."""
        with patch.dict(os.environ, {"ELEVEN_LABS_API_KEY": "test-key-123"}, clear=True):
            key = get_api_key()
            assert key == "test-key-123"

    def test_get_api_key_from_elevenlabs_var(self):
        """Test getting API key from ELEVENLABS_API_KEY."""
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-key-456"}, clear=True):
            key = get_api_key()
            assert key == "test-key-456"

    def test_get_api_key_prefers_eleven_labs(self):
        """Test that ELEVEN_LABS_API_KEY takes precedence."""
        with patch.dict(
            os.environ,
            {
                "ELEVEN_LABS_API_KEY": "primary-key",
                "ELEVENLABS_API_KEY": "secondary-key",
            },
            clear=True,
        ):
            key = get_api_key()
            assert key == "primary-key"

    def test_get_api_key_missing_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ELEVEN_LABS_API_KEY not set"):
                get_api_key()


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_empty_text(self):
        """Test cleaning empty text."""
        assert clean_text("") == ""
        assert clean_text(None) == ""

    def test_remove_pause_markers(self):
        """Test removing [pause:X] markers."""
        text = "Hello [pause:1.5] world [pause:0.5] today"
        result = clean_text(text)
        assert "[pause:" not in result
        assert "Hello" in result
        assert "world" in result
        assert "today" in result

    def test_remove_emphasis_markers(self):
        """Test removing emphasis markers."""
        text = "This is [emphasis]important[emphasis] and [slower]slow[slower]"
        result = clean_text(text)
        assert "[emphasis]" not in result
        assert "[slower]" not in result
        assert "important" in result

    def test_remove_break_markers(self):
        """Test removing break markers."""
        text = "First part[break]second part"
        result = clean_text(text)
        assert "[break]" not in result

    def test_remove_faster_markers(self):
        """Test removing faster markers."""
        text = "Speed up [faster]this part[faster]"
        result = clean_text(text)
        assert "[faster]" not in result

    def test_clean_whitespace(self):
        """Test cleaning excess whitespace."""
        text = "Hello    world\n\n  today   "
        result = clean_text(text)
        assert result == "Hello world today"

    def test_clean_complex_text(self):
        """Test cleaning text with multiple markers and whitespace."""
        text = "  Welcome [pause:2.0] to the [emphasis]demo[emphasis]  \n  today  "
        result = clean_text(text)
        assert result == "Welcome to the demo today"


class TestCalculateHash:
    """Tests for calculate_hash function."""

    def test_hash_consistency(self):
        """Test that same inputs produce same hash."""
        hash1 = calculate_hash("Hello world", "voice-123", "en")
        hash2 = calculate_hash("Hello world", "voice-123", "en")
        assert hash1 == hash2

    def test_hash_length(self):
        """Test that hash is truncated to 16 chars."""
        result = calculate_hash("Test", "voice", "en")
        assert len(result) == 16

    def test_different_text_different_hash(self):
        """Test that different text produces different hash."""
        hash1 = calculate_hash("Hello", "voice-123", "en")
        hash2 = calculate_hash("Goodbye", "voice-123", "en")
        assert hash1 != hash2

    def test_different_voice_different_hash(self):
        """Test that different voice ID produces different hash."""
        hash1 = calculate_hash("Hello", "voice-1", "en")
        hash2 = calculate_hash("Hello", "voice-2", "en")
        assert hash1 != hash2

    def test_different_language_different_hash(self):
        """Test that different language produces different hash."""
        hash1 = calculate_hash("Hello", "voice-123", "en")
        hash2 = calculate_hash("Hello", "voice-123", "no")
        assert hash1 != hash2

    def test_hash_format(self):
        """Test that hash contains only hexadecimal characters."""
        result = calculate_hash("Test", "voice", "en")
        assert all(c in "0123456789abcdef" for c in result)


class TestCalculatePause:
    """Tests for calculate_pause function."""

    def test_last_segment_no_pause(self):
        """Test that last segment gets no pause."""
        assert calculate_pause("Any text here.", is_last=True) == 0.0
        assert calculate_pause("Question?", is_last=True) == 0.0

    def test_empty_text_default_pause(self):
        """Test empty text gets default pause."""
        assert calculate_pause("") == 0.3
        assert calculate_pause("   ") == 0.3

    def test_question_mark_pause(self):
        """Test question mark gets longer pause."""
        assert calculate_pause("What is this?") == 0.9

    def test_exclamation_pause(self):
        """Test exclamation gets medium pause."""
        assert calculate_pause("Amazing!") == 0.6

    def test_period_short_sentence(self):
        """Test period with short sentence."""
        pause = calculate_pause("Hello.")
        assert pause == 0.5  # Less than 5 words

    def test_period_long_sentence(self):
        """Test period with longer sentence."""
        pause = calculate_pause("This is a longer sentence with many words.")
        assert pause == 0.4  # 5 or more words

    def test_comma_pause(self):
        """Test comma gets short pause."""
        assert calculate_pause("First,") == 0.25

    def test_semicolon_pause(self):
        """Test semicolon gets short pause."""
        assert calculate_pause("First part;") == 0.25

    def test_colon_pause(self):
        """Test colon gets short pause."""
        assert calculate_pause("Here it is:") == 0.25

    def test_other_punctuation(self):
        """Test other endings get default pause."""
        assert calculate_pause("Testing") == 0.4

    def test_with_markers_removed(self):
        """Test that pause markers are removed before checking."""
        pause = calculate_pause("What is this[pause:1.0]?")
        assert pause == 0.9  # Should detect the question mark


class TestMeasureDuration:
    """Tests for measure_duration function."""

    @patch("pydub.AudioSegment")
    def test_measure_duration_success(self, mock_audio_segment, temp_dir):
        """Test successful duration measurement."""
        # Mock AudioSegment.from_mp3
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=5000)  # 5000ms = 5s
        mock_audio_segment.from_mp3.return_value = mock_audio

        audio_path = temp_dir / "test.mp3"
        audio_path.touch()

        duration = measure_duration(audio_path)
        assert duration == 5.0
        mock_audio_segment.from_mp3.assert_called_once_with(str(audio_path))

    @patch("pydub.AudioSegment")
    def test_measure_duration_error(self, mock_audio_segment, temp_dir):
        """Test that errors return 0.0."""
        mock_audio_segment.from_mp3.side_effect = Exception("Test error")

        audio_path = temp_dir / "test.mp3"
        duration = measure_duration(audio_path)
        assert duration == 0.0


class TestGenerateSilence:
    """Tests for generate_silence function."""

    @pytest.mark.asyncio
    @patch("pydub.AudioSegment")
    async def test_generate_silence(self, mock_audio_segment, temp_dir):
        """Test generating silent audio."""
        mock_silence = MagicMock()
        mock_audio_segment.silent.return_value = mock_silence

        output_path = temp_dir / "silence.mp3"
        result = await generate_silence(output_path, 2.5)

        assert result == output_path
        mock_audio_segment.silent.assert_called_once_with(duration=2500)  # 2.5s = 2500ms
        mock_silence.export.assert_called_once_with(str(output_path), format="mp3")

    @pytest.mark.asyncio
    @patch("pydub.AudioSegment")
    async def test_generate_silence_creates_parent_dir(self, mock_audio_segment, temp_dir):
        """Test that parent directory is created."""
        mock_silence = MagicMock()
        mock_audio_segment.silent.return_value = mock_silence

        output_path = temp_dir / "subdir" / "nested" / "silence.mp3"
        await generate_silence(output_path, 1.0)

        assert output_path.parent.exists()


class TestGenerateSegment:
    """Tests for generate_segment function."""

    @pytest.mark.asyncio
    async def test_generate_segment_empty_text(self, temp_dir):
        """Test generating segment with empty text creates silence."""
        output_path = temp_dir / "output.mp3"

        with patch("media_engine.video.voiceover.generate_silence") as mock_silence:
            mock_silence.return_value = output_path
            path, cached = await generate_segment(
                text="   ",
                voice_id="voice-123",
                output_path=output_path,
            )

            assert path == output_path
            assert cached is False
            mock_silence.assert_called_once_with(output_path, 0.5)

    @pytest.mark.asyncio
    async def test_generate_segment_from_cache(self, temp_dir):
        """Test generating segment from cache."""
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        output_path = temp_dir / "output.mp3"

        # Create cached file
        text = "Hello world"
        text_hash = calculate_hash(clean_text(text), "voice-123", "en")
        cache_path = cache_dir / f"{text_hash}.mp3"
        cache_path.write_text("cached audio data")

        path, cached = await generate_segment(
            text=text,
            voice_id="voice-123",
            output_path=output_path,
            cache_dir=cache_dir,
            language="en",
        )

        assert path == output_path
        assert cached is True
        assert output_path.exists()
        assert output_path.read_text() == "cached audio data"

    @pytest.mark.asyncio
    @patch("elevenlabs.client.ElevenLabs")
    @patch("media_engine.video.voiceover.get_api_key")
    async def test_generate_segment_new_audio(self, mock_get_key, mock_elevenlabs, temp_dir):
        """Test generating new audio with ElevenLabs."""
        mock_get_key.return_value = "test-api-key"

        # Mock ElevenLabs client
        mock_client = MagicMock()
        mock_audio_data = [b"audio", b"chunk", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio_data
        mock_elevenlabs.return_value = mock_client

        output_path = temp_dir / "output.mp3"
        path, cached = await generate_segment(
            text="Hello world",
            voice_id="voice-123",
            output_path=output_path,
            language="en",
            stability=0.6,
            similarity_boost=0.8,
        )

        assert path == output_path
        assert cached is False
        assert output_path.exists()
        assert output_path.read_bytes() == b"audiochunkdata"

        mock_client.text_to_speech.convert.assert_called_once_with(
            text="Hello world",
            voice_id="voice-123",
            model_id="eleven_turbo_v2_5",
            language_code=None,  # en gets None
        )

    @pytest.mark.asyncio
    @patch("elevenlabs.client.ElevenLabs")
    @patch("media_engine.video.voiceover.get_api_key")
    async def test_generate_segment_non_english(self, mock_get_key, mock_elevenlabs, temp_dir):
        """Test generating audio with non-English language."""
        mock_get_key.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]
        mock_elevenlabs.return_value = mock_client

        output_path = temp_dir / "output.mp3"
        await generate_segment(
            text="Hei verden",
            voice_id="voice-no",
            output_path=output_path,
            language="no",
        )

        # Should pass language code for non-English
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        assert call_kwargs["language_code"] == "no"

    @pytest.mark.asyncio
    @patch("elevenlabs.client.ElevenLabs")
    @patch("media_engine.video.voiceover.get_api_key")
    async def test_generate_segment_with_caching(self, mock_get_key, mock_elevenlabs, temp_dir):
        """Test that generated audio is cached."""
        mock_get_key.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio_data"]
        mock_elevenlabs.return_value = mock_client

        cache_dir = temp_dir / "cache"
        output_path = temp_dir / "output.mp3"

        await generate_segment(
            text="Test caching",
            voice_id="voice-123",
            output_path=output_path,
            cache_dir=cache_dir,
            language="en",
        )

        # Check cache file was created
        text_hash = calculate_hash("Test caching", "voice-123", "en")
        cache_path = cache_dir / f"{text_hash}.mp3"
        assert cache_path.exists()
        assert cache_path.read_bytes() == b"audio_data"


class TestConcatenateSegments:
    """Tests for concatenate_segments function."""

    @pytest.mark.asyncio
    @patch("pydub.AudioSegment")
    async def test_concatenate_empty_segments(self, mock_audio_segment, temp_dir):
        """Test concatenating empty segment list."""
        mock_empty = MagicMock()
        mock_empty.__len__ = MagicMock(return_value=0)
        mock_audio_segment.empty.return_value = mock_empty

        output_path = temp_dir / "final.mp3"
        duration = await concatenate_segments([], output_path)

        assert duration == 0.0
        mock_empty.export.assert_called_once()

    @pytest.mark.asyncio
    @patch("pydub.AudioSegment")
    async def test_concatenate_segments(self, mock_audio_segment, temp_dir):
        """Test concatenating multiple segments with pauses."""
        # Create temp audio files
        audio1 = temp_dir / "seg1.mp3"
        audio2 = temp_dir / "seg2.mp3"
        audio1.touch()
        audio2.touch()

        # Mock the addition operation properly
        class MockAudio:
            def __init__(self, length):
                self._length = length

            def __len__(self):
                return self._length

            def __add__(self, other):
                return MockAudio(self._length + len(other))

            def export(self, path, format):
                pass

        mock_empty = MockAudio(0)
        mock_segment1 = MockAudio(2000)
        mock_segment2 = MockAudio(2500)
        mock_pause = MockAudio(500)

        mock_audio_segment.empty.return_value = mock_empty
        mock_audio_segment.from_mp3.side_effect = [mock_segment1, mock_segment2]
        mock_audio_segment.silent.return_value = mock_pause

        segments = [
            AudioSegment(id="s1", text="First", duration=2.0, audio_path=audio1, pause_after=0.5),
            AudioSegment(id="s2", text="Second", duration=2.5, audio_path=audio2, pause_after=0.0),
        ]

        output_path = temp_dir / "final.mp3"
        duration = await concatenate_segments(segments, output_path)

        assert duration == 5.0
        assert mock_audio_segment.from_mp3.call_count == 2
        # First segment has pause
        mock_audio_segment.silent.assert_called_once_with(duration=500)  # 0.5s = 500ms

    @pytest.mark.asyncio
    @patch("pydub.AudioSegment")
    async def test_concatenate_skips_missing_files(self, mock_audio_segment, temp_dir):
        """Test that missing audio files are skipped."""
        mock_combined = MagicMock()
        mock_combined.__len__ = MagicMock(return_value=2000)
        mock_audio_segment.empty.return_value = mock_combined

        # Only create one file
        audio1 = temp_dir / "exists.mp3"
        audio1.touch()
        audio2 = temp_dir / "missing.mp3"  # Don't create this one

        mock_segment = MagicMock()
        mock_audio_segment.from_mp3.return_value = mock_segment

        segments = [
            AudioSegment(id="s1", text="First", duration=1.0, audio_path=audio1),
            AudioSegment(id="s2", text="Second", duration=1.0, audio_path=audio2),
        ]

        output_path = temp_dir / "final.mp3"
        await concatenate_segments(segments, output_path)

        # Should only load the existing file
        assert mock_audio_segment.from_mp3.call_count == 1

    @pytest.mark.asyncio
    @patch("pydub.AudioSegment")
    async def test_concatenate_creates_parent_dir(self, mock_audio_segment, temp_dir):
        """Test that parent directory is created."""
        mock_combined = MagicMock()
        mock_combined.__len__ = MagicMock(return_value=1000)
        mock_audio_segment.empty.return_value = mock_combined

        output_path = temp_dir / "nested" / "dir" / "final.mp3"
        await concatenate_segments([], output_path)

        assert output_path.parent.exists()


class TestGenerateVoiceover:
    """Tests for generate_voiceover function."""

    @pytest.mark.asyncio
    async def test_generate_voiceover_empty_texts(self):
        """Test that empty text list raises ValueError."""
        with pytest.raises(ValueError, match="No text segments provided"):
            await generate_voiceover(
                texts=[],
                output_path=Path("/tmp/test.mp3"),
                voice_id="voice-123",
            )

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("media_engine.video.voiceover.generate_segment")
    async def test_generate_voiceover_success(
        self, mock_gen_seg, mock_measure, mock_concat, temp_dir
    ):
        """Test successful voiceover generation."""

        # Setup mocks
        async def mock_generate(text, voice_id, output_path, **kwargs):
            output_path.touch()
            return output_path, False

        mock_gen_seg.side_effect = mock_generate
        mock_measure.return_value = 2.5
        mock_concat.return_value = 7.5

        texts = [
            ("seg1", "First segment."),
            ("seg2", "Second segment?"),
            ("seg3", "Third segment!"),
        ]

        output_path = temp_dir / "voiceover.mp3"
        result = await generate_voiceover(
            texts=texts,
            output_path=output_path,
            voice_id="voice-123",
            language="en",
            stability=0.5,
            similarity_boost=0.75,
        )

        assert result.audio_path == output_path
        assert result.total_duration == 7.5
        assert len(result.segments) == 3
        assert result.cached is False  # No segments were cached

        # Verify segments have correct pauses
        assert result.segments[0].pause_after == 0.5  # period, 2 words (< 5)
        assert result.segments[1].pause_after == 0.9  # question
        assert result.segments[2].pause_after == 0.0  # last segment

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("media_engine.video.voiceover.generate_segment")
    async def test_generate_voiceover_with_cache(
        self, mock_gen_seg, mock_measure, mock_concat, temp_dir
    ):
        """Test voiceover generation using cache."""

        async def mock_generate(text, voice_id, output_path, **kwargs):
            output_path.touch()
            # All segments cached
            return output_path, True

        mock_gen_seg.side_effect = mock_generate
        mock_measure.return_value = 2.0
        mock_concat.return_value = 6.0

        cache_dir = temp_dir / "cache"
        texts = [("s1", "One."), ("s2", "Two.")]

        output_path = temp_dir / "voiceover.mp3"
        result = await generate_voiceover(
            texts=texts,
            output_path=output_path,
            voice_id="voice-123",
            cache_dir=cache_dir,
        )

        assert result.cached is True  # All segments were cached

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("media_engine.video.voiceover.generate_segment")
    async def test_generate_voiceover_progress_callback(
        self, mock_gen_seg, mock_measure, mock_concat, temp_dir
    ):
        """Test progress callback is called correctly."""

        async def mock_generate(text, voice_id, output_path, **kwargs):
            output_path.touch()
            return output_path, False

        mock_gen_seg.side_effect = mock_generate
        mock_measure.return_value = 1.0
        mock_concat.return_value = 3.0

        callback_calls = []

        def progress_callback(seg_id, status):
            callback_calls.append((seg_id, status))

        texts = [("s1", "One."), ("s2", "Two.")]
        output_path = temp_dir / "voiceover.mp3"

        await generate_voiceover(
            texts=texts,
            output_path=output_path,
            voice_id="voice-123",
            progress_callback=progress_callback,
        )

        # Should have generating and done for each segment
        assert callback_calls == [
            ("s1", "generating"),
            ("s1", "done"),
            ("s2", "generating"),
            ("s2", "done"),
        ]

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("media_engine.video.voiceover.generate_segment")
    async def test_generate_voiceover_cleans_up_temp_files(
        self, mock_gen_seg, mock_measure, mock_concat, temp_dir
    ):
        """Test that temporary files are cleaned up."""

        async def mock_generate(text, voice_id, output_path, **kwargs):
            output_path.touch()
            return output_path, False

        mock_gen_seg.side_effect = mock_generate
        mock_measure.return_value = 1.0
        mock_concat.return_value = 2.0

        texts = [("s1", "Test.")]
        output_path = temp_dir / "voiceover.mp3"

        await generate_voiceover(
            texts=texts,
            output_path=output_path,
            voice_id="voice-123",
        )

        # Temp directory should be cleaned up
        temp_seg_dir = output_path.parent / ".temp" / output_path.stem
        assert not temp_seg_dir.exists()

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("media_engine.video.voiceover.generate_segment")
    async def test_generate_voiceover_cleans_up_on_error(
        self, mock_gen_seg, mock_measure, mock_concat, temp_dir
    ):
        """Test that temp files are cleaned up even on error."""

        async def mock_generate(text, voice_id, output_path, **kwargs):
            raise Exception("Test error")

        mock_gen_seg.side_effect = mock_generate

        texts = [("s1", "Test.")]
        output_path = temp_dir / "voiceover.mp3"

        with pytest.raises(Exception, match="Test error"):
            await generate_voiceover(
                texts=texts,
                output_path=output_path,
                voice_id="voice-123",
            )

        # Temp directory should still be cleaned up
        temp_seg_dir = output_path.parent / ".temp" / output_path.stem
        assert not temp_seg_dir.exists()


class TestGenerateVoiceoverForScript:
    """Tests for generate_voiceover_for_script function."""

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.generate_voiceover")
    async def test_generate_from_script_basic(self, mock_gen_vo, temp_dir):
        """Test generating voiceover from script file."""
        # Create script
        script_content = """
metadata:
  title: "Test Video"
  language: "en"

scenes:
  - id: intro
    content:
      text: "Welcome to the video."
  - id: main
    content:
      narration: "This is the main content."
"""
        script_path = temp_dir / "script.yaml"
        script_path.write_text(script_content)

        # Mock project
        mock_project = MagicMock()
        mock_project.source_language = "en"
        mock_lang_config = MagicMock()
        mock_lang_config.voice_id = "voice-en"
        mock_project.languages = {"en": mock_lang_config}
        mock_project.config.voiceover.stability = 0.5
        mock_project.config.voiceover.similarity_boost = 0.75
        mock_project.cache_dir = temp_dir / "cache"

        mock_result = VoiceoverResult(
            audio_path=temp_dir / "output.mp3",
            total_duration=10.0,
            segments=[],
        )
        mock_gen_vo.return_value = mock_result

        output_path = temp_dir / "output.mp3"
        result = await generate_voiceover_for_script(
            script_path=script_path,
            output_path=output_path,
            project=mock_project,
        )

        assert result == mock_result

        # Verify generate_voiceover was called with correct texts
        call_args = mock_gen_vo.call_args
        texts = call_args[1]["texts"]
        assert len(texts) == 2
        assert texts[0] == ("intro", "Welcome to the video.")
        assert texts[1] == ("main", "This is the main content.")

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.generate_voiceover")
    async def test_generate_from_script_string_content(self, mock_gen_vo, temp_dir):
        """Test script with string content instead of dict."""
        script_content = """
scenes:
  - id: scene1
    content: "Simple text content."
"""
        script_path = temp_dir / "script.yaml"
        script_path.write_text(script_content)

        mock_project = MagicMock()
        mock_project.source_language = "en"
        mock_project.config.voiceover.voice_id = "default-voice"
        mock_project.languages = {}
        mock_project.config.voiceover.stability = 0.5
        mock_project.config.voiceover.similarity_boost = 0.75
        mock_project.cache_dir = temp_dir / "cache"

        mock_gen_vo.return_value = VoiceoverResult(
            audio_path=temp_dir / "out.mp3",
            total_duration=5.0,
            segments=[],
        )

        await generate_voiceover_for_script(
            script_path=script_path,
            output_path=temp_dir / "out.mp3",
            project=mock_project,
        )

        texts = mock_gen_vo.call_args[1]["texts"]
        assert texts[0] == ("scene1", "Simple text content.")

    @pytest.mark.asyncio
    async def test_generate_from_script_no_voiceover_text(self, temp_dir):
        """Test that missing voiceover text raises error."""
        script_content = """
scenes:
  - id: scene1
    visual:
      type: "title"
"""
        script_path = temp_dir / "script.yaml"
        script_path.write_text(script_content)

        mock_project = MagicMock()
        mock_project.source_language = "en"
        mock_project.config.voiceover.voice_id = "voice-123"
        mock_project.languages = {}

        with pytest.raises(ValueError, match="No voiceover text found"):
            await generate_voiceover_for_script(
                script_path=script_path,
                output_path=temp_dir / "out.mp3",
                project=mock_project,
            )

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.generate_voiceover")
    async def test_generate_from_script_language_override(self, mock_gen_vo, temp_dir):
        """Test language override parameter."""
        script_content = """
metadata:
  language: "en"

scenes:
  - id: scene1
    content:
      text: "Hei verden"
"""
        script_path = temp_dir / "script.yaml"
        script_path.write_text(script_content)

        mock_project = MagicMock()
        mock_project.source_language = "en"
        mock_no_config = MagicMock()
        mock_no_config.voice_id = "voice-no"
        mock_project.languages = {"no": mock_no_config}
        mock_project.config.voiceover.stability = 0.5
        mock_project.config.voiceover.similarity_boost = 0.75
        mock_project.cache_dir = temp_dir / "cache"

        mock_gen_vo.return_value = VoiceoverResult(
            audio_path=temp_dir / "out.mp3",
            total_duration=5.0,
            segments=[],
        )

        await generate_voiceover_for_script(
            script_path=script_path,
            output_path=temp_dir / "out.mp3",
            project=mock_project,
            language="no",  # Override to Norwegian
        )

        # Should use Norwegian voice and language
        call_kwargs = mock_gen_vo.call_args[1]
        assert call_kwargs["voice_id"] == "voice-no"
        assert call_kwargs["language"] == "no"

    @pytest.mark.asyncio
    async def test_generate_from_script_no_voice_id(self, temp_dir):
        """Test that missing voice ID raises error."""
        script_content = """
scenes:
  - id: scene1
    content:
      text: "Test"
"""
        script_path = temp_dir / "script.yaml"
        script_path.write_text(script_content)

        mock_project = MagicMock()
        mock_project.source_language = "en"
        mock_project.languages = {}
        mock_project.config.voiceover.voice_id = None

        with pytest.raises(ValueError, match="No voice_id configured"):
            await generate_voiceover_for_script(
                script_path=script_path,
                output_path=temp_dir / "out.mp3",
                project=mock_project,
            )

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.generate_voiceover")
    async def test_generate_from_script_auto_scene_ids(self, mock_gen_vo, temp_dir):
        """Test automatic scene ID generation."""
        script_content = """
scenes:
  - content:
      text: "First scene"
  - content:
      text: "Second scene"
"""
        script_path = temp_dir / "script.yaml"
        script_path.write_text(script_content)

        mock_project = MagicMock()
        mock_project.source_language = "en"
        mock_project.config.voiceover.voice_id = "voice-123"
        mock_project.languages = {}
        mock_project.config.voiceover.stability = 0.5
        mock_project.config.voiceover.similarity_boost = 0.75
        mock_project.cache_dir = temp_dir / "cache"

        mock_gen_vo.return_value = VoiceoverResult(
            audio_path=temp_dir / "out.mp3",
            total_duration=5.0,
            segments=[],
        )

        await generate_voiceover_for_script(
            script_path=script_path,
            output_path=temp_dir / "out.mp3",
            project=mock_project,
        )

        # Should generate scene IDs automatically
        texts = mock_gen_vo.call_args[1]["texts"]
        assert texts[0][0] == "scene_0"
        assert texts[1][0] == "scene_1"


class TestGenerateVoiceoverMacos:
    """Tests for generate_voiceover_macos function (macOS fallback)."""

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("subprocess.run")
    async def test_macos_voiceover_basic(self, mock_run, mock_measure, mock_concat, temp_dir):
        """Test basic macOS voiceover generation."""
        mock_measure.return_value = 2.0
        mock_concat.return_value = 6.0

        texts = [
            ("s1", "First segment."),
            ("s2", "Second segment."),
        ]

        output_path = temp_dir / "output.mp3"
        result = await generate_voiceover_macos(
            texts=texts,
            output_path=output_path,
            voice="Samantha",
        )

        assert result.audio_path == output_path
        assert result.total_duration == 6.0
        assert len(result.segments) == 2
        assert result.cached is False

        # Verify say command was called
        say_calls = [call for call in mock_run.call_args_list if "say" in call[0][0]]
        assert len(say_calls) == 2

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("subprocess.run")
    async def test_macos_voiceover_skips_empty_text(
        self, mock_run, mock_measure, mock_concat, temp_dir
    ):
        """Test that empty text is skipped."""
        mock_measure.return_value = 1.0
        mock_concat.return_value = 1.0

        texts = [
            ("s1", "Valid text."),
            ("s2", "   "),  # Empty after cleaning
        ]

        output_path = temp_dir / "output.mp3"
        result = await generate_voiceover_macos(
            texts=texts,
            output_path=output_path,
        )

        # Should only generate one segment
        assert len(result.segments) == 1
        assert result.segments[0].text == "Valid text."

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("subprocess.run")
    async def test_macos_voiceover_custom_voice(
        self, mock_run, mock_measure, mock_concat, temp_dir
    ):
        """Test using custom voice."""
        mock_measure.return_value = 1.0
        mock_concat.return_value = 1.0

        texts = [("s1", "Test.")]
        output_path = temp_dir / "output.mp3"

        await generate_voiceover_macos(
            texts=texts,
            output_path=output_path,
            voice="Alex",
        )

        # Check that Alex voice was used
        say_call = [call for call in mock_run.call_args_list if "say" in call[0][0]][0]
        assert "Alex" in say_call[0][0]

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("subprocess.run")
    async def test_macos_voiceover_cleans_temp_files(
        self, mock_run, mock_measure, mock_concat, temp_dir
    ):
        """Test that temporary files are cleaned up."""
        mock_measure.return_value = 1.0
        mock_concat.return_value = 1.0

        texts = [("s1", "Test.")]
        output_path = temp_dir / "output.mp3"

        await generate_voiceover_macos(
            texts=texts,
            output_path=output_path,
        )

        # The temp directory used by tempfile.mkdtemp should be cleaned up
        # We can't easily test this without mocking tempfile.mkdtemp

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("subprocess.run")
    async def test_macos_voiceover_pause_calculation(
        self, mock_run, mock_measure, mock_concat, temp_dir
    ):
        """Test that pauses are calculated correctly."""
        mock_measure.return_value = 1.0
        mock_concat.return_value = 3.0

        texts = [
            ("s1", "First?"),
            ("s2", "Last."),
        ]

        output_path = temp_dir / "output.mp3"
        result = await generate_voiceover_macos(
            texts=texts,
            output_path=output_path,
        )

        # First segment should have question pause
        assert result.segments[0].pause_after == 0.9
        # Last segment should have no pause
        assert result.segments[1].pause_after == 0.0

    @pytest.mark.asyncio
    @patch("media_engine.video.voiceover.concatenate_segments")
    @patch("media_engine.video.voiceover.measure_duration")
    @patch("subprocess.run")
    async def test_macos_voiceover_cleans_text(self, mock_run, mock_measure, mock_concat, temp_dir):
        """Test that text is cleaned before processing."""
        mock_measure.return_value = 1.0
        mock_concat.return_value = 1.0

        texts = [("s1", "Test [pause:1.0] with [emphasis]markers[emphasis].")]
        output_path = temp_dir / "output.mp3"

        await generate_voiceover_macos(
            texts=texts,
            output_path=output_path,
        )

        # Check that say was called with cleaned text
        say_call = [call for call in mock_run.call_args_list if "say" in call[0][0]][0]
        # The cleaned text should not have markers
        assert "[pause:" not in " ".join(say_call[0][0])
        assert "[emphasis]" not in " ".join(say_call[0][0])
