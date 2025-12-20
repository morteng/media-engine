"""
Notes System Types

Defines note types, statuses, and data structures for the general notes system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NoteType(str, Enum):
    """Types of content that notes can be attached to."""

    SCENE = "scene"
    DOCUMENT = "document"
    ASSET = "asset"
    PROJECT = "project"
    CHAPTER = "chapter"
    TRANSLATION = "translation"
    SCRIPT = "script"
    DIAGRAM = "diagram"


class NoteStatus(str, Enum):
    """Lifecycle states for notes."""

    PENDING = "pending"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NotePriority(str, Enum):
    """Priority levels for notes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Note:
    """
    A single note attached to content.

    Notes can be attached to any content type and track lifecycle state.
    """

    note_id: str
    note_type: NoteType
    target_path: str
    text: str
    target_id: Optional[str] = None
    status: NoteStatus = NoteStatus.PENDING
    priority: NotePriority = NotePriority.MEDIUM
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created is None:
            self.created = datetime.now()
        if self.updated is None:
            self.updated = self.created

    def complete(self):
        """Mark note as completed."""
        self.status = NoteStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated = datetime.now()

    def archive(self):
        """Archive the note."""
        self.status = NoteStatus.ARCHIVED
        self.updated = datetime.now()

    def reopen(self):
        """Reopen an archived or completed note."""
        self.status = NoteStatus.PENDING
        self.completed_at = None
        self.updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "note_id": self.note_id,
            "note_type": self.note_type.value,
            "target_path": self.target_path,
            "target_id": self.target_id,
            "text": self.text,
            "status": self.status.value,
            "priority": self.priority.value,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        """Create from dictionary."""
        return cls(
            note_id=data["note_id"],
            note_type=NoteType(data["note_type"]),
            target_path=data["target_path"],
            target_id=data.get("target_id"),
            text=data["text"],
            status=NoteStatus(data.get("status", "pending")),
            priority=NotePriority(data.get("priority", "medium")),
            created=datetime.fromisoformat(data["created"]) if data.get("created") else None,
            updated=datetime.fromisoformat(data["updated"]) if data.get("updated") else None,
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            created_by=data.get("created_by"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class NotesReport:
    """Summary report of notes status."""

    project_name: str
    generated: datetime
    total_notes: int = 0
    pending_count: int = 0
    completed_count: int = 0
    archived_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    pending_notes: List[Note] = field(default_factory=list)
    recent_completed: List[Note] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "generated": self.generated.isoformat(),
            "summary": {
                "total": self.total_notes,
                "pending": self.pending_count,
                "completed": self.completed_count,
                "archived": self.archived_count,
            },
            "by_type": self.by_type,
            "by_priority": self.by_priority,
            "pending_notes": [n.to_dict() for n in self.pending_notes],
            "recent_completed": [n.to_dict() for n in self.recent_completed],
        }
