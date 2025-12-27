"""
AI Notes System

Allows AI to leave notes for humans or future AI sessions.
Notes can flag uncertainties, suggest improvements, or request review.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class NoteType(str, Enum):
    """Types of notes."""
    UNCERTAINTY = "uncertainty"        # AI is unsure about something
    SUGGESTION = "suggestion"          # Improvement suggestion
    HUMAN_REVIEW = "human_review"      # Needs human verification
    DECISION_RATIONALE = "decision"    # Explains a decision
    TODO = "todo"                      # Action item
    WARNING = "warning"                # Potential issue
    INFO = "info"                      # Informational note


class NoteStatus(str, Enum):
    """Note status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class NotePriority(str, Enum):
    """Note priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NoteLocation:
    """Location within a document."""
    section: Optional[str] = None
    line: Optional[int] = None
    anchor: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "line": self.line,
            "anchor": self.anchor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NoteLocation":
        return cls(
            section=data.get("section"),
            line=data.get("line"),
            anchor=data.get("anchor"),
        )


@dataclass
class Note:
    """An AI note attached to a document or project."""
    id: str
    note_type: NoteType
    content: str
    document: Optional[str] = None  # Document path, None for project-level
    location: Optional[NoteLocation] = None
    status: NoteStatus = NoteStatus.OPEN
    priority: NotePriority = NotePriority.MEDIUM
    created_by: Optional[str] = None  # Session ID
    created_at: str = ""
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.note_type.value,
            "content": self.content,
            "document": self.document,
            "location": self.location.to_dict() if self.location else None,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
            "resolution": self.resolution,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        location = None
        if data.get("location"):
            location = NoteLocation.from_dict(data["location"])

        return cls(
            id=data["id"],
            note_type=NoteType(data.get("type", "info")),
            content=data["content"],
            document=data.get("document"),
            location=location,
            status=NoteStatus(data.get("status", "open")),
            priority=NotePriority(data.get("priority", "medium")),
            created_by=data.get("created_by"),
            created_at=data.get("created_at", ""),
            resolved_at=data.get("resolved_at"),
            resolved_by=data.get("resolved_by"),
            resolution=data.get("resolution"),
            tags=data.get("tags", []),
        )


class NotesManager:
    """
    Manages AI notes for documents and projects.

    Notes allow AI to:
    - Flag uncertainties for human review
    - Leave suggestions for improvements
    - Explain decisions made
    - Create action items
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.notes_dir = self.project_root / ".media-engine" / "ai" / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.notes_dir / "index.json"

    def _load_index(self) -> Dict[str, Any]:
        """Load notes index."""
        if not self.index_path.exists():
            return {"notes": [], "updated_at": None}
        try:
            with open(self.index_path) as f:
                return json.load(f)
        except Exception:
            return {"notes": [], "updated_at": None}

    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save notes index."""
        index["updated_at"] = datetime.now().isoformat()
        with open(self.index_path, "w") as f:
            json.dump(index, f, indent=2)

    def add(
        self,
        note_type: NoteType,
        content: str,
        document: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Note:
        """
        Add a new note.

        Args:
            note_type: Type of note
            content: Note content
            document: Document path (None for project-level)
            location: Location within document
            priority: Note priority
            session_id: AI session that created this
            tags: Tags for categorization

        Returns:
            The created note
        """
        loc = NoteLocation.from_dict(location) if location else None

        note = Note(
            id=str(uuid.uuid4())[:8],
            note_type=note_type,
            content=content,
            document=document,
            location=loc,
            priority=NotePriority(priority),
            created_by=session_id,
            tags=tags or [],
        )

        index = self._load_index()
        index["notes"].append(note.to_dict())
        self._save_index(index)

        return note

    def get(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        index = self._load_index()
        for note_data in index["notes"]:
            if note_data["id"] == note_id:
                return Note.from_dict(note_data)
        return None

    def list_notes(
        self,
        document: Optional[str] = None,
        note_type: Optional[NoteType] = None,
        status: Optional[NoteStatus] = None,
        priority: Optional[NotePriority] = None,
        limit: int = 100,
    ) -> List[Note]:
        """List notes with optional filters."""
        index = self._load_index()
        notes = []

        for note_data in index["notes"]:
            note = Note.from_dict(note_data)

            if document is not None and note.document != document:
                continue
            if note_type and note.note_type != note_type:
                continue
            if status and note.status != status:
                continue
            if priority and note.priority != priority:
                continue

            notes.append(note)

        # Sort by priority (critical first) then by created_at
        priority_order = {
            NotePriority.CRITICAL: 0,
            NotePriority.HIGH: 1,
            NotePriority.MEDIUM: 2,
            NotePriority.LOW: 3,
        }
        notes.sort(key=lambda n: (priority_order.get(n.priority, 2), n.created_at))

        return notes[:limit]

    def get_open_notes(self, document: Optional[str] = None) -> List[Note]:
        """Get all open notes."""
        return self.list_notes(document=document, status=NoteStatus.OPEN)

    def get_notes_requiring_review(self) -> List[Note]:
        """Get notes that need human review."""
        return self.list_notes(
            note_type=NoteType.HUMAN_REVIEW,
            status=NoteStatus.OPEN,
        )

    def get_uncertainties(self) -> List[Note]:
        """Get all open uncertainties."""
        return self.list_notes(
            note_type=NoteType.UNCERTAINTY,
            status=NoteStatus.OPEN,
        )

    def resolve(
        self,
        note_id: str,
        resolution: str,
        resolved_by: Optional[str] = None,
    ) -> Optional[Note]:
        """Resolve a note."""
        index = self._load_index()

        for i, note_data in enumerate(index["notes"]):
            if note_data["id"] == note_id:
                note_data["status"] = NoteStatus.RESOLVED.value
                note_data["resolved_at"] = datetime.now().isoformat()
                note_data["resolved_by"] = resolved_by
                note_data["resolution"] = resolution
                index["notes"][i] = note_data
                self._save_index(index)
                return Note.from_dict(note_data)

        return None

    def dismiss(self, note_id: str, reason: Optional[str] = None) -> Optional[Note]:
        """Dismiss a note without resolving."""
        index = self._load_index()

        for i, note_data in enumerate(index["notes"]):
            if note_data["id"] == note_id:
                note_data["status"] = NoteStatus.DISMISSED.value
                note_data["resolved_at"] = datetime.now().isoformat()
                if reason:
                    note_data["resolution"] = f"Dismissed: {reason}"
                index["notes"][i] = note_data
                self._save_index(index)
                return Note.from_dict(note_data)

        return None

    def update_status(
        self,
        note_id: str,
        status: NoteStatus,
    ) -> Optional[Note]:
        """Update note status."""
        index = self._load_index()

        for i, note_data in enumerate(index["notes"]):
            if note_data["id"] == note_id:
                note_data["status"] = status.value
                if status == NoteStatus.RESOLVED:
                    note_data["resolved_at"] = datetime.now().isoformat()
                index["notes"][i] = note_data
                self._save_index(index)
                return Note.from_dict(note_data)

        return None

    def delete(self, note_id: str) -> bool:
        """Delete a note."""
        index = self._load_index()
        original_len = len(index["notes"])
        index["notes"] = [n for n in index["notes"] if n["id"] != note_id]

        if len(index["notes"]) < original_len:
            self._save_index(index)
            return True
        return False

    def get_document_notes(self, document: str) -> Dict[str, Any]:
        """Get all notes for a document organized by section."""
        notes = self.list_notes(document=document)

        by_section: Dict[str, List[Dict]] = {}
        no_section = []

        for note in notes:
            if note.location and note.location.section:
                section = note.location.section
                if section not in by_section:
                    by_section[section] = []
                by_section[section].append(note.to_dict())
            else:
                no_section.append(note.to_dict())

        return {
            "document": document,
            "total": len(notes),
            "by_section": by_section,
            "general": no_section,
            "open_count": len([n for n in notes if n.status == NoteStatus.OPEN]),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get notes statistics."""
        notes = self.list_notes(limit=10000)

        by_type = {}
        for nt in NoteType:
            by_type[nt.value] = len([n for n in notes if n.note_type == nt])

        by_status = {}
        for status in NoteStatus:
            by_status[status.value] = len([n for n in notes if n.status == status])

        by_priority = {}
        for priority in NotePriority:
            by_priority[priority.value] = len([n for n in notes if n.priority == priority])

        # Documents with notes
        docs_with_notes = set(n.document for n in notes if n.document)

        return {
            "total": len(notes),
            "by_type": by_type,
            "by_status": by_status,
            "by_priority": by_priority,
            "open": by_status.get("open", 0),
            "documents_with_notes": len(docs_with_notes),
            "requiring_review": len([
                n for n in notes
                if n.note_type == NoteType.HUMAN_REVIEW and n.status == NoteStatus.OPEN
            ]),
        }

    def cleanup(self, max_age_days: int = 30) -> int:
        """Remove old resolved/dismissed notes."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()

        index = self._load_index()
        original_count = len(index["notes"])

        index["notes"] = [
            n for n in index["notes"]
            if n.get("status") not in ("resolved", "dismissed")
            or (n.get("resolved_at") and n["resolved_at"] > cutoff_str)
        ]

        self._save_index(index)
        return original_count - len(index["notes"])
