"""
AI Prompts and Templates

System prompts and user prompt construction for AI operations.
"""

from typing import TYPE_CHECKING

from .types import AIOperation, AIProcessRequest

if TYPE_CHECKING:
    from ..core.project import Project


OPERATION_PROMPTS = {
    AIOperation.IMPROVE: """You are an expert content editor. Your task is to improve the provided content while maintaining its core meaning and style.

Focus on:
- Clarity and readability
- Grammar and punctuation
- Flow and structure
- Removing redundancy

Preserve:
- Technical accuracy
- Code blocks (do not modify code)
- Markdown formatting
- Document structure""",
    AIOperation.TRANSLATE: """You are a professional translator specializing in technical documentation.

Guidelines:
- Maintain the exact same structure and formatting
- Preserve all code blocks, file paths, and technical terms
- Keep markdown formatting intact
- Translate naturally, not word-for-word
- Adapt idioms appropriately for the target culture
- Keep frontmatter keys in English, only translate values where appropriate""",
    AIOperation.ANALYZE: """You are a content analyst. Review the provided content and provide detailed feedback.

Provide:
- Summary of strengths
- Areas for improvement
- Specific suggestions with examples
- Overall quality assessment

Do NOT rewrite the content - only analyze and suggest.""",
    AIOperation.SUMMARIZE: """Create a concise summary of the provided content.

Guidelines:
- Capture all key points
- Maintain technical accuracy
- Use clear, simple language
- Preserve any critical details
- Keep the summary to about 20% of the original length""",
    AIOperation.EXPAND: """Expand and elaborate on the provided content.

Guidelines:
- Add more detail and examples
- Explain concepts more thoroughly
- Maintain the original tone and style
- Don't change the fundamental meaning
- Add helpful context where appropriate""",
    AIOperation.SIMPLIFY: """Simplify the provided content for a broader audience.

Guidelines:
- Use simpler vocabulary
- Break down complex sentences
- Explain technical terms
- Maintain accuracy
- Keep the core message intact""",
    AIOperation.PROOFREAD: """You are a professional proofreader. Check the content for:
- Spelling errors
- Grammar issues
- Punctuation problems
- Inconsistent formatting
- Typos

Return the corrected content with a brief list of changes made.""",
}


def build_system_prompt(operation: AIOperation, project: "Project" = None) -> str:
    """Build system prompt for AI operation."""
    base_prompt = OPERATION_PROMPTS.get(
        operation, OPERATION_PROMPTS[AIOperation.IMPROVE]
    )

    context = ""
    if project:
        context = f"""

Project Context:
- Project: {project.config.name}
- Languages: {', '.join(project.languages)}
- Source Language: {project.source_language}
"""

    output_format = """

Output Format:
Return your response as JSON with this structure:
```json
{
  "results": [
    {
      "path": "original/file/path.md",
      "processed": "the processed/improved content",
      "changes_summary": "brief description of changes made"
    }
  ]
}
```

Important: Return ONLY valid JSON. Do not include any text before or after the JSON block.
"""

    return base_prompt + context + output_format


def build_user_prompt(request: AIProcessRequest) -> str:
    """Build user prompt from request."""
    parts = []

    # Add custom instructions
    if request.instructions:
        parts.append(f"## Instructions\n{request.instructions}\n")

    # Add target language for translation
    if request.operation == AIOperation.TRANSLATE and request.target_language:
        parts.append(f"## Target Language\nTranslate to: {request.target_language}\n")

    # Add content sections
    parts.append("## Content to Process\n")

    for i, selection in enumerate(request.selections):
        parts.append(f"### Document {i + 1}: {selection.title}")
        parts.append(f"Path: `{selection.path}`")
        parts.append(f"Type: {selection.content_type}")

        if selection.notes:
            parts.append("\nNotes attached to this content:")
            for note in selection.notes:
                priority = note.get("priority", "medium")
                text = note.get("text", "")
                parts.append(f"- [{priority}] {text}")

        parts.append(f"\n```markdown\n{selection.content}\n```\n")

    return "\n".join(parts)
