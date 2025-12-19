"""Context-rich MCP tools for AI agents.

Provides comprehensive project context and intelligent document discovery
to help AI agents understand and work with media-engine projects effectively.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer


def register_context_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register context-related MCP tools."""

    @mcp.tool()
    async def get_project_context() -> str:
        """
        Get comprehensive project context for AI agents.

        Returns everything an AI agent needs to understand the project:
        - Project overview and purpose
        - Content structure and organization
        - Key terminology and concepts
        - Current health status
        - Recent activity summary
        - Pending issues and recommendations

        This is the recommended first call when starting work on a project.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        context = {
            "overview": _get_project_overview(project),
            "structure": _get_content_structure(project),
            "health": _get_health_context(project),
            "activity": _get_activity_summary(project),
            "issues": _get_pending_issues(project),
            "recommendations": _get_recommendations(project),
        }

        return json.dumps(context, indent=2)

    @mcp.tool()
    async def find_relevant_documents(query: str, context: str = "") -> str:
        """
        Find documents most relevant to a query or task.

        Uses intelligent matching to find documents that:
        - Match keywords in title, content, or metadata
        - Are related through dependencies or links
        - Are ranked by relevance and freshness

        Args:
            query: Search query or task description
            context: Optional additional context about what you're looking for

        Returns:
            Ranked list of relevant documents with context about why each matched.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        results = _find_relevant_docs(project, query, context)

        return json.dumps(
            {
                "query": query,
                "context": context if context else None,
                "results": results,
                "total": len(results),
            },
            indent=2,
        )

    @mcp.tool()
    async def analyze_change_impact(
        target: str, change_type: str = "update", description: str = ""
    ) -> str:
        """
        Analyze the impact of a proposed change.

        Given a document or code change, analyzes what else might need updating:
        - Documents that depend on the target
        - Translations that may need updating
        - Related documents via links or topics
        - Suggested follow-up actions

        Args:
            target: Path to document being changed (relative to content dir)
            change_type: Type of change - "update", "delete", "create", "rename"
            description: Optional description of what's changing

        Returns:
            Impact report with affected documents and suggested actions.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        impact = _analyze_impact(project, target, change_type, description)

        return json.dumps(impact, indent=2)

    @mcp.tool()
    async def get_document_context(document_path: str) -> str:
        """
        Get comprehensive context about a specific document.

        Returns everything needed to understand a document:
        - Content summary and metadata
        - Translation status
        - Dependencies (what this document needs)
        - Dependents (what needs this document)
        - Related documents
        - Quality issues
        - Suggested actions

        Args:
            document_path: Path to document (relative to content dir)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        doc_context = _get_document_context(project, document_path)

        return json.dumps(doc_context, indent=2)


def _get_project_overview(project) -> dict:
    """Build project overview section."""
    return {
        "name": project.config.name,
        "description": project.config.description or "No description",
        "languages": list(project.languages.keys()),
        "source_language": project.source_language,
        "paths": {
            "root": str(project.root),
            "content": str(project.content_dir),
            "assets": str(project.assets_dir),
        },
    }


