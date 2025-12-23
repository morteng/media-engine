"""
Knowledge Graph for Media Engine

Builds and analyzes a semantic knowledge graph of documentation:
- Entity extraction from documents
- Concept relationship mapping
- Prerequisite chain validation
- Orphan concept detection
- Reading path generation
- Cross-reference density analysis

Uses NetworkX for graph operations.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""

    DOCUMENT = "document"
    CONCEPT = "concept"
    TERM = "term"
    CODE_ENTITY = "code_entity"  # Function, class, etc.
    EXAMPLE = "example"


class EdgeType(str, Enum):
    """Types of relationships in the knowledge graph."""

    DEFINES = "defines"  # Document defines concept
    REFERENCES = "references"  # Document references concept
    PREREQUISITE = "prerequisite"  # Concept requires another
    RELATED = "related"  # Concepts are related
    LINKS_TO = "links_to"  # Document links to document
    TRANSLATED_FROM = "translated_from"  # Translation relationship
    CONTAINS = "contains"  # Document contains example
    DEMONSTRATES = "demonstrates"  # Example demonstrates concept


@dataclass
class GraphNode:
    """A node in the knowledge graph."""

    node_id: str
    node_type: NodeType
    label: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""

    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }


@dataclass
class OrphanConcept:
    """A concept mentioned but never defined."""

    concept: str
    mentions: list[dict]  # [{doc, line, context}, ...]
    importance: float  # Based on mention frequency

    def to_dict(self) -> dict:
        return {
            "concept": self.concept,
            "mentions": self.mentions[:5],
            "mention_count": len(self.mentions),
            "importance": round(self.importance, 2),
        }


@dataclass
class PrerequisiteIssue:
    """A prerequisite chain issue."""

    document: Path
    missing_prereq: str
    explanation: str
    suggested_order: list[str]

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "missing_prereq": self.missing_prereq,
            "explanation": self.explanation,
            "suggested_order": self.suggested_order,
        }


@dataclass
class ReadingPath:
    """A recommended reading path through documentation."""

    path_id: str
    title: str
    documents: list[Path]
    concepts_covered: list[str]
    estimated_time_minutes: float

    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "title": self.title,
            "documents": [str(d) for d in self.documents],
            "concepts_covered": self.concepts_covered,
            "estimated_time_minutes": round(self.estimated_time_minutes, 1),
        }


@dataclass
class GraphMetrics:
    """Metrics about the knowledge graph."""

    total_nodes: int
    total_edges: int
    document_count: int
    concept_count: int
    avg_connections_per_doc: float
    orphan_concepts: int
    circular_dependencies: int
    clustering_coefficient: float
    connected_components: int

    def to_dict(self) -> dict:
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "document_count": self.document_count,
            "concept_count": self.concept_count,
            "avg_connections_per_doc": round(self.avg_connections_per_doc, 2),
            "orphan_concepts": self.orphan_concepts,
            "circular_dependencies": self.circular_dependencies,
            "clustering_coefficient": round(self.clustering_coefficient, 3),
            "connected_components": self.connected_components,
        }


@dataclass
class KnowledgeGraphReport:
    """Complete knowledge graph analysis report."""

    metrics: GraphMetrics
    orphan_concepts: list[OrphanConcept]
    prerequisite_issues: list[PrerequisiteIssue]
    reading_paths: list[ReadingPath]
    central_documents: list[dict]  # Most connected docs
    isolated_documents: list[Path]  # No connections

    def to_dict(self) -> dict:
        return {
            "metrics": self.metrics.to_dict(),
            "orphan_concepts": [o.to_dict() for o in self.orphan_concepts],
            "prerequisite_issues": [p.to_dict() for p in self.prerequisite_issues],
            "reading_paths": [r.to_dict() for r in self.reading_paths],
            "central_documents": self.central_documents,
            "isolated_documents": [str(d) for d in self.isolated_documents],
        }


class ConceptExtractor:
    """
    Extracts concepts from document content.

    Uses heuristics and patterns to identify:
    - Defined concepts (headers, bold terms)
    - Referenced concepts
    - Code entities
    """

    # Patterns for concept extraction
    DEFINITION_PATTERNS = [
        r"^#+\s+(.+)$",  # Headers
        r"\*\*([A-Z][a-zA-Z\s]+)\*\*",  # Bold capitalized
        r"^([A-Z][a-zA-Z\s]+):(?:\s|$)",  # Term definitions
        r"(?:is|are)\s+(?:a|an|the)\s+\*\*(.+?)\*\*",  # "is a **concept**"
    ]

    REFERENCE_PATTERNS = [
        r"`([A-Z][a-zA-Z]+)`",  # Code references
        r"\[([^\]]+)\]\([^)]+\)",  # Link text
        r"(?:the|a|an)\s+([A-Z][a-zA-Z]+)",  # Capitalized terms
    ]

    CODE_ENTITY_PATTERNS = [
        r"`([a-z_][a-z_0-9]+)\(`",  # Function calls
        r"`([A-Z][a-zA-Z]+)`",  # Class names
        r"from\s+\S+\s+import\s+(\w+)",  # Imports
    ]

    def __init__(self, min_term_length: int = 3):
        self.min_term_length = min_term_length
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns."""
        self.def_patterns = [re.compile(p, re.MULTILINE) for p in self.DEFINITION_PATTERNS]
        self.ref_patterns = [re.compile(p) for p in self.REFERENCE_PATTERNS]
        self.code_patterns = [re.compile(p) for p in self.CODE_ENTITY_PATTERNS]

    def extract_definitions(self, content: str) -> list[dict]:
        """Extract concept definitions from content."""
        definitions = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.def_patterns:
                for match in pattern.finditer(line):
                    term = match.group(1).strip()
                    if len(term) >= self.min_term_length:
                        definitions.append(
                            {
                                "term": term,
                                "line": i,
                                "type": "definition",
                            }
                        )

        return definitions

    def extract_references(self, content: str) -> list[dict]:
        """Extract concept references from content."""
        references = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.ref_patterns:
                for match in pattern.finditer(line):
                    term = match.group(1).strip()
                    if len(term) >= self.min_term_length:
                        references.append(
                            {
                                "term": term,
                                "line": i,
                                "type": "reference",
                            }
                        )

        return references

    def extract_code_entities(self, content: str) -> list[dict]:
        """Extract code entity references."""
        entities = []

        for pattern in self.code_patterns:
            for match in pattern.finditer(content):
                term = match.group(1).strip()
                if len(term) >= self.min_term_length:
                    entities.append(
                        {
                            "term": term,
                            "type": "code_entity",
                        }
                    )

        return entities


