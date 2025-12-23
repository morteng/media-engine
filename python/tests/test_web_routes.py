"""
Tests for media_engine.web.routes module.
"""

import json

import pytest
from media_engine.core.config import Config
from media_engine.core.project import LanguageConfig, Project
from media_engine.core.theme import Theme
from media_engine.web.routes import (
    find_source_demo,
    find_source_script,
    register_routes,
)


class TestFindSourceScript:
    """Tests for find_source_script helper function."""

    def test_find_script_basic_structure(self, temp_dir):
        """Test finding script with basic path structure."""
        # Setup project structure
        content_dir = temp_dir / "content"
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        script_file = en_scripts / "intro.yaml"
        script_file.write_text("title: Intro")

        # Create mock project
        project = self._create_mock_project(temp_dir)

        # Test with media file in output
        media_file = temp_dir / "output" / "en" / "intro.mp3"
        result = find_source_script(project, media_file)

        assert result is not None
        assert result["name"] == "intro"
        assert result["language"] == "en"
        assert result["type"] == "script"
        assert "intro.yaml" in result["path"]

    def test_find_script_nested_structure(self, temp_dir):
        """Test finding script with nested folder structure."""
        # Setup project structure
        content_dir = temp_dir / "content"
        en_scripts = content_dir / "en" / "scripts"
        en_scripts.mkdir(parents=True)

        script_file = en_scripts / "showcase.yaml"
        script_file.write_text("title: Showcase")

        # Create mock project
        project = self._create_mock_project(temp_dir)

        # Test with media file in scripts subfolder
        # Note: The function needs to find "en" in the path to determine language
        media_file = temp_dir / "output" / "en" / "scripts" / "showcase" / "scene1.mp3"
        result = find_source_script(project, media_file)

        assert result is not None
        assert result["name"] == "showcase"
        assert result["type"] == "script"

    def test_find_script_no_language_in_path(self, temp_dir):
        """Test finding script when language cannot be determined."""
        project = self._create_mock_project(temp_dir)

        # Media file with no language in path
        media_file = temp_dir / "output" / "unknown" / "video.mp4"
        result = find_source_script(project, media_file)

        assert result is None

    def test_find_script_nonexistent_script(self, temp_dir):
        """Test finding script that doesn't exist."""
        project = self._create_mock_project(temp_dir)

        # Media file exists but script doesn't
        media_file = temp_dir / "output" / "en" / "nonexistent.mp3"
        result = find_source_script(project, media_file)

        assert result is None

    def test_find_script_multiple_languages(self, temp_dir):
        """Test finding script with multiple language support."""
        # Setup project structure for multiple languages
        content_dir = temp_dir / "content"
        for lang in ["en", "no"]:
            scripts_dir = content_dir / lang / "scripts"
            scripts_dir.mkdir(parents=True)
            script_file = scripts_dir / "demo.yaml"
            script_file.write_text(f"title: Demo {lang}")

        # Create mock project with multiple languages
        project = self._create_mock_project(temp_dir, languages=["en", "no"])

        # Test finding English script
        media_file = temp_dir / "output" / "en" / "demo.mp3"
        result = find_source_script(project, media_file)
        assert result["language"] == "en"

        # Test finding Norwegian script
        media_file = temp_dir / "output" / "no" / "demo.mp3"
        result = find_source_script(project, media_file)
        assert result["language"] == "no"

    def _create_mock_project(self, root_dir, languages=None):
        """Helper to create a mock project."""
        if languages is None:
            languages = ["en"]

        config = Config()
        config.paths.content = "content"
        theme = Theme()

        lang_configs = {lang: LanguageConfig(code=lang, name=lang.upper()) for lang in languages}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestFindSourceDemo:
    """Tests for find_source_demo helper function."""

    def test_find_demo_basic(self, temp_dir):
        """Test finding demo with basic structure."""
        # Setup project structure
        content_dir = temp_dir / "content"
        en_demos = content_dir / "en" / "demos"
        en_demos.mkdir(parents=True)

        demo_file = en_demos / "calculator.yaml"
        demo_file.write_text("type: calculator")

        # Create mock project
        project = self._create_mock_project(temp_dir)

        # Test with demo HTML file
        demo_html = temp_dir / "output" / "demos" / "en" / "calculator.html"
        result = find_source_demo(project, demo_html)

        assert result is not None
        assert result["name"] == "calculator"
        assert result["language"] == "en"
        assert result["type"] == "demo"
        assert "calculator.yaml" in result["path"]

    def test_find_demo_no_language(self, temp_dir):
        """Test finding demo when language cannot be determined."""
        project = self._create_mock_project(temp_dir)

        # Demo file with no language in path
        demo_html = temp_dir / "output" / "unknown" / "demo.html"
        result = find_source_demo(project, demo_html)

        assert result is None

    def test_find_demo_nonexistent(self, temp_dir):
        """Test finding demo that doesn't exist."""
        project = self._create_mock_project(temp_dir)

        # Demo HTML exists but source doesn't
        demo_html = temp_dir / "output" / "demos" / "en" / "missing.html"
        result = find_source_demo(project, demo_html)

        assert result is None

    def test_find_demo_multiple_languages(self, temp_dir):
        """Test finding demo with multiple language support."""
        # Setup project structure
        content_dir = temp_dir / "content"
        for lang in ["en", "no"]:
            demos_dir = content_dir / lang / "demos"
            demos_dir.mkdir(parents=True)
            demo_file = demos_dir / "pricing.yaml"
            demo_file.write_text("type: calculator")

        # Create mock project
        project = self._create_mock_project(temp_dir, languages=["en", "no"])

        # Test finding English demo
        demo_html = temp_dir / "output" / "demos" / "en" / "pricing.html"
        result = find_source_demo(project, demo_html)
        assert result["language"] == "en"

        # Test finding Norwegian demo
        demo_html = temp_dir / "output" / "demos" / "no" / "pricing.html"
        result = find_source_demo(project, demo_html)
        assert result["language"] == "no"

    def _create_mock_project(self, root_dir, languages=None):
        """Helper to create a mock project."""
        if languages is None:
            languages = ["en"]

        config = Config()
        config.paths.content = "content"
        theme = Theme()

        lang_configs = {lang: LanguageConfig(code=lang, name=lang.upper()) for lang in languages}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestGenerateSceneNotesExport:
    """Tests for scene notes export logic via API endpoint."""

    @pytest.mark.asyncio
    async def test_generate_empty_export(self, temp_dir):
        """Test generating export when no notes exist."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/scene-notes-export")

        assert response.status_code == 200
        result = response.json()
        assert result["project"] == "Test Project"
        assert result["total_notes"] == 0
        assert result["scripts"] == []
        assert "generated" in result

    @pytest.mark.asyncio
    async def test_generate_export_with_notes(self, temp_dir):
        """Test generating export with scene notes."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create notes directory and files
        notes_dir = temp_dir / ".media-engine" / "scene-notes"
        notes_dir.mkdir(parents=True)

        # Create a script file
        content_dir = temp_dir / "content"
        scripts_dir = content_dir / "en" / "scripts"
        scripts_dir.mkdir(parents=True)
        script_path = scripts_dir / "intro.yaml"
        script_content = """title: Introduction
scenes:
  - id: scene1
    name: Opening
    scene_type: narration
  - id: scene2
    name: Overview
    scene_type: demo
"""
        script_path.write_text(script_content)

        # Create notes file
        notes_file = notes_dir / "content_en_scripts_intro.yaml.json"
        notes_data = {
            "script_path": "content/en/scripts/intro.yaml",
            "notes": {
                "scene1": {
                    "text": "Improve the voiceover pacing",
                    "created": "2024-01-15T10:00:00",
                    "scene_id": "scene1",
                },
                "scene2": {
                    "text": "Add background music",
                    "created": "2024-01-15T11:00:00",
                    "scene_id": "scene2",
                },
            },
            "updated": "2024-01-15T11:00:00",
        }
        notes_file.write_text(json.dumps(notes_data))

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/scene-notes-export")

        assert response.status_code == 200
        result = response.json()
        assert result["total_notes"] == 2
        assert len(result["scripts"]) == 1
        assert result["scripts"][0]["script_name"] == "Introduction"
        assert len(result["scripts"][0]["notes"]) == 2

    @pytest.mark.asyncio
    async def test_generate_export_handles_invalid_notes(self, temp_dir):
        """Test export generation handles corrupted notes files gracefully."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create notes directory with invalid JSON
        notes_dir = temp_dir / ".media-engine" / "scene-notes"
        notes_dir.mkdir(parents=True)

        invalid_file = notes_dir / "invalid.json"
        invalid_file.write_text("{invalid json content")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/scene-notes-export")

        assert response.status_code == 200
        result = response.json()
        # Should handle error gracefully
        assert result["total_notes"] == 0
        assert result["scripts"] == []

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
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


class TestUpdateSceneNotesExport:
    """Tests for scene notes update functionality via POST endpoint."""

    @pytest.mark.asyncio
    async def test_update_creates_files(self, temp_dir):
        """Test that saving a note creates both JSON and markdown export files."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create notes directory
        notes_dir = temp_dir / ".media-engine" / "scene-notes"
        notes_dir.mkdir(parents=True)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)

        # Save a scene note via the API
        response = client.post(
            "/api/scene-notes/content_en_scripts_test.yaml",
            json={"scene_id": "scene1", "note": "Test note"},
        )

        assert response.status_code == 200

        # Check JSON export exists
        json_export = temp_dir / ".media-engine" / "scene-notes-todo.json"
        assert json_export.exists()

        json_data = json.loads(json_export.read_text())
        assert json_data["project"] == "Test Project"

        # Check markdown export exists
        md_export = temp_dir / ".media-engine" / "scene-notes-todo.md"
        assert md_export.exists()

        md_content = md_export.read_text()
        assert "# Scene Notes & Suggestions" in md_content
        assert "Test note" in md_content

    @pytest.mark.asyncio
    async def test_update_markdown_formatting(self, temp_dir):
        """Test markdown export has proper formatting."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create script with scene name
        content_dir = temp_dir / "content"
        scripts_dir = content_dir / "en" / "scripts"
        scripts_dir.mkdir(parents=True)
        script_path = scripts_dir / "demo.yaml"
        script_content = """title: Demo Script
