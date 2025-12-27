"""
Approval Gates for Human-in-the-Loop Workflows

Provides blocking approval mechanism for critical agent actions.
Agents can request approval and wait for human response before
proceeding with potentially destructive or high-impact operations.

Features:
- Create approval requests with context and options
- Wait for human approval (blocking or timeout)
- Track approval history and patterns
- Support for bulk approvals

Usage:
    from media_engine.ai.approval import ApprovalManager

    manager = ApprovalManager(project_root)

    # Request approval
    request = manager.request_approval(
        action="delete",
        description="Delete 15 outdated documents",
        context={"documents": [...], "reason": "cleanup"},
        options=["approve", "reject", "defer"],
    )

    # Wait for response (blocking)
    response = manager.wait_for_approval(request.id, timeout_seconds=300)

    if response.approved:
        # Proceed with action
        pass
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """An approval request from an agent."""
    id: str
    session_id: Optional[str]
    action: str  # e.g., "delete", "publish", "modify_critical"
    description: str
    context: Dict[str, Any]
    options: List[str]  # e.g., ["approve", "reject", "defer"]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = ""
    expires_at: Optional[str] = None
    response_at: Optional[str] = None
    responder: Optional[str] = None  # human identifier
    response_notes: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == ApprovalStatus.REJECTED

    @property
    def is_expired(self) -> bool:
        if self.status == ApprovalStatus.EXPIRED:
            return True
        if self.expires_at:
            return datetime.now() >= datetime.fromisoformat(self.expires_at)
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "action": self.action,
            "description": self.description,
            "context": self.context,
            "options": self.options,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "response_at": self.response_at,
            "responder": self.responder,
            "response_notes": self.response_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRequest":
        return cls(
            id=data["id"],
            session_id=data.get("session_id"),
            action=data["action"],
            description=data["description"],
            context=data.get("context", {}),
            options=data.get("options", ["approve", "reject"]),
            status=ApprovalStatus(data.get("status", "pending")),
            created_at=data.get("created_at", ""),
            expires_at=data.get("expires_at"),
            response_at=data.get("response_at"),
            responder=data.get("responder"),
            response_notes=data.get("response_notes"),
        )


@dataclass
class ApprovalResponse:
    """Response to an approval request."""
    request_id: str
    approved: bool
    status: ApprovalStatus
    responder: Optional[str] = None
    notes: Optional[str] = None
    responded_at: str = ""

    def __post_init__(self):
        if not self.responded_at:
            self.responded_at = datetime.now().isoformat()


class ApprovalManager:
    """
    Manages approval requests for human-in-the-loop workflows.

    Approval requests are stored as JSON files in .media-engine/ai/approvals/
    for persistence and visibility to dashboard UI.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.approvals_dir = self.project_root / ".media-engine" / "ai" / "approvals"
        self.approvals_dir.mkdir(parents=True, exist_ok=True)

    def _request_path(self, request_id: str) -> Path:
        return self.approvals_dir / f"{request_id}.json"

    def _save_request(self, request: ApprovalRequest) -> None:
        """Save an approval request to disk."""
        path = self._request_path(request.id)
        with open(path, "w") as f:
            json.dump(request.to_dict(), f, indent=2)

    def _load_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Load an approval request from disk."""
        path = self._request_path(request_id)
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return ApprovalRequest.from_dict(data)
        except Exception:
            return None

    def request_approval(
        self,
        action: str,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        timeout_minutes: int = 60,
    ) -> ApprovalRequest:
        """
        Create an approval request.

        Args:
            action: Type of action requiring approval
            description: Human-readable description
            context: Additional context for the approver
            options: Available response options
            session_id: Session creating the request
            timeout_minutes: How long until request expires

        Returns:
            ApprovalRequest ready for human response
        """
        from datetime import timedelta

        request = ApprovalRequest(
            id=str(uuid.uuid4())[:12],
            session_id=session_id,
            action=action,
            description=description,
            context=context or {},
            options=options or ["approve", "reject"],
            expires_at=(datetime.now() + timedelta(minutes=timeout_minutes)).isoformat(),
        )

        self._save_request(request)
        return request

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        request = self._load_request(request_id)
        if request and request.is_expired and request.status == ApprovalStatus.PENDING:
            request.status = ApprovalStatus.EXPIRED
            self._save_request(request)
        return request

    def respond(
        self,
        request_id: str,
        status: ApprovalStatus,
        responder: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ApprovalResponse]:
        """
        Respond to an approval request.

        Args:
            request_id: ID of the request to respond to
            status: Approval status (approved, rejected, deferred)
            responder: Human identifier providing the response
            notes: Optional notes explaining the decision

        Returns:
            ApprovalResponse if successful, None if request not found
        """
        request = self._load_request(request_id)
        if not request:
            return None

        if not request.is_pending:
            return None  # Already responded

        request.status = status
        request.response_at = datetime.now().isoformat()
        request.responder = responder
        request.response_notes = notes

        self._save_request(request)

        return ApprovalResponse(
            request_id=request_id,
            approved=status == ApprovalStatus.APPROVED,
            status=status,
            responder=responder,
            notes=notes,
        )

    def approve(
        self,
        request_id: str,
        responder: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ApprovalResponse]:
        """Shorthand to approve a request."""
        return self.respond(request_id, ApprovalStatus.APPROVED, responder, notes)

    def reject(
        self,
        request_id: str,
        responder: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ApprovalResponse]:
        """Shorthand to reject a request."""
        return self.respond(request_id, ApprovalStatus.REJECTED, responder, notes)

    def wait_for_approval(
        self,
        request_id: str,
        timeout_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> Optional[ApprovalResponse]:
        """
        Wait for human approval (blocking).

        This is a synchronous blocking call that polls for a response.
        Use for CLI or script contexts where blocking is acceptable.

        Args:
            request_id: ID of the request to wait for
            timeout_seconds: Maximum time to wait
            poll_interval: How often to check for response

        Returns:
            ApprovalResponse when human responds, or None if timeout
        """
        start_time = time.time()

        while True:
            request = self.get_request(request_id)

            if not request:
                return None

            if not request.is_pending:
                return ApprovalResponse(
                    request_id=request_id,
                    approved=request.is_approved,
                    status=request.status,
                    responder=request.responder,
                    notes=request.response_notes,
                    responded_at=request.response_at or datetime.now().isoformat(),
                )

            if request.is_expired:
                return ApprovalResponse(
                    request_id=request_id,
                    approved=False,
                    status=ApprovalStatus.EXPIRED,
                )

            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                # Mark as expired
                request.status = ApprovalStatus.EXPIRED
                self._save_request(request)
                return ApprovalResponse(
                    request_id=request_id,
                    approved=False,
                    status=ApprovalStatus.EXPIRED,
                )

            time.sleep(poll_interval)

    def list_pending(self, session_id: Optional[str] = None) -> List[ApprovalRequest]:
        """
        List pending approval requests.

        Args:
            session_id: Filter by session

        Returns:
            List of pending requests
        """
        requests = []
        for path in self.approvals_dir.glob("*.json"):
            request = self._load_request(path.stem)
            if request and request.is_pending:
                if session_id is None or request.session_id == session_id:
                    requests.append(request)

        # Sort by created_at descending (newest first)
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return requests

    def list_all(
        self,
        status: Optional[ApprovalStatus] = None,
        limit: int = 50,
    ) -> List[ApprovalRequest]:
        """
        List all approval requests.

        Args:
            status: Filter by status
            limit: Maximum number to return

        Returns:
            List of requests
        """
        requests = []
        for path in self.approvals_dir.glob("*.json"):
            request = self._load_request(path.stem)
            if request:
                if status is None or request.status == status:
                    requests.append(request)

        # Sort by created_at descending
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return requests[:limit]

    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel a pending approval request.

        Returns:
            True if cancelled, False if not found or already responded
        """
        request = self._load_request(request_id)
        if not request or not request.is_pending:
            return False

        request.status = ApprovalStatus.EXPIRED
        request.response_notes = "Cancelled by requester"
        self._save_request(request)
        return True

    def cleanup_old(self, days: int = 7) -> int:
        """
        Remove old approval requests.

        Args:
            days: Remove requests older than this many days

        Returns:
            Number of requests removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        count = 0

        for path in self.approvals_dir.glob("*.json"):
            request = self._load_request(path.stem)
            if request:
                try:
                    created = datetime.fromisoformat(request.created_at)
                    if created < cutoff and not request.is_pending:
                        path.unlink()
                        count += 1
                except Exception:
                    pass

        return count

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of approval requests.

        Returns:
            Summary with counts by status
        """
        summary = {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "deferred": 0,
            "expired": 0,
            "total": 0,
        }

        for path in self.approvals_dir.glob("*.json"):
            request = self._load_request(path.stem)
            if request:
                summary["total"] += 1
                summary[request.status.value] += 1

        return summary
