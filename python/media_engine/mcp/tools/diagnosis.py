"""
Failure Diagnosis MCP Tools

Provides tools for agents to diagnose failures and recover automatically.
When an agent encounters an error, it can use these tools to understand
what went wrong and how to fix it.

Usage:
    # After encountering an error
    result = await diagnose_failure(
        error_code="DOCUMENT_LOCKED",
        context={"path": "content/en/chapters/01.md"},
    )

    # Follow the recovery steps
    for step in result["recovery_steps"]:
        print(step)
"""

import json
from typing import Optional

from .errors import format_error, mcp_error_handler, require_project


def register_diagnosis_tools(mcp, server_instance):
    """Register failure diagnosis MCP tools."""

    @mcp.tool()
    @mcp_error_handler
    async def diagnose_failure(
        error_code: str = None,
        error_message: str = None,
        context: str = None,
    ) -> str:
        """
        Diagnose a failure and get recovery suggestions.

        Use this when you encounter an error and need to understand
        how to recover. Provide either the error_code or error_message.

        Args:
            error_code: Structured error code (e.g., "DOCUMENT_LOCKED", "SESSION_NOT_FOUND")
            error_message: The error message received
            context: Optional JSON string with additional context

        Returns:
            Diagnosis with recovery steps and suggestions
        """
        if error := require_project(server_instance):
            return error

        # Parse context
        context_dict = {}
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                context_dict = {"raw": context}

        diagnosis = {
            "error_code": error_code,
            "error_message": error_message,
            "diagnosis": None,
            "cause": None,
            "recovery_steps": [],
            "prevention": [],
            "related_tools": [],
        }

        # Diagnose based on error code
        if error_code == "DOCUMENT_LOCKED":
            diagnosis["diagnosis"] = "Document is locked by another session"
            diagnosis["cause"] = "Another agent or session is currently modifying this document"
            diagnosis["recovery_steps"] = [
                "1. Check who holds the lock: check_document_lock(path)",
                "2. If it's your session, you already have access",
                "3. If it's another session, wait or request the lock be released",
                "4. Use extend_document_lock() if you need more time",
                "5. Contact the other agent's operator if lock appears stale",
            ]
            diagnosis["prevention"] = [
                "Always acquire locks before modifying documents",
                "Release locks promptly after finishing",
                "Use session checkpoints for long operations",
            ]
            diagnosis["related_tools"] = [
                "check_document_lock",
                "acquire_document_lock",
                "release_document_lock",
                "list_document_locks",
            ]

        elif error_code == "SESSION_NOT_FOUND":
            diagnosis["diagnosis"] = "The session ID is invalid or session was deleted"
            diagnosis["cause"] = "Session may have been completed, abandoned, or never existed"
            diagnosis["recovery_steps"] = [
                "1. List available sessions: get_sessions()",
                "2. Create a new session if needed: start_ai_session()",
                "3. Check if session was completed: get_session_detail(id)",
            ]
            diagnosis["prevention"] = [
                "Store session ID after creation",
                "Complete sessions properly instead of abandoning",
            ]
            diagnosis["related_tools"] = [
                "start_ai_session",
                "get_sessions",
                "get_session_detail",
            ]

        elif error_code == "DOCUMENT_NOT_FOUND":
            path = context_dict.get("path", "unknown")
            diagnosis["diagnosis"] = f"Document does not exist at path: {path}"
            diagnosis["cause"] = "Path is incorrect, document was deleted, or never created"
            diagnosis["recovery_steps"] = [
                "1. Verify the path is correct (check for typos)",
                "2. List available documents: list_chapters(language)",
                "3. Search for the document: search_documents(query)",
                "4. Create the document if it should exist: create_document()",
            ]
            diagnosis["prevention"] = [
                "Use list_chapters() to get valid paths",
                "Use relative paths from project root",
            ]
            diagnosis["related_tools"] = [
                "list_chapters",
                "search_documents",
                "create_document",
            ]

        elif error_code == "APPROVAL_REQUIRED":
            diagnosis["diagnosis"] = "This action requires human approval before proceeding"
            diagnosis["cause"] = "Action is classified as critical or potentially destructive"
            diagnosis["recovery_steps"] = [
                "1. Create an approval request: request_approval()",
                "2. Wait for human response: wait_for_approval() or check_approval_status()",
                "3. Proceed only after approval is granted",
                "4. If rejected, follow alternative approach from responder notes",
            ]
            diagnosis["prevention"] = [
                "Check if approval is needed before starting critical operations",
                "Batch similar operations into single approval requests",
            ]
            diagnosis["related_tools"] = [
                "request_approval",
                "wait_for_approval",
                "check_approval_status",
            ]

        elif error_code == "APPROVAL_TIMEOUT":
            diagnosis["diagnosis"] = "Approval request timed out waiting for human response"
            diagnosis["cause"] = "Human did not respond within the timeout period"
            diagnosis["recovery_steps"] = [
                "1. Create a new approval request with longer timeout",
                "2. Notify the operator via alternative channel",
                "3. Consider deferring the action to a later time",
                "4. Check if the action is still necessary",
            ]
            diagnosis["prevention"] = [
                "Set appropriate timeout based on urgency",
                "Ensure humans are available to respond",
            ]
            diagnosis["related_tools"] = [
                "request_approval",
                "list_pending_approvals",
            ]

        elif error_code == "CHECKPOINT_ERROR":
            diagnosis["diagnosis"] = "Failed to create or restore checkpoint"
            diagnosis["cause"] = "File system issue or corrupted checkpoint data"
            diagnosis["recovery_steps"] = [
                "1. List available checkpoints: list_checkpoints(session_id)",
                "2. Try rolling back to an earlier checkpoint",
                "3. Check file system permissions",
                "4. Create a fresh checkpoint at current state",
            ]
            diagnosis["prevention"] = [
                "Create checkpoints before major changes",
                "Verify checkpoint creation succeeded",
            ]
            diagnosis["related_tools"] = [
                "create_session_checkpoint",
                "list_checkpoints",
                "rollback_to_checkpoint",
            ]

        elif error_code == "PROJECT_NOT_FOUND":
            diagnosis["diagnosis"] = "No project.yaml found in current directory or parents"
            diagnosis["cause"] = "Not running from a media-engine project directory"
            diagnosis["recovery_steps"] = [
                "1. Navigate to a directory with project.yaml",
                "2. Or specify project path when starting the server",
                "3. Initialize a new project: media-engine init",
            ]
            diagnosis["prevention"] = [
                "Always run from project root or specify path",
            ]
            diagnosis["related_tools"] = [
                "get_project_status",
            ]

        elif error_code == "CONFIGURATION_ERROR":
            diagnosis["diagnosis"] = "Project configuration is invalid or missing required fields"
            diagnosis["cause"] = "project.yaml or brand.yaml has syntax errors or missing fields"
            diagnosis["recovery_steps"] = [
                "1. Validate YAML syntax in configuration files",
                "2. Check for required fields in project.yaml",
                "3. Compare with a working project configuration",
                "4. Run: media-engine validate",
            ]
            diagnosis["prevention"] = [
                "Use schema validation when editing config files",
                "Make incremental changes and test after each",
            ]
            diagnosis["related_tools"] = [
                "get_project_status",
            ]

        elif error_code == "PERMISSION_DENIED":
            diagnosis["diagnosis"] = "Insufficient permissions to access or modify resource"
            diagnosis["cause"] = "File system permissions prevent access"
            diagnosis["recovery_steps"] = [
                "1. Check file ownership and permissions",
                "2. Ensure the process user has write access",
                "3. Check if file is read-only or locked by OS",
            ]
            diagnosis["prevention"] = [
                "Run with appropriate user permissions",
                "Check permissions before batch operations",
            ]
            diagnosis["related_tools"] = []

        elif error_code == "INVALID_JSON":
            diagnosis["diagnosis"] = "Failed to parse JSON input"
            diagnosis["cause"] = "Malformed JSON string provided to a tool"
            diagnosis["recovery_steps"] = [
                "1. Validate JSON syntax",
                "2. Check for unescaped special characters",
                "3. Ensure proper quoting of strings",
                "4. Use a JSON validator tool",
            ]
            diagnosis["prevention"] = [
                "Always validate JSON before sending",
                "Use proper escaping for special characters",
            ]
            diagnosis["related_tools"] = []

        else:
            # Generic diagnosis for unknown errors
            diagnosis["diagnosis"] = "Unable to determine specific cause"
            diagnosis["cause"] = error_message or "Unknown error occurred"
            diagnosis["recovery_steps"] = [
                "1. Check the error message for clues",
                "2. Review recent operations for what might have caused it",
                "3. Use get_observability_full() to check system state",
                "4. Try the operation again after checking preconditions",
            ]
            diagnosis["prevention"] = [
                "Use structured error handling",
                "Check preconditions before operations",
            ]
            diagnosis["related_tools"] = [
                "get_observability_full",
                "diagnose_issue",
            ]

        return json.dumps(diagnosis, indent=2)

    @mcp.tool()
    @mcp_error_handler
    async def get_system_health() -> str:
        """
        Get a quick system health check.

        Use this to verify the system is working before starting work
        or after encountering errors.

        Returns:
            Health status with any issues found
        """
        if error := require_project(server_instance):
            return error

        project = server_instance.project
        issues = []
        status = "healthy"

        # Check project config
        try:
            _ = project.config
        except Exception as e:
            issues.append(f"Project config issue: {e}")
            status = "unhealthy"

        # Check for stale locks
        try:
            from ...ai.locking import get_lock_manager

            lock_manager = get_lock_manager(project.root)
            expired = lock_manager.list_expired_locks()
            if expired:
                issues.append(f"{len(expired)} expired locks need cleanup")
                if status == "healthy":
                    status = "warning"
        except Exception:
            pass

        # Check for stale sessions
        try:
            from ...ai.sessions import SessionManager, SessionStatus
            from datetime import datetime, timedelta

            session_manager = SessionManager(project.root)
            active = session_manager.list_sessions(status=SessionStatus.ACTIVE)
            stale = []
            for s in active:
                try:
                    last_active = datetime.fromisoformat(s.last_active)
                    if datetime.now() - last_active > timedelta(hours=2):
                        stale.append(s.id)
                except Exception:
                    pass
            if stale:
                issues.append(f"{len(stale)} stale sessions may need attention")
                if status == "healthy":
                    status = "warning"
        except Exception:
            pass

        # Check for pending approvals
        try:
            from ...ai.approval import ApprovalManager

            approval_manager = ApprovalManager(project.root)
            pending = approval_manager.list_pending()
            if pending:
                issues.append(f"{len(pending)} approval requests awaiting response")
        except Exception:
            pass

        return json.dumps(
            {
                "status": status,
                "project": project.name,
                "issues": issues,
                "issue_count": len(issues),
                "recommendations": [
                    "Run diagnose_failure() if you encounter errors",
                    "Use get_observability_full() for detailed system state",
                ] if issues else [],
            },
            indent=2,
        )

    @mcp.tool()
    @mcp_error_handler
    async def suggest_recovery(
        failed_operation: str,
        error_message: str = None,
    ) -> str:
        """
        Get recovery suggestions for a failed operation.

        Args:
            failed_operation: Name of the tool or operation that failed
            error_message: The error message received

        Returns:
            Suggested recovery steps specific to the operation
        """
        if error := require_project(server_instance):
            return error

        suggestions = {
            "operation": failed_operation,
            "error": error_message,
            "recovery_options": [],
            "alternative_approaches": [],
        }

        # Operation-specific recovery suggestions
        if "document" in failed_operation.lower() or "chapter" in failed_operation.lower():
            suggestions["recovery_options"] = [
                "1. Verify document path with list_chapters()",
                "2. Check if document is locked with check_document_lock()",
                "3. Acquire lock before modifying: acquire_document_lock()",
                "4. Create document if it doesn't exist: create_document()",
            ]
            suggestions["alternative_approaches"] = [
                "Use scaffold_document() to preview before creating",
                "Read document first to confirm path: read_document()",
            ]

        elif "session" in failed_operation.lower():
            suggestions["recovery_options"] = [
                "1. List sessions to find valid IDs: get_sessions()",
                "2. Check session details: get_session_detail()",
                "3. Create new session if needed: start_ai_session()",
                "4. Resume paused session: resume_session()",
            ]
            suggestions["alternative_approaches"] = [
                "Create checkpoint before risky operations",
                "Use session notes to track progress",
            ]

        elif "approval" in failed_operation.lower():
            suggestions["recovery_options"] = [
                "1. Check request status: check_approval_status()",
                "2. Create new request with longer timeout",
                "3. Cancel and retry: cancel_approval_request()",
                "4. List pending: list_pending_approvals()",
            ]
            suggestions["alternative_approaches"] = [
                "Break action into smaller approvable steps",
                "Provide more context in the approval request",
            ]

        elif "lock" in failed_operation.lower():
            suggestions["recovery_options"] = [
                "1. Check lock status: check_document_lock()",
                "2. Wait and retry after lock expires",
                "3. Extend your lock if you own it: extend_document_lock()",
                "4. Release lock when done: release_document_lock()",
            ]
            suggestions["alternative_approaches"] = [
                "Use shorter lock timeouts",
                "Create checkpoints before locking multiple files",
            ]

        elif "build" in failed_operation.lower() or "render" in failed_operation.lower():
            suggestions["recovery_options"] = [
                "1. Check build dependencies are met",
                "2. Verify input files exist and are valid",
                "3. Check for syntax errors in configuration",
                "4. Try building with verbose logging",
            ]
            suggestions["alternative_approaches"] = [
                "Build incrementally to isolate failures",
                "Validate inputs before building",
            ]

        else:
            # Generic suggestions
            suggestions["recovery_options"] = [
                "1. Check system health: get_system_health()",
                "2. Review error details: diagnose_failure()",
                "3. Check observability: get_observability_full()",
                "4. Try operation again with correct inputs",
            ]
            suggestions["alternative_approaches"] = [
                "Break operation into smaller steps",
                "Verify preconditions before retrying",
            ]

        return json.dumps(suggestions, indent=2)
