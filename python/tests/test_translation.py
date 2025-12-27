"""
Tests for translation tracking functionality.

The translation system uses content hash comparison for automatic change detection.
When source content changes, translations are automatically flagged as outdated.
"""

import pytest
from media_engine.cms.document import Document
from media_engine.cms.translation import TranslationTracker
from media_engine.core.hashing import compute_content_hash
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
    source_content = """# Introduction

This is the source document.
"""
    source_doc = temp_dir / "content/en/chapters/01_intro.md"
    source_doc.write_text(f"""---
title: "Introduction"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
---

{source_content}""")

    # Compute content hash for the source
    source_hash = compute_content_hash(source_content)

    # Create translated document (current with source) - includes source_content_hash
    trans_doc = temp_dir / "content/no/chapters/01_intro.md"
    trans_doc.write_text(f"""---
title: "Introduksjon"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
language: "no"
source_document: "en/chapters/01_intro.md"
source_content_hash: "{source_hash}"
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

    # Create source document (UPDATED content)
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

    # Create translated document with OLD hash (simulating translation from old content)
    old_hash = "oldhash12345678"  # Different from current source hash
    trans_doc = temp_dir / "content/no/chapters/01_intro.md"
    trans_doc.write_text(f"""---
title: "Introduksjon"
version: "1.0.0"
status: "final"
last_modified: "2025-12-15"
language: "no"
source_document: "en/chapters/01_intro.md"
source_content_hash: "{old_hash}"
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

    def test_not_outdated_when_hashes_match(self, translation_project):
        """Test that matching hashes show as current."""
        tracker = TranslationTracker(translation_project)
        statuses = tracker.get_all_statuses()

        assert len(statuses) == 1
        status = statuses[0]
        assert not status.is_outdated
        assert status.status_label == "current"
        # Hash fields should be populated
        assert status.source_content_hash
        assert status.translated_from_hash

    def test_detects_outdated_when_source_updated(self, outdated_translation_project):
        """Test that tracker detects outdated translations via hash mismatch."""
        tracker = TranslationTracker(outdated_translation_project)
        outdated = tracker.get_outdated_translations()

        assert len(outdated) == 1
        status = outdated[0]
        assert status.is_outdated
        assert status.status_label == "outdated"
        # Hash mismatch is the cause
        assert status.source_content_hash != status.translated_from_hash

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

    def test_to_dict_serialization(self, translation_project):
        """Test that TranslationStatus.to_dict() works correctly."""
        tracker = TranslationTracker(translation_project)
        statuses = tracker.get_all_statuses()

        assert len(statuses) == 1
        status_dict = statuses[0].to_dict()

        assert "source_path" in status_dict
        assert "translation_path" in status_dict
        assert "source_content_hash" in status_dict
        assert "translated_from_hash" in status_dict
        assert "is_outdated" in status_dict
        assert "status" in status_dict
        assert status_dict["status"] == "current"


class TestBidirectionalSync:
    """Tests for bidirectional translation sync scenarios."""

    def test_source_update_marks_translation_outdated(self, translation_project):
        """Test that updating source content marks translation as outdated."""
        tracker = TranslationTracker(translation_project)

        # Initially not outdated (hashes match)
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 0

        # Update source content (which changes its hash)
        source_path = translation_project.content_dir / "en/chapters/01_intro.md"
        source_doc = Document.load(source_path)
        source_doc.content = "# Introduction\n\nThis is UPDATED content that will change the hash.\n"
        source_doc.save()

        # Refresh tracker
        tracker.refresh()

        # Now should be outdated because source hash changed
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 1

    def test_translation_update_preserves_source_link(self, translation_project):
        """Test that updating translation preserves source document link."""
        TranslationTracker(translation_project)

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

    def test_mark_synced_updates_source_hash(self, outdated_translation_project):
        """Test that mark_synced updates the source_content_hash field."""
        tracker = TranslationTracker(outdated_translation_project)

        # Initially outdated
        outdated = tracker.get_outdated_translations()
        assert len(outdated) == 1

        # Load translation and mark synced
        trans_path = outdated_translation_project.content_dir / "no/chapters/01_intro.md"
        trans_doc = Document.load(trans_path)

        # Record old hash
        old_hash = trans_doc.metadata.get("source_content_hash")

        tracker.mark_synced(trans_doc)

        # Reload and check hash was updated
        trans_doc_reloaded = Document.load(trans_path)
        new_hash = trans_doc_reloaded.metadata.get("source_content_hash")
        assert new_hash != old_hash

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
source_content_hash: "somehash12345678"
---
# Introduksjon
""")

        project = Project.load(temp_dir)
        tracker = TranslationTracker(project)

        missing = tracker.get_missing_translations("no")

        assert len(missing) == 1
        assert missing[0].title == "Features"


class TestHashBasedTracking:
    """Tests for hash-based translation tracking."""

    def test_empty_hash_marks_outdated(self, temp_dir):
        """Test that missing source_content_hash marks translation as outdated."""
        # Create project structure
        (temp_dir / "content/en/chapters").mkdir(parents=True)
        (temp_dir / "content/no/chapters").mkdir(parents=True)

        # Create project.yaml
        project_yaml = temp_dir / "project.yaml"
        project_yaml.write_text("""
project:
  name: "Hash Test"

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

        # Create source document
        (temp_dir / "content/en/chapters/01_intro.md").write_text("""---
title: "Introduction"
---
# Introduction
""")

        # Create translation WITHOUT source_content_hash
        (temp_dir / "content/no/chapters/01_intro.md").write_text("""---
title: "Introduksjon"
language: "no"
source_document: "en/chapters/01_intro.md"
---
# Introduksjon
""")

        project = Project.load(temp_dir)
        tracker = TranslationTracker(project)

        statuses = tracker.get_all_statuses()
        assert len(statuses) == 1

        # Should be outdated because no hash recorded
        assert statuses[0].is_outdated
        assert statuses[0].translated_from_hash == ""
