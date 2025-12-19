#!/usr/bin/env python3
"""
Pikkolo Demo Video Capture System

Captures demo videos using Playwright's built-in video recording.
Supports scripted scenes with JavaScript actions executed at specific timings.
Videos are used in presentations, documentation, and marketing.

Usage:
    python video_capture.py                    # Capture all videos
    python video_capture.py --video highlight  # Capture specific video
    python video_capture.py --list             # List available videos
    python video_capture.py --lang en          # Capture only English
    python video_capture.py --script           # Use script YAML files
"""

import argparse
import asyncio
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

try:
    from PIL import Image
except ImportError:
    Image = None

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent

# Look for manifest in priority order:
# 1. Current directory (project-specific)
# 2. docs/deliverables/video/ (project deliverables)
# 3. Module directory (fallback)
MANIFEST_SEARCH_PATHS = [
    Path.cwd() / "video_manifest.yaml",
    Path.cwd() / "docs" / "deliverables" / "video" / "video_manifest.yaml",
    SCRIPT_DIR / "video_manifest.yaml",
]


@dataclass
class SceneAction:
    """A single scene action in a video script."""

    id: str
    name: str
    duration: float  # seconds
    action: Optional[str] = None  # JavaScript to execute
    voiceover: Optional[str] = None


@dataclass
class VideoScript:
    """A complete video script with scenes."""

    id: str
    title: str
    language: str
    demo_url: str
    duration: float  # total duration in seconds
    scenes: List[SceneAction] = field(default_factory=list)
    output_filename: str = ""

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "VideoScript":
        """Load a video script from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        scenes = []
        for scene_data in data.get("scenes", []):
            scenes.append(
                SceneAction(
                    id=scene_data.get("id", ""),
                    name=scene_data.get("name", ""),
                    duration=float(scene_data.get("duration", 3)),
                    action=scene_data.get("action"),
                    voiceover=scene_data.get("voiceover"),
                )
            )

        return cls(
            id=data.get("id", yaml_path.stem),
            title=data.get("title", ""),
            language=data.get("language", "en"),
            demo_url=data.get("demo_url", ""),
            duration=float(data.get("duration", sum(s.duration for s in scenes))),
            scenes=scenes,
            output_filename=data.get("output", {}).get("filename", f"{yaml_path.stem}.mp4"),
        )


@dataclass
class VideoResult:
    """Result of a video capture."""

    video_id: str
    language: str
    success: bool
    output_path: Optional[Path] = None
    poster_path: Optional[Path] = None
    error: Optional[str] = None


def find_manifest() -> Path:
    """Find the video manifest file."""
    for path in MANIFEST_SEARCH_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Video manifest not found. Searched:\n  " + "\n  ".join(str(p) for p in MANIFEST_SEARCH_PATHS)
    )


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the video manifest."""
    manifest_file = manifest_path or find_manifest()
    print(f"Using manifest: {manifest_file}")

    with open(manifest_file, "r") as f:
        manifest = yaml.safe_load(f)

    # Set project root based on manifest location
    manifest["_project_root"] = manifest_file.parent.parent.parent.parent
    manifest["_manifest_dir"] = manifest_file.parent
    return manifest


def discover_scripts(manifest: Dict[str, Any], language: str) -> List[VideoScript]:
    """Discover video scripts from the scripts directory."""
    scripts_dir = manifest.get("scripts_dir", "scripts")
    manifest_dir = manifest.get("_manifest_dir", Path.cwd())
    scripts_path = manifest_dir / scripts_dir / language

    if not scripts_path.exists():
        print(f"  ⚠ Scripts directory not found: {scripts_path}")
        return []

    scripts = []
    for yaml_file in scripts_path.glob("*.yaml"):
        try:
            script = VideoScript.from_yaml(yaml_file)
            scripts.append(script)
            print(f"  → Discovered script: {script.id} ({len(script.scenes)} scenes)")
        except Exception as e:
            print(f"  ⚠ Failed to load {yaml_file}: {e}")

    return scripts


