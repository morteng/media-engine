"""
Camera Path Module

Generates smooth camera paths from focus sequences using Catmull-Rom splines.
Converts CSS selector targets to pixel coordinates and interpolates between keyframes.

Features:
- CSS selector → pixel coordinate resolution
- Catmull-Rom spline interpolation for smooth motion
- Frame-accurate camera state generation
- Easing function support
"""

import math
from dataclasses import dataclass
from typing import Any

from .camera_capture import CameraConfig, CameraKeyframe, ElementBounds


@dataclass
class CameraState:
    """Camera state at a specific frame."""

    frame: int
    center_x: float
    center_y: float
    zoom: float
    easing: str = "linear"

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "frame": self.frame,
            "centerX": self.center_x,
            "centerY": self.center_y,
            "zoom": self.zoom,
            "easing": self.easing,
        }


@dataclass
class ResolvedKeyframe:
    """Keyframe with resolved pixel coordinates."""

    frame: int
    center_x: float
    center_y: float
    zoom: float
    easing: str
    hold_frames: int = 0


# Easing functions
def ease_linear(t: float) -> float:
    return t


def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)


def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


def ease_in_cubic(t: float) -> float:
    return t * t * t


def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)


def ease_in_out_cubic(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def ease_in_quart(t: float) -> float:
    return t * t * t * t


def ease_out_quart(t: float) -> float:
    return 1 - pow(1 - t, 4)


def ease_in_out_quart(t: float) -> float:
    return 8 * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 4) / 2


def ease_in_expo(t: float) -> float:
    return 0 if t == 0 else pow(2, 10 * t - 10)


def ease_out_expo(t: float) -> float:
    return 1 if t == 1 else 1 - pow(2, -10 * t)


def ease_in_out_expo(t: float) -> float:
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return pow(2, 20 * t - 10) / 2
    return (2 - pow(2, -20 * t + 10)) / 2


def ease_in_sine(t: float) -> float:
    return 1 - math.cos((t * math.pi) / 2)


def ease_out_sine(t: float) -> float:
    return math.sin((t * math.pi) / 2)


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


EASING_FUNCTIONS = {
    "linear": ease_linear,
    "easeInQuad": ease_in_quad,
    "easeOutQuad": ease_out_quad,
    "easeInOutQuad": ease_in_out_quad,
    "easeInCubic": ease_in_cubic,
    "easeOutCubic": ease_out_cubic,
    "easeInOutCubic": ease_in_out_cubic,
    "easeInQuart": ease_in_quart,
    "easeOutQuart": ease_out_quart,
    "easeInOutQuart": ease_in_out_quart,
    "easeInExpo": ease_in_expo,
    "easeOutExpo": ease_out_expo,
    "easeInOutExpo": ease_in_out_expo,
    "easeInSine": ease_in_sine,
    "easeOutSine": ease_out_sine,
    "easeInOutSine": ease_in_out_sine,
}


def get_easing(name: str) -> callable:
    """Get easing function by name."""
    return EASING_FUNCTIONS.get(name, ease_linear)


