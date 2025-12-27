"""
Agent Observability API Routes

Provides endpoints for AI agents to introspect system state,
diagnose issues, and understand what's happening in the project.

Endpoints:
- GET /api/observability/health - System health summary
- GET /api/observability/sessions - Active AI sessions
- GET /api/observability/locks - Document locks
- GET /api/observability/queue - Task queue status
- GET /api/observability/full - Complete observability snapshot
- POST /api/observability/diagnose - Issue diagnosis
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable

from fastapi import APIRouter

if TYPE_CHECKING:
    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_observability_routes(
    router: APIRouter,
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register observability API routes."""

    @router.get("/api/observability/health")
    async def get_health_summary() -> dict[str, Any]:
        """
        Get a health summary of the system.

        Returns overall system health indicators for quick status checks.
        """
        project = get_project()

        health = {
            "status": "healthy",
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "project": {
                "name": project.name,
                "root": str(project.root),
                "languages": list(project.languages.keys()),
                "source_language": project.source_language,
            },
            "indicators": {},
        }

        # Check document count
        try:
            doc_count = 0
            for lang in project.languages:
                doc_count += len(list(project.list_chapters(lang)))
            health["indicators"]["documents"] = {"count": doc_count, "status": "ok"}
        except Exception as e:
            health["indicators"]["documents"] = {"status": "error", "message": str(e)}
            health["healthy"] = False

        # Check for stale content
        try:
            from ...freshness.freshness_checker import FreshnessChecker

            checker = FreshnessChecker(project)
            stale_docs = checker.get_stale_documents()
            health["indicators"]["freshness"] = {
                "stale_count": len(stale_docs),
                "status": "warning" if stale_docs else "ok",
            }
        except Exception:
            health["indicators"]["freshness"] = {"status": "unknown"}

        # Check active locks
        try:
            from ...ai.locking import get_lock_manager

            lock_manager = get_lock_manager(project.root)
            locks = lock_manager.list_locks()
            health["indicators"]["locks"] = {
                "active_count": len(locks),
                "status": "ok",
            }
        except Exception:
            health["indicators"]["locks"] = {"status": "unknown"}

        # Check active sessions
        try:
            from ...ai.sessions import SessionManager, SessionStatus

            session_manager = SessionManager(project.root)
            active_sessions = session_manager.list_sessions(status=SessionStatus.ACTIVE)
            health["indicators"]["sessions"] = {
                "active_count": len(active_sessions),
                "status": "ok",
            }
        except Exception:
            health["indicators"]["sessions"] = {"status": "unknown"}

        return health

    @router.get("/api/observability/sessions")
    async def get_sessions(status: str = None, limit: int = 10) -> dict[str, Any]:
        """
        Get AI session information.

        Args:
            status: Filter by status (active, paused, completed, abandoned)
            limit: Maximum number of sessions to return

        Returns detailed session information for debugging and continuity.
        """
        project = get_project()

        from ...ai.sessions import SessionManager, SessionStatus

        session_manager = SessionManager(project.root)

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = SessionStatus(status)
            except ValueError:
                pass

        sessions = session_manager.list_sessions(status=status_filter, limit=limit)

        return {
            "total": len(sessions),
            "sessions": [
                {
                    "id": s.id,
                    "status": s.status.value,
                    "started_at": s.started_at,
                    "last_active": s.last_active,
                    "current_task_id": s.current_task_id,
                    "progress": {
                        "total_steps": len(s.progress),
                        "completed_steps": len([p for p in s.progress if p.completed]),
                        "in_progress": [p.description for p in s.progress if p.in_progress],
                    },
                    "changes_count": len(s.changes_made),
                    "decisions_count": len(s.decisions),
                    "blockers": s.blockers,
                }
                for s in sessions
            ],
        }

    @router.get("/api/observability/sessions/{session_id}")
    async def get_session_detail(session_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific session.

        Includes full progress, changes, decisions, and checkpoint info.
        """
        project = get_project()

        from ...ai.sessions import SessionManager

        session_manager = SessionManager(project.root)
        session = session_manager.get(session_id)

        if not session:
            return {"error": f"Session not found: {session_id}"}

        # Get checkpoints
        checkpoints = session_manager.list_checkpoints(session_id)

        return {
            "id": session.id,
            "status": session.status.value,
            "started_at": session.started_at,
            "last_active": session.last_active,
            "current_task_id": session.current_task_id,
            "notes": session.notes,
            "progress": [
                {
                    "description": p.description,
                    "completed": p.completed,
                    "in_progress": p.in_progress,
                    "timestamp": p.timestamp,
                }
                for p in session.progress
            ],
            "changes_made": [
                {
                    "file": c.file,
                    "type": c.change_type,
                    "sections": c.sections,
                    "timestamp": c.timestamp,
                }
                for c in session.changes_made
            ],
            "decisions": [
                {
                    "question": d.question,
                    "decision": d.decision,
                    "reasoning": d.reasoning,
                    "scope": d.scope,
                    "timestamp": d.timestamp,
                }
                for d in session.decisions
            ],
            "blockers": session.blockers,
            "checkpoints": [
                {
                    "id": cp.id,
                    "label": cp.label,
                    "timestamp": cp.timestamp,
                    "step_index": cp.step_index,
                    "files_backed_up": len(cp.files_snapshot),
                }
                for cp in checkpoints
            ],
        }

    @router.get("/api/observability/locks")
    async def get_locks(session_id: str = None) -> dict[str, Any]:
        """
        Get document lock information.

        Args:
            session_id: Filter locks by session

        Returns all active document locks for concurrent safety monitoring.
        """
        project = get_project()

        from ...ai.locking import get_lock_manager

        lock_manager = get_lock_manager(project.root)
        summary = lock_manager.get_lock_summary()

        return {
            "total_active": summary["total_active"],
            "total_expired": summary["total_expired"],
            "sessions_with_locks": summary["sessions_with_locks"],
            "locks": summary["all_locks"],
            "by_session": summary["by_session"],
        }

    @router.get("/api/observability/queue")
    async def get_queue_status() -> dict[str, Any]:
        """
        Get task queue status.

        Returns pending, active, and recent completed tasks.
        """
        project = get_project()

        from ...ai.queue import TaskQueue, TaskStatus

        queue = TaskQueue(project.root)

        pending = queue.list_tasks(status=TaskStatus.PENDING)
        in_progress = queue.list_tasks(status=TaskStatus.IN_PROGRESS)
        completed = queue.list_tasks(status=TaskStatus.COMPLETED, limit=5)
        failed = queue.list_tasks(status=TaskStatus.FAILED, limit=5)

        return {
            "summary": {
                "pending": len(pending),
                "in_progress": len(in_progress),
            },
            "pending": [
                {
                    "id": t.id,
                    "type": t.task_type,
                    "priority": t.priority.value,
                    "created_at": t.created_at,
                    "description": t.description,
                }
                for t in pending[:10]
            ],
            "in_progress": [
                {
                    "id": t.id,
                    "type": t.task_type,
                    "started_at": t.started_at,
                    "description": t.description,
                }
                for t in in_progress
            ],
            "recent_completed": [
                {
                    "id": t.id,
                    "type": t.task_type,
                    "completed_at": t.completed_at,
                }
                for t in completed
            ],
            "recent_failed": [
                {
                    "id": t.id,
                    "type": t.task_type,
                    "error": t.error_message,
                }
                for t in failed
            ],
        }

    @router.get("/api/observability/full")
    async def get_full_snapshot() -> dict[str, Any]:
        """
        Get a complete observability snapshot.

        Combines health, sessions, locks, and queue status into
        a single comprehensive view for agent introspection.
        """
        health = await get_health_summary()
        sessions = await get_sessions(limit=5)
        locks = await get_locks()
        queue = await get_queue_status()

        return {
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "sessions": sessions,
            "locks": locks,
            "queue": queue,
        }

    @router.post("/api/observability/diagnose")
    async def diagnose_issue(issue_type: str = None) -> dict[str, Any]:
        """
        Diagnose common issues and provide recovery suggestions.

        Args:
            issue_type: Specific issue to diagnose (lock_conflict, stale_session, etc.)

        Returns diagnosis with actionable recovery steps.
        """
        project = get_project()

        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue_type,
            "findings": [],
            "suggestions": [],
        }

        # Check for expired locks
        from ...ai.locking import get_lock_manager

        lock_manager = get_lock_manager(project.root)
        expired_locks = lock_manager.list_expired_locks()
        if expired_locks:
            diagnostics["findings"].append({
                "type": "expired_locks",
                "count": len(expired_locks),
                "paths": [lock.path for lock in expired_locks[:5]],
            })
            diagnostics["suggestions"].append(
                "Run lock cleanup to remove expired locks"
            )

        # Check for stale sessions
        from ...ai.sessions import SessionManager, SessionStatus

        session_manager = SessionManager(project.root)
        active_sessions = session_manager.list_sessions(status=SessionStatus.ACTIVE)

        stale_sessions = []
        for session in active_sessions:
            try:
                last_active = datetime.fromisoformat(session.last_active)
                if datetime.now() - last_active > timedelta(hours=2):
                    stale_sessions.append(session)
            except Exception:
                pass

        if stale_sessions:
            diagnostics["findings"].append({
                "type": "stale_sessions",
                "count": len(stale_sessions),
                "session_ids": [s.id for s in stale_sessions],
            })
            diagnostics["suggestions"].append(
                "Consider pausing or completing stale sessions"
            )

        # Check for lock conflicts (same doc locked by multiple)
        all_locks = lock_manager.list_locks()
        lock_paths = [lock.path for lock in all_locks]
        duplicate_paths = [p for p in lock_paths if lock_paths.count(p) > 1]
        if duplicate_paths:
            diagnostics["findings"].append({
                "type": "lock_conflict",
                "paths": list(set(duplicate_paths)),
            })
            diagnostics["suggestions"].append(
                "Force release conflicting locks and retry"
            )

        # If specific issue type requested
        if issue_type == "lock_conflict":
            diagnostics["recovery_steps"] = [
                "1. Identify which session should retain the lock",
                "2. Use release_document_lock for other sessions",
                "3. Or use force_release if session is unresponsive",
                "4. Retry your operation",
            ]
        elif issue_type == "stale_session":
            diagnostics["recovery_steps"] = [
                "1. Check if the session's work was completed",
                "2. If incomplete, resume the session with resume_session",
                "3. If abandoned, use complete_session or abandon_session",
                "4. Release any locks held by the session",
            ]

        if not diagnostics["findings"]:
            diagnostics["status"] = "healthy"
            diagnostics["message"] = "No issues detected"

        return diagnostics

    @router.get("/api/observability/metrics")
    async def get_metrics() -> dict[str, Any]:
        """
        Get system metrics for monitoring.

        Returns performance and usage metrics.
        """
        project = get_project()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "project": project.name,
            "counts": {},
            "performance": {},
        }

        # Document counts
        try:
            for lang in project.languages:
                chapters = list(project.list_chapters(lang))
                metrics["counts"][f"documents_{lang}"] = len(chapters)
        except Exception:
            pass

        # Session metrics
        try:
            from ...ai.sessions import SessionManager, SessionStatus

            session_manager = SessionManager(project.root)
            active = session_manager.list_sessions(status=SessionStatus.ACTIVE)
            completed = session_manager.list_sessions(status=SessionStatus.COMPLETED, limit=100)

            metrics["counts"]["active_sessions"] = len(active)
            metrics["counts"]["completed_sessions"] = len(completed)
        except Exception:
            pass

        # Lock metrics
        try:
            from ...ai.locking import get_lock_manager

            lock_manager = get_lock_manager(project.root)
            summary = lock_manager.get_lock_summary()
            metrics["counts"]["active_locks"] = summary["total_active"]
            metrics["counts"]["expired_locks"] = summary["total_expired"]
        except Exception:
            pass

        # Queue metrics
        try:
            from ...ai.queue import TaskQueue, TaskStatus

            queue = TaskQueue(project.root)
            metrics["counts"]["pending_tasks"] = len(queue.list_tasks(status=TaskStatus.PENDING))
            metrics["counts"]["failed_tasks"] = len(queue.list_tasks(status=TaskStatus.FAILED, limit=100))
        except Exception:
            pass

        # Approval metrics
        try:
            from ...ai.approval import ApprovalManager

            approval_manager = ApprovalManager(project.root)
            summary = approval_manager.get_summary()
            metrics["counts"]["pending_approvals"] = summary["pending"]
        except Exception:
            pass

        return metrics
