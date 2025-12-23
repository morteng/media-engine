"""Claude Code specific integration tools.

Provides tools specifically designed for optimal integration with
Claude Code and similar AI development assistants.
"""

import json
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
    lines.append("  content/           # Documentation content")
    for lang in project.languages:
        lines.append(f"    {lang}/            # {project.languages[lang].name} content")
    lines.append("  assets/            # Images, diagrams, media")
    lines.append("  dist/              # Built outputs")
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
        from ...insights import ConsistencyChecker, IncompleteTracker

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

    # Advanced Analysis
    lines.append("## Advanced Analysis")
    lines.append("")
    lines.append("This project has advanced analysis capabilities:")
    lines.append("")

    # Check for available modules
    advanced_modules = []
    try:
        from ...semantic import SemanticAnalyzer

        advanced_modules.append("semantic")
        analyzer = SemanticAnalyzer(project)
        dups = analyzer.find_near_duplicates(threshold=0.85)
        if dups:
            lines.append(f"- **Semantic**: {len(dups)} near-duplicate pairs detected")
    except Exception:
        pass

    try:
        from ...knowledge import KnowledgeGraph

        advanced_modules.append("knowledge")
        kg = KnowledgeGraph(project)
        kg.build()
        stats = kg.get_statistics()
        lines.append(f"- **Knowledge Graph**: {stats.get('total_concepts', 0)} concepts mapped")
    except Exception:
        pass

    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        advanced_modules.append("freshness")
        model = PredictiveFreshnessModel(project)
        predictions = model.predict_staleness()
        high_risk = [p for p in predictions if p.risk_score > 0.7]
        if high_risk:
            lines.append(f"- **Freshness Risk**: {len(high_risk)} documents at high staleness risk")
    except Exception:
        pass

    try:
        from ...codesync import EnhancedCodeSyncChecker

        advanced_modules.append("codesync")
        checker = EnhancedCodeSyncChecker(project)
        issues = checker.get_all_issues()
        if issues:
            lines.append(f"- **Code-Doc Sync**: {len(issues)} synchronization issues")
    except Exception:
        pass

    try:
        advanced_modules.append("norwegian_readability")
    except Exception:
        pass

    if advanced_modules:
        lines.append("")
        lines.append(f"Available modules: {', '.join(advanced_modules)}")
    lines.append("")

    # MCP integration note
    lines.append("## AI Agent Integration")
    lines.append("")
    lines.append("This project supports MCP (Model Context Protocol) for AI agent integration.")
    lines.append("")
    lines.append("Key MCP tools:")
    lines.append(
        "- `get_project_context` - Get comprehensive project overview with advanced analysis"
    )
    lines.append("- `get_suggested_actions` - Get prioritized task recommendations")
    lines.append("- `find_relevant_documents` - Search for documents by topic")
    lines.append("- `validate_action` - Check if an action is safe before executing")
    lines.append("- `quality_report_comprehensive` - Full quality report across all modules")
    lines.append("- `quality_report_document` - Detailed analysis for a specific document")
    lines.append("")

    return "\n".join(lines)


