"""
Demo Capture Module

Captures video clips from web interfaces using Playwright.
Reads demo definitions from YAML and executes state-based captures.

Features:
- Named state-based capture from YAML definitions
- JavaScript setup execution for each state
- wait_for element support
- Multi-state sequence capture
- MP4 output with configurable duration
"""

import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import yaml

if TYPE_CHECKING:
    from playwright.async_api import Page, Browser


@dataclass
class DemoState:
    """A named demo state for capture."""

    id: str
    description: str
    setup: str  # JavaScript to execute
    wait_for: str  # CSS selector to wait for
    duration: float = 5.0  # Capture duration in seconds


@dataclass
class DemoSequence:
    """A sequence of states for continuous capture."""

    id: str
    description: str
    states: List[str]  # State IDs
    transition_delay: float = 1.0


@dataclass
class DemoDefinition:
    """Complete demo definition loaded from YAML."""

    name: str
    url: str
    viewport_width: int = 1920
    viewport_height: int = 1080
    states: Dict[str, DemoState] = field(default_factory=dict)
    sequences: Dict[str, DemoSequence] = field(default_factory=dict)


def load_demo_definition(yaml_path: Path) -> DemoDefinition:
    """Load demo definition from YAML file."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # Parse viewport
    viewport = data.get("viewport", {})

    # Parse states
    states = {}
    for state_id, state_data in data.get("states", {}).items():
        states[state_id] = DemoState(
            id=state_id,
            description=state_data.get("description", ""),
            setup=state_data.get("setup", ""),
            wait_for=state_data.get("wait_for", "body"),
            duration=state_data.get("duration", 5.0),
        )

    # Parse sequences
    sequences = {}
    for seq_id, seq_data in data.get("sequences", {}).items():
        sequences[seq_id] = DemoSequence(
            id=seq_id,
            description=seq_data.get("description", ""),
            states=seq_data.get("states", []),
            transition_delay=seq_data.get("transition_delay", 1.0),
        )

    return DemoDefinition(
        name=data.get("name", "Demo"),
        url=data.get("url", "http://localhost:8080"),
        viewport_width=viewport.get("width", 1920),
        viewport_height=viewport.get("height", 1080),
        states=states,
        sequences=sequences,
    )


async def capture_state(
    page: "Page",
    state: DemoState,
    output_path: Path,
    duration: float = 5.0,
    fps: int = 30,
) -> Path:
    """
    Capture a single demo state as video.

    Args:
        page: Playwright page instance
        state: DemoState to capture
        output_path: Where to save the video
        duration: Capture duration in seconds
        fps: Frames per second for capture

    Returns:
        Path to captured video file
    """
    print(f"  Capturing state: {state.id} - {state.description}")

    # Execute setup JavaScript
    if state.setup:
        await page.evaluate(f"""
            (async () => {{
                {state.setup}
            }})()
        """)

    # Wait for element to appear
    try:
        await page.wait_for_selector(state.wait_for, timeout=10000)
    except Exception as e:
        print(f"    Warning: wait_for element '{state.wait_for}' not found: {e}")

    # Small delay to let animations settle
    await asyncio.sleep(0.5)

    # Start video capture
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use Playwright's built-in video recording
    # Note: Video recording is configured at context level, so we'll use screenshots
    # and ffmpeg for more control. For now, capture as series of screenshots.

    temp_dir = output_path.parent / ".temp" / state.id
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Capture screenshots at fps rate
        frame_count = int(duration * fps)
        frame_interval = 1.0 / fps

        for i in range(frame_count):
            screenshot_path = temp_dir / f"frame_{i:05d}.png"
            await page.screenshot(path=str(screenshot_path))
            await asyncio.sleep(frame_interval)

        # Combine screenshots into video using ffmpeg
        import subprocess

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(temp_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            str(output_path),
        ]

        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"    Saved: {output_path}")

    finally:
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_path


async def capture_sequence(
    page: "Page",
    definition: DemoDefinition,
    sequence: DemoSequence,
    output_path: Path,
    fps: int = 30,
) -> Path:
    """
    Capture a sequence of states as a single video.

    Args:
        page: Playwright page instance
        definition: Full demo definition for state lookup
        sequence: Sequence to capture
        output_path: Where to save the video
        fps: Frames per second

    Returns:
        Path to captured video file
    """
    print(f"Capturing sequence: {sequence.id} - {sequence.description}")

    temp_dir = output_path.parent / ".temp" / sequence.id
    temp_dir.mkdir(parents=True, exist_ok=True)

    frame_counter = 0
    frame_interval = 1.0 / fps

    try:
        for state_id in sequence.states:
            state = definition.states.get(state_id)
            if not state:
                print(f"  Warning: State '{state_id}' not found, skipping")
                continue

            print(f"  State: {state_id}")

            # Execute setup
            if state.setup:
                await page.evaluate(f"""
                    (async () => {{
                        {state.setup}
                    }})()
                """)

            # Wait for element
            try:
                await page.wait_for_selector(state.wait_for, timeout=10000)
            except Exception:
                pass

            await asyncio.sleep(0.3)

            # Capture frames for this state
            state_frames = int(state.duration * fps)
            for _ in range(state_frames):
                screenshot_path = temp_dir / f"frame_{frame_counter:05d}.png"
                await page.screenshot(path=str(screenshot_path))
                await asyncio.sleep(frame_interval)
                frame_counter += 1

            # Transition delay
            transition_frames = int(sequence.transition_delay * fps)
            for _ in range(transition_frames):
                screenshot_path = temp_dir / f"frame_{frame_counter:05d}.png"
                await page.screenshot(path=str(screenshot_path))
                await asyncio.sleep(frame_interval)
                frame_counter += 1

        # Combine into video
        import subprocess

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(temp_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            str(output_path),
        ]

        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"  Saved: {output_path}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_path


async def capture_all_states(
    definition_path: Path,
    output_dir: Path,
    states: Optional[List[str]] = None,
    duration: float = 5.0,
    fps: int = 30,
    headless: bool = True,
) -> Dict[str, Path]:
    """
    Capture all (or specified) demo states from a definition file.

    Args:
        definition_path: Path to demo YAML definition
        output_dir: Directory to save captured videos
        states: List of state IDs to capture (None = all)
        duration: Duration per state in seconds
        fps: Frames per second
        headless: Run browser in headless mode

    Returns:
        Dict mapping state ID to output path
    """
    from playwright.async_api import async_playwright

    definition = load_demo_definition(definition_path)
    print(f"Loaded demo definition: {definition.name}")
    print(f"  URL: {definition.url}")
    print(f"  States: {len(definition.states)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={
                "width": definition.viewport_width,
                "height": definition.viewport_height,
            },
        )
        page = await context.new_page()

        # Navigate to base URL
        print(f"Navigating to {definition.url}")
        await page.goto(definition.url, wait_until="networkidle")

        # Capture each state
        states_to_capture = states or list(definition.states.keys())

        for state_id in states_to_capture:
            state = definition.states.get(state_id)
            if not state:
                print(f"Warning: State '{state_id}' not found, skipping")
                continue

            output_path = output_dir / f"{state_id}.mp4"
            await capture_state(
                page=page,
                state=state,
                output_path=output_path,
                duration=duration,
                fps=fps,
            )
            results[state_id] = output_path

        await browser.close()

    return results


async def capture_for_video_script(
    script_path: Path,
    definition_path: Path,
    output_dir: Path,
    fps: int = 30,
    headless: bool = True,
) -> Dict[str, Path]:
    """
    Capture all demo clips needed by a video script.

    Reads the video script YAML, finds all scenes with demo cues,
    and captures the corresponding states from the demo definition.

    Args:
        script_path: Path to video script YAML
        definition_path: Path to demo definition YAML
        output_dir: Directory to save captured videos
        fps: Frames per second
        headless: Run browser in headless mode

    Returns:
        Dict mapping state ID to output path
    """
    # Load video script
    with open(script_path, "r") as f:
        script = yaml.safe_load(f)

    # Extract demo states from scenes
    needed_states = {}
    for scene in script.get("scenes", []):
        demo = scene.get("demo")
        if demo:
            state_id = demo.get("state")
            duration = scene.get("duration", 5)
            if state_id:
                needed_states[state_id] = duration

    if not needed_states:
        print("No demo states found in video script")
        return {}

    print(f"Found {len(needed_states)} demo states in video script:")
    for state_id, duration in needed_states.items():
        print(f"  - {state_id} ({duration}s)")

    # Load demo definition
    definition = load_demo_definition(definition_path)

    # Capture each needed state
    from playwright.async_api import async_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={
                "width": definition.viewport_width,
                "height": definition.viewport_height,
            },
        )
        page = await context.new_page()

        # Navigate to base URL
        print(f"Navigating to {definition.url}")
        await page.goto(definition.url, wait_until="networkidle")

        for state_id, duration in needed_states.items():
            state = definition.states.get(state_id)
            if not state:
                print(f"Warning: State '{state_id}' not found in demo definition")
                continue

            output_path = output_dir / f"{state_id}.mp4"
            await capture_state(
                page=page,
                state=state,
                output_path=output_path,
                duration=duration,
                fps=fps,
            )
            results[state_id] = output_path

        await browser.close()

    return results


# CLI entry point
async def main():
    """CLI entry point for demo capture."""
    import argparse

    parser = argparse.ArgumentParser(description="Capture demo clips from web interface")
    parser.add_argument("definition", type=Path, help="Path to demo definition YAML")
    parser.add_argument("-o", "--output", type=Path, default=Path("demos"), help="Output directory")
    parser.add_argument("-s", "--states", nargs="+", help="Specific states to capture")
    parser.add_argument("-d", "--duration", type=float, default=5.0, help="Duration per state")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    parser.add_argument("--script", type=Path, help="Video script to capture states for")

    args = parser.parse_args()

    if args.script:
        # Capture for video script
        results = await capture_for_video_script(
            script_path=args.script,
            definition_path=args.definition,
            output_dir=args.output,
            fps=args.fps,
            headless=not args.no_headless,
        )
    else:
        # Capture specified or all states
        results = await capture_all_states(
            definition_path=args.definition,
            output_dir=args.output,
            states=args.states,
            duration=args.duration,
            fps=args.fps,
            headless=not args.no_headless,
        )

    print(f"\nCaptured {len(results)} demo clips")
    for state_id, path in results.items():
        print(f"  {state_id}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
