"""
Scene Capture Engine

Captures individual video clips per scene based on named demo states.
Each scene gets a fresh browser instance for reliability and independence.

Usage:
    engine = SceneCaptureEngine(project)
    clips = await engine.capture_all_scenes(script, demo_registry)
    # Returns dict mapping scene_id -> clip_path
"""

import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .demo_registry import DemoDefinition, DemoRegistry, DemoState

if TYPE_CHECKING:
    from ..core.project import Project
    from .builder import VideoScene, VideoScript


@dataclass
class SceneCaptureConfig:
    """Configuration for scene capture."""

    width: int = 1920
    height: int = 1080
    fps: int = 60
    crf: int = 18  # Quality (lower = better)
    headless: bool = True
    timeout_ms: int = 5000  # Max wait for selectors (5 seconds)


@dataclass
class SceneCaptureResult:
    """Result of capturing a single scene."""

    scene_id: str
    success: bool
    clip_path: Optional[Path] = None
    duration: float = 0.0
    error: Optional[str] = None


class SceneCaptureEngine:
    """
    Captures individual video clips per scene based on named demo states.

    Each scene is captured independently with a fresh browser for reliability.
    The capture duration is driven by voiceover timing for perfect sync.
    """

    def __init__(
        self,
        project: "Project" = None,
        config: SceneCaptureConfig = None,
    ):
        self.project = project
        self.config = config or SceneCaptureConfig()
        self.demo_registry = DemoRegistry(project)

    async def capture_scene(
        self,
        demo: DemoDefinition,
        state: DemoState,
        duration: float,
        output_path: Path,
    ) -> SceneCaptureResult:
        """
        Capture a single scene's video clip.

        Args:
            demo: Demo definition with URL
            state: Target state to reach and record
            duration: Recording duration in seconds (from voiceover)
            output_path: Where to save the final MP4

        Returns:
            SceneCaptureResult with clip path or error
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return SceneCaptureResult(
                scene_id=state.name,
                success=False,
                error="Playwright not installed. Run: pip install playwright && playwright install chromium",
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = output_path.parent / f".temp_{state.name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            async with async_playwright() as p:
                # Launch fresh browser for this scene
                browser = await p.chromium.launch(headless=self.config.headless)

                # Create context with video recording
                viewport = demo.viewport or {"width": self.config.width, "height": self.config.height}
                context = await browser.new_context(
                    viewport=viewport,
                    record_video_dir=str(temp_dir),
                    record_video_size=viewport,
                )

                page = await context.new_page()

                # Navigate to demo URL
                url = self._resolve_url(demo.url)
                await page.goto(url, wait_until="networkidle")

                # Small settle time
                await page.wait_for_timeout(200)

                # Execute state setup if present
                if state.setup:
                    try:
                        await page.evaluate(state.setup)
                    except Exception as e:
                        print(f"    Warning: State setup failed: {e}")

                # Wait for element if specified
                if state.wait_for:
                    try:
                        await page.wait_for_selector(
                            state.wait_for,
                            timeout=self.config.timeout_ms,
                            state="visible",
                        )
                    except Exception as e:
                        print(f"    Warning: wait_for selector timeout: {e}")

                # Small settle time after state transition
                await page.wait_for_timeout(300)

                # Record for the exact scene duration
                duration_ms = int(duration * 1000)
                await page.wait_for_timeout(duration_ms)

                # Close everything to finalize video
                await page.close()
                await context.close()
                await browser.close()

            # Find the recorded WebM file
            video_files = list(temp_dir.glob("*.webm"))
            if not video_files:
                return SceneCaptureResult(
                    scene_id=state.name,
                    success=False,
                    error="No video file generated by Playwright",
                )

            # Convert to MP4
            temp_video = video_files[0]
            final_path = await self._convert_to_mp4(temp_video, output_path)

            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

            return SceneCaptureResult(
                scene_id=state.name,
                success=True,
                clip_path=final_path,
                duration=duration,
            )

        except Exception as e:
            # Cleanup on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            return SceneCaptureResult(
                scene_id=state.name,
                success=False,
                error=str(e),
            )

    async def capture_all_scenes(
        self,
        script: "VideoScript",
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Capture clips for all scenes that have demo states.

        Args:
            script: Video script with scenes
            output_dir: Directory to save clips

        Returns:
            Dict mapping scene_id to clip path
        """
        clips = {}
        scenes_dir = output_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        # Collect scenes with demo references
        demo_scenes = []
        for scene in script.scenes:
            demo_ref = self._get_scene_demo(scene)
            if demo_ref:
                demo_scenes.append((scene, demo_ref))

        if not demo_scenes:
            return clips

        print(f"  Capturing {len(demo_scenes)} scene clips...")

        for i, (scene, demo_ref) in enumerate(demo_scenes):
            print(f"  [{i + 1}/{len(demo_scenes)}] Scene '{scene.id}': state '{demo_ref['state']}'")

            # Load demo definition
            try:
                demo = self.demo_registry.load(demo_ref["source"], script.language)
                state = demo.get_state(demo_ref["state"])
            except (FileNotFoundError, KeyError) as e:
                print(f"    Error: {e}")
                continue

            # Use scene duration (set from voiceover timing)
            duration = scene.duration or 3.0
            output_path = scenes_dir / f"{scene.id}.mp4"

            result = await self.capture_scene(demo, state, duration, output_path)

            if result.success:
                clips[scene.id] = result.clip_path
                print(f"    Captured: {result.clip_path} ({result.duration:.2f}s)")
            else:
                print(f"    Failed: {result.error}")

        return clips

    def _get_scene_demo(self, scene: "VideoScene") -> Optional[dict]:
        """Extract demo reference from scene if present."""
        # Check for demo reference in scene
        demo_ref = scene.visual.get("demo")
        if demo_ref and isinstance(demo_ref, dict):
            if "source" in demo_ref and "state" in demo_ref:
                return demo_ref
        return None

    def _resolve_url(self, url: str) -> str:
        """Resolve demo URL to full path."""
        if url.startswith(("http://", "https://", "file://")):
            return url

        # Relative path - resolve against project
        if self.project:
            demo_path = self.project.root / url
            if demo_path.exists():
                return f"file://{demo_path}"

        # Try current directory
        cwd_path = Path.cwd() / url
        if cwd_path.exists():
            return f"file://{cwd_path}"

        # Assume it's a URL as-is
        return url

    async def _convert_to_mp4(self, input_path: Path, output_path: Path) -> Path:
        """Convert WebM to high-quality MP4."""
        try:
            # Check if ffmpeg is available
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)

            # Convert to MP4 with high quality settings
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(input_path),
                    "-c:v", "libx264",
                    "-preset", "slow",
                    "-crf", str(self.config.crf),
                    "-profile:v", "high",
                    "-level", "4.2",
                    "-r", str(self.config.fps),
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    "-y",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
            return output_path

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: keep WebM format
            webm_output = output_path.with_suffix(".webm")
            shutil.move(str(input_path), str(webm_output))
            return webm_output


async def capture_scene_clips(
    script: "VideoScript",
    output_dir: Path,
    project: "Project" = None,
) -> dict[str, Path]:
    """
    Convenience function to capture scene clips.

    Args:
        script: Video script with scenes
        output_dir: Output directory
        project: Optional Project for configuration

    Returns:
        Dict mapping scene_id to clip path
    """
    engine = SceneCaptureEngine(project=project)
    return await engine.capture_all_scenes(script, output_dir)
