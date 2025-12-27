"""
Tests for AI agent infrastructure.

Tests the core components that enable safe, observable agent operations:
- Document locking
- Session checkpoints
- Approval gates
- Structured logging
"""

import json
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDocumentLocking:
    """Tests for document locking system."""

    @pytest.fixture
    def lock_manager(self):
        """Create a lock manager with temp directory."""
        from media_engine.ai.locking import LockManager

        with tempfile.TemporaryDirectory() as tmpdir:
            yield LockManager(Path(tmpdir))

    def test_acquire_lock(self, lock_manager):
        """Test acquiring a document lock."""
        result = lock_manager.acquire("content/doc.md", "session-123")
        assert result is True

        lock = lock_manager.check_lock("content/doc.md")
        assert lock is not None
        assert lock.session_id == "session-123"
        assert lock.path == "content/doc.md"

    def test_release_lock(self, lock_manager):
        """Test releasing a document lock."""
        lock_manager.acquire("content/doc.md", "session-123")
        result = lock_manager.release("content/doc.md", "session-123")
        assert result is True

        lock = lock_manager.check_lock("content/doc.md")
        assert lock is None

    def test_cannot_acquire_locked_document(self, lock_manager):
        """Test that acquiring a locked document raises error."""
        from media_engine.core.exceptions import DocumentLockedError

        lock_manager.acquire("content/doc.md", "session-1")

        with pytest.raises(DocumentLockedError) as exc_info:
            lock_manager.acquire("content/doc.md", "session-2")

        assert "locked by session" in str(exc_info.value)

    def test_same_session_can_reacquire(self, lock_manager):
        """Test that same session can re-acquire its own lock."""
        lock_manager.acquire("content/doc.md", "session-123")
        result = lock_manager.acquire("content/doc.md", "session-123")
        assert result is True

    def test_force_acquire(self, lock_manager):
        """Test force acquiring a locked document."""
        lock_manager.acquire("content/doc.md", "session-1")
        result = lock_manager.acquire("content/doc.md", "session-2", force=True)
        assert result is True

        lock = lock_manager.check_lock("content/doc.md")
        assert lock.session_id == "session-2"

    def test_extend_lock(self, lock_manager):
        """Test extending a lock timeout."""
        lock_manager.acquire("content/doc.md", "session-123", timeout_minutes=5)
        original_lock = lock_manager.check_lock("content/doc.md")

        result = lock_manager.extend_lock("content/doc.md", "session-123", 30)
        assert result is True

        extended_lock = lock_manager.check_lock("content/doc.md")
        assert extended_lock.remaining_minutes > original_lock.remaining_minutes

    def test_list_locks(self, lock_manager):
        """Test listing all locks."""
        lock_manager.acquire("doc1.md", "session-1")
        lock_manager.acquire("doc2.md", "session-1")
        lock_manager.acquire("doc3.md", "session-2")

        all_locks = lock_manager.list_locks()
        assert len(all_locks) == 3

        session_1_locks = lock_manager.list_locks(session_id="session-1")
        assert len(session_1_locks) == 2

    def test_release_all_for_session(self, lock_manager):
        """Test releasing all locks for a session."""
        lock_manager.acquire("doc1.md", "session-1")
        lock_manager.acquire("doc2.md", "session-1")
        lock_manager.acquire("doc3.md", "session-2")

        count = lock_manager.release_all_for_session("session-1")
        assert count == 2

        remaining = lock_manager.list_locks()
        assert len(remaining) == 1
        assert remaining[0].session_id == "session-2"


