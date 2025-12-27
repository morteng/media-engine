"""
Document Locking for Concurrent Agent Safety

Provides file-based locking to prevent multiple agents from modifying
the same documents simultaneously. Locks are stored in .media-engine/locks/
and automatically expire after a configurable timeout.

Usage:
    from media_engine.ai.locking import LockManager

    manager = LockManager(project_root)

    # Acquire lock before modifying
    if manager.acquire("content/chapter1.md", session_id="abc123"):
        try:
            # Modify document...
            pass
        finally:
            manager.release("content/chapter1.md", session_id="abc123")

    # Check what's locked
    locks = manager.list_locks()
    for lock in locks:
        print(f"{lock.path} locked by {lock.session_id}")
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..core.exceptions import DocumentLockedError


@dataclass
class DocumentLock:
    """Represents a lock on a document."""

    path: str
    session_id: str
    acquired_at: str
    expires_at: str
    agent_id: Optional[str] = None
    reason: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if the lock has expired."""
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() >= expires

    @property
    def remaining_minutes(self) -> int:
        """Minutes until lock expires."""
        expires = datetime.fromisoformat(self.expires_at)
        remaining = expires - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            "is_expired": self.is_expired,
            "remaining_minutes": self.remaining_minutes,
        }


class LockManager:
    """
    Manages document locks for concurrent agent safety.

    Locks are stored as individual JSON files in .media-engine/locks/
    to allow atomic operations and easy cleanup.
    """

    DEFAULT_TIMEOUT_MINUTES = 30

    def __init__(self, project_root: Path):
        """
        Initialize lock manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.locks_dir = self.project_root / ".media-engine" / "locks"
        self.locks_dir.mkdir(parents=True, exist_ok=True)

    def _lock_file_for(self, document_path: str) -> Path:
        """Get the lock file path for a document."""
        # Normalize path and create safe filename
        safe_name = document_path.replace("/", "__").replace("\\", "__")
        return self.locks_dir / f"{safe_name}.lock"

    def _read_lock(self, lock_file: Path) -> Optional[DocumentLock]:
        """Read lock from file, return None if doesn't exist or is corrupted."""
        if not lock_file.exists():
            return None
        try:
            with open(lock_file) as f:
                data = json.load(f)
            return DocumentLock(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            # Corrupted lock file, remove it
            lock_file.unlink(missing_ok=True)
            return None

    def _write_lock(self, lock_file: Path, lock: DocumentLock) -> None:
        """Write lock to file atomically."""
        temp_file = lock_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(asdict(lock), f, indent=2)
        temp_file.replace(lock_file)  # Atomic on POSIX

    def acquire(
        self,
        document_path: str,
        session_id: str,
        timeout_minutes: int = None,
        agent_id: str = None,
        reason: str = None,
        force: bool = False,
    ) -> bool:
        """
        Acquire a lock on a document.

        Args:
            document_path: Path to the document (relative to project root)
            session_id: ID of the session acquiring the lock
            timeout_minutes: Lock timeout (default: 30 minutes)
            agent_id: Optional identifier for the agent
            reason: Optional reason for locking
            force: Force acquire even if locked by another session

        Returns:
            True if lock acquired, False if already locked by another session

        Raises:
            DocumentLockedError: If document is locked and force=False
        """
        timeout = timeout_minutes or self.DEFAULT_TIMEOUT_MINUTES
        lock_file = self._lock_file_for(document_path)

        # Check existing lock
        existing = self._read_lock(lock_file)
        if existing and not existing.is_expired:
            if existing.session_id == session_id:
                # Same session, extend the lock
                pass
            elif not force:
                raise DocumentLockedError(
                    message=f"Document '{document_path}' is locked by session '{existing.session_id}'",
                    path=document_path,
                    locked_by=existing.session_id,
                    lock_expires=existing.expires_at,
                )

        # Create new lock
        now = datetime.now()
        lock = DocumentLock(
            path=document_path,
            session_id=session_id,
            acquired_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=timeout)).isoformat(),
            agent_id=agent_id,
            reason=reason,
        )

        self._write_lock(lock_file, lock)
        return True

    def release(self, document_path: str, session_id: str) -> bool:
        """
        Release a lock on a document.

        Args:
            document_path: Path to the document
            session_id: ID of the session releasing the lock

        Returns:
            True if lock was released, False if not owned by this session
        """
        lock_file = self._lock_file_for(document_path)
        existing = self._read_lock(lock_file)

        if not existing:
            return True  # No lock to release

        if existing.session_id != session_id:
            return False  # Can't release someone else's lock

        lock_file.unlink(missing_ok=True)
        return True

    def force_release(self, document_path: str) -> bool:
        """
        Force release a lock (admin operation).

        Args:
            document_path: Path to the document

        Returns:
            True if lock was released
        """
        lock_file = self._lock_file_for(document_path)
        lock_file.unlink(missing_ok=True)
        return True

    def check_lock(self, document_path: str) -> Optional[DocumentLock]:
        """
        Check if a document is locked.

        Args:
            document_path: Path to the document

        Returns:
            DocumentLock if locked and not expired, None otherwise
        """
        lock_file = self._lock_file_for(document_path)
        lock = self._read_lock(lock_file)

        if lock and lock.is_expired:
            # Clean up expired lock
            lock_file.unlink(missing_ok=True)
            return None

        return lock

    def check_locks(self, document_paths: list[str]) -> dict[str, Optional[DocumentLock]]:
        """
        Check locks on multiple documents.

        Args:
            document_paths: List of document paths to check

        Returns:
            Dict mapping path to lock (or None if not locked)
        """
        return {path: self.check_lock(path) for path in document_paths}

    def is_locked(self, document_path: str) -> bool:
        """Check if a document is currently locked."""
        return self.check_lock(document_path) is not None

    def is_locked_by(self, document_path: str, session_id: str) -> bool:
        """Check if a document is locked by a specific session."""
        lock = self.check_lock(document_path)
        return lock is not None and lock.session_id == session_id

    def list_locks(self, session_id: str = None) -> list[DocumentLock]:
        """
        List all active locks.

        Args:
            session_id: Optional filter by session

        Returns:
            List of active (non-expired) locks
        """
        locks = []
        for lock_file in self.locks_dir.glob("*.lock"):
            lock = self._read_lock(lock_file)
            if lock and not lock.is_expired:
                if session_id is None or lock.session_id == session_id:
                    locks.append(lock)
            elif lock and lock.is_expired:
                # Clean up expired locks
                lock_file.unlink(missing_ok=True)

        return locks

    def list_expired_locks(self) -> list[DocumentLock]:
        """List all expired locks (for cleanup reporting)."""
        locks = []
        for lock_file in self.locks_dir.glob("*.lock"):
            lock = self._read_lock(lock_file)
            if lock and lock.is_expired:
                locks.append(lock)
        return locks

    def cleanup_expired(self) -> int:
        """
        Remove all expired locks.

        Returns:
            Number of locks cleaned up
        """
        count = 0
        for lock_file in self.locks_dir.glob("*.lock"):
            lock = self._read_lock(lock_file)
            if lock and lock.is_expired:
                lock_file.unlink(missing_ok=True)
                count += 1
        return count

    def release_all_for_session(self, session_id: str) -> int:
        """
        Release all locks held by a session.

        Useful when a session completes or is abandoned.

        Args:
            session_id: Session ID to release locks for

        Returns:
            Number of locks released
        """
        count = 0
        for lock_file in self.locks_dir.glob("*.lock"):
            lock = self._read_lock(lock_file)
            if lock and lock.session_id == session_id:
                lock_file.unlink(missing_ok=True)
                count += 1
        return count

    def extend_lock(
        self,
        document_path: str,
        session_id: str,
        additional_minutes: int = None,
    ) -> bool:
        """
        Extend the timeout on an existing lock.

        Args:
            document_path: Path to the document
            session_id: Session ID that owns the lock
            additional_minutes: Minutes to add (default: original timeout)

        Returns:
            True if extended, False if not owned by this session
        """
        lock_file = self._lock_file_for(document_path)
        existing = self._read_lock(lock_file)

        if not existing or existing.session_id != session_id:
            return False

        additional = additional_minutes or self.DEFAULT_TIMEOUT_MINUTES
        new_expires = datetime.now() + timedelta(minutes=additional)

        lock = DocumentLock(
            path=existing.path,
            session_id=existing.session_id,
            acquired_at=existing.acquired_at,
            expires_at=new_expires.isoformat(),
            agent_id=existing.agent_id,
            reason=existing.reason,
        )

        self._write_lock(lock_file, lock)
        return True

    def get_lock_summary(self) -> dict:
        """
        Get summary of all locks.

        Returns:
            Summary with counts and details
        """
        all_locks = []
        expired_count = 0

        for lock_file in self.locks_dir.glob("*.lock"):
            lock = self._read_lock(lock_file)
            if lock:
                if lock.is_expired:
                    expired_count += 1
                else:
                    all_locks.append(lock)

        # Group by session
        by_session: dict[str, list[DocumentLock]] = {}
        for lock in all_locks:
            if lock.session_id not in by_session:
                by_session[lock.session_id] = []
            by_session[lock.session_id].append(lock)

        return {
            "total_active": len(all_locks),
            "total_expired": expired_count,
            "sessions_with_locks": len(by_session),
            "by_session": {
                sid: [l.to_dict() for l in locks] for sid, locks in by_session.items()
            },
            "all_locks": [l.to_dict() for l in all_locks],
        }


# Convenience function for getting a lock manager
_managers: dict[str, LockManager] = {}


def get_lock_manager(project_root: Path) -> LockManager:
    """
    Get or create a LockManager for a project.

    Uses a cache to avoid creating multiple managers for the same project.
    """
    key = str(project_root.resolve())
    if key not in _managers:
        _managers[key] = LockManager(project_root)
    return _managers[key]
