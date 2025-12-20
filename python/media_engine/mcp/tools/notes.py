"""Notes management tools for MCP."""

import json


def register_notes_tools(mcp, server_instance):
    """Register notes-related MCP tools."""

    @mcp.tool()
    async def notes_list(
        status: str = None,
        note_type: str = None,
        target_path: str = None,
        priority: str = None,
        tag: str = None,
    ) -> str:
        """
        List notes with optional filters.

        Args:
            status: Filter by status: 'pending', 'completed', 'archived'
            note_type: Filter by type: 'scene', 'document', 'asset', 'project', etc.
            target_path: Filter by target content path
            priority: Filter by priority: 'low', 'medium', 'high', 'critical'
            tag: Filter by tag
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotePriority, NotesRegistry, NoteStatus, NoteType

        registry = NotesRegistry(server_instance.project)
        notes = registry.get_all()

        # Apply filters
        if status:
            notes = [n for n in notes if n.status == NoteStatus(status)]
        if note_type:
            notes = [n for n in notes if n.note_type == NoteType(note_type)]
        if target_path:
            notes = [n for n in notes if n.target_path == target_path]
        if priority:
            notes = [n for n in notes if n.priority == NotePriority(priority)]
        if tag:
            notes = [n for n in notes if tag in n.tags]

        return json.dumps(
            {
                "count": len(notes),
                "notes": [n.to_dict() for n in notes],
            },
            indent=2,
        )

    @mcp.tool()
    async def notes_pending() -> str:
        """
        Get all pending notes that need action.

        Returns notes organized by priority (critical first).
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry, NoteStatus

        registry = NotesRegistry(server_instance.project)
        notes = registry.get_pending()

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        notes.sort(key=lambda n: priority_order.get(n.priority.value, 2))

        return json.dumps(
            {
                "count": len(notes),
                "notes": [n.to_dict() for n in notes],
            },
            indent=2,
        )

    @mcp.tool()
    async def notes_add(
        note_type: str,
        target_path: str,
        text: str,
        target_id: str = None,
        priority: str = "medium",
        tags: str = None,
    ) -> str:
        """
        Add a new note.

        Args:
            note_type: Type: 'scene', 'document', 'asset', 'project', 'chapter', etc.
            target_path: Path to the target content (relative to project)
            text: The note content
            target_id: Optional sub-target ID (e.g., scene_id within a script)
            priority: Priority: 'low', 'medium', 'high', 'critical'
            tags: Comma-separated tags (optional)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotePriority, NotesRegistry, NoteType

        registry = NotesRegistry(server_instance.project)

        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        note = registry.add(
            note_type=NoteType(note_type),
            target_path=target_path,
            text=text,
            target_id=target_id,
            priority=NotePriority(priority),
            tags=tag_list,
        )

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "added",
                "note_id": note.note_id,
                "note": note.to_dict(),
            },
            indent=2,
        )

    @mcp.tool()
    async def notes_complete(note_id: str) -> str:
        """
        Mark a note as completed.

        Args:
            note_id: The note ID to complete
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry

        registry = NotesRegistry(server_instance.project)
        note = registry.complete(note_id)

        if note:
            server_instance._invalidate_cache()
            return json.dumps({"status": "completed", "note": note.to_dict()}, indent=2)
        return json.dumps({"error": "Note not found"}, indent=2)

    @mcp.tool()
    async def notes_archive(note_id: str) -> str:
        """
        Archive a note.

        Args:
            note_id: The note ID to archive
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry

        registry = NotesRegistry(server_instance.project)
        note = registry.archive(note_id)

        if note:
            server_instance._invalidate_cache()
            return json.dumps({"status": "archived", "note": note.to_dict()}, indent=2)
        return json.dumps({"error": "Note not found"}, indent=2)

    @mcp.tool()
    async def notes_reopen(note_id: str) -> str:
        """
        Reopen a completed or archived note.

        Args:
            note_id: The note ID to reopen
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry

        registry = NotesRegistry(server_instance.project)
        note = registry.reopen(note_id)

        if note:
            server_instance._invalidate_cache()
            return json.dumps({"status": "reopened", "note": note.to_dict()}, indent=2)
        return json.dumps({"error": "Note not found"}, indent=2)

    @mcp.tool()
    async def notes_delete(note_id: str) -> str:
        """
        Delete a note permanently.

        Args:
            note_id: The note ID to delete
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry

        registry = NotesRegistry(server_instance.project)
        result = registry.delete(note_id)

        if result:
            server_instance._invalidate_cache()
            return json.dumps({"status": "deleted", "note_id": note_id}, indent=2)
        return json.dumps({"error": "Note not found"}, indent=2)

    @mcp.tool()
    async def notes_report() -> str:
        """
        Get comprehensive notes report.

        Returns summary of all notes by status, type, and priority.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry

        registry = NotesRegistry(server_instance.project)
        report = registry.generate_report()

        return json.dumps(report.to_dict(), indent=2)

    @mcp.tool()
    async def notes_for_target(target_path: str, target_id: str = None) -> str:
        """
        Get all notes for a specific target.

        Args:
            target_path: Path to the target content
            target_id: Optional sub-target ID
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry

        registry = NotesRegistry(server_instance.project)
        notes = registry.get_for_target(target_path, target_id)

        return json.dumps(
            {
                "target_path": target_path,
                "target_id": target_id,
                "count": len(notes),
                "notes": [n.to_dict() for n in notes],
            },
            indent=2,
        )

    @mcp.tool()
    async def notes_export() -> str:
        """
        Export all pending notes for agent consumption.

        Returns structured export with all pending notes organized by target.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import NotesRegistry, generate_export

        registry = NotesRegistry(server_instance.project)
        export_data = generate_export(registry, server_instance.project)

        return json.dumps(export_data, indent=2)

    @mcp.tool()
    async def notes_migrate() -> str:
        """
        Migrate existing scene notes to the general notes system.

        Reads from .media-engine/scene-notes/ and converts to new format.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...notes import migrate_scene_notes

        result = migrate_scene_notes(server_instance.project)
        server_instance._invalidate_cache()

        return json.dumps(result, indent=2)