class TestSessionCheckpoints:
    """Tests for session checkpoint system."""

    @pytest.fixture
    def session_manager(self):
        """Create a session manager with temp directory."""
        from media_engine.ai.sessions import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            yield SessionManager(Path(tmpdir))

    def test_create_checkpoint(self, session_manager):
        """Test creating a checkpoint."""
        session = session_manager.create()
        checkpoint = session_manager.create_checkpoint(
            session.id,
            "Before risky change",
        )

        assert checkpoint is not None
        assert checkpoint.session_id == session.id
        assert checkpoint.label == "Before risky change"

    def test_list_checkpoints(self, session_manager):
        """Test listing checkpoints for a session."""
        session = session_manager.create()
        session_manager.create_checkpoint(session.id, "Checkpoint 1")
        session_manager.create_checkpoint(session.id, "Checkpoint 2")

        checkpoints = session_manager.list_checkpoints(session.id)
        assert len(checkpoints) == 2

    def test_checkpoint_with_file_backup(self, session_manager):
        """Test checkpoint with file backup."""
        # Create a test file
        test_file = session_manager.project_root / "test.md"
        test_file.write_text("Original content")

        session = session_manager.create()
        checkpoint = session_manager.create_checkpoint(
            session.id,
            "With backup",
            files_to_backup=["test.md"],
        )

        assert "test.md" in checkpoint.files_snapshot
        assert checkpoint.files_snapshot["test.md"]  # Has hash

    def test_rollback_to_checkpoint(self, session_manager):
        """Test rolling back to a checkpoint."""
        # Create a test file
        test_file = session_manager.project_root / "test.md"
        test_file.write_text("Original content")

        session = session_manager.create()
        session_manager.add_progress(session.id, "Step 1", completed=True)
        session_manager.add_progress(session.id, "Step 2", completed=True)

        checkpoint = session_manager.create_checkpoint(
            session.id,
            "Before changes",
            files_to_backup=["test.md"],
        )

        # Make changes
        session_manager.add_progress(session.id, "Step 3", completed=True)
        test_file.write_text("Modified content")

        # Rollback
        result = session_manager.rollback_to_checkpoint(session.id, checkpoint.id)

        assert result["success"] is True
        assert "test.md" in result["files_restored"]
        assert test_file.read_text() == "Original content"

    def test_delete_checkpoint(self, session_manager):
        """Test deleting a checkpoint."""
        session = session_manager.create()
        checkpoint = session_manager.create_checkpoint(session.id, "Test")

        result = session_manager.delete_checkpoint(session.id, checkpoint.id)
        assert result is True

        checkpoints = session_manager.list_checkpoints(session.id)
        assert len(checkpoints) == 0


class TestApprovalGates:
    """Tests for approval gate system."""

    @pytest.fixture
    def approval_manager(self):
        """Create an approval manager with temp directory."""
        from media_engine.ai.approval import ApprovalManager

        with tempfile.TemporaryDirectory() as tmpdir:
            yield ApprovalManager(Path(tmpdir))

    def test_request_approval(self, approval_manager):
        """Test creating an approval request."""
        request = approval_manager.request_approval(
            action="delete",
            description="Delete 5 documents",
            context={"documents": ["doc1.md", "doc2.md"]},
        )

        assert request.id is not None
        assert request.action == "delete"
        assert request.is_pending

    def test_approve_request(self, approval_manager):
        """Test approving a request."""
        request = approval_manager.request_approval("delete", "Delete docs")
        response = approval_manager.approve(request.id, responder="admin")

        assert response.approved is True
        assert response.responder == "admin"

        # Verify request is updated
        updated = approval_manager.get_request(request.id)
        assert updated.is_approved

    def test_reject_request(self, approval_manager):
        """Test rejecting a request."""
        request = approval_manager.request_approval("delete", "Delete docs")
        response = approval_manager.reject(request.id, notes="Not authorized")

        assert response.approved is False

        updated = approval_manager.get_request(request.id)
        assert updated.is_rejected

    def test_list_pending(self, approval_manager):
        """Test listing pending requests."""
        approval_manager.request_approval("action1", "Request 1")
        req2 = approval_manager.request_approval("action2", "Request 2")
        approval_manager.request_approval("action3", "Request 3")

        # Approve one
        approval_manager.approve(req2.id)

        pending = approval_manager.list_pending()
        assert len(pending) == 2

    def test_cancel_request(self, approval_manager):
        """Test cancelling a pending request."""
        request = approval_manager.request_approval("delete", "Delete docs")
        result = approval_manager.cancel_request(request.id)
        assert result is True

        updated = approval_manager.get_request(request.id)
        assert updated.is_expired

    def test_get_summary(self, approval_manager):
        """Test getting approval summary."""
        req1 = approval_manager.request_approval("action1", "Request 1")
        req2 = approval_manager.request_approval("action2", "Request 2")
        req3 = approval_manager.request_approval("action3", "Request 3")

        approval_manager.approve(req1.id)
        approval_manager.reject(req2.id)

        summary = approval_manager.get_summary()
        assert summary["approved"] == 1
        assert summary["rejected"] == 1
        assert summary["pending"] == 1
        assert summary["total"] == 3


