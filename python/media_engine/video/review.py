"""
Video Review System

Manages review comments on video project components.
Comments can be timestamped (for specific points in video),
queued for AI processing, and tracked through resolution.

Usage:
    from media_engine.video.review import VideoReviewStore

    store = VideoReviewStore(project)
    comment = store.add_comment(
        project_id="vp_abc123",
        component_id="voiceover_xyz",
        text="The pacing here is too fast",
        author="user",
        timestamp=15.5,  # 15.5 seconds into video
    )

    # Queue for AI processing
    task_id = store.queue_for_ai(comment.id)

    # Later, resolve it
    store.resolve_comment(comment.id, "Regenerated voiceover with slower pacing")
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional
import json

from ..core.hashing import compute_short_hash

if TYPE_CHECKING:
    from ..core.project import Project
    from ..ai.queue import TaskQueue


class CommentStatus(str, Enum):
    """Status of a review comment."""
    PENDING = "pending"           # New comment, not yet processed
    QUEUED = "queued"             # Queued for AI processing
    PROCESSING = "processing"     # AI is working on it
    RESOLVED = "resolved"         # Comment addressed
    REJECTED = "rejected"         # Comment rejected (not actionable)


class CommentPriority(str, Enum):
    """Priority level for comment processing."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class VideoReviewComment:
    """
    A review comment on a video project component.

    Comments can target specific timestamps/frames in video content,
    reference specific components, and be queued for AI processing.
    """
    id: str
    project_id: str
    component_id: str
    text: str
    author: str
    timestamp: Optional[float] = None  # Time position in seconds
    frame: Optional[int] = None        # Frame number
    status: CommentStatus = CommentStatus.PENDING
    priority: CommentPriority = CommentPriority.NORMAL
    ai_task_id: Optional[str] = None   # Linked AI task
    resolution: Optional[str] = None   # What was done to resolve
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "component_id": self.component_id,
            "text": self.text,
            "author": self.author,
            "timestamp": self.timestamp,
            "frame": self.frame,
            "status": self.status.value,
            "priority": self.priority.value,
            "ai_task_id": self.ai_task_id,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoReviewComment":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            component_id=data["component_id"],
            text=data["text"],
            author=data.get("author", "unknown"),
            timestamp=data.get("timestamp"),
            frame=data.get("frame"),
            status=CommentStatus(data.get("status", "pending")),
            priority=CommentPriority(data.get("priority", "normal")),
            ai_task_id=data.get("ai_task_id"),
            resolution=data.get("resolution"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolved_by=data.get("resolved_by"),
            metadata=data.get("metadata", {}),
        )

    @property
    def is_resolved(self) -> bool:
        """Check if comment is resolved or rejected."""
        return self.status in (CommentStatus.RESOLVED, CommentStatus.REJECTED)

    @property
    def is_actionable(self) -> bool:
        """Check if comment can be acted upon."""
        return self.status in (CommentStatus.PENDING, CommentStatus.QUEUED)

    def format_timestamp(self) -> str:
        """Format timestamp as MM:SS.ms."""
        if self.timestamp is None:
            return ""
        mins = int(self.timestamp // 60)
        secs = self.timestamp % 60
        return f"{mins:02d}:{secs:05.2f}"


class VideoReviewStore:
    """
    Storage and management for video review comments.

    Comments are stored in .media-engine/video/reviews.json
    """

    def __init__(self, project: "Project"):
        self.project = project
        self._storage_path = project.root / ".media-engine" / "video" / "reviews.json"
        self._comments: dict[str, VideoReviewComment] = {}
        self._load()

    def _load(self):
        """Load comments from storage."""
        if self._storage_path.exists():
            data = json.loads(self._storage_path.read_text())
            for comment_data in data.get("comments", []):
                comment = VideoReviewComment.from_dict(comment_data)
                self._comments[comment.id] = comment

    def _save(self):
        """Save comments to storage."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "comments": [c.to_dict() for c in self._comments.values()],
            "modified_at": datetime.now().isoformat(),
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def add_comment(
        self,
        project_id: str,
        component_id: str,
        text: str,
        author: str,
        timestamp: Optional[float] = None,
        frame: Optional[int] = None,
        priority: CommentPriority = CommentPriority.NORMAL,
        metadata: Optional[dict] = None,
    ) -> VideoReviewComment:
        """
        Add a review comment on a component.

        Args:
            project_id: Video project ID
            component_id: Component ID being commented on
            text: Comment text
            author: Who made the comment
            timestamp: Optional time position in seconds
            frame: Optional frame number
            priority: Comment priority
            metadata: Additional metadata

        Returns:
            Created VideoReviewComment
        """
        comment_id = f"vc_{compute_short_hash(f'{project_id}_{component_id}_{datetime.now().isoformat()}')}"

        comment = VideoReviewComment(
            id=comment_id,
            project_id=project_id,
            component_id=component_id,
            text=text,
            author=author,
            timestamp=timestamp,
            frame=frame,
            priority=priority,
            metadata=metadata or {},
        )

        self._comments[comment_id] = comment
        self._save()
        return comment

    def get_comment(self, comment_id: str) -> Optional[VideoReviewComment]:
        """Get a comment by ID."""
        return self._comments.get(comment_id)

    def get_comments_for_project(
        self,
        project_id: str,
        status: Optional[CommentStatus] = None,
        include_resolved: bool = False,
    ) -> list[VideoReviewComment]:
        """
        Get all comments for a project.

        Args:
            project_id: Video project ID
            status: Filter by status
            include_resolved: Include resolved/rejected comments

        Returns:
            List of comments
        """
        comments = [c for c in self._comments.values() if c.project_id == project_id]

        if status:
            comments = [c for c in comments if c.status == status]
        elif not include_resolved:
            comments = [c for c in comments if not c.is_resolved]

        return sorted(comments, key=lambda c: c.created_at, reverse=True)

    def get_comments_for_component(
        self,
        component_id: str,
        include_resolved: bool = False,
    ) -> list[VideoReviewComment]:
        """Get all comments for a specific component."""
        comments = [c for c in self._comments.values() if c.component_id == component_id]

        if not include_resolved:
            comments = [c for c in comments if not c.is_resolved]

        return sorted(comments, key=lambda c: (c.timestamp or 0, c.created_at))

    def get_pending_comments(
        self,
        project_id: Optional[str] = None,
    ) -> list[VideoReviewComment]:
        """Get all pending (unprocessed) comments."""
        comments = [c for c in self._comments.values() if c.status == CommentStatus.PENDING]

        if project_id:
            comments = [c for c in comments if c.project_id == project_id]

        return sorted(comments, key=lambda c: (c.priority.value, c.created_at))

    def get_queued_comments(self) -> list[VideoReviewComment]:
        """Get all comments queued for AI processing."""
        return [c for c in self._comments.values() if c.status == CommentStatus.QUEUED]

    def update_comment(self, comment: VideoReviewComment) -> VideoReviewComment:
        """Update an existing comment."""
        self._comments[comment.id] = comment
        self._save()
        return comment

    def resolve_comment(
        self,
        comment_id: str,
        resolution: str,
        resolved_by: str = "ai",
    ) -> Optional[VideoReviewComment]:
        """
        Mark a comment as resolved.

        Args:
            comment_id: Comment ID
            resolution: Description of how it was resolved
            resolved_by: Who resolved it ("ai", "human", or username)

        Returns:
            Updated comment or None if not found
        """
        comment = self._comments.get(comment_id)
        if not comment:
            return None

        comment.status = CommentStatus.RESOLVED
        comment.resolution = resolution
        comment.resolved_at = datetime.now()
        comment.resolved_by = resolved_by

        self._save()
        return comment

    def reject_comment(
        self,
        comment_id: str,
        reason: str,
        rejected_by: str = "ai",
    ) -> Optional[VideoReviewComment]:
        """
        Mark a comment as rejected (not actionable).

        Args:
            comment_id: Comment ID
            reason: Why the comment was rejected
            rejected_by: Who rejected it

        Returns:
            Updated comment or None if not found
        """
        comment = self._comments.get(comment_id)
        if not comment:
            return None

        comment.status = CommentStatus.REJECTED
        comment.resolution = f"Rejected: {reason}"
        comment.resolved_at = datetime.now()
        comment.resolved_by = rejected_by

        self._save()
        return comment

    def queue_for_ai(
        self,
        comment_id: str,
        task_queue: Optional["TaskQueue"] = None,
    ) -> Optional[str]:
        """
        Queue a comment for AI processing.

        Args:
            comment_id: Comment ID to queue
            task_queue: Optional TaskQueue instance. If not provided,
                        will attempt to get one from project context.

        Returns:
            Task ID if successfully queued, None otherwise
        """
        comment = self._comments.get(comment_id)
        if not comment:
            return None

        if not comment.is_actionable:
            return None

        # Get task queue if not provided
        if task_queue is None:
            from ..ai.queue import TaskQueue
            task_queue = TaskQueue(self.project.root)

        # Build AI task
        from .project import VideoProjectRegistry
        registry = VideoProjectRegistry(self.project)
        video_project = registry.get(comment.project_id)

        component = video_project.components.get(comment.component_id) if video_project else None
        component_info = ""
        if component:
            component_info = f"""
Component Type: {component.type.value}
Component Path: {component.path}
Component Status: {component.status.value}
Scene ID: {component.scene_id or 'N/A'}
"""

        timestamp_info = ""
        if comment.timestamp is not None:
            timestamp_info = f"Timestamp: {comment.format_timestamp()} ({comment.timestamp:.2f}s)"
        if comment.frame is not None:
            timestamp_info += f"\nFrame: {comment.frame}"

        instructions = f"""Video Review Comment Processing

Comment ID: {comment.id}
Project ID: {comment.project_id}
Author: {comment.author}
Priority: {comment.priority.value}

{timestamp_info}

{component_info}

Comment:
{comment.text}

---

Instructions:
1. Analyze this review comment and determine what changes are needed
2. Make the necessary modifications to the component
3. After modifying, trigger cascade regeneration for downstream components
4. Use resolve_video_comment tool to mark this comment as resolved

Note: This comment will be automatically removed from pending after resolution.
"""

        # Submit to task queue
        task_id = task_queue.submit(
            operation="video_review",
            instructions=instructions,
            selections=[{"path": str(component.path)}] if component else [],
            priority=comment.priority.value,
            metadata={
                "comment_id": comment.id,
                "project_id": comment.project_id,
                "component_id": comment.component_id,
            },
        )

        # Update comment status
        comment.status = CommentStatus.QUEUED
        comment.ai_task_id = task_id
        self._save()

        return task_id

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment."""
        if comment_id in self._comments:
            del self._comments[comment_id]
            self._save()
            return True
        return False

    def delete_resolved_comments(
        self,
        project_id: Optional[str] = None,
        older_than_days: int = 30,
    ) -> int:
        """
        Delete resolved comments older than specified days.

        Args:
            project_id: Optional project ID to limit deletion to
            older_than_days: Delete comments resolved more than this many days ago

        Returns:
            Number of comments deleted
        """
        cutoff = datetime.now() - timedelta(days=older_than_days)
        to_delete = []

        for comment in self._comments.values():
            if not comment.is_resolved:
                continue
            if project_id and comment.project_id != project_id:
                continue
            if comment.resolved_at and comment.resolved_at < cutoff:
                to_delete.append(comment.id)

        for comment_id in to_delete:
            del self._comments[comment_id]

        if to_delete:
            self._save()

        return len(to_delete)

    def get_stats(self, project_id: Optional[str] = None) -> dict:
        """Get review statistics."""
        comments = list(self._comments.values())
        if project_id:
            comments = [c for c in comments if c.project_id == project_id]

        return {
            "total": len(comments),
            "pending": sum(1 for c in comments if c.status == CommentStatus.PENDING),
            "queued": sum(1 for c in comments if c.status == CommentStatus.QUEUED),
            "processing": sum(1 for c in comments if c.status == CommentStatus.PROCESSING),
            "resolved": sum(1 for c in comments if c.status == CommentStatus.RESOLVED),
            "rejected": sum(1 for c in comments if c.status == CommentStatus.REJECTED),
        }


# Import timedelta at module level for delete_resolved_comments
from datetime import timedelta
