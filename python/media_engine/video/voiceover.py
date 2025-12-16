#!/usr/bin/env python3
"""
ROP Voiceover Generation

Generates voiceover audio from video scripts using Eleven Labs TTS.

Features:
- Scene-by-scene audio generation with pacing
- Caching to avoid regeneration
- Concatenation into single audio file
- Support for multiple voices and languages

Requirements:
    pip install elevenlabs pydub

Environment:
    ELEVEN_LABS_API_KEY - Your Eleven Labs API key

Usage:
    from voiceover import generate_voiceover
    audio_path = await generate_voiceover(script)
"""

import asyncio
import hashlib
import os
import re
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
VIDEO_DIR = PROJECT_ROOT / "docs" / "deliverables" / "video"
AUDIO_DIR = VIDEO_DIR / "audio"
CACHE_DIR = AUDIO_DIR / ".cache"

# Configure pydub to find ffprobe
FFPROBE_PATH = Path.home() / "bin" / "ffprobe"
if FFPROBE_PATH.exists():
    import pydub.utils
    pydub.utils.get_prober_name = lambda: str(FFPROBE_PATH)

# Default voice IDs for Eleven Labs
VOICE_IDS = {
    "adam": "pNInz6obpgDQGcFmaJgB",  # Adam - deep, professional
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Rachel - warm, friendly
    "domi": "AZnzlk1XvdvUeBnXmlld",  # Domi - young, energetic
    "bella": "EXAVITQu4vr4xnSDxMaL",  # Bella - soft, warm
    "antoni": "ErXwobaYiN019PkySvjV",  # Antoni - crisp, clear
    "elli": "MF3mGyEYCl7XYWbV9V6O",  # Elli - young female
    "josh": "TxGEqnHWrfWFTfGW9XjX",  # Josh - young male
    "arnold": "VR6AewLTigWG4xSOukaG",  # Arnold - deep, authoritative
    "sam": "yoZ06aMxZJJ28mfd3POQ",  # Sam - young, natural
}

# Norwegian voices (if available on your account)
NORWEGIAN_VOICE_IDS = {
    "nora": None,  # Will need to be set up in Eleven Labs
}


@dataclass
class AudioSegment:
    """Represents a single audio segment."""
    scene_id: str
    text: str
    duration: float
    audio_path: Optional[Path] = None


def get_api_key() -> str:
    """Get Eleven Labs API key from environment or .env file."""
    # Try loading from .env file first
    try:
        from dotenv import load_dotenv
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass  # dotenv not installed, rely on environment

    key = os.environ.get("ELEVEN_LABS_API_KEY")
    if not key:
        raise ValueError(
            "ELEVEN_LABS_API_KEY not set. "
            "Add it to .env file or export as environment variable. "
            "Get your key from: https://elevenlabs.io/api"
        )
    return key


def extract_voice_id(voice_spec: str) -> str:
    """
    Extract voice ID from voice specification.

    Supports formats:
    - "eleven_labs/adam" -> looks up adam in VOICE_IDS
    - "pNInz6obpgDQGcFmaJgB" -> uses directly
    - "adam" -> looks up in VOICE_IDS
    """
    # Strip prefix
    if "/" in voice_spec:
        voice_spec = voice_spec.split("/")[-1]

    # Check if it's already a voice ID (long alphanumeric string)
    if len(voice_spec) > 15 and voice_spec.isalnum():
        return voice_spec

    # Look up in voice IDs
    voice_id = VOICE_IDS.get(voice_spec.lower())
    if voice_id:
        return voice_id

    # Try Norwegian voices
    voice_id = NORWEGIAN_VOICE_IDS.get(voice_spec.lower())
    if voice_id:
        return voice_id

    # Default to Adam
    print(f"  Warning: Unknown voice '{voice_spec}', using 'adam'")
    return VOICE_IDS["adam"]


