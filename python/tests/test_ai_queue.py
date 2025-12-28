"""
Tests for AI Task Queue system.

Tests the complete queue lifecycle:
- Task submission
- Claiming and processing
- Completion and failure handling
- Priority ordering
- Cleanup operations
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from media_engine.ai.queue import (
    AITask,
    TaskPriority,
    TaskQueue,
    TaskSelection,
    TaskStatus,
)


class TestTaskQueue:
    """Tests for TaskQueue class."""

    @pytest.fixture
    def queue(self):
        """Create a queue with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield TaskQueue(Path(tmpdir))

    def test_submit_task(self, queue):
        """Test submitting a new task."""
        task = queue.submit(
            operation="improve",
            instructions="Make it better",
            selections=[
                {
                    "path": "content/en/doc.md",
                    "title": "Test Doc",
                    "content": "Some content",
                }
            ],
            priority="high",
        )

        assert task.id is not None
        assert task.operation == "improve"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert len(task.selections) == 1

    def test_list_tasks(self, queue):
        """Test listing tasks."""
        queue.submit("improve", "Task 1", [{"path": "a.md", "title": "A"}])
        queue.submit("translate", "Task 2", [{"path": "b.md", "title": "B"}])
        queue.submit("analyze", "Task 3", [{"path": "c.md", "title": "C"}])

        tasks = queue.list_tasks()
        assert len(tasks) == 3

    def test_list_tasks_by_status(self, queue):
        """Test filtering tasks by status."""
        t1 = queue.submit("improve", "Task 1", [{"path": "a.md", "title": "A"}])
        queue.submit("improve", "Task 2", [{"path": "b.md", "title": "B"}])

        # Claim one
        queue.claim(t1.id)

        pending = queue.list_tasks(status=TaskStatus.PENDING)
        assert len(pending) == 1

        claimed = queue.list_tasks(status=TaskStatus.CLAIMED)
        assert len(claimed) == 1

    def test_get_task(self, queue):
        """Test getting a specific task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])

        retrieved = queue.get_task(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id
        assert retrieved.operation == "improve"

    def test_get_task_not_found(self, queue):
        """Test getting non-existent task."""
        result = queue.get_task("nonexistent")
        assert result is None

    def test_claim_task(self, queue):
        """Test claiming a task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])

        claimed = queue.claim(task.id, claimed_by="test_agent")

        assert claimed is not None
        assert claimed.status == TaskStatus.CLAIMED
        assert claimed.claimed_by == "test_agent"
        assert claimed.claimed_at is not None

    def test_claim_already_claimed(self, queue):
        """Test claiming an already claimed task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)

        # Try to claim again
        result = queue.claim(task.id, claimed_by="another_agent")
        assert result is None

    def test_start_processing(self, queue):
        """Test starting to process a claimed task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)

        processing = queue.start_processing(task.id)

        assert processing is not None
        assert processing.status == TaskStatus.PROCESSING

    def test_complete_task(self, queue):
        """Test completing a task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)
        queue.start_processing(task.id)

        completed = queue.complete(
            task.id,
            summary="Made improvements",
            files_modified=["a.md"],
            result={"changes": 5},
        )

        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED
        assert completed.summary == "Made improvements"
        assert completed.files_modified == ["a.md"]
        assert completed.completed_at is not None

    def test_fail_task(self, queue):
        """Test marking a task as failed."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)

        failed = queue.fail(task.id, error="Something went wrong")

        assert failed is not None
        assert failed.status == TaskStatus.FAILED
        assert failed.error == "Something went wrong"

    def test_cancel_task(self, queue):
        """Test cancelling a pending task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])

        result = queue.cancel(task.id)
        assert result is True

        cancelled = queue.get_task(task.id)
        assert cancelled.status == TaskStatus.CANCELLED

    def test_cancel_non_pending_fails(self, queue):
        """Test that cancelling a non-pending task fails."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)

        result = queue.cancel(task.id)
        assert result is False

    def test_delete_task(self, queue):
        """Test deleting a completed task."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)
        queue.complete(task.id, "Done")

        result = queue.delete(task.id)
        assert result is True

        deleted = queue.get_task(task.id)
        assert deleted is None

    def test_delete_pending_fails(self, queue):
        """Test that deleting a pending task fails."""
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])

        result = queue.delete(task.id)
        assert result is False

    def test_priority_ordering(self, queue):
        """Test that tasks are ordered by priority."""
        queue.submit("improve", "Low", [{"path": "a.md", "title": "A"}], priority="low")
        queue.submit("improve", "High", [{"path": "b.md", "title": "B"}], priority="high")
        queue.submit("improve", "Urgent", [{"path": "c.md", "title": "C"}], priority="urgent")
        queue.submit("improve", "Normal", [{"path": "d.md", "title": "D"}], priority="normal")

        tasks = queue.list_tasks()
        priorities = [t.priority for t in tasks]

        assert priorities[0] == TaskPriority.URGENT
        assert priorities[1] == TaskPriority.HIGH
        assert priorities[2] == TaskPriority.NORMAL
        assert priorities[3] == TaskPriority.LOW

    def test_get_stats(self, queue):
        """Test getting queue statistics."""
        t1 = queue.submit("improve", "Task 1", [{"path": "a.md", "title": "A"}])
        t2 = queue.submit("translate", "Task 2", [{"path": "b.md", "title": "B"}])
        queue.submit("analyze", "Task 3", [{"path": "c.md", "title": "C"}])

        queue.claim(t1.id)
        queue.complete(t1.id, "Done")
        queue.claim(t2.id)
        queue.fail(t2.id, "Error")

        stats = queue.get_stats()

        assert stats["total"] == 3
        assert stats["by_status"]["completed"] == 1
        assert stats["by_status"]["failed"] == 1
        assert stats["by_status"]["pending"] == 1
        assert stats["by_operation"]["improve"] == 1
        assert stats["by_operation"]["translate"] == 1
        assert stats["by_operation"]["analyze"] == 1

    def test_cleanup(self, queue):
        """Test cleaning up old tasks."""
        # Submit and complete a task
        task = queue.submit("improve", "Test", [{"path": "a.md", "title": "A"}])
        queue.claim(task.id)
        queue.complete(task.id, "Done")

        # Cleanup with 0 days should remove it
        removed = queue.cleanup(max_age_days=0)
        assert removed == 1

        tasks = queue.list_tasks()
        assert len(tasks) == 0

    def test_task_with_notes(self, queue):
        """Test task with attached notes."""
        task = queue.submit(
            operation="improve",
            instructions="Follow the notes",
            selections=[
                {
                    "path": "doc.md",
                    "title": "Doc",
                    "content": "Content",
                    "notes": [
                        {"text": "Fix this part", "priority": "high"},
                        {"text": "Also check spelling", "priority": "low"},
                    ],
                }
            ],
        )

        retrieved = queue.get_task(task.id)
        assert len(retrieved.selections[0].notes) == 2

    def test_task_with_target_language(self, queue):
        """Test translation task with target language."""
        task = queue.submit(
            operation="translate",
            instructions="Translate to Norwegian",
            selections=[{"path": "doc.md", "title": "Doc"}],
            target_language="no",
        )

        assert task.target_language == "no"


class TestAITask:
    """Tests for AITask dataclass."""

    def test_to_dict(self):
        """Test serialization to dict."""
        task = AITask(
            id="test123",
            operation="improve",
            instructions="Make it better",
            selections=[
                TaskSelection(
                    path="doc.md",
                    title="Test Doc",
                    content="Content",
                )
            ],
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
        )

        data = task.to_dict()

        assert data["id"] == "test123"
        assert data["operation"] == "improve"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert len(data["selections"]) == 1

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "test123",
            "operation": "translate",
            "instructions": "Translate",
            "selections": [
                {
                    "path": "doc.md",
                    "title": "Doc",
                    "content": "Content",
                }
            ],
            "status": "completed",
            "priority": "urgent",
            "target_language": "no",
            "summary": "Done",
            "files_modified": ["doc.md"],
        }

        task = AITask.from_dict(data)

        assert task.id == "test123"
        assert task.operation == "translate"
        assert task.status == TaskStatus.COMPLETED
        assert task.priority == TaskPriority.URGENT
        assert task.target_language == "no"
        assert task.summary == "Done"

    def test_auto_timestamp(self):
        """Test that created_at is auto-set."""
        task = AITask(
            id="test",
            operation="test",
            instructions="",
            selections=[],
        )

        assert task.created_at != ""
        # Should be a valid ISO timestamp
        datetime.fromisoformat(task.created_at)


class TestTaskSelection:
    """Tests for TaskSelection dataclass."""

    def test_defaults(self):
        """Test default values."""
        selection = TaskSelection(
            path="doc.md",
            title="Doc",
        )

        assert selection.content == ""
        assert selection.content_type == "document"
        assert selection.target_id is None
        assert selection.notes == []
        assert selection.metadata == {}

    def test_with_all_fields(self):
        """Test with all fields populated."""
        selection = TaskSelection(
            path="doc.md",
            title="Doc",
            content="Full content here",
            content_type="scene",
            target_id="scene-1",
            notes=[{"text": "Note 1"}],
            metadata={"line": 10},
        )

        assert selection.content == "Full content here"
        assert selection.content_type == "scene"
        assert selection.target_id == "scene-1"
        assert len(selection.notes) == 1


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_all_statuses(self):
        """Test all status values exist."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.CLAIMED.value == "claimed"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTaskPriority:
    """Tests for TaskPriority enum."""

    def test_all_priorities(self):
        """Test all priority values exist."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.NORMAL.value == "normal"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"
