"""
Camera Presets Module

Pre-defined camera movement patterns for common demo scenarios.
Each preset generates a focus sequence based on available elements.

Features:
- Preset pattern definitions
- Automatic element-based sequence generation
- Customizable timing and zoom parameters
"""

from dataclasses import dataclass
from typing import Any

from .camera_capture import CameraKeyframe


@dataclass
class CameraPreset:
    """Definition of a camera movement preset."""

    id: str
    name: str
    description: str
    pattern: str  # sequential | zoom_out | focus_main | flow | overview
    default_zoom: float = 2.0
    default_duration: float = 1.0
    default_hold: float = 1.5
    default_easing: str = "easeInOutCubic"
    start_zoom: float | None = None  # For zoom_out pattern
    end_zoom: float | None = None


# Pre-defined camera presets
CAMERA_PRESETS: dict[str, CameraPreset] = {
    "guided_tour": CameraPreset(
        id="guided_tour",
        name="Guided Tour",
        description="Systematic element-by-element walkthrough with smooth transitions",
        pattern="sequential",
        default_zoom=2.0,
        default_duration=1.2,
        default_hold=1.5,
        default_easing="easeInOutCubic",
    ),
    "quick_overview": CameraPreset(
        id="quick_overview",
        name="Quick Overview",
        description="Fast overview of key elements with subtle zoom",
        pattern="sequential",
        default_zoom=1.3,
        default_duration=0.6,
        default_hold=0.8,
        default_easing="easeOutQuart",
    ),
    "dramatic_reveal": CameraPreset(
        id="dramatic_reveal",
        name="Dramatic Reveal",
        description="Start zoomed in on detail, reveal full page",
        pattern="zoom_out",
        start_zoom=3.0,
        end_zoom=1.0,
        default_duration=2.0,
        default_hold=2.0,
        default_easing="easeOutExpo",
    ),
    "follow_flow": CameraPreset(
        id="follow_flow",
        name="Follow Flow",
        description="Follow natural reading/interaction flow",
        pattern="flow",
        default_zoom=1.8,
        default_duration=1.0,
        default_hold=1.2,
        default_easing="easeInOutSine",
    ),
    "focus_main": CameraPreset(
        id="focus_main",
        name="Focus Main",
        description="Start full, zoom to main content, return to full",
        pattern="focus_main",
        default_zoom=2.5,
        default_duration=1.5,
        default_hold=3.0,
        default_easing="easeInOutCubic",
    ),
    "cinematic": CameraPreset(
        id="cinematic",
        name="Cinematic",
        description="Slow, dramatic movements with deep zoom",
        pattern="sequential",
        default_zoom=2.8,
        default_duration=2.0,
        default_hold=2.5,
        default_easing="easeInOutQuart",
    ),
    "scan": CameraPreset(
        id="scan",
        name="Scan",
        description="Quick scan across elements without deep zoom",
        pattern="sequential",
        default_zoom=1.4,
        default_duration=0.4,
        default_hold=0.5,
        default_easing="easeOutCubic",
    ),
}


def get_preset(preset_id: str) -> CameraPreset | None:
    """Get a preset by ID."""
    return CAMERA_PRESETS.get(preset_id)


def list_presets() -> list[dict[str, Any]]:
    """List all available presets."""
    return [
        {
            "id": preset.id,
            "name": preset.name,
            "description": preset.description,
        }
        for preset in CAMERA_PRESETS.values()
    ]


