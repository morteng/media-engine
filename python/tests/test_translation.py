"""
Tests for translation tracking functionality.
"""

import pytest
from media_engine.cms.document import Document
from media_engine.cms.translation import TranslationTracker
from media_engine.core.project import Project


@pytest.fixture
def translation_project(temp_dir):
    """Create a project with source and translated documents."""
    # Create project structure
    (temp_dir / "content/en/chapters").mkdir(parents=True)
    (temp_dir / "content/no/chapters").mkdir(parents=True)

    # Create project.yaml
    project_yaml = temp_dir / "project.yaml"
    project_yaml.write_text("""
project:
  name: "Translation Test"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
    "no":
      name: "Norwegian"

paths:
  content: "content"
  assets: "assets"
  output: "output"
""")

    # Create source document
    source_doc = temp_dir / "content/en/chapters/01_intro.md"
    source_doc.write_text("""---
title: "Introduction"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
---

# Introduction

This is the source document.
""")

    # Create translated document (current with source)
    trans_doc = temp_dir / "content/no/chapters/01_intro.md"
    trans_doc.write_text("""---
title: "Introduksjon"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
language: "no"
source_document: "en/chapters/01_intro.md"
source_version: "1.0.0"
---

# Introduksjon

Dette er det oversatte dokumentet.
""")

    return Project.load(temp_dir)


@pytest.fixture
def outdated_translation_project(temp_dir):
    """Create a project where translation is outdated."""
    # Create project structure
    (temp_dir / "content/en/chapters").mkdir(parents=True)
    (temp_dir / "content/no/chapters").mkdir(parents=True)

    # Create project.yaml
    project_yaml = temp_dir / "project.yaml"
    project_yaml.write_text("""
project:
  name: "Outdated Translation Test"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
    "no":
      name: "Norwegian"

paths:
  content: "content"
""")

    # Create source document (version 2.0.0)
    source_doc = temp_dir / "content/en/chapters/01_intro.md"
    source_doc.write_text("""---
title: "Introduction"
version: "2.0.0"
status: "final"
last_modified: "2025-12-16"
---

# Introduction

This is the UPDATED source document.
""")

    # Create translated document (translated from version 1.0.0)
    trans_doc = temp_dir / "content/no/chapters/01_intro.md"
    trans_doc.write_text("""---
title: "Introduksjon"
version: "1.0.0"
status: "final"
last_modified: "2025-12-15"
language: "no"
source_document: "en/chapters/01_intro.md"
source_version: "1.0.0"
---

# Introduksjon

Dette er det GAMLE oversatte dokumentet.
""")

    return Project.load(temp_dir)


class TestTranslationTracker:
    """Tests for TranslationTracker class."""

    def test_finds_translation_pairs(self, translation_project):
        """Test that tracker finds source-translation pairs."""
        tracker = TranslationTracker(translation_project)
        pairs = tracker.get_translation_pairs()

        assert len(pairs) == 1
        source, trans = pairs[0]
        assert source.title == "Introduction"
        assert trans.title == "Introduksjon"

    def test_not_outdated_when_versions_match(self, translation_project):
        """Test that matching versions show as current."""
        tracker = TranslationTracker(translation_project)
        statuses = tracker.get_all_statuses()

        assert len(statuses) == 1
        status = statuses[0]
        assert not status.is_outdated
        assert status.source_version == "1.0.0"
        assert status.translated_version == "1.0.0"
        assert status.status_label == "current"

    def test_detects_outdated_when_source_updated(self, outdated_translation_project):
        """Test that tracker detects outdated translations."""
        tracker = TranslationTracker(outdated_translation_project)
        outdated = tracker.get_outdated_translations()

        assert len(outdated) == 1
        status = outdated[0]
        assert status.is_outdated
        assert status.source_version == "2.0.0"
        assert status.translated_version == "1.0.0"
        assert status.status_label == "outdated"

    def test_get_sync_status_groups_by_language(self, translation_project):
        """Test that sync status is grouped by language."""
        tracker = TranslationTracker(translation_project)
        status = tracker.get_sync_status()

        assert "no" in status
        assert len(status["no"]) == 1

    def test_get_status_for_single_document(self, translation_project):
        """Test getting status for a single translation."""
        tracker = TranslationTracker(translation_project)

        # Load the translation document
        trans_path = translation_project.content_dir / "no/chapters/01_intro.md"
        trans_doc = Document.load(trans_path)

        status = tracker.get_status(trans_doc)

        assert status is not None
        assert status.source_language == "en"
        assert status.target_language == "no"
        assert not status.is_outdated


