"""Tests for MCP quality and search tools."""

import json

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Quality Test Project",
        "description": "A test project for quality tools",
        "languages": ["en"],
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
status: draft
version: 1.0.0
---

# Introduction

This is the introduction chapter about the system.
It has searchable content for testing purposes.
""")

    doc2 = content_dir / "en" / "chapters" / "02_api.md"
    doc2.write_text("""---
title: API Reference
status: final
version: 1.0.0
---

# API Reference

This chapter documents the API endpoints.
Users can search for specific methods.
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


class TestQualityTools:
    """Tests for quality.py tools."""

    @pytest.mark.asyncio
    async def test_quality_check(self, mock_server):
        """Test running quality checks."""
        from media_engine.mcp.tools import quality

        mock = MockMCP()
        quality.register_quality_tools(mock, mock_server)

        result = await mock.tools["quality_check"]()
        data = json.loads(result)

        assert "summary" in data
        assert "total" in data["summary"]
        assert "errors" in data["summary"]
        assert "warnings" in data["summary"]
        assert "passed" in data["summary"]
        assert "issues" in data

    @pytest.mark.asyncio
    async def test_validate_project(self, mock_server):
        """Test project validation."""
        from media_engine.mcp.tools import quality

        mock = MockMCP()
        quality.register_quality_tools(mock, mock_server)

        result = await mock.tools["validate_project"]()
        data = json.loads(result)

        assert "valid" in data
        assert "summary" in data
        assert "issues" in data


class TestSearchTools:
    """Tests for search.py tools."""

    @pytest.mark.asyncio
    async def test_search_content(self, mock_server):
        """Test content search."""
        from media_engine.mcp.tools import search

        mock = MockMCP()
        search.register_search_tools(mock, mock_server)

        result = await mock.tools["search_content"](query="introduction", limit=5)
        data = json.loads(result)

        assert data["query"] == "introduction"
        assert "count" in data
        assert "results" in data

    @pytest.mark.asyncio
    async def test_search_content_with_language(self, mock_server):
        """Test content search with language filter."""
        from media_engine.mcp.tools import search

        mock = MockMCP()
        search.register_search_tools(mock, mock_server)

        result = await mock.tools["search_content"](query="API", language="en", limit=10)
        data = json.loads(result)

        assert data["query"] == "API"
        # All results should be English
        for r in data["results"]:
            assert r["language"] == "en"

    @pytest.mark.asyncio
    async def test_search_content_no_results(self, mock_server):
        """Test search with no matching results."""
        from media_engine.mcp.tools import search

        mock = MockMCP()
        search.register_search_tools(mock, mock_server)

        result = await mock.tools["search_content"](query="xyznonexistent12345", limit=5)
        data = json.loads(result)

        assert data["count"] == 0
        assert data["results"] == []

    @pytest.mark.asyncio
    async def test_search_uses_cache(self, mock_server):
        """Test that search uses caching."""
        from media_engine.mcp.tools import search

        mock = MockMCP()
        search.register_search_tools(mock, mock_server)

        # First search
        await mock.tools["search_content"](query="test", limit=5)

        # Check cache was populated
        assert "search_index_all" in mock_server._cache

        # Second search should use cache
        result = await mock.tools["search_content"](query="another", limit=5)
        data = json.loads(result)

        assert "results" in data
