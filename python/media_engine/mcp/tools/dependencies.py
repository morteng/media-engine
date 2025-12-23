"""Dependency tracking MCP tools with hash-based change detection."""

import json


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
        from ...dependencies import DependencyHashTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = DependencyHashTracker(server_instance.project)

        if document_path:
            try:
                validated_path = server_instance._validate_path(document_path)
            except ValueError as e:
                return json.dumps({"error": str(e)}, indent=2)

            status = tracker.check_document(validated_path)

            return json.dumps(
                {
                    "path": str(status.path),
                    "title": status.title,
                    "total_dependencies": status.total_dependencies,
                    "stale_dependencies": status.stale_dependencies,
                    "is_stale": status.is_stale,
                    "dependencies": [
                        {
                            "target": d.target_path,
                            "type": d.dep_type,
                            "recorded_hash": d.recorded_hash,
                            "current_hash": d.current_hash,
                            "is_stale": d.is_stale,
                        }
                        for d in status.dependencies
                    ],
                },
                indent=2,
            )
        else:
            statuses = tracker.get_all_statuses()

            return json.dumps(
                {
                    "total_documents": len(statuses),
                    "documents_with_stale_deps": sum(1 for s in statuses if s.is_stale),
                    "documents": [
                        {
                            "path": str(s.path),
                            "title": s.title,
                            "total_deps": s.total_dependencies,
                            "stale_deps": s.stale_dependencies,
                            "is_stale": s.is_stale,
                        }
                        for s in statuses
                    ],
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
        from ...dependencies import DependencyHashTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = DependencyHashTracker(server_instance.project)
        stale = tracker.get_all_stale()

        return json.dumps(
            {
                "count": len(stale),
                "stale_documents": [
                    {
                        "path": str(s.path),
                        "title": s.title,
                        "stale_count": s.stale_dependencies,
                        "stale_deps": [
                            {
                                "target": d.target_path,
                                "type": d.dep_type,
                                "old_hash": d.recorded_hash,
                                "new_hash": d.current_hash,
                            }
                            for d in s.dependencies
                            if d.is_stale
                        ],
                    }
                    for s in stale
                ],
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
        from ...dependencies import DependencyHashTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(document_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        tracker = DependencyHashTracker(server_instance.project)
        updated = tracker.mark_current(validated_path)

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "updated",
                "document": str(validated_path),
                "dependencies_updated": updated,
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
        from ...dependencies import DependencyGraph, DependencyHashTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        graph = DependencyGraph(server_instance.project)
        graph.refresh()

        report = graph.generate_report()

        result = {
            "status": "refreshed",
            "summary": report["summary"],
            "by_type": report["by_type"],
        }

        if sync_hashes:
            tracker = DependencyHashTracker(server_instance.project)
            synced = tracker.sync_from_graph(graph)
            result["hashes_synced"] = synced

        server_instance._invalidate_cache()

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def dependency_report() -> str:
        """
        Generate comprehensive dependency status report.

        Provides overview of all document dependencies, stale items,
        and dependency types.
        """
        from ...dependencies import DependencyGraph, DependencyHashTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        graph = DependencyGraph(server_instance.project)
        tracker = DependencyHashTracker(server_instance.project)

        graph_report = graph.generate_report()
        hash_report = tracker.generate_report()

        return json.dumps(
            {
                "dependency_graph": graph_report,
                "hash_tracking": hash_report,
            },
            indent=2,
        )
