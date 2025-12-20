"""
Notes Registry

Central registry for managing notes across all content types.
Stores data in {project}/.media-engine/notes/
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from .types import Note, NotePriority, NotesReport, NoteStatus, NoteType

if TYPE_CHECKING:
    from ..core.project import Project


class NotesRegistry:
    """
    Manages notes for all content types in a project.

    Features:
    - Add/update/delete notes
    - Query by type, status, target
    - Lifecycle management (pending -> completed -> archived)
    - Export for agent consumption
    - Audit logging integration
    """

    def __init__(self, project: "Project"):
        self.project = project
        self.data_dir = project.root / ".media-engine" / "notes"
        self.registry_path = self.data_dir / "registry.json"
        self._notes: Dict[str, Note] = {}
        self._loaded = False

    def _load(self):
        """Load notes from disk."""
        if self._loaded:
            return
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                data = json.load(f)
            for note_id, note_data in data.get("notes", {}).items():
                self._notes[note_id] = Note.from_dict(note_data)
        self._loaded = True

    def _save(self):
        """Save notes to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "project": self.project.config.name,
            "last_updated": datetime.now().isoformat(),
            "stats": self._compute_stats(),
            "notes": {nid: n.to_dict() for nid, n in self._notes.items()},
        }
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def _compute_stats(self) -> Dict[str, int]:
        """Compute summary statistics."""
        stats = {"total": 0, "pending": 0, "completed": 0, "archived": 0}
        for note in self._notes.values():
            stats["total"] += 1
            stats[note.status.value] += 1
        return stats

    def _generate_id(self, text: str, target_path: str) -> str:
        """Generate unique note ID."""
        content = f"{text}:{target_path}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:8]

    def _log_action(self, action: str, details: str = None, user: str = None):
        """Log action to audit log."""
        try:
            from ..audit import log_action

            log_action(self.project, action, details=details, user=user)
        except Exception:
            pass

    # === CRUD Operations ===

    def add(
        self,
        note_type: NoteType,
        target_path: str,
        text: str,
        target_id: str = None,
        priority: NotePriority = NotePriority.MEDIUM,
        created_by: str = None,
        tags: List[str] = None,
        metadata: Dict = None,
    ) -> Note:
        """Add a new note."""
        self._load()

        note_id = self._generate_id(text, target_path)
        note = Note(
            note_id=note_id,
            note_type=note_type,
            target_path=target_path,
            target_id=target_id,
            text=text,
            priority=priority,
            created_by=created_by,
            tags=tags or [],
            metadata=metadata or {},
        )

        self._notes[note_id] = note
        self._save()
        self._log_action("note_added", f"Note added to {target_path}", user=created_by)

        return note

    def get(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        self._load()
        return self._notes.get(note_id)

    def update(
        self,
        note_id: str,
        text: str = None,
        priority: NotePriority = None,
        tags: List[str] = None,
    ) -> Optional[Note]:
        """Update a note's content."""
        self._load()
        note = self._notes.get(note_id)
        if not note:
            return None

        if text is not None:
            note.text = text
        if priority is not None:
            note.priority = priority
        if tags is not None:
            note.tags = tags
        note.updated = datetime.now()

        self._save()
        self._log_action("note_updated", f"Note {note_id} updated")
        return note

    def delete(self, note_id: str) -> bool:
        """Delete a note permanently."""
        self._load()
        if note_id in self._notes:
            del self._notes[note_id]
            self._save()
            self._log_action("note_deleted", f"Note {note_id} deleted")
            return True
        return False

    # === Lifecycle Operations ===

    def complete(self, note_id: str) -> Optional[Note]:
        """Mark a note as completed."""
        self._load()
        note = self._notes.get(note_id)
        if note:
            note.complete()
            self._save()
            self._log_action("note_completed", f"Note {note_id} completed")
        return note

    def archive(self, note_id: str) -> Optional[Note]:
        """Archive a note."""
        self._load()
        note = self._notes.get(note_id)
        if note:
            note.archive()
            self._save()
            self._log_action("note_archived", f"Note {note_id} archived")
        return note

    def reopen(self, note_id: str) -> Optional[Note]:
        """Reopen a completed/archived note."""
        self._load()
        note = self._notes.get(note_id)
        if note:
            note.reopen()
            self._save()
            self._log_action("note_reopened", f"Note {note_id} reopened")
        return note

    # === Query Operations ===

    def get_all(self) -> List[Note]:
        """Get all notes."""
        self._load()
        return list(self._notes.values())

    def get_by_status(self, status: NoteStatus) -> List[Note]:
        """Get notes by status."""
        self._load()
        return [n for n in self._notes.values() if n.status == status]

    def get_pending(self) -> List[Note]:
        """Get all pending notes."""
        return self.get_by_status(NoteStatus.PENDING)

    def get_by_type(self, note_type: NoteType) -> List[Note]:
        """Get notes by type."""
        self._load()
        return [n for n in self._notes.values() if n.note_type == note_type]

    def get_for_target(self, target_path: str, target_id: str = None) -> List[Note]:
        """Get notes for a specific target."""
        self._load()
        notes = [n for n in self._notes.values() if n.target_path == target_path]
        if target_id:
            notes = [n for n in notes if n.target_id == target_id]
        return notes

    def get_by_priority(self, priority: NotePriority) -> List[Note]:
        """Get notes by priority."""
        self._load()
        return [n for n in self._notes.values() if n.priority == priority]

    def get_by_tag(self, tag: str) -> List[Note]:
        """Get notes with a specific tag."""
        self._load()
        return [n for n in self._notes.values() if tag in n.tags]

    # === Reports ===

    def generate_report(self) -> NotesReport:
        """Generate comprehensive notes report."""
        self._load()

        report = NotesReport(
            project_name=self.project.config.name,
            generated=datetime.now(),
        )

        by_type: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}

        for note in self._notes.values():
            report.total_notes += 1

            # Count by status
            if note.status == NoteStatus.PENDING:
                report.pending_count += 1
                report.pending_notes.append(note)
            elif note.status == NoteStatus.COMPLETED:
                report.completed_count += 1
                report.recent_completed.append(note)
            else:
                report.archived_count += 1

            # Count by type
            type_key = note.note_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by priority
            prio_key = note.priority.value
            by_priority[prio_key] = by_priority.get(prio_key, 0) + 1

        report.by_type = by_type
        report.by_priority = by_priority

        # Sort pending by priority (critical first)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        report.pending_notes.sort(key=lambda n: priority_order.get(n.priority.value, 2))

        # Sort completed by completion date (most recent first)
        report.recent_completed.sort(key=lambda n: n.completed_at or datetime.min, reverse=True)
        report.recent_completed = report.recent_completed[:10]

        return report

    def save(self):
        """Explicitly save to disk."""
        self._save()
