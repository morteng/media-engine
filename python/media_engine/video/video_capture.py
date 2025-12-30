"""
Video Capture Module

Records real browser interactions as video using Playwright's native video recording.
Unlike screenshot-based capture, this records actual browser rendering including:
- Smooth scrolling animations
- Click interactions with visual feedback
- Typing animations
- Hover effects and transitions
- CSS animations and transitions

Usage:
    from media_engine.video.video_capture import VideoCaptureEngine

    async with VideoCaptureEngine() as engine:
        result = await engine.capture_state(
            url="http://localhost:8080",
            state=state,
            output_path=Path("output/demo.webm"),
        )

Features:
- Native Playwright video recording (WebM format)
- Optional cursor overlay for visual feedback
- Action execution during recording
- Automatic format conversion to MP4
- Integration with VideoProject components
"""

import asyncio
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page


@dataclass
class RecordingConfig:
    """Configuration for video recording."""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    include_cursor: bool = True
    cursor_color: str = "rgba(0, 212, 255, 0.8)"
    cursor_size: int = 20
    output_format: str = "mp4"  # "webm" or "mp4"
    quality: str = "high"  # "low", "medium", "high"


@dataclass
class CaptureResult:
    """Result of a video capture operation."""
    success: bool
    output_path: Optional[Path] = None
    duration: float = 0.0
    frames: int = 0
    error: Optional[str] = None
    captured_at: datetime = field(default_factory=datetime.now)

    @property
    def file_size(self) -> int:
        """Get the output file size in bytes."""
        if self.output_path and self.output_path.exists():
            return self.output_path.stat().st_size
        return 0


