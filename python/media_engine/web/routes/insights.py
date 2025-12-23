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
            ConsistencyChecker,
            HealthScorer,
            IncompleteTracker,
            KnowledgeGraph,
            ParityAnalyzer,
            StatisticsCollector,
            VelocityTracker,
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

    @router.get("/api/insights/stats")
    async def get_stats():
        """Alias for /api/insights/statistics."""
        return await get_statistics()

    @router.get("/api/insights/overview")
    async def get_overview():
        """Alias for /api/insights - Get project overview."""
        return await get_insights()

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

    @router.get("/api/insights/terminology")
    async def get_terminology():
        """Alias for /api/insights/terms - Get terminology issues."""
        return await get_terms()

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

    # ============== ADVANCED ANALYSIS ENDPOINTS ==============

    @router.get("/api/insights/advanced")
    async def get_advanced_insights():
        """Get comprehensive advanced analysis results."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        result = {
            "semantic": None,
            "llm_quality": None,
            "knowledge_graph": None,
            "norwegian_readability": None,
            "predictive_freshness": None,
            "enhanced_codesync": None,
            "advanced_analysis": None,
        }

        # Semantic Analysis
        try:
            from ...semantic import SemanticAnalyzer

            analyzer = SemanticAnalyzer(project)
            duplicates = analyzer.find_near_duplicates(threshold=0.85)
            drift = analyzer.detect_terminology_drift()
            clusters = analyzer.cluster_content(n_clusters=5)
            result["semantic"] = {
                "available": True,
                "near_duplicates": [d.to_dict() for d in duplicates[:10]],
                "near_duplicate_count": len(duplicates),
                "terminology_drift": [d.to_dict() for d in drift[:10]],
                "drift_count": len(drift),
                "clusters": [
                    {"id": c.cluster_id, "theme": c.topic, "doc_count": len(c.documents)}
                    for c in clusters
                ],
                "cluster_count": len(clusters),
            }
        except ImportError:
            result["semantic"] = {"available": False, "reason": "semantic module not installed"}
        except Exception as e:
            result["semantic"] = {"available": True, "error": str(e)}

        # Knowledge Graph (enhanced)
        try:
            from ...knowledge import KnowledgeGraph as EnhancedKG

            kg = EnhancedKG(project)
            kg.build()
            orphans = kg.find_orphan_concepts()
            prereq_issues = kg.validate_prerequisites()
            metrics = kg.compute_metrics()
            result["knowledge_graph"] = {
                "available": True,
                "metrics": metrics.to_dict() if hasattr(metrics, "to_dict") else vars(metrics),
                "orphan_concepts": [
                    o.to_dict() if hasattr(o, "to_dict") else o for o in orphans[:10]
                ],
                "orphan_count": len(orphans),
                "prerequisite_issues": [
                    p.to_dict() if hasattr(p, "to_dict") else p for p in prereq_issues[:10]
                ],
                "prereq_issue_count": len(prereq_issues),
            }
        except ImportError as e:
            result["knowledge_graph"] = {
                "available": False,
                "reason": f"networkx package required: {e}",
            }
        except Exception as e:
            result["knowledge_graph"] = {"available": True, "error": str(e)}

        # Norwegian Readability
        try:
            from ...readability.norwegian import NorwegianReadabilityChecker

            checker = NorwegianReadabilityChecker()
            project_results = checker.check_project(project, language="no")

            if "error" not in project_results:
                reports = project_results.get("documents", [])
                avg_lix = project_results.get("summary", {}).get("average_lix", 0)
                difficult_docs = [
                    r for r in reports if r.get("lix_level") in ("difficult", "very_difficult")
                ]
                result["norwegian_readability"] = {
                    "available": True,
                    "documents_analyzed": len(reports),
                    "average_lix": round(avg_lix, 1),
                    "difficulty_distribution": {},
                    "difficult_documents": [
                        {"path": r["file"], "lix": r["lix"], "level": r["lix_level"]}
                        for r in difficult_docs[:10]
                    ],
                    "difficult_count": len(difficult_docs),
                }
            else:
                result["norwegian_readability"] = {
                    "available": True,
                    "message": project_results["error"],
                }
        except ImportError:
            result["norwegian_readability"] = {
                "available": False,
                "reason": "norwegian readability module not installed",
            }
        except Exception as e:
            result["norwegian_readability"] = {"available": True, "error": str(e)}

        # Predictive Freshness
        try:
            from ...freshness.predictive import FreshnessPredictor

            predictor = FreshnessPredictor(project)
            predictor.train()
            report = predictor.generate_report()
            predictions = report.predictions
            high_risk = [p for p in predictions if p.risk_level in ("high", "critical")]
            queue = report.review_priority_queue
            result["predictive_freshness"] = {
                "available": True,
                "predictions_count": len(predictions),
                "high_risk_count": len(high_risk),
                "high_risk_documents": [
                    {
                        "path": str(p.path),
                        "risk_level": p.risk_level,
                        "staleness_probability": round(p.staleness_risk, 2),
                        "days_until_stale": p.days_until_stale,
                    }
                    for p in high_risk[:10]
                ],
                "review_queue": [
                    {
                        "path": q["path"],
                        "priority": q["risk"],
                        "reason": q.get("recommendation", ""),
                    }
                    for q in queue[:10]
                ]
                if queue
                else [],
            }
        except ImportError:
            result["predictive_freshness"] = {
                "available": False,
                "reason": "predictive freshness module not installed",
            }
        except Exception as e:
            result["predictive_freshness"] = {"available": True, "error": str(e)}

        # Enhanced CodeSync
        try:
            from ...codesync import EnhancedCodeSyncChecker, SyncIssueType

            checker = EnhancedCodeSyncChecker(project)
            summary = checker.generate_summary()

            # Extract issues by type from all documents
            all_issues = []
            for doc in summary.get("documents", []):
                for issue in doc.get("issues", []):
                    issue["document"] = doc.get("document", "unknown")
                    all_issues.append(issue)

            syntax_errors = [i for i in all_issues if i.get("issue_type") == "syntax_error"]
            deprecated = [i for i in all_issues if i.get("issue_type") == "deprecated"]
            api_issues = [i for i in all_issues if i.get("issue_type") == "api_changed"]

            result["enhanced_codesync"] = {
                "available": True,
                "syntax_errors": syntax_errors[:10],
                "syntax_error_count": len(syntax_errors),
                "deprecated_patterns": deprecated[:10],
                "deprecated_count": len(deprecated),
                "api_issues": api_issues[:10],
                "api_issue_count": len(api_issues),
                "total_issues": len(syntax_errors) + len(deprecated) + len(api_issues),
            }
        except ImportError:
            result["enhanced_codesync"] = {
                "available": False,
                "reason": "codesync module not installed",
            }
        except Exception as e:
            result["enhanced_codesync"] = {"available": True, "error": str(e)}

        # Advanced Analysis (audience drift, questions, style)
        try:
            from ...advanced import AdvancedAnalyzer

            analyzer = AdvancedAnalyzer(project)
            report = analyzer.analyze_project()
            # Convert report to dict if it's a dataclass/object
            if hasattr(report, "to_dict"):
                report_dict = report.to_dict()
            elif hasattr(report, "__dict__"):
                report_dict = vars(report)
            else:
                report_dict = report if isinstance(report, dict) else {}

            result["advanced_analysis"] = {
                "available": True,
                "audience_drift": report_dict.get("audience_drift", []),
                "question_coverage": report_dict.get("question_coverage", []),
                "cross_references": report_dict.get("cross_reference_metrics", []),
                "structure_analysis": report_dict.get("structure_analyses", []),
                "style_consistency": report_dict.get("style_consistency", []),
                "overall_quality_score": report_dict.get("overall_quality_score", 0),
            }
        except ImportError:
            result["advanced_analysis"] = {
                "available": False,
                "reason": "advanced module not installed",
            }
        except Exception as e:
            result["advanced_analysis"] = {"available": True, "error": str(e)}

        return result

    @router.get("/api/insights/semantic")
    async def get_semantic_analysis(
        duplicates: bool = False,
        drift: bool = False,
        clusters: bool = False,
        contradictions: bool = False,
        threshold: float = 0.85,
    ):
        """Get semantic similarity analysis."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        try:
            from ...semantic import SemanticAnalyzer

            analyzer = SemanticAnalyzer(project)
            result = {"available": True}

            if duplicates or not any([duplicates, drift, clusters, contradictions]):
                dups = analyzer.find_near_duplicates(threshold=threshold)
                result["near_duplicates"] = [d.to_dict() for d in dups]

            if drift:
                drift_items = analyzer.detect_terminology_drift()
                result["terminology_drift"] = [d.to_dict() for d in drift_items]

            if clusters:
                cluster_items = analyzer.cluster_content(n_clusters=5)
                result["clusters"] = [c.to_dict() for c in cluster_items]

            if contradictions:
                contradictions_items = analyzer.find_contradictions()
                result["contradictions"] = [c.to_dict() for c in contradictions_items]

            return result
        except ImportError:
            return {"available": False, "reason": "semantic module not installed"}
        except Exception as e:
            return {"available": True, "error": str(e)}

    @router.get("/api/insights/knowledge-graph")
    async def get_enhanced_knowledge_graph(
        build: bool = True,
        orphans: bool = False,
        prerequisites: bool = False,
        metrics: bool = False,
        path_from: str = None,
    ):
        """Get enhanced knowledge graph analysis."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        try:
            from ...knowledge import KnowledgeGraph as EnhancedKG

            kg = EnhancedKG(project)
            if build:
                kg.build()

            result = {"available": True}

            if orphans:
                result["orphan_concepts"] = kg.find_orphan_concepts()

            if prerequisites:
                issues = kg.validate_prerequisites()
                result["prerequisite_issues"] = [
                    p.to_dict() if hasattr(p, "to_dict") else p for p in issues
                ]

            if metrics:
                result["metrics"] = kg.get_metrics()

            if path_from:
                path = kg.generate_reading_path(start_concept=path_from)
                result["reading_path"] = path

            # Always include basic graph structure
            result["node_count"] = kg.graph.number_of_nodes() if hasattr(kg, "graph") else 0
            result["edge_count"] = kg.graph.number_of_edges() if hasattr(kg, "graph") else 0

            return result
        except ImportError as e:
            return {"available": False, "reason": f"networkx package required: {e}"}
        except Exception as e:
            return {"available": True, "error": str(e)}

    @router.get("/api/insights/knowledge")
    async def get_knowledge():
        """Alias for /api/insights/knowledge-graph."""
        return await get_enhanced_knowledge_graph()

    @router.get("/api/insights/norwegian-readability")
    async def get_norwegian_readability(document: str = None, target: str = None):
        """Get Norwegian LIX readability analysis."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        try:
            from ...readability.norwegian import NorwegianReadabilityChecker

            checker = NorwegianReadabilityChecker()

            if document:
                doc_path = project.content_dir / document
                if doc_path.exists():
                    report = checker.check_document(doc_path)
                    return {
                        "available": True,
                        "document": document,
                        "lix_score": report.metrics.lix,
                        "difficulty_level": report.metrics.lix_level.value,
                        "word_count": report.metrics.word_count,
                        "sentence_count": report.metrics.sentence_count,
                        "long_word_count": report.metrics.long_word_count,
                        "suggestions": [
                            {"message": i.message, "suggestion": i.suggestion}
                            for i in report.issues
                        ],
                    }
                else:
                    return {"error": f"Document not found: {document}"}
            else:
                project_results = checker.check_project(project, language="no")
                if "error" in project_results:
                    return {"available": True, "message": project_results["error"]}

                reports = project_results.get("documents", [])
                summary = project_results.get("summary", {})
                return {
                    "available": True,
                    "documents": [
                        {
                            "path": r["file"],
                            "lix_score": r["lix"],
                            "difficulty_level": r["lix_level"],
                            "word_count": r["word_count"],
                        }
                        for r in reports
                    ],
                    "summary": {
                        "total_documents": summary.get("total_documents", 0),
                        "average_lix": summary.get("average_lix", 0),
                        "by_difficulty": {},
                    },
                }
        except ImportError:
            return {"available": False, "reason": "norwegian readability module not installed"}
        except Exception as e:
            return {"available": True, "error": str(e)}

    @router.get("/api/insights/predictive-freshness")
    async def get_predictive_freshness(train: bool = False, days: int = 90):
        """Get predictive staleness analysis."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        try:
            from ...freshness.predictive import FreshnessPredictor

            predictor = FreshnessPredictor(project)
            predictor.train()
            report = predictor.generate_report()
            predictions = report.predictions

            return {
                "available": True,
                "predictions": [
                    {
                        "path": str(p.path),
                        "risk_level": p.risk_level,
                        "staleness_probability": round(p.staleness_risk, 2),
                        "days_until_stale": p.days_until_stale,
                        "contributing_factors": p.contributing_factors,
                    }
                    for p in predictions
                ],
                "review_queue": report.review_priority_queue,
                "summary": {
                    "total": len(predictions),
                    "low_risk": len([p for p in predictions if p.risk_level == "low"]),
                    "medium_risk": len([p for p in predictions if p.risk_level == "medium"]),
                    "high_risk": len([p for p in predictions if p.risk_level == "high"]),
                    "critical_risk": len([p for p in predictions if p.risk_level == "critical"]),
                },
            }
        except ImportError:
            return {"available": False, "reason": "predictive freshness module not installed"}
        except Exception as e:
            return {"available": True, "error": str(e)}

    @router.get("/api/insights/freshness-predictions")
    async def get_freshness_predictions():
        """Alias for /api/insights/predictive-freshness."""
        return await get_predictive_freshness()

    @router.get("/api/insights/enhanced-codesync")
    async def get_enhanced_codesync(
        syntax: bool = True,
        deprecated: bool = True,
        api_refs: bool = True,
        document: str = None,
    ):
        """Get enhanced code-documentation sync analysis."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        try:
            from ...codesync import EnhancedCodeSyncChecker

            checker = EnhancedCodeSyncChecker(project)

            if document:
                doc_report = checker.check_document(Path(document))
                # Convert single document report to issue format
                all_issues = []
                if hasattr(doc_report, "issues"):
                    for issue in doc_report.issues:
                        issue_dict = issue.to_dict() if hasattr(issue, "to_dict") else vars(issue)
                        issue_dict["document"] = document
                        all_issues.append(issue_dict)
                syntax_errors = [i for i in all_issues if i.get("issue_type") == "syntax_error"]
                deprecated_patterns = [
                    i for i in all_issues if i.get("issue_type") == "deprecated_pattern"
                ]
                api_issues = [i for i in all_issues if i.get("issue_type") == "api_mismatch"]
            else:
                # Get summary of all documents
                summary_report = checker.generate_summary()
                # Extract issues by type from all documents
                all_issues = []
                for doc in summary_report.get("documents", []):
                    for issue in doc.get("issues", []):
                        issue["document"] = doc.get("document", "unknown")
                        all_issues.append(issue)
                syntax_errors = [i for i in all_issues if i.get("issue_type") == "syntax_error"]
                deprecated_patterns = [
                    i for i in all_issues if i.get("issue_type") == "deprecated_pattern"
                ]
                api_issues = [i for i in all_issues if i.get("issue_type") == "api_mismatch"]

            result = {"available": True}

            if syntax:
                result["syntax_errors"] = syntax_errors

            if deprecated:
                result["deprecated_patterns"] = deprecated_patterns

            if api_refs:
                result["api_issues"] = api_issues

            result["summary"] = {
                "total_issues": len(all_issues),
                "documents_with_issues": len(set(i.get("document", "") for i in all_issues)),
            }

            return result
        except ImportError:
            return {"available": False, "reason": "codesync module not installed"}
        except Exception as e:
            return {"available": True, "error": str(e)}

    @router.get("/api/insights/advanced-analysis")
    async def get_advanced_analysis(
        audience_drift: bool = False,
        questions: bool = False,
        crossrefs: bool = False,
        structure: bool = False,
        style: bool = False,
        full: bool = False,
        document: str = None,
    ):
        """Get advanced content analysis."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        try:
            from ...advanced import AdvancedAnalyzer

            analyzer = AdvancedAnalyzer(project)
            result = {"available": True}

            # If full or no specific flags, run all
            run_all = full or not any([audience_drift, questions, crossrefs, structure, style])

            if document:
                doc_path = Path(document)
                if run_all or audience_drift:
                    result["audience_drift"] = analyzer.analyze_audience_drift(doc_path)
                if run_all or questions:
                    result["question_coverage"] = analyzer.analyze_question_coverage(doc_path)
                if run_all or crossrefs:
                    result["cross_references"] = analyzer.analyze_cross_references(doc_path)
                if run_all or structure:
                    result["structure"] = analyzer.analyze_structure(doc_path)
                if run_all or style:
                    result["style"] = analyzer.analyze_style_consistency(doc_path)
            else:
                report = analyzer.analyze_project()
                # Convert report to dict if it's a dataclass/object
                if hasattr(report, "to_dict"):
                    report_dict = report.to_dict()
                elif hasattr(report, "__dict__"):
                    report_dict = vars(report)
                else:
                    report_dict = report if isinstance(report, dict) else {}
                if run_all:
                    result.update(report_dict)
                else:
                    if audience_drift:
                        result["audience_drift"] = report_dict.get("audience_drift", {})
                    if questions:
                        result["question_coverage"] = report_dict.get("question_coverage", {})
                    if crossrefs:
                        result["cross_references"] = report_dict.get("cross_references", {})
                    if structure:
                        result["structure"] = report_dict.get("structure", {})
                    if style:
                        result["style"] = report_dict.get("style", {})

            return result
        except ImportError:
            return {"available": False, "reason": "advanced module not installed"}
        except Exception as e:
            return {"available": True, "error": str(e)}

    @router.get("/api/insights/quality-summary")
    async def get_quality_summary():
        """Get intelligent quality summary for dashboard."""
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...insights import (
            HealthScorer,
        )

        summary = {
            "overall_score": 0,
            "grade": "N/A",
            "status": "unknown",
            "key_metrics": [],
            "critical_issues": [],
            "recommendations": [],
            "advanced_available": {
                "semantic": False,
                "knowledge_graph": False,
                "norwegian_readability": False,
                "predictive_freshness": False,
                "enhanced_codesync": False,
                "advanced_analysis": False,
            },
            "advanced_highlights": {},
        }

        # Core health score
        try:
            scorer = HealthScorer(project)
            health = scorer.score_project()
            summary["overall_score"] = health.overall
            summary["grade"] = health.grade
            summary["status"] = health.status
            summary["key_metrics"] = [
                {"name": k, "score": v, "weight": health.weights.get(k, 0)}
                for k, v in health.components.items()
            ]
            summary["critical_issues"] = [
                i.to_dict() for i in health.issues if i.severity == "critical"
            ][:5]
            summary["recommendations"] = health.recommendations[:5]
        except Exception as e:
            summary["health_error"] = str(e)

        # Check advanced module availability and get highlights
        try:
            from ...semantic import SemanticAnalyzer

            summary["advanced_available"]["semantic"] = True
            analyzer = SemanticAnalyzer(project)
            dups = analyzer.find_near_duplicates(threshold=0.9)
            if dups:
                summary["advanced_highlights"]["semantic"] = {
                    "near_duplicates": len(dups),
                    "message": f"Found {len(dups)} near-duplicate content pairs",
                }
        except ImportError:
            pass
        except Exception:
            summary["advanced_available"]["semantic"] = True

        try:
            from ...knowledge import KnowledgeGraph as EnhancedKG

            summary["advanced_available"]["knowledge_graph"] = True
            kg = EnhancedKG(project)
            kg.build()
            orphans = kg.find_orphan_concepts()
            if orphans:
                summary["advanced_highlights"]["knowledge_graph"] = {
                    "orphan_concepts": len(orphans),
                    "message": f"Found {len(orphans)} orphan concepts without connections",
                }
        except ImportError:
            pass
        except Exception:
            summary["advanced_available"]["knowledge_graph"] = True

        try:
            from ...readability.norwegian import NorwegianReadabilityChecker

            summary["advanced_available"]["norwegian_readability"] = True
        except ImportError:
            pass

        try:
            from ...freshness.predictive import FreshnessPredictor

            summary["advanced_available"]["predictive_freshness"] = True
            predictor = FreshnessPredictor(project)
            predictor.train_from_history(days=60)
            predictions = predictor.predict_all()
            high_risk = [p for p in predictions if p.risk_level in ("high", "critical")]
            if high_risk:
                summary["advanced_highlights"]["predictive_freshness"] = {
                    "high_risk_count": len(high_risk),
                    "message": f"{len(high_risk)} documents predicted to become stale soon",
                }
        except ImportError:
            pass
        except Exception:
            summary["advanced_available"]["predictive_freshness"] = True

        try:
            from ...codesync import EnhancedCodeSyncChecker

            summary["advanced_available"]["enhanced_codesync"] = True
            checker = EnhancedCodeSyncChecker(project)
            report = checker.generate_summary()
            total_issues = report.get("total_issues", 0)
            if total_issues > 0:
                summary["advanced_highlights"]["enhanced_codesync"] = {
                    "issues": total_issues,
                    "message": f"{total_issues} code-documentation sync issues found",
                }
        except ImportError:
            pass
        except Exception:
            summary["advanced_available"]["enhanced_codesync"] = True

        try:
            from ...advanced import AdvancedAnalyzer

            summary["advanced_available"]["advanced_analysis"] = True
        except ImportError:
            pass

        return summary

    @router.get("/api/insights/comprehensive")
    async def get_comprehensive():
        """Alias for /api/insights/quality-summary - Get comprehensive quality report."""
        return await get_quality_summary()
