"""
Comprehensive Quality Reporting Tools for MCP.

These tools provide structured quality data to LLM agents.
The LLM agent (Claude Code) applies judgment on top of programmatic analysis.

Architecture:
- All analysis is PROGRAMMATIC (no LLM calls here)
- Data is structured for LLM consumption
- Reports can be general (project-wide) or specific (per-document)
- The calling LLM agent interprets and acts on the data
"""

import json
from datetime import datetime
from pathlib import Path


def register_report_tools(mcp, server_instance):
    """Register comprehensive reporting MCP tools."""

    def _get_project():
        """Get current project or raise error."""
        if not server_instance.project:
            return None
        return server_instance.project

    def _safe_import(module_path: str, class_name: str):
        """Safely import a module, returning None if not available."""
        try:
            import importlib

            module = importlib.import_module(module_path)
            return getattr(module, class_name, None)
        except ImportError:
            return None
        except Exception:
            return None

    # ============== COMPREHENSIVE REPORTS ==============

    @mcp.tool()
    async def quality_report_comprehensive() -> str:
        """
        Generate a comprehensive quality report aggregating ALL programmatic analysis.

        This is the main entry point for LLM agents to get project quality status.
        Returns structured data from all available analysis modules:
        - Core health metrics
        - Freshness status
        - Semantic analysis (duplicates, drift, clusters)
        - Knowledge graph (orphans, prerequisites)
        - Code sync issues
        - Readability scores
        - Advanced analysis (audience drift, questions, style)

        The LLM agent can then apply judgment and prioritize actions.
        """
        project = _get_project()
        if not project:
            return json.dumps({"error": "No project loaded"}, indent=2)

        report = {
            "generated_at": datetime.now().isoformat(),
            "project": {
                "name": project.config.name
                if hasattr(project.config, "name")
                else str(project.root.name),
                "root": str(project.root),
            },
            "modules": {},
            "summary": {
                "overall_health": None,
                "critical_issues": 0,
                "warnings": 0,
                "available_modules": [],
                "unavailable_modules": [],
            },
            "recommendations": [],
        }

        # Core Health Score
        try:
            from ...insights import HealthScorer

            scorer = HealthScorer(project)
            health = scorer.score_project()
            report["modules"]["health"] = {
                "available": True,
                "overall_score": health.overall,
                "grade": health.grade,
                "status": health.status,
                "components": health.components,
                "issues": [i.to_dict() for i in health.issues[:20]],
                "issue_count": len(health.issues),
            }
            report["summary"]["overall_health"] = health.overall
            report["summary"]["critical_issues"] = len(
                [i for i in health.issues if i.severity == "critical"]
            )
            report["summary"]["warnings"] = len(
                [i for i in health.issues if i.severity == "warning"]
            )
            report["recommendations"].extend(health.recommendations[:5])
            report["summary"]["available_modules"].append("health")
        except Exception as e:
            report["modules"]["health"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("health")

        # Freshness
        try:
            from ...freshness import FreshnessRegistry, FreshnessScanner

            registry = FreshnessRegistry(project)
            scanner = FreshnessScanner(project)
            stale = scanner.find_stale(days=30)
            report["modules"]["freshness"] = {
                "available": True,
                "total_tracked": len(registry.entries) if hasattr(registry, "entries") else 0,
                "stale_count": len(stale),
                "stale_documents": [
                    {
                        "path": str(s.path),
                        "days_old": s.days_since_update
                        if hasattr(s, "days_since_update")
                        else None,
                    }
                    for s in stale[:10]
                ],
            }
            report["summary"]["available_modules"].append("freshness")
        except Exception as e:
            report["modules"]["freshness"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("freshness")

        # Semantic Analysis
        try:
            from ...semantic import SemanticAnalyzer

            analyzer = SemanticAnalyzer(project)
            duplicates = analyzer.find_near_duplicates(threshold=0.85)
            drift = analyzer.detect_terminology_drift()
            clusters = analyzer.cluster_content(n_clusters=5)
            report["modules"]["semantic"] = {
                "available": True,
                "near_duplicates": {
                    "count": len(duplicates),
                    "pairs": [d.to_dict() for d in duplicates[:5]],
                },
                "terminology_drift": {
                    "count": len(drift),
                    "items": [d.to_dict() for d in drift[:5]],
                },
                "content_clusters": {
                    "count": len(clusters),
                    "clusters": [
                        {"id": c.cluster_id, "theme": c.theme, "doc_count": len(c.documents)}
                        for c in clusters
                    ],
                },
            }
            report["summary"]["available_modules"].append("semantic")
            if duplicates:
                report["recommendations"].append(
                    f"Review {len(duplicates)} near-duplicate content pairs for consolidation"
                )
            if drift:
                report["recommendations"].append(
                    f"Address {len(drift)} terminology inconsistencies"
                )
        except ImportError:
            report["modules"]["semantic"] = {
                "available": False,
                "reason": "semantic module not installed",
            }
            report["summary"]["unavailable_modules"].append("semantic")
        except Exception as e:
            report["modules"]["semantic"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("semantic")

        # Knowledge Graph
        try:
            from ...knowledge import KnowledgeGraph

            kg = KnowledgeGraph(project)
            kg.build()
            orphans = kg.find_orphan_concepts()
            prereq_issues = kg.validate_prerequisites()
            metrics = kg.get_metrics()
            report["modules"]["knowledge_graph"] = {
                "available": True,
                "metrics": metrics,
                "orphan_concepts": {
                    "count": len(orphans),
                    "items": orphans[:10],
                },
                "prerequisite_issues": {
                    "count": len(prereq_issues),
                    "items": [
                        p.to_dict() if hasattr(p, "to_dict") else str(p) for p in prereq_issues[:10]
                    ],
                },
            }
            report["summary"]["available_modules"].append("knowledge_graph")
            if orphans:
                report["recommendations"].append(
                    f"Connect {len(orphans)} orphan concepts to the knowledge graph"
                )
            if prereq_issues:
                report["recommendations"].append(
                    f"Fix {len(prereq_issues)} prerequisite chain issues"
                )
        except ImportError:
            report["modules"]["knowledge_graph"] = {
                "available": False,
                "reason": "knowledge module not installed",
            }
            report["summary"]["unavailable_modules"].append("knowledge_graph")
        except Exception as e:
            report["modules"]["knowledge_graph"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("knowledge_graph")

        # Enhanced Code Sync
        try:
            from ...codesync import EnhancedCodeSyncChecker

            checker = EnhancedCodeSyncChecker(project)
            codesync_report = checker.generate_summary()
            syntax_errors = codesync_report.get("syntax_errors", [])
            deprecated = codesync_report.get("deprecated_patterns", [])
            api_issues = codesync_report.get("api_issues", [])
            report["modules"]["codesync"] = {
                "available": True,
                "syntax_errors": {
                    "count": len(syntax_errors),
                    "items": syntax_errors[:10],
                },
                "deprecated_patterns": {
                    "count": len(deprecated),
                    "items": deprecated[:10],
                },
                "api_issues": {
                    "count": len(api_issues),
                    "items": api_issues[:10],
                },
                "total_issues": len(syntax_errors) + len(deprecated) + len(api_issues),
            }
            report["summary"]["available_modules"].append("codesync")
            if syntax_errors:
                report["recommendations"].append(
                    f"Fix {len(syntax_errors)} syntax errors in code examples"
                )
            if deprecated:
                report["recommendations"].append(
                    f"Update {len(deprecated)} deprecated code patterns"
                )
        except ImportError:
            report["modules"]["codesync"] = {
                "available": False,
                "reason": "codesync module not installed",
            }
            report["summary"]["unavailable_modules"].append("codesync")
        except Exception as e:
            report["modules"]["codesync"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("codesync")

        # Norwegian Readability (LIX)
        try:
            from ...readability.norwegian import NorwegianReadabilityChecker

            checker = NorwegianReadabilityChecker(project)
            lix_reports = checker.analyze_all_documents()
            avg_lix = sum(r.lix_score for r in lix_reports) / len(lix_reports) if lix_reports else 0
            difficult = [
                r for r in lix_reports if r.difficulty_level in ("difficult", "very_difficult")
            ]
            report["modules"]["norwegian_readability"] = {
                "available": True,
                "documents_analyzed": len(lix_reports),
                "average_lix": round(avg_lix, 1),
                "difficult_documents": {
                    "count": len(difficult),
                    "items": [
                        {
                            "path": str(r.document_path),
                            "lix": r.lix_score,
                            "level": r.difficulty_level,
                        }
                        for r in difficult[:10]
                    ],
                },
            }
            report["summary"]["available_modules"].append("norwegian_readability")
            if difficult:
                report["recommendations"].append(
                    f"Simplify {len(difficult)} documents with high LIX scores"
                )
        except ImportError:
            report["modules"]["norwegian_readability"] = {
                "available": False,
                "reason": "norwegian readability module not installed",
            }
            report["summary"]["unavailable_modules"].append("norwegian_readability")
        except Exception as e:
            report["modules"]["norwegian_readability"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("norwegian_readability")

        # Predictive Freshness
        try:
            from ...freshness.predictive import FreshnessPredictor

            predictor = FreshnessPredictor(project)
            predictor.train_from_history(days=90)
            predictions = predictor.predict_all()
            high_risk = [p for p in predictions if p.risk_level in ("high", "critical")]
            queue = predictor.get_review_priority_queue()
            report["modules"]["predictive_freshness"] = {
                "available": True,
                "total_predictions": len(predictions),
                "high_risk_count": len(high_risk),
                "high_risk_documents": [
                    {
                        "path": str(p.document_path),
                        "risk_level": p.risk_level,
                        "staleness_probability": round(p.staleness_probability, 2),
                        "days_until_stale": p.days_until_stale,
                    }
                    for p in high_risk[:10]
                ],
                "review_queue": queue[:10] if queue else [],
            }
            report["summary"]["available_modules"].append("predictive_freshness")
            if high_risk:
                report["recommendations"].append(
                    f"Prioritize review of {len(high_risk)} documents predicted to become stale"
                )
        except ImportError:
            report["modules"]["predictive_freshness"] = {
                "available": False,
                "reason": "predictive freshness module not installed",
            }
            report["summary"]["unavailable_modules"].append("predictive_freshness")
        except Exception as e:
            report["modules"]["predictive_freshness"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("predictive_freshness")

        # Advanced Analysis
        try:
            from ...advanced import AdvancedAnalyzer

            analyzer = AdvancedAnalyzer(project)
            adv_report = analyzer.analyze_project().to_dict()
            report["modules"]["advanced_analysis"] = {
                "available": True,
                "audience_drift": adv_report.get("audience_drift", {}),
                "question_coverage": adv_report.get("question_coverage", {}),
                "cross_references": adv_report.get("cross_references", {}),
                "structure": adv_report.get("structure", {}),
                "style": adv_report.get("style", {}),
            }
            report["summary"]["available_modules"].append("advanced_analysis")
        except ImportError:
            report["modules"]["advanced_analysis"] = {
                "available": False,
                "reason": "advanced module not installed",
            }
            report["summary"]["unavailable_modules"].append("advanced_analysis")
        except Exception as e:
            report["modules"]["advanced_analysis"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("advanced_analysis")

        # Consistency Check
        try:
            from ...insights import ConsistencyChecker

            checker = ConsistencyChecker(project)
            issues = checker.check_project()
            report["modules"]["consistency"] = {
                "available": True,
                "issue_count": len(issues),
                "issues": [i.to_dict() for i in issues[:10]],
            }
            report["summary"]["available_modules"].append("consistency")
        except Exception as e:
            report["modules"]["consistency"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("consistency")

        # Translation Parity
        try:
            from ...insights import ParityChecker

            checker = ParityChecker(project)
            parity = checker.check_project()
            report["modules"]["translation_parity"] = {
                "available": True,
                "languages": parity.languages,
                "coverage": parity.coverage,
                "missing_translations": parity.missing[:10] if hasattr(parity, "missing") else [],
            }
            report["summary"]["available_modules"].append("translation_parity")
        except Exception as e:
            report["modules"]["translation_parity"] = {"available": False, "error": str(e)}
            report["summary"]["unavailable_modules"].append("translation_parity")

        return json.dumps(report, indent=2, default=str)

    @mcp.tool()
    async def quality_report_document(document_path: str) -> str:
        """
        Generate a detailed quality report for a SPECIFIC document.

        Use this when you need to deeply analyze a single document.
        Returns all available programmatic analysis for that document.

        Args:
            document_path: Path to the document (relative to content dir or absolute)
        """
        project = _get_project()
        if not project:
            return json.dumps({"error": "No project loaded"}, indent=2)

        # Resolve path
        doc_path = Path(document_path)
        if not doc_path.is_absolute():
            doc_path = project.content_dir / doc_path

        if not doc_path.exists():
            return json.dumps({"error": f"Document not found: {document_path}"}, indent=2)

        report = {
            "document": str(doc_path),
            "relative_path": str(doc_path.relative_to(project.root))
            if doc_path.is_relative_to(project.root)
            else str(doc_path),
            "generated_at": datetime.now().isoformat(),
            "analysis": {},
        }

        # Read document content
        try:
            content = doc_path.read_text(encoding="utf-8")
            report["document_info"] = {
                "size_bytes": len(content.encode("utf-8")),
                "line_count": content.count("\n") + 1,
                "word_count": len(content.split()),
            }
        except Exception as e:
            report["document_info"] = {"error": str(e)}

        # Readability (general)
        try:
            from ...readability import analyze_readability

            readability = analyze_readability(content)
            report["analysis"]["readability"] = readability
        except Exception as e:
            report["analysis"]["readability"] = {"error": str(e)}

        # Norwegian LIX
        try:
            from ...readability.norwegian import NorwegianReadabilityChecker

            checker = NorwegianReadabilityChecker(project)
            lix_report = checker.analyze_document(doc_path)
            report["analysis"]["norwegian_lix"] = {
                "lix_score": lix_report.lix_score,
                "difficulty_level": lix_report.difficulty_level,
                "word_count": lix_report.word_count,
                "sentence_count": lix_report.sentence_count,
                "long_word_count": lix_report.long_word_count,
            }
        except Exception as e:
            report["analysis"]["norwegian_lix"] = {"available": False, "error": str(e)}

        # Code examples
        try:
            from ...codesync import EnhancedCodeSyncChecker

            checker = EnhancedCodeSyncChecker(project)
            codesync = checker.check_document(doc_path)
            report["analysis"]["code_examples"] = codesync
        except Exception as e:
            report["analysis"]["code_examples"] = {"available": False, "error": str(e)}

        # Links
        try:
            from ...links import check_document_links

            links = check_document_links(doc_path)
            report["analysis"]["links"] = links
        except Exception as e:
            report["analysis"]["links"] = {"error": str(e)}

        # Security scan
        try:
            from ...security import scan_document

            security = scan_document(doc_path)
            report["analysis"]["security"] = security
        except Exception as e:
            report["analysis"]["security"] = {"error": str(e)}

        return json.dumps(report, indent=2, default=str)

    @mcp.tool()
    async def quality_report_summary() -> str:
        """
        Generate a brief executive summary of project quality.

        This is a lighter-weight version for quick status checks.
        Returns key metrics and top issues only.
        """
        project = _get_project()
        if not project:
            return json.dumps({"error": "No project loaded"}, indent=2)

        summary = {
            "generated_at": datetime.now().isoformat(),
            "status": "unknown",
            "health_score": None,
            "grade": None,
            "key_metrics": {},
            "top_issues": [],
            "top_recommendations": [],
        }

        # Core health
        try:
            from ...insights import HealthScorer

            scorer = HealthScorer(project)
            health = scorer.score_project()
            summary["health_score"] = health.overall
            summary["grade"] = health.grade
            summary["status"] = health.status
            summary["key_metrics"]["health_components"] = health.components
            summary["top_issues"] = [
                i.to_dict() for i in health.issues[:5] if i.severity in ("critical", "warning")
            ]
            summary["top_recommendations"] = health.recommendations[:3]
        except Exception as e:
            summary["health_error"] = str(e)

        # Quick counts
        try:
            from ...insights import StatisticsCollector

            collector = StatisticsCollector(project)
            stats = collector.collect()
            summary["key_metrics"]["documents"] = stats.content.get("total_documents", 0)
            summary["key_metrics"]["languages"] = len(stats.content.get("by_language", {}))
        except Exception:
            pass

        # Freshness
        try:
            from ...freshness import FreshnessScanner

            scanner = FreshnessScanner(project)
            stale = scanner.find_stale(days=30)
            summary["key_metrics"]["stale_documents"] = len(stale)
        except Exception:
            pass

        return json.dumps(summary, indent=2, default=str)

    @mcp.tool()
    async def quality_report_issues(
        severity: str = "all",
        category: str = "all",
        limit: int = 50,
    ) -> str:
        """
        Get a filtered list of quality issues.

        Useful for focusing on specific problem areas.

        Args:
            severity: Filter by severity - "critical", "warning", "info", or "all"
            category: Filter by category - "freshness", "consistency", "links", etc., or "all"
            limit: Maximum number of issues to return
        """
        project = _get_project()
        if not project:
            return json.dumps({"error": "No project loaded"}, indent=2)

        all_issues = []

        # Collect issues from various sources
        try:
            from ...insights import HealthScorer

            scorer = HealthScorer(project)
            health = scorer.score_project()
            for issue in health.issues:
                issue_dict = issue.to_dict()
                issue_dict["source"] = "health"
                all_issues.append(issue_dict)
        except Exception:
            pass

        try:
            from ...quality import run_quality_checks

            report = run_quality_checks(project, console_output=False)
            for issue in report.issues:
                all_issues.append(
                    {
                        "severity": issue.severity,
                        "category": issue.type,
                        "message": issue.message,
                        "document": str(issue.file_path) if issue.file_path else None,
                        "line": issue.line,
                        "source": "quality_checks",
                    }
                )
        except Exception:
            pass

        # Filter
        if severity != "all":
            all_issues = [i for i in all_issues if i.get("severity") == severity]
        if category != "all":
            all_issues = [i for i in all_issues if i.get("category") == category]

        # Sort by severity
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 99))

        return json.dumps(
            {
                "total_found": len(all_issues),
                "returned": min(len(all_issues), limit),
                "filters": {"severity": severity, "category": category},
                "issues": all_issues[:limit],
            },
            indent=2,
        )

    @mcp.tool()
    async def quality_report_module(module_name: str) -> str:
        """
        Get detailed report from a specific analysis module.

        Available modules:
        - semantic: Near-duplicates, terminology drift, content clusters
        - knowledge_graph: Concepts, prerequisites, reading paths
        - codesync: Code example validation, deprecated patterns
        - norwegian_readability: LIX readability scores
        - predictive_freshness: Staleness predictions
        - advanced: Audience drift, question coverage, style
        - consistency: Status consistency checks
        - parity: Translation coverage

        Args:
            module_name: Name of the analysis module
        """
        project = _get_project()
        if not project:
            return json.dumps({"error": "No project loaded"}, indent=2)

        report = {
            "module": module_name,
            "generated_at": datetime.now().isoformat(),
            "data": None,
        }

        if module_name == "semantic":
            try:
                from ...semantic import SemanticAnalyzer

                analyzer = SemanticAnalyzer(project)
                report["data"] = {
                    "near_duplicates": [
                        d.to_dict() for d in analyzer.find_near_duplicates(threshold=0.85)
                    ],
                    "terminology_drift": [d.to_dict() for d in analyzer.detect_terminology_drift()],
                    "content_clusters": [
                        c.to_dict() for c in analyzer.cluster_content(n_clusters=5)
                    ],
                }
            except ImportError:
                report["error"] = "semantic module not installed"
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "knowledge_graph":
            try:
                from ...knowledge import KnowledgeGraph

                kg = KnowledgeGraph(project)
                kg.build()
                report["data"] = {
                    "metrics": kg.get_metrics(),
                    "orphan_concepts": kg.find_orphan_concepts(),
                    "prerequisite_issues": [
                        p.to_dict() if hasattr(p, "to_dict") else str(p)
                        for p in kg.validate_prerequisites()
                    ],
                    "node_count": kg.graph.number_of_nodes() if hasattr(kg, "graph") else 0,
                    "edge_count": kg.graph.number_of_edges() if hasattr(kg, "graph") else 0,
                }
            except ImportError:
                report["error"] = "knowledge module not installed"
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "codesync":
            try:
                from ...codesync import EnhancedCodeSyncChecker

                checker = EnhancedCodeSyncChecker(project)
                report["data"] = checker.generate_summary()
            except ImportError:
                report["error"] = "codesync module not installed"
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "norwegian_readability":
            try:
                from ...readability.norwegian import NorwegianReadabilityChecker

                checker = NorwegianReadabilityChecker(project)
                reports = checker.analyze_all_documents()
                report["data"] = {
                    "documents": [
                        {
                            "path": str(r.document_path),
                            "lix_score": r.lix_score,
                            "difficulty_level": r.difficulty_level,
                            "word_count": r.word_count,
                        }
                        for r in reports
                    ],
                    "summary": {
                        "total": len(reports),
                        "average_lix": round(sum(r.lix_score for r in reports) / len(reports), 1)
                        if reports
                        else 0,
                    },
                }
            except ImportError:
                report["error"] = "norwegian readability module not installed"
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "predictive_freshness":
            try:
                from ...freshness.predictive import FreshnessPredictor

                predictor = FreshnessPredictor(project)
                predictor.train_from_history(days=90)
                predictions = predictor.predict_all()
                report["data"] = {
                    "predictions": [
                        {
                            "path": str(p.document_path),
                            "risk_level": p.risk_level,
                            "staleness_probability": round(p.staleness_probability, 2),
                            "days_until_stale": p.days_until_stale,
                        }
                        for p in predictions
                    ],
                    "review_queue": predictor.get_review_priority_queue(),
                }
            except ImportError:
                report["error"] = "predictive freshness module not installed"
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "advanced":
            try:
                from ...advanced import AdvancedAnalyzer

                analyzer = AdvancedAnalyzer(project)
                report["data"] = analyzer.analyze_project().to_dict()
            except ImportError:
                report["error"] = "advanced module not installed"
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "consistency":
            try:
                from ...insights import ConsistencyChecker

                checker = ConsistencyChecker(project)
                issues = checker.check_project()
                report["data"] = {
                    "issues": [i.to_dict() for i in issues],
                    "total": len(issues),
                }
            except Exception as e:
                report["error"] = str(e)

        elif module_name == "parity":
            try:
                from ...insights import ParityChecker

                checker = ParityChecker(project)
                parity = checker.check_project()
                report["data"] = (
                    parity.to_dict()
                    if hasattr(parity, "to_dict")
                    else {
                        "languages": parity.languages,
                        "coverage": parity.coverage,
                    }
                )
            except Exception as e:
                report["error"] = str(e)

        else:
            report["error"] = (
                f"Unknown module: {module_name}. Available: semantic, knowledge_graph, codesync, norwegian_readability, predictive_freshness, advanced, consistency, parity"
            )

        return json.dumps(report, indent=2, default=str)

    @mcp.tool()
    async def quality_available_modules() -> str:
        """
        List all available quality analysis modules.

        Shows which advanced analysis modules are installed and working.
        Use this to understand what analysis capabilities are available.
        """
        project = _get_project()
        if not project:
            return json.dumps({"error": "No project loaded"}, indent=2)

        modules = {}

        # Check each module
        module_checks = [
            ("semantic", "media_engine.semantic", "SemanticAnalyzer"),
            ("knowledge_graph", "media_engine.knowledge", "KnowledgeGraph"),
            ("codesync", "media_engine.codesync", "EnhancedCodeSyncChecker"),
            (
                "norwegian_readability",
                "media_engine.readability.norwegian",
                "NorwegianReadabilityChecker",
            ),
            ("predictive_freshness", "media_engine.freshness.predictive", "FreshnessPredictor"),
            ("advanced", "media_engine.advanced", "AdvancedAnalyzer"),
            ("consistency", "media_engine.insights", "ConsistencyChecker"),
            ("parity", "media_engine.insights", "ParityChecker"),
            ("health", "media_engine.insights", "HealthScorer"),
        ]

        for name, module_path, class_name in module_checks:
            try:
                import importlib

                module = importlib.import_module(module_path)
                cls = getattr(module, class_name, None)
                modules[name] = {
                    "available": cls is not None,
                    "module": module_path,
                    "class": class_name,
                }
            except ImportError:
                modules[name] = {
                    "available": False,
                    "reason": "module not installed",
                }
            except Exception as e:
                modules[name] = {
                    "available": False,
                    "error": str(e),
                }

        return json.dumps(
            {
                "modules": modules,
                "available_count": sum(1 for m in modules.values() if m.get("available")),
                "total_count": len(modules),
            },
            indent=2,
        )