class VideoCaptureEngine:
    """
    Engine for capturing browser interactions as video.

    Uses Playwright's native video recording for smooth, accurate captures
    of browser interactions including scrolling, clicks, and animations.
    """

    def __init__(
        self,
        config: Optional[RecordingConfig] = None,
        headless: bool = True,
    ):
        self.config = config or RecordingConfig()
        self.headless = headless
        self._playwright = None
        self._browser: Optional["Browser"] = None

    async def __aenter__(self):
        """Start Playwright browser."""
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _create_recording_context(
        self,
        video_dir: Path,
    ) -> "BrowserContext":
        """Create a browser context with video recording enabled."""
        if not self._browser:
            raise RuntimeError("Browser not started. Use 'async with' context manager.")

        video_dir.mkdir(parents=True, exist_ok=True)

        context = await self._browser.new_context(
            viewport={"width": self.config.width, "height": self.config.height},
            record_video_dir=str(video_dir),
            record_video_size={"width": self.config.width, "height": self.config.height},
        )

        return context

    async def _inject_cursor(self, page: "Page"):
        """Inject a visible cursor element for visual feedback."""
        if not self.config.include_cursor:
            return

        await page.evaluate(f"""
            (() => {{
                // Remove existing cursor if present
                document.getElementById('video-capture-cursor')?.remove();

                // Create cursor element
                const cursor = document.createElement('div');
                cursor.id = 'video-capture-cursor';
                cursor.style.cssText = `
                    position: fixed;
                    width: {self.config.cursor_size}px;
                    height: {self.config.cursor_size}px;
                    border-radius: 50%;
                    background: {self.config.cursor_color};
                    box-shadow: 0 0 15px {self.config.cursor_color};
                    pointer-events: none;
                    z-index: 999999;
                    transform: translate(-50%, -50%);
                    transition: transform 0.1s ease-out, opacity 0.2s;
                    left: 50%;
                    top: 50%;
                    opacity: 0;
                `;
                document.body.appendChild(cursor);

                // Track mouse movement
                document.addEventListener('mousemove', (e) => {{
                    cursor.style.left = e.clientX + 'px';
                    cursor.style.top = e.clientY + 'px';
                    cursor.style.opacity = '1';
                }});

                // Click effect
                document.addEventListener('mousedown', () => {{
                    cursor.style.transform = 'translate(-50%, -50%) scale(0.8)';
                }});
                document.addEventListener('mouseup', () => {{
                    cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                }});
            }})()
        """)

    async def _remove_cursor(self, page: "Page"):
        """Remove the injected cursor element."""
        await page.evaluate("""
            document.getElementById('video-capture-cursor')?.remove();
        """)

    async def _convert_to_mp4(self, webm_path: Path, mp4_path: Path) -> bool:
        """Convert WebM to MP4 using ffmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(webm_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "medium",
                "-crf", "23" if self.config.quality == "high" else "28",
                "-movflags", "+faststart",
                str(mp4_path),
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            print(f"FFmpeg conversion failed: {e}")
            return False

    async def capture_state(
        self,
        url: str,
        setup_js: Optional[str] = None,
        actions_js: Optional[str] = None,
        wait_for: str = "body",
        duration: float = 5.0,
        output_path: Optional[Path] = None,
    ) -> CaptureResult:
        """
        Capture a single state as video.

        Args:
            url: URL to navigate to
            setup_js: JavaScript to run before recording
            actions_js: JavaScript actions to execute during recording
            wait_for: CSS selector to wait for before starting
            duration: Recording duration in seconds
            output_path: Where to save the final video

        Returns:
            CaptureResult with output path and metadata
        """
        if not self._browser:
            raise RuntimeError("Browser not started. Use 'async with' context manager.")

        # Create temp directory for video recording
        temp_dir = Path("/tmp/video_capture_temp") / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        context = None
        page = None

        try:
            # Create recording context
            context = await self._create_recording_context(temp_dir)
            page = await context.new_page()

            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for target element
            try:
                await page.wait_for_selector(wait_for, timeout=10000)
            except Exception as e:
                print(f"Warning: wait_for '{wait_for}' timeout: {e}")

            # Small delay for initial render
            await asyncio.sleep(0.5)

            # Execute setup JavaScript
            if setup_js:
                await page.evaluate(f"""
                    (async () => {{
                        {setup_js}
                    }})()
                """)
                await asyncio.sleep(0.3)

            # Inject cursor overlay
            await self._inject_cursor(page)

            # Execute actions during recording
            if actions_js:
                # Run actions in background while waiting
                actions_task = asyncio.create_task(
                    page.evaluate(f"""
                        (async () => {{
                            const duration = {duration * 1000};
                            const startTime = Date.now();

                            // Helper functions
                            const wait = (ms) => new Promise(r => setTimeout(r, ms));
                            const elapsed = () => Date.now() - startTime;
                            const progress = () => Math.min(elapsed() / duration, 1);

                            // Smooth scroll helper
                            const smoothScroll = async (target, distance, dur = 1000) => {{
                                const el = typeof target === 'string' ? document.querySelector(target) : target;
                                if (!el) return;
                                const start = el.scrollTop;
                                const startTime = Date.now();
                                while (Date.now() - startTime < dur) {{
                                    const t = (Date.now() - startTime) / dur;
                                    const eased = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2, 2)/2;
                                    el.scrollTop = start + distance * eased;
                                    await wait(16);
                                }}
                                el.scrollTop = start + distance;
                            }};

                            // Move cursor helper
                            const moveTo = async (x, y, dur = 500) => {{
                                const cursor = document.getElementById('video-capture-cursor');
                                if (!cursor) return;
                                const startX = parseFloat(cursor.style.left) || window.innerWidth/2;
                                const startY = parseFloat(cursor.style.top) || window.innerHeight/2;
                                const startTime = Date.now();
                                while (Date.now() - startTime < dur) {{
                                    const t = (Date.now() - startTime) / dur;
                                    const eased = 1 - Math.pow(1 - t, 3);
                                    cursor.style.left = (startX + (x - startX) * eased) + 'px';
                                    cursor.style.top = (startY + (y - startY) * eased) + 'px';
                                    await wait(16);
                                }}
                                cursor.style.left = x + 'px';
                                cursor.style.top = y + 'px';
                            }};

                            // Click helper (visual only)
                            const clickAt = async (x, y) => {{
                                await moveTo(x, y, 300);
                                const cursor = document.getElementById('video-capture-cursor');
                                if (cursor) {{
                                    cursor.style.transform = 'translate(-50%, -50%) scale(0.7)';
                                    await wait(100);
                                    cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                                }}
                            }};

                            // Execute user actions
                            {actions_js}
                        }})()
                    """)
                )

                # Wait for duration
                await asyncio.sleep(duration)

                # Cancel actions if still running
                actions_task.cancel()
                try:
                    await actions_task
                except asyncio.CancelledError:
                    pass
            else:
                # Just wait for duration
                await asyncio.sleep(duration)

            # Remove cursor
            await self._remove_cursor(page)

            # Close page to finalize video
            await page.close()
            await context.close()
            context = None
            page = None

            # Find the recorded video file
            video_files = list(temp_dir.glob("*.webm"))
            if not video_files:
                return CaptureResult(success=False, error="No video file created")

            webm_path = video_files[0]

            # Determine output path
            if output_path is None:
                output_path = Path(f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self.config.output_format}")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to MP4 if needed
            if self.config.output_format == "mp4":
                if await self._convert_to_mp4(webm_path, output_path):
                    pass  # Success
                else:
                    # Fallback: use webm
                    output_path = output_path.with_suffix(".webm")
                    shutil.move(str(webm_path), str(output_path))
            else:
                shutil.move(str(webm_path), str(output_path))

            # Calculate frames
            frames = int(duration * self.config.fps)

            return CaptureResult(
                success=True,
                output_path=output_path,
                duration=duration,
                frames=frames,
            )

        except Exception as e:
            return CaptureResult(success=False, error=str(e))

        finally:
            # Cleanup
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

            # Remove temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def capture_demo_state(
        self,
        demo_definition: "DemoDefinition",
        state_id: str,
        output_path: Path,
    ) -> CaptureResult:
        """
        Capture a demo state using the demo definition.

        Args:
            demo_definition: Loaded DemoDefinition
            state_id: ID of the state to capture
            output_path: Where to save the video

        Returns:
            CaptureResult with output path and metadata
        """
        from .demo_capture import DemoDefinition

        state = demo_definition.states.get(state_id)
        if not state:
            return CaptureResult(
                success=False,
                error=f"State '{state_id}' not found in demo definition"
            )

        # Override config with demo viewport
        self.config.width = demo_definition.viewport_width
        self.config.height = demo_definition.viewport_height

        return await self.capture_state(
            url=demo_definition.url,
            setup_js=state.setup,
            actions_js=state.actions,
            wait_for=state.wait_for,
            duration=state.duration,
            output_path=output_path,
        )


async def capture_video(
    url: str,
    output_path: Path,
    setup_js: Optional[str] = None,
    actions_js: Optional[str] = None,
    wait_for: str = "body",
    duration: float = 5.0,
    width: int = 1920,
    height: int = 1080,
    include_cursor: bool = True,
    headless: bool = True,
) -> CaptureResult:
    """
    Convenience function to capture a single video.

    Args:
        url: URL to navigate to
        output_path: Where to save the video
        setup_js: JavaScript to run before recording
        actions_js: JavaScript actions to execute during recording
        wait_for: CSS selector to wait for
        duration: Recording duration in seconds
        width: Viewport width
        height: Viewport height
        include_cursor: Show cursor overlay
        headless: Run browser headlessly

    Returns:
        CaptureResult with output path and metadata
    """
    config = RecordingConfig(
        width=width,
        height=height,
        include_cursor=include_cursor,
    )

    async with VideoCaptureEngine(config=config, headless=headless) as engine:
        return await engine.capture_state(
            url=url,
            setup_js=setup_js,
            actions_js=actions_js,
            wait_for=wait_for,
            duration=duration,
            output_path=output_path,
        )


# Type hint import for demo definition
if TYPE_CHECKING:
    from .demo_capture import DemoDefinition
