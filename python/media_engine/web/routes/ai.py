"""
AI Processing Routes

REST API endpoints for AI-assisted content processing.
"""

from typing import TYPE_CHECKING, Callable, List, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


class ContentSelectionModel(BaseModel):
    """Request model for content selection."""

    path: str
    content: str
    title: str
    content_type: str = "document"
    target_id: Optional[str] = None
    notes: Optional[List[dict]] = None
    metadata: Optional[dict] = None


class AIProcessRequestModel(BaseModel):
    """Request model for AI processing."""

    operation: str
    selections: List[ContentSelectionModel]
    instructions: str = ""
    target_language: Optional[str] = None
    options: Optional[dict] = None


class AIConfigUpdateModel(BaseModel):
    """Request model for updating AI config."""

    api_key: Optional[str] = None
    backend: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class TaskSubmitModel(BaseModel):
    """Request model for submitting a task."""

    operation: str
    selections: List[ContentSelectionModel]
    instructions: str = ""
    priority: str = "normal"
    target_language: Optional[str] = None


def register_ai_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register AI processing routes."""

    @router.get("/api/ai/config")
    async def get_ai_config_endpoint():
        """Get current AI configuration (without API key)."""
        from ...ai.config import get_ai_config, is_ai_configured

        project = get_project()
        config = get_ai_config(project)

        return {
            "configured": is_ai_configured(),
            "backend": config.backend.value,
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "has_api_key": config.api_key is not None,
        }

    @router.post("/api/ai/config")
    async def update_ai_config_endpoint(request: AIConfigUpdateModel):
        """Update AI configuration."""
        from ...ai.config import save_ai_config

        save_ai_config(
            api_key=request.api_key,
            backend=request.backend,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Broadcast config update
        await manager.broadcast({"type": "ai_config_updated"})

        return {"status": "updated"}

    @router.post("/api/ai/process")
    async def process_content_endpoint(request: AIProcessRequestModel):
        """Process content through AI."""
        from ...ai.client import AIClient
        from ...ai.types import AIOperation, AIProcessRequest, ContentSelection

        project = get_project()
        client = AIClient(project)

        # Convert request models to domain types
        selections = [
            ContentSelection(
                path=s.path,
                content=s.content,
                title=s.title,
                content_type=s.content_type,
                target_id=s.target_id,
                notes=s.notes or [],
                metadata=s.metadata or {},
            )
            for s in request.selections
        ]

        ai_request = AIProcessRequest(
            operation=AIOperation(request.operation),
            selections=selections,
            instructions=request.instructions,
            target_language=request.target_language,
            options=request.options or {},
        )

        result = await client.process(ai_request)

        # Broadcast to WebSocket for real-time updates
        await manager.broadcast(
            {
                "type": "ai_process_complete",
                "request_id": result.request_id,
                "status": result.status,
            }
        )

        return {
            "request_id": result.request_id,
            "status": result.status,
            "results": result.results,
            "usage": result.usage,
            "duration_ms": result.duration_ms,
            "error": result.error,
        }

    @router.get("/api/ai/operations")
    async def list_operations():
        """List available AI operations."""
        from ...ai.types import AIOperation

        descriptions = {
            "improve": "Improve clarity, grammar, and flow",
            "translate": "Translate to another language",
            "analyze": "Get feedback and suggestions without changes",
            "summarize": "Create a concise summary",
            "expand": "Expand and elaborate on content",
            "simplify": "Simplify language for broader audience",
            "proofread": "Check spelling and grammar",
        }

        return {
            "operations": [
                {
                    "id": op.value,
                    "name": op.name.replace("_", " ").title(),
                    "description": descriptions.get(op.value, "Process content"),
                }
                for op in AIOperation
            ]
        }

    @router.get("/api/ai/models")
    async def list_models():
        """List available AI models."""
        return {
            "models": [
                {
                    "id": "claude-sonnet-4-20250514",
                    "name": "Claude Sonnet 4",
                    "description": "Best balance of speed and quality",
                },
                {
                    "id": "claude-opus-4-20250514",
                    "name": "Claude Opus 4",
                    "description": "Highest quality, slower",
                },
                {
                    "id": "claude-3-5-haiku-20241022",
                    "name": "Claude 3.5 Haiku",
                    "description": "Fastest, best for simple tasks",
                },
            ]
        }

    @router.get("/api/ai/backends")
    async def list_backends():
        """List available AI backends."""
        from ...ai.types import AIBackend

        return {
            "backends": [
                {
                    "id": AIBackend.ANTHROPIC.value,
                    "name": "Anthropic API",
                    "description": "Direct API access (requires API key)",
                    "requires_key": True,
                },
                {
                    "id": AIBackend.CLAUDE_CODE.value,
                    "name": "Claude Code",
                    "description": "Use Claude Code CLI (no API key needed)",
                    "requires_key": False,
                },
            ]
        }

    # ===== Task Queue Endpoints for Claude Code Integration =====

    @router.post("/api/ai/tasks")
    async def submit_task(request: TaskSubmitModel):
        """
        Submit a task to the AI queue for Claude Code processing.

        Tasks are queued and processed by Claude Code with full access
        to tools, skills, and file editing capabilities.
        """
        from ...ai.queue import TaskQueue

        project = get_project()
        queue = TaskQueue(project.root)

        # Convert selections to dict format
        selections = [
            {
                "path": s.path,
                "title": s.title,
                "content": s.content,
                "content_type": s.content_type,
                "target_id": s.target_id,
                "notes": s.notes or [],
                "metadata": s.metadata or {},
            }
            for s in request.selections
        ]

        task = queue.submit(
            operation=request.operation,
            instructions=request.instructions,
            selections=selections,
            priority=request.priority,
            target_language=request.target_language,
        )

        # Broadcast task submission
        await manager.broadcast(
            {
                "type": "ai_task_submitted",
                "task_id": task.id,
                "operation": task.operation,
            }
        )

        return {
            "task_id": task.id,
            "status": task.status.value,
            "operation": task.operation,
            "selections_count": len(task.selections),
            "priority": task.priority.value,
            "created_at": task.created_at,
        }

    @router.get("/api/ai/tasks")
    async def list_tasks(status: Optional[str] = None, limit: int = 50):
        """
        List AI tasks in the queue.

        Query params:
            status: Filter by status (pending, claimed, processing, completed, failed)
            limit: Maximum number of tasks to return
        """
        from ...ai.queue import TaskQueue, TaskStatus

        project = get_project()
        queue = TaskQueue(project.root)

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                pass

        tasks = queue.list_tasks(status=status_filter, limit=limit)

        return {
            "tasks": [
                {
                    "id": t.id,
                    "operation": t.operation,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "instructions": t.instructions[:200] + "..."
                    if len(t.instructions) > 200
                    else t.instructions,
                    "selections": [
                        {
                            "path": s.path,
                            "title": s.title,
                            "notes_count": len(s.notes),
                        }
                        for s in t.selections
                    ],
                    "created_at": t.created_at,
                    "completed_at": t.completed_at,
                    "summary": t.summary,
                    "files_modified": t.files_modified,
                    "error": t.error,
                }
                for t in tasks
            ],
            "total": len(tasks),
            "stats": queue.get_stats(),
        }

    @router.get("/api/ai/tasks/{task_id}")
    async def get_task(task_id: str):
        """Get details of a specific task."""
        from ...ai.queue import TaskQueue

        project = get_project()
        queue = TaskQueue(project.root)
        task = queue.get_task(task_id)

        if not task:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return task.to_dict()

    @router.post("/api/ai/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str):
        """Cancel a pending task."""
        from ...ai.queue import TaskQueue

        project = get_project()
        queue = TaskQueue(project.root)

        if queue.cancel(task_id):
            await manager.broadcast(
                {
                    "type": "ai_task_cancelled",
                    "task_id": task_id,
                }
            )
            return {"status": "cancelled", "task_id": task_id}

        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} not found or cannot be cancelled",
        )

    @router.delete("/api/ai/tasks/{task_id}")
    async def delete_task(task_id: str):
        """
        Delete a completed, failed, or cancelled task.

        Only tasks with terminal status can be deleted.
        """
        from ...ai.queue import TaskQueue

        project = get_project()
        queue = TaskQueue(project.root)

        if queue.delete(task_id):
            await manager.broadcast(
                {
                    "type": "ai_task_deleted",
                    "task_id": task_id,
                }
            )
            return {"status": "deleted", "task_id": task_id}

        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} not found or cannot be deleted (only completed/failed/cancelled tasks can be deleted)",
        )

    @router.get("/api/ai/queue/stats")
    async def get_queue_stats():
        """Get AI task queue statistics."""
        from ...ai.queue import TaskQueue

        project = get_project()
        queue = TaskQueue(project.root)

        return queue.get_stats()

    # ===== AI Context & Session Endpoints =====

    @router.get("/api/ai/context")
    async def get_ai_context():
        """
        Get comprehensive AI context for starting/continuing work.

        Returns project status, work queue, sessions, notes, and research.
        """
        from ...ai import AIContext

        project = get_project()
        context = AIContext(project)
        return context.get_full_context()

    @router.get("/api/ai/context/document/{path:path}")
    async def get_document_context(path: str):
        """Get AI context for a specific document."""
        from ...ai import AIContext

        project = get_project()
        context = AIContext(project)
        return context.get_document_context(path)

    @router.get("/api/ai/sessions")
    async def list_sessions(status: Optional[str] = None):
        """List AI sessions."""
        from ...ai import SessionManager

        project = get_project()
        sessions = SessionManager(project.root)
        all_sessions = sessions.list_sessions()

        if status:
            all_sessions = [s for s in all_sessions if s.status == status]

        return {
            "sessions": [
                {
                    "id": s.id,
                    "status": s.status,
                    "task_id": s.task_id,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "steps_count": len(s.steps),
                    "changes_count": len(s.changes),
                    "decisions_count": len(s.decisions),
                    "summary": s.summary,
                }
                for s in all_sessions
            ],
            "total": len(all_sessions),
        }

    @router.get("/api/ai/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session details."""
        from ...ai import SessionManager

        project = get_project()
        sessions = SessionManager(project.root)
        session = sessions.get_session(session_id)

        if not session:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return {
            "id": session.id,
            "status": session.status,
            "task_id": session.task_id,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "summary": session.summary,
            "notes": session.notes,
            "steps": [
                {
                    "description": s.description,
                    "completed": s.completed,
                    "timestamp": s.timestamp,
                }
                for s in session.steps
            ],
            "changes": [
                {
                    "file": c.file,
                    "change_type": c.change_type,
                    "timestamp": c.timestamp,
                    "sections": c.sections,
                }
                for c in session.changes
            ],
            "decisions": [
                {
                    "question": d.question,
                    "decision": d.decision,
                    "reasoning": d.reasoning,
                    "timestamp": d.timestamp,
                    "scope": d.scope,
                }
                for d in session.decisions
            ],
        }

    @router.get("/api/ai/notes")
    async def get_ai_notes(
        document: Optional[str] = None,
        note_type: Optional[str] = None,
        status: str = "open",
    ):
        """Get AI notes with filters."""
        from ...ai import NotesManager, NoteStatus, NoteType

        project = get_project()
        notes_mgr = NotesManager(project.root)

        nt = NoteType(note_type) if note_type else None
        st = NoteStatus(status) if status else None

        notes = notes_mgr.list_notes(
            document=document,
            note_type=nt,
            status=st,
        )

        return {
            "notes": [n.to_dict() for n in notes],
            "total": len(notes),
        }

    @router.post("/api/ai/notes/{note_id}/resolve")
    async def resolve_ai_note(note_id: str, resolution: str = ""):
        """Resolve an AI note."""
        from ...ai import NotesManager

        project = get_project()
        notes_mgr = NotesManager(project.root)
        note = notes_mgr.resolve(note_id, resolution)

        if note:
            await manager.broadcast({
                "type": "ai_note_resolved",
                "note_id": note_id,
            })
            return {"success": True, "note_id": note.id}

        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

    @router.get("/api/ai/research")
    async def get_research(
        topic: Optional[str] = None,
        affects_document: Optional[str] = None,
    ):
        """Get stored research."""
        from ...ai import ResearchStore

        project = get_project()
        store = ResearchStore(project.root)

        if topic:
            items = store.search(topic)
        elif affects_document:
            items = store.get_research_for_document(affects_document)
        else:
            items = store.list_items()

        return {
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
            "total": len(items),
        }

    @router.get("/api/ai/decisions")
    async def get_decisions(scope: Optional[str] = None, limit: int = 20):
        """Get past decisions for consistency."""
        from ...ai import SessionManager

        project = get_project()
        sessions = SessionManager(project.root)
        decisions = sessions.get_all_decisions(scope)[:limit]

        return {
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
            "total": len(decisions),
        }
