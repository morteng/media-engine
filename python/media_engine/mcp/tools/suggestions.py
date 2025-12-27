"""Proactive guidance tools for AI agents.

Provides intelligent suggestions, action validation, and workflow guidance
to help AI agents work effectively with media-engine projects.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer


def register_suggestion_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register suggestion and guidance MCP tools."""

    @mcp.tool()
    async def get_suggested_actions() -> str:
        """
        Get prioritized list of recommended actions.

        Analyzes project state and returns actionable suggestions:
        - Critical issues requiring immediate attention
        - Medium priority improvements
        - Low priority enhancements

        Each suggestion includes:
        - Priority level (high, medium, low)
        - Action type and target
        - Clear description of what to do
        - Estimated impact

        This is ideal for agents looking for productive next steps.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        suggestions = _gather_suggestions(project)

        return json.dumps(
            {
                "total_suggestions": len(suggestions),
                "by_priority": {
                    "high": [s for s in suggestions if s["priority"] == "high"],
                    "medium": [s for s in suggestions if s["priority"] == "medium"],
                    "low": [s for s in suggestions if s["priority"] == "low"],
                },
                "top_5": suggestions[:5],
            },
            indent=2,
        )

    @mcp.tool()
    async def validate_action(action: str, target: str, params: str = "{}") -> str:
        """
        Validate a proposed action before execution.

        Checks if an action is safe and appropriate:
        - Verifies target exists
        - Checks permissions/constraints
        - Estimates impact
        - Suggests alternatives if problematic

        Args:
            action: Action type (update_document, delete_document, translate, etc.)
            target: Target path or identifier
            params: JSON string of additional parameters

        Returns:
            Validation result with approval/warnings/errors.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project

        try:
            params_dict = json.loads(params) if params else {}
        except json.JSONDecodeError:
            params_dict = {}

        result = _validate_action(project, action, target, params_dict)

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def get_workflow_guidance(workflow: str) -> str:
        """
        Get step-by-step guidance for common workflows.

        Available workflows:
        - "new_document": Create a new document
        - "update_document": Update existing content
        - "translate": Translate content to another language
        - "review": Review and approve content
        - "quality_fix": Fix quality issues
        - "bulk_update": Update multiple documents

        Args:
            workflow: Name of the workflow to get guidance for

        Returns:
            Step-by-step instructions and best practices.
        """
        guidance = _get_workflow_guidance(workflow)
        return json.dumps(guidance, indent=2)

    @mcp.tool()
    async def get_best_practices(topic: str = "general") -> str:
        """
        Get best practices for working with media-engine projects.

        Topics:
        - "general": Overall best practices
        - "translations": Translation workflow tips
        - "quality": Maintaining content quality
        - "structure": Document organization
        - "metadata": Frontmatter and versioning

        Args:
            topic: Best practices topic

        Returns:
            Relevant best practices and tips.
        """
        practices = _get_best_practices(topic)
        return json.dumps(practices, indent=2)


