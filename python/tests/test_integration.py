"""
Integration tests using the demo project.

These tests verify that all components work together correctly
using the actual demo project content.
"""

import json
import shutil
from pathlib import Path

import pytest
from media_engine.cms.document import Document
from media_engine.cms.translation import TranslationTracker
from media_engine.core.project import Project

# Path to demo project
DEMO_PROJECT_PATH = Path(__file__).parent.parent.parent / "demo"


@pytest.fixture
def demo_project():
    """Load the demo project."""
    if not DEMO_PROJECT_PATH.exists():
        pytest.skip("Demo project not found")
    return Project.load(DEMO_PROJECT_PATH)


@pytest.fixture
def demo_project_copy(temp_dir):
    """Create a copy of demo project for modification tests."""
    if not DEMO_PROJECT_PATH.exists():
        pytest.skip("Demo project not found")

    # Copy demo to temp
    dest = temp_dir / "demo"
    shutil.copytree(DEMO_PROJECT_PATH, dest)
    return Project.load(dest)


class TestDemoProjectLoading:
    """Tests for loading and accessing the demo project."""

    def test_project_loads(self, demo_project):
        """Test that demo project loads correctly."""
        assert demo_project is not None
        assert demo_project.config.name == "Media Engine Demo"

    def test_languages_configured(self, demo_project):
        """Test that languages are configured."""
        assert "en" in demo_project.languages
        assert "no" in demo_project.languages
        assert demo_project.source_language == "en"

    def test_english_chapters_exist(self, demo_project):
        """Test that English chapters exist."""
        chapters = demo_project.list_chapters("en")
        assert len(chapters) >= 3  # At least intro, cms, video
        titles = [Document.load(c).title for c in chapters]
        assert "Introduction to Media Engine" in titles

    def test_norwegian_chapters_exist(self, demo_project):
        """Test that Norwegian translations exist."""
        chapters = demo_project.list_chapters("no")
        assert len(chapters) >= 1
        titles = [Document.load(c).title for c in chapters]
        assert "Introduksjon til Media Engine" in titles


