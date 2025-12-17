"""MCP resources and prompts registration."""

import json

try:
    from mcp.types import GetPromptResult, PromptMessage, TextContent

    HAS_MCP = True
except ImportError:
    HAS_MCP = False


def register_resources(server, server_instance, get_health_summary_func):
    """Register MCP resources for context."""
    if not HAS_MCP:
        return

    @server.resource("project://overview")
    async def project_overview() -> str:
        """Project overview and health status."""
        if not server_instance.project:
            return "No project loaded"

        status = server_instance.project.get_status()
        health = get_health_summary_func(server_instance.project)

        return f"""# {server_instance.project.config.name}

{server_instance.project.config.description}

## Languages
- Source: {server_instance.project.source_language}
- Configured: {", ".join(server_instance.project.languages.keys())}

## Content
{json.dumps(status["content"], indent=2)}

## Health
- Translation sync: {health["translation_status"]}
- Quality: {health["quality_status"]}
"""

    @server.resource("project://languages")
    async def project_languages() -> str:
        """Configured languages and their settings."""
        if not server_instance.project:
            return "No project loaded"

        return json.dumps(
            {
                code: {"name": lang.name, "locale": lang.locale}
                for code, lang in server_instance.project.languages.items()
            },
            indent=2,
        )


def register_prompts(server):
    """Register prompts for common workflows."""
    if not HAS_MCP:
        return

    @server.prompt()
    async def review_translation(language: str) -> GetPromptResult:
        """Prompt for reviewing translations in a language."""
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Review all translations for language '{language}':

1. First, get the translation status for {language}
2. For any outdated translations, read both source and translation
3. Summarize what changes are needed
4. Suggest whether minor updates or full re-translation is needed

Use the translation_status and read_document tools.""",
                    ),
                )
            ]
        )

    @server.prompt()
    async def quality_review() -> GetPromptResult:
        """Prompt for comprehensive quality review."""
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""Perform a comprehensive quality review:

1. Run quality_check to find all issues
2. Run validate_project to check schema compliance
3. Check translation_status for sync issues
4. Summarize findings by severity
5. Recommend priority fixes

Start with quality_check.""",
                    ),
                )
            ]
        )
