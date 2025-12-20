"""Tests for the general notes system."""

import json
from datetime import datetime
from pathlib import Path

import pytest


class TestNoteTypes:
    """Test Note dataclass and enums."""

    def test_note_type_enum(self):
        from media_engine.notes import NoteType

        assert NoteType.SCENE.value == "scene"
        assert NoteType.DOCUMENT.value == "document"
        assert NoteType.ASSET.value == "asset"
        assert NoteType.PROJECT.value == "project"

    def test_note_status_enum(self):
        from media_engine.notes import NoteStatus

        assert NoteStatus.PENDING.value == "pending"
        assert NoteStatus.COMPLETED.value == "completed"
        assert NoteStatus.ARCHIVED.value == "archived"

    def test_note_priority_enum(self):
        from media_engine.notes import NotePriority

        assert NotePriority.LOW.value == "low"
        assert NotePriority.MEDIUM.value == "medium"
        assert NotePriority.HIGH.value == "high"
        assert NotePriority.CRITICAL.value == "critical"

    def test_note_creation(self):
        from media_engine.notes import Note, NotePriority, NoteStatus, NoteType

        note = Note(
            note_id="test123",
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="Add more examples",
        )

        assert note.note_id == "test123"
        assert note.note_type == NoteType.DOCUMENT
        assert note.target_path == "content/en/intro.md"
        assert note.text == "Add more examples"
        assert note.status == NoteStatus.PENDING
        assert note.priority == NotePriority.MEDIUM
        assert note.created is not None

    def test_note_to_dict(self):
        from media_engine.notes import Note, NoteType

        note = Note(
            note_id="test123",
            note_type=NoteType.SCENE,
            target_path="scripts/intro.yaml",
            target_id="hook",
            text="Add pause",
            tags=["video", "timing"],
        )

        data = note.to_dict()

        assert data["note_id"] == "test123"
        assert data["note_type"] == "scene"
        assert data["target_path"] == "scripts/intro.yaml"
        assert data["target_id"] == "hook"
        assert data["text"] == "Add pause"
        assert data["status"] == "pending"
        assert data["tags"] == ["video", "timing"]

    def test_note_from_dict(self):
        from media_engine.notes import Note, NotePriority, NoteStatus, NoteType

        data = {
            "note_id": "abc123",
            "note_type": "document",
            "target_path": "content/en/chapter.md",
            "target_id": None,
            "text": "Review this section",
            "status": "completed",
            "priority": "high",
            "created": "2025-01-15T10:00:00",
            "updated": "2025-01-15T12:00:00",
            "completed_at": "2025-01-15T12:00:00",
            "tags": ["review"],
            "metadata": {},
        }

        note = Note.from_dict(data)

        assert note.note_id == "abc123"
        assert note.note_type == NoteType.DOCUMENT
        assert note.status == NoteStatus.COMPLETED
        assert note.priority == NotePriority.HIGH
        assert note.completed_at is not None

    def test_note_lifecycle_complete(self):
        from media_engine.notes import Note, NoteStatus, NoteType

        note = Note(
            note_id="test",
            note_type=NoteType.DOCUMENT,
            target_path="test.md",
            text="Test note",
        )

        assert note.status == NoteStatus.PENDING
        assert note.completed_at is None

        note.complete()

        assert note.status == NoteStatus.COMPLETED
        assert note.completed_at is not None

    def test_note_lifecycle_archive(self):
        from media_engine.notes import Note, NoteStatus, NoteType

        note = Note(
            note_id="test",
            note_type=NoteType.DOCUMENT,
            target_path="test.md",
            text="Test note",
        )

        note.archive()

        assert note.status == NoteStatus.ARCHIVED

    def test_note_lifecycle_reopen(self):
        from media_engine.notes import Note, NoteStatus, NoteType

        note = Note(
            note_id="test",
            note_type=NoteType.DOCUMENT,
            target_path="test.md",
            text="Test note",
        )

        note.complete()
        assert note.status == NoteStatus.COMPLETED

        note.reopen()
        assert note.status == NoteStatus.PENDING
        assert note.completed_at is None