class TestDemoProjectBuilds:
    """Tests for building outputs from demo project."""

    def test_html_build_produces_output(self, demo_project_copy, temp_dir):
        """Test that HTML build produces output."""
        from media_engine.builders.html import HTMLBuilder, HTMLConfig

        builder = HTMLBuilder(theme=demo_project_copy.theme)
        chapters = demo_project_copy.list_chapters("en")

        assert len(chapters) > 0

        # Build from first chapter
        doc = Document.load(chapters[0])
        config = HTMLConfig(include_toc=True, lang="en")
        html = builder.build(doc.content, doc.title, config)

        assert html is not None
        assert len(html) > 0
        assert "<html" in html
        assert doc.title in html

        # Save and verify
        output_path = temp_dir / "test.html"
        builder.save(html, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_pptx_build_from_yaml(self, demo_project_copy, temp_dir):
        """Test PowerPoint build from YAML."""
        from media_engine.builders.pptx import PPTXBuilder

        slides_path = demo_project_copy.get_content_path("en", "slides", "pitch_deck.yaml")

        if not slides_path.exists():
            pytest.skip("Slides YAML not found")

        builder = PPTXBuilder(theme=demo_project_copy.theme)
        builder.build_from_yaml(slides_path)

        output_path = temp_dir / "test.pptx"
        saved_path = builder.save(output_path)

        assert saved_path.exists()
        assert saved_path.stat().st_size > 0

    def test_xlsx_build_from_data(self, demo_project_copy, temp_dir):
        """Test Excel build from YAML data."""
        from media_engine.builders.xlsx import XLSXBuilder

        data_path = demo_project_copy.get_content_path("en", "data", "calculator.yaml")

        if not data_path.exists():
            pytest.skip("Calculator YAML not found")

        builder = XLSXBuilder(theme=demo_project_copy.theme)
        builder.build_from_yaml(data_path)

        output_path = temp_dir / "test.xlsx"
        saved_path = builder.save(output_path)

        assert saved_path.exists()
        assert saved_path.stat().st_size > 0

    def test_diagram_generation(self, demo_project_copy, temp_dir):
        """Test diagram generation from YAML."""
        from media_engine.diagrams import DiagramDefinition, DiagramGenerator

        diagram_path = demo_project_copy.get_content_path("en", "diagrams", "architecture.yaml")

        if not diagram_path.exists():
            pytest.skip("Diagram YAML not found")

        definition = DiagramDefinition.from_yaml(diagram_path)
        generator = DiagramGenerator(theme=demo_project_copy.theme)

        light_path, dark_path = generator.generate_both_themes(definition, temp_dir, "architecture")

        assert light_path.exists()
        assert dark_path.exists()
        assert light_path.stat().st_size > 0
        assert dark_path.stat().st_size > 0

    def test_build_both_languages(self, demo_project_copy, temp_dir):
        """Test building for both languages."""
        from media_engine.builders.html import HTMLBuilder, HTMLConfig

        builder = HTMLBuilder(theme=demo_project_copy.theme)

        for lang in ["en", "no"]:
            chapters = demo_project_copy.list_chapters(lang)
            if not chapters:
                continue

            doc = Document.load(chapters[0])
            config = HTMLConfig(include_toc=True, lang=lang)
            html = builder.build(doc.content, doc.title, config)

            output_path = temp_dir / f"{lang}.html"
            builder.save(html, output_path)

            assert output_path.exists()


class TestDemoProjectQuality:
    """Tests for quality checks on demo project."""

    def test_quality_checks_pass(self, demo_project_copy):
        """Test that demo project passes quality checks."""
        from media_engine.quality import run_quality_checks

        report = run_quality_checks(demo_project_copy, console_output=False)

        # Demo project should have no errors
        assert report.error_count == 0, (
            f"Errors found: {[i.message for i in report.issues if i.severity == 'error']}"
        )

    def test_validation_passes(self, demo_project_copy):
        """Test that demo project passes validation."""
        from media_engine.validation import validate_project

        schema_path = demo_project_copy.root / "schema.yaml"

        report = validate_project(
            demo_project_copy,
            schema_path if schema_path.exists() else None,
            console_output=False,
        )

        # Allow some warnings but no errors
        assert report.error_count == 0, (
            f"Validation errors: {[i.message for i in report.issues if i.severity == 'error']}"
        )


class TestDemoProjectSearch:
    """Tests for search functionality on demo project."""

    def test_search_index_builds(self, demo_project_copy, temp_dir):
        """Test that search index builds correctly."""
        from media_engine.search import build_search_index

        index = build_search_index(demo_project_copy, console_output=False)

        assert index is not None
        assert len(index.entries) > 0

        # Save and reload
        index_path = temp_dir / "search_index.json"
        index.save(index_path)

        assert index_path.exists()

        # Verify JSON is valid
        with open(index_path) as f:
            data = json.load(f)
        assert "entries" in data

    def test_search_returns_results(self, demo_project_copy):
        """Test that search returns relevant results."""
        from media_engine.search import build_search_index

        index = build_search_index(demo_project_copy, console_output=False)

        # Search for something that should exist
        results = index.search("introduction", limit=10)

        assert len(results) > 0
        # First result should be the introduction chapter
        assert (
            "introduction" in results[0].entry.title.lower()
            or "introduksjon" in results[0].entry.title.lower()
        )


class TestDemoProjectTranslation:
    """Tests for translation tracking on demo project."""

    def test_translation_tracker_loads(self, demo_project):
        """Test that translation tracker loads demo project."""
        tracker = TranslationTracker(demo_project)
        pairs = tracker.get_translation_pairs()

        # Should have at least the intro translation
        assert len(pairs) >= 1

    def test_translation_status_available(self, demo_project):
        """Test that translation status is available."""
        tracker = TranslationTracker(demo_project)
        statuses = tracker.get_all_statuses()

        assert len(statuses) >= 1

        # Check structure
        for status in statuses:
            assert status.source_language == "en"
            assert status.target_language == "no"
            assert status.source_version is not None

    def test_sync_status_by_language(self, demo_project):
        """Test sync status grouped by language."""
        tracker = TranslationTracker(demo_project)
        by_lang = tracker.get_sync_status()

        assert "no" in by_lang
        assert len(by_lang["no"]) >= 1


class TestDemoProjectCache:
    """Tests for caching functionality."""

    def test_cache_operations(self, demo_project_copy):
        """Test cache operations work correctly."""
        # Hash a file
        chapters = demo_project_copy.list_chapters("en")
        if not chapters:
            pytest.skip("No chapters found")

        file_hash = demo_project_copy.hash_file(chapters[0])
        assert file_hash is not None
        assert len(file_hash) > 0

        # Record and check build
        output_key = "test/build"
        demo_project_copy.record_build(output_key, chapters[0], [chapters[0]])

        # Should not need rebuild
        assert not demo_project_copy.should_rebuild(output_key, [chapters[0]])

        # After clearing, should need rebuild
        demo_project_copy.clear_cache("builds")
        assert demo_project_copy.should_rebuild(output_key, [chapters[0]])


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_full_build_workflow(self, demo_project_copy, temp_dir):
        """Test a complete build workflow."""
        from media_engine.builders.html import HTMLBuilder, HTMLConfig
        from media_engine.quality import run_quality_checks

        # 1. Quality check
        quality_report = run_quality_checks(demo_project_copy, console_output=False)
        assert quality_report.error_count == 0

        # 2. Build HTML for each language
        builder = HTMLBuilder(theme=demo_project_copy.theme)
        outputs = {}

        for lang in ["en", "no"]:
            chapters = demo_project_copy.list_chapters(lang)
            if not chapters:
                continue

            combined = []
            for chapter_path in chapters:
                doc = Document.load(chapter_path)
                combined.append(doc.content)

            config = HTMLConfig(include_toc=True, lang=lang)
            html = builder.build("\n\n---\n\n".join(combined), f"Documentation ({lang})", config)

            output_path = temp_dir / lang / "documentation.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            builder.save(html, output_path)
            outputs[lang] = output_path

        # 3. Verify outputs
        assert "en" in outputs
        assert outputs["en"].exists()

        # Check content
        en_content = outputs["en"].read_text()
        assert "Media Engine" in en_content