async def capture_scripted_video(
    script: VideoScript,
    manifest: Dict[str, Any],
    force: bool = False,
) -> VideoResult:
    """Capture a video using scripted scenes with JavaScript actions."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return VideoResult(
            video_id=script.id,
            language=script.language,
            success=False,
            error="Playwright not installed. Run: pip install playwright && playwright install chromium",
        )

    # Construct output paths
    project_root = manifest.get("_project_root", PROJECT_ROOT)
    output_base = Path(manifest.get("output_base", "docs/deliverables/assets/videos"))
    output_dir = project_root / output_base / script.language
    output_dir.mkdir(parents=True, exist_ok=True)

    video_output = output_dir / script.output_filename

    # Skip if exists and not forcing
    if video_output.exists() and not force:
        print(f"  ⊙ Already exists: {video_output}")
        return VideoResult(
            video_id=script.id, language=script.language, success=True, output_path=video_output
        )

    try:
        async with async_playwright() as p:
            # Launch browser with video recording
            browser = await p.chromium.launch(headless=True)

            # Get video settings
            video_settings = manifest.get("video_settings", {})
            resolution = video_settings.get("resolution", {"width": 1920, "height": 1080})

            # Create context with video recording
            context = await browser.new_context(
                viewport=resolution,
                record_video_dir=str(output_dir / "temp"),
                record_video_size=resolution,
            )

            page = await context.new_page()

            # Construct demo URL from script's demo_url
            manifest_dir = manifest.get("_manifest_dir", Path.cwd())
            demo_base = manifest_dir.parent / "demo"  # docs/deliverables/demo

            # Handle relative demo_url (e.g., "demo/no/interactive-demo.html")
            if script.demo_url.startswith("demo/"):
                demo_path = manifest_dir.parent / script.demo_url
            else:
                demo_path = demo_base / script.demo_url

            url = f"file://{demo_path}?mode=record"

            print(f"  → Loading: {url}")
            await page.goto(url, wait_until="networkidle")

            # Initial wait for page to settle
            await page.wait_for_timeout(500)

            # Execute each scene
            total_scenes = len(script.scenes)
            for i, scene in enumerate(script.scenes):
                print(f"  → Scene {i + 1}/{total_scenes}: {scene.name} ({scene.duration}s)")

                # Execute scene action if present
                if scene.action:
                    try:
                        # Execute JavaScript in the page context
                        await page.evaluate(scene.action)
                    except Exception as e:
                        print(f"    ⚠ Action failed: {e}")

                # Wait for scene duration (convert to ms)
                await page.wait_for_timeout(int(scene.duration * 1000))

            # Close page and context to finalize video
            await page.close()
            await context.close()
            await browser.close()

            # Move video from temp to final location
            temp_dir = output_dir / "temp"
            video_files = list(temp_dir.glob("*.webm"))

            if not video_files:
                return VideoResult(
                    video_id=script.id,
                    language=script.language,
                    success=False,
                    error="No video file generated by Playwright",
                )

            temp_video = video_files[0]

            # Convert WebM to MP4 using ffmpeg if available
            video_output = await convert_to_mp4(temp_video, video_output)

            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            # Generate poster image if requested
            poster_path = None
            if manifest.get("build", {}).get("generate_posters", True):
                poster_path = await generate_poster(video_output, output_dir, script.id)

            return VideoResult(
                video_id=script.id,
                language=script.language,
                success=True,
                output_path=video_output,
                poster_path=poster_path,
            )

    except Exception as e:
        import traceback

        return VideoResult(
            video_id=script.id,
            language=script.language,
            success=False,
            error=f"{str(e)}\n{traceback.format_exc()}",
        )


async def convert_to_mp4(input_path: Path, output_path: Path) -> Path:
    """Convert WebM to MP4 using ffmpeg if available."""
    try:
        import subprocess

        # Check if ffmpeg is installed
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)

        # Convert to MP4 - High quality 1080p60
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(input_path),
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "18",
                "-profile:v",
                "high",
                "-level",
                "4.2",
                "-r",
                "60",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-y",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )

        print(f"  ✓ Converted to MP4: {output_path}")
        return output_path

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: Just move the WebM file
        print("  ⚠ ffmpeg not available, keeping WebM format")
        webm_output = output_path.with_suffix(".webm")
        shutil.move(str(input_path), str(webm_output))
        return webm_output


async def capture_video(
    video_id: str,
    video_config: Dict[str, Any],
    manifest: Dict[str, Any],
    language: str = "en",
    force: bool = False,
) -> VideoResult:
    """Capture a single demo video using Playwright (simple mode without scene actions)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return VideoResult(
            video_id=video_id,
            language=language,
            success=False,
            error="Playwright not installed. Run: pip install playwright && playwright install chromium",
        )

    # Construct output paths
    project_root = manifest.get("_project_root", PROJECT_ROOT)
    output_base = Path(manifest.get("output_base", "docs/deliverables/assets/videos"))
    output_dir = project_root / output_base / language
    output_dir.mkdir(parents=True, exist_ok=True)

    video_output = output_dir / video_config["output"]

    # Skip if exists and not forcing
    if video_output.exists() and not force:
        print(f"  ⊙ Already exists: {video_output}")
        return VideoResult(
            video_id=video_id, language=language, success=True, output_path=video_output
        )

    try:
        async with async_playwright() as p:
            # Launch browser with video recording
            browser = await p.chromium.launch(headless=True)

            # Get video settings
            video_settings = manifest.get("video_settings", {})
            resolution = video_settings.get("resolution", {"width": 1920, "height": 1080})

            # Create context with video recording
            context = await browser.new_context(
                viewport=resolution,
                record_video_dir=str(output_dir / "temp"),
                record_video_size=resolution,
            )

            page = await context.new_page()

            # Construct demo URL
            manifest_dir = manifest.get("_manifest_dir", Path.cwd())
            demo_base = manifest_dir.parent / "demo"

            # Use demo_url from config if present, otherwise construct from language
            demo_url = video_config.get("demo_url", f"{language}/index.html")
            if demo_url.startswith("demo/"):
                demo_path = manifest_dir.parent / demo_url
            else:
                demo_path = demo_base / demo_url

            url = f"file://{demo_path}?mode=record"

            # Add chapter parameter if specified
            if video_config.get("chapter"):
                url += f"&chapter={video_config['chapter']}"

            print(f"  → Loading: {url}")
            await page.goto(url, wait_until="networkidle")

            # Wait for demo to complete
            duration = video_config.get("duration", 180000)
            print(f"  → Recording for {duration / 1000:.1f}s...")
            await page.wait_for_timeout(duration)

            # Close page and context to finalize video
            await page.close()
            await context.close()
            await browser.close()

            # Move video from temp to final location
            temp_dir = output_dir / "temp"
            video_files = list(temp_dir.glob("*.webm"))

            if not video_files:
                return VideoResult(
                    video_id=video_id,
                    language=language,
                    success=False,
                    error="No video file generated by Playwright",
                )

            temp_video = video_files[0]

            # Convert WebM to MP4
            video_output = await convert_to_mp4(temp_video, video_output)

            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            # Generate poster image if requested
            poster_path = None
            if manifest.get("build", {}).get("generate_posters", True):
                poster_path = await generate_poster(video_output, output_dir, video_id)

            return VideoResult(
                video_id=video_id,
                language=language,
                success=True,
                output_path=video_output,
                poster_path=poster_path,
            )

    except Exception as e:
        import traceback

        return VideoResult(
            video_id=video_id,
            language=language,
            success=False,
            error=f"{str(e)}\n{traceback.format_exc()}",
        )


