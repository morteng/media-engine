"""
Hierarchy API routes for the dashboard.

Provides endpoints for document hierarchy tree visualization.
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
        project = get_project()
        if not project:
            return {"error": "No project found", "nodes": []}

        from ...hierarchy import HierarchyRegistry

        registry = HierarchyRegistry(project)
        registry.refresh()

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
            if language:
                # Check if path contains language code
                path_parts = path.parts
                lang_found = False
                for part in path_parts:
                    if part in project.languages:
                        lang_found = True
                        if part != language:
                            return None
                        break

            children = []
            for child_path in registry.get_children(path):
                child_node = build_tree_node(child_path, visited.copy())
                if child_node:
                    children.append(child_node)

            return {
                "path": str(path),
                "title": node.title or path.stem,
                "doc_type": node.doc_type.value if node.doc_type else "chapter",
                "lifecycle": node.lifecycle.value if node.lifecycle else "living",
                "is_stale": node.is_stale,
                "level": node.level,
                "sequence_order": node.sequence_order,
                "has_anchors": bool(node.anchors),
                "derived_from_count": len(node.derived_from),
                "children": sorted(children, key=lambda x: x.get("sequence_order", 0)),
            }

        # Build tree from roots
        roots = registry.get_roots()
        tree_nodes = []
        for root_path in roots:
            node = build_tree_node(root_path)
            if node:
                tree_nodes.append(node)

        # Sort roots by sequence_order
        tree_nodes.sort(key=lambda x: x.get("sequence_order", 0))

        return {
            "nodes": tree_nodes,
            "total_count": len(registry.get_all_nodes()),
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
        project = get_project()
        if not project:
            return {"error": "No project found"}

        from ...hierarchy import HierarchyRegistry
        from ...hierarchy.anchors import AnchorRegistry

        hierarchy = HierarchyRegistry(project)
        hierarchy.refresh()

        # Resolve path
        doc_path = Path(path)
        if not doc_path.is_absolute():
            # Try to find in registry
            for node_path_str in hierarchy._nodes:
                if node_path_str.endswith(str(doc_path)) or str(doc_path) in node_path_str:
                    doc_path = Path(node_path_str)
                    break

        node = hierarchy.get_node(doc_path)
        if not node:
            return {"error": f"Node not found: {path}"}

        # Get anchor info
        anchor_registry = AnchorRegistry(hierarchy)

        # Get anchors defined in this document
        defined_anchors = []
        for anchor_id, anchor_info in (node.anchors or {}).items():
            defined_anchors.append({
                "id": anchor_id,
                "value": anchor_info.get("value") if isinstance(anchor_info, dict) else anchor_info,
            })

        # Get anchor references from this document
        anchor_refs = []
        if node.raw_metadata and "anchor_refs" in node.raw_metadata:
            for ref in node.raw_metadata["anchor_refs"]:
                anchor_refs.append({
                    "source": ref.get("source", ""),
                    "anchor": ref.get("anchor", ""),
                })

        return {
            "path": str(doc_path),
            "title": node.title,
            "doc_type": node.doc_type.value if node.doc_type else "chapter",
            "lifecycle": node.lifecycle.value if node.lifecycle else "living",
            "is_stale": node.is_stale,
            "level": node.level,
            "sequence_order": node.sequence_order,
            "parent": str(node.parent) if node.parent else None,
            "children": [str(c) for c in hierarchy.get_children(doc_path)],
            "ancestors": [str(a) for a in hierarchy.get_ancestors(doc_path)],
            "siblings": [str(s) for s in hierarchy.get_siblings(doc_path)],
            "derived_from": [
                {
                    "path": str(d.path),
                    "version": d.version,
                    "relationship": d.relationship.value if d.relationship else "implements",
                }
                for d in node.derived_from
            ],
            "derivatives": [str(d) for d in hierarchy.get_derivatives(doc_path)],
            "defined_anchors": defined_anchors,
            "anchor_refs": anchor_refs,
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
        project = get_project()
        if not project:
            return {"error": "No project found", "breadcrumbs": []}

        from ...hierarchy import HierarchyRegistry

        hierarchy = HierarchyRegistry(project)
        hierarchy.refresh()

        # Resolve path
        doc_path = Path(path)
        if not doc_path.is_absolute():
            for node_path_str in hierarchy._nodes:
                if node_path_str.endswith(str(doc_path)) or str(doc_path) in node_path_str:
                    doc_path = Path(node_path_str)
                    break

        node = hierarchy.get_node(doc_path)
        if not node:
            return {"error": f"Node not found: {path}", "breadcrumbs": []}

        # Get ancestors and reverse to get root->doc order
        ancestors = hierarchy.get_ancestors(doc_path)
        ancestors.reverse()

        breadcrumbs = []
        for ancestor_path in ancestors:
            ancestor_node = hierarchy.get_node(ancestor_path)
            if ancestor_node:
                breadcrumbs.append({
                    "path": str(ancestor_path),
                    "title": ancestor_node.title or ancestor_path.stem,
                    "doc_type": ancestor_node.doc_type.value if ancestor_node.doc_type else "chapter",
                })

        # Add current document
        breadcrumbs.append({
            "path": str(doc_path),
            "title": node.title or doc_path.stem,
            "doc_type": node.doc_type.value if node.doc_type else "chapter",
        })

        return {"breadcrumbs": breadcrumbs}

    @router.get("/api/hierarchy/derivation-graph")
    async def get_derivation_graph():
        """
        Get the derivation graph for visualization.

        Returns:
            Graph structure with nodes and edges for derivation relationships.
        """
        project = get_project()
        if not project:
            return {"error": "No project found", "nodes": [], "edges": []}

        from ...hierarchy import HierarchyRegistry

        hierarchy = HierarchyRegistry(project)
        hierarchy.refresh()

        nodes = []
        edges = []
        node_ids = set()

        for node in hierarchy.get_all_nodes():
            path_str = str(node.path)
            node_ids.add(path_str)
            nodes.append({
                "id": path_str,
                "title": node.title or node.path.stem,
                "doc_type": node.doc_type.value if node.doc_type else "chapter",
                "lifecycle": node.lifecycle.value if node.lifecycle else "living",
                "is_stale": node.is_stale,
            })

            # Add derivation edges
            for source in node.derived_from:
                source_str = str(source.path)
                edges.append({
                    "source": source_str,
                    "target": path_str,
                    "relationship": source.relationship.value if source.relationship else "implements",
                    "version": source.version,
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    @router.get("/api/hierarchy/flow-graph")
    async def get_flow_graph(
        focus_path: str = None,
        direction: str = "both",
        max_depth: int = 3,
        language: str = None,
    ):
        """
        Get flow graph data with layout positions for visualization.

        Args:
            focus_path: Optional path to focus the graph around
            direction: "upstream", "downstream", or "both"
            max_depth: Maximum depth to traverse
            language: Filter to specific language

        Returns:
            Positioned graph data for rendering.
        """
        project = get_project()
        if not project:
            return {"error": "No project found", "nodes": [], "edges": [], "levels": []}

        from ...hierarchy import HierarchyRegistry

        hierarchy = HierarchyRegistry(project)
        hierarchy.refresh()

        # Build the graph from all nodes
        all_nodes = {}
        all_edges = []

        for node in hierarchy.get_all_nodes():
            path_str = str(node.path)

            # Filter by language if specified
            if language:
                path_parts = node.path.parts
                lang_found = False
                for part in path_parts:
                    if part in project.languages:
                        lang_found = True
                        if part != language:
                            continue
                        break

            all_nodes[path_str] = {
                "id": path_str,
                "title": node.title or node.path.stem,
                "doc_type": node.doc_type.value if node.doc_type else "chapter",
                "lifecycle": node.lifecycle.value if node.lifecycle else "living",
                "is_stale": node.is_stale,
                "level": node.level,
                "sequence_order": node.sequence_order,
            }

            # Add derivation edges
            for source in node.derived_from:
                source_str = str(source.path)
                all_edges.append({
                    "source": source_str,
                    "target": path_str,
                    "type": source.relationship.value if source.relationship else "implements",
                    "is_stale": node.is_stale,
                    "version": source.version,
                })

        # Group nodes by level for layered layout
        levels = {}
        for node_id, node_data in all_nodes.items():
            level = node_data.get("level", 0)
            if level not in levels:
                levels[level] = []
            levels[level].append(node_id)

        # Sort each level by sequence order
        for level in levels:
            levels[level].sort(
                key=lambda nid: all_nodes[nid].get("sequence_order", 0)
            )

        # Calculate positions for visualization
        level_keys = sorted(levels.keys())
        positioned_nodes = []

        for level_idx, level in enumerate(level_keys):
            node_ids = levels[level]
            for node_idx, node_id in enumerate(node_ids):
                node_data = all_nodes[node_id].copy()
                node_data["position"] = {
                    "x": (node_idx + 1) * 200,
                    "y": (level_idx + 1) * 120,
                }
                positioned_nodes.append(node_data)

        # Calculate staleness summary
        total_nodes = len(positioned_nodes)
        stale_nodes = sum(1 for n in positioned_nodes if n.get("is_stale"))
        stale_edges = sum(1 for e in all_edges if e.get("is_stale"))

        return {
            "nodes": positioned_nodes,
            "edges": all_edges,
            "levels": [{"level": k, "count": len(levels[k])} for k in level_keys],
            "staleness_summary": {
                "total_nodes": total_nodes,
                "stale_nodes": stale_nodes,
                "stale_percentage": round(stale_nodes / total_nodes * 100, 1) if total_nodes > 0 else 0,
                "stale_edges": stale_edges,
            },
        }
