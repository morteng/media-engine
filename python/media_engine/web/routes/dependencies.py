"""
Dependencies API routes.

Uses the Unified Registry (cached) for efficient queries.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_dependencies_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register dependency-related routes."""
    from pathlib import Path

    def _get_registry():
        """Get the cached registry manager."""
        from ...relationships import get_registry_manager, init_registry_manager

        project = get_project()
        if not project:
            return None, None

        registry_manager = get_registry_manager(project)
        if registry_manager is None:
            registry_manager = init_registry_manager(project)

        return project, registry_manager

    @router.get("/api/dependencies")
    async def get_dependencies():
        """Get all document dependencies from the unified registry."""
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "items": [], "tree": [], "stats": {}}

        registry = registry_manager.registry

        # Build dependency data from unified registry
        items = []
        for node in registry.all_nodes():
            # Get outgoing edges (what this document depends on)
            outgoing = registry.get_outgoing_edges(node.path)
            depends_on = [str(e.target) for e in outgoing]

            # Get incoming edges (what depends on this document)
            incoming = registry.get_incoming_edges(node.path)
            dependents = [str(e.source) for e in incoming]

            items.append({
                "path": str(node.path),
                "title": node.title,
                "type": node.doc_type or "document",
                "lifecycle": node.lifecycle,
                "is_stale": node.is_stale,
                "language": node.language,
                "depends_on": depends_on,
                "dependents": dependents,
            })

        # Build tree structure by type
        tree = _build_dependency_tree(items)

        return {
            "items": items,
            "tree": tree,
            "stats": {
                "total": len(items),
                "with_deps": len([i for i in items if i["depends_on"]]),
                "roots": len([i for i in items if not i["depends_on"]]),
                "stale": len([i for i in items if i.get("is_stale")]),
            },
        }

    @router.get("/api/dependencies/impact/{path:path}")
    async def get_dependency_impact(path: str):
        """Get documents affected if a file changes."""
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "source": path, "affected": [], "count": 0}

        # Resolve path
        doc_path = Path(path)
        if not doc_path.is_absolute():
            doc_path = project.content_dir / path

        # Get impact set from registry
        affected_paths = registry_manager.get_impact(doc_path)

        # Build response with node details
        affected = []
        for affected_path in affected_paths:
            node = registry_manager.get_node(affected_path)
            if node:
                affected.append({
                    "path": str(affected_path),
                    "title": node.title,
                    "type": node.doc_type or "document",
                    "is_stale": node.is_stale,
                })

        return {
            "source": path,
            "affected": affected,
            "count": len(affected),
        }

    @router.get("/api/dependencies/graph")
    async def get_dependency_graph(language: str = None):
        """
        Get full dependency graph for visualization.

        Returns nodes and edges suitable for graph rendering.
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "nodes": [], "edges": []}

        registry = registry_manager.registry

        nodes = []
        edges = []

        for node in registry.all_nodes():
            # Filter by language if specified
            if language and node.language and node.language != language:
                continue

            nodes.append({
                "id": str(node.path),
                "label": node.title or node.path.stem,
                "type": node.doc_type or "document",
                "lifecycle": node.lifecycle,
                "is_stale": node.is_stale,
                "language": node.language,
            })

            # Add edges
            for edge in registry.get_outgoing_edges(node.path):
                edges.append({
                    "source": str(edge.source),
                    "target": str(edge.target),
                    "type": edge.edge_type.value,
                    "is_stale": edge.is_stale,
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

    @router.get("/api/dependencies/stale")
    async def get_stale_dependencies():
        """Get all documents with stale dependencies."""
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "stale": []}

        stale_docs = registry_manager.get_stale_documents()

        return {
            "count": len(stale_docs),
            "stale": [
                {
                    "path": str(doc.path),
                    "title": doc.title,
                    "reasons": doc.stale_reasons,
                    "language": doc.language,
                }
                for doc in stale_docs
            ],
        }

    @router.post("/api/dependencies/mark-fresh/{path:path}")
    async def mark_dependency_fresh(path: str):
        """Mark a document's dependencies as reviewed/fresh."""
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found"}

        doc_path = Path(path)
        if not doc_path.is_absolute():
            doc_path = project.content_dir / path

        registry_manager.mark_fresh(doc_path)

        return {"status": "marked_fresh", "path": str(doc_path)}

    @router.get("/api/dependencies/files")
    async def get_trackable_files():
        """Get list of files that can be selected for impact analysis."""
        project, registry_manager = _get_registry()
        if not project:
            return {"files": []}

        registry = registry_manager.registry

        files = []
        for node in registry.all_nodes():
            files.append({
                "path": str(node.path.relative_to(project.root)),
                "name": node.path.name,
                "title": node.title,
                "type": node.doc_type or "document",
                "language": node.language,
            })

        # Sort by type and name
        files.sort(key=lambda x: (x.get("type", ""), x["name"]))

        return {"files": files[:500]}  # Limit to 500


def _build_dependency_tree(items: list) -> list:
    """Build a tree structure from flat dependency list."""
    # Group items by type for better organization
    by_type = {}
    for item in items:
        item_type = item.get("type", "document")
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)

    tree = []
    for type_name, type_items in sorted(by_type.items()):
        tree.append({
            "type": "group",
            "name": type_name.replace("_", " ").title(),
            "count": len(type_items),
            "children": [
                {
                    "type": "item",
                    "path": i["path"],
                    "title": i.get("title"),
                    "item_type": i.get("type"),
                    "is_stale": i.get("is_stale", False),
                    "deps_count": len(i.get("depends_on", [])),
                    "dependents_count": len(i.get("dependents", [])),
                }
                for i in sorted(type_items, key=lambda x: x["path"])
            ],
        })

    return tree
