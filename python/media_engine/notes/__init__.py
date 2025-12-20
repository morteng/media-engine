"""
General Notes System for Media Engine

Provides a unified system for attaching notes to any content type
with lifecycle management (pending -> completed -> archived).

Usage:
    from media_engine.notes import NotesRegistry, NoteType, NoteStatus

    registry = NotesRegistry(project)

    # Add a note
    note = registry.add(
        note_type=NoteType.DOCUMENT,
        target_path="content/en/chapters/01_intro.md",
        text="Add more examples to the introduction",
        priority=NotePriority.HIGH,
    )

    # Complete a note
    registry.complete(note.note_id)

    # Generate report
    report = registry.generate_report()

    # Export for agents
    from media_engine.notes import generate_export, write_exports
    export_data = generate_export(registry, project)
    write_exports(project, export_data)
"""

from .export import generate_export, write_exports
from .migrate import migrate_scene_notes
from .registry import NotesRegistry
from .types import Note, NotePriority, NotesReport, NoteStatus, NoteType

__all__ = [
    "NotesRegistry",
    "Note",
    "NoteType",
    "NoteStatus",
    "NotePriority",
    "NotesReport",
    "generate_export",
    "write_exports",
    "migrate_scene_notes",
]
