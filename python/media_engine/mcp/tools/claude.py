"""Claude Code specific integration tools.

Provides tools specifically designed for optimal integration with
Claude Code and similar AI development assistants.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer


def register_claude_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register Claude Code specific MCP tools."""

    @mcp.tool()
    async def generate_claude_context() -> str:
        """
        Generate optimal CLAUDE.md content for this project.

        Creates a comprehensive context document that helps Claude Code
        understand and work with this media-engine project effectively.

        The generated content includes:
        - Project overview and purpose
        - Key commands and workflows
        - Project structure summary
        - Important conventions
        - Current issues and priorities
        - Recommended actions

        Returns:
            Markdown content suitable for CLAUDE.md file.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        content = _generate_claude_md(project)

        return json.dumps(
            {
                "content": content,
                "suggested_path": str(project.root / "CLAUDE.md"),
                "note": "Review and customize this content before saving",
            },
            indent=2,
        )

    @mcp.tool()
    async def get_quick_status() -> str:
        """
        Get a quick one-line status suitable for display.

        Returns a concise summary of project health and any urgent issues.
        Ideal for status bars or quick checks.

        Returns:
            Brief status string with key metrics.
        """
        if not server_instance.project:
            return json.dumps({"status": "No project loaded"}, indent=2)

        project = server_instance.project
        status = _get_quick_status(project)

        return json.dumps(status, indent=2)

    @mcp.tool()
    async def get_slash_commands() -> str:
        """
        Get available slash command definitions for Claude Code.

        Returns command definitions that can be saved as .claude/commands/*.md
        files for quick access to common media-engine operations.

        Returns:
            Dictionary of command name to command content.
        """
        commands = _get_slash_commands()
        return json.dumps(commands, indent=2)

    @mcp.tool()
    async def natural_language_query(query: str) -> str:
        """
        Process a natural language query about the project.

        Understands questions like:
        - "What documents mention authentication?"
        - "Which chapters need translation to Norwegian?"
        - "What's the health of the API documentation?"
        - "Show me incomplete content"
        - "What changed recently?"

        Args:
            query: Natural language question about the project

        Returns:
            Answer to the query with relevant data.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        result = _process_natural_query(project, query)

        return json.dumps(result, indent=2)


def _generate_claude_md(project) -> str:
    """Generate CLAUDE.md content for the project."""
    lines = []

    # Header
    lines.append(f"# {project.config.name}")
    lines.append("")
    if project.config.description:
        lines.append(project.config.description)
        lines.append("")

    # Quick reference
    lines.append("## Quick Reference")
    lines.append("")
    lines.append("```bash")
    lines.append("# Check project status")
    lines.append("media-engine status")
    lines.append("")
    lines.append("# Run quality checks")
    lines.append("media-engine quality")
    lines.append("")
    lines.append("# Check translations")
    lines.append("media-engine translation status")
    lines.append("")
    lines.append("# Launch dashboard")
    lines.append("media-engine dashboard")
    lines.append("")
    lines.append("# Build outputs")
    lines.append("media-engine build")
    lines.append("```")
    lines.append("")

    # Project structure
    lines.append("## Project Structure")
    lines.append("")
    lines.append("```")
    lines.append(f"{project.config.name}/")
    lines.append(f"  content/           # Documentation content")
    for lang in project.languages:
        lines.append(f"    {lang}/            # {project.languages[lang].name} content")
    lines.append(f"  assets/            # Images, diagrams, media")
    lines.append(f"  dist/              # Built outputs")
    lines.append("```")
    lines.append("")

    # Languages
    lines.append("## Languages")
    lines.append("")
    lines.append(f"- **Source language**: {project.source_language}")
    lines.append(f"- **Available translations**: {', '.join(project.languages.keys())}")
    lines.append("")

    # Current status
    lines.append("## Current Status")
    lines.append("")
    try:
        from ...insights import HealthScorer, IncompleteTracker

        scorer = HealthScorer(project)
        health = scorer.score_project()
        lines.append(f"- **Health Score**: {health.score}/100 ({health.grade})")

        tracker = IncompleteTracker(project)
        summary = tracker.get_summary()
        if summary["total"] > 0:
            lines.append(f"- **Incomplete Items**: {summary['total']} (TODO, TBD, etc.)")
    except Exception:
        lines.append("- Health scoring not available")
    lines.append("")

    # Translation status
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()
        missing = tracker.get_missing_translations()

        if outdated:
            lines.append(f"- **Outdated Translations**: {len(outdated)}")
        if missing:
            lines.append(f"- **Missing Translations**: {len(missing)}")
    except Exception:
        pass
    lines.append("")

    # Key conventions
    lines.append("## Conventions")
    lines.append("")
    lines.append("### Document Frontmatter")
    lines.append("")
    lines.append("```yaml")
    lines.append("---")
    lines.append("title: Document Title")
    lines.append("status: draft | in_review | approved | final")
    lines.append("version: 1.0.0")
    lines.append("tags: [tag1, tag2]")
    lines.append("---")
    lines.append("```")
    lines.append("")
    lines.append("### Translation Frontmatter")
    lines.append("")
    lines.append("```yaml")
    lines.append("---")
    lines.append("title: Translated Title")
    lines.append('language: "no"  # Quote language codes!')
    lines.append("source_document: en/path/to/source.md")
    lines.append("source_version: 1.0.0")
    lines.append("---")
    lines.append("```")
    lines.append("")

    # Priorities
    lines.append("## Current Priorities")
    lines.append("")
    try:
        from ...insights import IncompleteTracker, ConsistencyChecker

        # High priority items
        tracker = IncompleteTracker(project)
        items = tracker.scan_project()
        high = [i for i in items if i.priority == "high"]
        if high:
            lines.append(f"1. Complete {len(high)} high-priority incomplete items")

        # Consistency issues
        checker = ConsistencyChecker(project)
        issues = checker.check_project()
        if issues:
            lines.append(f"2. Fix {len(issues)} status consistency issues")

        # Translations
        if outdated:
            lines.append(f"3. Update {len(outdated)} outdated translations")

    except Exception:
        lines.append("- Run `media-engine status` to see current priorities")
    lines.append("")

    # MCP integration note
    lines.append("## AI Agent Integration")
    lines.append("")
    lines.append("This project supports MCP (Model Context Protocol) for AI agent integration.")
    lines.append("")
    lines.append("Key MCP tools:")
    lines.append("- `get_project_context` - Get comprehensive project overview")
    lines.append("- `get_suggested_actions` - Get prioritized task recommendations")
    lines.append("- `find_relevant_documents` - Search for documents by topic")
    lines.append("- `validate_action` - Check if an action is safe before executing")
    lines.append("")

    return "\n".join(lines)


def _get_quick_status(project) -> dict:
    """Get a quick status summary."""
    status = {
        "project": project.config.name,
        "health": None,
        "issues": 0,
        "summary": "",
    }

    try:
        from ...insights import HealthScorer

        scorer = HealthScorer(project)
        health = scorer.score_project()
        status["health"] = health.score
        status["grade"] = health.grade
    except Exception:
        pass

    # Count issues
    issues = []

    try:
        from ...insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()
        if items:
            issues.append(f"{len(items)} incomplete")
    except Exception:
        pass

    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()
        if outdated:
            issues.append(f"{len(outdated)} translations outdated")
    except Exception:
        pass

    status["issues"] = len(issues)

    # Build summary line
    if status["health"]:
        summary = f"Health: {status['health']}/100"
        if issues:
            summary += f" | Issues: {', '.join(issues)}"
        else:
            summary += " | No issues"
    else:
        summary = "Status unknown"

    status["summary"] = summary

    return status


def _get_slash_commands() -> dict:
    """Get slash command definitions for Claude Code."""
    return {
        "media-status": {
            "description": "Get project health summary",
            "content": """Check the current status of this media-engine project.

Use the MCP tool `get_project_context` to get a comprehensive overview including:
- Project health score
- Pending issues
- Translation status
- Recommended actions

Then summarize the key findings for the user.""",
        },
        "media-update": {
            "description": "Update outdated documents",
            "content": """Help update outdated documents in this media-engine project.

1. First, use `get_suggested_actions` to find documents needing updates
2. Show the user what needs updating and ask which to work on
3. For each document:
   - Read the current content with `read_document`
   - Make the necessary updates
   - Increment the version with `increment_document_version`
   - Check translation impact with `analyze_change_impact`

Always validate actions before making changes.""",
        },
        "media-translate": {
            "description": "Start translation workflow",
            "content": """Help translate content in this media-engine project.

1. Use `translation_status` to see current translation state
2. Use `outdated_translations` to find translations needing updates
3. Use `missing_translations` to find content without translations

For translation work:
- Read the source document first
- Create or update the translation maintaining structure
- Set proper frontmatter (source_document, source_version)
- Use `mark_translation_synced` when complete

Ask the user which language and documents to focus on.""",
        },
        "media-quality": {
            "description": "Run quality checks",
            "content": """Run quality checks on this media-engine project.

1. Use `quality_check` to run comprehensive quality validation
2. Review the results and categorize by severity
3. Use `get_suggested_actions` for prioritized fixes
4. Help the user fix issues one at a time

For each issue:
- Explain what the problem is
- Suggest how to fix it
- Offer to make the fix if appropriate""",
        },
        "media-context": {
            "description": "Generate CLAUDE.md for this project",
            "content": """Generate a CLAUDE.md context file for this media-engine project.

Use the `generate_claude_context` MCP tool to create comprehensive
context documentation, then:

1. Review the generated content
2. Ask the user if they want to customize anything
3. Save to CLAUDE.md in the project root

This helps future Claude Code sessions understand the project better.""",
        },
    }


def _process_natural_query(project, query: str) -> dict:
    """Process a natural language query about the project."""
    query_lower = query.lower()

    # Document search queries
    if any(word in query_lower for word in ["mention", "about", "contains", "discuss"]):
        # Extract topic from query
        topic = _extract_topic(query)
        if topic:
            return _search_documents(project, topic)

    # Translation queries
    if "translat" in query_lower:
        if "need" in query_lower or "missing" in query_lower:
            return _get_translation_needs(project, query)
        elif "outdated" in query_lower or "update" in query_lower:
            return _get_outdated_translations(project)
        else:
            return _get_translation_status(project)

    # Health queries
    if "health" in query_lower or "quality" in query_lower:
        return _get_health_info(project, query)

    # Incomplete content queries
    if any(word in query_lower for word in ["incomplete", "todo", "tbd", "missing"]):
        return _get_incomplete_info(project)

    # Recent changes queries
    if any(word in query_lower for word in ["recent", "changed", "modified", "activity"]):
        return _get_recent_activity(project)

    # Status queries
    if "status" in query_lower:
        return _get_status_info(project)

    # Default: try document search
    return _search_documents(project, query)


def _extract_topic(query: str) -> str:
    """Extract the topic/subject from a query."""
    # Remove common question words
    words_to_remove = [
        "what", "which", "where", "how", "documents", "mention",
        "about", "contains", "discuss", "the", "a", "an", "do", "does"
    ]
    words = query.lower().split()
    topic_words = [w for w in words if w not in words_to_remove and len(w) > 2]
    return " ".join(topic_words)


def _search_documents(project, topic: str) -> dict:
    """Search documents for a topic."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)
    docs = manager.list_documents()

    matches = []
    topic_terms = set(topic.lower().split())

    for doc in docs:
        title = doc.get("title", "").lower()
        path = doc.get("path", "").lower()

        if any(term in title or term in path for term in topic_terms):
            matches.append({
                "path": doc.get("path"),
                "title": doc.get("title"),
                "language": doc.get("language"),
            })

    return {
        "query_type": "document_search",
        "topic": topic,
        "results": matches[:10],
        "total_matches": len(matches),
        "answer": f"Found {len(matches)} documents mentioning '{topic}'" if matches else f"No documents found mentioning '{topic}'",
    }


def _get_translation_needs(project, query: str) -> dict:
    """Get translation needs for a language."""
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        missing = tracker.get_missing_translations()

        # Check if specific language mentioned
        for lang in project.languages:
            if lang.lower() in query.lower():
                lang_missing = [m for m in missing if m.get("language") == lang]
                return {
                    "query_type": "translation_needs",
                    "language": lang,
                    "missing_count": len(lang_missing),
                    "missing": lang_missing[:10],
                    "answer": f"{len(lang_missing)} documents need translation to {lang}",
                }

        return {
            "query_type": "translation_needs",
            "total_missing": len(missing),
            "by_language": _group_by_language(missing),
            "answer": f"{len(missing)} total translations missing across all languages",
        }
    except Exception as e:
        return {"error": str(e)}


def _group_by_language(items: list) -> dict:
    """Group items by language."""
    by_lang = {}
    for item in items:
        lang = item.get("language", "unknown")
        if lang not in by_lang:
            by_lang[lang] = 0
        by_lang[lang] += 1
    return by_lang


def _get_outdated_translations(project) -> dict:
    """Get outdated translations."""
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()

        return {
            "query_type": "outdated_translations",
            "count": len(outdated),
            "translations": outdated[:10],
            "answer": f"{len(outdated)} translations are outdated and need updating",
        }
    except Exception as e:
        return {"error": str(e)}


def _get_translation_status(project) -> dict:
    """Get overall translation status."""
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        pairs = tracker.get_translation_pairs()
        outdated = tracker.get_outdated_translations()
        missing = tracker.get_missing_translations()

        return {
            "query_type": "translation_status",
            "total_pairs": len(pairs),
            "outdated": len(outdated),
            "missing": len(missing),
            "languages": list(project.languages.keys()),
            "answer": f"Translation status: {len(pairs)} pairs, {len(outdated)} outdated, {len(missing)} missing",
        }
    except Exception as e:
        return {"error": str(e)}


def _get_health_info(project, query: str) -> dict:
    """Get health information."""
    try:
        from ...insights import HealthScorer

        scorer = HealthScorer(project)

        # Check if asking about specific document
        # For now, return project health
        health = scorer.score_project()

        return {
            "query_type": "health",
            "score": health.score,
            "grade": health.grade,
            "components": health.components,
            "issues_count": len(health.issues),
            "answer": f"Project health: {health.score}/100 ({health.grade})",
        }
    except Exception as e:
        return {"error": str(e)}


def _get_incomplete_info(project) -> dict:
    """Get incomplete content info."""
    try:
        from ...insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()
        summary = tracker.get_summary()

        return {
            "query_type": "incomplete_content",
            "total": summary["total"],
            "by_priority": summary.get("by_priority", {}),
            "top_items": [
                {"path": str(i.document), "type": i.marker_type, "line": i.line_number}
                for i in items[:5]
            ],
            "answer": f"{summary['total']} incomplete items found (TODO, TBD, placeholders, etc.)",
        }
    except Exception as e:
        return {"error": str(e)}


def _get_recent_activity(project) -> dict:
    """Get recent activity info."""
    try:
        from ...insights import VelocityTracker

        tracker = VelocityTracker(project)
        metrics = tracker.get_metrics(days=7)

        return {
            "query_type": "recent_activity",
            "period": "last 7 days",
            "commits": metrics.total_commits,
            "documents_modified": metrics.documents_modified,
            "lines_changed": metrics.lines_added + metrics.lines_removed,
            "answer": f"Last 7 days: {metrics.total_commits} commits, {metrics.documents_modified} docs modified",
        }
    except Exception as e:
        return {"error": str(e)}


def _get_status_info(project) -> dict:
    """Get general status info."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)
    docs = manager.list_documents()

    # Count by status
    by_status = {}
    for doc in docs:
        status = doc.get("status", "unknown")
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1

    return {
        "query_type": "status",
        "total_documents": len(docs),
        "by_status": by_status,
        "languages": list(project.languages.keys()),
        "answer": f"Project has {len(docs)} documents across {len(project.languages)} languages",
    }
