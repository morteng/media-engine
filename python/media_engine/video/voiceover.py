"""
Voiceover Generation Module

Generates voiceover audio using ElevenLabs TTS with smart caching.
Integrates with Project for caching and configuration.

Features:
- Script-hash based caching (don't regenerate unchanged text)
- Multiple voice support
- Multi-language support
- Pause calculation based on punctuation
- Segment concatenation
"""

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from ..core.hashing import compute_raw_hash

if TYPE_CHECKING:
    from ..core.project import Project


@dataclass
class AudioSegment:
    """Represents a generated audio segment."""

    id: str
    text: str
    duration: float
    audio_path: Optional[Path] = None
    pause_after: float = 0.0


@dataclass
class VoiceoverResult:
    """Result of voiceover generation."""

    audio_path: Path
    total_duration: float
    segments: List[AudioSegment]
    cached: bool = False


def get_api_key() -> str:
    """Get ElevenLabs API key from environment.

    Searches for .env file in current directory and parent directories.
    """
    from dotenv import load_dotenv

    # Try loading from current directory first
    load_dotenv()

    # If not found, search up to find project .env file
    if not (os.environ.get("ELEVEN_LABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")):
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            env_file = parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                break
            # Stop at typical project boundaries
            if (parent / "project.yaml").exists() or (parent / "pyproject.toml").exists():
                load_dotenv(env_file)  # Try loading even if .env doesn't exist (will be no-op)
                break

    key = os.environ.get("ELEVEN_LABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError(
            "ELEVEN_LABS_API_KEY not set. Add it to .env file or export as environment variable."
        )
    return key


def clean_text(text: str) -> str:
    """
    Clean text for TTS processing.

    Removes:
    - [pause:X] markers
    - [emphasis] markers
    - Excess whitespace
    """
    if not text:
        return ""

    # Remove markers
    text = re.sub(r"\[pause:[0-9.]+\]", " ", text)
    text = re.sub(r"\[(emphasis|slower|faster|break)\]", "", text)

    # Clean whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def calculate_hash(text: str, voice_id: str, language: str = "en") -> str:
    """Calculate cache hash for text + voice + language."""
    content = f"{voice_id}:{language}:{text}"
    return compute_raw_hash(content)


def calculate_pause(text: str, is_last: bool = False) -> float:
    """
    Calculate natural pause duration based on punctuation.

    Args:
        text: The text that was spoken
        is_last: Whether this is the last segment (no pause after)

    Returns:
        Pause duration in seconds
    """
    if is_last:
        return 0.0

    if not text or not text.strip():
        return 0.3

    clean = clean_text(text)
    if not clean:
        return 0.3

    last_char = clean.rstrip()[-1] if clean.rstrip() else "."

    # Pause based on punctuation
    if last_char == "?":
        return 0.9  # Questions need comprehension time
    elif last_char == "!":
        return 0.6  # Exclamations
    elif last_char == ".":
        word_count = len(clean.split())
        return 0.5 if word_count < 5 else 0.4
    elif last_char in [",", ";", ":"]:
        return 0.25  # Continuing thought
    else:
        return 0.4


def measure_duration(audio_path: Path) -> float:
    """Measure duration of an audio file in seconds."""
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_mp3(str(audio_path))
        return len(audio) / 1000.0
    except Exception:
        return 0.0


async def generate_silence(output_path: Path, duration: float) -> Path:
    """Generate silent audio of specified duration."""
    from pydub import AudioSegment as PyAudio

    silence = PyAudio.silent(duration=int(duration * 1000))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    silence.export(str(output_path), format="mp3")

    return output_path


async def generate_segment(
    text: str,
    voice_id: str,
    output_path: Path,
    cache_dir: Optional[Path] = None,
    language: str = "en",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
) -> tuple[Path, bool]:
    """
    Generate audio for a single text segment.

    Args:
        text: Text to synthesize
        voice_id: ElevenLabs voice ID
        output_path: Where to save the audio
        cache_dir: Optional cache directory
        language: Language code (e.g., "en", "no")
        stability: Voice stability (0-1)
        similarity_boost: Voice similarity boost (0-1)

    Returns:
        Tuple of (audio_path, was_cached)
    """
    from elevenlabs.client import ElevenLabs

    clean = clean_text(text)
    if not clean:
        await generate_silence(output_path, 0.5)
        return output_path, False

    # Check cache
    text_hash = calculate_hash(clean, voice_id, language)
    if cache_dir:
        cache_path = cache_dir / f"{text_hash}.mp3"
        if cache_path.exists():
            shutil.copy(cache_path, output_path)
            return output_path, True

    # Generate with ElevenLabs
    client = ElevenLabs(api_key=get_api_key())

    audio = client.text_to_speech.convert(
        text=clean,
        voice_id=voice_id,
        model_id="eleven_turbo_v2_5",
        language_code=language if language != "en" else None,
    )

    # Save audio
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Cache for future use
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(output_path, cache_path)

    return output_path, False


async def concatenate_segments(
    segments: List[AudioSegment],
    output_path: Path,
) -> float:
    """
    Concatenate audio segments with calculated pauses.

    Args:
        segments: List of AudioSegment with paths and pause_after values
        output_path: Output file path

    Returns:
        Total duration in seconds
    """
    from pydub import AudioSegment as PyAudio

    combined = PyAudio.empty()

    for i, segment in enumerate(segments):
        if segment.audio_path and segment.audio_path.exists():
            audio = PyAudio.from_mp3(str(segment.audio_path))
            combined += audio

            # Add pause (not after last segment)
            if segment.pause_after > 0:
                pause = PyAudio.silent(duration=int(segment.pause_after * 1000))
                combined += pause

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(output_path), format="mp3")

    return len(combined) / 1000.0


