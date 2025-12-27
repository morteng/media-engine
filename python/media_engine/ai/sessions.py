"""
AI Session Management

Tracks AI work sessions for continuity across conversations.
Enables seamless handoff between sessions and progress tracking.

Features:
- Session lifecycle (active, paused, completed, abandoned)
- Progress tracking with steps
- Change tracking with before/after hashes
- Decision recording with reasoning
- Checkpoint support for granular rollback
"""

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class SessionStep:
    """A step in session progress."""
    description: str
    completed: bool = False
    timestamp: Optional[str] = None
    in_progress: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "completed": self.completed,
            "timestamp": self.timestamp,
            "in_progress": self.in_progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionStep":
        return cls(
            description=data["description"],
            completed=data.get("completed", False),
            timestamp=data.get("timestamp"),
            in_progress=data.get("in_progress", False),
        )


@dataclass
class SessionChange:
    """A change made during a session."""
    file: str
    change_type: str  # created, modified, deleted
    sections: List[str] = field(default_factory=list)
    hash_before: Optional[str] = None
    hash_after: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "type": self.change_type,
            "sections": self.sections,
            "hash_before": self.hash_before,
            "hash_after": self.hash_after,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionChange":
        return cls(
            file=data["file"],
            change_type=data.get("type", "modified"),
            sections=data.get("sections", []),
            hash_before=data.get("hash_before"),
            hash_after=data.get("hash_after"),
            timestamp=data.get("timestamp"),
        )


@dataclass
class SessionDecision:
    """A decision made during a session."""
    question: str
    decision: str
    reasoning: str
    timestamp: str
    scope: Optional[str] = None  # document path or "project"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionDecision":
        return cls(
            question=data["question"],
            decision=data["decision"],
            reasoning=data.get("reasoning", ""),
            timestamp=data.get("timestamp", ""),
            scope=data.get("scope"),
        )


@dataclass
class SessionCheckpoint:
    """A checkpoint for session rollback.

    Captures session state and optionally file snapshots
    for granular rollback capability.
    """
    id: str
    session_id: str
    timestamp: str
    label: str
    step_index: int  # Progress step when checkpoint was created
    files_snapshot: Dict[str, str] = field(default_factory=dict)  # path -> hash
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "label": self.label,
            "step_index": self.step_index,
            "files_snapshot": self.files_snapshot,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCheckpoint":
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            timestamp=data.get("timestamp", ""),
            label=data.get("label", ""),
            step_index=data.get("step_index", 0),
            files_snapshot=data.get("files_snapshot", {}),
            notes=data.get("notes", ""),
        )


@dataclass
class Session:
    """An AI work session."""
    id: str
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: str = ""
    last_active: str = ""
    current_task_id: Optional[str] = None
    progress: List[SessionStep] = field(default_factory=list)
    changes_made: List[SessionChange] = field(default_factory=list)
    decisions: List[SessionDecision] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if not self.last_active:
            self.last_active = self.started_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "started_at": self.started_at,
            "last_active": self.last_active,
            "current_task_id": self.current_task_id,
            "progress": [s.to_dict() for s in self.progress],
            "changes_made": [c.to_dict() for c in self.changes_made],
            "decisions": [d.to_dict() for d in self.decisions],
            "blockers": self.blockers,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            id=data["id"],
            status=SessionStatus(data.get("status", "active")),
            started_at=data.get("started_at", ""),
            last_active=data.get("last_active", ""),
            current_task_id=data.get("current_task_id"),
            progress=[SessionStep.from_dict(s) for s in data.get("progress", [])],
            changes_made=[SessionChange.from_dict(c) for c in data.get("changes_made", [])],
            decisions=[SessionDecision.from_dict(d) for d in data.get("decisions", [])],
            blockers=data.get("blockers", []),
            notes=data.get("notes", ""),
        )


