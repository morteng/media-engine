"""
Cross-reference management for documents.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict

from .document import Document, DocumentCollection


@dataclass
class Reference:
    """A reference to another document or external source."""
    source_doc: str  # Path of document containing the reference
    target: str  # Target path, URL, or reference ID
    ref_type: str  # internal, external, citation, image
    line_number: Optional[int] = None
    anchor: Optional[str] = None  # For #section links
    text: Optional[str] = None  # Link text

    def __str__(self) -> str:
        return f"{self.source_doc} -> {self.target} ({self.ref_type})"


@dataclass
class ReferenceIssue:
    """An issue with a reference."""
    reference: Reference
    issue_type: str  # broken, orphan, circular, missing_anchor
    message: str

    def __str__(self) -> str:
        return f"[{self.issue_type}] {self.reference}: {self.message}"


class ReferenceManager:
    """Manages cross-references between documents."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.references: list[Reference] = []
        self.reverse_refs: dict[str, list[Reference]] = defaultdict(list)
        self._analyzed = False

    def analyze_collection(self, collection: DocumentCollection) -> None:
        """Analyze all documents for references."""
        self.references.clear()
        self.reverse_refs.clear()

        for doc in collection.all_documents:
            self._analyze_document(doc)

        self._analyzed = True

    def _analyze_document(self, doc: Document) -> None:
        """Extract all references from a document."""
        doc_path = str(doc.path.relative_to(self.docs_dir))

        # Internal markdown links
        for link in doc.find_internal_links():
            anchor = None
            target = link
            if '#' in link:
                target, anchor = link.split('#', 1)

            ref = Reference(
                source_doc=doc_path,
                target=target or doc_path,  # Same-doc anchor
                ref_type="internal",
                anchor=anchor,
            )
            self.references.append(ref)
            self.reverse_refs[target or doc_path].append(ref)

        # External links
        external_pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        for match in re.finditer(external_pattern, doc.content):
            ref = Reference(
                source_doc=doc_path,
                target=match.group(2),
                ref_type="external",
                text=match.group(1),
            )
            self.references.append(ref)

        # Citation references
        for cite_num in doc.find_citations():
            ref = Reference(
                source_doc=doc_path,
                target=f"citation:{cite_num}",
                ref_type="citation",
            )
            self.references.append(ref)

        # Image references
        for img_path in doc.find_images():
            ref = Reference(
                source_doc=doc_path,
                target=img_path,
                ref_type="image",
            )
            self.references.append(ref)

        # Document dependencies from frontmatter
        for dep in doc.depends_on:
            ref = Reference(
                source_doc=doc_path,
                target=dep,
                ref_type="dependency",
            )
            self.references.append(ref)
            self.reverse_refs[dep].append(ref)

    def validate(self, collection: DocumentCollection) -> list[ReferenceIssue]:
        """Validate all references and return issues."""
        if not self._analyzed:
            self.analyze_collection(collection)

        issues = []

        # Get all document paths
        doc_paths = {
            str(doc.path.relative_to(self.docs_dir))
            for doc in collection.all_documents
        }

        # Get all anchors per document
        doc_anchors: dict[str, set[str]] = {}
        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            anchors = set()
            for _, _, text in doc.get_headings():
                # Convert heading to anchor format
                anchor = self._heading_to_anchor(text)
                anchors.add(anchor)
            doc_anchors[path] = anchors

        for ref in self.references:
            # Check internal links
            if ref.ref_type == "internal":
                target = ref.target
                if target and not target.startswith('#'):
                    # Resolve relative path
                    source_dir = Path(ref.source_doc).parent
                    resolved = (source_dir / target).resolve()
                    try:
                        resolved_rel = str(resolved.relative_to(self.docs_dir.resolve()))
                    except ValueError:
                        resolved_rel = str(resolved)

                    # Check if target exists
                    full_path = self.docs_dir / target
                    if not full_path.exists() and resolved_rel not in doc_paths:
                        issues.append(ReferenceIssue(
                            reference=ref,
                            issue_type="broken",
                            message=f"Target document not found: {target}"
                        ))
                    elif ref.anchor:
                        # Check anchor exists in target
                        target_path = resolved_rel if resolved_rel in doc_paths else target
                        if target_path in doc_anchors:
                            if ref.anchor not in doc_anchors[target_path]:
                                issues.append(ReferenceIssue(
                                    reference=ref,
                                    issue_type="missing_anchor",
                                    message=f"Anchor #{ref.anchor} not found in {target}"
                                ))

            # Check images
            elif ref.ref_type == "image":
                if not ref.target.startswith(('http://', 'https://')):
                    source_dir = Path(ref.source_doc).parent
                    img_path = self.docs_dir / source_dir / ref.target
                    if not img_path.exists():
                        # Also check from docs root
                        img_path = self.docs_dir.parent / ref.target
                        if not img_path.exists():
                            issues.append(ReferenceIssue(
                                reference=ref,
                                issue_type="broken",
                                message=f"Image not found: {ref.target}"
                            ))

        return issues

    def _heading_to_anchor(self, heading: str) -> str:
        """Convert a heading to an anchor ID."""
        # Lowercase, replace spaces with hyphens, remove special chars
        anchor = heading.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        return anchor

    def get_incoming_refs(self, doc_path: str) -> list[Reference]:
        """Get all references pointing to a document."""
        return self.reverse_refs.get(doc_path, [])

    def get_outgoing_refs(self, doc_path: str) -> list[Reference]:
        """Get all references from a document."""
        return [r for r in self.references if r.source_doc == doc_path]

    def get_orphan_documents(self, collection: DocumentCollection) -> list[Document]:
        """Find documents with no incoming references."""
        if not self._analyzed:
            self.analyze_collection(collection)

        orphans = []
        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            # Skip index/readme files
            if doc.path.stem.lower() in ('index', 'readme', '00_introduction'):
                continue
            if not self.reverse_refs.get(path):
                orphans.append(doc)

        return orphans

    def get_dependency_order(self, collection: DocumentCollection) -> list[Document]:
        """Get documents in dependency order (dependencies first)."""
        if not self._analyzed:
            self.analyze_collection(collection)

        # Build dependency graph
        deps: dict[str, set[str]] = defaultdict(set)
        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            for dep in doc.depends_on:
                deps[path].add(dep)

        # Topological sort
        visited = set()
        result = []
        temp_marks = set()

        def visit(path: str) -> None:
            if path in temp_marks:
                return  # Circular dependency, skip
            if path in visited:
                return
            temp_marks.add(path)
            for dep in deps.get(path, []):
                visit(dep)
            temp_marks.remove(path)
            visited.add(path)
            result.append(path)

        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            visit(path)

        # Convert back to documents
        path_to_doc = {
            str(doc.path.relative_to(self.docs_dir)): doc
            for doc in collection.all_documents
        }

        return [path_to_doc[p] for p in result if p in path_to_doc]

    def find_circular_dependencies(self, collection: DocumentCollection) -> list[list[str]]:
        """Find circular dependency chains."""
        if not self._analyzed:
            self.analyze_collection(collection)

        # Build dependency graph
        deps: dict[str, set[str]] = defaultdict(set)
        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            for dep in doc.depends_on:
                deps[path].add(dep)

        # Find cycles using DFS
        cycles = []
        visited = set()

        def find_cycle(path: str, chain: list[str]) -> None:
            if path in chain:
                # Found cycle
                cycle_start = chain.index(path)
                cycles.append(chain[cycle_start:] + [path])
                return

            if path in visited:
                return

            chain.append(path)
            for dep in deps.get(path, []):
                find_cycle(dep, chain.copy())

            visited.add(path)

        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            if path not in visited:
                find_cycle(path, [])

        return cycles

    def generate_reference_map(self, collection: DocumentCollection) -> dict[str, Any]:
        """Generate a complete reference map for the collection."""
        if not self._analyzed:
            self.analyze_collection(collection)

        ref_map = {
            "documents": {},
            "external_links": [],
            "citations": {},
            "images": [],
        }

        for doc in collection.all_documents:
            path = str(doc.path.relative_to(self.docs_dir))
            ref_map["documents"][path] = {
                "title": doc.title,
                "outgoing": [
                    {"target": r.target, "type": r.ref_type}
                    for r in self.get_outgoing_refs(path)
                    if r.ref_type == "internal"
                ],
                "incoming": [
                    {"source": r.source_doc, "type": r.ref_type}
                    for r in self.get_incoming_refs(path)
                ],
                "dependencies": doc.depends_on,
            }

        # Collect external links
        external = [r for r in self.references if r.ref_type == "external"]
        ref_map["external_links"] = [
            {"url": r.target, "text": r.text, "source": r.source_doc}
            for r in external
        ]

        # Collect images
        images = [r for r in self.references if r.ref_type == "image"]
        ref_map["images"] = list(set(r.target for r in images))

        return ref_map

    def generate_backlinks_section(self, doc: Document) -> str:
        """Generate a backlinks section for a document."""
        path = str(doc.path.relative_to(self.docs_dir))
        incoming = self.get_incoming_refs(path)

        if not incoming:
            return ""

        lines = ["## Referenced By", ""]
        for ref in incoming:
            source_name = Path(ref.source_doc).stem
            lines.append(f"- [{source_name}]({ref.source_doc})")

        return "\n".join(lines)