async def generate_poster(video_path: Path, output_dir: Path, video_id: str) -> Optional[Path]:
    """Generate a poster image from the first frame of the video."""
    try:
        import subprocess

        poster_path = output_dir / f"{video_id}-poster.jpg"

        # Extract frame at 1 second using ffmpeg
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(video_path),
                "-ss",
                "00:00:01.000",  # 1 second in
                "-vframes",
                "1",
                "-q:v",
                "2",  # High quality
                "-y",
                str(poster_path),
            ],
            check=True,
            capture_output=True,
        )

        print(f"  ✓ Generated poster: {poster_path}")
        return poster_path

    except Exception as e:
        print(f"  ⚠ Failed to generate poster: {e}")
        return None


async def capture_all_videos(
    video_ids: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    force: bool = False,
    use_scripts: bool = False,
) -> List[VideoResult]:
    """Capture multiple videos, optionally in parallel.

    Args:
        video_ids: Specific video IDs to capture (or None for all)
        languages: Languages to capture (or None for all configured)
        force: Force regeneration even if files exist
        use_scripts: Use script YAML files with scene actions
    """
    manifest = load_manifest()

    # Get configuration
    default_languages = manifest.get("languages", ["en"])
    languages = languages or default_languages

    results = []
    max_concurrent = manifest.get("build", {}).get("max_concurrent", 2)

    if use_scripts:
        # Scripted mode: discover and execute script YAMLs
        print("\n[Script Mode] Discovering video scripts...")

        tasks = []
        for language in languages:
            scripts = discover_scripts(manifest, language)

            # Filter by video_ids if specified
            if video_ids:
                scripts = [s for s in scripts if s.id in video_ids or s.output_filename.replace(".mp4", "") in video_ids]

            for script in scripts:
                tasks.append(script)

        if not tasks:
            print("  ⚠ No scripts found to capture")
            return results

        print(f"\nFound {len(tasks)} scripts to capture")

        # Process scripts (one at a time for stability)
        for i, script in enumerate(tasks):
            print(f"\n=== Capturing {i + 1}/{len(tasks)}: {script.id} ({script.language}) ===")

            result = await capture_scripted_video(script, manifest, force)
            results.append(result)

            if result.success:
                print(f"✓ {result.language.upper()}/{result.video_id}: {result.output_path}")
            else:
                print(f"✗ {result.language.upper()}/{result.video_id}: {result.error}")

    else:
        # Simple mode: use manifest videos dict
        all_videos = manifest.get("videos", {})

        # Filter videos if specific ones requested
        if video_ids:
            all_videos = {k: v for k, v in all_videos.items() if k in video_ids}

        if not all_videos:
            print("  ⚠ No videos configured in manifest")
            return results

        # Sort by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_videos = sorted(
            all_videos.items(), key=lambda x: priority_order.get(x[1].get("priority", "medium"), 1)
        )

        # Create tasks for all language/video combinations
        tasks = []
        for video_id, video_config in sorted_videos:
            for language in languages:
                tasks.append((video_id, video_config, language))

        # Process in batches for controlled concurrency
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i : i + max_concurrent]

            print(f"\n=== Processing batch {i // max_concurrent + 1} ===")

            # Run batch in parallel
            batch_results = await asyncio.gather(
                *[
                    capture_video(video_id, config, manifest, lang, force)
                    for video_id, config, lang in batch
                ]
            )

            results.extend(batch_results)

            # Report batch results
            for result in batch_results:
                if result.success:
                    print(f"✓ {result.language.upper()}/{result.video_id}: {result.output_path}")
                else:
                    print(f"✗ {result.language.upper()}/{result.video_id}: {result.error}")

    return results


