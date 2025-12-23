"""
AI Task Queue

Persistent queue for Claude Code to process AI tasks with full tool access.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task processing status."""

    PENDING = "pending"
    CLAIMED = "claimed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class TaskSelection:
    """Content selection within a task."""

    path: str
    title: str
    content: str = ""
    content_type: str = "document"
    target_id: Optional[str] = None
    notes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AITask:
    """An AI processing task in the queue."""

    id: str
    operation: str
    instructions: str
    selections: List[TaskSelection]
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    target_language: Optional[str] = None
    created_at: str = ""
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    claimed_by: Optional[str] = None
    summary: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    files_modified: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "operation": self.operation,
            "instructions": self.instructions,
            "selections": [
                {
                    "path": s.path,
                    "title": s.title,
                    "content": s.content,
                    "content_type": s.content_type,
                    "target_id": s.target_id,
                    "notes": s.notes,
                    "metadata": s.metadata,
                }
                for s in self.selections
            ],
            "status": self.status.value,
            "priority": self.priority.value,
            "target_language": self.target_language,
            "created_at": self.created_at,
            "claimed_at": self.claimed_at,
            "completed_at": self.completed_at,
            "claimed_by": self.claimed_by,
            "summary": self.summary,
            "result": self.result,
            "files_modified": self.files_modified,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AITask":
        """Create from dictionary."""
        selections = [
            TaskSelection(
                path=s["path"],
                title=s["title"],
                content=s.get("content", ""),
                content_type=s.get("content_type", "document"),
                target_id=s.get("target_id"),
                notes=s.get("notes", []),
                metadata=s.get("metadata", {}),
            )
            for s in data.get("selections", [])
        ]

        return cls(
            id=data["id"],
            operation=data["operation"],
            instructions=data.get("instructions", ""),
            selections=selections,
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "normal")),
            target_language=data.get("target_language"),
            created_at=data.get("created_at", ""),
            claimed_at=data.get("claimed_at"),
            completed_at=data.get("completed_at"),
            claimed_by=data.get("claimed_by"),
            summary=data.get("summary"),
            result=data.get("result"),
            files_modified=data.get("files_modified", []),
            error=data.get("error"),
        )


