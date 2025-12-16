#!/usr/bin/env python3
"""
ROP Caption Generation

Generates WebVTT caption files from video scripts.

Features:
- WebVTT format output
- Scene-based timing calculation
- Caption styling support
- Optional voiceover text as captions

Usage:
    from captions import generate_webvtt
    caption_path = generate_webvtt(script)
"""

from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
CAPTIONS_DIR = PROJECT_ROOT / "docs" / "deliverables" / "assets" / "captions"


@dataclass
class CaptionEntry:
    """Represents a single caption entry."""
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    style: str = "default"


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as WebVTT timestamp.

    Format: HH:MM:SS.mmm
    Example: 00:01:23.456
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def generate_vtt_content(entries: List[CaptionEntry], title: str = "") -> str:
    """
    Generate WebVTT file content from caption entries.

    Args:
        entries: List of CaptionEntry objects
        title: Optional title/metadata

    Returns:
        WebVTT formatted string
    """
    lines = ["WEBVTT", ""]

    # Add metadata
    if title:
        lines.append(f"NOTE Title: {title}")
        lines.append("")

    # Add styling for caption types
    lines.extend([
        "STYLE",
        "::cue(.emphasis) {",
        "  color: #c45c3c;",
        "  font-weight: bold;",
        "}",
        "",
        "::cue(.warning) {",
        "  color: #b8860b;",
        "}",
        "",
        "::cue(.success) {",
        "  color: #2d6a4f;",
        "}",
        ""
    ])

    # Add caption entries
    for i, entry in enumerate(entries, 1):
        # Cue identifier
        lines.append(str(i))

        # Timestamp line
        start = format_timestamp(entry.start_time)
        end = format_timestamp(entry.end_time)
        lines.append(f"{start} --> {end}")

        # Caption text (with optional class for styling)
        if entry.style and entry.style != "default":
            lines.append(f"<c.{entry.style}>{entry.text}</c>")
        else:
            lines.append(entry.text)

        lines.append("")  # Blank line between entries

    return "\n".join(lines)


def extract_captions_from_script(script) -> List[CaptionEntry]:
    """
    Extract caption entries from a VideoScript.

    Combines explicit captions and optionally voiceover text.

    Args:
        script: VideoScript object

    Returns:
        List of CaptionEntry objects sorted by start time
    """
    from video_orchestrator import VideoScript

    if not isinstance(script, VideoScript):
        raise TypeError("Expected VideoScript object")

    entries = []
    cumulative_time = 0.0

    for scene in script.scenes:
        # Process explicit captions
        for caption in scene.captions:
            start_time = cumulative_time + caption.time

            # Calculate end time
            if caption.duration:
                end_time = start_time + caption.duration
            else:
                # Default: end when scene ends or 3 seconds, whichever is shorter
                remaining_in_scene = scene.duration - caption.time
                end_time = start_time + min(3.0, remaining_in_scene)

            entries.append(CaptionEntry(
                start_time=start_time,
                end_time=end_time,
                text=caption.text,
                style=caption.style
            ))

        cumulative_time += scene.duration

    # Sort by start time
    entries.sort(key=lambda e: e.start_time)

    return entries