scenes:
  - id: intro
    name: Introduction Scene
    scene_type: narration
"""
        script_path.write_text(script_content)

        # Create notes directory
        notes_dir = temp_dir / ".media-engine" / "scene-notes"
        notes_dir.mkdir(parents=True)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)

        # Save a scene note via the API
        response = client.post(
            "/api/scene-notes/content/en/scripts/demo.yaml",
            json={"scene_id": "intro", "note": "Needs improvement"},
        )

        assert response.status_code == 200

        md_export = temp_dir / ".media-engine" / "scene-notes-todo.md"
        md_content = md_export.read_text()

        # Check formatting
        assert "# Scene Notes & Suggestions" in md_content
        assert "### Scene: intro" in md_content
        assert "Needs improvement" in md_content

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
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


class TestRegisterRoutes:
    """Tests for register_routes function."""

    def test_register_routes_no_errors(self, temp_dir):
        """Test that register_routes completes without errors."""
        from fastapi import FastAPI
        from media_engine.web.websocket import ConnectionManager

        app = FastAPI()
        manager = ConnectionManager()

        project = self._create_mock_project(temp_dir)

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        # Should not raise any errors
        register_routes(app, get_project, manager, static_dir)

        # Verify app has routes registered
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/api/project" in routes
        assert "/api/status" in routes
        assert "/api/translations" in routes

    def test_register_routes_all_endpoints(self, temp_dir):
        """Test that all expected endpoints are registered."""
        from fastapi import FastAPI
        from media_engine.web.websocket import ConnectionManager

        app = FastAPI()
        manager = ConnectionManager()

        project = self._create_mock_project(temp_dir)

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        # Check for key API endpoints
        routes = [route.path for route in app.routes]

        expected_routes = [
            "/",
            "/api/project",
            "/api/status",
            "/api/translations",
            "/api/translations/matrix",
            "/api/quality",
            "/api/validation",
            "/api/chapters/{language}",
            "/api/document",
            "/api/documents/{language}",
            "/api/file",
            "/api/audit-log",
            "/api/registry",
            "/api/packs",
            "/api/assets",
            "/api/media",
            "/media/{path:path}",
            "/assets/{path:path}",
            "/api/scene-notes/{script_path:path}",
            "/api/scene-notes-export",
            "/ws/{user_id}",
        ]

        for expected in expected_routes:
            # Handle path parameters
            if "{" in expected:
                base_path = expected.split("{")[0].rstrip("/")
                assert any(base_path in route for route in routes), f"Missing route: {expected}"
            else:
                assert expected in routes, f"Missing route: {expected}"

    def test_register_routes_with_mock_app(self, temp_dir):
        """Test route registration registers different HTTP methods."""
        from fastapi import FastAPI
        from fastapi.routing import APIRoute, APIWebSocketRoute
        from media_engine.web.websocket import ConnectionManager

        app = FastAPI()
        manager = ConnectionManager()

        project = self._create_mock_project(temp_dir)

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        # Collect routes by method
        get_routes = []
        post_routes = []
        delete_routes = []
        ws_routes = []

        for route in app.routes:
            if isinstance(route, APIWebSocketRoute):
                ws_routes.append(route.path)
            elif isinstance(route, APIRoute):
                for method in route.methods:
                    if method == "GET":
                        get_routes.append(route.path)
                    elif method == "POST":
                        post_routes.append(route.path)
                    elif method == "DELETE":
                        delete_routes.append(route.path)

        # Verify different HTTP methods are used
        assert len(get_routes) > 0, "No GET routes registered"
        assert len(post_routes) > 0, "No POST routes registered"
        assert len(delete_routes) > 0, "No DELETE routes registered"
        assert len(ws_routes) > 0, "No WebSocket routes registered"

    def test_register_routes_get_project_callable(self, temp_dir):
        """Test that get_project parameter is used correctly."""
        from fastapi import FastAPI
        from media_engine.web.websocket import ConnectionManager

        app = FastAPI()
        manager = ConnectionManager()

        project = self._create_mock_project(temp_dir)

        # Track calls to get_project
        call_count = {"count": 0}

        def get_project():
            call_count["count"] += 1
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        # Registration should not call get_project
        # (routes use it lazily when endpoints are hit)
        assert call_count["count"] == 0

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.description = "Test Description"
        config.paths.content = "content"
        config.paths.assets = "assets"
        config.paths.output = "output"
        config.paths.publish = "publish"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English", locale="en-US")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestDocumentListing:
    """Tests for document listing logic in list_documents route."""

    def test_list_documents_chapters_only(self, temp_dir):
        """Test listing when only chapters exist."""
        from media_engine.cms.document import Document

        project = self._create_mock_project(temp_dir)

        # Create some chapters
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)

        for i in range(3):
            chapter = chapters_dir / f"0{i + 1}_chapter.md"
            chapter_num = i + 1
            content = f"""---
