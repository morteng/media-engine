"""
MCP tools for Unified Relationship Registry.

Provides comprehensive tools for:
- Relationship status and visualization
- Staleness detection across all relationship types
- Impact analysis for document changes
- Relationship type queries
- Consistency anchor management
"""

import json


def register_relationship_tools(mcp, server_instance) -> None:
    """Register unified relationship registry tools."""

    @mcp.tool(
        description="""
        Get unified relationship status.

        Returns summary of all document relationships including:
        - Total documents and relationships
        - Stale, orphan, and root document counts
        - Consistency anchors
        - Breakdown by relationship type
        """
    )
    def relationships_status() -> str:
        """Get unified relationship status overview."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import UnifiedRegistry

        registry = UnifiedRegistry(project)
        report = registry.generate_report()

        return json.dumps(report, indent=2)

    @mcp.tool(
        description="""
        Refresh the unified relationship registry.

        Scans all documents to rebuild the relationship graph including:
        - Parent/child hierarchies
        - Derivation chains (implements, extends, summarizes)
        - Translations
        - Dependencies (depends_on)
        - Asset references
        - Consistency anchors
        """
    )
    def relationships_refresh() -> str:
        """Refresh unified registry from documents."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import RelationshipScanner, UnifiedRegistry

        registry = UnifiedRegistry(project)
        scanner = RelationshipScanner(project, registry)
        scanner.full_scan()
        registry.save()

        report = registry.generate_report()
        summary = report.get("summary", {})

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "refreshed",
                "total_documents": summary.get("total_documents", 0),
                "total_relationships": summary.get("total_relationships", 0),
                "stale_documents": summary.get("stale_documents", 0),
                "anchors": summary.get("anchors", 0),
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get stale documents from unified registry.

        Returns documents with stale relationships including:
        - Stale edges with reasons (content_changed, target_missing)
        - Transitive staleness sources
        - Suggested actions for each stale document
        """
    )
    def relationships_stale() -> str:
        """Get stale documents from unified registry."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import StalenessTracker, UnifiedRegistry

        registry = UnifiedRegistry(project)
        tracker = StalenessTracker(registry)
        stale_statuses = tracker.check_all()

        return json.dumps(
            {
                "count": len(stale_statuses),
                "stale_documents": [s.to_dict() for s in stale_statuses],
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Analyze impact of changing a document.

        Returns all documents that would be affected by changes:
        - Direct dependents
        - Transitive dependents through derivation chains
        - Documents referencing the target

        Args:
            document_path: Path to the document being changed (relative to content/)
        """
    )
    def relationships_impact(document_path: str) -> str:
        """Analyze impact of changing a document."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})


        from ...relationships import UnifiedRegistry

        registry = UnifiedRegistry(project)

        # Resolve document path
        doc_path = project.content_dir / document_path
        if not doc_path.exists():
            doc_path = doc_path.with_suffix(".md")

        if not doc_path.exists():
            return json.dumps({"error": f"Document not found: {document_path}"})

        affected = registry.get_impact(doc_path)

        # Get edge details for each affected document
        affected_details = []
        for affected_doc in affected:
            edges = registry.get_outgoing_edges(affected_doc)
            relevant = [e for e in edges if str(e.target) == str(doc_path)]

            affected_details.append(
                {
                    "document": str(affected_doc.relative_to(project.content_dir)),
                    "relationship_types": [e.edge_type.value for e in relevant],
                }
            )

        return json.dumps(
            {
                "source": document_path,
                "affected_count": len(affected),
                "affected_documents": affected_details,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get relationships for a specific document.

        Returns all incoming and outgoing edges for the document:
        - Outgoing: what this document depends on
        - Incoming: what depends on this document

        Args:
            document_path: Path to the document (relative to content/)
        """
    )
    def relationships_document(document_path: str) -> str:
        """Get relationships for a specific document."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})


        from ...relationships import UnifiedRegistry

        registry = UnifiedRegistry(project)

        # Resolve document path
        doc_path = project.content_dir / document_path
        if not doc_path.exists():
            doc_path = doc_path.with_suffix(".md")

        if not doc_path.exists():
            return json.dumps({"error": f"Document not found: {document_path}"})

        outgoing = registry.get_outgoing_edges(doc_path)
        incoming = registry.get_incoming_edges(doc_path)

        def edge_to_dict(edge, show_target=True):
            if show_target:
                path = edge.target
            else:
                path = edge.source

            try:
                rel_path = str(path.relative_to(project.content_dir))
            except ValueError:
                rel_path = str(path)

            return {
                "path": rel_path,
                "type": edge.edge_type.value,
                "is_stale": edge.is_stale,
                "stale_reason": edge.stale_reason,
            }

        return json.dumps(
            {
                "document": document_path,
                "outgoing": [edge_to_dict(e, show_target=True) for e in outgoing],
                "incoming": [edge_to_dict(e, show_target=False) for e in incoming],
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get relationships filtered by type.

        Available types:
        - parent: Parent document relationships
        - implements: Document implements another
        - extends: Document extends another
        - summarizes: Document summarizes another
        - translates: Translation relationship
        - references: Cross-reference link
        - uses_asset: Asset usage
        - anchor_ref: Consistency anchor reference
        - depends_on: Explicit dependency

        Args:
            edge_type: Type of relationship to query
        """
    )
    def relationships_by_type(edge_type: str) -> str:
        """Get relationships filtered by type."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import EdgeType, UnifiedRegistry

        registry = UnifiedRegistry(project)

        # Validate edge type
        valid_types = [e.value for e in EdgeType]
        if edge_type not in valid_types:
            return json.dumps(
                {"error": f"Invalid edge type. Valid types: {valid_types}"}
            )

        # Collect all edges of this type
        edges_of_type = []
        for node in registry.all_nodes():
            for edge in registry.get_outgoing_edges(node.path):
                if edge.edge_type.value == edge_type:
                    try:
                        source_rel = str(edge.source.relative_to(project.content_dir))
                    except ValueError:
                        source_rel = str(edge.source)

                    try:
                        target_rel = str(edge.target.relative_to(project.content_dir))
                    except ValueError:
                        target_rel = str(edge.target)

                    edges_of_type.append(
                        {
                            "source": source_rel,
                            "target": target_rel,
                            "is_stale": edge.is_stale,
                        }
                    )

        return json.dumps(
            {
                "edge_type": edge_type,
                "count": len(edges_of_type),
                "relationships": edges_of_type,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Mark a document's relationships as fresh.

        Updates hashes to current values and clears staleness markers.
        Use after reviewing a document to acknowledge its relationships are verified.

        Args:
            document_path: Path to the document (relative to content/)
        """
    )
    def relationships_sync(document_path: str) -> str:
        """Mark a document's relationships as fresh."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})


        from ...relationships import StalenessTracker, UnifiedRegistry

        registry = UnifiedRegistry(project)
        tracker = StalenessTracker(registry)

        # Resolve document path
        doc_path = project.content_dir / document_path
        if not doc_path.exists():
            doc_path = doc_path.with_suffix(".md")

        if not doc_path.exists():
            return json.dumps({"error": f"Document not found: {document_path}"})

        tracker.mark_fresh(doc_path)

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "synced",
                "document": document_path,
                "message": "All relationships marked as fresh",
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Mark all documents as fresh.

        Updates all relationship hashes to current values.
        Use after a bulk update or initial setup.
        """
    )
    def relationships_sync_all() -> str:
        """Mark all documents as fresh."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import StalenessTracker, UnifiedRegistry

        registry = UnifiedRegistry(project)
        tracker = StalenessTracker(registry)

        count = 0
        for node in registry.all_nodes():
            tracker.mark_fresh(node.path)
            count += 1

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "synced",
                "documents_synced": count,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get consistency anchors from unified registry.

        Returns all anchors defined across documents with:
        - Anchor names and values
        - Defining documents
        - Reference counts
        """
    )
    def relationships_anchors() -> str:
        """Get consistency anchors."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        import json as json_lib
        from pathlib import Path

        from ...relationships import UnifiedRegistry

        registry = UnifiedRegistry(project)

        # Load anchors from registry data
        if registry.data_path.exists():
            with open(registry.data_path) as f:
                data = json_lib.load(f)
            anchors_data = data.get("anchors", {})
        else:
            anchors_data = {}

        anchors = []
        for anchor_id, anchor in anchors_data.items():
            try:
                defined_in = str(
                    Path(anchor["defined_in"]).relative_to(project.content_dir)
                )
            except ValueError:
                defined_in = anchor["defined_in"]

            refs = anchor.get("referenced_in", [])

            anchors.append(
                {
                    "id": anchor_id,
                    "value": anchor["value"],
                    "type": anchor["value_type"],
                    "defined_in": defined_in,
                    "reference_count": len(refs),
                }
            )

        return json.dumps(
            {
                "count": len(anchors),
                "anchors": anchors,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Export relationship graph for visualization.

        Args:
            format: Output format - "dot" (Graphviz), "mermaid", or "json"
            edge_types: Comma-separated edge types to include (optional, all if not specified)
        """
    )
    def relationships_export(format: str = "json", edge_types: str = None) -> str:
        """Export relationship graph for visualization."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import UnifiedRegistry

        registry = UnifiedRegistry(project)

        type_filter = None
        if edge_types:
            type_filter = [t.strip() for t in edge_types.split(",")]

        if format == "dot":
            content = _generate_dot(registry, project, type_filter)
            return content
        elif format == "mermaid":
            content = _generate_mermaid(registry, project, type_filter)
            return content
        else:
            report = registry.generate_report()
            return json.dumps(report, indent=2)

    @mcp.tool(
        description="""
        Get comprehensive relationship report.

        Combines status, staleness, and type distribution for
        a complete overview of document relationships.
        """
    )
    def relationships_report() -> str:
        """Get comprehensive relationship report."""
        project = server_instance.project
        if not project:
            return json.dumps({"error": "No project found"})

        from ...relationships import StalenessTracker, UnifiedRegistry

        registry = UnifiedRegistry(project)
        tracker = StalenessTracker(registry)

        # Get base report
        report = registry.generate_report()

        # Add staleness report
        stale_report = tracker.get_stale_report()
        report["staleness"] = stale_report

        return json.dumps(report, indent=2)


def _generate_dot(registry, project, edge_types=None) -> str:
    """Generate DOT format for Graphviz."""
    lines = ["digraph relationships {"]
    lines.append("  rankdir=LR;")
    lines.append("  node [shape=box, fontname=Arial];")
    lines.append("  edge [fontname=Arial, fontsize=10];")

    colors = {
        "parent": "black",
        "implements": "green",
        "extends": "blue",
        "summarizes": "purple",
        "translates": "orange",
        "references": "gray",
        "uses_asset": "brown",
        "depends_on": "darkgreen",
        "anchor_ref": "red",
    }

    for node in registry.all_nodes():
        for edge in registry.get_outgoing_edges(node.path):
            if edge_types and edge.edge_type.value not in edge_types:
                continue

            source = node.path.stem
            target = edge.target.stem
            edge_type = edge.edge_type.value
            color = colors.get(edge_type, "gray")
            style = ", style=dashed" if edge.is_stale else ""

            lines.append(
                f'  "{source}" -> "{target}" [color={color}, label="{edge_type}"{style}];'
            )

    lines.append("}")
    return "\n".join(lines)


def _generate_mermaid(registry, project, edge_types=None) -> str:
    """Generate Mermaid format for diagrams."""
    lines = ["graph LR"]

    for node in registry.all_nodes():
        for edge in registry.get_outgoing_edges(node.path):
            if edge_types and edge.edge_type.value not in edge_types:
                continue

            source = node.path.stem.replace("-", "_").replace(" ", "_")
            target = edge.target.stem.replace("-", "_").replace(" ", "_")
            edge_type = edge.edge_type.value

            arrow = "-...->" if edge.is_stale else "-->"
            lines.append(f"    {source} {arrow}|{edge_type}| {target}")

    return "\n".join(lines)