def list_videos():
    """List all available videos from manifest and script files."""
    manifest = load_manifest()

    print("\nAvailable Demo Videos (from manifest):")
    print("=" * 70)

    videos = manifest.get("videos", {})
    if videos:
        for video_id, config in videos.items():
            print(f"\n  {video_id}")
            print(f"    Description: {config.get('description', 'N/A')}")
            print(f"    Duration: {config.get('duration', 0) / 1000:.1f}s")
            print(f"    Output: {config.get('output', 'N/A')}")
            print(f"    Priority: {config.get('priority', 'medium')}")
            if config.get("chapter"):
                print(f"    Chapter: {config['chapter']}")
            if config.get("use_in"):
                print(f"    Use in: {', '.join(config['use_in'][:2])}")
    else:
        print("  (No videos in manifest)")

    # Also show discovered scripts
    print("\n\nDiscovered Script Files:")
    print("=" * 70)

    languages = manifest.get("languages", ["en"])
    for lang in languages:
        scripts = discover_scripts(manifest, lang)
        if scripts:
            print(f"\n  {lang.upper()}:")
            for script in scripts:
                print(f"    {script.id}")
                print(f"      Title: {script.title}")
                print(f"      Duration: {script.duration:.1f}s ({len(script.scenes)} scenes)")
                print(f"      Output: {script.output_filename}")
                print(f"      Demo URL: {script.demo_url}")


def main():
    parser = argparse.ArgumentParser(description="Capture demo videos using Playwright")
    parser.add_argument("--video", "-v", action="append", help="Specific video(s) to capture")
    parser.add_argument(
        "--lang", action="append", help="Specific language(s) to capture (e.g., en, no)"
    )
    parser.add_argument("--list", "-l", action="store_true", help="List available videos")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force regeneration even if files exist"
    )
    parser.add_argument(
        "--script", "-s", action="store_true",
        help="Use script YAML files with scene actions (from scripts/{lang}/ directory)"
    )

    args = parser.parse_args()

    if args.list:
        list_videos()
        return

    # Capture videos
    print("\n" + "=" * 70)
    print("Pikkolo Demo Video Capture")
    print("=" * 70)

    if args.script:
        print("Mode: Scripted (executing scene actions from YAML)")
    else:
        print("Mode: Simple (recording for fixed duration)")

    results = asyncio.run(capture_all_videos(args.video, args.lang, args.force, args.script))

    # Summary
    print(f"\n{'=' * 70}")
    success = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    print(f"Videos captured: {success}")
    if failed:
        print(f"Failed: {failed}")
        print("\nFailed videos:")
        for r in results:
            if not r.success:
                print(f"  - {r.language}/{r.video_id}: {r.error[:100]}...")

    # Check for required tools
    print(f"\n{'=' * 70}")
    print("System check:")

    try:
        import subprocess

        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("  ✓ ffmpeg installed (MP4 conversion available)")
    except:
        print("  ⚠ ffmpeg not installed (videos will be in WebM format)")
        print("    Install: brew install ffmpeg  # macOS")
        print("             apt install ffmpeg   # Ubuntu")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