def _get_content_structure(project) -> dict:
    """Build content structure section."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)
    docs = manager.list_documents()

    # Group by language and type
    by_language = {}
    types = set()

    for doc in docs:
        lang = doc.get("language", "unknown")
        if lang not in by_language:
            by_language[lang] = {"count": 0, "documents": []}
        by_language[lang]["count"] += 1
        by_language[lang]["documents"].append(
            {
                "path": doc.get("path", ""),
                "title": doc.get("title", "Untitled"),
                "status": doc.get("status", "unknown"),
            }
        )

        doc_type = doc.get("type", "document")
        types.add(doc_type)

    return {
        "total_documents": len(docs),
        "by_language": {
            lang: {"count": info["count"], "documents": info["documents"][:10]}
            for lang, info in by_language.items()
        },
        "document_types": list(types),
    }


def _get_health_context(project) -> dict:
    """Build health context section."""
    try:
        from ...insights import HealthScorer

        scorer = HealthScorer(project)
        health = scorer.score_project()
        return {
            "score": health.score,
            "grade": health.grade,
            "summary": f"Project health is {health.grade} ({health.score}/100)",
            "components": {
                comp: {"score": score, "weight": health.weights.get(comp, 0)}
                for comp, score in health.components.items()
            },
            "top_issues": [issue.to_dict() for issue in health.issues[:5]],
        }
    except Exception as e:
        return {"error": str(e), "score": None}


def _get_activity_summary(project) -> dict:
    """Build recent activity summary."""
    try:
        from ...insights import VelocityTracker

        tracker = VelocityTracker(project)
        metrics = tracker.get_metrics(days=7)

        return {
            "period": "last_7_days",
            "commits": metrics.total_commits,
            "lines_changed": metrics.lines_added + metrics.lines_removed,
            "documents_modified": metrics.documents_modified,
            "most_active_areas": metrics.area_breakdown[:5] if metrics.area_breakdown else [],
        }
    except Exception:
        return {"period": "last_7_days", "commits": 0, "error": "Could not fetch activity"}


def _get_pending_issues(project) -> dict:
    """Build pending issues summary."""
    issues = {"incomplete": [], "consistency": [], "stale_translations": []}

    # Incomplete content
    try:
        from ...insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()
        issues["incomplete"] = [
            {"path": str(i.document), "type": i.marker_type, "text": i.text[:100]}
            for i in items[:5]
        ]
    except Exception:
        pass

    # Consistency issues
    try:
        from ...insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        consistency_issues = checker.check_project()
        issues["consistency"] = [
            {"path": str(i.document), "issue": i.issue_type, "suggestion": i.suggested_status}
            for i in consistency_issues[:5]
        ]
    except Exception:
        pass

    # Stale translations
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()
        issues["stale_translations"] = [
            {"path": str(t["path"]), "source_changed": True} for t in outdated[:5]
        ]
    except Exception:
        pass

    return issues


def _get_recommendations(project) -> list:
    """Generate actionable recommendations."""
    recommendations = []

    # Check health score
    try:
        from ...insights import HealthScorer

        scorer = HealthScorer(project)
        health = scorer.score_project()

        if health.score < 70:
            recommendations.append(
                {
                    "priority": "high",
                    "action": "improve_health",
                    "message": f"Project health is low ({health.score}/100). Focus on fixing quality issues.",
                }
            )

        # Check component scores
        for comp, score in health.components.items():
            if score < 60:
                recommendations.append(
                    {
                        "priority": "medium",
                        "action": f"improve_{comp}",
                        "message": f"{comp.title()} score is low ({score}/100)",
                    }
                )
    except Exception:
        pass

    # Check incomplete content
    try:
        from ...insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        summary = tracker.get_summary()
        if summary["total"] > 0:
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "complete_content",
                    "message": f"{summary['total']} incomplete items (TODO, TBD, etc.) found",
                    "count": summary["total"],
                }
            )
    except Exception:
        pass

    # Check translations
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()
        if outdated:
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "update_translations",
                    "message": f"{len(outdated)} translations need updating",
                    "count": len(outdated),
                }
            )
    except Exception:
        pass

    return recommendations


def _find_relevant_docs(project, query: str, context: str = "") -> list:
    """Find documents relevant to a query."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)
    docs = manager.list_documents()

    # Tokenize query
    query_terms = set(query.lower().split())
    if context:
        query_terms.update(context.lower().split())

    results = []

    for doc in docs:
        score = 0
        reasons = []

        # Check title match
        title = doc.get("title", "").lower()
        title_matches = sum(1 for term in query_terms if term in title)
        if title_matches:
            score += title_matches * 10
            reasons.append(f"title matches: {title_matches} terms")

        # Check path match
        path = doc.get("path", "").lower()
        path_matches = sum(1 for term in query_terms if term in path)
        if path_matches:
            score += path_matches * 5
            reasons.append(f"path matches: {path_matches} terms")

        # Check status (boost recent/active docs)
        status = doc.get("status", "").lower()
        if status in ["draft", "in_review"]:
            score += 3
            reasons.append("active document")

        # Check tags/keywords if available
        tags = doc.get("tags", []) or doc.get("keywords", [])
        if tags:
            tag_set = set(t.lower() for t in tags)
            tag_matches = len(query_terms & tag_set)
            if tag_matches:
                score += tag_matches * 8
                reasons.append(f"tag matches: {tag_matches}")

        if score > 0:
            results.append(
                {
                    "path": doc.get("path"),
                    "title": doc.get("title"),
                    "language": doc.get("language"),
                    "status": doc.get("status"),
                    "relevance_score": score,
                    "match_reasons": reasons,
                }
            )

    # Sort by relevance score
    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    return results[:20]