def _gather_suggestions(project) -> list:
    """Gather all suggestions from various analyzers."""
    suggestions = []

    # Check for incomplete content
    try:
        from ...insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()
        high_priority = [i for i in items if i.priority in ["high", "critical"]]

        if high_priority:
            suggestions.append(
                {
                    "priority": "high",
                    "action": "complete_content",
                    "target": str(high_priority[0].document),
                    "description": f"Complete {len(high_priority)} high-priority incomplete items",
                    "details": {
                        "count": len(high_priority),
                        "first_item": {
                            "path": str(high_priority[0].document),
                            "type": high_priority[0].marker_type,
                            "line": high_priority[0].line_number,
                        },
                    },
                }
            )

        if len(items) > len(high_priority):
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "complete_content",
                    "target": None,
                    "description": f"Address {len(items) - len(high_priority)} remaining incomplete items",
                    "details": {"count": len(items) - len(high_priority)},
                }
            )
    except Exception:
        pass

    # Check for outdated translations
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()

        if outdated:
            suggestions.append(
                {
                    "priority": "high",
                    "action": "update_translations",
                    "target": str(outdated[0].get("path", "")),
                    "description": f"Update {len(outdated)} outdated translations",
                    "details": {
                        "count": len(outdated),
                        "languages": list(set(t.get("language", "") for t in outdated)),
                    },
                }
            )
    except Exception:
        pass

    # Check for missing translations
    try:
        from ...translation.tracker import TranslationTracker

        tracker = TranslationTracker(project)
        missing = tracker.get_missing_translations()

        if missing:
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "create_translations",
                    "target": None,
                    "description": f"Create {len(missing)} missing translations",
                    "details": {
                        "count": len(missing),
                        "by_language": _group_by_language(missing),
                    },
                }
            )
    except Exception:
        pass

    # Check for consistency issues
    try:
        from ...insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        issues = checker.check_project()

        if issues:
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "fix_status_consistency",
                    "target": str(issues[0].document),
                    "description": f"Fix {len(issues)} status consistency issues",
                    "details": {
                        "count": len(issues),
                        "first_issue": {
                            "path": str(issues[0].document),
                            "current_status": issues[0].current_status,
                            "suggested": issues[0].suggested_status,
                        },
                    },
                }
            )
    except Exception:
        pass

    # Check for terminology issues
    try:
        from ...insights import TerminologyChecker

        checker = TerminologyChecker(project)
        issues = checker.find_inconsistencies()

        if issues:
            suggestions.append(
                {
                    "priority": "low",
                    "action": "fix_terminology",
                    "target": None,
                    "description": f"Fix {len(issues)} terminology inconsistencies",
                    "details": {"count": len(issues)},
                }
            )
    except Exception:
        pass

    # Check for stagnant areas
    try:
        from ...insights import VelocityTracker

        tracker = VelocityTracker(project)
        stagnant = tracker.get_stagnant_areas(days=90)

        if stagnant:
            suggestions.append(
                {
                    "priority": "low",
                    "action": "review_stagnant",
                    "target": stagnant[0] if stagnant else None,
                    "description": f"Review {len(stagnant)} areas with no recent activity",
                    "details": {"areas": stagnant[:5]},
                }
            )
    except Exception:
        pass

    # ============== ADVANCED ANALYSIS MODULES ==============

    # Check for near-duplicate content (semantic)
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        duplicates = analyzer.find_near_duplicates(threshold=0.85)

        if duplicates:
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "consolidate_duplicates",
                    "target": str(duplicates[0].doc1_path)
                    if hasattr(duplicates[0], "doc1_path")
                    else None,
                    "description": f"Review {len(duplicates)} near-duplicate content pairs for consolidation",
                    "details": {
                        "count": len(duplicates),
                        "first_pair": {
                            "doc1": str(duplicates[0].doc1_path)
                            if hasattr(duplicates[0], "doc1_path")
                            else None,
                            "doc2": str(duplicates[0].doc2_path)
                            if hasattr(duplicates[0], "doc2_path")
                            else None,
                            "similarity": round(duplicates[0].similarity * 100)
                            if hasattr(duplicates[0], "similarity")
                            else None,
                        },
                    },
                    "module": "semantic",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for terminology drift (semantic)
    try:
        from ...semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        drift = analyzer.detect_terminology_drift()

        if drift:
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "fix_terminology_drift",
                    "target": None,
                    "description": f"Address {len(drift)} terminology inconsistencies across documents",
                    "details": {
                        "count": len(drift),
                        "first_term": {
                            "term": drift[0].term if hasattr(drift[0], "term") else None,
                            "drift_score": round(drift[0].drift_score * 100)
                            if hasattr(drift[0], "drift_score")
                            else None,
                        }
                        if drift
                        else None,
                    },
                    "module": "semantic",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for orphan concepts (knowledge graph)
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()
        orphans = kg.find_orphan_concepts()

        if orphans:
            suggestions.append(
                {
                    "priority": "low",
                    "action": "connect_orphan_concepts",
                    "target": None,
                    "description": f"Connect {len(orphans)} orphan concepts to the knowledge graph",
                    "details": {
                        "count": len(orphans),
                        "concepts": orphans[:5],
                    },
                    "module": "knowledge_graph",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for prerequisite issues (knowledge graph)
    try:
        from ...knowledge import KnowledgeGraph

        kg = KnowledgeGraph(project)
        kg.build()
        prereq_issues = kg.validate_prerequisites()

        if prereq_issues:
            suggestions.append(
                {
                    "priority": "high",
                    "action": "fix_prerequisites",
                    "target": str(prereq_issues[0].document)
                    if hasattr(prereq_issues[0], "document")
                    else None,
                    "description": f"Fix {len(prereq_issues)} prerequisite chain issues",
                    "details": {
                        "count": len(prereq_issues),
                    },
                    "module": "knowledge_graph",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for code syntax errors (codesync)
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        report = checker.generate_summary()
        syntax_errors = report.get("syntax_errors", [])

        if syntax_errors:
            suggestions.append(
                {
                    "priority": "high",
                    "action": "fix_code_syntax",
                    "target": syntax_errors[0].get("document") if syntax_errors else None,
                    "description": f"Fix {len(syntax_errors)} syntax errors in code examples",
                    "details": {
                        "count": len(syntax_errors),
                        "first_error": syntax_errors[0] if syntax_errors else None,
                    },
                    "module": "codesync",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for deprecated patterns (codesync)
    try:
        from ...codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        report = checker.generate_summary()
        deprecated = report.get("deprecated_patterns", [])

        if deprecated:
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "update_deprecated_code",
                    "target": deprecated[0].get("document") if deprecated else None,
                    "description": f"Update {len(deprecated)} deprecated code patterns in documentation",
                    "details": {
                        "count": len(deprecated),
                    },
                    "module": "codesync",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for high-risk staleness (predictive freshness)
    try:
        from ...freshness.predictive import FreshnessPredictor

        predictor = FreshnessPredictor(project)
        predictor.train_from_history(days=90)
        predictions = predictor.predict_all()
        high_risk = [p for p in predictions if p.risk_level in ("high", "critical")]

        if high_risk:
            suggestions.append(
                {
                    "priority": "high",
                    "action": "review_at_risk_content",
                    "target": str(high_risk[0].document_path)
                    if hasattr(high_risk[0], "document_path")
                    else None,
                    "description": f"Review {len(high_risk)} documents predicted to become stale soon",
                    "details": {
                        "count": len(high_risk),
                        "first_doc": {
                            "path": str(high_risk[0].document_path)
                            if hasattr(high_risk[0], "document_path")
                            else None,
                            "risk_level": high_risk[0].risk_level
                            if hasattr(high_risk[0], "risk_level")
                            else None,
                            "probability": round(high_risk[0].staleness_probability * 100)
                            if hasattr(high_risk[0], "staleness_probability")
                            else None,
                        }
                        if high_risk
                        else None,
                    },
                    "module": "predictive_freshness",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for difficult documents (Norwegian LIX)
    try:
        from ...readability.norwegian import NorwegianReadabilityChecker

        checker = NorwegianReadabilityChecker(project)
        reports = checker.analyze_all_documents()
        difficult = [r for r in reports if r.difficulty_level in ("difficult", "very_difficult")]

        if difficult:
            suggestions.append(
                {
                    "priority": "low",
                    "action": "simplify_difficult_content",
                    "target": str(difficult[0].document_path)
                    if hasattr(difficult[0], "document_path")
                    else None,
                    "description": f"Simplify {len(difficult)} documents with high readability difficulty (LIX)",
                    "details": {
                        "count": len(difficult),
                        "first_doc": {
                            "path": str(difficult[0].document_path)
                            if hasattr(difficult[0], "document_path")
                            else None,
                            "lix_score": difficult[0].lix_score
                            if hasattr(difficult[0], "lix_score")
                            else None,
                            "level": difficult[0].difficulty_level
                            if hasattr(difficult[0], "difficulty_level")
                            else None,
                        }
                        if difficult
                        else None,
                    },
                    "module": "norwegian_readability",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for audience drift (advanced)
    try:
        from ...advanced import AdvancedAnalyzer

        analyzer = AdvancedAnalyzer(project)
        report = analyzer.analyze_project().to_dict()
        drift = report.get("audience_drift", {})

        if drift.get("trend") in ("increasing", "decreasing"):
            suggestions.append(
                {
                    "priority": "medium",
                    "action": "address_audience_drift",
                    "target": None,
                    "description": f"Address audience drift: complexity is {drift.get('trend')} over time",
                    "details": {
                        "trend": drift.get("trend"),
                        "drift_score": drift.get("drift_score"),
                        "documents_affected": len(drift.get("documents_with_drift", [])),
                    },
                    "module": "advanced",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Check for style inconsistencies (advanced)
    try:
        from ...advanced import AdvancedAnalyzer

        analyzer = AdvancedAnalyzer(project)
        report = analyzer.analyze_project().to_dict()
        style = report.get("style", {})

        if style.get("style_score", 100) < 70:
            suggestions.append(
                {
                    "priority": "low",
                    "action": "improve_style_consistency",
                    "target": None,
                    "description": f"Improve style consistency (score: {style.get('style_score', 0)}/100)",
                    "details": {
                        "score": style.get("style_score"),
                        "inconsistencies": len(style.get("inconsistencies", [])),
                    },
                    "module": "advanced",
                }
            )
    except ImportError:
        pass
    except Exception:
        pass

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s["priority"], 3))

    return suggestions


def _group_by_language(missing: list) -> dict:
    """Group missing translations by language."""
    by_lang = {}
    for item in missing:
        lang = item.get("language", "unknown")
        if lang not in by_lang:
            by_lang[lang] = 0
        by_lang[lang] += 1
    return by_lang


def _validate_action(project, action: str, target: str, params: dict) -> dict:
    """Validate a proposed action."""
    result = {
        "action": action,
        "target": target,
        "valid": True,
        "warnings": [],
        "errors": [],
        "suggestions": [],
        "estimated_impact": {},
    }

    # Validate target exists for update/delete actions
    if action in ["update_document", "delete_document", "translate"]:
        target_path = project.content_dir / target
        if not target_path.exists():
            # Try without leading slash
            target_path = project.content_dir / target.lstrip("/")

        if not target_path.exists():
            result["valid"] = False
            result["errors"].append(f"Target document not found: {target}")
            result["suggestions"].append("Check the document path and try again")
            return result

    # Action-specific validation
    if action == "delete_document":
        result["warnings"].append("Document deletion is permanent")

        # Check for dependents using UnifiedRegistry
        try:
            from ...relationships import get_registry_manager, init_registry_manager

            registry_manager = get_registry_manager(project)
            if registry_manager is None:
                registry_manager = init_registry_manager(project)

            dependents = registry_manager.registry.get_impact(Path(target))

            if dependents:
                result["warnings"].append(f"{len(dependents)} documents depend on this document")
                result["estimated_impact"]["broken_dependencies"] = len(dependents)
        except Exception:
            pass

        # Check for translations
        try:
            from ...translation.tracker import TranslationTracker

            tracker = TranslationTracker(project)
            translations = tracker.get_translations_for_source(Path(target))

            if translations:
                result["warnings"].append(f"{len(translations)} translations will be orphaned")
                result["estimated_impact"]["orphaned_translations"] = len(translations)
        except Exception:
            pass

    elif action == "update_document":
        # Check translation impact
        try:
            from ...translation.tracker import TranslationTracker

            tracker = TranslationTracker(project)
            translations = tracker.get_translations_for_source(Path(target))

            if translations:
                result["warnings"].append(f"{len(translations)} translations may need updating")
                result["estimated_impact"]["translations_to_update"] = len(translations)
        except Exception:
            pass

    elif action == "translate":
        target_lang = params.get("language")
        if not target_lang:
            result["valid"] = False
            result["errors"].append("Target language is required")
            return result

        if target_lang not in project.languages:
            result["warnings"].append(f"Language '{target_lang}' is not configured in project")
            result["suggestions"].append(f"Add '{target_lang}' to project.yaml languages section")

    elif action == "bulk_update":
        selector = params.get("selector", "")
        if not selector:
            result["valid"] = False
            result["errors"].append("Selector is required for bulk updates")
            return result

        # Estimate affected documents
        from ...cms.document_manager import DocumentManager

        manager = DocumentManager(project)
        docs = manager.list_documents()

        affected = _count_matching_docs(docs, selector)
        result["estimated_impact"]["documents_affected"] = affected

        if affected > 10:
            result["warnings"].append(f"This will affect {affected} documents")

    return result


def _count_matching_docs(docs: list, selector: str) -> int:
    """Count documents matching a selector."""
    # Simple selector parsing: "key:value"
    count = 0
    if ":" in selector:
        key, value = selector.split(":", 1)
        for doc in docs:
            if str(doc.get(key, "")).lower() == value.lower():
                count += 1
    return count


def _get_workflow_guidance(workflow: str) -> dict:
    """Get guidance for a specific workflow."""
    workflows = {
        "new_document": {
            "name": "Create New Document",
            "description": "Create a new document with proper metadata and structure",
            "steps": [
                {
                    "step": 1,
                    "action": "Determine document type and location",
                    "details": "Choose the appropriate directory (chapters/, guides/, etc.)",
                },
                {
                    "step": 2,
                    "action": "Create file with frontmatter",
                    "details": "Include required fields: title, status (draft), version (1.0.0)",
                },
                {
                    "step": 3,
                    "action": "Write initial content",
                    "details": "Add main content sections, avoiding TODOs if possible",
                },
                {
                    "step": 4,
                    "action": "Run quality checks",
                    "details": "Use quality_check tool to verify content quality",
                },
            ],
            "best_practices": [
                "Start with status: draft",
                "Include a clear title and description",
                "Add appropriate tags for discoverability",
            ],
        },
        "update_document": {
            "name": "Update Existing Document",
            "description": "Modify document content while maintaining version history",
            "steps": [
                {
                    "step": 1,
                    "action": "Read current document",
                    "details": "Use read_document to get current content and metadata",
                },
                {
                    "step": 2,
                    "action": "Make content changes",
                    "details": "Update the relevant sections",
                },
                {
                    "step": 3,
                    "action": "Increment version",
                    "details": "Use increment_document_version for semantic versioning",
                },
                {
                    "step": 4,
                    "action": "Check translation impact",
                    "details": "Use analyze_change_impact to see affected translations",
                },
            ],
            "best_practices": [
                "Always increment version for significant changes",
                "Note changes in document if it has a changelog section",
                "Consider impact on translations before major changes",
            ],
        },
        "translate": {
            "name": "Translate Document",
            "description": "Create or update a translation of a source document",
            "steps": [
                {
                    "step": 1,
                    "action": "Identify source document",
                    "details": "Find the source document and its current version",
                },
                {
                    "step": 2,
                    "action": "Check if translation exists",
                    "details": "Use translation_status to find existing translation",
                },
                {
                    "step": 3,
                    "action": "Create/update translation file",
                    "details": "Mirror source structure in target language directory",
                },
                {
                    "step": 4,
                    "action": "Set translation metadata",
                    "details": "Include source_document and source_version in frontmatter",
                },
                {
                    "step": 5,
                    "action": "Mark as synced",
                    "details": "Use mark_translation_synced when complete",
                },
            ],
            "best_practices": [
                "Maintain same file structure as source",
                "Keep source_version accurate for tracking",
                "Preserve formatting and code blocks exactly",
            ],
        },
        "review": {
            "name": "Review Content",
            "description": "Review and approve content for publication",
            "steps": [
                {
                    "step": 1,
                    "action": "Run quality checks",
                    "details": "Use quality_check tool on the document",
                },
                {
                    "step": 2,
                    "action": "Check for incomplete content",
                    "details": "Look for TODOs, TBDs, placeholders",
                },
                {
                    "step": 3,
                    "action": "Verify links and references",
                    "details": "Ensure all links are valid",
                },
                {
                    "step": 4,
                    "action": "Update status",
                    "details": "Change from draft/in_review to approved/final",
                },
            ],
            "best_practices": [
                "Never approve content with TODOs or placeholders",
                "Check that translations are current",
                "Verify all code examples work",
            ],
        },
        "quality_fix": {
            "name": "Fix Quality Issues",
            "description": "Address quality problems identified by checks",
            "steps": [
                {
                    "step": 1,
                    "action": "Get quality report",
                    "details": "Use quality_check to get detailed issues",
                },
                {
                    "step": 2,
                    "action": "Prioritize issues",
                    "details": "Focus on errors before warnings",
                },
                {
                    "step": 3,
                    "action": "Fix each issue",
                    "details": "Address one issue at a time",
                },
                {
                    "step": 4,
                    "action": "Re-run quality check",
                    "details": "Verify fixes resolved the issues",
                },
            ],
            "best_practices": [
                "Fix critical issues first",
                "Document any intentional deviations",
                "Run full project check after bulk fixes",
            ],
        },
        "bulk_update": {
            "name": "Bulk Update Documents",
            "description": "Update multiple documents efficiently",
            "steps": [
                {
                    "step": 1,
                    "action": "Define selector",
                    "details": "Identify which documents to update (status:draft, lang:en)",
                },
                {
                    "step": 2,
                    "action": "Validate scope",
                    "details": "Use validate_action to check impact",
                },
                {
                    "step": 3,
                    "action": "Do dry run",
                    "details": "Use apply_transformation with dry_run=true",
                },
                {
                    "step": 4,
                    "action": "Execute update",
                    "details": "Apply the transformation",
                },
            ],
            "best_practices": [
                "Always do a dry run first",
                "Start with a small subset to test",
                "Have a rollback plan for large updates",
            ],
        },
    }

    if workflow in workflows:
        return workflows[workflow]
    else:
        return {
            "error": f"Unknown workflow: {workflow}",
            "available_workflows": list(workflows.keys()),
        }


def _get_best_practices(topic: str) -> dict:
    """Get best practices for a topic."""
    practices = {
        "general": {
            "topic": "General Best Practices",
            "practices": [
                {
                    "title": "Use get_project_context first",
                    "description": "Always start by getting project context to understand the codebase",
                },
                {
                    "title": "Validate before acting",
                    "description": "Use validate_action before making changes to avoid errors",
                },
                {
                    "title": "Increment versions",
                    "description": "Always increment document versions when making significant changes",
                },
                {
                    "title": "Check translations",
                    "description": "Consider translation impact when modifying source documents",
                },
                {
                    "title": "Run quality checks",
                    "description": "Use quality_check after making changes to verify content quality",
                },
            ],
        },
        "translations": {
            "topic": "Translation Best Practices",
            "practices": [
                {
                    "title": "Track source versions",
                    "description": "Always set source_version in translation frontmatter",
                },
                {
                    "title": "Preserve structure",
                    "description": "Keep the same heading structure as the source document",
                },
                {
                    "title": "Don't translate code",
                    "description": "Keep code blocks, file paths, and technical terms as-is",
                },
                {
                    "title": "Update promptly",
                    "description": "Update translations soon after source changes",
                },
            ],
        },
        "quality": {
            "topic": "Content Quality Best Practices",
            "practices": [
                {
                    "title": "Avoid incomplete markers",
                    "description": "Don't leave TODO, TBD, or placeholder text in final content",
                },
                {
                    "title": "Match status to content",
                    "description": "Status should reflect actual content state",
                },
                {
                    "title": "Fix issues before approval",
                    "description": "Address all quality warnings before marking content as approved",
                },
                {
                    "title": "Use consistent terminology",
                    "description": "Use the same terms throughout the project",
                },
            ],
        },
        "structure": {
            "topic": "Document Structure Best Practices",
            "practices": [
                {
                    "title": "Organize by language",
                    "description": "Use language directories (en/, no/) at the top level",
                },
                {
                    "title": "Group by type",
                    "description": "Organize content into chapters/, guides/, reference/",
                },
                {
                    "title": "Use descriptive names",
                    "description": "File names should indicate content (01_introduction.md)",
                },
                {
                    "title": "Maintain parallel structure",
                    "description": "Translations should mirror source directory structure",
                },
            ],
        },
        "metadata": {
            "topic": "Metadata Best Practices",
            "practices": [
                {
                    "title": "Required frontmatter",
                    "description": "Always include title, status, and version",
                },
                {
                    "title": "Semantic versioning",
                    "description": "Use MAJOR.MINOR.PATCH version format",
                },
                {
                    "title": "Translation metadata",
                    "description": "Include source_document and source_version for translations",
                },
                {
                    "title": "Use tags",
                    "description": "Add relevant tags for discoverability",
                },
            ],
        },
    }

    if topic in practices:
        return practices[topic]
    else:
        return {
            "error": f"Unknown topic: {topic}",
            "available_topics": list(practices.keys()),
        }
