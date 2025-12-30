"""
Tests for media_engine.web.routes.video module.

Tests video production API routes including:
- Script management (list, get, update)
- Render queue management
- Asset listing
- Motion component catalog
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from media_engine.core.config import Config
from media_engine.core.project import LanguageConfig, Project
from media_engine.core.theme import Theme


class TestVideoRoutes:
    """Tests for video production API routes."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project with video scripts."""
        # Create project structure
        content_dir = temp_dir / "content"
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        # Create video script
        script_content = """
title: Test Video
description: A test video script
metadata:
  version: "1.0.0"
  status: draft
scenes:
  - id: intro
    name: Introduction
    type: intro
    duration: 5
    voiceover: "Welcome to the test"
  - id: main
    name: Main Content
    type: feature
    duration: 10
    voiceover: "Here is the main content"
  - id: outro
    name: Conclusion
    type: outro
    duration: 5
    voiceover: "Thanks for watching"
"""
        script_file = en_scripts / "test-video.yaml"
        script_file.write_text(script_content)

        # Create output directory
        output_dir = temp_dir / "output" / "en" / "videos"
        output_dir.mkdir(parents=True)

        # Create a mock output video
        output_video = output_dir / "test-video.mp4"
        output_video.write_bytes(b"fake video content")

        # Create remotion demos directory
        demos_dir = temp_dir / "remotion" / "public" / "demos"
        demos_dir.mkdir(parents=True)
        demo_clip = demos_dir / "demo-clip.mp4"
        demo_clip.write_bytes(b"fake demo clip")

        # Create project
        return self._create_mock_project(temp_dir)

    def _create_mock_project(self, root: Path, languages=None):
        """Helper to create mock project."""
        if languages is None:
            languages = ["en"]

        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {
            lang: LanguageConfig(code=lang, name=lang.upper(), locale=f"{lang}-{lang.upper()}")
            for lang in languages
        }

        project = Project(
            root=root,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project

    @pytest.fixture
    def mock_manager(self):
        """Create mock WebSocket connection manager."""
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    def test_video_routes_registration(self, mock_project, mock_manager):
        """Test that video routes can be registered."""
        from fastapi import APIRouter

        from media_engine.web.routes.video import register_video_routes

        router = APIRouter()
        register_video_routes(router, lambda: mock_project, mock_manager)

        # Check routes were registered
        route_paths = [route.path for route in router.routes]
        assert "/api/video/scripts" in route_paths
        assert "/api/video/scripts/{script_id:path}" in route_paths
        assert "/api/video/render" in route_paths
        assert "/api/video/render/{job_id}" in route_paths
        assert "/api/video/queue" in route_paths
        assert "/api/video/assets" in route_paths
        assert "/api/video/components" in route_paths
        assert "/api/video/voices" in route_paths


class TestListVideoScripts:
    """Tests for list_video_scripts endpoint."""

    @pytest.fixture
    def project_with_scripts(self, temp_dir):
        """Create project with multiple video scripts."""
        content_dir = temp_dir / "content"

        # English scripts
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        script1 = en_scripts / "intro.yaml"
        script1.write_text("""
title: Introduction Video
description: An intro video
metadata:
  version: "1.0.0"
  status: published
scenes:
  - id: scene1
    duration: 5
  - id: scene2
    duration: 10
""")

        script2 = en_scripts / "demo.yaml"
        script2.write_text("""
title: Demo Video
description: A demonstration
metadata:
  version: "2.0.0"
  status: draft
scenes:
  - id: intro
    duration: 3
""")

        # Norwegian script
        no_scripts = content_dir / "no" / "scripts"
        no_scripts.mkdir(parents=True)

        script3 = no_scripts / "intro.yaml"
        script3.write_text("""
title: Introduksjonsvideo
description: En introduksjonsvideo
scenes:
  - id: intro
    duration: 5
""")

        # Create mock project
        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {
            "en": LanguageConfig(code="en", name="English", locale="en-US"),
            "no": LanguageConfig(code="no", name="Norwegian", locale="nb-NO"),
        }

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.mark.asyncio
    async def test_list_scripts_returns_all_scripts(self, project_with_scripts, mock_manager):
        """Test that all scripts are listed."""
        from fastapi import APIRouter
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        # Create test app
        from fastapi import FastAPI

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_scripts, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/scripts")

        assert response.status_code == 200
        data = response.json()
        assert "scripts" in data
        assert "count" in data
        assert data["count"] == 3

        # Check script IDs
        script_ids = [s["id"] for s in data["scripts"]]
        assert "en/intro" in script_ids
        assert "en/demo" in script_ids
        assert "no/intro" in script_ids

    @pytest.mark.asyncio
    async def test_list_scripts_includes_metadata(self, project_with_scripts, mock_manager):
        """Test that script metadata is included."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_scripts, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/scripts")
        data = response.json()

        # Find intro script
        intro_script = next(s for s in data["scripts"] if s["id"] == "en/intro")
        assert intro_script["name"] == "Introduction Video"
        assert intro_script["version"] == "1.0.0"
        assert intro_script["status"] == "published"
        assert intro_script["scenes"] == 2
        assert intro_script["duration"] == 15  # 5 + 10


class TestGetVideoScript:
    """Tests for get_video_script endpoint."""

    @pytest.fixture
    def project_with_script(self, temp_dir):
        """Create project with a single script."""
        content_dir = temp_dir / "content"
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        script = en_scripts / "test.yaml"
        script.write_text("""
title: Test Script
description: A test script
scenes:
  - id: intro
    duration: 5
""")

        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_get_script_returns_content(self, project_with_script, mock_manager):
        """Test that script content is returned."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/scripts/en/test")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "en/test"
        assert "content" in data
        assert "parsed" in data
        assert data["parsed"]["title"] == "Test Script"

    @pytest.mark.asyncio
    async def test_get_script_not_found(self, project_with_script, mock_manager):
        """Test 404 for non-existent script."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/scripts/en/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_script_invalid_format(self, project_with_script, mock_manager):
        """Test 400 for invalid script ID format."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/scripts/invalid-format")

        assert response.status_code == 400


