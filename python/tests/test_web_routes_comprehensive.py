"""Comprehensive tests for web routes."""

import pytest
from fastapi.testclient import TestClient


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
    (tmp_path / "assets").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Web Routes Test",
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
status: draft
version: 1.0.0
---

# Introduction

This is the introduction chapter.
""")

    doc2 = content_dir / "en" / "chapters" / "02_api.md"
    doc2.write_text("""---
title: API Reference
status: final
version: 1.0.0
---

# API Reference

API documentation here.
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

    return tmp_path


@pytest.fixture
def client(sample_project):
    """Create test client."""
    from media_engine.web.app import create_app

    app = create_app(sample_project)
    return TestClient(app)


class TestCoreRoutes:
    """Tests for core API routes."""

    def test_get_status(self, client):
        """Test getting project status."""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestTranslationRoutes:
    """Tests for translation routes."""

    def test_get_translations(self, client):
        """Test getting translations."""
        response = client.get("/api/translations")
        assert response.status_code == 200


class TestFreshnessRoutes:
    """Tests for freshness routes."""

    def test_get_freshness(self, client):
        """Test getting freshness info."""
        response = client.get("/api/freshness")
        assert response.status_code == 200


class TestSearchRoutes:
    """Tests for search routes."""

    def test_search_content(self, client):
        """Test searching content."""
        response = client.get("/api/search?q=introduction")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or isinstance(data, list)

    def test_search_empty_query(self, client):
        """Test searching with empty query."""
        response = client.get("/api/search?q=")
        assert response.status_code == 200


class TestQualityRoutes:
    """Tests for quality routes."""

    def test_get_quality(self, client):
        """Test getting quality info."""
        response = client.get("/api/quality")
        assert response.status_code == 200


class TestMediaRoutes:
    """Tests for media routes."""

    def test_get_media(self, client):
        """Test getting media info."""
        response = client.get("/api/media")
        assert response.status_code == 200


class TestDependencyRoutes:
    """Tests for dependency routes."""

    def test_get_dependencies(self, client):
        """Test getting dependencies."""
        response = client.get("/api/dependencies")
        assert response.status_code == 200


class TestProvenanceRoutes:
    """Tests for provenance routes."""

    def test_get_provenance(self, client):
        """Test getting provenance info."""
        response = client.get("/api/provenance")
        assert response.status_code == 200


class TestSceneNotesRoutes:
    """Tests for scene notes routes."""

    def test_list_notes(self, client):
        """Test listing notes."""
        response = client.get("/api/notes")
        assert response.status_code == 200

    def test_get_pending_notes(self, client):
        """Test getting pending notes."""
        response = client.get("/api/notes/pending")
        assert response.status_code == 200


class TestAssetsRoutes:
    """Tests for assets routes."""

    def test_list_assets(self, client):
        """Test listing assets."""
        response = client.get("/api/assets")
        assert response.status_code == 200


class TestRegistryRoutes:
    """Tests for registry routes."""

    def test_get_registry(self, client):
        """Test getting registry."""
        response = client.get("/api/registry")
        assert response.status_code == 200
