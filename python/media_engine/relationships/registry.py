"""
Unified Relationship Registry for Media Engine

A single registry that stores all document relationships.
Consolidates dependencies.json, hierarchy.json, and translation tracking.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

from .types import (
    DocumentNode,
    EdgeType,
    RelationshipEdge,
)


class UnifiedRegistry:
    """
    Unified registry for all document relationships.

    Stores:
    - Document nodes with metadata
    - Relationship edges between documents
    - Content hashes for change detection
    - Consistency anchors

    Provides:
    - Graph queries (forward/reverse edges)
    - Impact analysis
    - Staleness detection
    - Migration from legacy systems
    """

    VERSION = "2.0.0"

    def __init__(self, project):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.data_path = self.data_dir / "relationships.json"

        # Graph structure
        self._nodes: dict[str, DocumentNode] = {}

        # Edges: source -> list of edges
        self._forward: dict[str, list[RelationshipEdge]] = defaultdict(list)
        # Reverse index: target -> list of edges
        self._reverse: dict[str, list[RelationshipEdge]] = defaultdict(list)

        # Consistency anchors: anchor_id -> anchor data
        self._anchors: dict[str, dict] = {}

        # Load existing data
        self._load()

    def _load(self):
        """Load registry data from disk."""
        if self.data_path.exists():
            try:
                with open(self.data_path) as f:
                    data = json.load(f)

                # Load nodes
                for path, node_data in data.get("nodes", {}).items():
                    self._nodes[path] = DocumentNode.from_dict(node_data)

                # Load edges
                for source, edges in data.get("edges", {}).items():
                    for edge_data in edges:
                        edge = RelationshipEdge.from_dict(edge_data)
                        self._forward[source].append(edge)
                        self._reverse[str(edge.target)].append(edge)

                # Load anchors
                self._anchors = data.get("anchors", {})

            except (json.JSONDecodeError, KeyError) as e:
                # If corrupted, start fresh
                print(f"Warning: Could not load relationships.json: {e}")
                self._nodes = {}
                self._forward = defaultdict(list)
                self._reverse = defaultdict(list)
                self._anchors = {}

    def _save(self):
        """Save registry data to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "version": self.VERSION,
            "generated_at": datetime.now().isoformat(),
            "nodes": {path: node.to_dict() for path, node in self._nodes.items()},
            "edges": {
                source: [e.to_dict() for e in edges]
                for source, edges in self._forward.items()
            },
            "anchors": self._anchors,
            "summary": {
                "total_nodes": len(self._nodes),
                "total_edges": sum(len(e) for e in self._forward.values()),
                "edge_types": self._count_edge_types(),
                "anchor_count": len(self._anchors),
            },
        }

        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def _count_edge_types(self) -> dict[str, int]:
        """Count edges by type."""
        counts = defaultdict(int)
        for edges in self._forward.values():
            for edge in edges:
                counts[edge.edge_type.value] += 1
        return dict(counts)

    # ==========================================================================
    # Node Operations
    # ==========================================================================

    def add_node(self, node: DocumentNode):
        """Add or update a document node."""
        self._nodes[str(node.path)] = node

    def get_node(self, path: Path) -> Optional[DocumentNode]:
        """Get a document node by path."""
        return self._nodes.get(str(path))

    def remove_node(self, path: Path):
        """Remove a node and all its edges."""
        path_str = str(path)
        if path_str in self._nodes:
            del self._nodes[path_str]

        # Remove forward edges
        if path_str in self._forward:
            for edge in self._forward[path_str]:
                target_str = str(edge.target)
                if target_str in self._reverse:
                    self._reverse[target_str] = [
                        e for e in self._reverse[target_str]
                        if str(e.source) != path_str
                    ]
            del self._forward[path_str]

        # Remove reverse edges
        if path_str in self._reverse:
            for edge in self._reverse[path_str]:
                source_str = str(edge.source)
                if source_str in self._forward:
                    self._forward[source_str] = [
                        e for e in self._forward[source_str]
                        if str(e.target) != path_str
                    ]
            del self._reverse[path_str]

    def all_nodes(self) -> list[DocumentNode]:
        """Get all document nodes."""
        return list(self._nodes.values())

    # ==========================================================================
    # Edge Operations
    # ==========================================================================

    def add_edge(self, edge: RelationshipEdge, save: bool = True):
        """Add a relationship edge."""
        source_str = str(edge.source)
        target_str = str(edge.target)

        # Check for duplicate
        for existing in self._forward[source_str]:
            if (str(existing.target) == target_str and
                existing.edge_type == edge.edge_type and
                existing.context == edge.context):
                # Update existing edge
                existing.target_hash = edge.target_hash
                existing.recorded_at = edge.recorded_at
                existing.is_stale = edge.is_stale
                existing.stale_reason = edge.stale_reason
                if save:
                    self._save()
                return

        # Add new edge
        self._forward[source_str].append(edge)
        self._reverse[target_str].append(edge)

        if save:
            self._save()

    def remove_edges(self, source: Path, edge_type: Optional[EdgeType] = None):
        """Remove edges from a source, optionally filtered by type."""
        source_str = str(source)
        if source_str not in self._forward:
            return

        if edge_type is None:
            # Remove all edges
            for edge in self._forward[source_str]:
                target_str = str(edge.target)
                if target_str in self._reverse:
                    self._reverse[target_str] = [
                        e for e in self._reverse[target_str]
                        if str(e.source) != source_str
                    ]
            del self._forward[source_str]
        else:
            # Remove edges of specific type
            edges_to_keep = []
            for edge in self._forward[source_str]:
                if edge.edge_type == edge_type:
                    target_str = str(edge.target)
                    if target_str in self._reverse:
                        self._reverse[target_str] = [
                            e for e in self._reverse[target_str]
                            if not (str(e.source) == source_str and e.edge_type == edge_type)
                        ]
                else:
                    edges_to_keep.append(edge)

            if edges_to_keep:
                self._forward[source_str] = edges_to_keep
            else:
                del self._forward[source_str]

    def get_outgoing_edges(
        self,
        source: Path,
        edge_type: Optional[EdgeType] = None
    ) -> list[RelationshipEdge]:
        """Get all outgoing edges from a document."""
        edges = self._forward.get(str(source), [])
        if edge_type:
            return [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_incoming_edges(
        self,
        target: Path,
        edge_type: Optional[EdgeType] = None
    ) -> list[RelationshipEdge]:
        """Get all incoming edges to a document."""
        edges = self._reverse.get(str(target), [])
        if edge_type:
            return [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_targets(
        self,
        source: Path,
        edge_type: Optional[EdgeType] = None
    ) -> list[Path]:
        """Get all documents that source points to."""
        edges = self.get_outgoing_edges(source, edge_type)
        return [e.target for e in edges]

    def get_sources(
        self,
        target: Path,
        edge_type: Optional[EdgeType] = None
    ) -> list[Path]:
        """Get all documents that point to target."""
        edges = self.get_incoming_edges(target, edge_type)
        return [e.source for e in edges]

    # ==========================================================================
    # Graph Queries
    # ==========================================================================

    def get_impact(self, changed: Path, max_depth: int = 10) -> Set[Path]:
        """
        Get all documents affected by a change.

        Follows reverse edges to find dependents.
        """
        affected = set()
        to_check = {str(changed)}
        checked = set()

        for _ in range(max_depth):
            if not to_check:
                break

            current = to_check.pop()
            if current in checked:
                continue
            checked.add(current)

            for edge in self._reverse.get(current, []):
                source_str = str(edge.source)
                affected.add(edge.source)
                to_check.add(source_str)

        return affected

    def get_dependencies(self, doc: Path, max_depth: int = 10) -> Set[Path]:
        """
        Get all documents that doc depends on.

        Follows forward edges to find dependencies.
        """
        deps = set()
        to_check = {str(doc)}
        checked = set()

        for _ in range(max_depth):
            if not to_check:
                break

            current = to_check.pop()
            if current in checked:
                continue
            checked.add(current)

            for edge in self._forward.get(current, []):
                target_str = str(edge.target)
                deps.add(edge.target)
                to_check.add(target_str)

        return deps

    def get_orphans(self) -> list[Path]:
        """Get documents that are not referenced by any other document."""
        all_docs = set(self._nodes.keys())
        referenced = set()

        for edges in self._forward.values():
            for edge in edges:
                referenced.add(str(edge.target))

        orphans = all_docs - referenced
        return [Path(p) for p in orphans]

    def get_roots(self) -> list[Path]:
        """Get documents that don't depend on anything else."""
        all_sources = set(self._forward.keys())
        all_targets = set()
        for edges in self._forward.values():
            for edge in edges:
                all_targets.add(str(edge.target))

        roots = all_sources - all_targets
        return [Path(p) for p in roots]

    # ==========================================================================
    # Translation Helpers
    # ==========================================================================

    def get_translations(self, source: Path) -> list[RelationshipEdge]:
        """Get all translations of a source document."""
        return [
            edge for edge in self._reverse.get(str(source), [])
            if edge.edge_type == EdgeType.TRANSLATES
        ]

    def get_translation_source(self, translation: Path) -> Optional[Path]:
        """Get the source document for a translation."""
        edges = self.get_outgoing_edges(translation, EdgeType.TRANSLATES)
        if edges:
            return edges[0].target
        return None

    # ==========================================================================
    # Hierarchy Helpers
    # ==========================================================================

    def get_parent(self, doc: Path) -> Optional[Path]:
        """Get the parent document."""
        edges = self.get_outgoing_edges(doc, EdgeType.PARENT)
        if edges:
            return edges[0].target
        return None

    def get_children(self, doc: Path) -> list[Path]:
        """Get child documents."""
        return self.get_sources(doc, EdgeType.PARENT)

    def get_ancestors(self, doc: Path) -> list[Path]:
        """Get all ancestors (parent chain to root)."""
        ancestors = []
        current = doc
        while True:
            parent = self.get_parent(current)
            if parent is None:
                break
            ancestors.append(parent)
            current = parent
        return ancestors

    def get_descendants(self, doc: Path) -> list[Path]:
        """Get all descendants (children recursively)."""
        descendants = []
        to_check = list(self.get_children(doc))
        checked = set()

        while to_check:
            current = to_check.pop(0)
            if str(current) in checked:
                continue
            checked.add(str(current))
            descendants.append(current)
            to_check.extend(self.get_children(current))

        return descendants

    # ==========================================================================
    # Anchor Operations
    # ==========================================================================

    def set_anchor(
        self,
        anchor_id: str,
        value: any,
        value_type: str,
        defined_in: Path
    ):
        """Define or update an anchor."""
        self._anchors[anchor_id] = {
            "id": anchor_id,
            "value": value,
            "value_type": value_type,
            "defined_in": str(defined_in),
            "referenced_in": self._anchors.get(anchor_id, {}).get("referenced_in", []),
        }

    def add_anchor_reference(self, anchor_id: str, doc: Path):
        """Add a document that references an anchor."""
        if anchor_id in self._anchors:
            ref_list = self._anchors[anchor_id].get("referenced_in", [])
            doc_str = str(doc)
            if doc_str not in ref_list:
                ref_list.append(doc_str)
                self._anchors[anchor_id]["referenced_in"] = ref_list

    def get_anchor(self, anchor_id: str) -> Optional[dict]:
        """Get anchor data."""
        return self._anchors.get(anchor_id)

    def get_anchors_in_document(self, doc: Path) -> dict[str, dict]:
        """Get all anchors defined in a document."""
        doc_str = str(doc)
        return {
            aid: data for aid, data in self._anchors.items()
            if data.get("defined_in") == doc_str
        }

    # ==========================================================================
    # Staleness
    # ==========================================================================

    def get_stale_edges(self) -> list[RelationshipEdge]:
        """Get all edges marked as stale."""
        stale = []
        for edges in self._forward.values():
            for edge in edges:
                if edge.is_stale:
                    stale.append(edge)
        return stale

    def get_stale_documents(self) -> list[DocumentNode]:
        """Get all documents with stale relationships."""
        stale_sources = set()
        for edges in self._forward.values():
            for edge in edges:
                if edge.is_stale:
                    stale_sources.add(str(edge.source))

        return [
            self._nodes[path] for path in stale_sources
            if path in self._nodes
        ]

    def mark_edge_stale(self, edge: RelationshipEdge, reason: str):
        """Mark an edge as stale."""
        edge.is_stale = True
        edge.stale_reason = reason

        # Update node staleness
        source_str = str(edge.source)
        if source_str in self._nodes:
            node = self._nodes[source_str]
            node.is_stale = True
            if reason not in node.stale_reasons:
                node.stale_reasons.append(reason)

    def mark_edge_fresh(self, source: Path, target: Path, edge_type: EdgeType):
        """Mark an edge as fresh (not stale)."""
        source_str = str(source)
        for edge in self._forward.get(source_str, []):
            if str(edge.target) == str(target) and edge.edge_type == edge_type:
                edge.is_stale = False
                edge.stale_reason = None
                edge.recorded_at = datetime.now()
                break

        # Recompute node staleness
        self._recompute_node_staleness(source)

    def _recompute_node_staleness(self, doc: Path):
        """Recompute staleness for a node based on its edges."""
        doc_str = str(doc)
        if doc_str not in self._nodes:
            return

        node = self._nodes[doc_str]
        stale_reasons = []

        for edge in self._forward.get(doc_str, []):
            if edge.is_stale and edge.stale_reason:
                if edge.stale_reason not in stale_reasons:
                    stale_reasons.append(edge.stale_reason)

        node.is_stale = len(stale_reasons) > 0
        node.stale_reasons = stale_reasons

    # ==========================================================================
    # Migration
    # ==========================================================================

    def migrate_from_legacy(self):
        """
        Migrate data from legacy systems:
        - dependencies.json
        - hierarchy.json
        - Translation frontmatter
        """
        from .scanner import RelationshipScanner

        scanner = RelationshipScanner(self.project, self)
        scanner.full_scan()
        self._save()

    # ==========================================================================
    # Persistence
    # ==========================================================================

    def save(self):
        """Save registry to disk."""
        self._save()

    def refresh(self):
        """Refresh registry by re-scanning all documents."""
        from .scanner import RelationshipScanner

        # Clear current data
        self._nodes.clear()
        self._forward.clear()
        self._reverse.clear()
        self._anchors.clear()

        # Re-scan
        scanner = RelationshipScanner(self.project, self)
        scanner.full_scan()
        self._save()

    # ==========================================================================
    # Reporting
    # ==========================================================================

    def generate_report(self) -> dict:
        """Generate a comprehensive relationship report."""
        return {
            "version": self.VERSION,
            "summary": {
                "total_documents": len(self._nodes),
                "total_relationships": sum(len(e) for e in self._forward.values()),
                "stale_documents": len(self.get_stale_documents()),
                "orphan_documents": len(self.get_orphans()),
                "root_documents": len(self.get_roots()),
                "anchors": len(self._anchors),
            },
            "by_type": self._count_edge_types(),
            "stale_edges": [e.to_dict() for e in self.get_stale_edges()],
            "orphans": [str(p) for p in self.get_orphans()],
            "roots": [str(p) for p in self.get_roots()],
        }


__all__ = ["UnifiedRegistry"]
