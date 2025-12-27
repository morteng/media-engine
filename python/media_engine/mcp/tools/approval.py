"""
Approval Gate MCP Tools

Provides tools for agents to request human approval before
taking critical or potentially destructive actions.

Usage:
    # Agent requests approval
    result = await request_approval(
        action="delete",
        description="Delete 15 outdated documents",
        context={"documents": [...]},
    )

    # Human responds via dashboard
    # Agent checks status
    status = await check_approval_status(request_id)
"""

import json
from typing import Optional

from .errors import format_error, mcp_error_handler, require_project
from ...ai.approval import ApprovalManager, ApprovalStatus
from ...core.exceptions import ApprovalRequiredError, ApprovalTimeoutError


def register_approval_tools(mcp, server_instance):
    """Register approval gate MCP tools."""

    @mcp.tool()
    @mcp_error_handler
    async def request_approval(
        action: str,
        description: str,
        context: str = None,
        options: str = None,
        session_id: str = None,
        timeout_minutes: int = 60,
    ) -> str:
        """
        Request human approval for a critical action.

        Use this before taking potentially destructive or high-impact actions
        to ensure human oversight.

        Args:
            action: Type of action (e.g., "delete", "publish", "modify_critical")
            description: Human-readable description of what will be done
            context: Optional JSON string with additional context
            options: Optional JSON array of response options (default: ["approve", "reject"])
            session_id: Optional session ID for tracking
            timeout_minutes: How long the request is valid (default: 60)

        Returns:
            Approval request details including ID for status checking
        """
        if error := require_project(server_instance):
            return error

        manager = ApprovalManager(server_instance.project.root)

        # Parse optional context
        context_dict = {}
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                context_dict = {"raw": context}

        # Parse optional options
        options_list = ["approve", "reject"]
        if options:
            try:
                options_list = json.loads(options)
            except json.JSONDecodeError:
                pass

        request = manager.request_approval(
            action=action,
            description=description,
            context=context_dict,
            options=options_list,
            session_id=session_id,
            timeout_minutes=timeout_minutes,
        )

        return json.dumps(
            {
                "status": "pending",
                "request_id": request.id,
                "action": request.action,
                "description": request.description,
                "expires_at": request.expires_at,
                "options": request.options,
                "message": "Approval request created. Check status or wait for response.",
            },
            indent=2,
        )

    @mcp.tool()
    @mcp_error_handler
    async def check_approval_status(request_id: str) -> str:
        """
        Check the status of an approval request.

        Use this to poll for human response without blocking.

        Args:
            request_id: ID of the approval request

        Returns:
            Current status and response details if available
        """
        if error := require_project(server_instance):
            return error

        manager = ApprovalManager(server_instance.project.root)
        request = manager.get_request(request_id)

        if not request:
            return format_error(
                ApprovalRequiredError(
                    message=f"Approval request not found: {request_id}",
                    action="check_status",
                    context={"request_id": request_id},
                )
            )

        result = {
            "request_id": request.id,
            "status": request.status.value,
            "action": request.action,
            "description": request.description,
            "created_at": request.created_at,
            "expires_at": request.expires_at,
        }

        if not request.is_pending:
            result["response_at"] = request.response_at
            result["responder"] = request.responder
            result["response_notes"] = request.response_notes
            result["approved"] = request.is_approved

        return json.dumps(result, indent=2)

    @mcp.tool()
    @mcp_error_handler
    async def wait_for_approval(
        request_id: str,
        timeout_seconds: int = 300,
    ) -> str:
        """
        Wait for human approval (blocking).

        This will block until a human responds or timeout is reached.
        Use sparingly as it blocks the agent.

        Args:
            request_id: ID of the approval request
            timeout_seconds: Maximum time to wait (default: 300 = 5 minutes)

        Returns:
            Approval response with decision and notes
        """
        if error := require_project(server_instance):
            return error

        manager = ApprovalManager(server_instance.project.root)
        response = manager.wait_for_approval(request_id, timeout_seconds)

        if not response:
            return format_error(
                ApprovalTimeoutError(
                    message="Approval request not found or timeout waiting",
                    timeout_seconds=timeout_seconds,
                )
            )

        if response.status == ApprovalStatus.EXPIRED:
            return format_error(
                ApprovalTimeoutError(
                    message="Approval request expired while waiting",
                    timeout_seconds=timeout_seconds,
                )
            )

        return json.dumps(
            {
                "request_id": response.request_id,
                "approved": response.approved,
                "status": response.status.value,
                "responder": response.responder,
                "notes": response.notes,
                "responded_at": response.responded_at,
            },
            indent=2,
        )

    @mcp.tool()
    @mcp_error_handler
    async def list_pending_approvals(session_id: str = None) -> str:
        """
        List pending approval requests.

        Args:
            session_id: Optional filter by session

        Returns:
            List of pending approval requests
        """
        if error := require_project(server_instance):
            return error

        manager = ApprovalManager(server_instance.project.root)
        requests = manager.list_pending(session_id=session_id)

        return json.dumps(
            {
                "pending_count": len(requests),
                "requests": [
                    {
                        "id": r.id,
                        "action": r.action,
                        "description": r.description,
                        "created_at": r.created_at,
                        "expires_at": r.expires_at,
                        "session_id": r.session_id,
                    }
                    for r in requests
                ],
            },
            indent=2,
        )

    @mcp.tool()
    @mcp_error_handler
    async def cancel_approval_request(request_id: str) -> str:
        """
        Cancel a pending approval request.

        Use this if you no longer need approval for an action.

        Args:
            request_id: ID of the request to cancel

        Returns:
            Cancellation status
        """
        if error := require_project(server_instance):
            return error

        manager = ApprovalManager(server_instance.project.root)
        cancelled = manager.cancel_request(request_id)

        if cancelled:
            return json.dumps(
                {
                    "status": "cancelled",
                    "request_id": request_id,
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "status": "not_cancelled",
                    "request_id": request_id,
                    "reason": "Request not found or already responded",
                },
                indent=2,
            )

    @mcp.tool()
    @mcp_error_handler
    async def get_approval_summary() -> str:
        """
        Get summary of all approval requests.

        Returns:
            Summary with counts by status
        """
        if error := require_project(server_instance):
            return error

        manager = ApprovalManager(server_instance.project.root)
        summary = manager.get_summary()

        return json.dumps(summary, indent=2)
