"""
Camera Effects Module

Visual effects for animated camera system including:
- 3D perspective tilt
- Camera shake
- Vignette overlay
- Depth of field blur
- Parallax layers
- Motion blur simulation

These effects enhance demo recordings with professional polish.
"""

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PerspectiveTiltConfig:
    """3D perspective tilt effect configuration."""

    enabled: bool = False
    # Rotation angles in degrees
    tilt_x: float = 0.0  # Pitch (up/down tilt)
    tilt_y: float = 0.0  # Yaw (left/right rotation)
    # Dynamic tilt based on camera movement
    dynamic: bool = False
    dynamic_intensity: float = 0.3  # How much camera motion affects tilt
    # Perspective depth (lower = more dramatic)
    perspective: int = 1200

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerspectiveTiltConfig":
        """Create from YAML config dict."""
        return cls(
            enabled=data.get("enabled", True),
            tilt_x=data.get("tilt_x", 0.0),
            tilt_y=data.get("tilt_y", 0.0),
            dynamic=data.get("dynamic", False),
            dynamic_intensity=data.get("dynamic_intensity", 0.3),
            perspective=data.get("perspective", 1200),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "enabled": self.enabled,
            "tiltX": self.tilt_x,
            "tiltY": self.tilt_y,
            "dynamic": self.dynamic,
            "dynamicIntensity": self.dynamic_intensity,
            "perspective": self.perspective,
        }


@dataclass
class CameraShakeConfig:
    """Camera shake effect for organic feel."""

    enabled: bool = False
    # Shake intensity (0-1)
    intensity: float = 0.3
    # Shake speed (oscillations per second)
    frequency: float = 2.0
    # Maximum pixel offset
    max_offset: float = 5.0
    # Rotation shake (degrees)
    rotation_intensity: float = 0.0
    # Decay over time (0 = no decay, 1 = full decay)
    decay: float = 0.0
    # Random seed for consistent shake
    seed: int = 42

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CameraShakeConfig":
        """Create from YAML config dict."""
        return cls(
            enabled=data.get("enabled", True),
            intensity=data.get("intensity", 0.3),
            frequency=data.get("frequency", 2.0),
            max_offset=data.get("max_offset", 5.0),
            rotation_intensity=data.get("rotation_intensity", 0.0),
            decay=data.get("decay", 0.0),
            seed=data.get("seed", 42),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "enabled": self.enabled,
            "intensity": self.intensity,
            "frequency": self.frequency,
            "maxOffset": self.max_offset,
            "rotationIntensity": self.rotation_intensity,
            "decay": self.decay,
            "seed": self.seed,
        }


@dataclass
class VignetteConfig:
    """Vignette overlay for cinematic look."""

    enabled: bool = False
    # Darkness at edges (0-1)
    intensity: float = 0.4
    # How far the vignette extends (0-1, 0 = edges only, 1 = center)
    spread: float = 0.3
    # Vignette color (usually black)
    color: str = "#000000"
    # Soft edge (higher = softer transition)
    softness: float = 0.5
    # Dynamic vignette based on zoom (more vignette when zoomed)
    dynamic: bool = False
    dynamic_scale: float = 0.5  # How much zoom affects vignette

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VignetteConfig":
        """Create from YAML config dict."""
        return cls(
            enabled=data.get("enabled", True),
            intensity=data.get("intensity", 0.4),
            spread=data.get("spread", 0.3),
            color=data.get("color", "#000000"),
            softness=data.get("softness", 0.5),
            dynamic=data.get("dynamic", False),
            dynamic_scale=data.get("dynamic_scale", 0.5),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "enabled": self.enabled,
            "intensity": self.intensity,
            "spread": self.spread,
            "color": self.color,
            "softness": self.softness,
            "dynamic": self.dynamic,
            "dynamicScale": self.dynamic_scale,
        }


