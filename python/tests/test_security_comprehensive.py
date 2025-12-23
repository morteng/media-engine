"""Comprehensive tests for security module."""

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
        "name": "Security Test",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample document
    doc = content_dir / "en" / "chapters" / "01_clean.md"
    doc.write_text("""---
title: Clean Document
status: final
---

# Clean Document

This document has no secrets or PII.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestSensitiveContentScanner:
    """Tests for SensitiveContentScanner."""

    def test_scanner_import(self):
        """Test scanner can be imported."""
        from media_engine.security import SensitiveContentScanner

        assert SensitiveContentScanner is not None

    def test_scanner_creation(self):
        """Test creating scanner."""
        from media_engine.security import SensitiveContentScanner

        scanner = SensitiveContentScanner()
        assert scanner is not None


class TestSensitiveMatch:
    """Tests for SensitiveMatch."""

    def test_match_import(self):
        """Test match can be imported."""
        from media_engine.security import SensitiveMatch

        assert SensitiveMatch is not None


class TestSensitivityLevel:
    """Tests for SensitivityLevel."""

    def test_level_import(self):
        """Test level can be imported."""
        from media_engine.security import SensitivityLevel

        assert SensitivityLevel is not None


class TestScanForSecrets:
    """Tests for scan_for_secrets function."""

    def test_scan_function_import(self):
        """Test scan function can be imported."""
        from media_engine.security import scan_for_secrets

        assert scan_for_secrets is not None


class TestSecurityModuleExports:
    """Tests for security module exports."""

    def test_module_exports(self):
        """Test all expected exports exist."""
        from media_engine import security

        assert hasattr(security, "SensitiveContentScanner")
        assert hasattr(security, "SensitiveMatch")
        assert hasattr(security, "SensitivityLevel")
        assert hasattr(security, "scan_for_secrets")
