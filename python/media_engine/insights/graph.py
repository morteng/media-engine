"""
Knowledge Graph Visualization

Creates an interactive visual knowledge graph showing how documents connect
to each other through links, dependencies, and topic relationships.

Graph elements:
- Nodes: Documents (size by word count, color by status)
- Edges: Dependencies, links, similarity

Export formats:
- DOT (Graphviz)
- JSON (D3.js compatible)
- Cytoscape JSON
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from ..core.project import Project


@dataclass
class GraphNode:
    """A node in the knowledge graph."""

    id: str
    document: Path
    title: str
    node_type: str  # "chapter", "script", "demo", etc.
    status: str  # "draft", "final", "published"
    word_count: int
    connections: int = 0
    language: str = "en"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "document": str(self.document),
            "title": self.title,
            "type": self.node_type,
            "status": self.status,
            "word_count": self.word_count,
            "connections": self.connections,
            "language": self.language,
        }


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""

    source: str
    target: str
    edge_type: str  # "depends", "links", "similar", "translation"
    weight: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "weight": self.weight,
        }


@dataclass
class KnowledgeGraph:
    """
    Builds and analyzes the documentation knowledge graph.

    Usage:
        graph = KnowledgeGraph(project)
        nodes, edges = graph.build_graph()

        # Find hub documents
        hubs = graph.find_hubs()

        # Find orphan documents
        orphans = graph.find_orphans()

        # Export to DOT format
        dot = graph.export_dot()
    """

    project: Project
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def build_graph(self) -> tuple[list[GraphNode], list[GraphEdge]]:
        """
        Build the complete knowledge graph.

        Returns:
            Tuple of (nodes, edges)
        """
        self.nodes = {}
        self.edges = []

        if not self.project.content_dir.exists():
            return [], []

        # Build nodes
        for md_file in self.project.content_dir.rglob("*.md"):
            node = self._create_node(md_file)
            if node:
                self.nodes[node.id] = node

        # Build edges
        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                node_id = str(rel_path)

                if node_id not in self.nodes:
                    continue

                content = md_file.read_text(encoding="utf-8")
                frontmatter, body = self._parse_frontmatter(content)

                # Dependencies from frontmatter
                depends_on = frontmatter.get("depends_on", [])
                if isinstance(depends_on, str):
                    depends_on = [depends_on]

                for dep in depends_on:
                    target_id = self._normalize_path(dep)
                    if target_id in self.nodes:
                        self.edges.append(
                            GraphEdge(source=node_id, target=target_id, edge_type="depends")
                        )

                # Translation links
                source_doc = frontmatter.get("source_document")
                if source_doc:
                    target_id = self._normalize_path(source_doc)
                    if target_id in self.nodes:
                        self.edges.append(
                            GraphEdge(source=node_id, target=target_id, edge_type="translation")
                        )

                # Internal links
                link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
                for text, url in link_pattern.findall(body):
                    if not url.startswith(("http://", "https://", "mailto:", "#")):
                        target_id = self._normalize_path(url)
                        if target_id in self.nodes:
                            self.edges.append(
                                GraphEdge(source=node_id, target=target_id, edge_type="links")
                            )

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Update connection counts
        for edge in self.edges:
            if edge.source in self.nodes:
                self.nodes[edge.source].connections += 1
            if edge.target in self.nodes:
                self.nodes[edge.target].connections += 1

        return list(self.nodes.values()), self.edges

    def find_hubs(self, threshold: int = 5) -> list[GraphNode]:
        """
        Find hub documents (highly connected).

        Args:
            threshold: Minimum connections to be considered a hub

        Returns:
            List of hub nodes sorted by connection count
        """
        if not self.nodes:
            self.build_graph()

        hubs = [node for node in self.nodes.values() if node.connections >= threshold]
        hubs.sort(key=lambda n: -n.connections)

        return hubs

    def find_orphans(self) -> list[GraphNode]:
        """
        Find orphan documents (no connections).

        Returns:
            List of orphan nodes
        """
        if not self.nodes:
            self.build_graph()

        return [node for node in self.nodes.values() if node.connections == 0]

    def find_clusters(self) -> list[list[GraphNode]]:
        """
        Find document clusters (connected components).

        Returns:
            List of clusters, each cluster is a list of nodes
        """
        if not self.nodes:
            self.build_graph()

        # Build adjacency list
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)

        # Find connected components
        visited: set[str] = set()
        clusters: list[list[GraphNode]] = []

        def dfs(node_id: str, cluster: list[GraphNode]):
            if node_id in visited:
                return
            visited.add(node_id)
            if node_id in self.nodes:
                cluster.append(self.nodes[node_id])
            for neighbor in adjacency[node_id]:
                dfs(neighbor, cluster)

        for node_id in self.nodes:
            if node_id not in visited:
                cluster: list[GraphNode] = []
                dfs(node_id, cluster)
                if cluster:
                    clusters.append(cluster)

        # Sort clusters by size
        clusters.sort(key=lambda c: -len(c))

        return clusters

    def get_document_connections(self, doc_path: Path) -> dict:
        """
        Get all connections for a specific document.

        Args:
            doc_path: Path to the document

        Returns:
            Dict with incoming and outgoing connections
        """
        if not self.nodes:
            self.build_graph()

        try:
            if not doc_path.is_absolute():
                doc_id = str(doc_path)
            else:
                doc_id = str(doc_path.relative_to(self.project.content_dir))
        except ValueError:
            doc_id = str(doc_path)

        incoming: list[GraphEdge] = []
        outgoing: list[GraphEdge] = []

        for edge in self.edges:
            if edge.source == doc_id:
                outgoing.append(edge)
            elif edge.target == doc_id:
                incoming.append(edge)

        return {
            "document": doc_id,
            "incoming": [e.to_dict() for e in incoming],
            "outgoing": [e.to_dict() for e in outgoing],
            "total_connections": len(incoming) + len(outgoing),
        }

    def export_dot(self) -> str:
        """
        Export graph in Graphviz DOT format.

        Returns:
            DOT format string
        """
        if not self.nodes:
            self.build_graph()

        lines = ["digraph knowledge {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        lines.append("")

        # Status colors
        status_colors = {
            "draft": "#ffcccc",
            "in_review": "#ffffcc",
            "final": "#ccffcc",
            "published": "#ccccff",
        }

        # Nodes
        for node in self.nodes.values():
            color = status_colors.get(node.status, "#ffffff")
            label = node.title.replace('"', '\\"')[:30]
            lines.append(f'  "{node.id}" [label="{label}", fillcolor="{color}", style=filled];')

        lines.append("")

        # Edges
        edge_styles = {
            "depends": "solid",
            "links": "dashed",
            "similar": "dotted",
            "translation": "bold",
        }

        for edge in self.edges:
            style = edge_styles.get(edge.edge_type, "solid")
            lines.append(f'  "{edge.source}" -> "{edge.target}" [style={style}];')

        lines.append("}")

        return "\n".join(lines)

    def export_json(self) -> dict:
        """
        Export graph in D3.js compatible JSON format.

        Returns:
            Dict with nodes and links arrays
        """
        if not self.nodes:
            self.build_graph()

        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "links": [edge.to_dict() for edge in self.edges],
        }

    def export_cytoscape(self) -> dict:
        """
        Export graph in Cytoscape.js format.

        Returns:
            Cytoscape-compatible elements dict
        """
        if not self.nodes:
            self.build_graph()

        elements = []

        for node in self.nodes.values():
            elements.append(
                {
                    "data": {
                        "id": node.id,
                        "label": node.title,
                        "type": node.node_type,
                        "status": node.status,
                        "word_count": node.word_count,
                    }
                }
            )

        for edge in self.edges:
            elements.append(
                {
                    "data": {
                        "source": edge.source,
                        "target": edge.target,
                        "type": edge.edge_type,
                    }
                }
            )

        return {"elements": elements}

    def _create_node(self, path: Path) -> Optional[GraphNode]:
        """Create a graph node from a document."""
        try:
            rel_path = path.relative_to(self.project.content_dir)
            content = path.read_text(encoding="utf-8")
            frontmatter, body = self._parse_frontmatter(content)

            # Determine type from path
            parts = rel_path.parts
            if len(parts) >= 2:
                node_type = parts[1]  # e.g., "chapters", "scripts"
                language = parts[0]
            else:
                node_type = "document"
                language = "en"

            return GraphNode(
                id=str(rel_path),
                document=rel_path,
                title=frontmatter.get("title", path.stem),
                node_type=node_type,
                status=frontmatter.get("status", "draft"),
                word_count=len(body.split()),
                language=language,
            )

        except (OSError, UnicodeDecodeError, ValueError):
            return None

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}, content

        try:
            end_idx = content.index("---", 3)
            frontmatter = yaml.safe_load(content[3:end_idx]) or {}
            body = content[end_idx + 3 :].strip()
            return frontmatter, body
        except (ValueError, yaml.YAMLError):
            return {}, content

    def _normalize_path(self, path: str) -> str:
        """Normalize a path reference to a node ID."""
        # Remove leading ./
        path = path.lstrip("./")
        # Remove anchor
        if "#" in path:
            path = path.split("#")[0]
        # Add .md if missing
        if not path.endswith(".md") and "." not in Path(path).suffix:
            path = path + ".md"
        return path


def build_knowledge_graph(project: Project) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Convenience function to build a knowledge graph."""
    graph = KnowledgeGraph(project)
    return graph.build_graph()