def extract_voiceover_captions(script) -> List[CaptionEntry]:
    """
    Generate captions from voiceover text.

    Creates caption entries that show the spoken text.

    Args:
        script: VideoScript object

    Returns:
        List of CaptionEntry objects
    """
    from video_orchestrator import VideoScript

    if not isinstance(script, VideoScript):
        raise TypeError("Expected VideoScript object")

    entries = []
    cumulative_time = 0.0

    for scene in script.scenes:
        if scene.voiceover:
            # Clean voiceover text
            text = scene.voiceover.strip()

            # Split into sentences for better readability
            sentences = split_into_sentences(text)

            # Distribute sentences across scene duration
            if sentences:
                duration_per_sentence = scene.duration / len(sentences)
                for i, sentence in enumerate(sentences):
                    start_time = cumulative_time + (i * duration_per_sentence)
                    end_time = start_time + duration_per_sentence

                    entries.append(CaptionEntry(
                        start_time=start_time,
                        end_time=end_time,
                        text=sentence.strip()
                    ))

        cumulative_time += scene.duration

    return entries


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences for caption display."""
    import re

    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def generate_webvtt(script, include_voiceover: bool = False) -> Path:
    """
    Generate WebVTT caption file from script.

    Args:
        script: VideoScript object
        include_voiceover: If True, include voiceover text as captions

    Returns:
        Path to generated .vtt file
    """
    from video_orchestrator import VideoScript

    if not isinstance(script, VideoScript):
        raise TypeError("Expected VideoScript object")

    print(f"  Generating captions for: {script.id}")

    # Extract caption entries
    entries = extract_captions_from_script(script)

    # Optionally add voiceover-based captions
    if include_voiceover:
        voiceover_entries = extract_voiceover_captions(script)
        entries.extend(voiceover_entries)
        entries.sort(key=lambda e: e.start_time)

    # Generate VTT content
    vtt_content = generate_vtt_content(entries, title=script.title)

    # Write to file
    output_path = script.get_caption_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(vtt_content)

    print(f"  Captions saved: {output_path}")
    return output_path


def generate_voiceover_vtt(script) -> Path:
    """
    Generate WebVTT file using voiceover text as captions.

    Useful for accessibility when explicit captions aren't defined.

    Args:
        script: VideoScript object

    Returns:
        Path to generated .vtt file
    """
    return generate_webvtt(script, include_voiceover=True)


def generate_webvtt_from_manifest(script, timing_manifest) -> Path:
    """
    Generate WebVTT captions using measured timing manifest.

    Uses actual measured durations from audio instead of YAML scene
    durations. This ensures captions are perfectly synchronized with
    the actual voiceover audio.

    Args:
        script: VideoScript object
        timing_manifest: TimingManifest with measured timings

    Returns:
        Path to generated .vtt file
    """
    print(f"  Generating captions from timing manifest: {script.id}")

    entries = []

    for scene in script.scenes:
        timing = timing_manifest.get_scene_timing(scene.id)
        cumulative_start = timing.cumulative_start

        # Process explicit captions
        for caption in scene.captions:
            start_time = cumulative_start + caption.time

            if caption.duration:
                end_time = start_time + caption.duration
            else:
                # Default: use voiceover duration or 3s, whichever is shorter
                remaining = timing.voiceover_duration - caption.time
                end_time = start_time + min(3.0, max(0.1, remaining))

            entries.append(CaptionEntry(
                start_time=start_time,
                end_time=end_time,
                text=caption.text,
                style=caption.style
            ))

    entries.sort(key=lambda e: e.start_time)

    # Generate VTT content
    vtt_content = generate_vtt_content(entries, title=script.title)

    # Write to file
    output_path = script.get_caption_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(vtt_content)

    print(f"  Captions saved: {output_path}")
    return output_path


def validate_vtt(vtt_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a WebVTT file.

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    if not vtt_path.exists():
        return False, ["File does not exist"]

    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Check header
    if not lines or not lines[0].strip().startswith('WEBVTT'):
        issues.append("Missing WEBVTT header")

    # Check for timing issues
    import re
    timestamp_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})'

    last_end_time = 0.0
    for i, line in enumerate(lines):
        match = re.match(timestamp_pattern, line)
        if match:
            start_str, end_str = match.groups()

            # Parse timestamps
            start = parse_timestamp(start_str)
            end = parse_timestamp(end_str)

            # Check for invalid timing
            if start >= end:
                issues.append(f"Line {i+1}: Start time >= end time")

            if start < last_end_time:
                issues.append(f"Line {i+1}: Overlapping captions")

            last_end_time = end

    return len(issues) == 0, issues


def parse_timestamp(ts: str) -> float:
    """Parse WebVTT timestamp to seconds."""
    parts = ts.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    return hours * 3600 + minutes * 60 + seconds


def main():
    """Test caption generation."""
    import sys
    sys.path.insert(0, str(SCRIPT_DIR))

    from video_orchestrator import ScriptLoader

    loader = ScriptLoader()
    scripts = loader.load_all()

    if not scripts:
        print("No scripts found")
        return

    # Generate captions for all scripts
    for script in scripts:
        try:
            path = generate_webvtt(script)
            print(f"Generated: {path}")

            # Validate
            is_valid, issues = validate_vtt(path)
            if not is_valid:
                print(f"  Validation issues:")
                for issue in issues:
                    print(f"    - {issue}")
        except Exception as e:
            print(f"Failed for {script.id}: {e}")


if __name__ == "__main__":
    main()