@dataclass
class DepthOfFieldConfig:
    """Depth of field blur effect."""

    enabled: bool = False
    # Blur amount for unfocused areas (px)
    blur_amount: float = 8.0
    # Focus falloff (how quickly blur increases)
    falloff: float = 0.5
    # Blur non-focused elements
    blur_background: bool = True
    # Animate focus based on camera target
    track_focus: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepthOfFieldConfig":
        """Create from YAML config dict."""
        return cls(
            enabled=data.get("enabled", True),
            blur_amount=data.get("blur_amount", 8.0),
            falloff=data.get("falloff", 0.5),
            blur_background=data.get("blur_background", True),
            track_focus=data.get("track_focus", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "enabled": self.enabled,
            "blurAmount": self.blur_amount,
            "falloff": self.falloff,
            "blurBackground": self.blur_background,
            "trackFocus": self.track_focus,
        }


@dataclass
class ParallaxLayer:
    """A single parallax layer."""

    id: str
    depth: float  # 0 = foreground (moves most), 1 = background (moves least)
    image_path: str | None = None
    opacity: float = 1.0
    blur: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "id": self.id,
            "depth": self.depth,
            "imagePath": self.image_path,
            "opacity": self.opacity,
            "blur": self.blur,
        }


@dataclass
class ParallaxConfig:
    """Multi-layer parallax effect."""

    enabled: bool = False
    # Parallax intensity (how much layers separate)
    intensity: float = 0.3
    # Layers (from front to back)
    layers: list[ParallaxLayer] = field(default_factory=list)
    # Auto-generate layers from UI depth
    auto_layers: bool = False
    auto_layer_count: int = 3

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParallaxConfig":
        """Create from YAML config dict."""
        layers = [
            ParallaxLayer(
                id=layer.get("id", f"layer_{i}"),
                depth=layer.get("depth", i / max(1, len(data.get("layers", [])) - 1)),
                image_path=layer.get("image_path"),
                opacity=layer.get("opacity", 1.0),
                blur=layer.get("blur", 0.0),
            )
            for i, layer in enumerate(data.get("layers", []))
        ]
        return cls(
            enabled=data.get("enabled", True),
            intensity=data.get("intensity", 0.3),
            layers=layers,
            auto_layers=data.get("auto_layers", False),
            auto_layer_count=data.get("auto_layer_count", 3),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "enabled": self.enabled,
            "intensity": self.intensity,
            "layers": [layer.to_dict() for layer in self.layers],
            "autoLayers": self.auto_layers,
            "autoLayerCount": self.auto_layer_count,
        }


