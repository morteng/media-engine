"""
AI Context Provider

Provides comprehensive context for AI agents starting work.
Aggregates information from queue, sessions, research, and notes.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .notes import NotesManager, NoteStatus, NoteType
from .queue import TaskQueue, TaskStatus
from .research import ResearchStore
from .sessions import SessionManager, SessionStatus

if TYPE_CHECKING:
    from ..core.project import Project


class AIContext:
    """
    Comprehensive context provider for AI agents.

    Aggregates information from all AI subsystems to give
    agents everything they need to start or continue work.
    """

    def __init__(self, project: "Project"):
        self.project = project
        self.queue = TaskQueue(project.root)
        self.sessions = SessionManager(project.root)
        self.research = ResearchStore(project.root)
        self.notes = NotesManager(project.root)

    def get_full_context(self) -> Dict[str, Any]:
        """
        Get complete AI context.

        Returns everything an AI agent needs to understand
        the current state and decide what to work on.
        """
        return {
            "project": self._get_project_context(),
            "work_queue": self._get_queue_context(),
            "active_session": self._get_session_context(),
            "notes_requiring_attention": self._get_notes_context(),
            "research_status": self._get_research_context(),
            "video_production": self._get_video_context(),
            "suggested_actions": self._get_suggested_actions(),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_project_context(self) -> Dict[str, Any]:
        """Get project-level context."""
        return {
            "name": self.project.name,
            "root": str(self.project.root),
            "languages": getattr(self.project, "languages", ["en"]),
            "content_dir": str(self.project.content_dir),
        }

    def _get_queue_context(self) -> Dict[str, Any]:
        """Get work queue context."""
        pending = self.queue.list_tasks(status=TaskStatus.PENDING, limit=10)
        processing = self.queue.list_tasks(status=TaskStatus.PROCESSING, limit=5)
        stats = self.queue.get_stats()

        return {
            "stats": stats,
            "pending_tasks": [
                {
                    "id": t.id,
                    "operation": t.operation,
                    "priority": t.priority.value,
                    "instructions": t.instructions[:200],
                    "selections_count": len(t.selections),
                }
                for t in pending
            ],
            "in_progress": [
                {
                    "id": t.id,
                    "operation": t.operation,
                    "claimed_by": t.claimed_by,
                    "claimed_at": t.claimed_at,
                }
                for t in processing
            ],
        }

    def _get_session_context(self) -> Optional[Dict[str, Any]]:
        """Get active session context."""
        active = self.sessions.get_active()
        if not active:
            # Check for paused sessions
            paused = self.sessions.list_sessions(status=SessionStatus.PAUSED, limit=3)
            if paused:
                return {
                    "status": "no_active_session",
                    "paused_sessions": [
                        {
                            "id": s.id,
                            "last_active": s.last_active,
                            "current_task": s.current_task_id,
                            "notes": s.notes[:100] if s.notes else None,
                        }
                        for s in paused
                    ],
                }
            return None

        return self.sessions.get_context(active.id)

    def _get_notes_context(self) -> Dict[str, Any]:
        """Get notes requiring attention."""
        review_needed = self.notes.get_notes_requiring_review()
        uncertainties = self.notes.get_uncertainties()
        stats = self.notes.get_stats()

        return {
            "stats": stats,
            "human_review_needed": [
                {
                    "id": n.id,
                    "document": n.document,
                    "content": n.content[:200],
                    "priority": n.priority.value,
                }
                for n in review_needed[:5]
            ],
            "uncertainties": [
                {
                    "id": n.id,
                    "document": n.document,
                    "content": n.content[:200],
                }
                for n in uncertainties[:5]
            ],
        }

    def _get_research_context(self) -> Dict[str, Any]:
        """Get research status."""
        stats = self.research.get_stats()
        stale = self.research.get_stale()
        possibly_stale = self.research.check_freshness(max_age_days=30)

        return {
            "stats": stats,
            "stale_count": len(stale),
            "stale_items": [
                {"id": r.id, "topic": r.topic}
                for r in stale[:5]
            ],
            "may_need_refresh": [
                {"id": r["id"], "topic": r["topic"], "days_old": r["days_old"]}
                for r in possibly_stale[:5]
            ],
        }

    def _get_video_context(self) -> Dict[str, Any]:
        """Get video production context including scripts, render queue, and brand."""
        try:
            # Get video scripts
            scripts_dir = self.project.content_dir
            video_scripts = []
            for lang_dir in scripts_dir.iterdir():
                if lang_dir.is_dir():
                    script_path = lang_dir / "scripts"
                    if script_path.exists():
                        for script_file in script_path.glob("*.yaml"):
                            video_scripts.append({
                                "id": f"{lang_dir.name}/{script_file.stem}",
                                "path": str(script_file),
                                "language": lang_dir.name,
                            })

            # Get render queue status from MCP tools module
            try:
                from ..mcp.tools.video_render import _render_jobs
                render_stats = {
                    "total": len(_render_jobs),
                    "queued": sum(1 for j in _render_jobs.values() if j.get("status") == "queued"),
                    "rendering": sum(1 for j in _render_jobs.values() if j.get("status") == "rendering"),
                    "completed": sum(1 for j in _render_jobs.values() if j.get("status") == "completed"),
                    "failed": sum(1 for j in _render_jobs.values() if j.get("status") == "failed"),
                }
                active_renders = [
                    {"id": job_id, "script_id": job.get("script_id"), "progress": job.get("progress", 0)}
                    for job_id, job in _render_jobs.items()
                    if job.get("status") in ("queued", "rendering")
                ]
            except ImportError:
                render_stats = {"total": 0}
                active_renders = []

            # Get brand context for videos
            brand_context = {}
            if hasattr(self.project, 'brand_context'):
                brand = self.project.brand_context
                brand_context = {
                    "has_brand": True,
                    "primary_color": brand.get_color("brand.primary") if hasattr(brand, 'get_color') else None,
                    "logo_available": hasattr(brand, 'get_logo'),
                }
            else:
                brand_context = {"has_brand": False}

            return {
                "scripts": {
                    "count": len(video_scripts),
                    "scripts": video_scripts[:10],  # Limit to 10 for context size
                },
                "render_queue": {
                    "stats": render_stats,
                    "active_renders": active_renders[:5],
                },
                "brand": brand_context,
                "capabilities": {
                    "has_video_tools": True,
                    "available_tools": [
                        "plan_video_from_content",
                        "generate_video_script",
                        "suggest_scene_visuals",
                        "optimize_timing",
                        "validate_video_script",
                        "list_motion_components",
                        "suggest_transitions",
                        "apply_brand_to_video",
                        "start_video_render",
                        "get_render_status",
                    ],
                },
            }
        except Exception as e:
            return {"error": str(e), "capabilities": {"has_video_tools": True}}

    def _get_suggested_actions(self) -> List[Dict[str, Any]]:
        """Generate suggested actions based on current state."""
        suggestions = []

        # Check for high-priority pending tasks
        high_priority = [
            t for t in self.queue.list_tasks(status=TaskStatus.PENDING)
            if t.priority.value in ("high", "urgent")
        ]
        for task in high_priority[:3]:
            suggestions.append({
                "type": "process_task",
                "priority": "high",
                "reason": f"High priority task: {task.operation}",
                "action": f"Claim and process task {task.id}",
                "task_id": task.id,
            })

        # Check for notes requiring review
        review_notes = self.notes.get_notes_requiring_review()
        if len(review_notes) > 3:
            suggestions.append({
                "type": "review_notes",
                "priority": "medium",
                "reason": f"{len(review_notes)} notes require human review",
                "action": "Review and resolve notes, or escalate to human",
            })

        # Check for stale research
        stale_research = self.research.get_stale()
        for research in stale_research[:2]:
            suggestions.append({
                "type": "refresh_research",
                "priority": "low",
                "reason": f"Research on '{research.topic}' is stale",
                "action": "Refresh research and update affected documents",
                "research_id": research.id,
                "affects": research.affects_documents,
            })

        # Check for paused sessions
        paused = self.sessions.list_sessions(status=SessionStatus.PAUSED, limit=1)
        if paused:
            session = paused[0]
            suggestions.append({
                "type": "resume_session",
                "priority": "high",
                "reason": f"Paused session from {session.last_active}",
                "action": f"Resume session {session.id}",
                "session_id": session.id,
                "notes": session.notes,
            })

        # Check for video render queue
        try:
            from ..mcp.tools.video_render import _render_jobs
            queued_renders = [
                (job_id, job) for job_id, job in _render_jobs.items()
                if job.get("status") == "queued"
            ]
            if queued_renders:
                suggestions.append({
                    "type": "process_render_queue",
                    "priority": "medium",
                    "reason": f"{len(queued_renders)} video renders queued",
                    "action": "Monitor and process render queue",
                    "queued_jobs": len(queued_renders),
                })
        except ImportError:
            pass

        return suggestions

    def get_document_context(self, document_path: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a specific document.

        Includes notes, research, related tasks, and usage info.
        """
        doc_notes = self.notes.get_document_notes(document_path)
        related_research = self.research.get_research_for_document(document_path)

        # Find tasks related to this document
        related_tasks = []
        for task in self.queue.list_tasks(limit=50):
            for sel in task.selections:
                if sel.path == document_path:
                    related_tasks.append({
                        "id": task.id,
                        "operation": task.operation,
                        "status": task.status.value,
                    })
                    break

        # Get publication usage
        try:
            from ..publications import PublicationRegistry
            registry = PublicationRegistry(self.project)
            usage = registry.get_document_usage(Path(document_path))
        except Exception:
            usage = {"used_in": [], "usage_count": 0}

        return {
            "document": document_path,
            "notes": doc_notes,
            "research": [
                {
                    "id": r.id,
                    "topic": r.topic,
                    "status": r.status.value,
                    "updated_at": r.updated_at,
                }
                for r in related_research
            ],
            "related_tasks": related_tasks,
            "publications": usage,
        }

    def get_publication_context(self, publication_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a publication."""
        try:
            from ..publications import PublicationRegistry, PublicationTracker

            registry = PublicationRegistry(self.project)
            tracker = PublicationTracker(self.project, registry)

            pub = registry.get(publication_id)
            if not pub:
                return {"error": f"Publication not found: {publication_id}"}

            status = registry.get_publication_status(publication_id)
            translation_status = tracker.get_translation_status(publication_id)

            # Get notes for all components
            all_notes = []
            for comp in pub.get_all_components():
                doc_notes = self.notes.list_notes(
                    document=str(comp.source),
                    status=NoteStatus.OPEN,
                )
                all_notes.extend(doc_notes)

            return {
                "publication": pub.to_dict(),
                "status": status,
                "translation_status": translation_status,
                "open_notes": len(all_notes),
                "notes_by_priority": {
                    "critical": len([n for n in all_notes if n.priority.value == "critical"]),
                    "high": len([n for n in all_notes if n.priority.value == "high"]),
                    "medium": len([n for n in all_notes if n.priority.value == "medium"]),
                    "low": len([n for n in all_notes if n.priority.value == "low"]),
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def start_session(
        self,
        task_id: Optional[str] = None,
        resume_from: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start or resume an AI session.

        Args:
            task_id: Optional task to associate with session
            resume_from: Optional session ID to resume

        Returns:
            Session context
        """
        if resume_from:
            session = self.sessions.resume(resume_from)
            if session:
                return {
                    "action": "resumed",
                    "session": self.sessions.get_context(session.id),
                }
            return {"error": f"Could not resume session: {resume_from}"}

        # Create new session
        session = self.sessions.create(task_id)

        # If task_id provided, claim it
        if task_id:
            self.queue.claim(task_id, claimed_by=f"session_{session.id}")

        return {
            "action": "created",
            "session_id": session.id,
            "context": self.get_full_context(),
        }

    def record_progress(
        self,
        session_id: str,
        step: str,
        completed: bool = False,
    ) -> Dict[str, Any]:
        """Record progress in a session."""
        session = self.sessions.add_progress(session_id, step, completed)
        if session:
            return {"success": True, "progress": len(session.progress)}
        return {"error": f"Session not found: {session_id}"}

    def record_change(
        self,
        session_id: str,
        file: str,
        change_type: str = "modified",
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Record a file change in the session."""
        session = self.sessions.record_change(
            session_id, file, change_type, sections
        )
        if session:
            return {"success": True, "changes_count": len(session.changes_made)}
        return {"error": f"Session not found: {session_id}"}

    def record_decision(
        self,
        session_id: str,
        question: str,
        decision: str,
        reasoning: str,
        scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a decision in the session."""
        session = self.sessions.record_decision(
            session_id, question, decision, reasoning, scope
        )
        if session:
            return {"success": True, "decisions_count": len(session.decisions)}
        return {"error": f"Session not found: {session_id}"}

    def add_note(
        self,
        note_type: str,
        content: str,
        document: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add an AI note."""
        note = self.notes.add(
            note_type=NoteType(note_type),
            content=content,
            document=document,
            location=location,
            priority=priority,
            session_id=session_id,
        )
        return {"success": True, "note_id": note.id}

    def store_research(
        self,
        topic: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        affects_documents: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store research findings."""
        item = self.research.store(
            topic=topic,
            content=content,
            sources=sources,
            affects_documents=affects_documents,
            session_id=session_id,
        )
        return {"success": True, "research_id": item.id}

    def complete_session(
        self,
        session_id: str,
        summary: str,
    ) -> Dict[str, Any]:
        """Complete a session."""
        session = self.sessions.complete(session_id, summary)
        if session:
            # Also complete associated task if any
            if session.current_task_id:
                files_modified = [c.file for c in session.changes_made]
                self.queue.complete(
                    session.current_task_id,
                    summary=summary,
                    files_modified=files_modified,
                )
            return {"success": True, "session_id": session.id}
        return {"error": f"Session not found: {session_id}"}