async def generate_voiceover(
    texts: List[tuple[str, str]],  # List of (id, text)
    output_path: Path,
    voice_id: str,
    cache_dir: Optional[Path] = None,
    language: str = "en",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    progress_callback=None,
) -> VoiceoverResult:
    """
    Generate complete voiceover from list of text segments.

    Args:
        texts: List of (segment_id, text) tuples
        output_path: Where to save final audio
        voice_id: ElevenLabs voice ID
        cache_dir: Optional cache directory for segments
        language: Language code
        stability: Voice stability
        similarity_boost: Voice similarity
        progress_callback: Optional callback(segment_id, status)

    Returns:
        VoiceoverResult with path, duration, and segment info
    """
    if not texts:
        raise ValueError("No text segments provided")

    # Create temp directory for segments
    temp_dir = output_path.parent / ".temp" / output_path.stem
    temp_dir.mkdir(parents=True, exist_ok=True)

    segments = []
    total_cached = 0

    try:
        for i, (seg_id, text) in enumerate(texts):
            is_last = i == len(texts) - 1
            segment_path = temp_dir / f"{i:03d}_{seg_id}.mp3"

            if progress_callback:
                progress_callback(seg_id, "generating")

            # Generate audio
            path, was_cached = await generate_segment(
                text=text,
                voice_id=voice_id,
                output_path=segment_path,
                cache_dir=cache_dir,
                language=language,
                stability=stability,
                similarity_boost=similarity_boost,
            )

            if was_cached:
                total_cached += 1

            # Measure duration
            duration = measure_duration(path)

            # Calculate pause
            pause = calculate_pause(text, is_last)

            segments.append(
                AudioSegment(
                    id=seg_id,
                    text=text,
                    duration=duration,
                    audio_path=path,
                    pause_after=pause,
                )
            )

            if progress_callback:
                progress_callback(seg_id, "done")

        # Concatenate all segments
        total_duration = await concatenate_segments(segments, output_path)

        return VoiceoverResult(
            audio_path=output_path,
            total_duration=total_duration,
            segments=segments,
            cached=(total_cached == len(texts)),
        )

    finally:
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)


async def generate_voiceover_for_script(
    script_path: Path,
    output_path: Path,
    project: "Project",
    language: str = None,
) -> VoiceoverResult:
    """
    Generate voiceover from a video script YAML file.

    Args:
        script_path: Path to video script YAML
        output_path: Where to save audio
        project: Project for configuration and caching
        language: Override language (default: from script or project)

    Returns:
        VoiceoverResult
    """
    import yaml

    with open(script_path, "r") as f:
        script = yaml.safe_load(f)

    # Get language
    lang = language or script.get("metadata", {}).get("language") or project.source_language

    # Get voice ID
    lang_config = project.languages.get(lang)
    voice_id = lang_config.voice_id if lang_config else project.config.voiceover.voice_id

    if not voice_id:
        raise ValueError(f"No voice_id configured for language '{lang}'")

    # Extract text segments from scenes
    texts = []
    for scene in script.get("scenes", []):
        scene_id = scene.get("id", f"scene_{len(texts)}")

        # Get narration/voiceover text
        text = None
        if "content" in scene:
            content = scene["content"]
            if isinstance(content, dict):
                text = content.get("text") or content.get("narration")
            elif isinstance(content, str):
                text = content

        if text:
            texts.append((scene_id, text))

    if not texts:
        raise ValueError(f"No voiceover text found in script: {script_path}")

    # Generate voiceover
    return await generate_voiceover(
        texts=texts,
        output_path=output_path,
        voice_id=voice_id,
        cache_dir=project.cache_dir / "voiceover",
        language=lang,
        stability=project.config.voiceover.stability,
        similarity_boost=project.config.voiceover.similarity_boost,
    )


# macOS fallback for offline/free generation
async def generate_voiceover_macos(
    texts: List[tuple[str, str]],
    output_path: Path,
    voice: str = "Samantha",
) -> VoiceoverResult:
    """
    Generate voiceover using macOS 'say' command (fallback).

    Lower quality but free and works offline.
    """
    import subprocess
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())
    segments = []

    try:
        for i, (seg_id, text) in enumerate(texts):
            is_last = i == len(texts) - 1
            clean = clean_text(text)

            if not clean:
                continue

            segment_path = temp_dir / f"{i:03d}.aiff"

            # Use macOS say command
            subprocess.run(
                ["say", "-v", voice, "-o", str(segment_path), clean],
                check=True,
                capture_output=True,
            )

            # Convert to mp3
            mp3_path = temp_dir / f"{i:03d}.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(segment_path),
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "192k",
                    str(mp3_path),
                ],
                check=True,
                capture_output=True,
            )

            duration = measure_duration(mp3_path)
            pause = calculate_pause(text, is_last)

            segments.append(
                AudioSegment(
                    id=seg_id,
                    text=text,
                    duration=duration,
                    audio_path=mp3_path,
                    pause_after=pause,
                )
            )

        # Concatenate
        total_duration = await concatenate_segments(segments, output_path)

        return VoiceoverResult(
            audio_path=output_path,
            total_duration=total_duration,
            segments=segments,
            cached=False,
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
