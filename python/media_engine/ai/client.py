"""
AI Client

Handles AI processing through configured backend.
"""

import time
import uuid
from typing import TYPE_CHECKING

from .config import get_ai_config
from .types import (
    AIBackend,
    AIProcessRequest,
    AIProcessResult,
    ContentResult,
)

if TYPE_CHECKING:
    from ..core.project import Project


class AIClient:
    """Client for AI-assisted content processing."""

    def __init__(self, project: "Project"):
        self.project = project
        self.config = get_ai_config(project)

    async def process(self, request: AIProcessRequest) -> AIProcessResult:
        """
        Process content through the configured AI backend.

        Args:
            request: The processing request

        Returns:
            Processing result with updated content
        """
        start = time.time()
        request_id = str(uuid.uuid4())[:8]

        try:
            if self.config.backend == AIBackend.ANTHROPIC:
                result = await self._process_anthropic(request, request_id)
            else:
                result = await self._process_claude_code(request, request_id)

            result.duration_ms = int((time.time() - start) * 1000)
            return result

        except Exception as e:
            return AIProcessResult(
                request_id=request_id,
                status="error",
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )

    async def _process_anthropic(
        self, request: AIProcessRequest, request_id: str
    ) -> AIProcessResult:
        """Process through Anthropic API directly."""
        try:
            import anthropic
        except ImportError:
            return AIProcessResult(
                request_id=request_id,
                status="error",
                error="anthropic package not installed. Run: pip install anthropic",
            )

        if not self.config.api_key:
            return AIProcessResult(
                request_id=request_id,
                status="error",
                error="No API key configured. Set ANTHROPIC_API_KEY or configure in settings.",
            )

        client = anthropic.Anthropic(api_key=self.config.api_key)

        results = []
        total_input = 0
        total_output = 0

        for selection in request.selections:
            # Build prompt based on operation
            system_prompt = self._get_system_prompt(request.operation.value)
            user_prompt = self._build_user_prompt(request, selection)

            try:
                response = client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                processed = response.content[0].text
                total_input += response.usage.input_tokens
                total_output += response.usage.output_tokens

                results.append(
                    ContentResult(
                        path=selection.path,
                        original=selection.content,
                        processed=processed,
                        changes_made=["AI processed"],
                        success=True,
                    )
                )
            except Exception as e:
                results.append(
                    ContentResult(
                        path=selection.path,
                        original=selection.content,
                        processed=selection.content,
                        success=False,
                        error=str(e),
                    )
                )

        return AIProcessResult(
            request_id=request_id,
            status="completed",
            results=results,
            usage={"input_tokens": total_input, "output_tokens": total_output},
        )

    async def _process_claude_code(
        self, request: AIProcessRequest, request_id: str
    ) -> AIProcessResult:
        """
        Process through Claude Code task queue.

        This adds a task to the queue for Claude Code to process
        with full tool access.
        """
        from .queue import TaskQueue

        queue = TaskQueue(self.project.root)

        # Submit to queue
        task = queue.submit(
            operation=request.operation.value,
            instructions=request.instructions,
            selections=[
                {
                    "path": s.path,
                    "content": s.content,
                    "title": s.title,
                    "content_type": s.content_type,
                    "notes": s.notes,
                }
                for s in request.selections
            ],
            target_language=request.target_language,
        )

        return AIProcessResult(
            request_id=request_id,
            status="queued",
            results=[
                ContentResult(
                    path=s.path,
                    original=s.content,
                    processed="",
                    changes_made=[f"Task {task.id} queued for Claude Code processing"],
                )
                for s in request.selections
            ],
        )

    def _get_system_prompt(self, operation: str) -> str:
        """Get system prompt for the given operation."""
        prompts = {
            "improve": """You are an expert editor. Improve the given content for clarity,
                flow, and readability while preserving the meaning and structure.
                Return only the improved content without explanations.""",
            "translate": """You are a professional translator. Translate the content
                accurately while maintaining the original tone and style.
                Return only the translated content.""",
            "analyze": """You are a content analyst. Provide detailed feedback on the
                content including strengths, areas for improvement, and specific suggestions.
                Format your response as markdown.""",
            "summarize": """You are a skilled summarizer. Create a concise summary
                that captures the key points. Return only the summary.""",
            "expand": """You are a content developer. Expand and elaborate on the
                given content with more details, examples, and explanations.
                Return only the expanded content.""",
            "simplify": """You are a plain language expert. Simplify the content
                for a broader audience while keeping essential information.
                Return only the simplified content.""",
            "proofread": """You are a meticulous proofreader. Fix any spelling,
                grammar, and punctuation errors. Return only the corrected content.""",
        }
        return prompts.get(operation, "Process the content as requested.")

    def _build_user_prompt(self, request: AIProcessRequest, selection) -> str:
        """Build user prompt from request and selection."""
        parts = [f"# Content\n\n{selection.content}"]

        if request.instructions:
            parts.append(f"\n\n# Instructions\n\n{request.instructions}")

        if request.target_language:
            parts.append(f"\n\nTarget language: {request.target_language}")

        if selection.notes:
            notes_text = "\n".join(f"- {n.get('content', n)}" for n in selection.notes)
            parts.append(f"\n\n# Notes\n\n{notes_text}")

        return "\n".join(parts)
