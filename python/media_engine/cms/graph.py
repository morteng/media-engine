"""
Document graph generation for visualizing document relationships.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .document import Document, DocumentCollection


@dataclass
class GraphNode:
    """A node in the document graph."""

    doc_id: str
    title: str
    doc_type: str
    status: str
    path: str
    word_count: int = 0


@dataclass
class GraphEdge:
    """An edge in the document graph."""

    source: str
    target: str
    edge_type: str  # depends_on, references, sources


@dataclass
class DocumentGraph:
    """Graph representing document relationships."""

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    # Adjacency lists for traversal
    outgoing: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    incoming: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))


class DocumentGraphBuilder:
    """Builds a document graph from a collection."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.graph = DocumentGraph()

    def build(self, collection: DocumentCollection) -> DocumentGraph:
        """Build the document graph from a collection."""
        self.graph = DocumentGraph()

        # Create nodes
        for doc in collection.all_documents:
            doc_id = self._get_doc_id(doc)
            self.graph.nodes[doc_id] = GraphNode(
                doc_id=doc_id,
                title=doc.title,
                doc_type=doc.doc_type,
                status=doc.status,
                path=str(doc.path.relative_to(self.docs_dir)),
                word_count=doc.word_count(),
            )

        # Create edges from dependencies
        for doc in collection.all_documents:
            doc_id = self._get_doc_id(doc)

            # depends_on edges
            for dep in doc.depends_on:
                target_id = self._normalize_ref(dep)
                if target_id and target_id in self.graph.nodes:
                    edge = GraphEdge(source=doc_id, target=target_id, edge_type="depends_on")
                    self.graph.edges.append(edge)
                    self.graph.outgoing[doc_id].append(target_id)
                    self.graph.incoming[target_id].append(doc_id)

            # references edges (from frontmatter sources field for deliverables)
            sources = doc.metadata.get("sources", [])
            for source in sources:
                target_id = self._normalize_ref(source)
                if target_id and target_id in self.graph.nodes:
                    edge = GraphEdge(source=doc_id, target=target_id, edge_type="sources")
                    self.graph.edges.append(edge)
                    self.graph.outgoing[doc_id].append(target_id)
                    self.graph.incoming[target_id].append(doc_id)

        return self.graph

    def _get_doc_id(self, doc: Document) -> str:
        """Get a unique ID for a document."""
        rel_path = doc.path.relative_to(self.docs_dir)
        # Use path without extension as ID
        return str(rel_path.with_suffix(""))

    def _normalize_ref(self, ref: Any) -> Optional[str]:
        """Normalize a reference to match node IDs."""
        # Handle dict references (e.g., {"id": "...", "title": "..."})
        if isinstance(ref, dict):
            ref = ref.get("id") or ref.get("path") or ref.get("ref")
            if not ref:
                return None

        if not isinstance(ref, str):
            return None

        ref = ref.strip()

        # Handle docs/source/vision/product_vision -> source/vision/product_vision
        if ref.startswith("docs/"):
            ref = ref[5:]

        # If it's already a full path, use it
        if ref in self.graph.nodes:
            return ref

        # Try adding common prefixes for short references
        # e.g., vision/product_vision -> source/vision/product_vision
        prefixes = ["source/", "deliverables/", "proposal/"]
        for prefix in prefixes:
            full_ref = prefix + ref
            if full_ref in self.graph.nodes:
                return full_ref

        # Return original ref (may not match any node)
        return ref

    def get_dependents(self, doc_id: str) -> list[str]:
        """Get documents that depend on the given document."""
        return list(self.graph.incoming.get(doc_id, []))

    def get_dependencies(self, doc_id: str) -> list[str]:
        """Get documents that the given document depends on."""
        return list(self.graph.outgoing.get(doc_id, []))

    def get_orphans(self) -> list[str]:
        """Get documents with no incoming or outgoing edges."""
        orphans = []
        for doc_id in self.graph.nodes:
            if not self.graph.incoming.get(doc_id) and not self.graph.outgoing.get(doc_id):
                orphans.append(doc_id)
        return orphans

    def get_root_documents(self) -> list[str]:
        """Get documents with no dependencies (source of truth)."""
        roots = []
        for doc_id in self.graph.nodes:
            if not self.graph.outgoing.get(doc_id):
                roots.append(doc_id)
        return roots

    def get_leaf_documents(self) -> list[str]:
        """Get documents that nothing depends on (final outputs)."""
        leaves = []
        for doc_id in self.graph.nodes:
            if not self.graph.incoming.get(doc_id):
                leaves.append(doc_id)
        return leaves

    def to_dict(self) -> dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "nodes": [
                {
                    "id": n.doc_id,
                    "title": n.title,
                    "type": n.doc_type,
                    "status": n.status,
                    "path": n.path,
                    "word_count": n.word_count,
                }
                for n in self.graph.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "type": e.edge_type,
                }
                for e in self.graph.edges
            ],
            "stats": {
                "total_nodes": len(self.graph.nodes),
                "total_edges": len(self.graph.edges),
                "orphans": len(self.get_orphans()),
                "roots": len(self.get_root_documents()),
                "leaves": len(self.get_leaf_documents()),
            },
        }

    def save(self, output_path: Path) -> None:
        """Save graph to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def generate_mermaid(self) -> str:
        """Generate a Mermaid diagram of the graph."""
        lines = ["graph LR"]

        # Group nodes by type
        type_colors = {
            "source/vision": "fill:#d4f0ff",
            "source/roadmap": "fill:#d4ffd4",
            "source/technical": "fill:#ffd4d4",
            "source/business": "fill:#fff4d4",
            "deliverable/pilot": "fill:#e8d4ff",
            "deliverable/investor": "fill:#ffd4e8",
            "deliverable/demo": "fill:#d4ffe8",
            "chapter": "fill:#f0f0f0",
            "research": "fill:#ffe8d4",
        }

        # Add nodes with styling
        for node in self.graph.nodes.values():
            # Escape special characters in title
            safe_title = node.title.replace('"', "'")[:30]
            lines.append(f'    {self._safe_id(node.doc_id)}["{safe_title}"]')

        # Add edges
        edge_styles = {
            "depends_on": "-->",
            "sources": "-.->",
            "references": "..>",
        }

        for edge in self.graph.edges:
            style = edge_styles.get(edge.edge_type, "-->")
            lines.append(f"    {self._safe_id(edge.source)} {style} {self._safe_id(edge.target)}")

        # Add styling
        lines.append("")
        for doc_type, color in type_colors.items():
            nodes_of_type = [n.doc_id for n in self.graph.nodes.values() if n.doc_type == doc_type]
            if nodes_of_type:
                node_list = ",".join(self._safe_id(n) for n in nodes_of_type)
                lines.append(f"    style {node_list} {color}")

        return "\n".join(lines)

    def _safe_id(self, doc_id: str) -> str:
        """Convert doc_id to a safe Mermaid node ID."""
        return doc_id.replace("/", "_").replace("-", "_").replace(".", "_")

    def generate_stats_report(self) -> str:
        """Generate a text report of graph statistics."""
        lines = ["# Document Graph Report", ""]

        # Summary
        lines.append("## Summary")
        lines.append(f"- Total documents: {len(self.graph.nodes)}")
        lines.append(f"- Total relationships: {len(self.graph.edges)}")
        lines.append(f"- Orphan documents: {len(self.get_orphans())}")
        lines.append("")

        # By type
        lines.append("## Documents by Type")
        type_counts: dict[str, int] = defaultdict(int)
        for node in self.graph.nodes.values():
            type_counts[node.doc_type] += 1
        for doc_type, count in sorted(type_counts.items()):
            lines.append(f"- {doc_type}: {count}")
        lines.append("")

        # Root documents (sources of truth)
        roots = self.get_root_documents()
        if roots:
            lines.append("## Root Documents (Sources of Truth)")
            for doc_id in roots:
                node = self.graph.nodes[doc_id]
                lines.append(f"- {node.title} ({node.doc_type})")
            lines.append("")

        # Leaf documents (final outputs)
        leaves = [
            l
            for l in self.get_leaf_documents()
            if self.graph.nodes[l].doc_type.startswith("deliverable")
        ]
        if leaves:
            lines.append("## Deliverable Outputs")
            for doc_id in leaves:
                node = self.graph.nodes[doc_id]
                lines.append(f"- {node.title} ({node.doc_type})")
            lines.append("")

        # Orphans (disconnected)
        orphans = self.get_orphans()
        if orphans:
            lines.append("## Orphan Documents (No Relationships)")
            for doc_id in orphans:
                node = self.graph.nodes[doc_id]
                lines.append(f"- {node.title} ({node.doc_type})")
            lines.append("")

        return "\n".join(lines)