def _get_quick_status(project) -> dict:
    """Get a quick status summary."""
    status = {
        "project": project.config.name,
        "health": None,
        "issues": 0,
        "summary": "",
        "advanced": {},
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

    # Advanced analysis issues
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        duplicates = analyzer.find_near_duplicates(threshold=0.85)
        if duplicates:
            issues.append(f"{len(duplicates)} duplicates")
            status["advanced"]["semantic_duplicates"] = len(duplicates)
    except Exception:
        pass

    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        model = PredictiveFreshnessModel(project)
        predictions = model.predict_staleness()
        high_risk = [p for p in predictions if p.risk_score > 0.7]
        if high_risk:
            issues.append(f"{len(high_risk)} high-risk staleness")
            status["advanced"]["freshness_risk"] = len(high_risk)
    except Exception:
        pass

    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        sync_issues = checker.get_all_issues()
        critical = [i for i in sync_issues if i.severity == "critical"]
        if critical:
            issues.append(f"{len(critical)} code-doc sync")
            status["advanced"]["codesync_critical"] = len(critical)
    except Exception:
        pass

    status["issues"] = len(issues)

    # Build summary line
    if status["health"]:
        summary = f"Health: {status['health']}/100"
        if issues:
            summary += f" | Issues: {', '.join(issues[:3])}"
            if len(issues) > 3:
                summary += f" (+{len(issues) - 3} more)"
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
- Advanced analysis (semantic, knowledge graph, freshness, codesync)
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
            "description": "Run comprehensive quality checks",
            "content": """Run comprehensive quality checks on this media-engine project.

1. Use `quality_report_comprehensive` to get a full quality report including:
   - Basic quality (readability, links, schema)
   - Semantic analysis (duplicates, terminology)
   - Knowledge graph (concepts, prerequisites)
   - Freshness predictions (staleness risk)
   - Code-doc synchronization
2. Review the results categorized by module and severity
3. Use `quality_report_issues` to get prioritized action items
4. Help the user fix issues one at a time

For each issue:
- Explain what the problem is and which analysis detected it
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
        "media-analyze": {
            "description": "Run advanced content analysis",
            "content": """Run advanced analysis on this media-engine project.

Use `quality_report_comprehensive` to run all analysis modules:

1. **Semantic Analysis**: Find near-duplicates, terminology drift, content clusters
2. **Knowledge Graph**: Map concepts, find orphans, check prerequisites
3. **Freshness Prediction**: Identify documents at risk of becoming stale
4. **Code-Doc Sync**: Check documentation matches code references
5. **Readability**: Analyze Norwegian LIX scores and English readability

For document-specific analysis, use `quality_report_document` with the document path.

Present findings organized by category with specific recommendations.""",
        },
        "media-semantic": {
            "description": "Analyze semantic similarity",
            "content": """Analyze semantic similarity in this media-engine project.

Use `quality_report_module` with module='semantic' to get:
- Near-duplicate document pairs
- Terminology drift across documents
- Content clusters by topic

Help identify:
- Redundant content that could be consolidated
- Inconsistent terminology usage
- Topic organization opportunities""",
        },
        "media-freshness": {
            "description": "Check content freshness risk",
            "content": """Analyze content freshness risk in this media-engine project.

Use `quality_report_module` with module='freshness' to get:
- Documents at high risk of becoming stale
- Predicted days until staleness
- Risk factors for each document

Help the user prioritize:
- Which documents to refresh first
- Understanding staleness patterns
- Planning content maintenance schedules""",
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

    # Semantic analysis queries
    if any(word in query_lower for word in ["duplicate", "similar", "semantic", "terminology"]):
        return _get_semantic_info(project, query)

    # Knowledge graph queries
    if any(word in query_lower for word in ["concept", "knowledge", "prerequisite", "orphan"]):
        return _get_knowledge_info(project, query)

    # Freshness queries
    if any(
        word in query_lower for word in ["fresh", "stale", "staleness", "risk", "outdated content"]
    ):
        return _get_freshness_info(project, query)

    # Code-doc sync queries
    if any(word in query_lower for word in ["sync", "code", "documentation sync", "codesync"]):
        return _get_codesync_info(project, query)

    # Readability queries
    if any(word in query_lower for word in ["readability", "lix", "difficulty", "readable"]):
        return _get_readability_info(project, query)

    # Default: try document search
    return _search_documents(project, query)


def _extract_topic(query: str) -> str:
    """Extract the topic/subject from a query."""
    # Remove common question words
    words_to_remove = [
        "what",
        "which",
        "where",
        "how",
        "documents",
        "mention",
        "about",
        "contains",
        "discuss",
        "the",
        "a",
        "an",
        "do",
        "does",
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
            matches.append(
                {
                    "path": doc.get("path"),
                    "title": doc.get("title"),
                    "language": doc.get("language"),
                }
            )

    return {
        "query_type": "document_search",
        "topic": topic,
        "results": matches[:10],
        "total_matches": len(matches),
        "answer": f"Found {len(matches)} documents mentioning '{topic}'"
        if matches
        else f"No documents found mentioning '{topic}'",
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


def _get_semantic_info(project, query: str) -> dict:
    """Get semantic analysis info."""
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)

        result = {
            "query_type": "semantic_analysis",
            "near_duplicates": [],
            "terminology_drift": [],
            "content_clusters": [],
        }

        # Get near-duplicates
        duplicates = analyzer.find_near_duplicates(threshold=0.85)
        result["near_duplicates"] = [
            {
                "doc1": str(d.doc1),
                "doc2": str(d.doc2),
                "similarity": d.similarity,
            }
            for d in duplicates[:10]
        ]

        # Get terminology drift
        if "terminology" in query.lower():
            drift = analyzer.detect_terminology_drift()
            result["terminology_drift"] = [
                {"term": d.term, "variants": d.variants, "documents": d.documents[:3]}
                for d in (drift or [])[:10]
            ]

        # Get content clusters
        clusters = analyzer.cluster_content()
        result["content_clusters"] = len(clusters) if clusters else 0

        # Build answer
        answer_parts = []
        if result["near_duplicates"]:
            answer_parts.append(f"{len(duplicates)} near-duplicate pairs found")
        if result["terminology_drift"]:
            answer_parts.append(f"{len(result['terminology_drift'])} terminology inconsistencies")

        result["answer"] = "; ".join(answer_parts) if answer_parts else "No semantic issues found"

        return result
    except ImportError:
        return {
            "error": "Semantic analysis module not installed",
            "query_type": "semantic_analysis",
        }
    except Exception as e:
        return {"error": str(e), "query_type": "semantic_analysis"}


def _get_knowledge_info(project, query: str) -> dict:
    """Get knowledge graph info."""
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()

        stats = kg.get_statistics()
        orphans = kg.find_orphan_concepts()

        result = {
            "query_type": "knowledge_graph",
            "total_concepts": stats.get("total_concepts", 0),
            "total_relationships": stats.get("total_relationships", 0),
            "orphan_concepts": [
                {"name": c.name, "document": str(c.document)} for c in orphans[:10]
            ],
            "coverage_score": stats.get("coverage_score", 0),
        }

        # Check for prerequisite issues if asked
        if "prerequisite" in query.lower():
            prereq_issues = kg.find_prerequisite_issues()
            result["prerequisite_issues"] = [
                {"document": str(p.document), "missing": p.missing_prerequisites}
                for p in (prereq_issues or [])[:10]
            ]

        result["answer"] = (
            f"Knowledge graph: {result['total_concepts']} concepts, "
            f"{result['total_relationships']} relationships, "
            f"{len(orphans)} orphan concepts"
        )

        return result
    except ImportError:
        return {"error": "Knowledge graph module not installed", "query_type": "knowledge_graph"}
    except Exception as e:
        return {"error": str(e), "query_type": "knowledge_graph"}


def _get_freshness_info(project, query: str) -> dict:
    """Get freshness prediction info."""
    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        model = PredictiveFreshnessModel(project)
        predictions = model.predict_staleness()

        high_risk = [p for p in predictions if p.risk_score > 0.7]
        medium_risk = [p for p in predictions if 0.4 <= p.risk_score <= 0.7]

        result = {
            "query_type": "freshness_prediction",
            "total_analyzed": len(predictions),
            "high_risk_count": len(high_risk),
            "medium_risk_count": len(medium_risk),
            "high_risk_documents": [
                {
                    "path": str(p.document),
                    "risk_score": p.risk_score,
                    "days_until_stale": p.days_until_stale,
                }
                for p in high_risk[:10]
            ],
            "average_risk": round(sum(p.risk_score for p in predictions) / len(predictions), 2)
            if predictions
            else 0,
        }

        result["answer"] = (
            f"Freshness analysis: {len(high_risk)} high-risk, {len(medium_risk)} medium-risk "
            f"documents out of {len(predictions)} analyzed"
        )

        return result
    except ImportError:
        return {
            "error": "Predictive freshness module not installed",
            "query_type": "freshness_prediction",
        }
    except Exception as e:
        return {"error": str(e), "query_type": "freshness_prediction"}


def _get_codesync_info(project, query: str) -> dict:
    """Get code-doc synchronization info."""
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        issues = checker.get_all_issues()

        critical = [i for i in issues if i.severity == "critical"]
        warnings = [i for i in issues if i.severity == "warning"]

        result = {
            "query_type": "codesync",
            "total_issues": len(issues),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "critical_issues": [
                {
                    "document": str(i.document),
                    "type": i.issue_type,
                    "message": i.message,
                }
                for i in critical[:10]
            ],
            "is_synced": len(issues) == 0,
        }

        if result["is_synced"]:
            result["answer"] = "Code and documentation are fully synchronized"
        else:
            result["answer"] = (
                f"Code-doc sync: {len(critical)} critical, {len(warnings)} warning issues"
            )

        return result
    except ImportError:
        return {"error": "Code-doc sync module not installed", "query_type": "codesync"}
    except Exception as e:
        return {"error": str(e), "query_type": "codesync"}


def _get_readability_info(project, query: str) -> dict:
    """Get readability analysis info."""
    result = {
        "query_type": "readability",
        "norwegian": {},
        "english": {},
    }

    # Norwegian LIX analysis
    try:
        from ...readability.norwegian import NorwegianReadabilityAnalyzer

        analyzer = NorwegianReadabilityAnalyzer(project)
        no_results = analyzer.analyze_all()

        if no_results:
            avg_lix = sum(r.lix for r in no_results) / len(no_results)
            difficult = [r for r in no_results if r.difficulty_level == "very_difficult"]

            result["norwegian"] = {
                "documents_analyzed": len(no_results),
                "average_lix": round(avg_lix, 1),
                "very_difficult_count": len(difficult),
                "difficult_documents": [
                    {"path": str(r.document), "lix": r.lix, "level": r.difficulty_level}
                    for r in difficult[:5]
                ],
            }
    except ImportError:
        result["norwegian"] = {"error": "Norwegian readability module not installed"}
    except Exception as e:
        result["norwegian"] = {"error": str(e)}

    # English readability
    try:
        from ...readability import ReadabilityScorer

        scorer = ReadabilityScorer(project)
        en_results = scorer.score_all()

        if en_results:
            avg_grade = sum(r.flesch_kincaid_grade for r in en_results) / len(en_results)
            result["english"] = {
                "documents_analyzed": len(en_results),
                "average_grade_level": round(avg_grade, 1),
            }
    except Exception:
        pass

    # Build answer
    answers = []
    if result["norwegian"].get("documents_analyzed"):
        answers.append(
            f"Norwegian: avg LIX {result['norwegian']['average_lix']}, "
            f"{result['norwegian']['very_difficult_count']} very difficult"
        )
    if result["english"].get("documents_analyzed"):
        answers.append(f"English: avg grade level {result['english']['average_grade_level']}")

    result["answer"] = "; ".join(answers) if answers else "No readability data available"

    return result
