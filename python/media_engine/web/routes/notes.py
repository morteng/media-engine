"""
General notes routes for the web dashboard.

Provides a unified API for managing notes across all content types.
"""

from typing import TYPE_CHECKING, Callable, List, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


class NoteCreateRequest(BaseModel):
    """Request body for creating a note."""

    note_type: str
    target_path: str
    text: str
    target_id: Optional[str] = None
    priority: str = "medium"
    tags: Optional[List[str]] = None


class NoteUpdateRequest(BaseModel):
    """Request body for updating a note."""

    text: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None


def register_notes_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register general notes routes."""

    @router.get("/api/notes")
    async def get_notes(
        status: str = None,
        note_type: str = None,
        target_path: str = None,
        priority: str = None,
    ):
        """Get notes with optional filters."""
        project = get_project()
        from ...notes import NotePriority, NotesRegistry, NoteStatus, NoteType

        registry = NotesRegistry(project)
        notes = registry.get_all()

        if status:
            notes = [n for n in notes if n.status == NoteStatus(status)]
        if note_type:
            notes = [n for n in notes if n.note_type == NoteType(note_type)]
        if target_path:
            notes = [n for n in notes if n.target_path == target_path]
        if priority:
            notes = [n for n in notes if n.priority == NotePriority(priority)]

        return {"count": len(notes), "notes": [n.to_dict() for n in notes]}

    @router.post("/api/notes")
    async def create_note(request: NoteCreateRequest):
        """Create a new note."""
        project = get_project()
        from ...notes import NotePriority, NotesRegistry, NoteType

        registry = NotesRegistry(project)
        note = registry.add(
            note_type=NoteType(request.note_type),
            target_path=request.target_path,
            text=request.text,
            target_id=request.target_id,
            priority=NotePriority(request.priority),
            tags=request.tags or [],
        )

        await manager.broadcast({"type": "note_added", "note": note.to_dict()})
        return {"status": "created", "note": note.to_dict()}

    @router.get("/api/notes/pending")
    async def get_pending_notes():
        """Get all pending notes that need action."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        notes = registry.get_pending()

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        notes.sort(key=lambda n: priority_order.get(n.priority.value, 2))

        return {"count": len(notes), "notes": [n.to_dict() for n in notes]}

    @router.get("/api/notes/report")
    async def get_notes_report():
        """Get comprehensive notes report."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        report = registry.generate_report()
        return report.to_dict()

    @router.get("/api/notes/export")
    async def get_notes_export():
        """Get notes export for agents."""
        project = get_project()
        from ...notes import NotesRegistry, generate_export

        registry = NotesRegistry(project)
        return generate_export(registry, project)

    @router.get("/api/notes/{note_id}")
    async def get_note(note_id: str):
        """Get a specific note."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        note = registry.get(note_id)

        if note:
            return {"note": note.to_dict()}
        return {"error": "Note not found"}

    @router.patch("/api/notes/{note_id}")
    async def update_note(note_id: str, request: NoteUpdateRequest):
        """Update a note."""
        project = get_project()
        from ...notes import NotePriority, NotesRegistry

        registry = NotesRegistry(project)
        note = registry.update(
            note_id,
            text=request.text,
            priority=NotePriority(request.priority) if request.priority else None,
            tags=request.tags,
        )

        if note:
            await manager.broadcast({"type": "note_updated", "note": note.to_dict()})
            return {"status": "updated", "note": note.to_dict()}
        return {"error": "Note not found"}

    @router.post("/api/notes/{note_id}/complete")
    async def complete_note(note_id: str):
        """Mark a note as completed."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        note = registry.complete(note_id)

        if note:
            await manager.broadcast({"type": "note_completed", "note": note.to_dict()})
            return {"status": "completed", "note": note.to_dict()}
        return {"error": "Note not found"}

    @router.post("/api/notes/{note_id}/archive")
    async def archive_note(note_id: str):
        """Archive a note."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        note = registry.archive(note_id)

        if note:
            await manager.broadcast({"type": "note_archived", "note": note.to_dict()})
            return {"status": "archived", "note": note.to_dict()}
        return {"error": "Note not found"}

    @router.post("/api/notes/{note_id}/reopen")
    async def reopen_note(note_id: str):
        """Reopen a note."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        note = registry.reopen(note_id)

        if note:
            await manager.broadcast({"type": "note_reopened", "note": note.to_dict()})
            return {"status": "reopened", "note": note.to_dict()}
        return {"error": "Note not found"}

    @router.delete("/api/notes/{note_id}")
    async def delete_note(note_id: str):
        """Delete a note."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        result = registry.delete(note_id)

        if result:
            await manager.broadcast({"type": "note_deleted", "note_id": note_id})
            return {"status": "deleted", "note_id": note_id}
        return {"error": "Note not found"}

    @router.get("/api/notes/target/{target_path:path}")
    async def get_notes_for_target(target_path: str, target_id: str = None):
        """Get all notes for a specific target."""
        project = get_project()
        from ...notes import NotesRegistry

        registry = NotesRegistry(project)
        notes = registry.get_for_target(target_path, target_id)

        return {
            "target_path": target_path,
            "target_id": target_id,
            "count": len(notes),
            "notes": [n.to_dict() for n in notes],
        }

    @router.post("/api/notes/migrate")
    async def migrate_notes():
        """Migrate existing scene notes to general notes system."""
        project = get_project()
        from ...notes import migrate_scene_notes

        result = migrate_scene_notes(project)
        return result