class TestStructuredLogging:
    """Tests for structured logging system."""

    def test_get_logger(self):
        """Test getting a logger."""
        from media_engine.core.logging import get_logger

        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    def test_log_context(self):
        """Test log context manager."""
        from media_engine.core.logging import LogContext, get_context

        with LogContext(session_id="abc", agent="test"):
            ctx = get_context()
            assert ctx["session_id"] == "abc"
            assert ctx["agent"] == "test"

        # Context should be restored
        ctx = get_context()
        assert "session_id" not in ctx

    def test_log_entry_to_dict(self):
        """Test log entry serialization."""
        from media_engine.core.logging import LogEntry

        entry = LogEntry(
            timestamp="2024-01-01T00:00:00",
            level="INFO",
            logger="test",
            message="Test message",
            context={"key": "value"},
            operation="test_op",
            duration_ms=123.4,
        )

        data = entry.to_dict()
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["context"] == {"key": "value"}
        assert data["duration_ms"] == 123.4

    def test_log_operation_decorator(self):
        """Test log_operation decorator."""
        from media_engine.core.logging import log_operation, configure_logging

        configure_logging(level="DEBUG")

        @log_operation("test")
        def my_function(x: int) -> int:
            return x * 2

        result = my_function(5)
        assert result == 10


class TestExceptionHierarchy:
    """Tests for structured exception hierarchy."""

    def test_media_engine_error_to_dict(self):
        """Test exception serialization."""
        from media_engine.core.exceptions import MediaEngineError

        error = MediaEngineError(
            message="Test error",
            error_code="TEST_ERROR",
            recoverable=True,
            suggestions=["Try again"],
            context={"key": "value"},
        )

        data = error.to_dict()
        assert data["error"] == "TEST_ERROR"
        assert data["message"] == "Test error"
        assert data["recoverable"] is True
        assert data["suggestions"] == ["Try again"]

    def test_document_locked_error(self):
        """Test document locked error."""
        from media_engine.core.exceptions import DocumentLockedError

        error = DocumentLockedError(
            message="Document is locked",
            path="content/doc.md",
            locked_by="session-123",
            lock_expires="2024-01-01T00:00:00",
        )

        assert error.error_code == "DOCUMENT_LOCKED"
        assert error.recoverable is True
        assert error.context["path"] == "content/doc.md"
        assert error.context["locked_by"] == "session-123"

    def test_approval_required_error(self):
        """Test approval required error."""
        from media_engine.core.exceptions import ApprovalRequiredError

        error = ApprovalRequiredError(
            message="Approval required for delete",
            context={"action": "delete", "documents": 5},
        )

        assert error.error_code == "APPROVAL_REQUIRED"
        assert error.recoverable is True

    def test_error_from_dict(self):
        """Test reconstructing error from dict."""
        from media_engine.core.exceptions import MediaEngineError, error_from_dict

        original = MediaEngineError(
            message="Test",
            error_code="TEST",
            recoverable=True,
        )

        data = original.to_dict()
        reconstructed = error_from_dict(data)

        assert reconstructed.message == original.message
        assert reconstructed.error_code == original.error_code

    def test_is_recoverable(self):
        """Test recoverable check utility."""
        from media_engine.core.exceptions import (
            DocumentLockedError,
            ConfigurationError,
            is_recoverable,
        )

        locked_error = DocumentLockedError(message="Document locked", locked_by="x")
        assert is_recoverable(locked_error) is True

        config_error = ConfigurationError(message="Bad config")
        assert is_recoverable(config_error) is False