def catmull_rom_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    """
    Catmull-Rom spline interpolation between p1 and p2.

    Args:
        p0: Control point before p1
        p1: Start point
        p2: End point
        p3: Control point after p2
        t: Parameter 0-1 between p1 and p2

    Returns:
        Interpolated point (x, y)
    """
    t2 = t * t
    t3 = t2 * t

    x = 0.5 * (
        (2 * p1[0])
        + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )

    y = 0.5 * (
        (2 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )

    return (x, y)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


class CameraPathGenerator:
    """
    Generates smooth camera paths from focus sequences.

    Resolves CSS selectors to pixel coordinates and generates
    frame-accurate camera states using Catmull-Rom splines.
    """

    def __init__(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        capture_scale: float = 2.0,
    ):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.capture_scale = capture_scale

    def resolve_keyframes(
        self,
        focus_sequence: list[CameraKeyframe],
        element_bounds: dict[str, ElementBounds],
        fps: int = 30,
    ) -> list[ResolvedKeyframe]:
        """
        Convert focus sequence to resolved keyframes with pixel coordinates.

        Args:
            focus_sequence: List of camera keyframes from config
            element_bounds: Dict mapping selector to bounds
            fps: Frames per second

        Returns:
            List of resolved keyframes with frame numbers and coordinates
        """
        resolved = []
        current_frame = 0

        # Calculate capture center for "fullpage" target
        capture_center_x = (self.viewport_width * self.capture_scale) / 2
        capture_center_y = (self.viewport_height * self.capture_scale) / 2

        for kf in focus_sequence:
            # Resolve target to coordinates
            if kf.target == "fullpage":
                center_x = capture_center_x
                center_y = capture_center_y
            else:
                bounds = element_bounds.get(kf.target)
                if bounds:
                    center_x = bounds.center_x + kf.offset_x
                    center_y = bounds.center_y + kf.offset_y
                else:
                    # Fallback to center if element not found
                    center_x = capture_center_x
                    center_y = capture_center_y

            # Convert hold time to frames
            hold_frames = int(kf.hold * fps)

            resolved.append(
                ResolvedKeyframe(
                    frame=current_frame,
                    center_x=center_x,
                    center_y=center_y,
                    zoom=kf.zoom,
                    easing=kf.easing,
                    hold_frames=hold_frames,
                )
            )

            # Advance frame counter by duration + hold
            duration_frames = int(kf.duration * fps)
            current_frame += duration_frames + hold_frames

        return resolved

    def interpolate_path(
        self,
        keyframes: list[ResolvedKeyframe],
        total_frames: int,
        use_spline: bool = True,
    ) -> list[CameraState]:
        """
        Generate per-frame camera states from keyframes.

        Args:
            keyframes: Resolved keyframes with coordinates
            total_frames: Total frames in the scene
            use_spline: Use Catmull-Rom splines (False = linear)

        Returns:
            List of camera states, one per frame
        """
        if not keyframes:
            # Return static center camera
            center_x = (self.viewport_width * self.capture_scale) / 2
            center_y = (self.viewport_height * self.capture_scale) / 2
            return [
                CameraState(
                    frame=f,
                    center_x=center_x,
                    center_y=center_y,
                    zoom=1.0,
                )
                for f in range(total_frames)
            ]

        states = []

        for frame in range(total_frames):
            state = self._interpolate_at_frame(frame, keyframes, use_spline)
            states.append(state)

        return states

    def _interpolate_at_frame(
        self,
        frame: int,
        keyframes: list[ResolvedKeyframe],
        use_spline: bool,
    ) -> CameraState:
        """Interpolate camera state at a specific frame."""
        # Find surrounding keyframes
        prev_kf = keyframes[0]
        next_kf = keyframes[-1]

        for i, kf in enumerate(keyframes):
            if kf.frame > frame:
                next_kf = kf
                prev_kf = keyframes[max(0, i - 1)]
                break
            prev_kf = kf

        # If before first keyframe, use first
        if frame <= keyframes[0].frame:
            kf = keyframes[0]
            return CameraState(
                frame=frame,
                center_x=kf.center_x,
                center_y=kf.center_y,
                zoom=kf.zoom,
                easing=kf.easing,
            )

        # If after last keyframe, use last
        if frame >= keyframes[-1].frame:
            kf = keyframes[-1]
            return CameraState(
                frame=frame,
                center_x=kf.center_x,
                center_y=kf.center_y,
                zoom=kf.zoom,
                easing=kf.easing,
            )

        # Check if in hold period
        if prev_kf == next_kf or prev_kf.frame == next_kf.frame:
            return CameraState(
                frame=frame,
                center_x=prev_kf.center_x,
                center_y=prev_kf.center_y,
                zoom=prev_kf.zoom,
                easing=prev_kf.easing,
            )

        # Calculate transition progress
        frame_in_transition = frame - prev_kf.frame - prev_kf.hold_frames
        transition_duration = next_kf.frame - prev_kf.frame - prev_kf.hold_frames

        # If in hold period, don't interpolate
        if frame_in_transition < 0:
            return CameraState(
                frame=frame,
                center_x=prev_kf.center_x,
                center_y=prev_kf.center_y,
                zoom=prev_kf.zoom,
                easing=prev_kf.easing,
            )

        # Calculate raw progress 0-1
        if transition_duration > 0:
            t = frame_in_transition / transition_duration
            t = max(0, min(1, t))
        else:
            t = 1

        # Apply easing
        easing_fn = get_easing(next_kf.easing)
        t_eased = easing_fn(t)

        # Interpolate position
        if use_spline and len(keyframes) >= 2:
            # Get control points for Catmull-Rom
            idx = keyframes.index(prev_kf)
            p0 = keyframes[max(0, idx - 1)]
            p1 = prev_kf
            p2 = next_kf
            p3 = keyframes[min(len(keyframes) - 1, keyframes.index(next_kf) + 1)]

            # Catmull-Rom for position
            center_x, center_y = catmull_rom_point(
                (p0.center_x, p0.center_y),
                (p1.center_x, p1.center_y),
                (p2.center_x, p2.center_y),
                (p3.center_x, p3.center_y),
                t_eased,
            )
        else:
            # Linear interpolation
            center_x = lerp(prev_kf.center_x, next_kf.center_x, t_eased)
            center_y = lerp(prev_kf.center_y, next_kf.center_y, t_eased)

        # Linear interpolation for zoom (Catmull-Rom can overshoot)
        zoom = lerp(prev_kf.zoom, next_kf.zoom, t_eased)

        return CameraState(
            frame=frame,
            center_x=center_x,
            center_y=center_y,
            zoom=zoom,
            easing=next_kf.easing,
        )

    def generate_camera_data(
        self,
        camera_config: CameraConfig,
        element_bounds: dict[str, ElementBounds],
        total_frames: int,
        fps: int = 30,
    ) -> dict[str, Any]:
        """
        Generate complete camera data for props export.

        Args:
            camera_config: Camera configuration
            element_bounds: Resolved element bounds
            total_frames: Total frames in scene
            fps: Frames per second

        Returns:
            Dict with keyframes and full path for Remotion
        """
        # Resolve keyframes
        resolved = self.resolve_keyframes(
            focus_sequence=camera_config.focus_sequence,
            element_bounds=element_bounds,
            fps=fps,
        )

        # Generate full path (for debugging/preview, not used in render)
        path = self.interpolate_path(resolved, total_frames)

        # Get effects configuration
        effects = camera_config.get_effects_config()

        return {
            "mode": camera_config.mode,
            "capture_scale": camera_config.capture_scale,
            "background": camera_config.background,
            "shadow": camera_config.shadow,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "fps": fps,
            "total_frames": total_frames,
            "keyframes": [
                {
                    "frame": kf.frame,
                    "centerX": kf.center_x,
                    "centerY": kf.center_y,
                    "zoom": kf.zoom,
                    "easing": kf.easing,
                    "holdFrames": kf.hold_frames,
                }
                for kf in resolved
            ],
            "element_bounds": {
                selector: bounds.to_dict()
                for selector, bounds in element_bounds.items()
            },
            # Include sampled path for preview (every 5th frame)
            "path_preview": [
                state.to_dict()
                for state in path[::5]
            ],
            # Visual effects configuration
            "effects": effects,
        }