class TestUpdateVideoScript:
    """Tests for update_video_script endpoint."""

    @pytest.fixture
    def project_with_script(self, temp_dir):
        """Create project with a single script."""
        content_dir = temp_dir / "content"
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        script = en_scripts / "test.yaml"
        script.write_text("""
title: Original Title
scenes:
  - id: intro
    duration: 5
""")

        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_update_script_success(self, project_with_script, mock_manager):
        """Test successful script update."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        new_content = """
title: Updated Title
scenes:
  - id: intro
    duration: 10
"""
        response = client.put("/api/video/scripts/en/test", json={"content": new_content})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # Verify broadcast was called
        mock_manager.broadcast.assert_called()

    @pytest.mark.asyncio
    async def test_update_script_invalid_yaml(self, project_with_script, mock_manager):
        """Test update with invalid YAML fails."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        invalid_content = "title: [invalid yaml"
        response = client.put("/api/video/scripts/en/test", json={"content": invalid_content})

        assert response.status_code == 400


class TestRenderManagement:
    """Tests for render queue management endpoints."""

    @pytest.fixture
    def project_with_script(self, temp_dir):
        """Create project with a script for rendering."""
        content_dir = temp_dir / "content"
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        script = en_scripts / "render-test.yaml"
        script.write_text("""
title: Render Test
scenes:
  - id: scene1
    duration: 5
""")

        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_start_render_creates_job(self, project_with_script, mock_manager):
        """Test that starting a render creates a job."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.post(
            "/api/video/render",
            json={"script_id": "en/render-test", "quality": "preview"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_start_render_invalid_script(self, project_with_script, mock_manager):
        """Test starting render for non-existent script fails."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.post(
            "/api/video/render",
            json={"script_id": "en/nonexistent", "quality": "preview"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_render_queue(self, project_with_script, mock_manager):
        """Test getting render queue."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_script, mock_manager)
        app.include_router(router)

        client = TestClient(app)

        # Start a render first
        client.post(
            "/api/video/render",
            json={"script_id": "en/render-test", "quality": "preview"},
        )

        # Get queue
        response = client.get("/api/video/queue")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "active" in data
        assert "completed" in data
        assert "failed" in data
        assert len(data["jobs"]) >= 1


class TestVideoAssets:
    """Tests for video assets listing endpoint."""

    @pytest.fixture
    def project_with_assets(self, temp_dir):
        """Create project with video assets."""
        # Create demo clips
        demos_dir = temp_dir / "remotion" / "public" / "demos"
        demos_dir.mkdir(parents=True)
        (demos_dir / "demo1.mp4").write_bytes(b"demo1 content")
        (demos_dir / "demo2.mp4").write_bytes(b"demo2 content")

        # Create audio files
        audio_dir = temp_dir / "output" / "en" / "videos"
        audio_dir.mkdir(parents=True)
        (audio_dir / "intro.mp3").write_bytes(b"audio content")

        # Create output videos
        (audio_dir / "intro.mp4").write_bytes(b"video content")

        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_list_assets_returns_categories(self, project_with_assets, mock_manager):
        """Test that assets are returned in categories."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_assets, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/assets")

        assert response.status_code == 200
        data = response.json()
        assert "demos" in data
        assert "audio" in data
        assert "outputs" in data
        assert len(data["demos"]) == 2


class TestMotionComponents:
    """Tests for motion graphics components endpoint."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_list_components_returns_catalog(self, mock_project, mock_manager):
        """Test that component catalog is returned."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: mock_project, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/components")

        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "backgrounds" in data
        assert "transitions" in data
        assert "text_effects" in data

        # Check some known components
        component_ids = [c["id"] for c in data["components"]]
        assert "TitleCard" in component_ids
        assert "TextReveal" in component_ids
        assert "Background" in component_ids

        # Check backgrounds
        assert "aurora" in data["backgrounds"]
        assert "dark" in data["backgrounds"]

        # Check transitions
        assert "glitch" in data["transitions"]
        assert "fade" in data["transitions"]