def clean_voiceover_text(text: str) -> str:
    """
    Clean voiceover text for TTS.

    Handles:
    - [pause:0.5] markers -> converted to SSML or removed
    - [emphasis] markers -> removed (TTS handles naturally)
    - Excess whitespace
    """
    if not text:
        return ""

    # Remove pacing markers (Eleven Labs handles timing naturally)
    text = re.sub(r'\[pause:[0-9.]+\]', ' ', text)
    text = re.sub(r'\[(emphasis|slower|faster)\]', '', text)

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def measure_audio_duration(audio_path: Path) -> float:
    """
    Measure duration of an audio file using pydub.

    Args:
        audio_path: Path to MP3/audio file

    Returns:
        Duration in seconds (float)
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError(
            "pydub package not installed. Run: pip install pydub"
        )

    audio = AudioSegment.from_mp3(str(audio_path))
    return len(audio) / 1000.0  # Convert ms to seconds


def calculate_pause_after(text: str, is_last_scene: bool = False) -> float:
    """
    Calculate appropriate pause duration based on text content.

    Analyzes punctuation and sentence structure to determine
    natural pause length.

    Args:
        text: Voiceover text to analyze
        is_last_scene: True if this is the final scene (no pause)

    Returns:
        Pause duration in seconds

    Rules:
    - Last scene: 0.0s (no pause after)
    - Ends with "?": 0.9s (question - longer pause for comprehension)
    - Ends with "!": 0.6s (exclamation - medium-long pause)
    - Ends with ".": 0.4-0.5s (statement - shorter for brief, longer for longer)
    - Ends with ",", ";", ":": 0.25s (continuing thought - short pause)
    - Default: 0.4s
    """
    if is_last_scene:
        return 0.0

    if not text or not text.strip():
        return 0.3  # Default for empty scenes

    clean_text = clean_voiceover_text(text)
    if not clean_text:
        return 0.3

    last_char = clean_text.rstrip()[-1] if clean_text.rstrip() else '.'

    # Pause based on punctuation
    if last_char == '?':
        return 0.9  # Question - longer pause for comprehension
    elif last_char == '!':
        return 0.6  # Exclamation - medium-long pause
    elif last_char == '.':
        word_count = len(clean_text.split())
        return 0.5 if word_count < 5 else 0.4  # Shorter statement = longer pause
    elif last_char in [',', ';', ':']:
        return 0.25  # Continuing thought - short pause
    else:
        return 0.4  # Default


def calculate_text_hash(text: str, voice_id: str, language: str = None) -> str:
    """Calculate hash for caching."""
    content = f"{voice_id}:{language or 'auto'}:{text}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]


async def generate_segment_audio(
    text: str,
    voice_id: str,
    output_path: Path,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    language: str = None
) -> Path:
    """
    Generate audio for a single segment using Eleven Labs.

    Returns path to generated audio file.
    """
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        raise ImportError(
            "elevenlabs package not installed. Run: pip install elevenlabs"
        )

    # Create client with API key
    client = ElevenLabs(api_key=get_api_key())

    # Clean text
    clean_text = clean_voiceover_text(text)
    if not clean_text:
        # Return silence for empty text
        return await generate_silence(output_path, 0.5)

    # Check cache (include language in hash)
    text_hash = calculate_text_hash(clean_text, voice_id, language)
    cache_path = CACHE_DIR / f"{text_hash}.mp3"

    if cache_path.exists():
        # Copy from cache
        import shutil
        shutil.copy(cache_path, output_path)
        return output_path

    # Generate audio
    print(f"    Generating: {clean_text[:50]}...")

    # Build API call parameters
    api_params = {
        "text": clean_text,
        "voice_id": voice_id,
        "model_id": "eleven_turbo_v2_5",  # Multilingual model
    }

    # Add language code to enforce pronunciation (ISO 639-1)
    # Turbo v2.5 supports language enforcement for all 32 languages
    if language:
        api_params["language_code"] = language

    audio = client.text_to_speech.convert(**api_params)

    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Cache for future use
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(output_path, cache_path)

    return output_path


async def generate_silence(output_path: Path, duration: float) -> Path:
    """Generate silent audio of specified duration."""
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
    except ImportError:
        raise ImportError(
            "pydub package not installed. Run: pip install pydub"
        )

    # Generate silence
    silence = AudioSegment.silent(duration=int(duration * 1000))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    silence.export(str(output_path), format="mp3")

    return output_path


async def concatenate_audio(
    segments: List[Path],
    output_path: Path,
    pause_between: float = 0.3
) -> Path:
    """
    Concatenate audio segments with pauses between.

    Returns path to concatenated audio file.
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError(
            "pydub package not installed. Run: pip install pydub"
        )

    # Create pause segment
    pause = AudioSegment.silent(duration=int(pause_between * 1000))

    # Concatenate
    combined = AudioSegment.empty()
    for i, segment_path in enumerate(segments):
        segment = AudioSegment.from_mp3(str(segment_path))
        combined += segment

        # Add pause between segments (not after last)
        if i < len(segments) - 1:
            combined += pause

    # Export
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(output_path), format="mp3")

    return output_path