class SessionManager:
    """
    Manages AI sessions for work continuity.

    Sessions track:
    - What task is being worked on
    - Progress through steps
    - Changes made to files
    - Decisions and their reasoning
    - Blockers encountered
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.sessions_dir = self.project_root / ".media-engine" / "ai" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def create(self, task_id: Optional[str] = None) -> Session:
        """Create a new session."""
        session = Session(
            id=str(uuid.uuid4())[:12],
            current_task_id=task_id,
        )
        self.save(session)
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception:
            return None

    def save(self, session: Session) -> None:
        """Save a session."""
        session.last_active = datetime.now().isoformat()
        path = self._session_path(session.id)
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 20,
    ) -> List[Session]:
        """List sessions, optionally filtered by status."""
        sessions = []
        for path in self.sessions_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                if status is None or session.status == status:
                    sessions.append(session)
            except Exception:
                continue

        # Sort by last_active descending
        sessions.sort(key=lambda s: s.last_active, reverse=True)
        return sessions[:limit]

    def get_active(self) -> Optional[Session]:
        """Get the most recently active session."""
        active = self.list_sessions(status=SessionStatus.ACTIVE, limit=1)
        return active[0] if active else None

    def resume(self, session_id: str) -> Optional[Session]:
        """Resume a paused session."""
        session = self.get(session_id)
        if session and session.status == SessionStatus.PAUSED:
            session.status = SessionStatus.ACTIVE
            self.save(session)
            return session
        return None

    def pause(self, session_id: str, notes: str = "") -> Optional[Session]:
        """Pause an active session."""
        session = self.get(session_id)
        if session and session.status == SessionStatus.ACTIVE:
            session.status = SessionStatus.PAUSED
            if notes:
                session.notes = notes
            self.save(session)
            return session
        return None

    def complete(self, session_id: str, notes: str = "") -> Optional[Session]:
        """Mark a session as completed."""
        session = self.get(session_id)
        if session:
            session.status = SessionStatus.COMPLETED
            if notes:
                session.notes = notes
            self.save(session)
            return session
        return None

    def add_progress(
        self,
        session_id: str,
        description: str,
        completed: bool = False,
    ) -> Optional[Session]:
        """Add a progress step to a session."""
        session = self.get(session_id)
        if session:
            step = SessionStep(
                description=description,
                completed=completed,
                timestamp=datetime.now().isoformat() if completed else None,
                in_progress=not completed,
            )
            session.progress.append(step)
            self.save(session)
            return session
        return None

    def complete_step(
        self,
        session_id: str,
        step_index: int,
    ) -> Optional[Session]:
        """Mark a progress step as completed."""
        session = self.get(session_id)
        if session and 0 <= step_index < len(session.progress):
            session.progress[step_index].completed = True
            session.progress[step_index].in_progress = False
            session.progress[step_index].timestamp = datetime.now().isoformat()
            self.save(session)
            return session
        return None

    def record_change(
        self,
        session_id: str,
        file: str,
        change_type: str = "modified",
        sections: Optional[List[str]] = None,
        hash_before: Optional[str] = None,
        hash_after: Optional[str] = None,
    ) -> Optional[Session]:
        """Record a file change in the session."""
        session = self.get(session_id)
        if session:
            change = SessionChange(
                file=file,
                change_type=change_type,
                sections=sections or [],
                hash_before=hash_before,
                hash_after=hash_after,
                timestamp=datetime.now().isoformat(),
            )
            session.changes_made.append(change)
            self.save(session)
            return session
        return None

    def record_decision(
        self,
        session_id: str,
        question: str,
        decision: str,
        reasoning: str,
        scope: Optional[str] = None,
    ) -> Optional[Session]:
        """Record a decision made during the session."""
        session = self.get(session_id)
        if session:
            dec = SessionDecision(
                question=question,
                decision=decision,
                reasoning=reasoning,
                timestamp=datetime.now().isoformat(),
                scope=scope,
            )
            session.decisions.append(dec)
            self.save(session)
            return session
        return None

    def add_blocker(
        self,
        session_id: str,
        blocker: str,
    ) -> Optional[Session]:
        """Add a blocker to the session."""
        session = self.get(session_id)
        if session:
            session.blockers.append(blocker)
            self.save(session)
            return session
        return None

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get full context for resuming a session."""
        session = self.get(session_id)
        if not session:
            return {"error": f"Session not found: {session_id}"}

        # Find incomplete progress
        incomplete_steps = [
            s.description for s in session.progress if not s.completed
        ]
        completed_steps = [
            s.description for s in session.progress if s.completed
        ]

        return {
            "session_id": session.id,
            "status": session.status.value,
            "started_at": session.started_at,
            "last_active": session.last_active,
            "current_task_id": session.current_task_id,
            "completed_steps": completed_steps,
            "remaining_steps": incomplete_steps,
            "files_changed": [c.file for c in session.changes_made],
            "recent_decisions": [
                {"question": d.question, "decision": d.decision}
                for d in session.decisions[-5:]
            ],
            "blockers": session.blockers,
            "notes": session.notes,
        }

    def get_all_decisions(self, scope: Optional[str] = None) -> List[SessionDecision]:
        """Get all decisions across sessions, optionally filtered by scope."""
        all_decisions = []
        for session in self.list_sessions(limit=100):
            for decision in session.decisions:
                if scope is None or decision.scope == scope:
                    all_decisions.append(decision)

        # Sort by timestamp descending
        all_decisions.sort(key=lambda d: d.timestamp, reverse=True)
        return all_decisions

    # -------------------------------------------------------------------------
    # Checkpoint Management
    # -------------------------------------------------------------------------

    def _checkpoints_dir(self, session_id: str) -> Path:
        """Get checkpoints directory for a session."""
        return self.sessions_dir / "checkpoints" / session_id

    def _checkpoint_path(self, session_id: str, checkpoint_id: str) -> Path:
        """Get path for a specific checkpoint."""
        return self._checkpoints_dir(session_id) / f"{checkpoint_id}.json"

    def _file_backups_dir(self, session_id: str, checkpoint_id: str) -> Path:
        """Get file backups directory for a checkpoint."""
        return self._checkpoints_dir(session_id) / "backups" / checkpoint_id

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        if not file_path.exists():
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def create_checkpoint(
        self,
        session_id: str,
        label: str,
        files_to_backup: Optional[List[str]] = None,
        notes: str = "",
    ) -> Optional[SessionCheckpoint]:
        """
        Create a checkpoint for potential rollback.

        Args:
            session_id: Session ID
            label: Human-readable label for the checkpoint
            files_to_backup: Optional list of file paths to backup for rollback
            notes: Optional notes about this checkpoint

        Returns:
            SessionCheckpoint if created, None if session not found
        """
        session = self.get(session_id)
        if not session:
            return None

        checkpoint_id = str(uuid.uuid4())[:12]
        checkpoints_dir = self._checkpoints_dir(session_id)
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        # Determine current step index
        step_index = len([s for s in session.progress if s.completed])

        # Create file snapshots
        files_snapshot: Dict[str, str] = {}
        if files_to_backup:
            backups_dir = self._file_backups_dir(session_id, checkpoint_id)
            backups_dir.mkdir(parents=True, exist_ok=True)

            for file_path in files_to_backup:
                full_path = self.project_root / file_path
                if full_path.exists():
                    # Compute hash and backup file
                    file_hash = self._compute_file_hash(full_path)
                    files_snapshot[file_path] = file_hash

                    # Copy file to backup
                    backup_path = backups_dir / file_path.replace("/", "__")
                    shutil.copy2(full_path, backup_path)

        checkpoint = SessionCheckpoint(
            id=checkpoint_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            label=label,
            step_index=step_index,
            files_snapshot=files_snapshot,
            notes=notes,
        )

        # Save checkpoint
        checkpoint_path = self._checkpoint_path(session_id, checkpoint_id)
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        return checkpoint

    def list_checkpoints(self, session_id: str) -> List[SessionCheckpoint]:
        """List all checkpoints for a session, sorted by timestamp."""
        checkpoints_dir = self._checkpoints_dir(session_id)
        if not checkpoints_dir.exists():
            return []

        checkpoints = []
        for path in checkpoints_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                checkpoints.append(SessionCheckpoint.from_dict(data))
            except Exception:
                continue

        # Sort by timestamp
        checkpoints.sort(key=lambda c: c.timestamp)
        return checkpoints

    def get_checkpoint(
        self, session_id: str, checkpoint_id: str
    ) -> Optional[SessionCheckpoint]:
        """Get a specific checkpoint."""
        path = self._checkpoint_path(session_id, checkpoint_id)
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return SessionCheckpoint.from_dict(data)
        except Exception:
            return None

    def rollback_to_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
        restore_files: bool = True,
    ) -> Dict[str, Any]:
        """
        Rollback a session to a checkpoint.

        Args:
            session_id: Session ID
            checkpoint_id: Checkpoint ID to rollback to
            restore_files: Whether to restore backed up files

        Returns:
            Dict with rollback status and details
        """
        session = self.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        checkpoint = self.get_checkpoint(session_id, checkpoint_id)
        if not checkpoint:
            return {"success": False, "error": "Checkpoint not found"}

        result = {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "checkpoint_label": checkpoint.label,
            "steps_rolled_back": 0,
            "files_restored": [],
            "files_failed": [],
        }

        # Rollback progress steps
        steps_before = len(session.progress)
        if checkpoint.step_index < len(session.progress):
            # Mark steps after checkpoint as incomplete
            for i in range(checkpoint.step_index, len(session.progress)):
                session.progress[i].completed = False
                session.progress[i].in_progress = False
                session.progress[i].timestamp = None
            result["steps_rolled_back"] = steps_before - checkpoint.step_index

        # Restore files if requested
        if restore_files and checkpoint.files_snapshot:
            backups_dir = self._file_backups_dir(session_id, checkpoint_id)
            for file_path, expected_hash in checkpoint.files_snapshot.items():
                backup_path = backups_dir / file_path.replace("/", "__")
                target_path = self.project_root / file_path

                if backup_path.exists():
                    try:
                        # Ensure target directory exists
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_path, target_path)
                        result["files_restored"].append(file_path)
                    except Exception as e:
                        result["files_failed"].append({
                            "path": file_path,
                            "error": str(e),
                        })
                else:
                    result["files_failed"].append({
                        "path": file_path,
                        "error": "Backup file not found",
                    })

        # Remove changes made after checkpoint
        original_changes = len(session.changes_made)
        session.changes_made = [
            c for c in session.changes_made
            if c.timestamp and c.timestamp <= checkpoint.timestamp
        ]
        result["changes_removed"] = original_changes - len(session.changes_made)

        # Add note about rollback
        session.notes = f"{session.notes}\n[Rolled back to checkpoint '{checkpoint.label}' at {datetime.now().isoformat()}]".strip()

        self.save(session)
        return result

    def delete_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint and its file backups.

        Args:
            session_id: Session ID
            checkpoint_id: Checkpoint ID to delete

        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self._checkpoint_path(session_id, checkpoint_id)
        if not checkpoint_path.exists():
            return False

        # Delete checkpoint file
        checkpoint_path.unlink()

        # Delete file backups
        backups_dir = self._file_backups_dir(session_id, checkpoint_id)
        if backups_dir.exists():
            shutil.rmtree(backups_dir)

        return True

    def cleanup_session_checkpoints(self, session_id: str) -> int:
        """
        Remove all checkpoints for a session.

        Useful when session is completed or abandoned.

        Returns:
            Number of checkpoints removed
        """
        checkpoints_dir = self._checkpoints_dir(session_id)
        if not checkpoints_dir.exists():
            return 0

        count = len(list(checkpoints_dir.glob("*.json")))
        shutil.rmtree(checkpoints_dir)
        return count
