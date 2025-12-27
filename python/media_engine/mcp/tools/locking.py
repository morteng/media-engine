"""
Document Locking MCP Tools

Provides tools for agents to manage document locks for
concurrent safety when multiple agents work on the same project.

Usage:
    # Before modifying a document
    result = await acquire_document_lock("content/en/chapters/01.md", session_id)

    # After finished
    await release_document_lock("content/en/chapters/01.md", session_id)
"""

import json
from typing import Optional

from .errors import format_error, mcp_error_handler, require_project
from ...ai.locking import get_lock_manager
from ...core.exceptions import DocumentLockedError


def register_locking_tools(mcp, server_instance):
    """Register document locking MCP tools."""

    @mcp.tool()
    @mcp_error_handler
    async def acquire_document_lock(
        document_path: str,
        session_id: str,
        timeout_minutes: int = 30,
        reason: str = None,
        force: bool = False,
    ) -> str:
        """
        Acquire a lock on a document before modifying it.

        This prevents other agents from modifying the same document
        simultaneously, avoiding conflicts and data loss.

        Args:
            document_path: Relative path to the document (e.g., "content/en/chapters/01.md")
            session_id: Your session ID (use from start_ai_session)
            timeout_minutes: Lock timeout in minutes (default: 30)
            reason: Optional reason for the lock
            force: Force acquire even if locked by another session (use carefully!)

        Returns:
            Lock confirmation with expiration time
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)

        try:
            manager.acquire(
                document_path=document_path,
                session_id=session_id,
                timeout_minutes=timeout_minutes,
                reason=reason,
                force=force,
            )

            lock = manager.check_lock(document_path)
            return json.dumps(
                {
                    "status": "lock_acquired",
                    "document": document_path,
                    "session_id": session_id,
                    "expires_at": lock.expires_at if lock else None,
                    "remaining_minutes": lock.remaining_minutes if lock else timeout_minutes,
                },
                indent=2,
            )
        except DocumentLockedError as e:
            return format_error(e)

    @mcp.tool()
    @mcp_error_handler
    async def release_document_lock(
        document_path: str,
        session_id: str,
    ) -> str:
        """
        Release a lock on a document after finishing modifications.

        Always release locks when done to allow other agents to work
        on the document.

        Args:
            document_path: Relative path to the document
            session_id: Your session ID

        Returns:
            Release confirmation
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)
        released = manager.release(document_path, session_id)

        if released:
            return json.dumps(
                {
                    "status": "lock_released",
                    "document": document_path,
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "status": "not_released",
                    "document": document_path,
                    "reason": "Lock not owned by this session",
                },
                indent=2,
            )

    @mcp.tool()
    @mcp_error_handler
    async def check_document_lock(document_path: str) -> str:
        """
        Check if a document is currently locked.

        Use this before attempting to modify a document to see
        if you need to acquire a lock or wait.

        Args:
            document_path: Relative path to the document

        Returns:
            Lock status with owner info if locked
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)
        lock = manager.check_lock(document_path)

        if lock:
            return json.dumps(
                {
                    "is_locked": True,
                    "document": document_path,
                    "locked_by": lock.session_id,
                    "acquired_at": lock.acquired_at,
                    "expires_at": lock.expires_at,
                    "remaining_minutes": lock.remaining_minutes,
                    "reason": lock.reason,
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "is_locked": False,
                    "document": document_path,
                },
                indent=2,
            )

    @mcp.tool()
    @mcp_error_handler
    async def list_document_locks(session_id: str = None) -> str:
        """
        List all active document locks.

        Args:
            session_id: Optional filter to only show locks for a specific session

        Returns:
            List of all active locks with details
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)
        locks = manager.list_locks(session_id=session_id)

        return json.dumps(
            {
                "total_locks": len(locks),
                "locks": [
                    {
                        "document": lock.path,
                        "session_id": lock.session_id,
                        "acquired_at": lock.acquired_at,
                        "expires_at": lock.expires_at,
                        "remaining_minutes": lock.remaining_minutes,
                        "reason": lock.reason,
                    }
                    for lock in locks
                ],
            },
            indent=2,
        )

    @mcp.tool()
    @mcp_error_handler
    async def extend_document_lock(
        document_path: str,
        session_id: str,
        additional_minutes: int = 30,
    ) -> str:
        """
        Extend the timeout on an existing lock.

        Use this if you need more time to complete your modifications.

        Args:
            document_path: Relative path to the document
            session_id: Your session ID
            additional_minutes: Minutes to add to the lock (default: 30)

        Returns:
            Extended lock details
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)
        extended = manager.extend_lock(document_path, session_id, additional_minutes)

        if extended:
            lock = manager.check_lock(document_path)
            return json.dumps(
                {
                    "status": "lock_extended",
                    "document": document_path,
                    "new_expires_at": lock.expires_at if lock else None,
                    "remaining_minutes": lock.remaining_minutes if lock else additional_minutes,
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "status": "not_extended",
                    "document": document_path,
                    "reason": "Lock not owned by this session or does not exist",
                },
                indent=2,
            )

    @mcp.tool()
    @mcp_error_handler
    async def release_session_locks(session_id: str) -> str:
        """
        Release all locks held by a session.

        Use this when completing or abandoning a session to clean up
        all locks at once.

        Args:
            session_id: Session ID to release locks for

        Returns:
            Number of locks released
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)
        count = manager.release_all_for_session(session_id)

        return json.dumps(
            {
                "status": "locks_released",
                "session_id": session_id,
                "locks_released": count,
            },
            indent=2,
        )

    @mcp.tool()
    @mcp_error_handler
    async def get_lock_summary() -> str:
        """
        Get a summary of all document locks in the project.

        Useful for understanding the current lock state and
        identifying potential issues.

        Returns:
            Summary with counts and details by session
        """
        if error := require_project(server_instance):
            return error

        manager = get_lock_manager(server_instance.project.root)
        summary = manager.get_lock_summary()

        return json.dumps(summary, indent=2)
