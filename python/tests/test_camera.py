"""
Tests for camera system modules.

Tests cover:
- Camera capture (ElementBounds, CameraConfig, CameraKeyframe)
- Camera effects (effect configs, shake calculation, presets)
- Camera path (spline interpolation, easing, path generation)
- Camera presets (preset resolution, pattern generation)
"""

import math

import pytest

from media_engine.video.camera_capture import (
    CameraConfig,
    CameraKeyframe,
    ElementBounds,
)
from media_engine.video.camera_effects import (
    EFFECT_PRESETS,
    CameraEffectsConfig,
    CameraShakeConfig,
    VignetteConfig,
    calculate_shake_offset,
    get_effect_preset,
)
from media_engine.video.camera_path import (
    EASING_FUNCTIONS,
    CameraPathGenerator,
    CameraState,
    ResolvedKeyframe,
    catmull_rom_point,
    get_easing,
    lerp,
)
from media_engine.video.camera_presets import (
    CAMERA_PRESETS,
    CameraPreset,
    PresetResolver,
    get_preset as get_camera_preset,
    list_presets as list_camera_presets,
    resolve_preset,
)


class TestElementBounds:
    """Tests for ElementBounds dataclass."""

    def test_from_dict(self):
        """Test creating ElementBounds from dict."""
        data = {
            "x": 100,
            "y": 200,
            "width": 300,
            "height": 150,
            "centerX": 250,
            "centerY": 275,
        }
        bounds = ElementBounds.from_dict(data, selector=".test-element")

        assert bounds.x == 100
        assert bounds.y == 200
        assert bounds.width == 300
        assert bounds.height == 150
        assert bounds.center_x == 250
        assert bounds.center_y == 275
        assert bounds.selector == ".test-element"

    def test_to_dict(self):
        """Test serializing ElementBounds to dict."""
        bounds = ElementBounds(
            x=10,
            y=20,
            width=100,
            height=50,
            center_x=60,
            center_y=45,
            selector=".btn",
        )
        result = bounds.to_dict()

        assert result["x"] == 10
        assert result["y"] == 20
        assert result["width"] == 100
        assert result["height"] == 50
        assert result["centerX"] == 60
        assert result["centerY"] == 45
        assert "selector" not in result  # selector not in dict

    def test_with_padding(self):
        """Test creating bounds with padding."""
        bounds = ElementBounds(
            x=100,
            y=100,
            width=200,
            height=100,
            center_x=200,
            center_y=150,
        )
        padded = bounds.with_padding(20)

        assert padded.x == 80
        assert padded.y == 80
        assert padded.width == 240
        assert padded.height == 140
        assert padded.center_x == 200  # center unchanged
        assert padded.center_y == 150


class TestCameraKeyframe:
    """Tests for CameraKeyframe dataclass."""

    def test_from_dict_defaults(self):
        """Test creating keyframe with defaults."""
        data = {"target": ".main-content"}
        kf = CameraKeyframe.from_dict(data)

        assert kf.target == ".main-content"
        assert kf.zoom == 1.0
        assert kf.padding == 40
        assert kf.duration == 1.0
        assert kf.easing == "easeInOutCubic"
        assert kf.hold == 0.0
        assert kf.offset_x == 0
        assert kf.offset_y == 0

    def test_from_dict_full(self):
        """Test creating keyframe with all options."""
        data = {
            "target": ".header",
            "zoom": 2.5,
            "padding": 20,
            "duration": 1.5,
            "easing": "easeOutExpo",
            "hold": 2.0,
            "offset": {"x": 10, "y": -5},
        }
        kf = CameraKeyframe.from_dict(data)

        assert kf.target == ".header"
        assert kf.zoom == 2.5
        assert kf.padding == 20
        assert kf.duration == 1.5
        assert kf.easing == "easeOutExpo"
        assert kf.hold == 2.0
        assert kf.offset_x == 10
        assert kf.offset_y == -5


