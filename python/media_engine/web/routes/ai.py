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
