"""
Dependency Graph Tracking for Media Engine

Tracks relationships between documents:
- Internal references (links to other docs)
- Asset dependencies (images, diagrams)
- Translation relationships
- Include/import relationships

When a document changes, dependent documents are flagged for review.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set


@dataclass
class DependencyInfo:
    """Information about a dependency."""

    source: Path
    target: Path
    dep_type: str  # reference, asset, translation, include
    line_number: Optional[int] = None
    context: Optional[str] = None


class DependencyGraph:
    """
    Tracks document dependencies as a directed graph.

    Provides:
    - Forward dependencies (what does this doc depend on)
    - Reverse dependencies (what depends on this doc)
    - Impact analysis (what's affected by a change)
    - Orphan detection (unreferenced documents)
    """

    def __init__(self, project):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.data_path = self.data_dir / "dependencies.json"

        # Graph structure: source -> list of targets
        self._forward: dict[str, list[DependencyInfo]] = defaultdict(list)
        # Reverse graph: target -> list of sources
        self._reverse: dict[str, list[str]] = defaultdict(list)

        self._load()

    def _load(self):
        """Load dependency data from disk."""
        if self.data_path.exists():
            with open(self.data_path) as f:
                data = json.load(f)
                for source, deps in data.get("dependencies", {}).items():
                    for dep in deps:
                        info = DependencyInfo(
                            source=Path(source),
                            target=Path(dep["target"]),
                            dep_type=dep["type"],
                            line_number=dep.get("line"),
                            context=dep.get("context"),
                        )
                        self._forward[source].append(info)
                        self._reverse[dep["target"]].append(source)

    def _save(self):
        """Save dependency data to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {"dependencies": {}}
        for source, deps in self._forward.items():
            data["dependencies"][source] = [
                {
                    "target": str(d.target),
                    "type": d.dep_type,
                    "line": d.line_number,
                    "context": d.context,
                }
                for d in deps
            ]
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_dependency(
        self,
        source: Path,
        target: Path,
        dep_type: str,
        line_number: int = None,
        context: str = None,
    ):
        """Add a dependency from source to target."""
        source_str = str(source)
        target_str = str(target)

        # Check if already exists
        for dep in self._forward[source_str]:
            if str(dep.target) == target_str and dep.dep_type == dep_type:
                return

        info = DependencyInfo(
            source=source,
            target=target,
            dep_type=dep_type,
            line_number=line_number,
            context=context,
        )
        self._forward[source_str].append(info)
        self._reverse[target_str].append(source_str)
        self._save()

    def remove_dependencies(self, source: Path):
        """Remove all dependencies for a source document."""
        source_str = str(source)
        if source_str in self._forward:
            # Remove from reverse graph
            for dep in self._forward[source_str]:
                target_str = str(dep.target)
                if target_str in self._reverse:
                    self._reverse[target_str] = [
                        s for s in self._reverse[target_str] if s != source_str
                    ]
            del self._forward[source_str]
            self._save()

    def get_dependencies(self, source: Path) -> list[DependencyInfo]:
        """Get all dependencies for a document."""
        return self._forward.get(str(source), [])

    def get_dependents(self, target: Path) -> list[Path]:
        """Get all documents that depend on the target."""
        return [Path(s) for s in self._reverse.get(str(target), [])]

    def get_impact(self, changed: Path, max_depth: int = 10) -> Set[Path]:
        """
        Get all documents affected by a change.

        Follows the dependency chain up to max_depth levels.
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

            for dependent in self._reverse.get(current, []):
                affected.add(Path(dependent))
                to_check.add(dependent)

        return affected

    def get_orphans(self) -> list[Path]:
        """Get documents that are not referenced by any other document."""
        all_docs = set()
        referenced = set()

        # Collect all documents
        for source in self._forward:
            all_docs.add(source)
            for dep in self._forward[source]:
                all_docs.add(str(dep.target))
                referenced.add(str(dep.target))

        orphans = all_docs - referenced
        return [Path(p) for p in orphans]

    def get_root_documents(self) -> list[Path]:
        """Get documents that don't depend on anything else."""
        all_sources = set(self._forward.keys())
        all_targets = set()
        for deps in self._forward.values():
            for dep in deps:
                all_targets.add(str(dep.target))

        roots = all_sources - all_targets
        return [Path(p) for p in roots]

    def refresh(self):
        """Rebuild dependency graph by scanning all documents."""
        self._forward.clear()
        self._reverse.clear()

        for lang in self.project.languages:
            chapters = self.project.list_chapters(lang)
            for chapter in chapters:
                self._scan_document(chapter, lang)

        self._save()

    def _scan_document(self, doc_path: Path, language: str):
        """Scan a document for dependencies."""
        from ..cms.document import Document

        doc = Document.load(doc_path)
        content = doc.content

        # 1. Scan for markdown links to other documents
        # Pattern: [text](path.md) or [text](../path.md)
        link_pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
        for match in re.finditer(link_pattern, content):
            link_text, link_path = match.groups()
            target = self._resolve_path(doc_path, link_path)
            if target:
                self.add_dependency(
                    doc_path,
                    target,
                    "reference",
                    context=f"Link: {link_text}",
                )

        # 2. Scan for image references
        # Pattern: ![alt](path) or ![alt](path.png)
        img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        for match in re.finditer(img_pattern, content):
            alt_text, img_path = match.groups()
            if not img_path.startswith(("http://", "https://")):
                target = self._resolve_path(doc_path, img_path)
                if target:
                    self.add_dependency(
                        doc_path,
                        target,
                        "asset",
                        context=f"Image: {alt_text or img_path}",
                    )

        # 3. Check for translation dependency
        source_doc = doc.metadata.get("source_document")
        if source_doc:
            target = self.project.content_dir / source_doc
            if target.exists():
                self.add_dependency(doc_path, target, "translation")

        # 4. Check for explicit depends_on in frontmatter
        depends_on = doc.metadata.get("depends_on", [])
        if isinstance(depends_on, str):
            depends_on = [depends_on]
        for dep in depends_on:
            target = self._resolve_path(doc_path, dep)
            if target:
                self.add_dependency(doc_path, target, "explicit")

    def _resolve_path(self, base: Path, relative: str) -> Optional[Path]:
        """Resolve a relative path from a base document."""
        try:
            # Handle various path formats
            if relative.startswith("/"):
                # Absolute from content root
                target = self.project.content_dir / relative.lstrip("/")
            else:
                # Relative to current document
                target = (base.parent / relative).resolve()

            # Check if within project
            try:
                target.relative_to(self.project.root)
                return target
            except ValueError:
                return None
        except Exception:
            return None

    def generate_report(self) -> dict:
        """Generate a dependency report."""
        return {
            "summary": {
                "total_documents": len(set(self._forward.keys()) | set(self._reverse.keys())),
                "total_dependencies": sum(len(deps) for deps in self._forward.values()),
                "orphan_count": len(self.get_orphans()),
                "root_count": len(self.get_root_documents()),
            },
            "by_type": self._count_by_type(),
            "most_referenced": self._get_most_referenced(10),
            "most_dependencies": self._get_most_dependencies(10),
            "orphans": [str(p) for p in self.get_orphans()],
        }

    def _count_by_type(self) -> dict[str, int]:
        """Count dependencies by type."""
        counts = defaultdict(int)
        for deps in self._forward.values():
            for dep in deps:
                counts[dep.dep_type] += 1
        return dict(counts)

    def _get_most_referenced(self, limit: int) -> list[dict]:
        """Get most referenced documents."""
        counts = {target: len(sources) for target, sources in self._reverse.items()}
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"path": path, "reference_count": count} for path, count in sorted_items[:limit]]

    def _get_most_dependencies(self, limit: int) -> list[dict]:
        """Get documents with most dependencies."""
        counts = {source: len(deps) for source, deps in self._forward.items()}
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"path": path, "dependency_count": count} for path, count in sorted_items[:limit]]

    def visualize_dot(self) -> str:
        """Generate DOT format for visualization."""
        lines = ["digraph dependencies {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")

        for source, deps in self._forward.items():
            source_label = Path(source).name
            for dep in deps:
                target_label = dep.target.name
                style = {
                    "reference": "",
                    "asset": "[style=dashed]",
                    "translation": "[color=blue]",
                    "explicit": "[color=green]",
                }.get(dep.dep_type, "")
                lines.append(f'  "{source_label}" -> "{target_label}" {style};')

        lines.append("}")
        return "\n".join(lines)


from .hashes import (
    DependencyHashInfo,
    DependencyHashTracker,
    DocumentDependencyStatus,
    compute_document_hash,
    compute_file_hash,
)

__all__ = [
    "DependencyInfo",
    "DependencyGraph",
    "DependencyHashInfo",
    "DependencyHashTracker",
    "DocumentDependencyStatus",
    "compute_document_hash",
    "compute_file_hash",
]
