"""
Relationship Scanner for Media Engine

Scans documents to detect all types of relationships:
- Structural hierarchy (parent_document)
- Semantic derivation (derived_from)
- Translation (source_document)
- Content references (markdown links)
- Assets (images, files)
- Anchors (consistency constraints)
- Explicit dependencies (depends_on)
"""

import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..core import compute_document_hash, compute_file_hash
from .types import DocumentNode, EdgeType, RelationshipEdge

if TYPE_CHECKING:
    from .registry import UnifiedRegistry


class RelationshipScanner:
    """
    Scans documents and populates the unified registry.

    Detects relationships from:
    - Document frontmatter (explicit relationships)
    - Document content (implicit relationships)
    - File structure (language organization)
    """

    def __init__(self, project, registry: "UnifiedRegistry"):
        self.project = project
        self.registry = registry
        self.content_dir = project.content_dir

    def full_scan(self):
        """Scan all documents and populate the registry."""
        # Scan all languages
        for lang in self.project.languages:
            chapters = self.project.list_chapters(lang)
            for chapter_path in chapters:
                self.scan_document(chapter_path)

        # Also scan any documents in research, scripts, etc.
        for pattern in ["research/**/*.md", "scripts/**/*.yaml", "diagrams/**/*.yaml"]:
            for doc_path in self.content_dir.glob(pattern):
                if doc_path.is_file():
                    self.scan_document(doc_path)

    def scan_document(self, doc_path: Path):
        """
        Scan a single document for all relationships.

        Creates:
        - DocumentNode for the document
        - RelationshipEdge for each detected relationship
        """
        from ..cms.document import Document

        try:
            doc = Document.load(doc_path)
        except Exception as e:
            print(f"Warning: Could not load {doc_path}: {e}")
            return

        # Create or update document node
        node = self._create_node(doc_path, doc)
        self.registry.add_node(node)

        # Clear existing edges for this document (we'll re-detect them)
        self.registry.remove_edges(doc_path)

        # Detect all relationship types
        self._detect_parent(doc_path, doc)
        self._detect_derived_from(doc_path, doc)
        self._detect_translation(doc_path, doc)
        self._detect_depends_on(doc_path, doc)
        self._detect_references(doc_path, doc)
        self._detect_assets(doc_path, doc)
        self._detect_anchors(doc_path, doc)
        self._detect_anchor_refs(doc_path, doc)

    def _create_node(self, doc_path: Path, doc) -> DocumentNode:
        """Create a DocumentNode from a document."""
        metadata = doc.metadata

        # Determine language from path
        language = None
        try:
            rel_path = doc_path.relative_to(self.content_dir)
            parts = rel_path.parts
            if parts and parts[0] in self.project.languages:
                language = parts[0]
        except ValueError:
            pass

        # Compute content hash
        content_hash = compute_document_hash(doc_path)

        # Parse anchors from frontmatter
        anchors = {}
        for key, value in metadata.get("anchors", {}).items():
            if isinstance(value, dict):
                anchors[key] = value
            else:
                anchors[key] = {"value": value, "type": type(value).__name__}

        return DocumentNode(
            path=doc_path,
            title=metadata.get("title", doc_path.stem),
            language=language,
            doc_type=metadata.get("doc_type", "chapter"),
            lifecycle=metadata.get("lifecycle", "living"),
            status=metadata.get("status", "draft"),
            content_hash=content_hash,
            last_modified=datetime.now(),
            owner=metadata.get("owner"),
            approvers=metadata.get("approvers", []),
            anchors=anchors,
        )

    def _detect_parent(self, doc_path: Path, doc):
        """Detect parent_document relationship."""
        parent = doc.metadata.get("parent_document")
        if not parent:
            return

        target = self._resolve_path(doc_path, parent)
        if target and target.exists():
            edge = RelationshipEdge(
                source=doc_path,
                target=target,
                edge_type=EdgeType.PARENT,
                target_hash=compute_document_hash(target) if target.exists() else None,
                recorded_at=datetime.now(),
            )
            self.registry.add_edge(edge, save=False)

    def _detect_derived_from(self, doc_path: Path, doc):
        """Detect derived_from relationships."""
        derived_from = doc.metadata.get("derived_from", [])
        if isinstance(derived_from, dict):
            derived_from = [derived_from]

        for item in derived_from:
            if isinstance(item, str):
                # Simple path string
                path = item
                relationship = "implements"
                version = None
            else:
                # Dict with path, relationship, version
                path = item.get("path")
                relationship = item.get("relationship", "implements")
                version = item.get("version")

            if not path:
                continue

            target = self._resolve_path(doc_path, path)
            if target:
                edge_type = EdgeType.from_relationship_type(relationship)
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=edge_type,
                    version=version,
                    target_hash=compute_document_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_translation(self, doc_path: Path, doc):
        """Detect source_document (translation) relationship."""
        source_doc = doc.metadata.get("source_document")
        if not source_doc:
            return

        target = self._resolve_path(doc_path, source_doc)
        if target and target.exists():
            # Get stored hash from frontmatter
            stored_hash = doc.metadata.get("source_content_hash")
            current_hash = compute_document_hash(target)

            edge = RelationshipEdge(
                source=doc_path,
                target=target,
                edge_type=EdgeType.TRANSLATES,
                target_hash=stored_hash,
                recorded_at=datetime.now(),
                is_stale=stored_hash != current_hash if stored_hash else False,
                stale_reason="source_changed" if stored_hash and stored_hash != current_hash else None,
            )
            self.registry.add_edge(edge, save=False)

    def _detect_depends_on(self, doc_path: Path, doc):
        """Detect explicit depends_on relationships."""
        depends_on = doc.metadata.get("depends_on", [])
        if isinstance(depends_on, str):
            depends_on = [depends_on]

        for dep in depends_on:
            target = self._resolve_path(doc_path, dep)
            if target:
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.DEPENDS_ON,
                    target_hash=compute_document_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_references(self, doc_path: Path, doc):
        """Detect markdown link references."""
        content = doc.content

        # Pattern: [text](path.md) or [text](../path.md)
        link_pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"

        for match in re.finditer(link_pattern, content):
            link_text, link_path = match.groups()

            # Skip external URLs
            if link_path.startswith(("http://", "https://", "mailto:")):
                continue

            target = self._resolve_path(doc_path, link_path)
            if target:
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.REFERENCES,
                    context=f"Link: {link_text[:50]}",
                    target_hash=compute_document_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_assets(self, doc_path: Path, doc):
        """Detect image and asset references."""
        content = doc.content

        # Pattern: ![alt](path) or ![alt](path.png)
        img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

        for match in re.finditer(img_pattern, content):
            alt_text, img_path = match.groups()

            # Skip external URLs
            if img_path.startswith(("http://", "https://")):
                continue

            target = self._resolve_path(doc_path, img_path)
            if target:
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.USES_ASSET,
                    context=f"Image: {alt_text or img_path}",
                    target_hash=compute_file_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_anchors(self, doc_path: Path, doc):
        """Detect and register anchors defined in document."""
        anchors = doc.metadata.get("anchors", {})

        for anchor_id, value in anchors.items():
            if isinstance(value, dict):
                anchor_value = value.get("value", value)
                value_type = value.get("type", type(anchor_value).__name__)
            else:
                anchor_value = value
                value_type = type(value).__name__

            self.registry.set_anchor(anchor_id, anchor_value, value_type, doc_path)

    def _detect_anchor_refs(self, doc_path: Path, doc):
        """Detect anchor references and create edges."""
        anchor_refs = doc.metadata.get("anchor_refs", [])

        for ref in anchor_refs:
            if isinstance(ref, dict):
                source_path = ref.get("source")
                anchor_id = ref.get("anchor")
            else:
                continue

            if not source_path or not anchor_id:
                continue

            target = self._resolve_path(doc_path, source_path)
            if target:
                # Add anchor reference edge
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.ANCHOR_REF,
                    context=f"anchor:{anchor_id}",
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

                # Update anchor registry
                self.registry.add_anchor_reference(anchor_id, doc_path)

    def _resolve_path(self, base: Path, relative: str) -> Optional[Path]:
        """
        Resolve a relative path to an absolute path.

        Handles multiple path formats:
        - Relative to content dir: "en/chapters/01_intro.md"
        - Relative to document: "../other.md"
        - Relative to same directory: "sibling.md"
        - Path without extension: "chapters/01_intro" -> tries .md

        FIXED: No longer resolves from document's parent directory
               when path looks like it's from content root.
        """
        # Clean up the path
        relative = relative.strip()

        # Handle absolute paths from content root
        if relative.startswith("/"):
            target = self.content_dir / relative.lstrip("/")
            return self._validate_path(target)

        # Check if path starts with a language code (content-relative)
        # or known content directory name (chapters/, research/, etc.)
        known_prefixes = set(self.project.languages) | {
            "chapters", "research", "scripts", "diagrams", "slides", "data", "assets"
        }

        first_part = relative.split("/")[0] if "/" in relative else None

        if first_part and first_part in known_prefixes:
            # Path is relative to content directory
            target = self.content_dir / relative
            return self._validate_path(target)

        # Path is relative to document location
        target = (base.parent / relative).resolve()
        return self._validate_path(target)

    def _validate_path(self, target: Path) -> Optional[Path]:
        """Validate and potentially fix a path."""
        # Check if within project
        try:
            target.relative_to(self.project.root)
        except ValueError:
            return None

        # If exists, return it
        if target.exists():
            return target

        # Try adding .md extension
        if not target.suffix:
            md_target = target.with_suffix(".md")
            if md_target.exists():
                return md_target

        # Return the target even if it doesn't exist (broken reference)
        # The edge will have no hash, signaling a missing target
        return target

    def scan_incremental(self, changed_paths: list[Path]):
        """
        Incrementally update registry for changed documents.

        More efficient than full_scan when only a few documents changed.
        """
        for doc_path in changed_paths:
            if doc_path.exists():
                self.scan_document(doc_path)
            else:
                # Document was deleted
                self.registry.remove_node(doc_path)


__all__ = ["RelationshipScanner"]
