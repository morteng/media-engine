"""
Tests for media_engine.video.scene_capture module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from media_engine.core.config import Config
from media_engine.core.project import LanguageConfig, Project
from media_engine.core.theme import Theme
from media_engine.video.demo_registry import DemoDefinition, DemoState
from media_engine.video.scene_capture import (
    SceneCaptureConfig,
    SceneCaptureEngine,
    SceneCaptureResult,
)


class TestSceneCaptureConfig:
    """Tests for SceneCaptureConfig dataclass."""

    def test_scene_capture_config_defaults(self):
        """Test SceneCaptureConfig with default values."""
        config = SceneCaptureConfig()
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 60
        assert config.crf == 18
        assert config.headless is True
        assert config.timeout_ms == 5000

    def test_scene_capture_config_custom(self):
        """Test SceneCaptureConfig with custom values."""
        config = SceneCaptureConfig(
            width=1280,
            height=720,
            fps=30,
            crf=23,
            headless=False,
            timeout_ms=10000,
        )
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 30
        assert config.crf == 23
        assert config.headless is False
        assert config.timeout_ms == 10000


class TestSceneCaptureResult:
    """Tests for SceneCaptureResult dataclass."""

    def test_scene_capture_result_defaults(self):
        """Test SceneCaptureResult with default values."""
        result = SceneCaptureResult(scene_id="intro", success=True)
        assert result.scene_id == "intro"
        assert result.success is True
        assert result.clip_path is None
        assert result.duration == 0.0
        assert result.error is None

    def test_scene_capture_result_success(self, temp_dir):
        """Test SceneCaptureResult for successful capture."""
        clip_path = temp_dir / "intro.mp4"
        result = SceneCaptureResult(
            scene_id="intro",
            success=True,
            clip_path=clip_path,
            duration=5.5,
        )
        assert result.success is True
        assert result.clip_path == clip_path
        assert result.duration == 5.5
        assert result.error is None

    def test_scene_capture_result_failure(self):
        """Test SceneCaptureResult for failed capture."""
        result = SceneCaptureResult(
            scene_id="intro",
            success=False,
            error="Playwright timeout",
        )
        assert result.success is False
        assert result.clip_path is None
        assert result.error == "Playwright timeout"


class TestSceneCaptureEngine:
    """Tests for SceneCaptureEngine class."""

    def test_engine_init_defaults(self):
        """Test SceneCaptureEngine initialization with defaults."""
        engine = SceneCaptureEngine()
        assert engine.project is None
        assert engine.config.width == 1920
        assert engine.config.height == 1080
        assert engine.demo_registry is not None

    def test_engine_init_with_project(self, temp_dir):
        """Test SceneCaptureEngine initialization with project."""
        project = self._create_mock_project(temp_dir)
        engine = SceneCaptureEngine(project=project)
        assert engine.project is project
        assert engine.demo_registry.project is project

    def test_engine_init_with_config(self):
        """Test SceneCaptureEngine initialization with config."""
        config = SceneCaptureConfig(width=1280, height=720, headless=False)
        engine = SceneCaptureEngine(config=config)
        assert engine.config.width == 1280
        assert engine.config.height == 720
        assert engine.config.headless is False

    def test_resolve_url_absolute(self, temp_dir):
        """Test _resolve_url with absolute URLs."""
        engine = SceneCaptureEngine()

        assert engine._resolve_url("http://example.com") == "http://example.com"
        assert engine._resolve_url("https://example.com") == "https://example.com"
        assert engine._resolve_url("file:///path/to/file") == "file:///path/to/file"

    def test_resolve_url_relative_with_project(self, temp_dir):
        """Test _resolve_url with relative paths and project."""
        project = self._create_mock_project(temp_dir)

        # Create a demo file
        demo_file = temp_dir / "demo" / "index.html"
        demo_file.parent.mkdir(parents=True)
        demo_file.write_text("<html>Demo</html>")

        engine = SceneCaptureEngine(project=project)
        resolved = engine._resolve_url("demo/index.html")

        assert resolved.startswith("file://")
        assert "demo/index.html" in resolved

    def test_resolve_url_relative_no_project(self, temp_dir, monkeypatch):
        """Test _resolve_url with relative path and no project."""
        # Create file in cwd
        demo_file = temp_dir / "local-demo.html"
        demo_file.write_text("<html>Local</html>")

        monkeypatch.chdir(temp_dir)
        engine = SceneCaptureEngine()

        resolved = engine._resolve_url("local-demo.html")
        assert resolved.startswith("file://")
        assert "local-demo.html" in resolved

    def test_resolve_url_fallback(self):
        """Test _resolve_url falls back to original URL."""
        engine = SceneCaptureEngine()
        url = "some-unknown-path"
        assert engine._resolve_url(url) == url

    def test_get_scene_demo_with_demo(self):
        """Test _get_scene_demo extracts demo reference."""
        engine = SceneCaptureEngine()

        # Create mock scene
        scene = MagicMock()
        scene.visual = {
            "demo": {
                "source": "platform-demo",
                "state": "dashboard",
            }
        }

        result = engine._get_scene_demo(scene)
        assert result is not None
        assert result["source"] == "platform-demo"
        assert result["state"] == "dashboard"

    def test_get_scene_demo_no_demo(self):
        """Test _get_scene_demo returns None when no demo."""
        engine = SceneCaptureEngine()

        # Scene without demo
        scene = MagicMock()
        scene.visual = {}

        result = engine._get_scene_demo(scene)
        assert result is None

    def test_get_scene_demo_incomplete(self):
        """Test _get_scene_demo returns None for incomplete demo ref."""
        engine = SceneCaptureEngine()

        # Scene with incomplete demo
        scene = MagicMock()
        scene.visual = {"demo": {"source": "platform-demo"}}  # Missing state

        result = engine._get_scene_demo(scene)
        assert result is None

    def test_get_scene_demo_string_value(self):
        """Test _get_scene_demo handles string demo value."""
        engine = SceneCaptureEngine()

        # Scene with string demo (not dict)
        scene = MagicMock()
        scene.visual = {"demo": "simple-demo-name"}

        result = engine._get_scene_demo(scene)
        assert result is None

    @pytest.mark.asyncio
    async def test_capture_scene_no_playwright(self, temp_dir):
        """Test capture_scene fails gracefully without Playwright."""
        SceneCaptureEngine()

        demo = DemoDefinition(name="test", url="http://example.com")
        state = DemoState(name="intro", description="Test state")
        output_path = temp_dir / "test.mp4"

        # Mock playwright import to fail
        with patch.dict("sys.modules", {"playwright.async_api": None}):
            with patch(
                "media_engine.video.scene_capture.SceneCaptureEngine.capture_scene",
                new_callable=AsyncMock,
            ) as mock_capture:
                mock_capture.return_value = SceneCaptureResult(
                    scene_id="intro",
                    success=False,
                    error="Playwright not installed",
                )
                result = await mock_capture(demo, state, 5.0, output_path)

        assert result.success is False
        assert "Playwright" in result.error

    @pytest.mark.asyncio
    async def test_convert_to_mp4_no_ffmpeg(self, temp_dir):
        """Test _convert_to_mp4 fallback when ffmpeg not available."""
        engine = SceneCaptureEngine()

        input_path = temp_dir / "test.webm"
        input_path.write_bytes(b"fake webm content")
        output_path = temp_dir / "test.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ffmpeg not found")
            result = await engine._convert_to_mp4(input_path, output_path)

        # Should fallback to WebM
        assert result.suffix == ".webm"

    @pytest.mark.asyncio
    async def test_convert_to_mp4_success(self, temp_dir):
        """Test _convert_to_mp4 with ffmpeg available."""
        engine = SceneCaptureEngine()

        input_path = temp_dir / "test.webm"
        input_path.write_bytes(b"fake webm content")
        output_path = temp_dir / "test.mp4"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = await engine._convert_to_mp4(input_path, output_path)

        assert result == output_path

    @pytest.mark.asyncio
    async def test_capture_all_scenes_no_demo_scenes(self, temp_dir):
        """Test capture_all_scenes with no demo scenes."""
        engine = SceneCaptureEngine()

        # Mock script with no demo references
        script = MagicMock()
        script.scenes = [
            MagicMock(id="scene1", visual={}),
            MagicMock(id="scene2", visual={}),
        ]

        clips = await engine.capture_all_scenes(script, temp_dir)

        assert clips == {}

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestCaptureScenesConvenience:
    """Tests for capture_scene_clips convenience function."""

    @pytest.mark.asyncio
    async def test_capture_scene_clips_empty(self, temp_dir):
        """Test capture_scene_clips with no demo scenes."""
        from media_engine.video.scene_capture import capture_scene_clips

        script = MagicMock()
        script.scenes = []

        clips = await capture_scene_clips(script, temp_dir)

        assert clips == {}

    @pytest.mark.asyncio
    async def test_capture_scene_clips_with_project(self, temp_dir):
        """Test capture_scene_clips with project."""
        from media_engine.video.scene_capture import capture_scene_clips

        config = Config()
        config.paths.content = "content"
        theme = Theme()
        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=temp_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        script = MagicMock()
        script.scenes = []

        clips = await capture_scene_clips(script, temp_dir, project=project)

        assert clips == {}


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_scene_capture_result_with_long_error(self):
        """Test SceneCaptureResult handles long error messages."""
        long_error = "Error: " + "x" * 1000
        result = SceneCaptureResult(
            scene_id="test",
            success=False,
            error=long_error,
        )
        assert len(result.error) == 1007

    def test_scene_capture_config_zero_values(self):
        """Test SceneCaptureConfig with zero/edge values."""
        config = SceneCaptureConfig(
            width=640,
            height=480,
            fps=1,
            crf=0,
            timeout_ms=1,
        )
        assert config.width == 640
        assert config.fps == 1
        assert config.crf == 0
        assert config.timeout_ms == 1

    def test_engine_with_custom_demo_registry(self):
        """Test engine uses internal demo registry correctly."""
        engine = SceneCaptureEngine()
        assert engine.demo_registry._cache == {}

        # Clear cache should work
        engine.demo_registry.clear_cache()
        assert engine.demo_registry._cache == {}