class TestNotesRegistry:
    """Test NotesRegistry operations."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create a mock project for testing."""
        from dataclasses import dataclass

        @dataclass
        class MockConfig:
            name: str = "Test Project"

        @dataclass
        class MockProject:
            root: Path
            config: MockConfig

        project = MockProject(root=tmp_path, config=MockConfig())
        return project

    def test_add_note(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        note = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="Add examples",
        )

        assert note.note_id is not None
        assert note.text == "Add examples"
        assert len(registry.get_all()) == 1

    def test_get_note(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        added = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="Test note",
        )

        retrieved = registry.get(added.note_id)

        assert retrieved is not None
        assert retrieved.note_id == added.note_id
        assert retrieved.text == "Test note"

    def test_get_nonexistent_note(self, project):
        from media_engine.notes import NotesRegistry

        registry = NotesRegistry(project)
        result = registry.get("nonexistent")

        assert result is None

    def test_update_note(self, project):
        from media_engine.notes import NotePriority, NotesRegistry, NoteType

        registry = NotesRegistry(project)

        note = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="Original text",
        )

        updated = registry.update(
            note.note_id,
            text="Updated text",
            priority=NotePriority.HIGH,
        )

        assert updated.text == "Updated text"
        assert updated.priority == NotePriority.HIGH

    def test_delete_note(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        note = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="To be deleted",
        )

        assert len(registry.get_all()) == 1

        result = registry.delete(note.note_id)

        assert result is True
        assert len(registry.get_all()) == 0

    def test_delete_nonexistent_note(self, project):
        from media_engine.notes import NotesRegistry

        registry = NotesRegistry(project)
        result = registry.delete("nonexistent")

        assert result is False

    def test_complete_note(self, project):
        from media_engine.notes import NotesRegistry, NoteStatus, NoteType

        registry = NotesRegistry(project)

        note = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="To complete",
        )

        completed = registry.complete(note.note_id)

        assert completed.status == NoteStatus.COMPLETED

    def test_archive_note(self, project):
        from media_engine.notes import NotesRegistry, NoteStatus, NoteType

        registry = NotesRegistry(project)

        note = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="To archive",
        )

        archived = registry.archive(note.note_id)

        assert archived.status == NoteStatus.ARCHIVED

    def test_reopen_note(self, project):
        from media_engine.notes import NotesRegistry, NoteStatus, NoteType

        registry = NotesRegistry(project)

        note = registry.add(
            note_type=NoteType.DOCUMENT,
            target_path="content/en/intro.md",
            text="To reopen",
        )

        registry.complete(note.note_id)
        reopened = registry.reopen(note.note_id)

        assert reopened.status == NoteStatus.PENDING

    def test_get_pending_notes(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        note1 = registry.add(NoteType.DOCUMENT, "doc1.md", "Pending 1")
        note2 = registry.add(NoteType.DOCUMENT, "doc2.md", "Pending 2")
        note3 = registry.add(NoteType.DOCUMENT, "doc3.md", "To complete")

        registry.complete(note3.note_id)

        pending = registry.get_pending()

        assert len(pending) == 2

    def test_get_by_type(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        registry.add(NoteType.DOCUMENT, "doc.md", "Doc note")
        registry.add(NoteType.SCENE, "script.yaml", "Scene note")
        registry.add(NoteType.DOCUMENT, "doc2.md", "Another doc note")

        doc_notes = registry.get_by_type(NoteType.DOCUMENT)
        scene_notes = registry.get_by_type(NoteType.SCENE)

        assert len(doc_notes) == 2
        assert len(scene_notes) == 1

    def test_get_for_target(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        registry.add(NoteType.SCENE, "script.yaml", "Note 1", target_id="scene1")
        registry.add(NoteType.SCENE, "script.yaml", "Note 2", target_id="scene2")
        registry.add(NoteType.SCENE, "other.yaml", "Note 3", target_id="scene1")

        all_script = registry.get_for_target("script.yaml")
        scene1_only = registry.get_for_target("script.yaml", "scene1")

        assert len(all_script) == 2
        assert len(scene1_only) == 1

    def test_get_by_priority(self, project):
        from media_engine.notes import NotePriority, NotesRegistry, NoteType

        registry = NotesRegistry(project)

        registry.add(NoteType.DOCUMENT, "doc1.md", "Low", priority=NotePriority.LOW)
        registry.add(NoteType.DOCUMENT, "doc2.md", "High", priority=NotePriority.HIGH)
        registry.add(NoteType.DOCUMENT, "doc3.md", "Critical", priority=NotePriority.CRITICAL)

        high_priority = registry.get_by_priority(NotePriority.HIGH)
        critical = registry.get_by_priority(NotePriority.CRITICAL)

        assert len(high_priority) == 1
        assert len(critical) == 1

    def test_get_by_tag(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        registry = NotesRegistry(project)

        registry.add(NoteType.DOCUMENT, "doc1.md", "Note 1", tags=["review", "urgent"])
        registry.add(NoteType.DOCUMENT, "doc2.md", "Note 2", tags=["review"])
        registry.add(NoteType.DOCUMENT, "doc3.md", "Note 3", tags=["other"])

        review_notes = registry.get_by_tag("review")
        urgent_notes = registry.get_by_tag("urgent")

        assert len(review_notes) == 2
        assert len(urgent_notes) == 1

    def test_generate_report(self, project):
        from media_engine.notes import NotePriority, NotesRegistry, NoteType

        registry = NotesRegistry(project)

        registry.add(NoteType.DOCUMENT, "doc1.md", "Pending 1")
        registry.add(NoteType.SCENE, "script.yaml", "Pending 2", priority=NotePriority.HIGH)
        note3 = registry.add(NoteType.DOCUMENT, "doc2.md", "To complete")
        note4 = registry.add(NoteType.ASSET, "image.png", "To archive")

        registry.complete(note3.note_id)
        registry.archive(note4.note_id)

        report = registry.generate_report()

        assert report.total_notes == 4
        assert report.pending_count == 2
        assert report.completed_count == 1
        assert report.archived_count == 1
        assert "document" in report.by_type
        assert "scene" in report.by_type

    def test_persistence(self, project):
        from media_engine.notes import NotesRegistry, NoteType

        # Create and add notes
        registry1 = NotesRegistry(project)
        note = registry1.add(NoteType.DOCUMENT, "doc.md", "Persistent note")
        note_id = note.note_id

        # Create a new registry instance (simulates restart)
        registry2 = NotesRegistry(project)
        retrieved = registry2.get(note_id)

        assert retrieved is not None
        assert retrieved.text == "Persistent note"


class TestNotesExport:
    """Test notes export functionality."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create a mock project for testing."""
        from dataclasses import dataclass

        @dataclass
        class MockConfig:
            name: str = "Test Project"

        @dataclass
        class MockProject:
            root: Path
            config: MockConfig

        return MockProject(root=tmp_path, config=MockConfig())

    def test_generate_export(self, project):
        from media_engine.notes import NotePriority, NotesRegistry, NoteType, generate_export

        registry = NotesRegistry(project)
        registry.add(NoteType.DOCUMENT, "doc1.md", "Note 1")
        registry.add(NoteType.SCENE, "script.yaml", "Note 2", target_id="scene1")

        export_data = generate_export(registry, project)

        assert export_data["project"] == "Test Project"
        assert export_data["total_pending"] == 2
        assert len(export_data["notes"]) == 2
        assert "by_target" in export_data
        assert "by_type" in export_data

    def test_write_exports(self, project):
        from media_engine.notes import NotesRegistry, NoteType, generate_export, write_exports

        registry = NotesRegistry(project)
        registry.add(NoteType.DOCUMENT, "doc.md", "Test note")

        export_data = generate_export(registry, project)
        write_exports(project, export_data)

        json_path = project.root / ".media-engine" / "notes-export.json"
        md_path = project.root / ".media-engine" / "notes-export.md"

        assert json_path.exists()
        assert md_path.exists()

        with open(json_path) as f:
            saved_data = json.load(f)
        assert saved_data["total_pending"] == 1


class TestNotesMigration:
    """Test migration from legacy scene notes."""

    @pytest.fixture
    def project_with_legacy_notes(self, tmp_path):
        """Create a project with legacy scene notes."""
        from dataclasses import dataclass

        @dataclass
        class MockConfig:
            name: str = "Test Project"

        @dataclass
        class MockProject:
            root: Path
            config: MockConfig

        project = MockProject(root=tmp_path, config=MockConfig())

        # Create legacy scene notes
        notes_dir = tmp_path / ".media-engine" / "scene-notes"
        notes_dir.mkdir(parents=True)

        legacy_data = {
            "script_path": "content/en/scripts/intro.yaml",
            "notes": {
                "hook": {
                    "text": "Add dramatic pause",
                    "created": "2025-01-15T10:00:00",
                    "scene_id": "hook",
                },
                "demo": {
                    "text": "Show code example",
                    "created": "2025-01-15T11:00:00",
                    "scene_id": "demo",
                },
            },
            "updated": "2025-01-15T11:00:00",
        }

        with open(notes_dir / "content_en_scripts_intro.yaml.json", "w") as f:
            json.dump(legacy_data, f)

        return project

    def test_migrate_scene_notes(self, project_with_legacy_notes):
        from media_engine.notes import NotesRegistry, NoteType, migrate_scene_notes

        result = migrate_scene_notes(project_with_legacy_notes)

        assert result["migrated"] == 2
        assert result["errors"] == []

        # Verify notes were migrated
        registry = NotesRegistry(project_with_legacy_notes)
        notes = registry.get_by_type(NoteType.SCENE)

        assert len(notes) == 2

    def test_migrate_skips_existing(self, project_with_legacy_notes):
        from media_engine.notes import migrate_scene_notes

        # First migration
        result1 = migrate_scene_notes(project_with_legacy_notes)
        assert result1["migrated"] == 2

        # Second migration should skip existing
        result2 = migrate_scene_notes(project_with_legacy_notes)
        assert result2["migrated"] == 0
        assert result2["skipped"] == 2