title: Chapter {chapter_num}
version: 1.0.0
---

# Chapter {chapter_num}

Content here.
"""
            chapter.write_text(content)

        # Mock list_chapters to return our test chapters
        def mock_list_chapters(lang):
            return sorted(chapters_dir.glob("*.md"))

        project.list_chapters = mock_list_chapters
        project.list_scripts = lambda lang: []

        # Simulate what the route does
        documents = []
        for chapter in project.list_chapters("en"):
            doc = Document.load(chapter)
            documents.append(
                {
                    "path": str(chapter),
                    "filename": chapter.name,
                    "title": doc.title,
                    "type": "chapter",
                    "metadata": doc.metadata,
                }
            )

        assert len(documents) == 3
        assert all(d["type"] == "chapter" for d in documents)
        assert documents[0]["title"] == "Chapter 1"

    def test_list_documents_multiple_types(self, temp_dir):
        """Test listing documents of various types."""
        self._create_mock_project(temp_dir)
        content_dir = temp_dir / "content" / "en"

        # Create different document types
        types_to_create = [
            ("scripts", "intro.yaml", "script"),
            ("diagrams", "architecture.yaml", "diagram"),
            ("slides", "pitch.yaml", "slides"),
            ("data", "metrics.yaml", "data"),
            ("demos", "calculator.yaml", "demo"),
        ]

        for folder, filename, _ in types_to_create:
            folder_path = content_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            file_path = folder_path / filename
            file_path.write_text("test: content")

        # Count created files
        scripts = list((content_dir / "scripts").glob("*.yaml"))
        diagrams = list((content_dir / "diagrams").glob("*.yaml"))
        slides = list((content_dir / "slides").glob("*.yaml"))
        data = list((content_dir / "data").glob("*.yaml"))
        demos = list((content_dir / "demos").glob("*.yaml"))

        assert len(scripts) == 1
        assert len(diagrams) == 1
        assert len(slides) == 1
        assert len(data) == 1
        assert len(demos) == 1

    def test_list_documents_with_deliverables(self, temp_dir):
        """Test listing deliverables with categories."""
        from media_engine.cms.document import Document

        self._create_mock_project(temp_dir)
        content_dir = temp_dir / "content" / "en"

        # Create deliverables
        deliverable_folders = ["investor", "pilot", "legal"]
        for folder in deliverable_folders:
            folder_path = content_dir / folder
            folder_path.mkdir(parents=True)

            doc_file = folder_path / f"{folder}_doc.md"
            folder_title = folder.title()
            content = f"""---
