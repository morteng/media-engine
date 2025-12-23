"""
MCP tools for document hierarchy and information flow.

Provides tools for:
- Hierarchy status and tree visualization
- Staleness detection and propagation
- Consistency anchors management
- Impact analysis for changes
- Coverage analysis for documentation gaps
"""

import json
from typing import Any


def register_hierarchy_tools(mcp, server_instance) -> None:
    """Register hierarchy management tools."""

    @mcp.tool(
        description="""
        Get document hierarchy status.

        Returns summary of hierarchy including:
        - Total documents and root count
        - Document type distribution
        - Lifecycle distribution
        - Stale document count
        """
    )
    def hierarchy_status() -> str:
        """Get hierarchy status overview."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import HierarchyGraph

        graph = HierarchyGraph(project)
        report = graph.registry.generate_report()

        return json.dumps(report, indent=2)

    @mcp.tool(
        description="""
        Get hierarchy tree as ASCII representation.

        Args:
            root_path: Optional path to start from (shows all roots if omitted)
        """
    )
    def hierarchy_tree(root_path: str = None) -> str:
        """Get hierarchy as ASCII tree."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from pathlib import Path

        from ...hierarchy import HierarchyGraph

        graph = HierarchyGraph(project)

        root = Path(root_path) if root_path else None
        tree_str = graph.to_tree_string(root)

        if not tree_str.strip():
            return "No hierarchy data found. Run hierarchy_refresh first."

        return tree_str

    @mcp.tool(
        description="""
        Refresh hierarchy from document frontmatter.

        Scans all documents to rebuild the hierarchy based on:
        - parent_document fields
        - derived_from relationships
        - doc_type and lifecycle metadata
        - consistency anchors
        """
    )
    def hierarchy_refresh() -> str:
        """Refresh hierarchy from documents."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import HierarchyGraph

        graph = HierarchyGraph(project)
        graph.refresh()
        report = graph.registry.generate_report()

        return json.dumps(
            {
                "status": "refreshed",
                "total_nodes": report["summary"]["total_nodes"],
                "root_count": report["summary"]["root_count"],
                "anchor_count": report["summary"]["anchor_count"],
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Validate hierarchy structure.

        Checks for:
        - Circular parent references
        - Orphan documents with missing parents
        - Duplicate sequence orders
        - Level mismatches
        - Invalid derivation sources
        """
    )
    def hierarchy_validate() -> str:
        """Validate hierarchy structure."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import HierarchyGraph, HierarchyValidator

        graph = HierarchyGraph(project)
        validator = HierarchyValidator(graph)
        result = validator.validate_all()

        return json.dumps(result.to_dict(), indent=2)

    @mcp.tool(
        description="""
        Get navigation context for a document.

        Returns:
        - Breadcrumbs from root to document
        - Parent, children, and siblings
        - Previous/next sibling navigation
        - Position in sibling list

        Args:
            document_path: Path to the document
        """
    )
    def hierarchy_navigation(document_path: str) -> str:
        """Get navigation context for a document."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from pathlib import Path

        from ...hierarchy import HierarchyGraph

        graph = HierarchyGraph(project)
        context = graph.get_navigation_context(Path(document_path))

        if not context:
            return json.dumps({"error": f"Document not found in hierarchy: {document_path}"})

        return json.dumps(context.to_dict(), indent=2)

    @mcp.tool(
        description="""
        Get stale documents report.

        Returns documents that need updating because:
        - Source documents were modified
        - Version mismatches exist
        - Staleness propagated through derivation chain
        - Freshness period expired
        - Anchors changed
        """
    )
    def hierarchy_stale() -> str:
        """Get stale documents report."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import HierarchyGraph, StalenessChecker

        graph = HierarchyGraph(project)
        checker = StalenessChecker(graph)
        report = checker.check_all()

        return json.dumps(report.to_dict(), indent=2)

    @mcp.tool(
        description="""
        Mark a document as stale.

        This triggers staleness propagation to dependent documents.

        Args:
            document_path: Path to the document
            reason: Reason for staleness (source_updated, version_mismatch, expired, anchor_changed)
        """
    )
    def hierarchy_mark_stale(
        document_path: str,
        reason: str = "source_updated",
    ) -> str:
        """Mark a document as stale."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from pathlib import Path

        from ...hierarchy import HierarchyGraph, StalenessChecker, StalenessReason

        graph = HierarchyGraph(project)
        checker = StalenessChecker(graph)

        reason_map = {
            "source_updated": StalenessReason.SOURCE_UPDATED,
            "version_mismatch": StalenessReason.VERSION_MISMATCH,
            "transitive": StalenessReason.TRANSITIVE,
            "expired": StalenessReason.EXPIRED,
            "anchor_changed": StalenessReason.ANCHOR_CHANGED,
        }

        staleness_reason = reason_map.get(reason, StalenessReason.SOURCE_UPDATED)
        result = checker.mark_stale(Path(document_path), staleness_reason)

        return json.dumps(
            {
                "marked_stale": result,
                "document": document_path,
                "reason": reason,
            }
        )

    @mcp.tool(
        description="""
        Get consistency anchors.

        Returns all anchors defined across documents with:
        - Anchor names and values
        - Which documents define them
        - Which documents reference them

        Args:
            validate: If true, also validate anchor references
        """
    )
    def hierarchy_anchors(validate: bool = False) -> str:
        """Get consistency anchors."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import AnchorRegistry, HierarchyGraph

        graph = HierarchyGraph(project)
        anchor_registry = AnchorRegistry(graph.registry)
        anchor_registry.build()

        summary = anchor_registry.get_impact_summary()

        result: dict[str, Any] = {"summary": summary}

        if validate:
            validation = anchor_registry.validate_references()
            result["validation"] = {
                "valid": validation.valid,
                "missing_anchors": [
                    {"ref_doc": str(r), "anchor": a, "source": str(s)}
                    for r, a, s in validation.missing_anchors
                ],
                "value_mismatches": [
                    {"ref_doc": str(r), "anchor": a, "expected": e, "actual": act}
                    for r, a, e, act in validation.value_mismatches
                ],
                "orphan_references": [
                    {"ref_doc": str(r), "anchor": a}
                    for r, a in validation.orphan_references
                ],
            }

        # List all anchors
        anchors = []
        for anchor in anchor_registry.get_all_anchors():
            refs = anchor_registry.get_referencing_documents(anchor.document_path, anchor.name)
            anchors.append(
                {
                    "name": anchor.name,
                    "value": anchor.value,
                    "document": str(anchor.document_path),
                    "description": anchor.description,
                    "referenced_by_count": len(refs),
                }
            )
        result["anchors"] = anchors

        return json.dumps(result, indent=2)

    @mcp.tool(
        description="""
        Analyze impact of changing a document.

        Returns what documents would be affected:
        - Direct derivatives
        - Transitive derivatives
        - Child documents
        - Anchor references
        - Translations

        Args:
            document_path: Path to document being changed
            change_type: Type of change (content, metadata, delete, anchor)
            description: Description of the change
        """
    )
    def hierarchy_impact(
        document_path: str,
        change_type: str = "content",
        description: str = "",
    ) -> str:
        """Analyze impact of a document change."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from pathlib import Path

        from ...hierarchy import HierarchyGraph, ImpactAnalyzer

        graph = HierarchyGraph(project)
        analyzer = ImpactAnalyzer(graph)

        if change_type == "delete":
            report = analyzer.analyze_deletion(Path(document_path))
        else:
            report = analyzer.analyze_change(
                Path(document_path),
                change_type,
                description or f"Change to {document_path}",
            )

        return json.dumps(report.to_dict(), indent=2)

    @mcp.tool(
        description="""
        Analyze documentation coverage.

        Returns:
        - Coverage score (0-100)
        - Missing derived documents
        - Orphan documents
        - Incomplete derivation chains
        - Missing translations (if languages specified)

        Args:
            languages: Comma-separated list of language codes to check translations
        """
    )
    def hierarchy_coverage(languages: str = None) -> str:
        """Analyze documentation coverage."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import CoverageAnalyzer, HierarchyGraph

        graph = HierarchyGraph(project)
        analyzer = CoverageAnalyzer(graph)

        lang_list = languages.split(",") if languages else None
        report = analyzer.analyze(lang_list)

        return json.dumps(report.to_dict(), indent=2)

    @mcp.tool(
        description="""
        Get coverage suggestions.

        Returns prioritized suggestions for improving documentation coverage,
        sorted by priority (critical, high, medium, low).
        """
    )
    def hierarchy_coverage_suggestions() -> str:
        """Get coverage improvement suggestions."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from ...hierarchy import CoverageAnalyzer, HierarchyGraph

        graph = HierarchyGraph(project)
        analyzer = CoverageAnalyzer(graph)
        suggestions = analyzer.get_suggestions()

        return json.dumps({"suggestions": suggestions}, indent=2)

    @mcp.tool(
        description="""
        Get derivation chains from a document.

        Returns all paths from the source document through its derivatives,
        showing how changes propagate through the documentation.

        Args:
            document_path: Path to the source document
        """
    )
    def hierarchy_derivation_chains(document_path: str) -> str:
        """Get derivation chains from a document."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})
        from pathlib import Path

        from ...hierarchy import HierarchyGraph, ImpactAnalyzer

        graph = HierarchyGraph(project)
        analyzer = ImpactAnalyzer(graph)
        chains = analyzer.get_impact_chain(Path(document_path))

        return json.dumps(
            {
                "source": document_path,
                "chains": [[str(p) for p in chain] for chain in chains],
                "chain_count": len(chains),
            },
            indent=2,
        )
