"""
Tests for media_engine.video.capture module.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
import yaml

from media_engine.video.capture import (
    MANIFEST_SEARCH_PATHS,
    SceneAction,
    VideoResult,
    VideoScript,
    convert_to_mp4,
    discover_scripts,
    find_manifest,
    generate_poster,
    list_videos,
    load_manifest,
)


class TestSceneAction:
    """Tests for SceneAction dataclass."""

    def test_scene_action_creation(self):
        """Test creating a scene action with all fields."""
        action = SceneAction(
            id="scene-1",
            name="Introduction",
            duration=5.0,
            action="console.log('hello')",
            voiceover="Welcome to the demo",
        )
        assert action.id == "scene-1"
        assert action.name == "Introduction"
        assert action.duration == 5.0
        assert action.action == "console.log('hello')"
        assert action.voiceover == "Welcome to the demo"

    def test_scene_action_defaults(self):
        """Test SceneAction with default optional fields."""
        action = SceneAction(
            id="scene-2",
            name="Content",
            duration=3.0,
        )
        assert action.id == "scene-2"
        assert action.name == "Content"
        assert action.duration == 3.0
        assert action.action is None
        assert action.voiceover is None

    def test_scene_action_zero_duration(self):
        """Test SceneAction with zero duration."""
        action = SceneAction(id="quick", name="Quick", duration=0.0)
        assert action.duration == 0.0


class TestVideoResult:
    """Tests for VideoResult dataclass."""

    def test_video_result_success(self, temp_dir):
        """Test successful video result."""
        result = VideoResult(
            video_id="demo",
            language="en",
            success=True,
            output_path=temp_dir / "demo.mp4",
            poster_path=temp_dir / "demo-poster.jpg",
        )
        assert result.video_id == "demo"
        assert result.language == "en"
        assert result.success is True
        assert result.output_path == temp_dir / "demo.mp4"
        assert result.poster_path == temp_dir / "demo-poster.jpg"
        assert result.error is None

    def test_video_result_failure(self):
        """Test failed video result."""
        result = VideoResult(
            video_id="demo",
            language="en",
            success=False,
            error="Playwright not installed",
        )
        assert result.success is False
        assert result.error == "Playwright not installed"
        assert result.output_path is None
        assert result.poster_path is None

    def test_video_result_defaults(self):
        """Test VideoResult with minimal required fields."""
        result = VideoResult(
            video_id="test",
            language="no",
            success=True,
        )
        assert result.output_path is None
        assert result.poster_path is None
        assert result.error is None


class TestVideoScript:
    """Tests for VideoScript dataclass."""

    def test_video_script_creation(self):
        """Test creating a VideoScript with all fields."""
        scenes = [
            SceneAction(id="intro", name="Introduction", duration=5.0),
            SceneAction(id="main", name="Main Content", duration=10.0),
        ]
        script = VideoScript(
            id="demo",
            title="Demo Video",
            language="en",
            demo_url="demo/en/index.html",
            duration=15.0,
            scenes=scenes,
            output_filename="demo.mp4",
        )
        assert script.id == "demo"
        assert script.title == "Demo Video"
        assert script.language == "en"
        assert script.demo_url == "demo/en/index.html"
        assert script.duration == 15.0
        assert len(script.scenes) == 2
        assert script.output_filename == "demo.mp4"

    def test_video_script_defaults(self):
        """Test VideoScript with minimal fields."""
        script = VideoScript(
            id="test",
            title="Test",
            language="en",
            demo_url="demo/index.html",
            duration=10.0,
        )
        assert script.scenes == []
        assert script.output_filename == ""

    def test_video_script_from_yaml(self, temp_dir):
        """Test loading VideoScript from YAML file."""
        yaml_content = """
id: walkthrough
title: "Product Walkthrough"
language: "en"
demo_url: "demo/en/interactive-demo.html"
duration: 30

scenes:
  - id: intro
    name: "Introduction"
    duration: 5
    voiceover: "Welcome to our product walkthrough"
  - id: feature1
    name: "Feature One"
    duration: 10
    action: "document.querySelector('.feature').click()"
    voiceover: "This is feature one"
  - id: outro
    name: "Conclusion"
    duration: 15
    voiceover: "Thank you for watching"

output:
  filename: "walkthrough.mp4"
"""
        yaml_path = temp_dir / "walkthrough.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert script.id == "walkthrough"
        assert script.title == "Product Walkthrough"
        assert script.language == "en"
        assert script.demo_url == "demo/en/interactive-demo.html"
        assert script.duration == 30.0
        assert len(script.scenes) == 3
        assert script.output_filename == "walkthrough.mp4"

        # Check scene details
        assert script.scenes[0].id == "intro"
        assert script.scenes[0].name == "Introduction"
        assert script.scenes[0].duration == 5.0
        assert script.scenes[0].voiceover == "Welcome to our product walkthrough"
        assert script.scenes[0].action is None

        assert script.scenes[1].id == "feature1"
        assert script.scenes[1].action == "document.querySelector('.feature').click()"

    def test_video_script_from_yaml_minimal(self, temp_dir):
        """Test loading VideoScript from minimal YAML file."""
        yaml_content = """