class TestBidirectionalSync:
    """Tests for bidirectional translation sync scenarios."""

    def test_source_update_marks_translation_outdated(self, translation_project):
        """Test that updating source marks translation as outdated."""
        tracker = TranslationTracker(translation_project)

        # Initially not outdated
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 0

        # Update source version
        source_path = translation_project.content_dir / "en/chapters/01_intro.md"
        source_doc = Document.load(source_path)
        source_doc.increment_version("minor")  # 1.0.0 -> 1.1.0
        source_doc.save()

        # Refresh tracker
        tracker.refresh()

        # Now should be outdated
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 1
        assert outdated[0].source_version == "1.1.0"
        assert outdated[0].translated_version == "1.0.0"

    def test_translation_update_preserves_source_link(self, translation_project):
        """Test that updating translation preserves source document link."""
        tracker = TranslationTracker(translation_project)

        # Load and update translation
        trans_path = translation_project.content_dir / "no/chapters/01_intro.md"
        trans_doc = Document.load(trans_path)

        # Update translation content
        trans_doc.increment_version("patch")
        trans_doc.save()

        # Reload and check source link is preserved
        trans_doc_reloaded = Document.load(trans_path)
        assert trans_doc_reloaded.metadata.get("source_document") == "en/chapters/01_intro.md"
        assert trans_doc_reloaded.metadata.get("language") == "no"

    def test_mark_synced_updates_source_version(self, outdated_translation_project):
        """Test that mark_synced updates the source_version field."""
        tracker = TranslationTracker(outdated_translation_project)

        # Initially outdated
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 1

        # Load translation and mark synced
        trans_path = outdated_translation_project.content_dir / "no/chapters/01_intro.md"
        trans_doc = Document.load(trans_path)
        tracker.mark_synced(trans_doc)

        # Reload and check
        trans_doc_reloaded = Document.load(trans_path)
        assert trans_doc_reloaded.metadata.get("source_version") == "2.0.0"

        # Refresh tracker and check no longer outdated
        tracker.refresh()
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 0


class TestMissingTranslations:
    """Tests for detecting missing translations."""

    def test_get_missing_translations(self, temp_dir):
        """Test detection of source docs without translations."""
        # Create project structure
        (temp_dir / "content/en/chapters").mkdir(parents=True)
        (temp_dir / "content/no/chapters").mkdir(parents=True)

        # Create project.yaml
        project_yaml = temp_dir / "project.yaml"
        project_yaml.write_text("""
project:
  name: "Missing Translation Test"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
    "no":
      name: "Norwegian"

paths:
  content: "content"
""")

        # Create two source documents
        (temp_dir / "content/en/chapters/01_intro.md").write_text("""---
title: "Introduction"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
---
# Introduction
""")

        (temp_dir / "content/en/chapters/02_features.md").write_text("""---
title: "Features"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
---
# Features
""")

        # Create translation for only the first
        (temp_dir / "content/no/chapters/01_intro.md").write_text("""---
title: "Introduksjon"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
language: "no"
source_document: "en/chapters/01_intro.md"
source_version: "1.0.0"
---
# Introduksjon
""")

        project = Project.load(temp_dir)
        tracker = TranslationTracker(project)

        missing = tracker.get_missing_translations("no")

        assert len(missing) == 1
        assert missing[0].title == "Features"


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_version_comparison(self, translation_project):
        """Test version comparison logic."""
        tracker = TranslationTracker(translation_project)

        # Test equal versions
        assert tracker._compare_versions("1.0.0", "1.0.0") == 0

        # Test greater versions
        assert tracker._compare_versions("2.0.0", "1.0.0") > 0
        assert tracker._compare_versions("1.1.0", "1.0.0") > 0
        assert tracker._compare_versions("1.0.1", "1.0.0") > 0

        # Test lesser versions
        assert tracker._compare_versions("1.0.0", "2.0.0") < 0
        assert tracker._compare_versions("1.0.0", "1.1.0") < 0
        assert tracker._compare_versions("1.0.0", "1.0.1") < 0

        # Test partial versions
        assert tracker._compare_versions("1.0", "1.0.0") == 0
        assert tracker._compare_versions("1", "1.0.0") == 0
