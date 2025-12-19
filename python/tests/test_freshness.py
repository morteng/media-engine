"""
Tests for media_engine.freshness module.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from media_engine.core.project import Project
from media_engine.freshness import (
    ContentRegistry,
    ContentType,
    FreshnessReport,
    FreshnessStatus,
    TrackedItem,
    scan_project,
)


@pytest.fixture
def freshness_project(temp_dir):
    """Create a test project for freshness tracking."""
    # Create project structure
    (temp_dir / "content/en/chapters").mkdir(parents=True)
    (temp_dir / "content/en/scripts").mkdir(parents=True)
    (temp_dir / "content/en/data").mkdir(parents=True)
    (temp_dir / "output/en").mkdir(parents=True)
    (temp_dir / ".media-engine").mkdir(parents=True)

    # Create project.yaml
    project_yaml = temp_dir / "project.yaml"
    project_yaml.write_text("""
project:
  name: "Freshness Test"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"

paths:
  content: "content"
  assets: "assets"
  output: "output"
""")

    # Create theme.yaml
    theme_yaml = temp_dir / "theme.yaml"
    theme_yaml.write_text("""
name: "Test Theme"
colors:
  primary: "#000000"
""")

    # Create sample chapter
    chapter = temp_dir / "content/en/chapters/01_intro.md"
    chapter.write_text("""---
title: "Introduction"
version: "1.0.0"
---

# Introduction

This is a test chapter.
""")

    # Create sample script
    script = temp_dir / "content/en/scripts/test_script.yaml"
    script.write_text("""
title: "Test Script"
scenes:
  - id: intro
    title: "Introduction"
""")

    # Create sample data file
    data_file = temp_dir / "content/en/data/stats.yaml"
    data_file.write_text("""
category: "Statistics"
values:
  - 100
  - 200
