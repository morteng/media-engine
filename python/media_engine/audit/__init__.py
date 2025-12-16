"""
Audit Logging System for Media Engine

Provides comprehensive audit trail for all operations:
- Document changes
- Build operations
- Translation updates
- User actions
- System events

All entries are stored in JSON Lines format for easy querying.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str
    action: str
    category: str
    user: Optional[str]
    details: Optional[str]
    file_path: Optional[str]
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(**data)


class AuditLogger:
    """
    Audit logger that writes to project audit log.

    Log file location: {project}/.media-engine/audit.log
    Format: JSON Lines (one JSON object per line)
    """

    # Action categories
    CATEGORY_DOCUMENT = "document"
    CATEGORY_BUILD = "build"
    CATEGORY_TRANSLATION = "translation"
    CATEGORY_QUALITY = "quality"
    CATEGORY_SYSTEM = "system"
    CATEGORY_USER = "user"

    def __init__(self, project):
        self.project = project
        self.log_dir = project.root / ".media-engine"
        self.log_path = self.log_dir / "audit.log"

    def _ensure_log_dir(self):
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        category: str = None,
        details: str = None,
        user: str = None,
        file_path: Path = None,
        **metadata
    ) -> AuditEntry:
        """
        Log an action to the audit trail.

        Args:
            action: Action identifier (e.g., "document_updated", "build_started")
            category: Category of action (document, build, translation, etc.)
            details: Human-readable description
            user: User identifier
            file_path: Related file path
            **metadata: Additional metadata to store

        Returns:
            The created AuditEntry
        """
        self._ensure_log_dir()

        # Auto-detect category from action if not provided
        if category is None:
            category = self._infer_category(action)

        # Get user from environment if not provided
        if user is None:
            user = os.environ.get("USER") or os.environ.get("USERNAME")

        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            category=category,
            user=user,
            details=details,
            file_path=str(file_path) if file_path else None,
            metadata=metadata,
        )

        # Append to log file
        with open(self.log_path, "a") as f:
            f.write(entry.to_json() + "\n")

        return entry

    def _infer_category(self, action: str) -> str:
        """Infer category from action name."""
        action_lower = action.lower()
        if any(x in action_lower for x in ["document", "content", "chapter"]):
            return self.CATEGORY_DOCUMENT
        elif any(x in action_lower for x in ["build", "generate", "compile"]):
            return self.CATEGORY_BUILD
        elif any(x in action_lower for x in ["translat", "sync"]):
            return self.CATEGORY_TRANSLATION
        elif any(x in action_lower for x in ["quality", "valid", "check"]):
            return self.CATEGORY_QUALITY
        elif any(x in action_lower for x in ["system", "cache", "config"]):
            return self.CATEGORY_SYSTEM
        return self.CATEGORY_USER

    def get_entries(
        self,
        limit: int = None,
        category: str = None,
        action: str = None,
        since: datetime = None,
        file_path: str = None,
    ) -> list[AuditEntry]:
        """
        Query audit log entries.

        Args:
            limit: Maximum entries to return
            category: Filter by category
            action: Filter by action (supports prefix match)
            since: Only entries after this timestamp
            file_path: Filter by file path

        Returns:
            List of matching AuditEntry objects
        """
        if not self.log_path.exists():
            return []

        entries = []
        with open(self.log_path) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entry = AuditEntry.from_dict(data)

                    # Apply filters
                    if category and entry.category != category:
                        continue
                    if action and not entry.action.startswith(action):
                        continue
                    if since:
                        entry_time = datetime.fromisoformat(entry.timestamp)
                        if entry_time < since:
                            continue
                    if file_path and entry.file_path != file_path:
                        continue

                    entries.append(entry)
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue

        # Return most recent first
        entries.reverse()

        if limit:
            entries = entries[:limit]

        return entries

    def get_document_history(self, file_path: Path) -> list[AuditEntry]:
        """Get all audit entries for a specific document."""
        return self.get_entries(file_path=str(file_path))

    def get_recent_activity(self, hours: int = 24) -> list[AuditEntry]:
        """Get recent activity within the specified hours."""
        from datetime import timedelta
        since = datetime.now() - timedelta(hours=hours)
        return self.get_entries(since=since)

    def get_user_activity(self, user: str, limit: int = 50) -> list[AuditEntry]:
        """Get activity for a specific user."""
        entries = self.get_entries(limit=None)
        user_entries = [e for e in entries if e.user == user]
        return user_entries[:limit]

    def clear(self):
        """Clear the audit log. Use with caution!"""
        if self.log_path.exists():
            self.log_path.unlink()

    def export(self, output_path: Path, format: str = "json") -> Path:
        """
        Export audit log to file.

        Args:
            output_path: Output file path
            format: Export format - "json" or "csv"

        Returns:
            Path to exported file
        """
        entries = self.get_entries()

        if format == "json":
            with open(output_path, "w") as f:
                json.dump([e.to_dict() for e in entries], f, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, "w", newline="") as f:
                if entries:
                    writer = csv.DictWriter(f, fieldnames=entries[0].to_dict().keys())
                    writer.writeheader()
                    for entry in entries:
                        row = entry.to_dict()
                        row["metadata"] = json.dumps(row["metadata"])
                        writer.writerow(row)
        else:
            raise ValueError(f"Unknown format: {format}")

        return output_path


# === Convenience Functions ===

_loggers: dict = {}


def get_logger(project) -> AuditLogger:
    """Get or create audit logger for a project."""
    project_id = str(project.root)
    if project_id not in _loggers:
        _loggers[project_id] = AuditLogger(project)
    return _loggers[project_id]


def log_action(
    project,
    action: str,
    details: str = None,
    user: str = None,
    **metadata
) -> AuditEntry:
    """Log an action for a project."""
    logger = get_logger(project)
    return logger.log(action, details=details, user=user, **metadata)


def get_recent_entries(project, limit: int = 50) -> list[dict]:
    """Get recent audit entries as dictionaries."""
    logger = get_logger(project)
    entries = logger.get_entries(limit=limit)
    return [e.to_dict() for e in entries]


# === Predefined Actions ===

class Actions:
    """Predefined action constants for consistency."""

    # Document actions
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_VERSION_BUMPED = "document_version_bumped"
    DOCUMENT_STATUS_CHANGED = "document_status_changed"

    # Translation actions
    TRANSLATION_CREATED = "translation_created"
    TRANSLATION_UPDATED = "translation_updated"
    TRANSLATION_SYNCED = "translation_synced"
    TRANSLATION_MARKED_OUTDATED = "translation_marked_outdated"

    # Build actions
    BUILD_STARTED = "build_started"
    BUILD_COMPLETED = "build_completed"
    BUILD_FAILED = "build_failed"
    BUILD_HTML = "build_html"
    BUILD_PPTX = "build_pptx"
    BUILD_XLSX = "build_xlsx"
    BUILD_VIDEO = "build_video"

    # Quality actions
    QUALITY_CHECK_RUN = "quality_check_run"
    VALIDATION_RUN = "validation_run"
    ISSUE_FOUND = "issue_found"
    ISSUE_RESOLVED = "issue_resolved"

    # System actions
    CACHE_CLEARED = "cache_cleared"
    PROJECT_LOADED = "project_loaded"
    CONFIG_CHANGED = "config_changed"

    # Approval actions
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"


__all__ = [
    "AuditEntry",
    "AuditLogger",
    "Actions",
    "get_logger",
    "log_action",
    "get_recent_entries",
]
