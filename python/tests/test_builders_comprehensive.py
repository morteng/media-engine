"""Comprehensive tests for builders."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "en" / "slides").mkdir(parents=True)
    (tmp_path / "dist").mkdir()
    (tmp_path / ".media-engine").mkdir()
    (tmp_path / "assets").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Builder Test",
        "description": "Test project for builders",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create theme.yaml
    theme_config = {
        "colors": {
            "primary": "#3B82F6",
            "secondary": "#10B981",
            "background": "#FFFFFF",
            "text": "#1F2937",
        },
        "fonts": {
            "heading": "Inter",
            "body": "Inter",
        },
    }
    (tmp_path / "theme.yaml").write_text(yaml.dump(theme_config))

    # Create sample document
    doc = content_dir / "en" / "chapters" / "01_intro.md"
    doc.write_text("""---
title: Introduction
status: final
version: 1.0.0
---

# Introduction

This is the introduction chapter.

## Overview

Some overview content here.

- Point one
- Point two
- Point three

## Features

Key features include:

1. First feature
2. Second feature
3. Third feature
""")

    # Create slide document
    slides = content_dir / "en" / "slides" / "presentation.md"
    slides.write_text("""---
title: Test Presentation
type: presentation
status: final
---

# Slide 1

First slide content

---

# Slide 2

Second slide content

- Bullet point
- Another bullet
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestHTMLBuilder:
    """Tests for HTML builder."""

    def test_html_builder_import(self):
        """Test HTMLBuilder can be imported."""
        from media_engine.builders import HTMLBuilder

        assert HTMLBuilder is not None

    def test_html_builder_creation(self):
        """Test creating HTML builder."""
        from media_engine.builders import HTMLBuilder

        builder = HTMLBuilder()
        assert builder is not None

    def test_html_builder_with_theme(self, project):
        """Test HTML builder with theme."""
        from media_engine.builders import HTMLBuilder

        builder = HTMLBuilder(theme=project.theme)
        assert builder is not None


class TestPPTXBuilder:
    """Tests for PPTX builder."""

    def test_pptx_builder_import(self):
        """Test PPTXBuilder can be imported."""
        from media_engine.builders import PPTXBuilder

        assert PPTXBuilder is not None

    def test_pptx_builder_creation(self):
        """Test creating PPTX builder."""
        from media_engine.builders import PPTXBuilder

        builder = PPTXBuilder()
        assert builder is not None

    def test_pptx_builder_with_theme(self, project):
        """Test PPTX builder with theme."""
        from media_engine.builders import PPTXBuilder

        builder = PPTXBuilder(theme=project.theme)
        assert builder is not None


class TestXLSXBuilder:
    """Tests for XLSX builder."""

    def test_xlsx_builder_import(self):
        """Test XLSXBuilder can be imported."""
        from media_engine.builders import XLSXBuilder

        assert XLSXBuilder is not None

    def test_xlsx_builder_creation(self):
        """Test creating XLSX builder."""
        from media_engine.builders import XLSXBuilder

        builder = XLSXBuilder()
        assert builder is not None

    def test_xlsx_builder_with_theme(self, project):
        """Test XLSX builder with theme."""
        from media_engine.builders import XLSXBuilder

        builder = XLSXBuilder(theme=project.theme)
        assert builder is not None


class TestBuildersExports:
    """Test builders module exports."""

    def test_builders_module_exports(self):
        """Test builders module has expected exports."""
        from media_engine import builders

        assert hasattr(builders, "HTMLBuilder")
        assert hasattr(builders, "PPTXBuilder")
        assert hasattr(builders, "XLSXBuilder")


class TestBrandContext:
    """Tests for brand context integration."""

    def test_brand_context_import(self):
        """Test BrandContext can be imported."""
        from media_engine.brand import BrandContext

        assert BrandContext is not None

    def test_brand_profile_import(self):
        """Test BrandProfile can be imported."""
        from media_engine.brand import BrandProfile

        assert BrandProfile is not None


class TestTemplates:
    """Tests for template components."""

    def test_html_document_template_import(self):
        """Test HTML document template can be imported."""
        from media_engine.templates.html_document import render_document

        assert render_document is not None

    def test_html_index_template_import(self):
        """Test HTML index template can be imported."""
        from media_engine.templates.html_index import render_project_index

        assert render_project_index is not None

    def test_html_presentation_template_import(self):
        """Test HTML presentation template can be imported."""
        from media_engine.templates.html_presentation import render_presentation

        assert render_presentation is not None