class TestEstimateDuration:
    """Tests for duration estimation helper."""

    def test_estimate_duration_basic(self):
        """Test basic duration estimation."""
        from media_engine.web.routes.video import _estimate_duration

        script_data = {
            "scenes": [
                {"duration": 5},
                {"duration": 10},
                {"duration": 15},
            ]
        }

        result = _estimate_duration(script_data)
        assert result == 30

    def test_estimate_duration_default_duration(self):
        """Test duration estimation with missing durations."""
        from media_engine.web.routes.video import _estimate_duration

        script_data = {
            "scenes": [
                {"duration": 5},
                {},  # Should use default of 5
                {"duration": 10},
            ]
        }

        result = _estimate_duration(script_data)
        assert result == 20  # 5 + 5 + 10

    def test_estimate_duration_no_scenes(self):
        """Test duration estimation with no scenes."""
        from media_engine.web.routes.video import _estimate_duration

        script_data = {"scenes": []}
        result = _estimate_duration(script_data)
        assert result is None

    def test_estimate_duration_missing_scenes(self):
        """Test duration estimation with missing scenes key."""
        from media_engine.web.routes.video import _estimate_duration

        script_data = {}
        result = _estimate_duration(script_data)
        assert result is None


class TestPreviewConfig:
    """Tests for preview configuration endpoint."""

    @pytest.fixture
    def project_with_remotion(self, temp_dir):
        """Create project with remotion setup."""
        # Create remotion directory
        remotion_dir = temp_dir / "remotion"
        remotion_dir.mkdir(parents=True)
        (remotion_dir / "package.json").write_text('{"name": "remotion"}')

        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def project_without_remotion(self, temp_dir):
        """Create project without remotion setup."""
        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"

        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        return Project(root=temp_dir, config=config, theme=theme, languages=lang_configs, source_language="en")

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_get_preview_config_with_remotion(self, project_with_remotion, mock_manager):
        """Test preview config when remotion exists."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_with_remotion, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/preview/config")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert "studio_url" in data
        assert "compositions" in data
        assert data["studio_port"] == 3001

    @pytest.mark.asyncio
    async def test_get_preview_config_without_remotion(self, project_without_remotion, mock_manager):
        """Test preview config when remotion doesn't exist."""
        from fastapi import APIRouter, FastAPI
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: project_without_remotion, mock_manager)
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/preview/config")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False


class TestCameraPresets:
    """Tests for camera preset API routes."""

    def test_list_camera_presets(self):
        """Test listing camera animation presets."""
        from fastapi import FastAPI, APIRouter
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: None, MagicMock())
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/camera/presets")

        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "count" in data
        assert data["count"] >= 5  # Should have at least 5 presets

        # Check preset structure
        presets = data["presets"]
        assert len(presets) > 0

        preset = presets[0]
        assert "id" in preset
        assert "name" in preset
        assert "description" in preset
        assert "pattern" in preset
        assert "default_zoom" in preset

    def test_list_camera_easings(self):
        """Test listing camera easing functions."""
        from fastapi import FastAPI, APIRouter
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: None, MagicMock())
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/camera/easings")

        assert response.status_code == 200
        data = response.json()
        assert "easings" in data
        assert "count" in data
        assert "recommended" in data

        # Check easing structure
        easings = data["easings"]
        assert len(easings) > 0

        easing = easings[0]
        assert "name" in easing
        assert "recommended" in easing

        # Should have recommended easing functions
        recommended_names = [e["name"] for e in easings if e["recommended"]]
        assert "easeInOutCubic" in recommended_names

    def test_list_effect_presets(self):
        """Test listing visual effects presets."""
        from fastapi import FastAPI, APIRouter
        from fastapi.testclient import TestClient

        from media_engine.web.routes.video import register_video_routes

        app = FastAPI()
        router = APIRouter()
        register_video_routes(router, lambda: None, MagicMock())
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/api/video/effects/presets")

        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "count" in data

        # Check preset structure
        presets = data["presets"]
        assert len(presets) > 0

        preset = presets[0]
        assert "id" in preset
        assert "name" in preset
        assert "description" in preset
        assert "vignette_enabled" in preset


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture providing a temporary directory."""
    return tmp_path


@pytest.fixture
def mock_manager():
    """Fixture providing a mock WebSocket manager."""
    manager = MagicMock()
    manager.broadcast = AsyncMock()
    return manager
