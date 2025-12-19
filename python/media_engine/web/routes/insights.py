"""API routes for project insights."""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

if TYPE_CHECKING:
    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_insights_routes(
    router: APIRouter,
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register insights API routes."""

    @router.get("/api/insights")
    async def get_insights():
        """Get comprehensive project insights."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import (
            HealthScorer,
            StatisticsCollector,
            IncompleteTracker,
            ConsistencyChecker,
            ParityAnalyzer,
            VelocityTracker,
            KnowledgeGraph,
        )

        result = {}

        # Health score
        try:
            scorer = HealthScorer(project)
            health = scorer.score_project()
            result["health"] = health.to_dict()
        except Exception as e:
            result["health"] = {"error": str(e)}

        # Statistics
        try:
            collector = StatisticsCollector(project)
            stats = collector.collect()
            result["statistics"] = stats.to_dict()
        except Exception as e:
            result["statistics"] = {"error": str(e)}

        # Incomplete content
        try:
            tracker = IncompleteTracker(project)
            items = tracker.scan_project()
            summary = tracker.get_summary()
            result["incomplete"] = {
                "total": summary["total"],
                "debt_score": summary["debt_score"],
                "items": [i.to_dict() for i in items[:10]],
            }
        except Exception as e:
            result["incomplete"] = {"error": str(e)}

        # Consistency issues
        try:
            checker = ConsistencyChecker(project)
            issues = checker.check_project()
            result["consistency"] = [i.to_dict() for i in issues[:10]]
        except Exception as e:
            result["consistency"] = {"error": str(e)}

        # Translation parity
        try:
            analyzer = ParityAnalyzer(project)
            parity = analyzer.analyze()
            result["parity"] = parity.to_dict()
        except Exception as e:
            result["parity"] = {"error": str(e)}

        # Velocity
        try:
            velocity_tracker = VelocityTracker(project)
            metrics = velocity_tracker.get_metrics(days=30)
            result["velocity"] = metrics.to_dict()
        except Exception as e:
            result["velocity"] = {"error": str(e)}

        # Knowledge graph summary
        try:
            graph = KnowledgeGraph(project)
            nodes, edges = graph.build_graph()
            hubs = graph.find_hubs()
            orphans = graph.find_orphans()
            result["graph"] = {
                "nodes": [n.to_dict() for n in nodes],
                "links": [e.to_dict() for e in edges],
                "hubs": len(hubs),
                "orphans": len(orphans),
            }
        except Exception as e:
            result["graph"] = {"error": str(e)}

        return result

    @router.get("/api/insights/health")
    async def get_health(document: str = None):
        """Get health score for project or specific document."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import HealthScorer

        scorer = HealthScorer(project)

        if document:
            health = scorer.score_document(Path(document))
        else:
            health = scorer.score_project()

        return health.to_dict() if hasattr(health, "to_dict") else health

    @router.get("/api/insights/statistics")
    async def get_statistics():
        """Get project statistics."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import StatisticsCollector

        collector = StatisticsCollector(project)
        stats = collector.collect()

        return stats.to_dict()

    @router.get("/api/insights/incomplete")
    async def get_incomplete(priority: str = None):
        """Get incomplete content items."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import IncompleteTracker

        tracker = IncompleteTracker(project)

        if priority:
            items = tracker.get_by_priority(priority)
        else:
            items = tracker.scan_project()

        return {
            "total": len(items),
            "items": [i.to_dict() for i in items],
            "summary": tracker.get_summary(),
        }

    @router.get("/api/insights/consistency")
    async def get_consistency():
        """Get status consistency issues."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        issues = checker.check_project()

        return {
            "total": len(issues),
            "issues": [i.to_dict() for i in issues],
        }

    @router.get("/api/insights/parity")
    async def get_parity(primary: str = "en"):
        """Get translation parity matrix."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import ParityAnalyzer

        analyzer = ParityAnalyzer(project, primary_language=primary)
        report = analyzer.analyze()

        return report.to_dict()

    @router.get("/api/insights/velocity")
    async def get_velocity(days: int = 30):
        """Get content velocity metrics."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import VelocityTracker

        tracker = VelocityTracker(project)
        metrics = tracker.get_metrics(days=days)

        return metrics.to_dict()

    @router.get("/api/insights/graph")
    async def get_graph(format: str = "json"):
        """Get knowledge graph."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        graph.build_graph()

        if format == "dot":
            return PlainTextResponse(graph.export_dot(), media_type="text/plain")
        elif format == "cytoscape":
            return graph.export_cytoscape()
        else:
            return graph.export_json()

    @router.get("/api/insights/path")
    async def get_path(
        type: str = Query("dependency", description="Path type: dependency, complexity, persona"),
        persona: str = None,
        lang: str = "en",
    ):
        """Get reading path."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import PathGenerator

        generator = PathGenerator(project, language=lang)

        if type == "persona" and persona:
            path = generator.generate_persona_path(persona)
        elif type == "complexity":
            path = generator.generate_complexity_path()
        else:
            path = generator.generate_dependency_path()

        return path.to_dict()

    @router.get("/api/insights/terms")
    async def get_terms():
        """Get terminology issues."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import TerminologyChecker

        checker = TerminologyChecker(project)
        issues = checker.find_inconsistencies()

        return {
            "total": len(issues),
            "issues": [i.to_dict() for i in issues],
        }

    @router.get("/api/insights/duplicates")
    async def get_duplicates(exact_only: bool = False):
        """Get duplicate content."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import DuplicateDetector

        detector = DuplicateDetector(project)

        if exact_only:
            matches = detector.find_exact_duplicates()
        else:
            report = detector.generate_report()
            matches = report.exact_duplicates + report.similar_content

        return {
            "total": len(matches),
            "matches": [m.to_dict() for m in matches],
        }

    @router.get("/api/insights/codesync")
    async def get_codesync():
        """Get code-documentation sync status."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import CodeSyncChecker

        checker = CodeSyncChecker(project)
        statuses = checker.check_project()

        stale_docs = [s for s in statuses if s.needs_review]

        return {
            "total_checked": len(statuses),
            "stale_count": len(stale_docs),
            "stale_documents": [s.to_dict() for s in stale_docs],
        }