""")

    return Project.load(temp_dir)


@pytest.fixture
def registry(freshness_project):
    """Create a ContentRegistry for testing."""
    return ContentRegistry(freshness_project)


class TestContentType:
    """Tests for ContentType enum."""

    def test_content_types_exist(self):
        """Test all content types are defined."""
        assert ContentType.SOURCE_DOCUMENT
        assert ContentType.TRANSLATED_DOCUMENT
        assert ContentType.VIDEO_SCRIPT
        assert ContentType.VIDEO_RENDER
        assert ContentType.VOICEOVER_AUDIO
        assert ContentType.DEMO_HTML
        assert ContentType.DEMO_ASSET
        assert ContentType.DEMO_CAPTURE
        assert ContentType.DIAGRAM_SOURCE
        assert ContentType.DIAGRAM_RENDER
        assert ContentType.DELIVERABLE
        assert ContentType.THEME
        assert ContentType.CONFIG

    def test_content_type_values(self):
        """Test content type string values."""
        assert ContentType.SOURCE_DOCUMENT.value == "source_document"
        assert ContentType.VIDEO_RENDER.value == "video_render"
        assert ContentType.THEME.value == "theme"


class TestFreshnessStatus:
    """Tests for FreshnessStatus enum."""

    def test_freshness_statuses_exist(self):
        """Test all freshness statuses are defined."""
        assert FreshnessStatus.FRESH
        assert FreshnessStatus.STALE
        assert FreshnessStatus.EXPIRED
        assert FreshnessStatus.UNTRACKED
        assert FreshnessStatus.MISSING
        assert FreshnessStatus.CLAIMS_ISSUE

    def test_freshness_status_values(self):
        """Test freshness status string values."""
        assert FreshnessStatus.FRESH.value == "fresh"
        assert FreshnessStatus.STALE.value == "stale"
        assert FreshnessStatus.EXPIRED.value == "expired"


class TestTrackedItem:
    """Tests for TrackedItem class."""

    def test_create_tracked_item(self):
        """Test creating a TrackedItem."""
        item = TrackedItem(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        assert item.path == Path("content/en/chapters/01_intro.md")
        assert item.content_type == ContentType.SOURCE_DOCUMENT
        assert item.depends_on == []
        assert item.freshness_status == FreshnessStatus.FRESH

    def test_tracked_item_with_dependencies(self):
        """Test TrackedItem with dependencies."""
        item = TrackedItem(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[
                Path("content/en/chapters/01_intro.md"),
                Path("theme.yaml"),
            ],
        )
        assert len(item.depends_on) == 2
        assert Path("content/en/chapters/01_intro.md") in item.depends_on

    def test_tracked_item_to_dict(self):
        """Test serializing TrackedItem to dict."""
        item = TrackedItem(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
            last_modified=datetime(2025, 1, 15, 10, 30),
            freshness_days=30,
            metadata={"author": "test"},
        )
        data = item.to_dict()
        assert data["path"] == "content/en/chapters/01_intro.md"
        assert data["type"] == "source_document"
        assert data["freshness_days"] == 30
        assert data["metadata"]["author"] == "test"
        assert "2025-01-15" in data["last_modified"]

    def test_tracked_item_from_dict(self):
        """Test deserializing TrackedItem from dict."""
        data = {
            "path": "content/en/chapters/01_intro.md",
            "type": "source_document",
            "depends_on": ["theme.yaml"],
            "last_modified": "2025-01-15T10:30:00",
            "last_checked": "2025-01-15T11:00:00",
            "content_hash": "abc123",
            "freshness_status": "fresh",
            "freshness_days": 30,
            "metadata": {"author": "test"},
        }
        item = TrackedItem.from_dict(data)
        assert item.path == Path("content/en/chapters/01_intro.md")
        assert item.content_type == ContentType.SOURCE_DOCUMENT
        assert len(item.depends_on) == 1
        assert item.freshness_days == 30
        assert item.metadata["author"] == "test"


class TestFreshnessReport:
    """Tests for FreshnessReport class."""

    def test_create_freshness_report(self):
        """Test creating a FreshnessReport."""
        report = FreshnessReport(
            project_name="Test Project",
            scan_time=datetime.now(),
            total_items=10,
            fresh_count=8,
            stale_count=2,
        )
        assert report.project_name == "Test Project"
        assert report.total_items == 10
        assert report.fresh_count == 8
        assert report.stale_count == 2

    def test_freshness_report_to_dict(self):
        """Test serializing FreshnessReport to dict."""
        now = datetime.now()
        report = FreshnessReport(
            project_name="Test Project",
            scan_time=now,
            total_items=10,
            fresh_count=7,
            stale_count=2,
            expired_count=1,
        )
        data = report.to_dict()
        assert data["project_name"] == "Test Project"
        assert data["summary"]["total"] == 10
        assert data["summary"]["fresh"] == 7
        assert data["summary"]["stale"] == 2


class TestContentRegistry:
    """Tests for ContentRegistry class."""

    def test_create_registry(self, registry):
        """Test creating a ContentRegistry."""
        assert registry.items == {}
        assert not registry._loaded

    def test_load_empty_registry(self, registry):
        """Test loading registry when file doesn't exist."""
        registry.load()
        assert registry.items == {}

    def test_register_item(self, registry, freshness_project):
        """Test registering a content item."""
        path = Path("content/en/chapters/01_intro.md")
        item = registry.register(
            path=path,
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        assert item.path == path
        assert item.content_type == ContentType.SOURCE_DOCUMENT
        assert str(path) in registry.items

    def test_register_item_with_absolute_path(self, registry, freshness_project):
        """Test registering with absolute path (should convert to relative)."""
        abs_path = freshness_project.root / "content/en/chapters/01_intro.md"
        item = registry.register(
            path=abs_path,
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        # Should be stored as relative path
        assert not item.path.is_absolute()
        assert str(item.path) == "content/en/chapters/01_intro.md"

    def test_register_item_with_dependencies(self, registry, freshness_project):
        """Test registering item with dependencies."""
        item = registry.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[
                Path("content/en/chapters/01_intro.md"),
                Path("theme.yaml"),
            ],
        )
        assert len(item.depends_on) == 2

    def test_register_item_with_freshness_days(self, registry, freshness_project):
        """Test registering item with freshness_days limit."""
        item = registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
            freshness_days=30,
        )
        assert item.freshness_days == 30

    def test_register_item_computes_hash(self, registry, freshness_project):
        """Test that registration computes content hash."""
        path = Path("content/en/chapters/01_intro.md")
        item = registry.register(
            path=path,
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        assert item.content_hash != ""
        assert len(item.content_hash) == 16  # SHA256[:16]

    def test_unregister_item(self, registry):
        """Test unregistering an item."""
        path = Path("content/en/chapters/01_intro.md")
        registry.register(path=path, content_type=ContentType.SOURCE_DOCUMENT)
        assert str(path) in registry.items

        result = registry.unregister(path)
        assert result is True
        assert str(path) not in registry.items

    def test_unregister_nonexistent_item(self, registry):
        """Test unregistering item that doesn't exist."""
        result = registry.unregister(Path("nonexistent.md"))
        assert result is False

    def test_get_item(self, registry):
        """Test getting an item by path."""
        path = Path("content/en/chapters/01_intro.md")
        registry.register(path=path, content_type=ContentType.SOURCE_DOCUMENT)

        item = registry.get(path)
        assert item is not None
        assert item.path == path

    def test_get_nonexistent_item(self, registry):
        """Test getting item that doesn't exist."""
        item = registry.get(Path("nonexistent.md"))
        assert item is None

    def test_get_by_type(self, registry, freshness_project):
        """Test getting items by content type."""
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )
        registry.register(
            path=Path("content/en/scripts/test_script.yaml"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )

        docs = registry.get_by_type(ContentType.SOURCE_DOCUMENT)
        assert len(docs) == 2

        themes = registry.get_by_type(ContentType.THEME)
        assert len(themes) == 1

    def test_save_and_load_registry(self, registry, freshness_project):
        """Test saving and loading registry from disk."""
        # Register some items
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )

        # Save
        registry.save()
        assert registry._registry_path.exists()

        # Load into new registry
        new_registry = ContentRegistry(freshness_project)
        new_registry.load()
        assert len(new_registry.items) == 2
        assert "content/en/chapters/01_intro.md" in new_registry.items

    def test_save_creates_directory(self, registry, freshness_project):
        """Test that save creates .media-engine directory if needed."""
        # Remove the directory
        import shutil

        if registry._registry_path.parent.exists():
            shutil.rmtree(registry._registry_path.parent)

        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )
        registry.save()

        assert registry._registry_path.parent.exists()
        assert registry._registry_path.exists()

    def test_all_paths(self, registry):
        """Test getting all tracked paths."""
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )

        paths = registry.all_paths()
        assert len(paths) == 2
        assert "content/en/chapters/01_intro.md" in paths
        assert "theme.yaml" in paths

    def test_get_dependents(self, registry):
        """Test finding items that depend on a given path."""
        # Register theme
        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )

        # Register items that depend on theme
        registry.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("theme.yaml")],
        )
        registry.register(
            path=Path("output/en/chapter2.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("theme.yaml")],
        )

        dependents = registry.get_dependents(Path("theme.yaml"))
        assert len(dependents) == 2

    def test_get_impact_transitive(self, registry):
        """Test transitive impact analysis."""
        # Chain: source.md -> html -> pdf
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("content/en/chapters/01_intro.md")],
        )
        registry.register(
            path=Path("output/en/intro.pdf"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("output/en/intro.html")],
        )

        # Changing source should affect both html and pdf
        affected = registry.get_impact(Path("content/en/chapters/01_intro.md"))
        assert len(affected) == 2
        paths = [str(item.path) for item in affected]
        assert "output/en/intro.html" in paths
        assert "output/en/intro.pdf" in paths

    def test_freshness_status_fresh(self, registry, freshness_project):
        """Test item is marked as FRESH when no issues."""
        item = registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        assert item.freshness_status == FreshnessStatus.FRESH

    def test_freshness_status_missing(self, registry, freshness_project):
        """Test item is marked as MISSING when file doesn't exist."""
        item = registry.register(
            path=Path("nonexistent.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        assert item.freshness_status == FreshnessStatus.MISSING

    def test_freshness_status_stale(self, registry, freshness_project, temp_dir):
        """Test item is marked as STALE when dependency is newer."""
        # Create a source file
        source_path = freshness_project.root / "content/en/chapters/01_intro.md"

        # Wait a bit to ensure different timestamps
        time.sleep(0.1)

        # Create output file that depends on source
        output_path = freshness_project.root / "output/en/intro.html"
        output_path.write_text("<html><body>Test</body></html>")

        # Register output with dependency
        registry.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("content/en/chapters/01_intro.md")],
        )

        # Wait a bit
        time.sleep(0.1)

        # Touch the source file to make it newer
        source_path.write_text(source_path.read_text() + "\n\n<!-- Updated -->")

        # Refresh to recompute freshness
        report = registry.refresh(check_provenance=False)

        # Output should now be stale
        output_item = registry.get(Path("output/en/intro.html"))
        assert output_item.freshness_status == FreshnessStatus.STALE
        assert report.stale_count == 1

    def test_freshness_status_expired(self, registry, freshness_project):
        """Test item is marked as EXPIRED when older than freshness_days."""
        # Create an old file
        old_file = freshness_project.root / "old_content.md"
        old_file.write_text("# Old Content\n")

        # Register item with freshness_days=1
        item = registry.register(
            path=Path("old_content.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
            freshness_days=1,
        )

        # Manually set the file's mtime to 3 days ago
        old_time = (datetime.now() - timedelta(days=3)).timestamp()
        import os
        os.utime(old_file, (old_time, old_time))

        # Refresh to recompute
        report = registry.refresh(check_provenance=False)

        item = registry.get(Path("old_content.md"))
        assert item.freshness_status == FreshnessStatus.EXPIRED

    def test_get_stale(self, registry, freshness_project):
        """Test getting all stale items."""
        # Create items with different statuses
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )

        # Create a stale item by manipulating the registry
        stale_item = registry.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
        )
        stale_item.freshness_status = FreshnessStatus.STALE
        registry.items[str(stale_item.path)] = stale_item

        stale_items = registry.get_stale()
        assert len(stale_items) == 1
        assert stale_items[0].path == Path("output/en/intro.html")

    def test_get_expired(self, registry):
        """Test getting all expired items."""
        item = registry.register(
            path=Path("old_doc.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        item.freshness_status = FreshnessStatus.EXPIRED
        registry.items[str(item.path)] = item

        expired_items = registry.get_expired()
        assert len(expired_items) == 1

    def test_get_missing(self, registry):
        """Test getting all missing items."""
        item = registry.register(
            path=Path("nonexistent.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        # Item should automatically be marked as missing
        assert item.freshness_status == FreshnessStatus.MISSING

        missing_items = registry.get_missing()
        assert len(missing_items) == 1

    def test_find_untracked(self, registry, freshness_project):
        """Test finding untracked files."""
        # Register one file
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )

        # Find untracked (should find script and data files)
        untracked, ignored = registry.find_untracked()
        untracked_names = [p.name for p in untracked]

        # These files exist but aren't registered
        assert "test_script.yaml" in untracked_names or "stats.yaml" in untracked_names

    def test_find_untracked_with_ignore(self, registry, freshness_project):
        """Test finding untracked files with ignore patterns."""
        # Create .mediaignore file
        mediaignore = freshness_project.root / ".mediaignore"
        mediaignore.write_text("*.yaml\n")

        # Clear cache to pick up new ignore file
        registry.clear_ignore_cache()

        untracked, ignored = registry.find_untracked(include_ignored=True)

        # YAML files should be in ignored list
        ignored_names = [p.name for p in ignored]
        assert any("yaml" in name for name in ignored_names)

    def test_ignore_patterns_default(self, registry):
        """Test default ignore patterns."""
        patterns = registry.get_ignore_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_ignore_patterns_from_mediaignore(self, registry, freshness_project):
        """Test loading patterns from .mediaignore file."""
        mediaignore = freshness_project.root / ".mediaignore"
        mediaignore.write_text("*.tmp\ntest_*.md\n# Comment\n\n")

        registry.clear_ignore_cache()
        patterns = registry.get_ignore_patterns()

        assert "*.tmp" in patterns
        assert "test_*.md" in patterns
        assert "# Comment" not in patterns  # Comments should be filtered

    def test_should_ignore_simple_pattern(self, registry, freshness_project):
        """Test simple ignore pattern matching."""
        mediaignore = freshness_project.root / ".mediaignore"
        mediaignore.write_text("*.tmp\n")
        registry.clear_ignore_cache()

        assert registry._should_ignore(Path("test.tmp"))
        assert not registry._should_ignore(Path("test.md"))

    def test_should_ignore_glob_pattern(self, registry, freshness_project):
        """Test glob pattern with ** matching."""
        mediaignore = freshness_project.root / ".mediaignore"
        mediaignore.write_text("**/node_modules/**\n")
        registry.clear_ignore_cache()

        assert registry._should_ignore(Path("node_modules/package.json"))
        assert registry._should_ignore(Path("src/node_modules/lib.js"))

    def test_refresh_basic(self, registry, freshness_project):
        """Test basic refresh operation."""
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )

        report = registry.refresh(check_provenance=False)

        assert report.project_name == "Freshness Test"
        assert report.total_items == 2
        assert report.fresh_count >= 1  # At least one should be fresh

    def test_refresh_updates_timestamps(self, registry, freshness_project):
        """Test that refresh updates last_checked timestamps."""
        item = registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )

        old_checked = item.last_checked

        # Wait a tiny bit
        time.sleep(0.01)

        registry.refresh(check_provenance=False)

        item = registry.get(Path("content/en/chapters/01_intro.md"))
        assert item.last_checked > old_checked

    def test_refresh_detects_untracked(self, registry, freshness_project):
        """Test that refresh detects untracked files."""
        # Don't register anything
        report = registry.refresh(check_provenance=False)

        # Should find some untracked files
        assert report.untracked_count > 0
        assert len(report.untracked_files) > 0

    def test_clear_ignore_cache(self, registry):
        """Test clearing ignore pattern cache."""
        # Load patterns to populate cache
        registry.get_ignore_patterns()
        assert registry._ignore_patterns is not None

        registry.clear_ignore_cache()
        assert registry._ignore_patterns is None

    def test_clear_provenance_cache(self, registry):
        """Test clearing provenance cache."""
        registry._provenance_cache = {"test": (1, 2, 3)}
        registry.clear_provenance_cache()
        assert registry._provenance_cache is None


class TestScanProject:
    """Tests for scan_project function."""

    def test_scan_empty_project(self, freshness_project):
        """Test scanning project with minimal content."""
        registry = ContentRegistry(freshness_project)
        count = scan_project(freshness_project, registry)

        # Should find at least the chapter, script, and config files
        assert count >= 3

    def test_scan_registers_chapters(self, freshness_project):
        """Test that scanning registers chapter files."""
        registry = ContentRegistry(freshness_project)
        scan_project(freshness_project, registry)

        # Should have registered the chapter
        docs = registry.get_by_type(ContentType.SOURCE_DOCUMENT)
        paths = [str(item.path) for item in docs]
        assert any("01_intro.md" in p for p in paths)

    def test_scan_registers_theme(self, freshness_project):
        """Test that scanning registers theme file."""
        registry = ContentRegistry(freshness_project)
        scan_project(freshness_project, registry)

        themes = registry.get_by_type(ContentType.THEME)
        assert len(themes) == 1
        assert themes[0].path == Path("theme.yaml")

    def test_scan_registers_config(self, freshness_project):
        """Test that scanning registers project config."""
        registry = ContentRegistry(freshness_project)
        scan_project(freshness_project, registry)

        configs = registry.get_by_type(ContentType.CONFIG)
        assert len(configs) == 1
        assert configs[0].path == Path("project.yaml")

    def test_scan_with_video_content(self, freshness_project):
        """Test scanning project with video scripts."""
        # Create video script directory
        video_dir = freshness_project.root / "docs/deliverables/video/scripts/en"
        video_dir.mkdir(parents=True, exist_ok=True)

        # Create a video script
        script = video_dir / "teaser.yaml"
        script.write_text("""
title: "Teaser Video"
output:
  filename: "teaser-en.mp4"
scenes:
  - id: intro
    title: "Introduction"
""")

        registry = ContentRegistry(freshness_project)
        scan_project(freshness_project, registry)

        # Should have registered the video script
        scripts = registry.get_by_type(ContentType.VIDEO_SCRIPT)
        assert len(scripts) >= 1

    def test_scan_with_demo_content(self, freshness_project):
        """Test scanning project with demo files."""
        # Create demo directory
        demo_dir = freshness_project.root / "docs/deliverables/demo/en"
        demo_dir.mkdir(parents=True, exist_ok=True)

        # Create a demo HTML file
        demo = demo_dir / "calculator.html"
        demo.write_text("<html><body>Demo</body></html>")

        # Create shared assets
        shared_dir = freshness_project.root / "docs/deliverables/demo/shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        (shared_dir / "style.css").write_text("body { margin: 0; }")

        registry = ContentRegistry(freshness_project)
        scan_project(freshness_project, registry)

        # Should have registered demo HTML
        demos = registry.get_by_type(ContentType.DEMO_HTML)
        assert len(demos) >= 1

        # Should have registered demo assets
        assets = registry.get_by_type(ContentType.DEMO_ASSET)
        assert len(assets) >= 1

    def test_scan_with_deliverables(self, freshness_project):
        """Test scanning project with output deliverables."""
        # Create HTML output
        html_out = freshness_project.root / "output/en/intro.html"
        html_out.write_text("<html><body>Output</body></html>")

        registry = ContentRegistry(freshness_project)
        scan_project(freshness_project, registry)

        # Should have registered the deliverable
        deliverables = registry.get_by_type(ContentType.DELIVERABLE)
        assert len(deliverables) >= 1

    def test_scan_returns_count(self, freshness_project):
        """Test that scan_project returns correct count."""
        registry = ContentRegistry(freshness_project)
        count = scan_project(freshness_project, registry)

        assert count == len(registry.items)
        assert count > 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_load_corrupted_registry(self, registry, freshness_project):
        """Test loading registry with corrupted JSON."""
        # Create corrupted registry file
        registry._registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry._registry_path.write_text("{ invalid json }")

        # Should handle gracefully
        registry.load()
        assert registry.items == {}

    def test_load_registry_with_missing_fields(self, registry, freshness_project):
        """Test loading registry with missing optional fields."""
        registry._registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "items": {
                "test.md": {
                    "path": "test.md",
                    "type": "source_document",
                    # Missing optional fields
                }
            }
        }
        registry._registry_path.write_text(json.dumps(data))

        registry.load()
        assert len(registry.items) == 1
        item = registry.get(Path("test.md"))
        assert item.content_hash == ""
        assert item.depends_on == []

    def test_scan_dirs_from_config(self, freshness_project):
        """Test that scanner respects additional scan_dirs from config."""
        # Create custom directory
        custom_dir = freshness_project.root / "custom_content"
        custom_dir.mkdir()
        (custom_dir / "custom.md").write_text("# Custom")

        # Create project with custom scan dirs
        project_yaml = freshness_project.root / "project.yaml"
        project_yaml.write_text("""
project:
  name: "Test"

freshness:
  scan_dirs:
    - "custom_content"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"

paths:
  content: "content"
  output: "output"
""")

        # Reload project
        project = Project.load(freshness_project.root)
        registry = ContentRegistry(project)

        # Find untracked should check custom directory
        untracked, _ = registry.find_untracked()
        untracked_names = [p.name for p in untracked]
        assert "custom.md" in untracked_names

    def test_ignore_patterns_from_project_config(self, freshness_project):
        """Test ignore patterns from project.yaml."""
        # Create project with ignore patterns
        project_yaml = freshness_project.root / "project.yaml"
        project_yaml.write_text("""
project:
  name: "Test"

freshness:
  ignore_patterns:
    - "*.tmp"
    - "backup_*"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"

paths:
  content: "content"
  output: "output"
""")

        project = Project.load(freshness_project.root)
        registry = ContentRegistry(project)

        patterns = registry.get_ignore_patterns()
        assert "*.tmp" in patterns
        assert "backup_*" in patterns

    def test_should_ignore_various_patterns(self, registry, freshness_project):
        """Test various ignore pattern formats."""
        mediaignore = freshness_project.root / ".mediaignore"
        mediaignore.write_text("""
*.tmp
backup_*
**/cache/**
logs/**
test_*.md
""")
        registry.clear_ignore_cache()

        # Simple patterns
        assert registry._should_ignore(Path("file.tmp"))
        assert registry._should_ignore(Path("backup_2024.md"))

        # Directory patterns
        assert registry._should_ignore(Path("logs/error.log"))
        assert registry._should_ignore(Path("src/cache/data.json"))

        # Wildcard patterns
        assert registry._should_ignore(Path("test_example.md"))

        # Should not ignore
        assert not registry._should_ignore(Path("normal.md"))

    def test_refresh_with_missing_dependency(self, registry, freshness_project):
        """Test refresh when a dependency is missing."""
        # Register item with missing dependency
        registry.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[
                Path("content/en/chapters/01_intro.md"),
                Path("missing_file.md"),  # Doesn't exist
            ],
        )

        # Should handle gracefully
        report = registry.refresh(check_provenance=False)
        assert report.total_items == 2

    def test_mediaignore_with_io_error(self, registry, freshness_project):
        """Test handling of .mediaignore file that can't be read."""
        # Create directory instead of file (will cause read error)
        mediaignore_dir = freshness_project.root / ".mediaignore"
        mediaignore_dir.mkdir(exist_ok=True)

        # Should handle gracefully
        patterns = registry._load_mediaignore()
        assert patterns == []

    def test_scan_video_with_malformed_script(self, freshness_project):
        """Test scanning video scripts with malformed YAML."""
        # Create video script directory
        video_dir = freshness_project.root / "docs/deliverables/video/scripts/en"
        video_dir.mkdir(parents=True, exist_ok=True)

        # Create malformed script
        script = video_dir / "bad_script.yaml"
        script.write_text("{ invalid yaml }")

        registry = ContentRegistry(freshness_project)
        # Should handle gracefully and not crash
        count = scan_project(freshness_project, registry)
        assert count >= 0


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_register_save_load(self, freshness_project):
        """Test complete workflow: register, save, load, query."""
        # Create and populate registry
        registry1 = ContentRegistry(freshness_project)
        registry1.register(
            path=Path("content/en/chapters/01_intro.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry1.register(
            path=Path("output/en/intro.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("content/en/chapters/01_intro.md")],
        )
        registry1.save()

        # Load into new registry
        registry2 = ContentRegistry(freshness_project)
        registry2.load()

        # Verify data persisted
        assert len(registry2.items) == 2
        item = registry2.get(Path("output/en/intro.html"))
        assert item is not None
        assert len(item.depends_on) == 1

    def test_full_workflow_scan_and_refresh(self, freshness_project):
        """Test scanning project and refreshing freshness."""
        registry = ContentRegistry(freshness_project)

        # Scan project
        count = scan_project(freshness_project, registry)
        assert count > 0

        # Refresh freshness
        report = registry.refresh(check_provenance=False)
        assert report.total_items == count
        assert report.fresh_count + report.stale_count + report.expired_count + report.missing_count == count

        # Save for later use
        registry.save()
        assert registry._registry_path.exists()

    def test_dependency_chain_staleness(self, freshness_project):
        """Test staleness propagation through dependency chain."""
        registry = ContentRegistry(freshness_project)

        # Create source
        source_path = freshness_project.root / "content/en/chapters/source.md"
        source_path.write_text("# Source\n\nOriginal content")

        # Wait to ensure different timestamps
        time.sleep(0.1)

        # Create intermediate
        inter_path = freshness_project.root / "output/en/intermediate.html"
        inter_path.write_text("<html>Intermediate</html>")

        # Wait
        time.sleep(0.1)

        # Create final
        final_path = freshness_project.root / "output/en/final.pdf"
        final_path.write_text("PDF content")

        # Register with dependencies
        registry.register(
            path=Path("content/en/chapters/source.md"),
            content_type=ContentType.SOURCE_DOCUMENT,
        )
        registry.register(
            path=Path("output/en/intermediate.html"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("content/en/chapters/source.md")],
        )
        registry.register(
            path=Path("output/en/final.pdf"),
            content_type=ContentType.DELIVERABLE,
            depends_on=[Path("output/en/intermediate.html")],
        )

        # Initial refresh - all fresh
        report = registry.refresh(check_provenance=False)
        assert report.stale_count == 0

        # Wait and modify source
        time.sleep(0.1)
        source_path.write_text("# Source\n\nUpdated content")

        # Refresh - should detect staleness
        report = registry.refresh(check_provenance=False)
        assert report.stale_count >= 1

        # Check impact
        affected = registry.get_impact(Path("content/en/chapters/source.md"))
        assert len(affected) >= 1  # At least intermediate should be affected