async def generate_voiceover(script) -> Path:
    """
    Generate complete voiceover audio for a video script.

    Args:
        script: VideoScript object with scenes and narrator config

    Returns:
        Path to generated audio file
    """
    from video_orchestrator import VideoScript

    if not isinstance(script, VideoScript):
        raise TypeError("Expected VideoScript object")

    print(f"  Generating voiceover for: {script.id}")

    # Extract voice ID and language
    voice_id = script.narrator.voice_id or extract_voice_id(script.narrator.voice)
    language = getattr(script.narrator, 'language', None) or script.language

    # Create temp directory for segments
    temp_dir = AUDIO_DIR / ".temp" / script.id
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate audio for each scene
    segment_paths = []
    for i, scene in enumerate(script.scenes):
        if not scene.voiceover:
            # Generate silence for scenes without voiceover
            segment_path = temp_dir / f"{i:03d}_{scene.id}_silence.mp3"
            await generate_silence(segment_path, scene.duration * 0.3)  # Short silence
        else:
            segment_path = temp_dir / f"{i:03d}_{scene.id}.mp3"
            await generate_segment_audio(
                scene.voiceover,
                voice_id,
                segment_path,
                stability=script.narrator.stability,
                similarity_boost=script.narrator.similarity_boost,
                language=language
            )

        segment_paths.append(segment_path)

    # Concatenate all segments
    output_path = script.get_audio_path()
    await concatenate_audio(
        segment_paths,
        output_path,
        pause_between=script.narrator.pause_between_scenes
    )

    # Clean up temp files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"  Audio saved: {output_path}")
    return output_path