class TaskQueue:
    """
    Persistent queue for AI tasks.

    Tasks are stored in .media-engine/ai_tasks.json and can be:
    - Submitted from the dashboard
    - Claimed and processed by Claude Code
    - Monitored for status updates
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.queue_dir = self.project_root / ".media-engine"
        self.queue_file = self.queue_dir / "ai_tasks.json"
        self._ensure_queue_file()

    def _ensure_queue_file(self):
        """Ensure queue file exists."""
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        if not self.queue_file.exists():
            self._save_tasks([])

    def _load_tasks(self) -> List[AITask]:
        """Load tasks from file."""
        try:
            with open(self.queue_file) as f:
                data = json.load(f)
            return [AITask.from_dict(t) for t in data]
        except Exception:
            return []

    def _save_tasks(self, tasks: List[AITask]):
        """Save tasks to file."""
        with open(self.queue_file, "w") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=2)

    def submit(
        self,
        operation: str,
        instructions: str,
        selections: List[Dict[str, Any]],
        priority: str = "normal",
        target_language: Optional[str] = None,
    ) -> AITask:
        """
        Submit a new task to the queue.

        Args:
            operation: The operation type (improve, translate, etc.)
            instructions: User instructions for the AI
            selections: List of content selections to process
            priority: Task priority (low, normal, high, urgent)
            target_language: Target language for translations

        Returns:
            The created task
        """
        task = AITask(
            id=str(uuid.uuid4())[:8],
            operation=operation,
            instructions=instructions,
            selections=[
                TaskSelection(
                    path=s["path"],
                    title=s["title"],
                    content=s.get("content", ""),
                    content_type=s.get("content_type", "document"),
                    target_id=s.get("target_id"),
                    notes=s.get("notes", []),
                    metadata=s.get("metadata", {}),
                )
                for s in selections
            ],
            priority=TaskPriority(priority),
            target_language=target_language,
        )

        tasks = self._load_tasks()
        tasks.append(task)
        self._save_tasks(tasks)

        return task

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
    ) -> List[AITask]:
        """
        List tasks, optionally filtered by status.

        Args:
            status: Filter by status
            limit: Maximum number of tasks to return

        Returns:
            List of tasks sorted by priority and creation time
        """
        tasks = self._load_tasks()

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by priority (urgent first) then by creation time
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 2), t.created_at))

        return tasks[:limit]

    def get_task(self, task_id: str) -> Optional[AITask]:
        """Get a specific task by ID."""
        tasks = self._load_tasks()
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    def claim(self, task_id: str, claimed_by: str = "claude_code") -> Optional[AITask]:
        """
        Claim a task for processing.

        Args:
            task_id: The task ID to claim
            claimed_by: Identifier for the claimer

        Returns:
            The claimed task, or None if not found/already claimed
        """
        tasks = self._load_tasks()

        for task in tasks:
            if task.id == task_id:
                if task.status != TaskStatus.PENDING:
                    return None
                task.status = TaskStatus.CLAIMED
                task.claimed_at = datetime.now().isoformat()
                task.claimed_by = claimed_by
                self._save_tasks(tasks)
                return task

        return None

    def start_processing(self, task_id: str) -> Optional[AITask]:
        """Mark a task as being processed."""
        tasks = self._load_tasks()

        for task in tasks:
            if task.id == task_id:
                if task.status != TaskStatus.CLAIMED:
                    return None
                task.status = TaskStatus.PROCESSING
                self._save_tasks(tasks)
                return task

        return None

    def complete(
        self,
        task_id: str,
        summary: str,
        files_modified: Optional[List[str]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> Optional[AITask]:
        """
        Mark a task as completed.

        Args:
            task_id: The task ID
            summary: Summary of what was done
            files_modified: List of modified file paths
            result: Optional detailed result data

        Returns:
            The completed task, or None if not found
        """
        tasks = self._load_tasks()

        for task in tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.summary = summary
                task.files_modified = files_modified or []
                task.result = result
                self._save_tasks(tasks)
                return task

        return None

    def fail(self, task_id: str, error: str) -> Optional[AITask]:
        """
        Mark a task as failed.

        Args:
            task_id: The task ID
            error: Error message

        Returns:
            The failed task, or None if not found
        """
        tasks = self._load_tasks()

        for task in tasks:
            if task.id == task_id:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now().isoformat()
                task.error = error
                self._save_tasks(tasks)
                return task

        return None

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Args:
            task_id: The task ID

        Returns:
            True if cancelled, False if not found or not pending
        """
        tasks = self._load_tasks()

        for task in tasks:
            if task.id == task_id:
                if task.status != TaskStatus.PENDING:
                    return False
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                self._save_tasks(tasks)
                return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        tasks = self._load_tasks()

        by_status = {}
        for status in TaskStatus:
            by_status[status.value] = len([t for t in tasks if t.status == status])

        by_operation = {}
        for task in tasks:
            by_operation[task.operation] = by_operation.get(task.operation, 0) + 1

        return {
            "total": len(tasks),
            "by_status": by_status,
            "by_operation": by_operation,
            "pending": by_status.get("pending", 0),
            "processing": by_status.get("claimed", 0) + by_status.get("processing", 0),
            "completed": by_status.get("completed", 0),
            "failed": by_status.get("failed", 0),
        }

    def delete(self, task_id: str) -> bool:
        """
        Delete a task from the queue.

        Only completed, failed, or cancelled tasks can be deleted.

        Args:
            task_id: The task ID to delete

        Returns:
            True if deleted, False if not found or not deletable
        """
        tasks = self._load_tasks()
        deletable_statuses = (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

        for i, task in enumerate(tasks):
            if task.id == task_id:
                if task.status not in deletable_statuses:
                    return False
                tasks.pop(i)
                self._save_tasks(tasks)
                return True

        return False

    def cleanup(self, max_age_days: int = 7) -> int:
        """
        Remove old completed/failed tasks.

        Args:
            max_age_days: Maximum age in days for completed tasks

        Returns:
            Number of tasks removed
        """
        from datetime import timedelta

        tasks = self._load_tasks()
        cutoff = datetime.now() - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()

        original_count = len(tasks)
        tasks = [
            t
            for t in tasks
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            or (t.completed_at and t.completed_at > cutoff_str)
        ]

        self._save_tasks(tasks)
        return original_count - len(tasks)
