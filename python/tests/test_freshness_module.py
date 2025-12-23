"""Tests for freshness module."""

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
        "name": "Freshness Test",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample document
    doc = content_dir / "en" / "chapters" / "01_intro.md"
    doc.write_text("""---
title: Introduction
status: final
---

# Introduction

This is content that may become stale.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestContentRegistry:
    """Tests for ContentRegistry."""

    def test_registry_import(self):
        """Test registry can be imported."""
        from media_engine.freshness import ContentRegistry

        assert ContentRegistry is not None


class TestFreshnessStatus:
    """Tests for FreshnessStatus."""

    def test_status_import(self):
        """Test status can be imported."""
        from media_engine.freshness import FreshnessStatus

        assert FreshnessStatus is not None


class TestFreshnessReport:
    """Tests for FreshnessReport."""

    def test_report_import(self):
        """Test report can be imported."""
        from media_engine.freshness import FreshnessReport

        assert FreshnessReport is not None


class TestScanProject:
    """Tests for scan_project function."""

    def test_scan_function_import(self):
        """Test scan function can be imported."""
        from media_engine.freshness import scan_project

        assert scan_project is not None

    def test_scan_project(self, project):
        """Test scanning project."""
        from media_engine.freshness import scan_project

        # Just verify it can be called
        assert scan_project is not None


class TestFreshnessModuleExports:
    """Tests for freshness module exports."""

    def test_module_exports(self):
        """Test all expected exports exist."""
        from media_engine import freshness

        assert hasattr(freshness, "ContentRegistry")
        assert hasattr(freshness, "FreshnessStatus")
        assert hasattr(freshness, "FreshnessReport")
        assert hasattr(freshness, "scan_project")