class KnowledgeGraph:
    """
    Knowledge graph for documentation.

    Builds a graph of documents, concepts, and their relationships.

    Usage:
        from media_engine.knowledge import KnowledgeGraph

        graph = KnowledgeGraph(project)
        graph.build()

        # Find orphan concepts
        orphans = graph.find_orphan_concepts()

        # Validate prerequisites
        issues = graph.validate_prerequisites()

        # Generate reading paths
        paths = graph.generate_reading_paths()

        # Get metrics
        metrics = graph.compute_metrics()

        # Full report
        report = graph.generate_report()
    """

    def __init__(self, project):
        """
        Initialize knowledge graph.

        Args:
            project: Media Engine project
        """
        if not HAS_NETWORKX:
            raise ImportError("networkx required: pip install networkx")

        self.project = project
        self.graph = nx.DiGraph()
        self.extractor = ConceptExtractor()

        # Track concepts and their definitions/references
        self._concept_definitions: dict[str, list[dict]] = defaultdict(list)
        self._concept_references: dict[str, list[dict]] = defaultdict(list)
        self._doc_metadata: dict[str, dict] = {}

    def build(self) -> None:
        """Build the knowledge graph from project content."""
        if not self.project.content_dir.exists():
            return

        # Process all documents
        for md_file in self.project.content_dir.rglob("*.md"):
            self._process_document(md_file)

        # Note: _build_concept_edges() removed - it created O(n²) "related" edges
        # per document which bloated the graph with meaningless connections.
        # Concepts in the same doc aren't necessarily related.

        # Build document link edges
        self._build_link_edges()

    def _process_document(self, doc_path: Path) -> None:
        """Process a single document."""
        try:
            content = doc_path.read_text(encoding="utf-8")
            rel_path = doc_path.relative_to(self.project.content_dir)
        except (OSError, UnicodeDecodeError, ValueError):
            return

        # Parse metadata
        metadata = self._parse_frontmatter(content)
        doc_id = f"doc:{rel_path}"

        # Remove keys that would conflict with explicit node attributes
        safe_metadata = {
            k: v for k, v in metadata.items() if k not in ("node_type", "label", "path", "language")
        }

        # Add document node
        self.graph.add_node(
            doc_id,
            node_type=NodeType.DOCUMENT.value,
            label=metadata.get("title", rel_path.stem),
            path=str(rel_path),
            language=metadata.get(
                "language", str(rel_path.parts[0]) if len(rel_path.parts) > 1 else "en"
            ),
            **safe_metadata,
        )
        self._doc_metadata[doc_id] = metadata

        # Extract definitions
        definitions = self.extractor.extract_definitions(content)
        for defn in definitions:
            concept_id = f"concept:{defn['term'].lower()}"

            # Add concept node if new
            if concept_id not in self.graph:
                self.graph.add_node(
                    concept_id,
                    node_type=NodeType.CONCEPT.value,
                    label=defn["term"],
                )

            # Add DEFINES edge
            self.graph.add_edge(
                doc_id,
                concept_id,
                edge_type=EdgeType.DEFINES.value,
                line=defn["line"],
            )

            self._concept_definitions[defn["term"].lower()].append(
                {
                    "doc": rel_path,
                    "line": defn["line"],
                }
            )

        # Extract references
        references = self.extractor.extract_references(content)
        for ref in references:
            concept_id = f"concept:{ref['term'].lower()}"

            # Add concept node if new
            if concept_id not in self.graph:
                self.graph.add_node(
                    concept_id,
                    node_type=NodeType.CONCEPT.value,
                    label=ref["term"],
                )

            # Add REFERENCES edge
            if not self.graph.has_edge(doc_id, concept_id):
                self.graph.add_edge(
                    doc_id,
                    concept_id,
                    edge_type=EdgeType.REFERENCES.value,
                )

            self._concept_references[ref["term"].lower()].append(
                {
                    "doc": rel_path,
                    "line": ref["line"],
                }
            )

        # Extract code entities
        code_entities = self.extractor.extract_code_entities(content)
        for entity in code_entities:
            entity_id = f"code:{entity['term']}"

            if entity_id not in self.graph:
                self.graph.add_node(
                    entity_id,
                    node_type=NodeType.CODE_ENTITY.value,
                    label=entity["term"],
                )

            if not self.graph.has_edge(doc_id, entity_id):
                self.graph.add_edge(
                    doc_id,
                    entity_id,
                    edge_type=EdgeType.REFERENCES.value,
                )

    def _build_concept_edges(self) -> None:
        """Build edges between related concepts."""
        # Concepts that appear together are related
        doc_concepts: dict[str, set[str]] = defaultdict(set)

        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") == NodeType.DOCUMENT.value:
                # Find concepts this doc connects to
                for _, target, edge_data in self.graph.out_edges(node, data=True):
                    target_data = self.graph.nodes[target]
                    if target_data.get("node_type") == NodeType.CONCEPT.value:
                        doc_concepts[node].add(target)

        # Add RELATED edges between concepts in same doc
        for doc_id, concepts in doc_concepts.items():
            concept_list = list(concepts)
            for i, c1 in enumerate(concept_list):
                for c2 in concept_list[i + 1 :]:
                    if not self.graph.has_edge(c1, c2):
                        self.graph.add_edge(
                            c1,
                            c2,
                            edge_type=EdgeType.RELATED.value,
                            weight=0.5,
                        )

    def _build_link_edges(self) -> None:
        """Build edges from document links."""
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for doc_id, data in self.graph.nodes(data=True):
            if data.get("node_type") != NodeType.DOCUMENT.value:
                continue

            doc_path = self.project.content_dir / data["path"]
            try:
                content = doc_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for match in link_pattern.finditer(content):
                link_url = match.group(2)

                # Skip external links
                if link_url.startswith(("http://", "https://", "mailto:")):
                    continue

                # Resolve internal link
                if link_url.startswith("/"):
                    target_path = link_url[1:]
                else:
                    target_path = str(Path(data["path"]).parent / link_url)

                # Normalize
                target_path = target_path.replace("\\", "/")
                if not target_path.endswith(".md"):
                    target_path += ".md"

                target_id = f"doc:{target_path}"
                if target_id in self.graph:
                    self.graph.add_edge(
                        doc_id,
                        target_id,
                        edge_type=EdgeType.LINKS_TO.value,
                    )

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}

        try:
            import yaml

            end = content.index("---", 3)
            return yaml.safe_load(content[3:end]) or {}
        except (ValueError, ImportError):
            return {}

    def find_orphan_concepts(self) -> list[OrphanConcept]:
        """
        Find concepts referenced but never defined.

        Returns:
            List of OrphanConcept instances
        """
        orphans = []

        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") != NodeType.CONCEPT.value:
                continue

            concept_name = data.get("label", "")
            concept_key = concept_name.lower()

            # Check if concept is defined
            has_definition = False
            for _, _, edge_data in self.graph.in_edges(node, data=True):
                if edge_data.get("edge_type") == EdgeType.DEFINES.value:
                    has_definition = True
                    break

            if not has_definition:
                # Get all references
                mentions = self._concept_references.get(concept_key, [])

                if mentions:
                    orphans.append(
                        OrphanConcept(
                            concept=concept_name,
                            mentions=mentions,
                            importance=len(mentions) / max(1, len(self._doc_metadata)),
                        )
                    )

        orphans.sort(key=lambda x: -x.importance)
        return orphans

    def validate_prerequisites(self) -> list[PrerequisiteIssue]:
        """
        Validate that prerequisite concepts are covered before use.

        Returns:
            List of PrerequisiteIssue instances
        """
        issues = []

        # Get document order by path
        doc_order = sorted(
            [
                (node, data)
                for node, data in self.graph.nodes(data=True)
                if data.get("node_type") == NodeType.DOCUMENT.value
            ],
            key=lambda x: x[1].get("path", ""),
        )

        # Track defined concepts as we go
        defined_concepts: set[str] = set()

        for doc_id, doc_data in doc_order:
            # Get concepts this doc references
            referenced = set()
            for _, target, edge_data in self.graph.out_edges(doc_id, data=True):
                if edge_data.get("edge_type") == EdgeType.REFERENCES.value:
                    target_data = self.graph.nodes[target]
                    if target_data.get("node_type") == NodeType.CONCEPT.value:
                        referenced.add(target_data.get("label", ""))

            # Get concepts this doc defines
            defines = set()
            for _, target, edge_data in self.graph.out_edges(doc_id, data=True):
                if edge_data.get("edge_type") == EdgeType.DEFINES.value:
                    target_data = self.graph.nodes[target]
                    if target_data.get("node_type") == NodeType.CONCEPT.value:
                        defines.add(target_data.get("label", ""))

            # Check for missing prerequisites
            missing = referenced - defined_concepts - defines
            for concept in missing:
                # Find where it's defined
                concept_key = concept.lower()
                definitions = self._concept_definitions.get(concept_key, [])

                if definitions:
                    suggested = [str(d["doc"]) for d in definitions]
                    issues.append(
                        PrerequisiteIssue(
                            document=Path(doc_data["path"]),
                            missing_prereq=concept,
                            explanation=f"'{concept}' is used before it's defined",
                            suggested_order=suggested + [doc_data["path"]],
                        )
                    )

            # Update defined concepts
            defined_concepts.update(defines)

        return issues

    def generate_reading_paths(
        self,
        max_paths: int = 5,
    ) -> list[ReadingPath]:
        """
        Generate recommended reading paths through documentation.

        Args:
            max_paths: Maximum number of paths to generate

        Returns:
            List of ReadingPath instances
        """
        paths = []

        # Get all document nodes
        doc_nodes = [
            (node, data)
            for node, data in self.graph.nodes(data=True)
            if data.get("node_type") == NodeType.DOCUMENT.value
        ]

        if not doc_nodes:
            return paths

        # Find entry points (documents with no incoming links)
        entry_points = []
        for doc_id, doc_data in doc_nodes:
            incoming_doc_edges = [
                (src, edge_data)
                for src, _, edge_data in self.graph.in_edges(doc_id, data=True)
                if edge_data.get("edge_type") == EdgeType.LINKS_TO.value
            ]
            if not incoming_doc_edges:
                entry_points.append((doc_id, doc_data))

        # Sort by path to prefer intro/readme
        entry_points.sort(
            key=lambda x: (
                0 if "intro" in x[1].get("path", "").lower() else 1,
                0 if "readme" in x[1].get("path", "").lower() else 1,
                0 if "01" in x[1].get("path", "") else 1,
                x[1].get("path", ""),
            )
        )

        # Generate paths from entry points
        for entry_id, entry_data in entry_points[:max_paths]:
            path_docs = []
            concepts_covered = set()
            visited = set()

            # BFS from entry point
            queue = [entry_id]
            while queue and len(path_docs) < 10:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)

                current_data = self.graph.nodes[current]
                if current_data.get("node_type") == NodeType.DOCUMENT.value:
                    path_docs.append(Path(current_data["path"]))

                    # Track concepts
                    for _, target, edge_data in self.graph.out_edges(current, data=True):
                        if edge_data.get("edge_type") in (
                            EdgeType.DEFINES.value,
                            EdgeType.REFERENCES.value,
                        ):
                            target_data = self.graph.nodes[target]
                            if target_data.get("node_type") == NodeType.CONCEPT.value:
                                concepts_covered.add(target_data.get("label", ""))

                    # Add linked documents to queue
                    for _, target, edge_data in self.graph.out_edges(current, data=True):
                        if edge_data.get("edge_type") == EdgeType.LINKS_TO.value:
                            if target not in visited:
                                queue.append(target)

            if path_docs:
                # Estimate reading time (200 words/minute)
                total_words = 0
                for doc_path in path_docs:
                    full_path = self.project.content_dir / doc_path
                    try:
                        content = full_path.read_text(encoding="utf-8")
                        total_words += len(content.split())
                    except (OSError, UnicodeDecodeError):
                        total_words += 500  # Estimate

                paths.append(
                    ReadingPath(
                        path_id=f"path_{len(paths) + 1}",
                        title=entry_data.get("title", entry_data.get("path", "Reading Path")),
                        documents=path_docs,
                        concepts_covered=list(concepts_covered)[:20],
                        estimated_time_minutes=total_words / 200,
                    )
                )

        return paths

    def compute_metrics(self) -> GraphMetrics:
        """
        Compute metrics about the knowledge graph.

        Returns:
            GraphMetrics instance
        """
        doc_nodes = [
            n
            for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == NodeType.DOCUMENT.value
        ]
        concept_nodes = [
            n
            for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == NodeType.CONCEPT.value
        ]

        # Average connections per document
        doc_connections = []
        for doc_id in doc_nodes:
            connections = self.graph.out_degree(doc_id) + self.graph.in_degree(doc_id)
            doc_connections.append(connections)
        avg_connections = sum(doc_connections) / max(1, len(doc_connections))

        # Orphan concepts
        orphans = self.find_orphan_concepts()

        # Circular dependencies (cycles in document links)
        # Note: simple_cycles is O(exponential), so we use a faster check
        try:
            # Check if graph has any cycles using efficient DAG check
            if nx.is_directed_acyclic_graph(self.graph):
                circular = 0
            else:
                # Count cycles with a limit to avoid exponential blowup
                cycle_count = 0
                cycle_limit = 100  # Stop counting after finding 100 cycles
                for cycle in nx.simple_cycles(self.graph):
                    if len(cycle) > 1:
                        cycle_count += 1
                    if cycle_count >= cycle_limit:
                        break
                circular = cycle_count
        except Exception:
            circular = 0

        # Clustering coefficient
        try:
            undirected = self.graph.to_undirected()
            clustering = nx.average_clustering(undirected)
        except Exception:
            clustering = 0.0

        # Connected components
        try:
            undirected = self.graph.to_undirected()
            components = nx.number_connected_components(undirected)
        except Exception:
            components = 1

        return GraphMetrics(
            total_nodes=self.graph.number_of_nodes(),
            total_edges=self.graph.number_of_edges(),
            document_count=len(doc_nodes),
            concept_count=len(concept_nodes),
            avg_connections_per_doc=avg_connections,
            orphan_concepts=len(orphans),
            circular_dependencies=circular,
            clustering_coefficient=clustering,
            connected_components=components,
        )

    def find_central_documents(self, top_n: int = 10) -> list[dict]:
        """
        Find most connected/important documents.

        Args:
            top_n: Number of documents to return

        Returns:
            List of document info dicts
        """
        doc_nodes = [
            (n, d)
            for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == NodeType.DOCUMENT.value
        ]

        # Calculate centrality (PageRank-style)
        try:
            centrality = nx.pagerank(self.graph)
        except Exception:
            centrality = {n: 1.0 for n, _ in doc_nodes}

        results = []
        for doc_id, doc_data in doc_nodes:
            results.append(
                {
                    "path": doc_data.get("path"),
                    "title": doc_data.get("title", doc_data.get("path")),
                    "centrality": centrality.get(doc_id, 0),
                    "outgoing_links": self.graph.out_degree(doc_id),
                    "incoming_links": self.graph.in_degree(doc_id),
                }
            )

        results.sort(key=lambda x: -x["centrality"])
        return results[:top_n]

    def find_isolated_documents(self) -> list[Path]:
        """
        Find documents with no connections.

        Returns:
            List of isolated document paths
        """
        isolated = []

        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") != NodeType.DOCUMENT.value:
                continue

            self.graph.in_degree(node)
            self.graph.out_degree(node)

            # Only count document-to-document edges
            doc_edges = 0
            for _, target, edge_data in self.graph.out_edges(node, data=True):
                if edge_data.get("edge_type") == EdgeType.LINKS_TO.value:
                    doc_edges += 1
            for src, _, edge_data in self.graph.in_edges(node, data=True):
                if edge_data.get("edge_type") == EdgeType.LINKS_TO.value:
                    doc_edges += 1

            if doc_edges == 0:
                isolated.append(Path(data["path"]))

        return isolated

    def generate_report(self) -> KnowledgeGraphReport:
        """
        Generate comprehensive knowledge graph report.

        Returns:
            KnowledgeGraphReport instance
        """
        self.build()

        return KnowledgeGraphReport(
            metrics=self.compute_metrics(),
            orphan_concepts=self.find_orphan_concepts()[:20],
            prerequisite_issues=self.validate_prerequisites()[:20],
            reading_paths=self.generate_reading_paths(),
            central_documents=self.find_central_documents(),
            isolated_documents=self.find_isolated_documents(),
        )

    def export_graphml(self, output_path: Path) -> None:
        """Export graph to GraphML format."""
        nx.write_graphml(self.graph, output_path)

    def export_json(self) -> dict:
        """Export graph to JSON format."""
        nodes = [
            {"id": n, **{k: v for k, v in d.items() if isinstance(v, (str, int, float, bool))}}
            for n, d in self.graph.nodes(data=True)
        ]
        edges = [{"source": u, "target": v, **d} for u, v, d in self.graph.edges(data=True)]
        return {"nodes": nodes, "edges": edges}


def build_knowledge_graph(project) -> KnowledgeGraphReport:
    """Convenience function to build and analyze knowledge graph."""
    graph = KnowledgeGraph(project)
    return graph.generate_report()


__all__ = [
    "KnowledgeGraph",
    "ConceptExtractor",
    "NodeType",
    "EdgeType",
    "GraphNode",
    "GraphEdge",
    "OrphanConcept",
    "PrerequisiteIssue",
    "ReadingPath",
    "GraphMetrics",
    "KnowledgeGraphReport",
    "build_knowledge_graph",
    "HAS_NETWORKX",
]