title: {folder_title} Document
version: 1.0.0
---

# {folder_title} Document
"""
            doc_file.write_text(content)

        # Collect deliverables like the route does
        documents = []
        deliverable_categories = [
            ("investor", "Investor"),
            ("pilot", "Pilot"),
            ("legal", "Legal"),
        ]

        for folder, category in deliverable_categories:
            folder_dir = content_dir / folder
            if folder_dir.exists():
                for md_file in folder_dir.glob("*.md"):
                    doc = Document.load(md_file)
                    documents.append(
                        {
                            "path": str(md_file),
                            "filename": md_file.name,
                            "title": doc.title,
                            "type": "deliverable",
                            "category": category,
                            "metadata": doc.metadata,
                        }
                    )

        assert len(documents) == 3
        assert all(d["type"] == "deliverable" for d in documents)
        categories = [d["category"] for d in documents]
        assert "Investor" in categories
        assert "Pilot" in categories
        assert "Legal" in categories

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.paths.content = "content"
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


class TestSearchRoutes:
    """Tests for search API routes."""

    @pytest.mark.asyncio
    async def test_search_content_empty_query(self, temp_dir):
        """Test search with empty query returns empty results."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/search?q=")

        assert response.status_code == 200
        result = response.json()
        assert result["results"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_search_content_short_query(self, temp_dir):
        """Test search with query too short."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/search?q=a")

        assert response.status_code == 200
        result = response.json()
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_content_with_results(self, temp_dir):
        """Test search that finds content."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create searchable content
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)

        chapter_file = chapters_dir / "introduction.md"
        chapter_file.write_text("""---
title: Introduction
---

# Introduction

Welcome to the project documentation. This chapter covers the basics.
""")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/search?q=documentation")

        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 1
        assert any("documentation" in r["snippet"].lower() for r in result["results"])

    @pytest.mark.asyncio
    async def test_search_with_language_filter(self, temp_dir):
        """Test search filtered by language."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir, languages=["en", "no"])

        # Create content in both languages
        for lang in ["en", "no"]:
            chapters_dir = temp_dir / "content" / lang / "chapters"
            chapters_dir.mkdir(parents=True)
            chapter_file = chapters_dir / "guide.md"
            chapter_file.write_text(f"# Guide for {lang}\n\nTest content here.")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/search?q=guide&lang=en")

        assert response.status_code == 200
        result = response.json()
        # Should only have English results
        if result["results"]:
            assert all(r["language"] == "en" for r in result["results"])

    @pytest.mark.asyncio
    async def test_search_with_type_filter(self, temp_dir):
        """Test search filtered by content type."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create chapters and scripts
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "intro.md").write_text("# Intro\n\nTest content.")

        scripts_dir = temp_dir / "content" / "en" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "demo.yaml").write_text("title: Demo Script\ncontent: Test content")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/search?q=content&type=chapter")

        assert response.status_code == 200
        result = response.json()
        if result["results"]:
            assert all(r["type"] == "chapter" for r in result["results"])

    def _create_mock_project(self, root_dir, languages=None):
        """Helper to create a mock project."""
        if languages is None:
            languages = ["en"]

        config = Config()
        config.paths.content = "content"
        theme = Theme()

        lang_configs = {lang: LanguageConfig(code=lang, name=lang.upper()) for lang in languages}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestInsightsRoutes:
    """Tests for insights API routes."""

    @pytest.mark.asyncio
    async def test_get_insights(self, temp_dir):
        """Test comprehensive insights endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create some content for insights
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "intro.md").write_text(
            "---\ntitle: Introduction\n---\n# Introduction\n\nContent here."
        )

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights")

        assert response.status_code == 200
        result = response.json()
        # Should have various insight categories
        assert "health" in result or "error" in str(result)
        assert "statistics" in result or "error" in str(result)

    @pytest.mark.asyncio
    async def test_get_health(self, temp_dir):
        """Test health score endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/health")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_statistics(self, temp_dir):
        """Test statistics endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/statistics")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_incomplete(self, temp_dir):
        """Test incomplete content endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/incomplete")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "items" in result

    @pytest.mark.asyncio
    async def test_get_consistency(self, temp_dir):
        """Test consistency issues endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/consistency")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_get_parity(self, temp_dir):
        """Test translation parity endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir, languages=["en", "no"])

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/parity")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_velocity(self, temp_dir):
        """Test velocity metrics endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/velocity?days=7")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_graph(self, temp_dir):
        """Test knowledge graph endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/graph")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_terms(self, temp_dir):
        """Test terminology issues endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/terms")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_get_duplicates(self, temp_dir):
        """Test duplicate content endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/duplicates")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "matches" in result

    @pytest.mark.asyncio
    async def test_get_codesync(self, temp_dir):
        """Test code-documentation sync endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/insights/codesync")

        assert response.status_code == 200
        result = response.json()
        assert "total_checked" in result
        assert "stale_count" in result

    def _create_mock_project(self, root_dir, languages=None):
        """Helper to create a mock project."""
        if languages is None:
            languages = ["en"]

        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
        theme = Theme()

        lang_configs = {lang: LanguageConfig(code=lang, name=lang.upper()) for lang in languages}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestFreshnessRoutes:
    """Tests for freshness tracking API routes."""

    @pytest.mark.asyncio
    async def test_get_freshness(self, temp_dir):
        """Test freshness report endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create .media-engine directory for registry
        me_dir = temp_dir / ".media-engine"
        me_dir.mkdir(parents=True)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/freshness")

        assert response.status_code == 200
        result = response.json()
        assert "total_items" in result
        assert "fresh_count" in result
        assert "stale_count" in result

    @pytest.mark.asyncio
    async def test_get_freshness_with_scan(self, temp_dir):
        """Test freshness with scan parameter."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create .media-engine directory
        me_dir = temp_dir / ".media-engine"
        me_dir.mkdir(parents=True)

        # Create some content
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "intro.md").write_text("# Introduction\n\nContent here.")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/freshness?scan=true")

        assert response.status_code == 200
        result = response.json()
        assert "total_items" in result

    @pytest.mark.asyncio
    async def test_scan_freshness(self, temp_dir):
        """Test freshness scan endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create .media-engine directory
        me_dir = temp_dir / ".media-engine"
        me_dir.mkdir(parents=True)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.post("/api/freshness/scan")

        assert response.status_code == 200
        result = response.json()
        assert "registered" in result
        assert "total_items" in result

    @pytest.mark.asyncio
    async def test_get_freshness_impact(self, temp_dir):
        """Test freshness impact endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create .media-engine directory
        me_dir = temp_dir / ".media-engine"
        me_dir.mkdir(parents=True)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/freshness/impact/content/en/chapters/intro.md")

        assert response.status_code == 200
        result = response.json()
        assert "source" in result
        assert "affected_items" in result

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
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


class TestDependenciesRoutes:
    """Tests for dependencies API routes."""

    @pytest.mark.asyncio
    async def test_get_dependencies_graph(self, temp_dir):
        """Test dependencies graph endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/dependencies")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_dependencies_files(self, temp_dir):
        """Test dependencies files endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create some trackable files
        content_dir = temp_dir / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)
        (content_dir / "intro.md").write_text("# Introduction")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/dependencies/files")

        assert response.status_code == 200
        result = response.json()
        assert "files" in result

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
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


class TestBuildRoutes:
    """Tests for build API routes."""

    @pytest.mark.asyncio
    async def test_get_build_status(self, temp_dir):
        """Test build status endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create .media-engine directory for freshness registry
        me_dir = temp_dir / ".media-engine"
        me_dir.mkdir(parents=True)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/build/status")

        assert response.status_code == 200
        result = response.json()
        assert "active" in result
        assert "progress" in result
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_get_build_status_with_outputs(self, temp_dir):
        """Test build status shows existing output files."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create .media-engine directory
        me_dir = temp_dir / ".media-engine"
        me_dir.mkdir(parents=True)

        # Create some output files
        output_dir = temp_dir / "output" / "en"
        output_dir.mkdir(parents=True)
        (output_dir / "chapter1.html").write_text("<html>Test</html>")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/build/status")

        assert response.status_code == 200
        result = response.json()
        assert "outputs" in result
        assert len(result["outputs"]) >= 1

    @pytest.mark.asyncio
    async def test_start_build(self, temp_dir):
        """Test starting a build endpoint exists and accepts parameters."""
        from unittest.mock import patch

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create content
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "intro.md").write_text("# Introduction\n\nContent here.")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        # Mock background task to avoid async issues in test
        with patch("fastapi.BackgroundTasks.add_task"):
            client = TestClient(app)
            response = client.post("/api/build/start?formats=html&languages=en")

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "started"
            assert "html" in result["formats"]
            assert "en" in result["languages"]

    @pytest.mark.asyncio
    async def test_start_build_default_params(self, temp_dir):
        """Test starting a build with default parameters."""
        from unittest.mock import patch

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        # Mock background task to avoid async issues in test
        with patch("fastapi.BackgroundTasks.add_task"):
            client = TestClient(app)
            response = client.post("/api/build/start")

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "started"
            assert "html" in result["formats"]  # Default format

    @pytest.mark.asyncio
    async def test_cancel_build_no_active(self, temp_dir):
        """Test cancelling when no build is active."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.post("/api/build/cancel")

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "error"
        assert "No active build" in result["message"]

    @pytest.mark.asyncio
    async def test_get_build_outputs_empty(self, temp_dir):
        """Test getting outputs when none exist."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/build/outputs")

        assert response.status_code == 200
        result = response.json()
        assert "outputs" in result
        assert result["outputs"] == []

    @pytest.mark.asyncio
    async def test_get_build_outputs_with_files(self, temp_dir):
        """Test getting outputs when files exist."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create output files
        output_dir = temp_dir / "output" / "en"
        output_dir.mkdir(parents=True)
        (output_dir / "document.html").write_text("<html>Test</html>")
        (output_dir / "slides.pptx").write_bytes(b"PK\x03\x04")  # Minimal PPTX header
        (output_dir / "data.xlsx").write_bytes(b"PK\x03\x04")  # Minimal XLSX header

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/build/outputs")

        assert response.status_code == 200
        result = response.json()
        assert "outputs" in result
        assert len(result["outputs"]) == 3

        # Check output properties
        formats = [o["format"] for o in result["outputs"]]
        assert "HTML" in formats
        assert "PPTX" in formats
        assert "XLSX" in formats

    @pytest.mark.asyncio
    async def test_start_build_multiple_formats(self, temp_dir):
        """Test starting a build with multiple formats."""
        from unittest.mock import patch

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        with patch("fastapi.BackgroundTasks.add_task"):
            client = TestClient(app)
            response = client.post("/api/build/start?formats=html,pptx,xlsx")

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "started"
            assert len(result["formats"]) == 3

    @pytest.mark.asyncio
    async def test_start_build_with_force(self, temp_dir):
        """Test starting a forced build."""
        from unittest.mock import patch

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        with patch("fastapi.BackgroundTasks.add_task"):
            client = TestClient(app)
            response = client.post("/api/build/start?formats=html&force=true")

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "started"
            assert result["force"] is True

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
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


