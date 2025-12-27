"""Dependency tracking MCP tools using the UnifiedRegistry via RegistryManager."""

import json


def _get_registry_manager(server_instance):
    """Get or create the RegistryManager for the project."""
    from ...relationships import get_registry_manager, init_registry_manager

    project = server_instance.project
    if not project:
        return None

    registry_manager = get_registry_manager(project)
    if registry_manager is None:
        registry_manager = init_registry_manager(project)

    return registry_manager


def register_dependency_tools(mcp, server_instance):
    """Register dependency tracking MCP tools."""

    @mcp.tool()
    async def dependency_status(document_path: str = None) -> str:
        """
        Get dependency status with hash-based change detection.

        Automatically detects when any dependency content has changed
        since the document was last reviewed.

        Args:
            document_path: Check specific document (optional, shows all if not provided)

        Returns:
            Dependency status showing current/stale state for each dependency.
        """
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"}, indent=2)

        registry = manager.registry

        if document_path:
            try:
                validated_path = server_instance._validate_path(document_path)
            except ValueError as e:
                return json.dumps({"error": str(e)}, indent=2)

            node = registry.get_node(validated_path)
            if not node:
                return json.dumps({"error": f"Document not found: {document_path}"}, indent=2)

            edges = registry.get_outgoing_edges(validated_path)
            stale_edges = [e for e in edges if e.is_stale]

            return json.dumps(
                {
                    "path": str(validated_path),
                    "title": node.title or validated_path.stem,
                    "total_dependencies": len(edges),
                    "stale_dependencies": len(stale_edges),
                    "is_stale": node.is_stale,
                    "dependencies": [
                        {
                            "target": str(e.target),
                            "type": e.edge_type.value,
                            "source_hash": e.source_hash,
                            "target_hash": e.target_hash,
                            "is_stale": e.is_stale,
                            "stale_reason": e.stale_reason,
                        }
                        for e in edges
                    ],
                },
                indent=2,
            )
        else:
            # Show all documents
            statuses = []
            for node in registry.all_nodes():
                edges = registry.get_outgoing_edges(node.path)
                stale_edges = [e for e in edges if e.is_stale]

                statuses.append({
                    "path": str(node.path),
                    "title": node.title or node.path.stem,
                    "total_deps": len(edges),
                    "stale_deps": len(stale_edges),
                    "is_stale": node.is_stale,
                })

            stale_count = sum(1 for s in statuses if s["is_stale"])

            return json.dumps(
                {
                    "total_documents": len(statuses),
                    "documents_with_stale_deps": stale_count,
                    "documents": statuses,
                },
                indent=2,
            )

    @mcp.tool()
    async def stale_dependencies() -> str:
        """
        Get all documents with stale dependencies.

        Returns documents whose dependent content has changed
        since they were last reviewed.
        """
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"}, indent=2)

        stale_docs = manager.get_stale_documents()

        stale_list = []
        for doc in stale_docs:
            edges = manager.registry.get_outgoing_edges(doc.path)
            stale_edges = [e for e in edges if e.is_stale]

            stale_list.append({
                "path": str(doc.path),
                "title": doc.title,
                "stale_count": len(stale_edges),
                "stale_deps": [
                    {
                        "target": str(e.target),
                        "type": e.edge_type.value,
                        "old_hash": e.source_hash,
                        "new_hash": e.target_hash,
                        "reason": e.stale_reason,
                    }
                    for e in stale_edges
                ],
            })

        return json.dumps(
            {
                "count": len(stale_list),
                "stale_documents": stale_list,
            },
            indent=2,
        )

    @mcp.tool()
    async def mark_dependencies_current(document_path: str) -> str:
        """
        Mark all dependencies of a document as current.

        Call this after reviewing/updating a document to acknowledge
        that you've verified its dependencies are correct.

        Args:
            document_path: Path to the document to mark as current

        Returns:
            Result with number of dependencies updated.
        """
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(document_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        # Mark the document and its edges as fresh
        manager.mark_fresh(validated_path)
        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "updated",
                "document": str(validated_path),
                "message": "Document and dependencies marked as current",
            },
            indent=2,
        )

    @mcp.tool()
    async def refresh_dependencies(sync_hashes: bool = True) -> str:
        """
        Refresh the dependency graph by scanning all documents.

        Rebuilds the graph of document relationships and optionally
        syncs all dependency hashes.

        Args:
            sync_hashes: Whether to sync hashes after refresh (default: True)

        Returns:
            Summary of refreshed dependencies.
        """
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"}, indent=2)

        result = manager.refresh()
        report = manager.registry.generate_report()

        output = {
            "status": "refreshed",
            "summary": report["summary"],
            "by_type": report.get("by_type", {}),
            "elapsed_seconds": result.get("elapsed_seconds", 0),
        }

        if sync_hashes:
            manager.mark_all_fresh()
            output["hashes_synced"] = True

        server_instance._invalidate_cache()

        return json.dumps(output, indent=2)

    @mcp.tool()
    async def dependency_report() -> str:
        """
        Generate comprehensive dependency status report.

        Provides overview of all document dependencies, stale items,
        and dependency types.
        """
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"}, indent=2)

        registry = manager.registry
        report = registry.generate_report()

        # Add staleness summary
        stale_docs = manager.get_stale_documents()

        # Count edges by type
        edge_types = {}
        stale_edges = 0
        total_edges = 0

        for node in registry.all_nodes():
            edges = registry.get_outgoing_edges(node.path)
            for edge in edges:
                total_edges += 1
                edge_type = edge.edge_type.value
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
                if edge.is_stale:
                    stale_edges += 1

        return json.dumps(
            {
                "dependency_graph": {
                    "total_documents": report["summary"]["total_documents"],
                    "total_relationships": report["summary"]["total_relationships"],
                    "roots": report["summary"]["root_documents"],
                    "orphans": report["summary"]["orphan_documents"],
                    "by_type": edge_types,
                },
                "staleness": {
                    "stale_documents": len(stale_docs),
                    "stale_edges": stale_edges,
                    "total_edges": total_edges,
                    "freshness_percentage": round(
                        (total_edges - stale_edges) / total_edges * 100, 1
                    ) if total_edges > 0 else 100,
                },
            },
            indent=2,
        )
