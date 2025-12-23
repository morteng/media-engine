"""
Hierarchy Graph for Media Engine

Provides tree traversal algorithms and graph operations
for document hierarchy management.
"""

import logging
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional

from .registry import HierarchyRegistry
from .types import (
    Breadcrumb,
    DocumentType,
    HierarchyNode,
    NavigationContext,
)

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class HierarchyGraph:
    """
    Manages document hierarchy as a forest (multiple trees).

    Provides tree traversal, navigation helpers, and graph operations.
    Builds on HierarchyRegistry for persistence.
    """

    def __init__(self, project: "Project"):
        self.project = project
        self.registry = HierarchyRegistry(project)

    # === Tree Structure ===

    def get_roots(self) -> list[Path]:
        """Get all root documents (no parent)."""
        return self.registry.get_roots()

    def get_parent(self, path: Path) -> Optional[Path]:
        """Get immediate parent."""
        return self.registry.get_parent(path)

    def get_children(self, path: Path) -> list[Path]:
        """Get immediate children, sorted by sequence_order."""
        return self.registry.get_children(path)

    def get_siblings(self, path: Path) -> list[Path]:
        """Get documents with same parent, excluding self."""
        return self.registry.get_siblings(path)

    def get_level(self, path: Path) -> int:
        """Get depth level (0 = root)."""
        return self.registry.get_level(path)

    # === Tree Traversal ===

    def get_ancestors(self, path: Path) -> list[Path]:
        """Get all ancestors from document to root."""
        return self.registry.get_ancestors(path)

    def get_descendants(self, path: Path) -> list[Path]:
        """Get all descendants (children, grandchildren, etc)."""
        return self.registry.get_descendants(path)

    def get_path_to_root(self, path: Path) -> list[Path]:
        """Get breadcrumb trail from doc to root (root first)."""
        ancestors = self.get_ancestors(path)
        return list(reversed(ancestors))

    def get_subtree(self, path: Path) -> dict:
        """
        Get entire subtree as nested dict.

        Returns:
            {
                "path": "...",
                "title": "...",
                "children": [...]
            }
        """
        node = self.registry.get_node(path)
        if not node:
            return {}

        children = self.get_children(path)
        return {
            "path": str(path),
            "title": node.title,
            "doc_type": node.doc_type.value,
            "children": [self.get_subtree(child) for child in children],
        }

    # === Tree Queries ===

    def find_common_ancestor(self, path1: Path, path2: Path) -> Optional[Path]:
        """Find lowest common ancestor of two documents."""
        ancestors1 = set(str(a) for a in self.get_ancestors(path1))
        ancestors1.add(str(path1))

        # Walk up path2's ancestors until we find one in path1's ancestors
        current = path2
        while current:
            if str(current) in ancestors1:
                return current
            current = self.get_parent(current)

        return None

    def get_documents_at_level(self, level: int) -> list[Path]:
        """Get all documents at a specific depth."""
        result = []
        for node in self.registry.get_all_nodes():
            if self.get_level(node.path) == level:
                result.append(node.path)
        return result

    def count_descendants(self, path: Path) -> int:
        """Count all descendants of a document."""
        return len(self.get_descendants(path))

    # === Tree Iteration ===

    def walk_preorder(self, root: Optional[Path] = None) -> Iterator[Path]:
        """
        Iterate documents in pre-order (parent before children).

        If root is None, walks all trees in the forest.
        """
        if root:
            yield root
            for child in self.get_children(root):
                yield from self.walk_preorder(child)
        else:
            for root_path in self.get_roots():
                yield from self.walk_preorder(root_path)

    def walk_postorder(self, root: Optional[Path] = None) -> Iterator[Path]:
        """
        Iterate documents in post-order (children before parent).

        If root is None, walks all trees in the forest.
        """
        if root:
            for child in self.get_children(root):
                yield from self.walk_postorder(child)
            yield root
        else:
            for root_path in self.get_roots():
                yield from self.walk_postorder(root_path)

    def walk_levelorder(self, root: Optional[Path] = None) -> Iterator[Path]:
        """
        Iterate documents level by level (BFS).

        If root is None, walks all trees in the forest.
        """
        if root:
            queue = deque([root])
            while queue:
                current = queue.popleft()
                yield current
                queue.extend(self.get_children(current))
        else:
            # Start with all roots
            queue = deque(self.get_roots())
            while queue:
                current = queue.popleft()
                yield current
                queue.extend(self.get_children(current))

    # === Navigation ===

    def get_breadcrumbs(self, path: Path) -> list[Breadcrumb]:
        """Get breadcrumb trail from root to document."""
        trail = []

        # Get path to root (root first)
        ancestors = self.get_path_to_root(path)

        # Add ancestors
        for i, ancestor in enumerate(ancestors):
            node = self.registry.get_node(ancestor)
            if node:
                trail.append(
                    Breadcrumb(
                        path=ancestor,
                        title=node.title,
                        doc_type=node.doc_type,
                        level=i,
                    )
                )

        # Add current document
        node = self.registry.get_node(path)
        if node:
            trail.append(
                Breadcrumb(
                    path=path,
                    title=node.title,
                    doc_type=node.doc_type,
                    level=len(ancestors),
                )
            )

        return trail

    def get_navigation_context(self, path: Path) -> Optional[NavigationContext]:
        """Get full navigation context for a document."""
        node = self.registry.get_node(path)
        if not node:
            return None

        # Get breadcrumbs
        breadcrumbs = self.get_breadcrumbs(path)

        # Get parent
        parent_path = self.get_parent(path)
        parent_crumb = None
        if parent_path:
            parent_node = self.registry.get_node(parent_path)
            if parent_node:
                parent_crumb = Breadcrumb(
                    path=parent_path,
                    title=parent_node.title,
                    doc_type=parent_node.doc_type,
                    level=self.get_level(parent_path),
                )

        # Get children
        children_crumbs = []
        for child_path in self.get_children(path):
            child_node = self.registry.get_node(child_path)
            if child_node:
                children_crumbs.append(
                    Breadcrumb(
                        path=child_path,
                        title=child_node.title,
                        doc_type=child_node.doc_type,
                        level=self.get_level(child_path),
                    )
                )

        # Get siblings with ordering
        all_siblings = []
        if parent_path:
            sibling_paths = self.get_children(parent_path)
        else:
            sibling_paths = self.get_roots()

        position = 0
        prev_sibling = None
        next_sibling = None

        for i, sib_path in enumerate(sibling_paths):
            sib_node = self.registry.get_node(sib_path)
            if sib_node:
                all_siblings.append((sib_path, sib_node.title, sib_node.sequence_order))

            if sib_path == path:
                position = i + 1
                if i > 0:
                    prev_sibling = sibling_paths[i - 1]
                if i < len(sibling_paths) - 1:
                    next_sibling = sibling_paths[i + 1]

        return NavigationContext(
            document=path,
            title=node.title,
            breadcrumbs=breadcrumbs,
            parent=parent_crumb,
            children=children_crumbs,
            previous_sibling=prev_sibling,
            next_sibling=next_sibling,
            siblings=all_siblings,
            position_in_siblings=position,
            total_siblings=len(sibling_paths),
        )

    def get_previous_in_sequence(self, path: Path) -> Optional[Path]:
        """Get previous document in reading order (DFS pre-order)."""
        all_docs = list(self.walk_preorder())
        try:
            idx = all_docs.index(path)
            if idx > 0:
                return all_docs[idx - 1]
        except ValueError:
            pass
        return None

    def get_next_in_sequence(self, path: Path) -> Optional[Path]:
        """Get next document in reading order (DFS pre-order)."""
        all_docs = list(self.walk_preorder())
        try:
            idx = all_docs.index(path)
            if idx < len(all_docs) - 1:
                return all_docs[idx + 1]
        except ValueError:
            pass
        return None

    def format_breadcrumb_string(self, path: Path, separator: str = " > ") -> str:
        """Format breadcrumbs as 'Root > Parent > Document'."""
        breadcrumbs = self.get_breadcrumbs(path)
        return separator.join(b.title for b in breadcrumbs)

    # === Tree Modification ===

    def set_parent(self, doc: Path, parent: Optional[Path]) -> None:
        """Set a document's parent."""
        node = self.registry.get_node(doc)
        if not node:
            node = HierarchyNode(path=doc)

        node.parent = parent
        node.level = self.get_level(parent) + 1 if parent else 0
        self.registry.set_node(node)

    def reorder_children(self, parent: Path, new_order: list[Path]) -> None:
        """Reorder children of a parent."""
        for i, child_path in enumerate(new_order):
            node = self.registry.get_node(child_path)
            if node:
                node.sequence_order = i + 1
                self.registry.set_node(node)

    def reparent_subtree(self, doc: Path, new_parent: Optional[Path]) -> None:
        """Move a document and all descendants to new parent."""
        # Just change the parent - descendants move automatically
        self.set_parent(doc, new_parent)

    # === Derivation Graph ===

    def get_derivation_sources(self, path: Path) -> list[Path]:
        """Get documents this one derives from."""
        sources = self.registry.get_derivation_sources(path)
        return [s.path for s in sources]

    def get_derivatives(self, path: Path) -> list[Path]:
        """Get documents that derive from this one."""
        return self.registry.get_derivatives(path)

    def get_derivation_chain(self, path: Path) -> list[Path]:
        """
        Get full derivation chain (sources of sources).

        Returns sources ordered from most upstream to immediate source.
        """
        chain = []
        visited = set()
        to_visit = list(self.get_derivation_sources(path))

        while to_visit:
            current = to_visit.pop(0)
            if str(current) in visited:
                continue
            visited.add(str(current))
            chain.append(current)
            to_visit.extend(self.get_derivation_sources(current))

        return list(reversed(chain))

    # === Visualization ===

    def to_tree_string(self, root: Optional[Path] = None, indent: str = "") -> str:
        """Generate ASCII tree representation."""
        lines = []

        def add_node(path: Path, prefix: str, is_last: bool) -> None:
            node = self.registry.get_node(path)
            title = node.title if node else path.name

            # Choose connector
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{title}")

            # Recurse to children
            children = self.get_children(path)
            child_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(children):
                add_node(child, child_prefix, i == len(children) - 1)

        if root:
            node = self.registry.get_node(root)
            lines.append(node.title if node else str(root))
            children = self.get_children(root)
            for i, child in enumerate(children):
                add_node(child, "", i == len(children) - 1)
        else:
            roots = self.get_roots()
            for i, root_path in enumerate(roots):
                node = self.registry.get_node(root_path)
                lines.append(node.title if node else str(root_path))
                children = self.get_children(root_path)
                for j, child in enumerate(children):
                    add_node(child, "", j == len(children) - 1)
                if i < len(roots) - 1:
                    lines.append("")  # Blank line between trees

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Generate DOT format for Graphviz visualization."""
        lines = ["digraph hierarchy {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box];")

        # Add all nodes
        for node in self.registry.get_all_nodes():
            label = node.title.replace('"', '\\"')
            style = ""
            if node.doc_type in DocumentType.source_types():
                style = ',style=filled,fillcolor=lightblue'
            elif node.doc_type in DocumentType.derived_types():
                style = ',style=filled,fillcolor=lightyellow'
            elif node.doc_type in DocumentType.communication_types():
                style = ',style=filled,fillcolor=lightgreen'

            lines.append(f'  "{node.path.name}" [label="{label}"{style}];')

        # Add parent-child edges
        for node in self.registry.get_all_nodes():
            for child in self.get_children(node.path):
                child_node = self.registry.get_node(child)
                if child_node:
                    lines.append(f'  "{node.path.name}" -> "{child.name}";')

        # Add derivation edges
        for node in self.registry.get_all_nodes():
            for source in node.derived_from:
                lines.append(
                    f'  "{source.path.name}" -> "{node.path.name}" '
                    f'[style=dashed,color=blue,label="{source.relationship.value}"];'
                )

        lines.append("}")
        return "\n".join(lines)

    def refresh(self) -> None:
        """Rebuild hierarchy from documents."""
        self.registry.refresh()


__all__ = ["HierarchyGraph"]
