"""
Hierarchy API routes for the dashboard.

Uses the Unified Registry (cached) for efficient queries.
No longer refreshes on every request - uses incremental updates from file watcher.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_hierarchy_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register hierarchy-related API routes."""

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

    @router.get("/api/hierarchy/tree")
    async def get_hierarchy_tree(language: str = None):
        """
        Get document hierarchy as a tree structure.

        Returns:
            Tree structure with nodes containing:
            - path: Document path
            - title: Document title
            - doc_type: Document type (chapter, operations, etc.)
            - lifecycle: Lifecycle state (living, snapshot, deprecated)
            - is_stale: Whether document is stale
            - children: Child nodes
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "nodes": []}

        registry = registry_manager.registry

        def build_tree_node(path: Path, visited: set = None) -> dict:
            """Build a tree node with children."""
            if visited is None:
                visited = set()

            path_str = str(path)
            if path_str in visited:
                return None  # Prevent circular references
            visited.add(path_str)

            node = registry.get_node(path)
            if not node:
                return None

            # Filter by language if specified
            if language and node.language and node.language != language:
                return None

            children = []
            for child_path in registry.get_children(path):
                child_node = build_tree_node(child_path, visited.copy())
                if child_node:
                    children.append(child_node)

            # Get sequence order from path (e.g., 01_intro -> 1)
            sequence_order = 0
            try:
                stem = path.stem
                if "_" in stem:
                    order_part = stem.split("_")[0]
                    if order_part.isdigit():
                        sequence_order = int(order_part)
            except Exception:
                pass

            return {
                "path": str(path),
                "title": node.title or path.stem,
                "doc_type": node.doc_type,
                "lifecycle": node.lifecycle,
                "is_stale": node.is_stale,
                "language": node.language,
                "sequence_order": sequence_order,
                "has_anchors": bool(node.anchors),
                "children": sorted(children, key=lambda x: x.get("sequence_order", 0)),
            }

        # Build tree from roots
        roots = registry.get_roots()
        tree_nodes = []

        for root_path in roots:
            node = registry.get_node(root_path)
            # Filter by language if specified
            if language and node and node.language != language:
                continue

            tree_node = build_tree_node(root_path)
            if tree_node:
                tree_nodes.append(tree_node)

        # Sort roots by sequence_order
        tree_nodes.sort(key=lambda x: x.get("sequence_order", 0))

        return {
            "nodes": tree_nodes,
            "total_count": len(registry._nodes),
            "root_count": len(roots),
        }

    @router.get("/api/hierarchy/node/{path:path}")
    async def get_hierarchy_node(path: str):
        """
        Get detailed information about a specific hierarchy node.

        Returns:
            Node details including:
            - Basic info (title, type, lifecycle)
            - Parent and children paths
            - Derivation sources
            - Anchors defined
            - Anchor references
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found"}

        registry = registry_manager.registry

        # Resolve path
        doc_path = Path(path)
        if not doc_path.is_absolute():
            # Try to find in registry
            for node_path_str in registry._nodes:
                if node_path_str.endswith(str(doc_path)) or str(doc_path) in node_path_str:
                    doc_path = Path(node_path_str)
                    break

        node = registry.get_node(doc_path)
        if not node:
            return {"error": f"Node not found: {path}"}

        # Get parent and children
        parent = registry.get_parent(doc_path)
        children = registry.get_children(doc_path)
        ancestors = registry.get_ancestors(doc_path)

        # Get siblings
        siblings = []
        if parent:
            siblings = [c for c in registry.get_children(parent) if c != doc_path]

        # Get derivation sources (implements, extends, etc.)
        from ...relationships import EdgeType

        derivation_edges = []
        for edge_type in EdgeType.derivation_types():
            edges = registry.get_outgoing_edges(doc_path, edge_type)
            for edge in edges:
                derivation_edges.append({
                    "path": str(edge.target),
                    "type": edge.edge_type.value,
                    "version": edge.version,
                    "is_stale": edge.is_stale,
                })

        # Get derivatives (documents that derive from this one)
        derivatives = []
        incoming = registry.get_incoming_edges(doc_path)
        for edge in incoming:
            if edge.edge_type in EdgeType.derivation_types():
                derivatives.append(str(edge.source))

        return {
            "path": str(doc_path),
            "title": node.title,
            "doc_type": node.doc_type,
            "lifecycle": node.lifecycle,
            "status": node.status,
            "is_stale": node.is_stale,
            "stale_reasons": node.stale_reasons,
            "language": node.language,
            "parent": str(parent) if parent else None,
            "children": [str(c) for c in children],
            "ancestors": [str(a) for a in ancestors],
            "siblings": [str(s) for s in siblings],
            "derived_from": derivation_edges,
            "derivatives": derivatives,
            "defined_anchors": list(node.anchors.keys()),
            "owner": node.owner,
            "approvers": node.approvers or [],
        }

    @router.get("/api/hierarchy/breadcrumbs/{path:path}")
    async def get_breadcrumbs(path: str):
        """
        Get breadcrumb trail for a document.

        Returns:
            List of ancestors from root to document.
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "breadcrumbs": []}

        registry = registry_manager.registry

        # Resolve path
        doc_path = Path(path)
        if not doc_path.is_absolute():
            for node_path_str in registry._nodes:
                if node_path_str.endswith(str(doc_path)) or str(doc_path) in node_path_str:
                    doc_path = Path(node_path_str)
                    break

        node = registry.get_node(doc_path)
        if not node:
            return {"error": f"Node not found: {path}", "breadcrumbs": []}

        # Get ancestors and reverse to get root->doc order
        ancestors = registry.get_ancestors(doc_path)
        ancestors.reverse()

        breadcrumbs = []
        for ancestor_path in ancestors:
            ancestor_node = registry.get_node(ancestor_path)
            if ancestor_node:
                breadcrumbs.append({
                    "path": str(ancestor_path),
                    "title": ancestor_node.title or ancestor_path.stem,
                    "doc_type": ancestor_node.doc_type,
                })

        # Add current document
        breadcrumbs.append({
            "path": str(doc_path),
            "title": node.title or doc_path.stem,
            "doc_type": node.doc_type,
        })

        return {"breadcrumbs": breadcrumbs}

    @router.get("/api/hierarchy/unified-graph")
    async def get_unified_graph(language: str = None):
        """
        Get unified graph combining all relationship types.

        Combines:
        - Hierarchy relationships (parent/child)
        - Derivation relationships (implements, extends, summarizes)
        - Dependencies (explicit depends_on)
        - References (internal markdown links)
        - Assets (image/file references)
        - Translations (source/translation pairs)

        Returns:
            Unified graph with nodes and typed edges.
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found", "nodes": [], "edges": []}

        registry = registry_manager.registry

        nodes = []
        edges = []

        for doc_node in registry.all_nodes():
            # Filter by language if specified
            if language and doc_node.language and doc_node.language != language:
                continue

            # Determine node type
            path_str = str(doc_node.path)
            node_type = "document"
            if "/assets/" in path_str or "/images/" in path_str:
                node_type = "asset"
            elif doc_node.path.suffix in (".yaml", ".json"):
                node_type = "config"

            nodes.append({
                "id": path_str,
                "label": doc_node.title or doc_node.path.stem,
                "type": node_type,
                "doc_type": doc_node.doc_type,
                "lifecycle": doc_node.lifecycle,
                "is_stale": doc_node.is_stale,
                "language": doc_node.language,
            })

            # Add edges
            for edge in registry.get_outgoing_edges(doc_node.path):
                edges.append({
                    "source": str(edge.source),
                    "target": str(edge.target),
                    "type": edge.edge_type.value,
                    "label": edge.context or edge.edge_type.value,
                    "is_stale": edge.is_stale,
                })

        # Calculate summary stats
        edge_counts = {}
        for edge in edges:
            edge_type = edge["type"]
            edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "edge_types": edge_counts,
            },
        }

    @router.get("/api/hierarchy/stale")
    async def get_stale_documents():
        """
        Get all stale documents and their staleness reasons.
        """
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

    @router.post("/api/hierarchy/refresh")
    async def refresh_hierarchy():
        """
        Force a full refresh of the registry.

        Normally not needed - incremental updates happen automatically.
        Use this if the registry gets out of sync.
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found"}

        result = registry_manager.refresh()
        return result

    @router.post("/api/hierarchy/mark-fresh/{path:path}")
    async def mark_document_fresh(path: str):
        """
        Mark a document and its relationships as fresh.

        Call after reviewing a document to acknowledge its current state.
        """
        project, registry_manager = _get_registry()
        if not project:
            return {"error": "No project found"}

        # Resolve path
        doc_path = Path(path)
        if not doc_path.is_absolute():
            doc_path = project.content_dir / path

        registry_manager.mark_fresh(doc_path)

        return {"status": "marked_fresh", "path": str(doc_path)}