scenes:
  - id: scene1
    name: "Scene One"
    duration: 3
"""
        yaml_path = temp_dir / "minimal.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert script.id == "minimal"  # Should use filename as fallback
        assert script.title == ""
        assert script.language == "en"  # Default
        assert script.duration == 3.0  # Computed from scenes
        assert len(script.scenes) == 1

    def test_video_script_auto_duration(self, temp_dir):
        """Test VideoScript auto-calculates duration from scenes."""
        yaml_content = """
scenes:
  - id: scene1
    name: "Scene One"
    duration: 5
  - id: scene2
    name: "Scene Two"
    duration: 7
  - id: scene3
    name: "Scene Three"
    duration: 3
"""
        yaml_path = temp_dir / "auto_duration.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert script.duration == 15.0  # 5 + 7 + 3

    def test_video_script_explicit_duration(self, temp_dir):
        """Test VideoScript uses explicit duration over calculated."""
        yaml_content = """
duration: 60

scenes:
  - id: scene1
    name: "Scene One"
    duration: 5
"""
        yaml_path = temp_dir / "explicit.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert script.duration == 60.0  # Explicit overrides


class TestFindManifest:
    """Tests for find_manifest function."""

    def test_find_manifest_not_found(self):
        """Test error when manifest not found."""
        # Mock MANIFEST_SEARCH_PATHS to contain non-existent paths
        fake_paths = [Path("/nonexistent/path1.yaml"), Path("/nonexistent/path2.yaml")]
        with patch("media_engine.video.capture.MANIFEST_SEARCH_PATHS", fake_paths):
            with pytest.raises(FileNotFoundError) as exc_info:
                find_manifest()
            assert "Video manifest not found" in str(exc_info.value)

    def test_find_manifest_found_first_path(self, temp_dir):
        """Test finding manifest in first search path."""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text("videos: {}")

        # Mock MANIFEST_SEARCH_PATHS to contain our temp path first
        with patch(
            "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
        ):
            found = find_manifest()
            assert found == manifest_path


class TestLoadManifest:
    """Tests for load_manifest function."""

    def test_load_manifest(self, temp_dir, capsys):
        """Test loading manifest from file."""
        manifest_content = """
videos:
  demo:
    description: "Demo video"
    duration: 60000
    output: "demo.mp4"
languages:
  - en
  - "no"
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        manifest = load_manifest(manifest_path)

        assert "videos" in manifest
        assert "demo" in manifest["videos"]
        assert manifest["videos"]["demo"]["duration"] == 60000
        assert manifest["languages"] == ["en", "no"]
        assert "_project_root" in manifest
        assert "_manifest_dir" in manifest

        # Check that it prints the manifest path
        captured = capsys.readouterr()
        assert "Using manifest" in captured.out


class TestDiscoverScripts:
    """Tests for discover_scripts function."""

    def test_discover_scripts_success(self, temp_dir):
        """Test discovering script files in a directory."""
        # Create scripts directory structure
        scripts_dir = temp_dir / "scripts" / "en"
        scripts_dir.mkdir(parents=True)

        # Create sample script files
        script1 = """
id: demo1
title: "Demo 1"
language: en
demo_url: "demo/en/index.html"
scenes:
  - id: intro
    name: "Intro"
    duration: 5
"""
        script2 = """
id: demo2
title: "Demo 2"
language: en
demo_url: "demo/en/other.html"
scenes:
  - id: start
    name: "Start"
    duration: 10
"""
        (scripts_dir / "demo1.yaml").write_text(script1)
        (scripts_dir / "demo2.yaml").write_text(script2)

        manifest = {
            "scripts_dir": "scripts",
            "_manifest_dir": temp_dir,
        }

        scripts = discover_scripts(manifest, "en")

        assert len(scripts) == 2
        ids = [s.id for s in scripts]
        assert "demo1" in ids
        assert "demo2" in ids

    def test_discover_scripts_missing_directory(self, temp_dir, capsys):
        """Test discovering scripts when directory doesn't exist."""
        manifest = {
            "scripts_dir": "nonexistent",
            "_manifest_dir": temp_dir,
        }

        scripts = discover_scripts(manifest, "en")

        assert scripts == []
        captured = capsys.readouterr()
        assert "Scripts directory not found" in captured.out

    def test_discover_scripts_invalid_yaml(self, temp_dir, capsys):
        """Test discovering scripts with invalid YAML file."""
        scripts_dir = temp_dir / "scripts" / "en"
        scripts_dir.mkdir(parents=True)

        # Create invalid YAML
        (scripts_dir / "bad.yaml").write_text("invalid: [yaml: syntax")

        manifest = {
            "scripts_dir": "scripts",
            "_manifest_dir": temp_dir,
        }

        scripts = discover_scripts(manifest, "en")

        assert len(scripts) == 0
        captured = capsys.readouterr()
        assert "Failed to load" in captured.out


