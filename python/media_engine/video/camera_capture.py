"""
Camera Capture Module

High-resolution demo capture with element bounds extraction for animated camera.
Supports CSS selector-based focus targeting and multi-scale capture.

Features:
- High-res capture (2x-4x scale) for zoom headroom
- Element bounding box extraction via CSS selectors
- Batch element extraction for camera focus sequences
- Integration with demo_capture module
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class ElementBounds:
    """Bounding box for a DOM element."""

    x: float
    y: float
    width: float
    height: float
    center_x: float
    center_y: float
    selector: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], selector: str = "") -> "ElementBounds":
        """Create from JavaScript getBoundingClientRect result."""
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            center_x=data["centerX"],
            center_y=data["centerY"],
            selector=selector,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props export."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "centerX": self.center_x,
            "centerY": self.center_y,
        }

    def with_padding(self, padding: int) -> "ElementBounds":
        """Return new bounds with padding applied."""
        return ElementBounds(
            x=self.x - padding,
            y=self.y - padding,
            width=self.width + padding * 2,
            height=self.height + padding * 2,
            center_x=self.center_x,
            center_y=self.center_y,
            selector=self.selector,
        )


@dataclass
class CameraKeyframe:
    """A keyframe in the camera focus sequence."""

    target: str  # CSS selector or "fullpage"
    zoom: float = 1.0
    padding: int = 40
    duration: float = 1.0  # seconds to reach this keyframe
    easing: str = "easeInOutCubic"
    hold: float = 0.0  # seconds to hold at this position
    offset_x: int = 0  # manual offset adjustment
    offset_y: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CameraKeyframe":
        """Create from YAML config dict."""
        offset = data.get("offset", {})
        return cls(
            target=data.get("target", "fullpage"),
            zoom=data.get("zoom", 1.0),
            padding=data.get("padding", 40),
            duration=data.get("duration", 1.0),
            easing=data.get("easing", "easeInOutCubic"),
            hold=data.get("hold", 0.0),
            offset_x=offset.get("x", 0) if isinstance(offset, dict) else 0,
            offset_y=offset.get("y", 0) if isinstance(offset, dict) else 0,
        )


@dataclass
class CameraConfig:
    """Complete camera configuration for a demo scene."""

    mode: str = "static"  # static | animated | follow_cursor
    capture_scale: float = 2.0  # 2x = 4K for 1080p output
    background: str = "#1a1a2e"
    shadow: bool = True
    focus_sequence: list[CameraKeyframe] = field(default_factory=list)
    preset: str | None = None
    # Visual effects
    effects: dict[str, Any] = field(default_factory=dict)
    effects_preset: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CameraConfig":
        """Create from YAML config dict."""
        focus_sequence = [
            CameraKeyframe.from_dict(kf)
            for kf in data.get("focus_sequence", [])
        ]
        return cls(
            mode=data.get("mode", "static"),
            capture_scale=data.get("capture_scale", 2.0),
            background=data.get("background", "#1a1a2e"),
            shadow=data.get("shadow", True),
            focus_sequence=focus_sequence,
            preset=data.get("preset"),
            effects=data.get("effects", {}),
            effects_preset=data.get("effects_preset"),
        )

    def get_all_selectors(self) -> list[str]:
        """Get all CSS selectors from focus sequence."""
        return [
            kf.target
            for kf in self.focus_sequence
            if kf.target != "fullpage"
        ]

    def get_effects_config(self) -> dict[str, Any]:
        """Get effects configuration, applying preset if specified."""
        from .camera_effects import CameraEffectsConfig, get_effect_preset

        if self.effects_preset:
            config = get_effect_preset(self.effects_preset)
            # Merge with any overrides
            if self.effects:
                override = CameraEffectsConfig.from_dict(self.effects)
                # Simple merge - override takes precedence for enabled effects
                merged = config.to_dict()
                for key, value in override.to_dict().items():
                    if isinstance(value, dict) and value.get("enabled", False):
                        merged[key] = value
                return merged
            return config.to_dict()
        elif self.effects:
            return CameraEffectsConfig.from_dict(self.effects).to_dict()
        return CameraEffectsConfig().to_dict()


@dataclass
class CaptureResult:
    """Result of high-res camera capture."""

    image_path: Path
    viewport_width: int
    viewport_height: int
    capture_scale: float
    element_bounds: dict[str, ElementBounds]

    @property
    def capture_width(self) -> int:
        """Width of captured image."""
        return int(self.viewport_width * self.capture_scale)

    @property
    def capture_height(self) -> int:
        """Height of captured image."""
        return int(self.viewport_height * self.capture_scale)

    def to_props_dict(self) -> dict[str, Any]:
        """Convert to props dict for Remotion."""
        return {
            "image_path": str(self.image_path),
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "capture_scale": self.capture_scale,
            "capture_width": self.capture_width,
            "capture_height": self.capture_height,
            "element_bounds": {
                selector: bounds.to_dict()
                for selector, bounds in self.element_bounds.items()
            },
        }


class CameraCaptureEngine:
    """
    High-resolution demo capture with element bounds extraction.

    Captures screenshots at higher resolution than output for zoom headroom,
    and extracts element bounding boxes for CSS selector-based focusing.
    """

    def __init__(
        self,
        page: "Page",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        self.page = page
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    async def get_element_bounds(self, selector: str) -> ElementBounds | None:
        """
        Get bounding box for a CSS selector.

        Args:
            selector: CSS selector to find

        Returns:
            ElementBounds or None if element not found
        """
        result = await self.page.evaluate(f'''
            (() => {{
                const el = document.querySelector("{selector}");
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    centerX: rect.x + rect.width / 2,
                    centerY: rect.y + rect.height / 2
                }};
            }})()
        ''')
        if result:
            return ElementBounds.from_dict(result, selector)
        return None

    async def get_multiple_element_bounds(
        self, selectors: list[str]
    ) -> dict[str, ElementBounds]:
        """
        Get bounding boxes for multiple selectors in one pass.

        Args:
            selectors: List of CSS selectors

        Returns:
            Dict mapping selector to ElementBounds
        """
        # Build JavaScript to get all bounds at once
        selector_list = ", ".join(f'"{s}"' for s in selectors)
        result = await self.page.evaluate(f'''
            (() => {{
                const selectors = [{selector_list}];
                const results = {{}};
                for (const selector of selectors) {{
                    const el = document.querySelector(selector);
                    if (el) {{
                        const rect = el.getBoundingClientRect();
                        results[selector] = {{
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            centerX: rect.x + rect.width / 2,
                            centerY: rect.y + rect.height / 2
                        }};
                    }}
                }}
                return results;
            }})()
        ''')

        return {
            selector: ElementBounds.from_dict(data, selector)
            for selector, data in result.items()
        }

    async def capture_high_res(
        self,
        output_path: Path,
        capture_scale: float = 2.0,
        selectors: list[str] | None = None,
    ) -> CaptureResult:
        """
        Capture high-resolution screenshot with element bounds.

        Args:
            output_path: Where to save the screenshot
            capture_scale: Scale factor (2.0 = 4K for 1080p)
            selectors: CSS selectors to extract bounds for

        Returns:
            CaptureResult with image path and element bounds
        """
        # Set viewport with device scale factor for high-res
        await self.page.set_viewport_size({
            "width": self.viewport_width,
            "height": self.viewport_height,
        })

        # Get element bounds before scaling (coordinates are in CSS pixels)
        element_bounds = {}
        if selectors:
            element_bounds = await self.get_multiple_element_bounds(selectors)

        # Capture at high resolution
        # Use CSS transform on body to scale content
        await self.page.evaluate(f'''
            (() => {{
                document.body.style.transform = 'scale({capture_scale})';
                document.body.style.transformOrigin = 'top left';
                document.body.style.width = '{self.viewport_width}px';
                document.body.style.height = '{self.viewport_height}px';
            }})()
        ''')

        # Small delay for render
        await asyncio.sleep(0.1)

        # Set viewport to capture size
        capture_width = int(self.viewport_width * capture_scale)
        capture_height = int(self.viewport_height * capture_scale)
        await self.page.set_viewport_size({
            "width": capture_width,
            "height": capture_height,
        })

        # Capture screenshot
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(output_path))

        # Reset body transform
        await self.page.evaluate('''
            (() => {
                document.body.style.transform = '';
                document.body.style.transformOrigin = '';
                document.body.style.width = '';
                document.body.style.height = '';
            })()
        ''')

        # Reset viewport
        await self.page.set_viewport_size({
            "width": self.viewport_width,
            "height": self.viewport_height,
        })

        # Scale element bounds to match captured image
        scaled_bounds = {
            selector: ElementBounds(
                x=bounds.x * capture_scale,
                y=bounds.y * capture_scale,
                width=bounds.width * capture_scale,
                height=bounds.height * capture_scale,
                center_x=bounds.center_x * capture_scale,
                center_y=bounds.center_y * capture_scale,
                selector=selector,
            )
            for selector, bounds in element_bounds.items()
        }

        return CaptureResult(
            image_path=output_path,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            capture_scale=capture_scale,
            element_bounds=scaled_bounds,
        )

    async def capture_with_camera_config(
        self,
        output_path: Path,
        camera_config: CameraConfig,
    ) -> CaptureResult:
        """
        Capture based on camera configuration.

        Args:
            output_path: Where to save the screenshot
            camera_config: Camera configuration with focus sequence

        Returns:
            CaptureResult with image and element bounds
        """
        selectors = camera_config.get_all_selectors()
        return await self.capture_high_res(
            output_path=output_path,
            capture_scale=camera_config.capture_scale,
            selectors=selectors,
        )


async def capture_demo_for_camera(
    demo_path: Path,
    state_id: str,
    output_dir: Path,
    camera_config: CameraConfig,
    headless: bool = True,
) -> CaptureResult:
    """
    Capture a demo state for animated camera use.

    Args:
        demo_path: Path to demo definition YAML
        state_id: State ID to capture
        output_dir: Directory for output files
        camera_config: Camera configuration
        headless: Run browser headless

    Returns:
        CaptureResult with high-res image and element bounds
    """
    from playwright.async_api import async_playwright

    from .demo_capture import load_demo_definition

    definition = load_demo_definition(demo_path)

    state = definition.states.get(state_id)
    if not state:
        raise ValueError(f"State '{state_id}' not found in demo definition")

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
        await page.goto(definition.url, wait_until="networkidle")

        # Execute state setup
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

        await asyncio.sleep(0.5)

        # Create camera capture engine
        engine = CameraCaptureEngine(
            page=page,
            viewport_width=definition.viewport_width,
            viewport_height=definition.viewport_height,
        )

        # Capture with camera config
        scale_suffix = f"_{camera_config.capture_scale}x"
        output_path = output_dir / f"{state_id}{scale_suffix}.png"

        result = await engine.capture_with_camera_config(
            output_path=output_path,
            camera_config=camera_config,
        )

        await browser.close()

    return result