class TestCameraConfig:
    """Tests for CameraConfig dataclass."""

    def test_from_dict_defaults(self):
        """Test creating config with defaults."""
        data = {}
        config = CameraConfig.from_dict(data)

        assert config.mode == "static"
        assert config.capture_scale == 2.0
        assert config.background == "#1a1a2e"
        assert config.shadow is True
        assert config.focus_sequence == []
        assert config.preset is None

    def test_from_dict_with_focus_sequence(self):
        """Test creating config with focus sequence."""
        data = {
            "mode": "animated",
            "capture_scale": 3.0,
            "focus_sequence": [
                {"target": "fullpage", "zoom": 1.0},
                {"target": ".button", "zoom": 2.0},
            ],
        }
        config = CameraConfig.from_dict(data)

        assert config.mode == "animated"
        assert config.capture_scale == 3.0
        assert len(config.focus_sequence) == 2
        assert config.focus_sequence[0].target == "fullpage"
        assert config.focus_sequence[1].target == ".button"

    def test_get_all_selectors(self):
        """Test extracting selectors from focus sequence."""
        config = CameraConfig(
            focus_sequence=[
                CameraKeyframe(target="fullpage"),
                CameraKeyframe(target=".header"),
                CameraKeyframe(target="fullpage"),
                CameraKeyframe(target=".content"),
            ]
        )
        selectors = config.get_all_selectors()

        assert selectors == [".header", ".content"]
        assert "fullpage" not in selectors


class TestCameraEffects:
    """Tests for camera effects module."""

    def test_shake_offset_disabled(self):
        """Test shake returns zero when disabled."""
        config = CameraShakeConfig(enabled=False)
        offset = calculate_shake_offset(0, 30, config)

        assert offset == (0.0, 0.0, 0.0)

    def test_shake_offset_enabled(self):
        """Test shake produces non-zero offsets when enabled."""
        config = CameraShakeConfig(
            enabled=True,
            intensity=0.5,
            frequency=2.0,
            max_offset=10.0,
        )

        # Check multiple frames for variance
        offsets = [calculate_shake_offset(f, 30, config) for f in range(30)]

        # Should have some variation
        x_values = [o[0] for o in offsets]
        y_values = [o[1] for o in offsets]

        assert max(x_values) != min(x_values)  # some variation
        assert max(y_values) != min(y_values)

        # Should be within reasonable bounds (Perlin noise can exceed slightly)
        max_expected = 10.0 * 0.5 * 4  # noise can exceed by up to 4x
        for x, y, _ in offsets:
            assert abs(x) <= max_expected
            assert abs(y) <= max_expected

    def test_shake_decay(self):
        """Test shake intensity decays over time."""
        config = CameraShakeConfig(
            enabled=True,
            intensity=1.0,
            decay=1.0,
            max_offset=10.0,
        )

        # Early frames should have more shake
        early = calculate_shake_offset(0, 30, config)
        late = calculate_shake_offset(300, 30, config)  # 10 seconds in

        # Late shake should be zero or near zero
        assert abs(late[0]) < abs(early[0]) + 0.01 or early[0] == 0

    def test_effect_presets(self):
        """Test effect presets are available."""
        assert "cinematic" in EFFECT_PRESETS
        assert "documentary" in EFFECT_PRESETS
        assert "minimal" in EFFECT_PRESETS

        cinematic = get_effect_preset("cinematic")
        assert cinematic.vignette.enabled is True

        minimal = get_effect_preset("minimal")
        assert minimal.vignette.enabled is False

    def test_effects_config_from_dict(self):
        """Test creating effects config from dict."""
        data = {
            "vignette": {
                "enabled": True,
                "intensity": 0.6,
            },
            "camera_shake": {
                "enabled": True,
                "intensity": 0.2,
            },
        }
        config = CameraEffectsConfig.from_dict(data)

        assert config.vignette.enabled is True
        assert config.vignette.intensity == 0.6
        assert config.camera_shake.enabled is True
        assert config.camera_shake.intensity == 0.2

    def test_effects_config_to_dict(self):
        """Test serializing effects config."""
        config = CameraEffectsConfig(
            vignette=VignetteConfig(enabled=True, intensity=0.5),
        )
        result = config.to_dict()

        assert result["vignette"]["enabled"] is True
        assert result["vignette"]["intensity"] == 0.5

    def test_has_any_enabled(self):
        """Test checking if any effects are enabled."""
        empty = CameraEffectsConfig()
        assert empty.has_any_enabled() is False

        with_vignette = CameraEffectsConfig(
            vignette=VignetteConfig(enabled=True)
        )
        assert with_vignette.has_any_enabled() is True