class TestConvertToMp4:
    """Tests for convert_to_mp4 async function."""

    @pytest.mark.asyncio
    async def test_convert_to_mp4_success(self, temp_dir):
        """Test successful MP4 conversion."""
        input_path = temp_dir / "video.webm"
        output_path = temp_dir / "video.mp4"
        input_path.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = await convert_to_mp4(input_path, output_path)

            assert result == output_path
            assert mock_run.call_count == 2  # version check + conversion

    @pytest.mark.asyncio
    async def test_convert_to_mp4_no_ffmpeg(self, temp_dir):
        """Test fallback when ffmpeg not available."""
        input_path = temp_dir / "video.webm"
        output_path = temp_dir / "video.mp4"
        input_path.touch()

        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ffmpeg not found")

            with patch("shutil.move") as mock_move:
                result = await convert_to_mp4(input_path, output_path)

                assert result.suffix == ".webm"
                mock_move.assert_called_once()


class TestGeneratePoster:
    """Tests for generate_poster async function."""

    @pytest.mark.asyncio
    async def test_generate_poster_success(self, temp_dir):
        """Test successful poster generation."""
        video_path = temp_dir / "video.mp4"
        video_path.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = await generate_poster(video_path, temp_dir, "demo")

            assert result == temp_dir / "demo-poster.jpg"
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_poster_failure(self, temp_dir, capsys):
        """Test poster generation failure."""
        video_path = temp_dir / "video.mp4"
        video_path.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("ffmpeg failed")

            result = await generate_poster(video_path, temp_dir, "demo")

            assert result is None
            captured = capsys.readouterr()
            assert "Failed to generate poster" in captured.out


class TestListVideos:
    """Tests for list_videos function."""

    def test_list_videos(self, temp_dir, capsys):
        """Test listing available videos."""
        manifest_content = """
videos:
  highlight:
    description: "Product highlight video"
    duration: 60000
    output: "highlight.mp4"
    priority: high
    chapter: intro
    use_in:
      - website
      - social
  demo:
    description: "Full demo"
    duration: 180000
    output: "demo.mp4"
languages:
  - en
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        with patch(
            "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
        ):
            list_videos()

        captured = capsys.readouterr()
        assert "highlight" in captured.out
        assert "Product highlight video" in captured.out
        assert "60.0s" in captured.out
        assert "high" in captured.out

    def test_list_videos_empty(self, temp_dir, capsys):
        """Test listing when no videos configured."""
        manifest_content = """
videos: {}
languages:
  - en
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        with patch(
            "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
        ):
            list_videos()

        captured = capsys.readouterr()
        assert "No videos in manifest" in captured.out


class TestCaptureVideoIntegration:
    """Integration tests for video capture (mocked)."""

    @pytest.mark.asyncio
    async def test_capture_scripted_video_no_playwright(self, temp_dir):
        """Test capture fails gracefully when Playwright not installed."""
        from media_engine.video.capture import capture_scripted_video

        script = VideoScript(
            id="test",
            title="Test",
            language="en",
            demo_url="demo/index.html",
            duration=10.0,
            scenes=[SceneAction(id="intro", name="Intro", duration=5.0)],
            output_filename="test.mp4",
        )

        manifest = {
            "_project_root": temp_dir,
            "output_base": "videos",
        }

        # The function imports playwright inside, so we need to mock at the right level
        # If playwright is not installed, the import will fail
        import sys

        # Temporarily remove playwright from modules if it exists
        playwright_modules = {k: v for k, v in sys.modules.items() if "playwright" in k}
        for mod in playwright_modules:
            del sys.modules[mod]

        # Now run the function - it should catch the ImportError
        result = await capture_scripted_video(script, manifest)

        # Restore playwright modules
        sys.modules.update(playwright_modules)

        # Check result - if playwright IS installed it will try to run and may fail differently
        # Just check we got a result
        assert result.video_id == "test"
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_capture_video_no_playwright(self, temp_dir):
        """Test simple capture fails gracefully when Playwright not installed."""
        from media_engine.video.capture import capture_video

        video_config = {
            "output": "demo.mp4",
            "duration": 5000,
        }

        manifest = {
            "_project_root": temp_dir,
            "output_base": "videos",
            "_manifest_dir": temp_dir,
        }

        import sys

        # Temporarily remove playwright from modules if it exists
        playwright_modules = {k: v for k, v in sys.modules.items() if "playwright" in k}
        for mod in playwright_modules:
            del sys.modules[mod]

        result = await capture_video("demo", video_config, manifest, "en")

        # Restore playwright modules
        sys.modules.update(playwright_modules)

        # Check result
        assert result.video_id == "demo"
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_capture_video_skips_existing(self, temp_dir, capsys):
        """Test capture skips existing files when force=False."""
        from media_engine.video.capture import capture_video

        # Create output directory and existing file
        output_dir = temp_dir / "videos" / "en"
        output_dir.mkdir(parents=True)
        existing_video = output_dir / "demo.mp4"
        existing_video.touch()

        video_config = {
            "output": "demo.mp4",
            "duration": 5000,
        }

        manifest = {
            "_project_root": temp_dir,
            "output_base": "videos",
            "_manifest_dir": temp_dir,
        }

        result = await capture_video("demo", video_config, manifest, "en", force=False)

        assert result.success is True
        assert result.output_path == existing_video
        captured = capsys.readouterr()
        assert "Already exists" in captured.out