async def generate_voiceover_with_timing(script) -> tuple:
    """
    Generate voiceover with measured timing information.

    Enhanced version that measures actual audio durations and
    calculates intelligent pauses based on content.

    Args:
        script: VideoScript object with scenes and narrator config

    Returns:
        Tuple of (audio_path, list of AudioSegment with measured durations)
    """
    from video_orchestrator import VideoScript

    if not isinstance(script, VideoScript):
        raise TypeError("Expected VideoScript object")

    print(f"  Generating voiceover with timing for: {script.id}")

    # Extract voice ID and language
    voice_id = script.narrator.voice_id or extract_voice_id(script.narrator.voice)
    language = getattr(script.narrator, 'language', None) or script.language

    # Create temp directory for segments
    temp_dir = AUDIO_DIR / ".temp" / script.id
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate and measure each segment
    measured_segments = []
    segment_paths = []

    for i, scene in enumerate(script.scenes):
        segment_path = temp_dir / f"{i:03d}_{scene.id}.mp3"

        if not scene.voiceover:
            # Silent scene - generate minimal silence
            duration = 0.5  # Default silence duration
            await generate_silence(segment_path, duration)
        else:
            await generate_segment_audio(
                scene.voiceover,
                voice_id,
                segment_path,
                stability=script.narrator.stability,
                similarity_boost=script.narrator.similarity_boost,
                language=language
            )

        # ⭐ MEASURE DURATION
        measured_duration = measure_audio_duration(segment_path)

        measured_segments.append(AudioSegment(
            scene_id=scene.id,
            text=scene.voiceover or "",
            duration=measured_duration,
            audio_path=segment_path
        ))

        segment_paths.append(segment_path)
        print(f"    Scene '{scene.id}': {measured_duration:.1f}s")

    # Concatenate with intelligent pauses
    output_path = script.get_audio_path()

    # Build combined audio with calculated pauses
    try:
        from pydub import AudioSegment as PyAudioSegment
    except ImportError:
        raise ImportError(
            "pydub package not installed. Run: pip install pydub"
        )

    combined = PyAudioSegment.empty()

    for i, segment_path in enumerate(segment_paths):
        segment_audio = PyAudioSegment.from_mp3(str(segment_path))
        combined += segment_audio

        # Add calculated pause (not after last scene)
        if i < len(segment_paths) - 1:
            is_last = False
            pause_duration = calculate_pause_after(
                measured_segments[i].text,
                is_last
            )
            pause = PyAudioSegment.silent(duration=int(pause_duration * 1000))
            combined += pause
            print(f"    Pause after '{measured_segments[i].scene_id}': {pause_duration:.2f}s")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(output_path), format="mp3")

    # Clean up temp files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"  Audio saved: {output_path}")
    return output_path, measured_segments


# Fallback for systems without Eleven Labs
async def generate_voiceover_macos(script) -> Path:
    """
    Generate voiceover using macOS say command (fallback).

    Lower quality but free and works offline.
    """
    import subprocess
    import tempfile

    from video_orchestrator import VideoScript

    if not isinstance(script, VideoScript):
        raise TypeError("Expected VideoScript object")

    print(f"  Generating voiceover (macOS) for: {script.id}")

    # Determine voice based on language
    voice = "Samantha" if script.language == "en" else "Nora"

    temp_dir = Path(tempfile.mkdtemp())
    segment_paths = []

    for i, scene in enumerate(script.scenes):
        if not scene.voiceover:
            continue

        clean_text = clean_voiceover_text(scene.voiceover)
        if not clean_text:
            continue

        segment_path = temp_dir / f"{i:03d}.aiff"

        # Use macOS say command
        subprocess.run([
            'say',
            '-v', voice,
            '-o', str(segment_path),
            clean_text
        ], check=True)

        segment_paths.append(segment_path)

    # Convert and concatenate using ffmpeg
    output_path = script.get_audio_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if segment_paths:
        # Create file list for ffmpeg
        list_file = temp_dir / "files.txt"
        with open(list_file, 'w') as f:
            for path in segment_paths:
                f.write(f"file '{path}'\n")

        # Concatenate with ffmpeg
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c:a', 'libmp3lame',
            '-b:a', '192k',
            str(output_path)
        ], check=True, capture_output=True)

    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"  Audio saved: {output_path}")
    return output_path


def main():
    """Test voiceover generation."""
    import sys
    sys.path.insert(0, str(SCRIPT_DIR))

    from video_orchestrator import ScriptLoader

    loader = ScriptLoader()
    scripts = loader.load_all()

    if not scripts:
        print("No scripts found")
        return

    # Generate voiceover for first script
    script = scripts[0]
    print(f"Testing voiceover for: {script.id}")

    try:
        path = asyncio.run(generate_voiceover(script))
        print(f"Generated: {path}")
    except Exception as e:
        print(f"Eleven Labs failed: {e}")
        print("Trying macOS fallback...")
        try:
            path = asyncio.run(generate_voiceover_macos(script))
            print(f"Generated (macOS): {path}")
        except Exception as e2:
            print(f"macOS fallback also failed: {e2}")


if __name__ == "__main__":
    main()