class TestCameraPath:
    """Tests for camera path module."""

    def test_lerp(self):
        """Test linear interpolation."""
        assert lerp(0, 100, 0) == 0
        assert lerp(0, 100, 1) == 100
        assert lerp(0, 100, 0.5) == 50
        assert lerp(-10, 10, 0.5) == 0

    def test_easing_functions(self):
        """Test easing functions are available and valid."""
        for name in ["linear", "easeInOutCubic", "easeOutExpo", "easeInSine"]:
            fn = get_easing(name)
            assert fn(0) == 0 or abs(fn(0)) < 0.001
            assert fn(1) == 1 or abs(fn(1) - 1) < 0.001

    def test_easing_fallback(self):
        """Test unknown easing falls back to linear."""
        fn = get_easing("nonexistent")
        assert fn(0.5) == 0.5  # linear

    def test_catmull_rom_point(self):
        """Test Catmull-Rom spline interpolation."""
        # Simple straight line
        p0 = (0, 0)
        p1 = (10, 10)
        p2 = (20, 20)
        p3 = (30, 30)

        result = catmull_rom_point(p0, p1, p2, p3, 0.5)

        # Should be midpoint between p1 and p2
        assert 14 < result[0] < 16
        assert 14 < result[1] < 16

    def test_camera_state_to_dict(self):
        """Test CameraState serialization."""
        state = CameraState(
            frame=15,
            center_x=960.5,
            center_y=540.5,
            zoom=1.5,
        )
        result = state.to_dict()

        assert result["frame"] == 15
        assert result["centerX"] == 960.5
        assert result["centerY"] == 540.5
        assert result["zoom"] == 1.5

    def test_path_generator_resolve_keyframes(self):
        """Test resolving keyframes with element bounds."""
        generator = CameraPathGenerator()

        focus_sequence = [
            CameraKeyframe(target="fullpage", zoom=1.0, duration=0.5),
            CameraKeyframe(target=".button", zoom=2.0, duration=1.0, hold=0.5),
        ]

        element_bounds = {
            ".button": ElementBounds(
                x=100, y=200, width=150, height=50,
                center_x=175, center_y=225,
            ),
        }

        resolved = generator.resolve_keyframes(
            focus_sequence=focus_sequence,
            element_bounds=element_bounds,
            fps=30,
        )

        assert len(resolved) == 2
        assert resolved[0].zoom == 1.0
        assert resolved[1].center_x == 175
        assert resolved[1].center_y == 225
        assert resolved[1].zoom == 2.0

    def test_path_generator_interpolate_path(self):
        """Test generating interpolated path."""
        generator = CameraPathGenerator()

        keyframes = [
            ResolvedKeyframe(frame=0, center_x=0, center_y=0, zoom=1.0, easing="linear"),
            ResolvedKeyframe(frame=30, center_x=100, center_y=100, zoom=2.0, easing="linear"),
        ]

        states = generator.interpolate_path(keyframes, total_frames=31, use_spline=False)

        assert len(states) == 31
        assert states[0].center_x == 0
        assert states[0].zoom == 1.0
        assert states[30].center_x == 100
        assert states[30].zoom == 2.0

        # Midpoint should be interpolated
        assert 45 < states[15].center_x < 55
        assert 1.4 < states[15].zoom < 1.6

    def test_path_generator_empty_keyframes(self):
        """Test path generation with no keyframes."""
        generator = CameraPathGenerator()
        states = generator.interpolate_path([], total_frames=30)

        assert len(states) == 30
        # Should default to center
        assert states[0].zoom == 1.0