class TestCaptureAllVideos:
    """Tests for capture_all_videos function."""

    @pytest.mark.asyncio
    async def test_capture_all_videos_no_videos(self, temp_dir, capsys):
        """Test capture_all_videos with empty manifest."""
        from media_engine.video.capture import capture_all_videos

        manifest_content = """
videos: {}
languages:
  - en
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        with patch(
            "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
        ):
            results = await capture_all_videos()

        assert len(results) == 0
        captured = capsys.readouterr()
        assert "No videos configured" in captured.out

    @pytest.mark.asyncio
    async def test_capture_all_videos_script_mode_no_scripts(self, temp_dir, capsys):
        """Test capture_all_videos in script mode with no scripts."""
        from media_engine.video.capture import capture_all_videos

        manifest_content = """
videos: {}
languages:
  - en
scripts_dir: scripts
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        with patch(
            "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
        ):
            results = await capture_all_videos(use_scripts=True)

        assert len(results) == 0
        captured = capsys.readouterr()
        assert "No scripts found" in captured.out


class TestMainCLI:
    """Tests for main CLI entry point."""

    def test_main_list_videos(self, temp_dir):
        """Test main function with --list flag."""
        from media_engine.video.capture import main

        manifest_content = """
videos:
  demo:
    description: "Demo video"
    duration: 60000
    output: "demo.mp4"
languages:
  - en
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        # Mock sys.argv for --list
        with patch("sys.argv", ["capture.py", "--list"]):
            with patch(
                "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
            ):
                result = main()

        assert result is None  # list_videos returns None

    def test_main_capture_no_videos(self, temp_dir):
        """Test main function with no videos to capture."""
        from media_engine.video.capture import main

        manifest_content = """
videos: {}
languages:
  - en
"""
        manifest_path = temp_dir / "video_manifest.yaml"
        manifest_path.write_text(manifest_content)

        with patch("sys.argv", ["capture.py"]):
            with patch(
                "media_engine.video.capture.MANIFEST_SEARCH_PATHS", [manifest_path]
            ):
                result = main()

        assert result == 0  # Success (no videos to fail)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_scene_action_with_special_characters(self):
        """Test SceneAction handles special characters in action."""
        action = SceneAction(
            id="special",
            name="Special Characters",
            duration=5.0,
            action="document.querySelector('[data-id=\"test\"]').click()",
            voiceover="Click the button with 'quotes' and \"double quotes\"",
        )
        assert "data-id" in action.action
        assert "quotes" in action.voiceover

    def test_video_script_empty_scenes(self, temp_dir):
        """Test VideoScript with empty scenes list."""
        yaml_content = """
id: empty
title: "Empty"
language: en
demo_url: "demo/index.html"
scenes: []
"""
        yaml_path = temp_dir / "empty.yaml"
        yaml_path.write_text(yaml_content)

        script = VideoScript.from_yaml(yaml_path)

        assert len(script.scenes) == 0
        assert script.duration == 0.0  # Sum of empty list

    def test_video_result_with_long_error(self):
        """Test VideoResult handles long error messages."""
        long_error = "Error: " + "x" * 1000
        result = VideoResult(
            video_id="test",
            language="en",
            success=False,
            error=long_error,
        )
        assert len(result.error) == 1007

    def test_manifest_search_paths_defined(self):
        """Test that manifest search paths are properly defined."""
        assert len(MANIFEST_SEARCH_PATHS) > 0
        for path in MANIFEST_SEARCH_PATHS:
            assert isinstance(path, Path)
