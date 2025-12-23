"""
Tests for the audit logging module.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from media_engine.audit import (
    Actions,
    AuditEntry,
    AuditLogger,
    get_logger,
    get_recent_entries,
    log_action,
)


class TestAuditEntry:
    """Test AuditEntry dataclass."""

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = AuditEntry(
            timestamp="2024-01-15T10:30:00",
            action="document_updated",
            category="document",
            user="testuser",
            details="Updated introduction",
            file_path="/docs/intro.md",
            metadata={"version": "1.0.1"},
        )
        result = entry.to_dict()

        assert result["timestamp"] == "2024-01-15T10:30:00"
        assert result["action"] == "document_updated"
        assert result["category"] == "document"
        assert result["user"] == "testuser"
        assert result["details"] == "Updated introduction"
        assert result["file_path"] == "/docs/intro.md"
        assert result["metadata"] == {"version": "1.0.1"}

    def test_to_json(self):
        """Test converting entry to JSON string."""
        entry = AuditEntry(
            timestamp="2024-01-15T10:30:00",
            action="test_action",
            category="test",
            user="user",
            details=None,
            file_path=None,
            metadata={},
        )
        result = entry.to_json()
        parsed = json.loads(result)

        assert parsed["action"] == "test_action"
        assert parsed["category"] == "test"

    def test_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "timestamp": "2024-01-15T10:30:00",
            "action": "build_started",
            "category": "build",
            "user": "builder",
            "details": "Starting HTML build",
            "file_path": None,
            "metadata": {"format": "html"},
        }
        entry = AuditEntry.from_dict(data)

        assert entry.action == "build_started"
        assert entry.category == "build"
        assert entry.metadata == {"format": "html"}


class TestAuditLogger:
    """Test AuditLogger class."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project for testing."""
        project = MagicMock()
        project.root = temp_dir
        return project

    @pytest.fixture
    def logger(self, mock_project):
        """Create an audit logger instance."""
        return AuditLogger(mock_project)

    def test_init(self, logger, temp_dir):
        """Test logger initialization."""
        assert logger.log_dir == temp_dir / ".media-engine"
        assert logger.log_path == temp_dir / ".media-engine" / "audit.log"

    def test_log_creates_directory(self, logger, temp_dir):
        """Test that logging creates the log directory."""
        logger.log("test_action")
        assert (temp_dir / ".media-engine").exists()

    def test_log_creates_entry(self, logger):
        """Test that logging creates an entry."""
        entry = logger.log(
            action="document_created",
            details="Created new document",
            user="author",
        )

        assert entry.action == "document_created"
        assert entry.details == "Created new document"
        assert entry.user == "author"

    def test_log_writes_to_file(self, logger, temp_dir):
        """Test that entries are written to log file."""
        logger.log("first_action")
        logger.log("second_action")

        log_path = temp_dir / ".media-engine" / "audit.log"
        assert log_path.exists()

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_infer_category_document(self, logger):
        """Test category inference for document actions."""
        assert logger._infer_category("document_updated") == "document"
        assert logger._infer_category("content_modified") == "document"
        assert logger._infer_category("chapter_deleted") == "document"

    def test_infer_category_build(self, logger):
        """Test category inference for build actions."""
        assert logger._infer_category("build_started") == "build"
        assert logger._infer_category("generate_html") == "build"
        assert logger._infer_category("compile_video") == "build"

    def test_infer_category_translation(self, logger):
        """Test category inference for translation actions."""
        assert logger._infer_category("translation_updated") == "translation"
        assert logger._infer_category("sync_translations") == "translation"

    def test_infer_category_quality(self, logger):
        """Test category inference for quality actions."""
        assert logger._infer_category("quality_check_run") == "quality"
        assert logger._infer_category("validation_failed") == "quality"

    def test_infer_category_system(self, logger):
        """Test category inference for system actions."""
        assert logger._infer_category("system_startup") == "system"
        assert logger._infer_category("cache_cleared") == "system"
        assert logger._infer_category("config_changed") == "system"

    def test_get_entries_empty(self, logger):
        """Test getting entries when log is empty."""
        entries = logger.get_entries()
        assert entries == []

    def test_get_entries_returns_all(self, logger):
        """Test getting all entries."""
        logger.log("action_1")
        logger.log("action_2")
        logger.log("action_3")

        entries = logger.get_entries()
        assert len(entries) == 3

    def test_get_entries_with_limit(self, logger):
        """Test getting entries with limit."""
        for i in range(10):
            logger.log(f"action_{i}")

        entries = logger.get_entries(limit=5)
        assert len(entries) == 5

    def test_get_entries_filter_by_category(self, logger):
        """Test filtering entries by category."""
        logger.log("document_created", category="document")
        logger.log("build_started", category="build")
        logger.log("document_updated", category="document")

        entries = logger.get_entries(category="document")
        assert len(entries) == 2
        assert all(e.category == "document" for e in entries)

    def test_get_entries_filter_by_action(self, logger):
        """Test filtering entries by action prefix."""
        logger.log("document_created")
        logger.log("document_updated")
        logger.log("build_started")

        entries = logger.get_entries(action="document")
        assert len(entries) == 2

    def test_get_entries_filter_by_since(self, logger, temp_dir):
        """Test filtering entries by time."""
        # Create old entry manually
        old_time = (datetime.now() - timedelta(days=2)).isoformat()
        log_path = temp_dir / ".media-engine" / "audit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        old_entry = {
            "timestamp": old_time,
            "action": "old_action",
            "category": "test",
            "user": None,
            "details": None,
            "file_path": None,
            "metadata": {},
        }
        log_path.write_text(json.dumps(old_entry) + "\n")

        # Create new entry
        logger.log("new_action")

        # Filter by since
        since = datetime.now() - timedelta(days=1)
        entries = logger.get_entries(since=since)
        assert len(entries) == 1
        assert entries[0].action == "new_action"

    def test_get_document_history(self, logger):
        """Test getting history for a specific document."""
        logger.log("created", file_path=Path("/docs/intro.md"))
        logger.log("updated", file_path=Path("/docs/intro.md"))
        logger.log("created", file_path=Path("/docs/chapter1.md"))

        history = logger.get_document_history(Path("/docs/intro.md"))
        assert len(history) == 2

    def test_get_recent_activity(self, logger):
        """Test getting recent activity."""
        logger.log("recent_action")

        activity = logger.get_recent_activity(hours=1)
        assert len(activity) == 1

    def test_get_user_activity(self, logger):
        """Test getting activity for a specific user."""
        logger.log("action_1", user="alice")
        logger.log("action_2", user="bob")
        logger.log("action_3", user="alice")

        activity = logger.get_user_activity("alice")
        assert len(activity) == 2

    def test_clear(self, logger, temp_dir):
        """Test clearing the audit log."""
        logger.log("test_action")
        log_path = temp_dir / ".media-engine" / "audit.log"
        assert log_path.exists()

        logger.clear()
        assert not log_path.exists()

    def test_export_json(self, logger, temp_dir):
        """Test exporting to JSON."""
        logger.log("action_1")
        logger.log("action_2")

        output_path = temp_dir / "audit_export.json"
        logger.export(output_path, format="json")

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert len(data) == 2

    def test_export_csv(self, logger, temp_dir):
        """Test exporting to CSV."""
        logger.log("action_1", details="First action")
        logger.log("action_2", details="Second action")

        output_path = temp_dir / "audit_export.csv"
        logger.export(output_path, format="csv")

        assert output_path.exists()
        content = output_path.read_text()
        assert "action_1" in content
        assert "action_2" in content

    def test_export_invalid_format(self, logger, temp_dir):
        """Test that invalid format raises error."""
        with pytest.raises(ValueError, match="Unknown format"):
            logger.export(temp_dir / "export.txt", format="txt")


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        project = MagicMock()
        project.root = temp_dir
        return project

    def test_get_logger_returns_logger(self, mock_project):
        """Test that get_logger returns an AuditLogger."""
        logger = get_logger(mock_project)
        assert isinstance(logger, AuditLogger)

    def test_get_logger_caches_instance(self, mock_project):
        """Test that get_logger caches logger instances."""
        logger1 = get_logger(mock_project)
        logger2 = get_logger(mock_project)
        assert logger1 is logger2

    def test_log_action(self, mock_project):
        """Test the log_action convenience function."""
        entry = log_action(
            mock_project,
            "test_action",
            details="Test details",
            user="tester",
        )

        assert entry.action == "test_action"
        assert entry.details == "Test details"
        assert entry.user == "tester"

    def test_get_recent_entries(self, mock_project):
        """Test the get_recent_entries convenience function."""
        log_action(mock_project, "action_1")
        log_action(mock_project, "action_2")

        entries = get_recent_entries(mock_project, limit=10)
        assert len(entries) == 2
        assert all(isinstance(e, dict) for e in entries)


class TestActions:
    """Test predefined action constants."""

    def test_document_actions(self):
        """Test document action constants."""
        assert Actions.DOCUMENT_CREATED == "document_created"
        assert Actions.DOCUMENT_UPDATED == "document_updated"
        assert Actions.DOCUMENT_DELETED == "document_deleted"

    def test_translation_actions(self):
        """Test translation action constants."""
        assert Actions.TRANSLATION_CREATED == "translation_created"
        assert Actions.TRANSLATION_UPDATED == "translation_updated"

    def test_build_actions(self):
        """Test build action constants."""
        assert Actions.BUILD_STARTED == "build_started"
        assert Actions.BUILD_COMPLETED == "build_completed"
        assert Actions.BUILD_FAILED == "build_failed"

    def test_quality_actions(self):
        """Test quality action constants."""
        assert Actions.QUALITY_CHECK_RUN == "quality_check_run"
        assert Actions.VALIDATION_RUN == "validation_run"

    def test_approval_actions(self):
        """Test approval action constants."""
        assert Actions.APPROVAL_REQUESTED == "approval_requested"
        assert Actions.APPROVAL_GRANTED == "approval_granted"
        assert Actions.APPROVAL_REJECTED == "approval_rejected"