class TestCameraPresets:
    """Tests for camera presets module."""

    def test_presets_available(self):
        """Test built-in presets exist."""
        assert "guided_tour" in CAMERA_PRESETS
        assert "quick_overview" in CAMERA_PRESETS
        assert "dramatic_reveal" in CAMERA_PRESETS
        assert "cinematic" in CAMERA_PRESETS

    def test_get_preset(self):
        """Test getting preset by ID."""
        preset = get_camera_preset("guided_tour")
        assert preset is not None
        assert preset.name == "Guided Tour"
        assert preset.pattern == "sequential"

        missing = get_camera_preset("nonexistent")
        assert missing is None

    def test_list_presets(self):
        """Test listing all presets."""
        presets = list_camera_presets()
        assert len(presets) >= 5

        ids = [p["id"] for p in presets]
        assert "guided_tour" in ids
        assert "cinematic" in ids

    def test_resolve_preset_sequential(self):
        """Test resolving sequential preset."""
        selectors = [".header", ".content", ".footer"]
        keyframes = resolve_preset("guided_tour", selectors)

        # Should have: fullpage + 3 elements + fullpage
        assert len(keyframes) == 5
        assert keyframes[0].target == "fullpage"
        assert keyframes[1].target == ".header"
        assert keyframes[2].target == ".content"
        assert keyframes[3].target == ".footer"
        assert keyframes[4].target == "fullpage"

    def test_resolve_preset_zoom_out(self):
        """Test resolving zoom_out preset."""
        selectors = [".main"]
        keyframes = resolve_preset("dramatic_reveal", selectors)

        assert len(keyframes) == 2
        # First should be zoomed in
        assert keyframes[0].zoom > 2.0
        # Last should be zoomed out
        assert keyframes[1].zoom == 1.0

    def test_resolve_preset_custom_params(self):
        """Test resolving preset with custom params."""
        selectors = [".test"]
        keyframes = resolve_preset(
            "quick_overview",
            selectors,
            custom_params={"zoom": 3.0, "hold": 2.0},
        )

        # Custom params should be applied
        assert keyframes[1].zoom == 3.0
        assert keyframes[1].hold == 2.0

    def test_resolve_unknown_preset(self):
        """Test resolving unknown preset returns fallback."""
        keyframes = resolve_preset("nonexistent", [".foo"])

        # Should return simple fullpage
        assert len(keyframes) == 1
        assert keyframes[0].target == "fullpage"

    def test_preset_resolver_flow_pattern(self):
        """Test flow pattern has alternating easing."""
        resolver = PresetResolver()
        keyframes = resolver.resolve("follow_flow", [".a", ".b", ".c"])

        # Flow should use alternating easing
        easings = [kf.easing for kf in keyframes[1:-1]]  # skip first/last
        assert "easeInOutSine" in easings or "easeOutSine" in easings


class TestIntegration:
    """Integration tests for camera system."""

    def test_full_camera_data_generation(self):
        """Test generating complete camera data for Remotion."""
        from media_engine.video.camera_path import CameraPathGenerator
        from media_engine.video.camera_capture import CameraConfig

        config = CameraConfig.from_dict({
            "mode": "animated",
            "capture_scale": 2.0,
            "background": "#1a1a2e",
            "effects_preset": "cinematic",
            "focus_sequence": [
                {"target": "fullpage", "zoom": 1.0, "duration": 0.5},
                {"target": ".sidebar", "zoom": 2.0, "duration": 1.0, "hold": 1.0},
                {"target": "fullpage", "zoom": 1.0, "duration": 1.0},
            ],
        })

        element_bounds = {
            ".sidebar": ElementBounds(
                x=0, y=100, width=250, height=800,
                center_x=125, center_y=500,
            ),
        }

        generator = CameraPathGenerator()
        camera_data = generator.generate_camera_data(
            camera_config=config,
            element_bounds=element_bounds,
            total_frames=120,
            fps=30,
        )

        # Verify structure
        assert "mode" in camera_data
        assert "keyframes" in camera_data
        assert "element_bounds" in camera_data
        assert "effects" in camera_data
        assert "path_preview" in camera_data

        # Verify keyframes were processed
        assert len(camera_data["keyframes"]) == 3

        # Verify effects preset was applied
        assert camera_data["effects"]["vignette"]["enabled"] is True