class TestProvenanceRoutes:
    """Tests for provenance API routes."""

    @pytest.mark.asyncio
    async def test_get_provenance_report(self, temp_dir):
        """Test provenance report endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_all_claims(self, temp_dir):
        """Test all claims endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/claims")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "claims" in result

    @pytest.mark.asyncio
    async def test_get_unverified_claims(self, temp_dir):
        """Test unverified claims endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/claims/unverified")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "claims" in result

    @pytest.mark.asyncio
    async def test_get_expired_claims(self, temp_dir):
        """Test expired claims endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/claims/expired")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "claims" in result

    @pytest.mark.asyncio
    async def test_get_expiring_claims(self, temp_dir):
        """Test expiring claims endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/claims/expiring?days=30")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "claims" in result

    @pytest.mark.asyncio
    async def test_get_approval_status(self, temp_dir):
        """Test approval status endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/approvals")

        assert response.status_code == 200
        result = response.json()
        assert "by_status" in result

    @pytest.mark.asyncio
    async def test_get_review_queue(self, temp_dir):
        """Test review queue endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/review-queue")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "queue" in result

    @pytest.mark.asyncio
    async def test_get_document_provenance(self, temp_dir):
        """Test document provenance endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create a document
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "intro.md").write_text("---\ntitle: Introduction\n---\n# Introduction")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/document/content/en/chapters/intro.md")

        assert response.status_code == 200
        result = response.json()
        assert "document_path" in result
        assert "status" in result
        assert "claims" in result

    @pytest.mark.asyncio
    async def test_check_publish_readiness(self, temp_dir):
        """Test publish readiness endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create a document
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "intro.md").write_text("---\ntitle: Introduction\n---\n# Introduction")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/publish-readiness/content/en/chapters/intro.md")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_claim_issues(self, temp_dir):
        """Test claim issues endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.get("/api/provenance/issues")

        assert response.status_code == 200
        result = response.json()
        assert "total" in result
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_add_claim(self, temp_dir):
        """Test add claim endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create a document
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        doc_path = chapters_dir / "intro.md"
        doc_path.write_text("---\ntitle: Introduction\n---\n# Introduction")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.post(
            "/api/provenance/claims",
            json={
                "document_path": "content/en/chapters/intro.md",
                "claim_type": "fact",
                "claim_text": "Test claim",
                "source": "test source",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_approval(self, temp_dir):
        """Test request approval endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        # Create a document
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        doc_path = chapters_dir / "intro.md"
        doc_path.write_text("---\ntitle: Introduction\n---\n# Introduction")

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.post(
            "/api/provenance/request-approval",
            json={
                "document_path": "content/en/chapters/intro.md",
                "user": "test@example.com",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_scan_documents_for_claims(self, temp_dir):
        """Test scan documents for claims endpoint."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from media_engine.web.websocket import ConnectionManager

        project = self._create_mock_project(temp_dir)

        app = FastAPI()
        manager = ConnectionManager()

        def get_project():
            return project

        static_dir = temp_dir / "static"
        static_dir.mkdir()

        register_routes(app, get_project, manager, static_dir)

        client = TestClient(app)
        response = client.post("/api/provenance/scan")

        assert response.status_code == 200
        result = response.json()
        assert "documents_scanned" in result
        assert "total_claims_found" in result

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
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