def _analyze_impact(project, target: str, change_type: str, description: str) -> dict:
    """Analyze the impact of a proposed change."""
    from ...cms.document_manager import DocumentManager

    DocumentManager(project)

    impact = {
        "target": target,
        "change_type": change_type,
        "description": description or f"{change_type} to {target}",
        "affected_documents": [],
        "translation_impact": [],
        "suggested_actions": [],
    }

    # Find the target document
    target_path = Path(target)

    # Check for dependents using dependency graph
    try:
        from ...dependencies import DependencyGraph

        graph = DependencyGraph(project)
        graph.refresh()

        # Get documents that depend on the target
        dependents = graph.get_dependents(target_path)
        for dep in dependents:
            impact["affected_documents"].append(
                {
                    "path": str(dep),
                    "relationship": "depends_on_target",
                    "action_needed": "review_for_updates",
                }
            )
    except Exception:
        pass

    # Check translation impact
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)

        # If this is a source document, find its translations
        pairs = tracker.get_translation_pairs()
        for pair in pairs:
            if str(pair.get("source", "")) == target:
                impact["translation_impact"].append(
                    {
                        "translation": str(pair.get("translation", "")),
                        "language": pair.get("language", ""),
                        "action_needed": "update_translation" if change_type == "update" else change_type,
                    }
                )
    except Exception:
        pass

    # Generate suggested actions
    if change_type == "update":
        if impact["translation_impact"]:
            impact["suggested_actions"].append(
                {
                    "action": "update_translations",
                    "priority": "high",
                    "count": len(impact["translation_impact"]),
                    "message": f"Update {len(impact['translation_impact'])} translations after source change",
                }
            )

        if impact["affected_documents"]:
            impact["suggested_actions"].append(
                {
                    "action": "review_dependents",
                    "priority": "medium",
                    "count": len(impact["affected_documents"]),
                    "message": f"Review {len(impact['affected_documents'])} dependent documents",
                }
            )

    elif change_type == "delete":
        impact["suggested_actions"].append(
            {
                "action": "fix_broken_links",
                "priority": "high",
                "message": "Check and fix any broken links to this document",
            }
        )

    return impact


def _get_document_context(project, document_path: str) -> dict:
    """Get comprehensive context for a document."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)

    # Find the document
    docs = manager.list_documents()
    doc = None
    for d in docs:
        if d.get("path") == document_path or str(d.get("path", "")).endswith(document_path):
            doc = d
            break

    if not doc:
        return {"error": f"Document not found: {document_path}"}

    context = {
        "document": {
            "path": doc.get("path"),
            "title": doc.get("title"),
            "language": doc.get("language"),
            "status": doc.get("status"),
            "version": doc.get("version"),
        },
        "translation": {},
        "dependencies": {"depends_on": [], "dependents": []},
        "related": [],
        "quality": {},
        "suggested_actions": [],
    }

    # Translation info
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)

        # Check if this is a translation
        source_doc = doc.get("source_document")
        if source_doc:
            context["translation"] = {
                "is_translation": True,
                "source_document": source_doc,
                "source_version": doc.get("source_version"),
                "needs_update": tracker.is_translation_outdated(Path(document_path)),
            }
        else:
            # Find translations of this document
            translations = tracker.get_translations_for_source(Path(document_path))
            context["translation"] = {"is_source": True, "translations": translations}
    except Exception:
        pass

    # Dependencies
    try:
        from ...dependencies import DependencyGraph

        graph = DependencyGraph(project)
        graph.refresh()

        context["dependencies"]["depends_on"] = [str(p) for p in graph.get_dependencies(Path(document_path))]
        context["dependencies"]["dependents"] = [str(p) for p in graph.get_dependents(Path(document_path))]
    except Exception:
        pass

    # Quality issues
    try:
        from ...insights import HealthScorer

        scorer = HealthScorer(project)
        doc_health = scorer.score_document(Path(document_path))
        context["quality"] = {
            "score": doc_health.score if hasattr(doc_health, "score") else None,
            "issues": [i.to_dict() for i in doc_health.issues[:5]] if hasattr(doc_health, "issues") else [],
        }
    except Exception:
        pass

    # Suggested actions for this document
    if context.get("translation", {}).get("needs_update"):
        context["suggested_actions"].append(
            {"action": "update_translation", "priority": "high", "message": "Translation is outdated"}
        )

    if context.get("quality", {}).get("score", 100) < 70:
        context["suggested_actions"].append(
            {"action": "improve_quality", "priority": "medium", "message": "Document has quality issues"}
        )

    return context
