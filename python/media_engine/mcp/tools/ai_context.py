"""
MCP tools for AI context and session management.

Provides comprehensive context and work management for AI agents.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from mcp.server import Server

    from ..server import MediaEngineMCP


def register_ai_context_tools(mcp: "Server", engine: "MediaEngineMCP") -> None:
    """Register AI context MCP tools."""

    @mcp.tool()
    async def get_ai_context() -> Dict[str, Any]:
        """
        Get comprehensive AI context.

        Returns everything needed to start or continue AI work:
        - Project status
        - Work queue with pending tasks
        - Active/paused sessions
        - Notes requiring attention
        - Research status
        - Suggested actions

        Use this at the start of work to understand what needs doing.
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.get_full_context()

    @mcp.tool()
    async def get_document_context(path: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a specific document.

        Args:
            path: Document path (relative to project root)

        Returns context including:
        - Notes attached to the document
        - Related research
        - Related tasks in queue
        - Publications using this document
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.get_document_context(path)

    @mcp.tool()
    async def start_ai_session(
        task_id: Optional[str] = None,
        resume_from: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start or resume an AI work session.

        Args:
            task_id: Optional task to associate with session
            resume_from: Optional session ID to resume

        Sessions track:
        - Progress through work steps
        - Changes made to files
        - Decisions and reasoning
        - Blockers encountered
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.start_session(task_id, resume_from)

    @mcp.tool()
    async def record_session_progress(
        session_id: str,
        step: str,
        completed: bool = False,
    ) -> Dict[str, Any]:
        """
        Record a progress step in the current session.

        Args:
            session_id: Current session ID
            step: Description of the step
            completed: Whether step is complete
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.record_progress(session_id, step, completed)

    @mcp.tool()
    async def record_session_change(
        session_id: str,
        file: str,
        change_type: str = "modified",
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Record a file change in the session.

        Args:
            session_id: Current session ID
            file: File path that was changed
            change_type: Type of change (created, modified, deleted)
            sections: Specific sections that were modified
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.record_change(session_id, file, change_type, sections)

    @mcp.tool()
    async def record_decision(
        session_id: str,
        question: str,
        decision: str,
        reasoning: str,
        scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a decision made during the session.

        Args:
            session_id: Current session ID
            question: The question or choice faced
            decision: The decision made
            reasoning: Why this decision was made
            scope: Document path or 'project' for project-wide decisions
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.record_decision(session_id, question, decision, reasoning, scope)

    @mcp.tool()
    async def complete_ai_session(
        session_id: str,
        summary: str,
    ) -> Dict[str, Any]:
        """
        Complete an AI session.

        Args:
            session_id: Session ID to complete
            summary: Summary of work done

        This also completes any associated task in the queue.
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.complete_session(session_id, summary)

    @mcp.tool()
    async def pause_ai_session(
        session_id: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Pause an AI session for later resumption.

        Args:
            session_id: Session ID to pause
            notes: Notes for the next session
        """
        from ...ai import SessionManager

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        sessions = SessionManager(project.root)
        session = sessions.pause(session_id, notes)
        if session:
            return {"success": True, "session_id": session.id, "status": "paused"}
        return {"error": f"Could not pause session: {session_id}"}

    @mcp.tool()
    async def add_ai_note(
        note_type: str,
        content: str,
        document: Optional[str] = None,
        section: Optional[str] = None,
        line: Optional[int] = None,
        priority: str = "medium",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a note for humans or future AI sessions.

        Args:
            note_type: Type of note - uncertainty, suggestion, human_review, decision, todo, warning, info
            content: Note content
            document: Document path (None for project-level)
            section: Section within document
            line: Line number
            priority: low, medium, high, critical
            session_id: Current session ID
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        location = None
        if section or line:
            location = {"section": section, "line": line}

        context = AIContext(project)
        return context.add_note(
            note_type=note_type,
            content=content,
            document=document,
            location=location,
            priority=priority,
            session_id=session_id,
        )

    @mcp.tool()
    async def get_ai_notes(
        document: Optional[str] = None,
        note_type: Optional[str] = None,
        status: str = "open",
    ) -> Dict[str, Any]:
        """
        Get AI notes with optional filters.

        Args:
            document: Filter by document path
            note_type: Filter by type
            status: Filter by status (open, resolved, dismissed)
        """
        from ...ai import NotesManager, NoteStatus, NoteType

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        notes_mgr = NotesManager(project.root)

        nt = NoteType(note_type) if note_type else None
        st = NoteStatus(status) if status else None

        notes = notes_mgr.list_notes(
            document=document,
            note_type=nt,
            status=st,
        )

        return {
            "total": len(notes),
            "notes": [n.to_dict() for n in notes],
        }

    @mcp.tool()
    async def resolve_ai_note(
        note_id: str,
        resolution: str,
    ) -> Dict[str, Any]:
        """
        Resolve an AI note.

        Args:
            note_id: Note ID to resolve
            resolution: How the note was resolved
        """
        from ...ai import NotesManager

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        notes_mgr = NotesManager(project.root)
        note = notes_mgr.resolve(note_id, resolution)
        if note:
            return {"success": True, "note_id": note.id}
        return {"error": f"Note not found: {note_id}"}

    @mcp.tool()
    async def store_research(
        topic: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        affects_documents: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store research findings for future reference.

        Args:
            topic: Research topic/title
            content: Research content (markdown)
            sources: List of source URLs/references
            affects_documents: Documents this research informs
            session_id: Current session ID
        """
        from ...ai import AIContext

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        context = AIContext(project)
        return context.store_research(
            topic=topic,
            content=content,
            sources=sources,
            affects_documents=affects_documents,
            session_id=session_id,
        )

    @mcp.tool()
    async def get_research(
        topic: Optional[str] = None,
        affects_document: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get stored research.

        Args:
            topic: Search by topic
            affects_document: Filter by affected document
        """
        from ...ai import ResearchStore

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        store = ResearchStore(project.root)

        if topic:
            items = store.search(topic)
        elif affects_document:
            items = store.get_research_for_document(affects_document)
        else:
            items = store.list_items()

        return {
            "total": len(items),
            "items": [
                {
                    "id": i.id,
                    "topic": i.topic,
                    "status": i.status.value,
                    "updated_at": i.updated_at,
                    "affects_documents": i.affects_documents,
                    "content_preview": i.content[:500] if i.content else "",
                }
                for i in items
            ],
        }

    @mcp.tool()
    async def get_past_decisions(
        scope: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get past decisions for consistency.

        Args:
            scope: Filter by scope (document path or 'project')
            limit: Maximum decisions to return
        """
        from ...ai import SessionManager

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        sessions = SessionManager(project.root)
        decisions = sessions.get_all_decisions(scope)[:limit]

        return {
            "total": len(decisions),
            "decisions": [
                {
                    "question": d.question,
                    "decision": d.decision,
                    "reasoning": d.reasoning,
                    "timestamp": d.timestamp,
                    "scope": d.scope,
                }
                for d in decisions
            ],
        }

    @mcp.tool()
    async def get_work_queue(
        status: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get AI work queue.

        Args:
            status: Filter by status (pending, claimed, processing, completed, failed)
            limit: Maximum tasks to return
        """
        from ...ai import TaskQueue, TaskStatus

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        queue = TaskQueue(project.root)

        st = TaskStatus(status) if status else None
        tasks = queue.list_tasks(status=st, limit=limit)
        stats = queue.get_stats()

        return {
            "stats": stats,
            "tasks": [t.to_dict() for t in tasks],
        }

    @mcp.tool()
    async def claim_task(
        task_id: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Claim a task from the queue.

        Args:
            task_id: Task ID to claim
            session_id: Optional session ID
        """
        from ...ai import TaskQueue

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        queue = TaskQueue(project.root)
        claimed_by = f"session_{session_id}" if session_id else "claude_code"
        task = queue.claim(task_id, claimed_by)

        if task:
            return {"success": True, "task": task.to_dict()}
        return {"error": f"Could not claim task: {task_id}"}

    @mcp.tool()
    async def complete_task(
        task_id: str,
        summary: str,
        files_modified: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID
            summary: Summary of what was done
            files_modified: List of files that were modified
        """
        from ...ai import TaskQueue

        project = engine.project
        if not project:
            return {"error": "No project loaded"}

        queue = TaskQueue(project.root)
        task = queue.complete(task_id, summary, files_modified)

        if task:
            return {"success": True, "task_id": task.id}
        return {"error": f"Could not complete task: {task_id}"}
