"""
AI Processing Tools for MCP

Provides AI-assisted content processing for MCP clients like Claude Code.
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer


def register_ai_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register AI processing MCP tools."""

    @mcp.tool()
    async def ai_process_content(
        operation: str,
        paths: str,
        instructions: str = "",
        target_language: str = None,
    ) -> str:
        """
        Process content through AI for improvement, translation, or analysis.

        Args:
            operation: Type of operation:
                - "improve": Improve clarity and quality
                - "translate": Translate to target language
                - "analyze": Get feedback without changes
                - "summarize": Create summary
                - "expand": Expand and elaborate
                - "simplify": Simplify language
                - "proofread": Check grammar/spelling
            paths: Comma-separated document paths to process (relative to content/)
            instructions: Custom instructions for the AI
            target_language: Target language for translation (e.g., "no", "es", "de")

        Returns:
            JSON with processed content and change summaries.

        Example:
            ai_process_content(
                operation="improve",
                paths="en/chapters/01_intro.md",
                instructions="Make it more engaging and add examples"
            )
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.client import AIClient
        from ...ai.types import AIOperation, AIProcessRequest, ContentSelection

        project = server_instance.project

        # Validate operation
        try:
            op = AIOperation(operation)
        except ValueError:
            valid_ops = [o.value for o in AIOperation]
            return json.dumps(
                {"error": f"Invalid operation. Valid: {valid_ops}"}, indent=2
            )

        # Parse paths
        path_list = [p.strip() for p in paths.split(",")]

        # Build selections
        selections = []

        for path in path_list:
            # Try to find the document
            doc_path = project.content_dir / path
            if not doc_path.exists():
                doc_path = project.content_dir / path.lstrip("/")

            if not doc_path.exists():
                # Try absolute path
                from pathlib import Path

                abs_path = Path(path)
                if abs_path.exists():
                    doc_path = abs_path

            if not doc_path.exists():
                continue

            content = doc_path.read_text(encoding="utf-8")
            title = doc_path.stem.replace("_", " ").title()

            # Get attached notes if available
            notes_dicts = []
            try:
                from ...notes import NotesRegistry

                notes_registry = NotesRegistry(project)
                rel_path = str(doc_path.relative_to(project.content_dir))
                notes = notes_registry.get_for_target(rel_path)
                notes_dicts = [
                    {"text": n.text, "priority": n.priority.value} for n in notes
                ]
            except Exception:
                pass

            selections.append(
                ContentSelection(
                    path=path,
                    content=content,
                    title=title,
                    content_type="document",
                    notes=notes_dicts,
                )
            )

        if not selections:
            return json.dumps(
                {"error": f"No valid documents found for paths: {paths}"}, indent=2
            )

        # Create request
        request = AIProcessRequest(
            operation=op,
            selections=selections,
            instructions=instructions,
            target_language=target_language,
        )

        # Process
        client = AIClient(project)
        result = await client.process(request)

        return json.dumps(
            {
                "request_id": result.request_id,
                "status": result.status,
                "results": result.results,
                "duration_ms": result.duration_ms,
                "usage": result.usage,
                "error": result.error,
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_config_status() -> str:
        """
        Check AI configuration status.

        Returns:
            JSON with configuration status and backend info.
        """
        from ...ai.config import get_ai_config, is_ai_configured

        project = server_instance.project
        config = get_ai_config(project)

        return json.dumps(
            {
                "configured": is_ai_configured(),
                "backend": config.backend.value,
                "model": config.model,
                "max_tokens": config.max_tokens,
                "has_api_key": config.api_key is not None,
                "note": "Set ANTHROPIC_API_KEY env var or use Claude Code backend",
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_list_operations() -> str:
        """
        List available AI operations.

        Returns:
            JSON with available operations and their descriptions.
        """
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

        return json.dumps(
            {
                "operations": [
                    {
                        "id": op.value,
                        "name": op.name.replace("_", " ").title(),
                        "description": descriptions.get(op.value, "Process content"),
                    }
                    for op in AIOperation
                ]
            },
            indent=2,
        )

    # ===== Task Queue Tools for Claude Code Integration =====

    @mcp.tool()
    async def ai_submit_task(
        operation: str,
        paths: str,
        instructions: str = "",
        priority: str = "normal",
        target_language: str = None,
    ) -> str:
        """
        Submit a task to the AI queue for Claude Code processing.

        Tasks are queued and can be processed by Claude Code with full
        access to tools, skills, and file editing capabilities.

        Args:
            operation: Type of operation (improve, translate, analyze, etc.)
            paths: Comma-separated document paths (relative to content/)
            instructions: Detailed instructions for Claude Code
            priority: Task priority: low, normal, high, urgent
            target_language: Target language for translation

        Returns:
            JSON with task ID and status.

        Example:
            ai_submit_task(
                operation="improve",
                paths="en/chapters/01_intro.md",
                instructions="Make it more engaging, add examples",
                priority="high"
            )
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue

        project = server_instance.project

        # Parse paths and build selections
        path_list = [p.strip() for p in paths.split(",")]
        selections = []

        for path in path_list:
            doc_path = project.content_dir / path
            if not doc_path.exists():
                doc_path = project.content_dir / path.lstrip("/")

            if not doc_path.exists():
                from pathlib import Path
                abs_path = Path(path)
                if abs_path.exists():
                    doc_path = abs_path

            if not doc_path.exists():
                continue

            content = doc_path.read_text(encoding="utf-8")
            title = doc_path.stem.replace("_", " ").title()

            # Get attached notes
            notes_dicts = []
            try:
                from ...notes import NotesRegistry
                notes_registry = NotesRegistry(project)
                rel_path = str(doc_path.relative_to(project.content_dir))
                notes = notes_registry.get_for_target(rel_path)
                notes_dicts = [
                    {"text": n.text, "priority": n.priority.value} for n in notes
                ]
            except Exception:
                pass

            selections.append({
                "path": str(doc_path.relative_to(project.root)),
                "title": title,
                "content": content,
                "content_type": "document",
                "notes": notes_dicts,
            })

        if not selections:
            return json.dumps(
                {"error": f"No valid documents found for paths: {paths}"}, indent=2
            )

        # Submit to queue
        queue = TaskQueue(project.root)
        task = queue.submit(
            operation=operation,
            instructions=instructions,
            selections=selections,
            priority=priority,
            target_language=target_language,
        )

        return json.dumps(
            {
                "task_id": task.id,
                "status": task.status.value,
                "operation": task.operation,
                "selections_count": len(task.selections),
                "priority": task.priority.value,
                "message": f"Task {task.id} submitted. Use ai_list_tasks to view pending tasks.",
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_list_tasks(
        status: str = None,
        limit: int = 20,
    ) -> str:
        """
        List AI tasks in the queue.

        Args:
            status: Filter by status: pending, claimed, processing, completed, failed
            limit: Maximum number of tasks to return (default 20)

        Returns:
            JSON with list of tasks.

        Example:
            ai_list_tasks(status="pending")  # Show tasks waiting to be processed
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue, TaskStatus

        queue = TaskQueue(server_instance.project.root)

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                valid = [s.value for s in TaskStatus]
                return json.dumps(
                    {"error": f"Invalid status. Valid: {valid}"}, indent=2
                )

        tasks = queue.list_tasks(status=status_filter, limit=limit)

        return json.dumps(
            {
                "tasks": [
                    {
                        "id": t.id,
                        "operation": t.operation,
                        "status": t.status.value,
                        "priority": t.priority.value,
                        "instructions": t.instructions[:100] + "..." if len(t.instructions) > 100 else t.instructions,
                        "selections": [
                            {"path": s.path, "title": s.title, "notes_count": len(s.notes)}
                            for s in t.selections
                        ],
                        "created_at": t.created_at,
                        "target_language": t.target_language,
                    }
                    for t in tasks
                ],
                "total": len(tasks),
                "stats": queue.get_stats(),
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_get_task(task_id: str) -> str:
        """
        Get details of a specific task including full content.

        Args:
            task_id: The task ID to retrieve

        Returns:
            JSON with full task details including content.

        Example:
            ai_get_task(task_id="abc12345")
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue

        queue = TaskQueue(server_instance.project.root)
        task = queue.get_task(task_id)

        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        return json.dumps(task.to_dict(), indent=2)

    @mcp.tool()
    async def ai_claim_task(task_id: str) -> str:
        """
        Claim a pending task for processing.

        Call this before starting to process a task. This marks the task
        as claimed so other agents don't process it simultaneously.

        Args:
            task_id: The task ID to claim

        Returns:
            JSON with claimed task details.

        Example:
            ai_claim_task(task_id="abc12345")
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue

        queue = TaskQueue(server_instance.project.root)
        task = queue.claim(task_id, claimed_by="claude_code")

        if not task:
            return json.dumps(
                {"error": f"Task {task_id} not found or already claimed"}, indent=2
            )

        # Mark as processing
        queue.start_processing(task_id)

        return json.dumps(
            {
                "task_id": task.id,
                "status": "processing",
                "operation": task.operation,
                "instructions": task.instructions,
                "target_language": task.target_language,
                "selections": [
                    {
                        "path": s.path,
                        "title": s.title,
                        "content": s.content,
                        "notes": s.notes,
                    }
                    for s in task.selections
                ],
                "message": "Task claimed. Process the content and call ai_complete_task when done.",
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_complete_task(
        task_id: str,
        summary: str,
        files_modified: str = "",
    ) -> str:
        """
        Mark a task as completed after processing.

        Call this after you've processed the task and made any file changes.

        Args:
            task_id: The task ID to complete
            summary: Summary of changes made (shown to user in dashboard)
            files_modified: Comma-separated list of files that were modified

        Returns:
            JSON confirming task completion.

        Example:
            ai_complete_task(
                task_id="abc12345",
                summary="Improved clarity in intro section, added 2 examples",
                files_modified="content/en/chapters/01_intro.md"
            )
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue

        queue = TaskQueue(server_instance.project.root)

        files_list = [f.strip() for f in files_modified.split(",") if f.strip()]

        task = queue.complete(
            task_id=task_id,
            summary=summary,
            files_modified=files_list,
        )

        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        return json.dumps(
            {
                "task_id": task.id,
                "status": "completed",
                "summary": summary,
                "files_modified": files_list,
                "completed_at": task.completed_at,
                "message": "Task completed successfully. Dashboard will show results.",
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_fail_task(task_id: str, error: str) -> str:
        """
        Mark a task as failed.

        Call this if you cannot complete the task due to an error.

        Args:
            task_id: The task ID that failed
            error: Error message explaining what went wrong

        Returns:
            JSON confirming task failure.

        Example:
            ai_fail_task(
                task_id="abc12345",
                error="Could not find referenced document"
            )
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue

        queue = TaskQueue(server_instance.project.root)
        task = queue.fail(task_id=task_id, error=error)

        if not task:
            return json.dumps({"error": f"Task {task_id} not found"}, indent=2)

        return json.dumps(
            {
                "task_id": task.id,
                "status": "failed",
                "error": error,
                "message": "Task marked as failed.",
            },
            indent=2,
        )

    @mcp.tool()
    async def ai_queue_stats() -> str:
        """
        Get AI task queue statistics.

        Returns:
            JSON with queue stats (pending, processing, completed counts).
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...ai.queue import TaskQueue

        queue = TaskQueue(server_instance.project.root)
        stats = queue.get_stats()

        return json.dumps(
            {
                "stats": stats,
                "message": f"{stats['pending']} tasks pending, {stats['processing']} processing",
            },
            indent=2,
        )