@dataclass
class MotionBlurConfig:
    """Simulated motion blur during fast camera movements."""

    enabled: bool = False
    # Blur intensity (0-1)
    intensity: float = 0.5
    # Motion threshold to trigger blur (pixels/frame)
    threshold: float = 10.0
    # Blur samples (higher = smoother but slower)
    samples: int = 8
    # Direction-aware blur
    directional: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MotionBlurConfig":
        """Create from YAML config dict."""
        return cls(
            enabled=data.get("enabled", True),
            intensity=data.get("intensity", 0.5),
            threshold=data.get("threshold", 10.0),
            samples=data.get("samples", 8),
            directional=data.get("directional", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "enabled": self.enabled,
            "intensity": self.intensity,
            "threshold": self.threshold,
            "samples": self.samples,
            "directional": self.directional,
        }


@dataclass
class CameraEffectsConfig:
    """Complete camera effects configuration."""

    perspective_tilt: PerspectiveTiltConfig = field(default_factory=PerspectiveTiltConfig)
    camera_shake: CameraShakeConfig = field(default_factory=CameraShakeConfig)
    vignette: VignetteConfig = field(default_factory=VignetteConfig)
    depth_of_field: DepthOfFieldConfig = field(default_factory=DepthOfFieldConfig)
    parallax: ParallaxConfig = field(default_factory=ParallaxConfig)
    motion_blur: MotionBlurConfig = field(default_factory=MotionBlurConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CameraEffectsConfig":
        """Create from YAML config dict."""
        return cls(
            perspective_tilt=PerspectiveTiltConfig.from_dict(data.get("perspective_tilt", {}))
            if data.get("perspective_tilt")
            else PerspectiveTiltConfig(),
            camera_shake=CameraShakeConfig.from_dict(data.get("camera_shake", {}))
            if data.get("camera_shake")
            else CameraShakeConfig(),
            vignette=VignetteConfig.from_dict(data.get("vignette", {}))
            if data.get("vignette")
            else VignetteConfig(),
            depth_of_field=DepthOfFieldConfig.from_dict(data.get("depth_of_field", {}))
            if data.get("depth_of_field")
            else DepthOfFieldConfig(),
            parallax=ParallaxConfig.from_dict(data.get("parallax", {}))
            if data.get("parallax")
            else ParallaxConfig(),
            motion_blur=MotionBlurConfig.from_dict(data.get("motion_blur", {}))
            if data.get("motion_blur")
            else MotionBlurConfig(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict for props."""
        return {
            "perspectiveTilt": self.perspective_tilt.to_dict(),
            "cameraShake": self.camera_shake.to_dict(),
            "vignette": self.vignette.to_dict(),
            "depthOfField": self.depth_of_field.to_dict(),
            "parallax": self.parallax.to_dict(),
            "motionBlur": self.motion_blur.to_dict(),
        }

    def has_any_enabled(self) -> bool:
        """Check if any effects are enabled."""
        return (
            self.perspective_tilt.enabled
            or self.camera_shake.enabled
            or self.vignette.enabled
            or self.depth_of_field.enabled
            or self.parallax.enabled
            or self.motion_blur.enabled
        )


# Effect presets for common use cases
EFFECT_PRESETS: dict[str, CameraEffectsConfig] = {
    "cinematic": CameraEffectsConfig(
        vignette=VignetteConfig(enabled=True, intensity=0.5, spread=0.4),
        perspective_tilt=PerspectiveTiltConfig(enabled=True, dynamic=True, dynamic_intensity=0.2),
    ),
    "documentary": CameraEffectsConfig(
        camera_shake=CameraShakeConfig(enabled=True, intensity=0.2, frequency=1.5),
        vignette=VignetteConfig(enabled=True, intensity=0.3, spread=0.3),
    ),
    "professional": CameraEffectsConfig(
        vignette=VignetteConfig(enabled=True, intensity=0.25, spread=0.2),
    ),
    "dramatic": CameraEffectsConfig(
        vignette=VignetteConfig(enabled=True, intensity=0.6, spread=0.5, dynamic=True),
        perspective_tilt=PerspectiveTiltConfig(enabled=True, tilt_x=3.0, tilt_y=2.0),
        depth_of_field=DepthOfFieldConfig(enabled=True, blur_amount=12.0),
    ),
    "tech_demo": CameraEffectsConfig(
        vignette=VignetteConfig(enabled=True, intensity=0.2, spread=0.2),
        depth_of_field=DepthOfFieldConfig(enabled=True, blur_amount=6.0, track_focus=True),
    ),
    "minimal": CameraEffectsConfig(),  # No effects
    "immersive": CameraEffectsConfig(
        parallax=ParallaxConfig(enabled=True, intensity=0.4, auto_layers=True),
        vignette=VignetteConfig(enabled=True, intensity=0.4),
        perspective_tilt=PerspectiveTiltConfig(enabled=True, dynamic=True),
    ),
}


def get_effect_preset(name: str) -> CameraEffectsConfig:
    """Get a named effect preset."""
    return EFFECT_PRESETS.get(name, EFFECT_PRESETS["minimal"])


# Perlin noise implementation for natural shake
def _fade(t: float) -> float:
    """Fade function for Perlin noise."""
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + t * (b - a)


def _grad(hash_val: int, x: float) -> float:
    """Gradient function for 1D Perlin noise."""
    h = hash_val & 15
    grad = 1 + (h & 7)  # Gradient value in 1-8
    if h & 8:
        grad = -grad
    return grad * x


# Permutation table for Perlin noise
_PERM = [
    151, 160, 137, 91, 90, 15, 131, 13, 201, 95, 96, 53, 194, 233, 7, 225,
    140, 36, 103, 30, 69, 142, 8, 99, 37, 240, 21, 10, 23, 190, 6, 148,
    247, 120, 234, 75, 0, 26, 197, 62, 94, 252, 219, 203, 117, 35, 11, 32,
    57, 177, 33, 88, 237, 149, 56, 87, 174, 20, 125, 136, 171, 168, 68, 175,
    74, 165, 71, 134, 139, 48, 27, 166, 77, 146, 158, 231, 83, 111, 229, 122,
    60, 211, 133, 230, 220, 105, 92, 41, 55, 46, 245, 40, 244, 102, 143, 54,
    65, 25, 63, 161, 1, 216, 80, 73, 209, 76, 132, 187, 208, 89, 18, 169,
    200, 196, 135, 130, 116, 188, 159, 86, 164, 100, 109, 198, 173, 186, 3, 64,
    52, 217, 226, 250, 124, 123, 5, 202, 38, 147, 118, 126, 255, 82, 85, 212,
    207, 206, 59, 227, 47, 16, 58, 17, 182, 189, 28, 42, 223, 183, 170, 213,
    119, 248, 152, 2, 44, 154, 163, 70, 221, 153, 101, 155, 167, 43, 172, 9,
    129, 22, 39, 253, 19, 98, 108, 110, 79, 113, 224, 232, 178, 185, 112, 104,
    218, 246, 97, 228, 251, 34, 242, 193, 238, 210, 144, 12, 191, 179, 162, 241,
    81, 51, 145, 235, 249, 14, 239, 107, 49, 192, 214, 31, 181, 199, 106, 157,
    184, 84, 204, 176, 115, 121, 50, 45, 127, 4, 150, 254, 138, 236, 205, 93,
    222, 114, 67, 29, 24, 72, 243, 141, 128, 195, 78, 66, 215, 61, 156, 180,
]
_PERM = _PERM + _PERM  # Duplicate for easier indexing


def perlin_noise_1d(x: float, seed: int = 0) -> float:
    """
    1D Perlin noise for natural camera shake.

    Args:
        x: Input value
        seed: Random seed offset

    Returns:
        Noise value in range [-1, 1]
    """
    x = x + seed * 100  # Offset by seed
    xi = int(math.floor(x)) & 255
    xf = x - math.floor(x)
    u = _fade(xf)
    return _lerp(_grad(_PERM[xi], xf), _grad(_PERM[xi + 1], xf - 1), u)


def calculate_shake_offset(
    frame: int,
    fps: int,
    config: CameraShakeConfig,
) -> tuple[float, float, float]:
    """
    Calculate shake offset for a frame.

    Args:
        frame: Current frame number
        fps: Frames per second
        config: Shake configuration

    Returns:
        Tuple of (offset_x, offset_y, rotation_degrees)
    """
    if not config.enabled:
        return (0.0, 0.0, 0.0)

    time = frame / fps
    freq = config.frequency

    # Use different frequencies for each axis
    noise_x = perlin_noise_1d(time * freq, config.seed)
    noise_y = perlin_noise_1d(time * freq + 100, config.seed)
    noise_rot = perlin_noise_1d(time * freq + 200, config.seed)

    # Apply intensity
    intensity = config.intensity
    if config.decay > 0:
        decay_factor = 1.0 - (frame / (fps * 10)) * config.decay
        decay_factor = max(0, decay_factor)
        intensity *= decay_factor

    offset_x = noise_x * config.max_offset * intensity
    offset_y = noise_y * config.max_offset * intensity
    rotation = noise_rot * config.rotation_intensity * intensity

    return (offset_x, offset_y, rotation)
