"""
Hierarchy Registry for Media Engine

Persistent storage and management of document hierarchy relationships.
Stores hierarchy data in .media-engine/hierarchy.json.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .types import (
    ConsistencyAnchor,
    DerivationSource,
    DocumentType,
    HierarchyNode,
    Lifecycle,
    RelationshipType,
)

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class HierarchyRegistry:
    """
    Manages document hierarchy as persistent registry.

    Provides:
    - Storage of hierarchy nodes with parent-child relationships
    - Derivation graph tracking
    - Consistency anchors
    - JSON persistence to .media-engine/hierarchy.json
    """

    VERSION = "1.0.0"

    def __init__(self, project: "Project"):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.data_path = self.data_dir / "hierarchy.json"

        # Hierarchy structure
        self._nodes: dict[str, HierarchyNode] = {}
        self._roots: set[str] = set()

        # Lookup caches
        self._children_cache: dict[str, list[str]] = {}
        self._parent_cache: dict[str, Optional[str]] = {}

        # Consistency anchors
        self._anchors: dict[str, ConsistencyAnchor] = {}

        # Load existing data
        self._load()

    def _load(self) -> None:
        """Load hierarchy data from disk."""
        if not self.data_path.exists():
            return

        try:
            with open(self.data_path) as f:
                data = json.load(f)

            # Load nodes
            for path_str, node_data in data.get("nodes", {}).items():
                node = HierarchyNode.from_dict(node_data)
                self._nodes[path_str] = node
                self._parent_cache[path_str] = str(node.parent) if node.parent else None

            # Build root set and children cache
            self._rebuild_caches()

            # Load anchors
            for anchor_id, anchor_data in data.get("anchors", {}).items():
                self._anchors[anchor_id] = ConsistencyAnchor.from_dict(anchor_data)

            node_count = len(self._nodes)
            anchor_count = len(self._anchors)
            logger.debug(f"Loaded hierarchy: {node_count} nodes, {anchor_count} anchors")

        except Exception as e:
            logger.error(f"Failed to load hierarchy registry: {e}")

    def _save(self) -> None:
        """Save hierarchy data to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "version": self.VERSION,
            "generated_at": datetime.now().isoformat(),
            "nodes": {path: node.to_dict() for path, node in self._nodes.items()},
            "anchors": {aid: anchor.to_dict() for aid, anchor in self._anchors.items()},
            "summary": {
                "total_nodes": len(self._nodes),
                "root_count": len(self._roots),
                "anchor_count": len(self._anchors),
            },
        }

        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved hierarchy: {len(self._nodes)} nodes")

    def _rebuild_caches(self) -> None:
        """Rebuild lookup caches from node data."""
        self._roots.clear()
        self._children_cache.clear()

        for path_str, node in self._nodes.items():
            # Track roots (nodes without parents)
            if node.parent is None:
                self._roots.add(path_str)

            # Build children cache
            if node.parent:
                parent_str = str(node.parent)
                if parent_str not in self._children_cache:
                    self._children_cache[parent_str] = []
                self._children_cache[parent_str].append(path_str)

        # Sort children by sequence_order
        for parent_str in self._children_cache:
            self._children_cache[parent_str].sort(
                key=lambda p: self._nodes[p].sequence_order if p in self._nodes else 0
            )

    # === Node Management ===

    def get_node(self, path: Path) -> Optional[HierarchyNode]:
        """Get hierarchy node for a document."""
        return self._nodes.get(str(path))

    def set_node(self, node: HierarchyNode) -> None:
        """Add or update a hierarchy node."""
        path_str = str(node.path)

        # Update parent cache
        old_parent = self._parent_cache.get(path_str)
        new_parent = str(node.parent) if node.parent else None

        # Remove from old parent's children
        if old_parent and old_parent != new_parent:
            if old_parent in self._children_cache:
                self._children_cache[old_parent] = [
                    c for c in self._children_cache[old_parent] if c != path_str
                ]

        # Add to new parent's children
        if new_parent:
            if new_parent not in self._children_cache:
                self._children_cache[new_parent] = []
            if path_str not in self._children_cache[new_parent]:
                self._children_cache[new_parent].append(path_str)
                # Re-sort by sequence_order
                self._children_cache[new_parent].sort(
                    key=lambda p: self._nodes.get(p, node).sequence_order
                )

        # Update root set
        if new_parent:
            self._roots.discard(path_str)
        else:
            self._roots.add(path_str)

        # Store node
        self._nodes[path_str] = node
        self._parent_cache[path_str] = new_parent

        self._save()

    def remove_node(self, path: Path) -> bool:
        """Remove a hierarchy node."""
        path_str = str(path)
        if path_str not in self._nodes:
            return False

        node = self._nodes[path_str]

        # Remove from parent's children
        if node.parent:
            parent_str = str(node.parent)
            if parent_str in self._children_cache:
                self._children_cache[parent_str] = [
                    c for c in self._children_cache[parent_str] if c != path_str
                ]

        # Remove from caches
        self._roots.discard(path_str)
        self._parent_cache.pop(path_str, None)
        self._children_cache.pop(path_str, None)
        del self._nodes[path_str]

        self._save()
        return True

    # === Hierarchy Queries ===

    def get_roots(self) -> list[Path]:
        """Get all root documents (no parent)."""
        return [Path(p) for p in sorted(self._roots)]

    def get_parent(self, path: Path) -> Optional[Path]:
        """Get immediate parent of a document."""
        parent_str = self._parent_cache.get(str(path))
        return Path(parent_str) if parent_str else None

    def get_children(self, path: Path) -> list[Path]:
        """Get immediate children of a document, sorted by sequence_order."""
        children = self._children_cache.get(str(path), [])
        return [Path(c) for c in children]

    def get_ancestors(self, path: Path) -> list[Path]:
        """Get all ancestors from document to root (inclusive of root)."""
        ancestors = []
        current = self.get_parent(path)
        seen = set()

        while current and str(current) not in seen:
            seen.add(str(current))
            ancestors.append(current)
            current = self.get_parent(current)

        return ancestors

    def get_descendants(self, path: Path) -> list[Path]:
        """Get all descendants (children, grandchildren, etc.)."""
        descendants = []
        to_visit = list(self.get_children(path))

        while to_visit:
            current = to_visit.pop(0)
            descendants.append(current)
            to_visit.extend(self.get_children(current))

        return descendants

    def get_siblings(self, path: Path) -> list[Path]:
        """Get siblings (same parent), excluding self."""
        parent = self.get_parent(path)
        if parent:
            children = self.get_children(parent)
            return [c for c in children if c != path]
        else:
            # Root-level siblings
            return [Path(r) for r in sorted(self._roots) if r != str(path)]

    def get_level(self, path: Path) -> int:
        """Get depth level (0 = root)."""
        return len(self.get_ancestors(path))

    # === Derivation Graph ===

    def get_derivation_sources(self, path: Path) -> list[DerivationSource]:
        """Get documents this one derives from."""
        node = self.get_node(path)
        return node.derived_from if node else []

    def get_derivatives(self, path: Path) -> list[Path]:
        """Get documents that derive from this one."""
        derivatives = []
        path_str = str(path)

        for node_path, node in self._nodes.items():
            for source in node.derived_from:
                if str(source.path) == path_str:
                    derivatives.append(Path(node_path))
                    break

        return derivatives

    def add_derivation(
        self,
        derived_path: Path,
        source_path: Path,
        version: Optional[str] = None,
        relationship: RelationshipType = RelationshipType.IMPLEMENTS,
    ) -> None:
        """Add a derivation relationship."""
        node = self.get_node(derived_path)
        if not node:
            node = HierarchyNode(path=derived_path)

        # Check if already exists
        for source in node.derived_from:
            if str(source.path) == str(source_path):
                # Update existing
                source.version = version
                source.relationship = relationship
                self.set_node(node)
                return

        # Add new
        node.derived_from.append(
            DerivationSource(
                path=source_path,
                version=version,
                relationship=relationship,
            )
        )
        self.set_node(node)

    # === Consistency Anchors ===

    def get_anchor(self, anchor_id: str) -> Optional[ConsistencyAnchor]:
        """Get a consistency anchor by ID."""
        return self._anchors.get(anchor_id)

    def set_anchor(self, anchor: ConsistencyAnchor) -> None:
        """Add or update a consistency anchor."""
        self._anchors[anchor.id] = anchor
        self._save()

    def get_all_anchors(self) -> dict[str, ConsistencyAnchor]:
        """Get all consistency anchors."""
        return self._anchors.copy()

    # === Bulk Operations ===

    def refresh(self) -> None:
        """
        Rebuild hierarchy by scanning all documents.

        Reads frontmatter from all documents to extract:
        - parent_document
        - sequence_order
        - doc_type
        - lifecycle
        - derived_from
        - anchors
        """

        self._nodes.clear()
        self._roots.clear()
        self._children_cache.clear()
        self._parent_cache.clear()
        self._anchors.clear()

        # Scan all documents
        for lang in self.project.languages:
            chapters = self.project.list_chapters(lang)
            for chapter_path in chapters:
                self._scan_document(chapter_path)

        # Rebuild caches
        self._rebuild_caches()
        self._save()

        logger.info(f"Refreshed hierarchy: {len(self._nodes)} nodes, {len(self._roots)} roots")

    def _resolve_relative_path(self, referencing_doc: Path, rel_path: Path) -> Path:
        """
        Resolve a relative path to an absolute path.

        Relative paths in derived_from and parent_document can be:
        - Relative to content dir: "chapters/01_introduction.md"
        - Language-prefixed: "en/chapters/01_introduction.md"
        """
        rel_str = str(rel_path)

        # Find language directory (parent of chapters/)
        lang_dir = referencing_doc.parent
        while lang_dir.name not in ("en", "no", "content") and lang_dir != lang_dir.parent:
            lang_dir = lang_dir.parent

        if lang_dir.name == "content":
            # Couldn't find language dir, try relative to content
            resolved = lang_dir / rel_str
            if resolved.exists():
                return resolved
        elif lang_dir.name in ("en", "no"):
            # Found language dir, try resolving from there
            resolved = lang_dir / rel_str
            if resolved.exists():
                return resolved
            # Also try content dir with language prefix
            content_dir = lang_dir.parent
            resolved = content_dir / rel_str
            if resolved.exists():
                return resolved

        # Fallback: return as-is (will fail validation later)
        return rel_path

    def _scan_document(self, doc_path: Path) -> None:
        """Scan a document for hierarchy metadata."""
        from ..cms.document import Document

        try:
            doc = Document.load(doc_path)
        except Exception as e:
            logger.warning(f"Could not load document {doc_path}: {e}")
            return

        metadata = doc.metadata
        path_str = str(doc_path)

        # Extract hierarchy fields
        parent_doc_raw = metadata.get("parent_document")
        parent_doc = None
        if parent_doc_raw:
            # Resolve relative parent path to absolute
            parent_doc = self._resolve_relative_path(doc_path, Path(parent_doc_raw))
        sequence_order = metadata.get("sequence_order", 0)
        hierarchy_level = metadata.get("hierarchy_level", 0)
        doc_type_str = metadata.get("doc_type", "chapter")
        lifecycle_str = metadata.get("lifecycle", "living")

        # Parse doc_type
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            doc_type = DocumentType.CHAPTER

        # Parse lifecycle
        try:
            lifecycle = Lifecycle(lifecycle_str)
        except ValueError:
            lifecycle = Lifecycle.LIVING

        # Parse derived_from (resolve relative paths to absolute)
        derived_from = []
        derived_from_data = metadata.get("derived_from", [])
        if isinstance(derived_from_data, list):
            for item in derived_from_data:
                if isinstance(item, dict):
                    source = DerivationSource.from_dict(item)
                    # Resolve relative path to absolute
                    source.path = self._resolve_relative_path(doc_path, source.path)
                    derived_from.append(source)
                elif isinstance(item, str):
                    resolved = self._resolve_relative_path(doc_path, Path(item))
                    derived_from.append(DerivationSource(path=resolved))

        # Extract anchors from frontmatter
        anchors_data = metadata.get("anchors", {})
        node_anchors: dict[str, Any] = {}
        if isinstance(anchors_data, dict):
            for anchor_id, anchor_info in anchors_data.items():
                # Store in node.anchors for AnchorRegistry to use
                node_anchors[anchor_id] = anchor_info

                # Also store in registry-level anchors
                if isinstance(anchor_info, dict):
                    anchor = ConsistencyAnchor(
                        id=anchor_id,
                        value=anchor_info.get("value"),
                        value_type=anchor_info.get("type", "string"),
                        defined_in=doc_path,
                    )
                else:
                    # Simple value format
                    anchor = ConsistencyAnchor(
                        id=anchor_id,
                        value=anchor_info,
                        value_type=type(anchor_info).__name__,
                        defined_in=doc_path,
                    )
                self._anchors[anchor_id] = anchor

        # Extract raw_metadata for anchor_refs and other fields
        raw_metadata: dict[str, Any] = {}
        if metadata.get("anchor_refs"):
            raw_metadata["anchor_refs"] = metadata["anchor_refs"]

        # Create node
        node = HierarchyNode(
            path=doc_path,
            title=doc.title or doc_path.stem,
            parent=parent_doc,  # Already a Path or None
            level=hierarchy_level,
            sequence_order=sequence_order,
            doc_type=doc_type,
            lifecycle=lifecycle,
            derived_from=derived_from,
            owner=metadata.get("owner"),
            approvers=metadata.get("approvers", []),
            anchors=node_anchors,
            raw_metadata=raw_metadata,
        )

        self._nodes[path_str] = node
        self._parent_cache[path_str] = str(node.parent) if node.parent else None

    def get_all_nodes(self) -> list[HierarchyNode]:
        """Get all hierarchy nodes."""
        return list(self._nodes.values())

    def generate_report(self) -> dict[str, Any]:
        """Generate a hierarchy report."""
        by_type = {}
        by_lifecycle = {}
        stale_count = 0

        for node in self._nodes.values():
            # Count by type
            type_name = node.doc_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # Count by lifecycle
            lifecycle_name = node.lifecycle.value
            by_lifecycle[lifecycle_name] = by_lifecycle.get(lifecycle_name, 0) + 1

            # Count stale
            if node.is_stale:
                stale_count += 1

        return {
            "summary": {
                "total_nodes": len(self._nodes),
                "root_count": len(self._roots),
                "stale_count": stale_count,
                "anchor_count": len(self._anchors),
            },
            "by_type": by_type,
            "by_lifecycle": by_lifecycle,
            "roots": [str(r) for r in self.get_roots()],
        }


__all__ = ["HierarchyRegistry"]
