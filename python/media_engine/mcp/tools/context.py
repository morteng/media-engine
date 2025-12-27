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
        - Advanced analysis insights (semantic, knowledge graph, freshness, etc.)

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
            "advanced_analysis": _get_advanced_context(project),
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
            "score": health.overall,
            "grade": health.grade,
            "summary": f"Project health is {health.grade} ({health.overall}/100)",
            "components": {
                comp: {"score": score, "weight": scorer.weights.get(comp, 0)}
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
    issues = {
        "incomplete": [],
        "consistency": [],
        "stale_translations": [],
        "semantic": [],
        "knowledge": [],
        "freshness": [],
        "codesync": [],
        "readability": [],
    }

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

    # Semantic issues (near-duplicates, terminology drift)
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        duplicates = analyzer.find_near_duplicates(threshold=0.85)
        issues["semantic"] = [
            {
                "type": "near_duplicate",
                "doc1": str(d.doc1),
                "doc2": str(d.doc2),
                "similarity": d.similarity,
            }
            for d in duplicates[:3]
        ]
    except Exception:
        pass

    # Knowledge graph issues (orphan concepts, missing prerequisites)
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()
        orphans = kg.find_orphan_concepts()
        issues["knowledge"] = [
            {"type": "orphan_concept", "concept": c.name, "document": str(c.document)}
            for c in orphans[:5]
        ]
    except Exception:
        pass

    # Predictive freshness (high-risk documents)
    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        model = PredictiveFreshnessModel(project)
        predictions = model.predict_staleness()
        high_risk = [p for p in predictions if p.risk_score > 0.7]
        issues["freshness"] = [
            {
                "path": str(p.document),
                "risk_score": p.risk_score,
                "days_until_stale": p.days_until_stale,
            }
            for p in high_risk[:5]
        ]
    except Exception:
        pass

    # Code-doc sync issues
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        sync_issues = checker.get_all_issues()
        issues["codesync"] = [
            {"path": str(i.document), "type": i.issue_type.value, "severity": i.severity}
            for i in sync_issues[:5]
        ]
    except Exception:
        pass

    # Readability issues (Norwegian LIX, difficulty)
    try:
        from ...readability.norwegian import NorwegianReadabilityAnalyzer

        analyzer = NorwegianReadabilityAnalyzer(project)
        results = analyzer.analyze_all()
        difficult = [r for r in results if r.difficulty_level == "very_difficult"]
        issues["readability"] = [
            {"path": str(r.document), "lix_score": r.lix, "level": r.difficulty_level}
            for r in difficult[:5]
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

        if health.overall < 70:
            recommendations.append(
                {
                    "priority": "high",
                    "action": "improve_health",
                    "message": f"Project health is low ({health.overall}/100). Focus on fixing quality issues.",
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

    # Check for semantic duplicates
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        duplicates = analyzer.find_near_duplicates(threshold=0.85)
        if duplicates:
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "consolidate_duplicates",
                    "message": f"{len(duplicates)} near-duplicate document pairs detected",
                    "count": len(duplicates),
                    "module": "semantic",
                }
            )
    except Exception:
        pass

    # Check for terminology drift
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        drift = analyzer.detect_terminology_drift()
        if drift and len(drift) > 3:
            recommendations.append(
                {
                    "priority": "low",
                    "action": "standardize_terminology",
                    "message": f"{len(drift)} terminology inconsistencies found",
                    "count": len(drift),
                    "module": "semantic",
                }
            )
    except Exception:
        pass

    # Check for orphan concepts in knowledge graph
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()
        orphans = kg.find_orphan_concepts()
        if orphans:
            recommendations.append(
                {
                    "priority": "low",
                    "action": "link_concepts",
                    "message": f"{len(orphans)} concepts not linked to others",
                    "count": len(orphans),
                    "module": "knowledge",
                }
            )
    except Exception:
        pass

    # Check for high staleness risk
    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        model = PredictiveFreshnessModel(project)
        predictions = model.predict_staleness()
        high_risk = [p for p in predictions if p.risk_score > 0.7]
        if high_risk:
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "refresh_content",
                    "message": f"{len(high_risk)} documents at high risk of becoming stale",
                    "count": len(high_risk),
                    "module": "freshness",
                }
            )
    except Exception:
        pass

    # Check for code-doc sync issues
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        issues = checker.get_all_issues()
        critical = [i for i in issues if i.severity == "critical"]
        if critical:
            recommendations.append(
                {
                    "priority": "high",
                    "action": "sync_code_docs",
                    "message": f"{len(critical)} critical code-documentation sync issues",
                    "count": len(critical),
                    "module": "codesync",
                }
            )
    except Exception:
        pass

    # Check Norwegian readability
    try:
        from ...readability.norwegian import NorwegianReadabilityAnalyzer

        analyzer = NorwegianReadabilityAnalyzer(project)
        results = analyzer.analyze_all()
        difficult = [r for r in results if r.difficulty_level == "very_difficult"]
        if difficult:
            recommendations.append(
                {
                    "priority": "low",
                    "action": "simplify_content",
                    "message": f"{len(difficult)} Norwegian documents are very difficult to read",
                    "count": len(difficult),
                    "module": "readability",
                }
            )
    except Exception:
        pass

    # Check for audience drift
    try:
        from ...advanced import AudienceAnalyzer

        analyzer = AudienceAnalyzer(project)
        drift = analyzer.detect_audience_drift()
        if drift and drift.severity == "high":
            recommendations.append(
                {
                    "priority": "medium",
                    "action": "align_audience",
                    "message": "Significant audience drift detected across documents",
                    "module": "advanced",
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

    # Check for dependents using UnifiedRegistry
    try:
        from ...relationships import get_registry_manager, init_registry_manager

        registry_manager = get_registry_manager(project)
        if registry_manager is None:
            registry_manager = init_registry_manager(project)

        # Get documents that depend on the target
        dependents = registry_manager.registry.get_impact(target_path)
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
                        "action_needed": "update_translation"
                        if change_type == "update"
                        else change_type,
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
        from ...relationships import get_registry_manager, init_registry_manager

        registry_manager = get_registry_manager(project)
        if registry_manager is None:
            registry_manager = init_registry_manager(project)

        registry = registry_manager.registry
        doc_path = Path(document_path)

        # Get outgoing edges (what this doc depends on)
        outgoing = registry.get_outgoing_edges(doc_path)
        context["dependencies"]["depends_on"] = [str(e.target) for e in outgoing]

        # Get incoming edges (what depends on this doc)
        dependents = registry.get_impact(doc_path)
        context["dependencies"]["dependents"] = [str(p) for p in dependents]
    except Exception:
        pass

    # Quality issues
    try:
        from ...insights import HealthScorer

        scorer = HealthScorer(project)
        doc_health = scorer.score_document(Path(document_path))
        context["quality"] = {
            "score": doc_health.overall if hasattr(doc_health, "overall") else None,
            "issues": [i.to_dict() for i in doc_health.issues[:5]]
            if hasattr(doc_health, "issues")
            else [],
        }
    except Exception:
        pass

    # Suggested actions for this document
    if context.get("translation", {}).get("needs_update"):
        context["suggested_actions"].append(
            {
                "action": "update_translation",
                "priority": "high",
                "message": "Translation is outdated",
            }
        )

    if context.get("quality", {}).get("score", 100) < 70:
        context["suggested_actions"].append(
            {
                "action": "improve_quality",
                "priority": "medium",
                "message": "Document has quality issues",
            }
        )

    # Add advanced analysis for this document
    context["advanced"] = _get_document_advanced_context(project, document_path, doc)

    return context


def _get_document_advanced_context(project, document_path: str, doc: dict) -> dict:
    """Get advanced analysis context for a specific document."""
    advanced = {
        "semantic": {},
        "knowledge": {},
        "readability": {},
        "freshness": {},
        "codesync": {},
    }

    doc_path = Path(document_path)

    # Semantic analysis - find similar documents
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        similar = analyzer.find_similar_documents(doc_path, top_k=5)
        advanced["semantic"] = {
            "similar_documents": [
                {"path": str(s.path), "similarity": s.similarity} for s in similar
            ]
        }
    except Exception:
        pass

    # Knowledge graph - concepts in this document
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()
        concepts = kg.get_document_concepts(doc_path)
        advanced["knowledge"] = {
            "concepts": [c.name for c in concepts[:10]],
            "prerequisites": [str(p) for p in kg.get_prerequisites(doc_path)],
        }
    except Exception:
        pass

    # Readability (Norwegian-specific if applicable)
    language = doc.get("language", "en")
    try:
        if language == "no":
            from ...readability.norwegian import NorwegianReadabilityAnalyzer

            analyzer = NorwegianReadabilityAnalyzer(project)
            result = analyzer.analyze_document(doc_path)
            if result:
                advanced["readability"] = {
                    "lix_score": result.lix,
                    "difficulty_level": result.difficulty_level,
                    "word_count": result.word_count,
                    "sentence_count": result.sentence_count,
                }
        else:
            from ...readability import ReadabilityScorer

            scorer = ReadabilityScorer(project)
            result = scorer.score_document(doc_path)
            if result:
                advanced["readability"] = {
                    "flesch_reading_ease": result.flesch_reading_ease,
                    "flesch_kincaid_grade": result.flesch_kincaid_grade,
                    "gunning_fog": result.gunning_fog,
                }
    except Exception:
        pass

    # Predictive freshness
    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        model = PredictiveFreshnessModel(project)
        prediction = model.predict_for_document(doc_path)
        if prediction:
            advanced["freshness"] = {
                "risk_score": prediction.risk_score,
                "days_until_stale": prediction.days_until_stale,
                "risk_factors": prediction.risk_factors,
            }
    except Exception:
        pass

    # Code-doc sync status
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        report = checker.check_document(doc_path)
        advanced["codesync"] = {
            "issues": [
                {"type": i.issue_type.value, "severity": i.severity, "message": i.message}
                for i in report.issues
            ],
            "is_synced": len(report.issues) == 0,
        }
    except Exception:
        pass

    return advanced


def _get_advanced_context(project) -> dict:
    """Get comprehensive advanced analysis context for the project."""
    advanced = {
        "semantic": {},
        "knowledge": {},
        "readability": {},
        "freshness": {},
        "codesync": {},
        "advanced": {},
        "modules_available": [],
    }

    # Check which modules are available
    modules = []

    # Semantic analysis summary
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        duplicates = analyzer.find_near_duplicates(threshold=0.85)
        clusters = analyzer.cluster_content()
        drift = analyzer.detect_terminology_drift()

        advanced["semantic"] = {
            "near_duplicates": len(duplicates),
            "content_clusters": len(clusters) if clusters else 0,
            "terminology_drift_items": len(drift) if drift else 0,
            "summary": f"{len(duplicates)} near-duplicates, {len(clusters) if clusters else 0} content clusters",
        }
        modules.append("semantic")
    except ImportError:
        advanced["semantic"] = {"error": "Module not installed"}
    except Exception as e:
        advanced["semantic"] = {"error": str(e)}

    # Knowledge graph summary
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()
        stats = kg.get_statistics()
        orphans = kg.find_orphan_concepts()

        advanced["knowledge"] = {
            "total_concepts": stats.get("total_concepts", 0),
            "total_relationships": stats.get("total_relationships", 0),
            "orphan_concepts": len(orphans),
            "coverage_score": stats.get("coverage_score", 0),
            "summary": f"{stats.get('total_concepts', 0)} concepts, {len(orphans)} orphans",
        }
        modules.append("knowledge")
    except ImportError:
        advanced["knowledge"] = {"error": "Module not installed"}
    except Exception as e:
        advanced["knowledge"] = {"error": str(e)}

    # Norwegian readability summary
    try:
        from ...readability.norwegian import NorwegianReadabilityAnalyzer

        analyzer = NorwegianReadabilityAnalyzer(project)
        results = analyzer.analyze_all()

        if results:
            avg_lix = sum(r.lix for r in results) / len(results)
            difficult = len([r for r in results if r.difficulty_level == "very_difficult"])
            easy = len([r for r in results if r.difficulty_level in ["easy", "very_easy"]])

            advanced["readability"] = {
                "norwegian_documents": len(results),
                "average_lix": round(avg_lix, 1),
                "very_difficult_count": difficult,
                "easy_count": easy,
                "summary": f"Avg LIX: {avg_lix:.1f}, {difficult} difficult docs",
            }
            modules.append("norwegian_readability")
    except ImportError:
        pass
    except Exception:
        pass

    # Predictive freshness summary
    try:
        from ...freshness.predictive import PredictiveFreshnessModel

        model = PredictiveFreshnessModel(project)
        predictions = model.predict_staleness()

        if predictions:
            high_risk = [p for p in predictions if p.risk_score > 0.7]
            medium_risk = [p for p in predictions if 0.4 <= p.risk_score <= 0.7]

            advanced["freshness"] = {
                "total_analyzed": len(predictions),
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "average_risk": round(sum(p.risk_score for p in predictions) / len(predictions), 2),
                "summary": f"{len(high_risk)} high-risk, {len(medium_risk)} medium-risk documents",
            }
            modules.append("predictive_freshness")
    except ImportError:
        advanced["freshness"] = {"error": "Module not installed"}
    except Exception as e:
        advanced["freshness"] = {"error": str(e)}

    # Code-doc sync summary
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        issues = checker.get_all_issues()

        critical = len([i for i in issues if i.severity == "critical"])
        warnings = len([i for i in issues if i.severity == "warning"])

        advanced["codesync"] = {
            "total_issues": len(issues),
            "critical_issues": critical,
            "warning_issues": warnings,
            "summary": f"{critical} critical, {warnings} warning sync issues",
        }
        modules.append("codesync")
    except ImportError:
        advanced["codesync"] = {"error": "Module not installed"}
    except Exception as e:
        advanced["codesync"] = {"error": str(e)}

    # Advanced analysis (audience, style, engagement)
    try:
        from ...advanced import AudienceAnalyzer, StyleAnalyzer

        audience_analyzer = AudienceAnalyzer(project)
        drift = audience_analyzer.detect_audience_drift()

        style_analyzer = StyleAnalyzer(project)
        style_issues = style_analyzer.check_consistency()

        advanced["advanced"] = {
            "audience_drift_severity": drift.severity if drift else "none",
            "style_inconsistencies": len(style_issues) if style_issues else 0,
            "summary": f"Audience drift: {drift.severity if drift else 'none'}, {len(style_issues) if style_issues else 0} style issues",
        }
        modules.append("advanced")
    except ImportError:
        advanced["advanced"] = {"error": "Module not installed"}
    except Exception as e:
        advanced["advanced"] = {"error": str(e)}

    advanced["modules_available"] = modules

    return advanced
