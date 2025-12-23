"""Tests for MCP build and translation tools."""

import json

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "no" / "chapters").mkdir(parents=True)
    (tmp_path / "dist").mkdir()
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Build Test Project",
        "description": "A test project",
        "languages": ["en", "no"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample documents
    doc1 = content_dir / "en" / "chapters" / "01_intro.md"
    doc1.write_text("""---
title: Introduction
status: final
version: 1.0.0
---

# Introduction

This is the introduction chapter.
""")

    # Create Norwegian translation
    trans = content_dir / "no" / "chapters" / "01_intro.md"
    trans.write_text("""---
title: Introduksjon
status: draft
version: 1.0.0
language: "no"
source_document: en/chapters/01_intro.md
source_version: 1.0.0
---

# Introduksjon

Dette er introduksjonskapittelet.
""")

    # Create outdated translation
    doc2 = content_dir / "en" / "chapters" / "02_features.md"
    doc2.write_text("""---
title: Features
status: final
version: 2.0.0
---

# Features

Updated features content.
""")

    trans2 = content_dir / "no" / "chapters" / "02_features.md"
    trans2.write_text("""---
title: Funksjoner
status: final
version: 1.0.0
language: "no"
source_document: en/chapters/02_features.md
source_version: 1.0.0
---

# Funksjoner

Outdated translation.
""")

    return tmp_path


@pytest.fixture
def mock_server(sample_project):
    """Create a mock MCP server for testing."""
    from media_engine.mcp.server import MediaEngineMCPServer

    server = MediaEngineMCPServer(project_path=sample_project)
    return server


class MockMCP:
    """Mock MCP for tool registration."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


class TestBuildTools:
    """Tests for build.py tools."""

    @pytest.mark.asyncio
    async def test_build_html(self, mock_server):
        """Test building HTML output."""
        from media_engine.mcp.tools import build

        mock = MockMCP()
        build.register_build_tools(mock, mock_server)

        result = await mock.tools["build_html"]()
        data = json.loads(result)

        # Should have some result structure
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_build_html_with_language(self, mock_server):
        """Test building HTML for specific language."""
        from media_engine.mcp.tools import build

        mock = MockMCP()
        build.register_build_tools(mock, mock_server)

        result = await mock.tools["build_html"](language="en")
        data = json.loads(result)

        assert isinstance(data, dict)


class TestTranslationTools:
    """Tests for translation.py tools."""

    @pytest.mark.asyncio
    async def test_translation_status(self, mock_server):
        """Test getting translation status."""
        from media_engine.mcp.tools import translation

        mock = MockMCP()
        translation.register_translation_tools(mock, mock_server)

        result = await mock.tools["translation_status"]()
        data = json.loads(result)

        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_outdated_translations(self, mock_server):
        """Test finding outdated translations."""
        from media_engine.mcp.tools import translation

        mock = MockMCP()
        translation.register_translation_tools(mock, mock_server)

        result = await mock.tools["outdated_translations"]()
        data = json.loads(result)

        assert isinstance(data, dict)


class TestCacheTools:
    """Tests for cache.py tools."""

    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_server):
        """Test clearing cache."""
        from media_engine.mcp.tools import cache

        mock = MockMCP()
        cache.register_cache_tools(mock, mock_server)

        # First populate cache
        mock_server._cache["test"] = ("value", 0)

        result = await mock.tools["clear_cache"]()
        data = json.loads(result)

        assert data["status"] == "cleared"
        assert len(mock_server._cache) == 0


class TestAuditTools:
    """Tests for audit.py tools."""

    @pytest.mark.asyncio
    async def test_log_action(self, mock_server):
        """Test logging an action."""
        from media_engine.mcp.tools import audit

        mock = MockMCP()
        audit.register_audit_tools(mock, mock_server)

        result = await mock.tools["log_action"](action="test_action", details="Test action details")
        data = json.loads(result)

        assert data["status"] == "logged"
        assert data["action"] == "test_action"