class PresetResolver:
    """
    Resolves camera presets into focus sequences.

    Takes a preset ID and list of available elements,
    generates appropriate focus sequence based on pattern.
    """

    def __init__(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    def resolve(
        self,
        preset_id: str,
        selectors: list[str],
        custom_params: dict[str, Any] | None = None,
    ) -> list[CameraKeyframe]:
        """
        Generate focus sequence from preset.

        Args:
            preset_id: Preset ID to use
            selectors: List of available CSS selectors
            custom_params: Override preset defaults

        Returns:
            List of CameraKeyframe objects
        """
        preset = get_preset(preset_id)
        if not preset:
            # Fallback to simple fullpage
            return [
                CameraKeyframe(
                    target="fullpage",
                    zoom=1.0,
                    duration=0.5,
                    hold=5.0,
                )
            ]

        # Merge custom params with defaults
        params = {
            "zoom": preset.default_zoom,
            "duration": preset.default_duration,
            "hold": preset.default_hold,
            "easing": preset.default_easing,
        }
        if custom_params:
            params.update(custom_params)

        # Generate based on pattern
        if preset.pattern == "sequential":
            return self._sequential(selectors, params)
        elif preset.pattern == "zoom_out":
            return self._zoom_out(selectors, preset, params)
        elif preset.pattern == "focus_main":
            return self._focus_main(selectors, params)
        elif preset.pattern == "flow":
            return self._flow(selectors, params)
        else:
            return self._sequential(selectors, params)

    def _sequential(
        self,
        selectors: list[str],
        params: dict[str, Any],
    ) -> list[CameraKeyframe]:
        """Sequential walkthrough of elements."""
        keyframes = [
            # Start with full page
            CameraKeyframe(
                target="fullpage",
                zoom=1.0,
                duration=0.5,
                hold=0.5,
                easing="easeOutCubic",
            )
        ]

        # Add each element
        for selector in selectors:
            keyframes.append(
                CameraKeyframe(
                    target=selector,
                    zoom=params["zoom"],
                    duration=params["duration"],
                    hold=params["hold"],
                    easing=params["easing"],
                )
            )

        # End with full page
        keyframes.append(
            CameraKeyframe(
                target="fullpage",
                zoom=1.0,
                duration=params["duration"],
                hold=0.5,
                easing="easeOutCubic",
            )
        )

        return keyframes

    def _zoom_out(
        self,
        selectors: list[str],
        preset: CameraPreset,
        params: dict[str, Any],
    ) -> list[CameraKeyframe]:
        """Start zoomed in, reveal full page."""
        keyframes = []

        # Start zoomed on first element or center
        start_target = selectors[0] if selectors else "fullpage"
        keyframes.append(
            CameraKeyframe(
                target=start_target,
                zoom=preset.start_zoom or 3.0,
                duration=0.5,
                hold=params["hold"],
                easing="easeOutCubic",
            )
        )

        # Zoom out to full page
        keyframes.append(
            CameraKeyframe(
                target="fullpage",
                zoom=preset.end_zoom or 1.0,
                duration=params["duration"],
                hold=params["hold"],
                easing=params["easing"],
            )
        )

        return keyframes

    def _focus_main(
        self,
        selectors: list[str],
        params: dict[str, Any],
    ) -> list[CameraKeyframe]:
        """Focus on main content element."""
        # Find main content element (heuristic)
        main_selector = None
        for selector in selectors:
            if any(word in selector.lower() for word in ["main", "content", "body"]):
                main_selector = selector
                break
        if not main_selector and selectors:
            main_selector = selectors[0]

        keyframes = [
            # Start full
            CameraKeyframe(
                target="fullpage",
                zoom=1.0,
                duration=0.5,
                hold=0.5,
                easing="easeOutCubic",
            ),
        ]

        if main_selector:
            # Zoom to main
            keyframes.append(
                CameraKeyframe(
                    target=main_selector,
                    zoom=params["zoom"],
                    duration=params["duration"],
                    hold=params["hold"],
                    easing=params["easing"],
                )
            )

        # Return to full
        keyframes.append(
            CameraKeyframe(
                target="fullpage",
                zoom=1.0,
                duration=params["duration"],
                hold=0.5,
                easing="easeOutCubic",
            )
        )

        return keyframes

    def _flow(
        self,
        selectors: list[str],
        params: dict[str, Any],
    ) -> list[CameraKeyframe]:
        """Follow natural reading flow (top-to-bottom, left-to-right)."""
        # Similar to sequential but with flow-optimized easing
        keyframes = [
            CameraKeyframe(
                target="fullpage",
                zoom=1.0,
                duration=0.5,
                hold=0.3,
                easing="easeOutSine",
            )
        ]

        for i, selector in enumerate(selectors):
            # Alternate easing for flow feel
            easing = "easeInOutSine" if i % 2 == 0 else "easeOutSine"
            keyframes.append(
                CameraKeyframe(
                    target=selector,
                    zoom=params["zoom"],
                    duration=params["duration"],
                    hold=params["hold"],
                    easing=easing,
                )
            )

        keyframes.append(
            CameraKeyframe(
                target="fullpage",
                zoom=1.0,
                duration=params["duration"],
                hold=0.5,
                easing="easeInOutSine",
            )
        )

        return keyframes


def resolve_preset(
    preset_id: str,
    selectors: list[str],
    custom_params: dict[str, Any] | None = None,
) -> list[CameraKeyframe]:
    """
    Convenience function to resolve a preset.

    Args:
        preset_id: Preset ID to use
        selectors: Available CSS selectors
        custom_params: Override defaults

    Returns:
        List of CameraKeyframe objects
    """
    resolver = PresetResolver()
    return resolver.resolve(preset_id, selectors, custom_params)
