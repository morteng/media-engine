"""
Hash-based dependency change detection.

Tracks content hashes for all document dependencies to automatically
detect when dependent content needs review.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import DependencyGraph, DependencyInfo
from ..core.hashing import (
    compute_content_hash,
    compute_document_hash,
    compute_file_hash,
    compute_raw_hash,
)


@dataclass
class DependencyHashInfo:
    """Hash tracking for a single dependency."""

    source_path: str  # Document that has the dependency
    target_path: str  # The dependency target
    dep_type: str     # reference, asset, translation, explicit, data

    # Hash when dependency was recorded
    recorded_hash: str
    recorded_at: str  # ISO timestamp

    # Current state (computed on check)
    current_hash: str = ""
    is_stale: bool = False

    @property
    def hash_changed(self) -> bool:
        """Check if the dependency content has changed."""
        return self.current_hash != self.recorded_hash and self.current_hash != ""


@dataclass
class DocumentDependencyStatus:
    """Aggregated dependency status for a document."""

    path: Path
    title: str
    total_dependencies: int
    stale_dependencies: int
    dependencies: list[DependencyHashInfo] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        return self.stale_dependencies > 0

    @property
    def status_label(self) -> str:
        if self.stale_dependencies == 0:
            return "current"
        return f"{self.stale_dependencies} stale"


class DependencyHashTracker:
    """
    Tracks content hashes for document dependencies.

    Automatically detects when any dependency has changed,
    flagging documents for review.

    Dependency types tracked:
    - reference: Links to other documents
    - asset: Images, diagrams, media files
    - translation: Source document for translations
    - explicit: Declared in depends_on frontmatter
    - data: YAML/JSON data files referenced
    """

    def __init__(self, project):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.data_path = self.data_dir / "dependency_hashes.json"

        # Hash registry: source_path -> {target_path -> DependencyHashInfo}
        self._registry: dict[str, dict[str, DependencyHashInfo]] = {}

        self._load()

    def _load(self):
        """Load hash registry from disk."""
        if self.data_path.exists():
            with open(self.data_path) as f:
                data = json.load(f)
                for source, deps in data.get("hashes", {}).items():
                    self._registry[source] = {}
                    for target, info in deps.items():
                        self._registry[source][target] = DependencyHashInfo(
                            source_path=source,
                            target_path=target,
                            dep_type=info["type"],
                            recorded_hash=info["hash"],
                            recorded_at=info["recorded_at"],
                        )

    def _save(self):
        """Save hash registry to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {"hashes": {}, "last_updated": datetime.now().isoformat()}

        for source, deps in self._registry.items():
            data["hashes"][source] = {}
            for target, info in deps.items():
                data["hashes"][source][target] = {
                    "type": info.dep_type,
                    "hash": info.recorded_hash,
                    "recorded_at": info.recorded_at,
                }

        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def record_dependency(
        self,
        source: Path,
        target: Path,
        dep_type: str,
    ) -> DependencyHashInfo:
        """
        Record a dependency with its current content hash.

        Call this when a document is updated/reviewed to mark
        its dependencies as "known good" at this point.
        """
        source_str = str(source)
        target_str = str(target)

        if source_str not in self._registry:
            self._registry[source_str] = {}

        current_hash = self._compute_hash(target)

        info = DependencyHashInfo(
            source_path=source_str,
            target_path=target_str,
            dep_type=dep_type,
            recorded_hash=current_hash,
            recorded_at=datetime.now().isoformat(),
            current_hash=current_hash,
            is_stale=False,
        )

        self._registry[source_str][target_str] = info
        self._save()

        return info

    def _compute_hash(self, path: Path) -> str:
        """Compute appropriate hash for a file type."""
        if not path.exists():
            return ""

        suffix = path.suffix.lower()

        # Documents - hash content only
        if suffix in (".md", ".mdx"):
            return compute_document_hash(path)

        # Data files - hash everything
        if suffix in (".yaml", ".yml", ".json"):
            return compute_file_hash(path)

        # Assets - hash binary content
        return compute_file_hash(path)

    def check_dependency(
        self,
        source: Path,
        target: Path,
    ) -> Optional[DependencyHashInfo]:
        """
        Check if a specific dependency has changed.

        Returns DependencyHashInfo with is_stale=True if changed.
        """
        source_str = str(source)
        target_str = str(target)

        if source_str not in self._registry:
            return None
        if target_str not in self._registry[source_str]:
            return None

        info = self._registry[source_str][target_str]
        info.current_hash = self._compute_hash(Path(target_str))
        info.is_stale = info.hash_changed

        return info

    def check_document(self, doc_path: Path) -> DocumentDependencyStatus:
        """
        Check all dependencies for a document.

        Returns status with list of stale dependencies.
        """
        from ..cms.document import Document

        doc_str = str(doc_path)

        try:
            doc = Document.load(doc_path)
            title = doc.title
        except Exception:
            title = doc_path.name

        if doc_str not in self._registry:
            return DocumentDependencyStatus(
                path=doc_path,
                title=title,
                total_dependencies=0,
                stale_dependencies=0,
            )

        dependencies = []
        stale_count = 0

        for target_str, info in self._registry[doc_str].items():
            info.current_hash = self._compute_hash(Path(target_str))
            info.is_stale = info.hash_changed
            dependencies.append(info)
            if info.is_stale:
                stale_count += 1

        return DocumentDependencyStatus(
            path=doc_path,
            title=title,
            total_dependencies=len(dependencies),
            stale_dependencies=stale_count,
            dependencies=dependencies,
        )

    def get_all_stale(self) -> list[DocumentDependencyStatus]:
        """Get all documents with stale dependencies."""
        stale = []

        for source_str in self._registry:
            source_path = Path(source_str)
            if not source_path.exists():
                continue

            status = self.check_document(source_path)
            if status.is_stale:
                stale.append(status)

        return stale

    def get_all_statuses(self) -> list[DocumentDependencyStatus]:
        """Get dependency status for all tracked documents."""
        statuses = []

        for source_str in self._registry:
            source_path = Path(source_str)
            if not source_path.exists():
                continue

            status = self.check_document(source_path)
            statuses.append(status)

        return statuses

    def sync_from_graph(self, graph: DependencyGraph):
        """
        Sync hash registry from dependency graph.

        Records current hashes for all dependencies in the graph.
        Use after updating documents to mark dependencies as current.
        """
        synced = 0

        for source_str, deps in graph._forward.items():
            source = Path(source_str)
            for dep_info in deps:
                self.record_dependency(
                    source=source,
                    target=dep_info.target,
                    dep_type=dep_info.dep_type,
                )
                synced += 1

        return synced

    def mark_current(self, doc_path: Path) -> int:
        """
        Mark all dependencies of a document as current.

        Call this after reviewing/updating a document to acknowledge
        that its dependencies are known-good.
        """
        doc_str = str(doc_path)

        if doc_str not in self._registry:
            return 0

        updated = 0
        for target_str in self._registry[doc_str]:
            target = Path(target_str)
            current_hash = self._compute_hash(target)
            self._registry[doc_str][target_str].recorded_hash = current_hash
            self._registry[doc_str][target_str].recorded_at = datetime.now().isoformat()
            self._registry[doc_str][target_str].is_stale = False
            updated += 1

        self._save()
        return updated

    def clear(self, doc_path: Optional[Path] = None):
        """Clear hash registry, optionally for a specific document."""
        if doc_path:
            doc_str = str(doc_path)
            if doc_str in self._registry:
                del self._registry[doc_str]
        else:
            self._registry.clear()

        self._save()

    def generate_report(self) -> dict:
        """Generate dependency hash status report."""
        statuses = self.get_all_statuses()
        stale = [s for s in statuses if s.is_stale]

        # Group by dependency type
        stale_by_type: dict[str, int] = {}
        for status in stale:
            for dep in status.dependencies:
                if dep.is_stale:
                    stale_by_type[dep.dep_type] = stale_by_type.get(dep.dep_type, 0) + 1

        return {
            "summary": {
                "total_documents": len(statuses),
                "documents_with_stale_deps": len(stale),
                "total_dependencies": sum(s.total_dependencies for s in statuses),
                "stale_dependencies": sum(s.stale_dependencies for s in statuses),
            },
            "stale_by_type": stale_by_type,
            "stale_documents": [
                {
                    "path": str(s.path),
                    "title": s.title,
                    "stale_count": s.stale_dependencies,
                    "stale_deps": [
                        {
                            "target": d.target_path,
                            "type": d.dep_type,
                            "old_hash": d.recorded_hash,
                            "new_hash": d.current_hash,
                        }
                        for d in s.dependencies
                        if d.is_stale
                    ],
                }
                for s in stale
            ],
        }

    def remove_document(self, doc_path: Path) -> bool:
        """
        Remove a document and all its dependencies from the registry.

        Called when a document is deleted.
        """
        doc_str = str(doc_path)

        if doc_str in self._registry:
            del self._registry[doc_str]
            self._save()
            return True
        return False

    def register_document(self, doc_path: Path) -> int:
        """
        Register a new document and scan for its dependencies.

        Called when a new document is created.

        Returns the number of dependencies found.
        """
        from ..cms.document import Document

        try:
            doc = Document.load(doc_path)
        except Exception:
            return 0

        registered = 0

        # Check for source_document reference (translations)
        source_ref = doc.metadata.get("source_document")
        if source_ref:
            source_path = self.project.content_dir / source_ref
            if source_path.exists():
                self.record_dependency(doc_path, source_path, "translation")
                registered += 1

        # Check for explicit dependencies
        deps = doc.metadata.get("dependencies", [])
        for dep in deps:
            dep_path = self.project.content_dir / dep
            if dep_path.exists():
                self.record_dependency(doc_path, dep_path, "explicit")
                registered += 1

        return registered

    def update_document_hash(self, doc_path: Path) -> None:
        """
        Update the content hash for a document.

        Called when a document's content changes.
        This updates any entries where this document is a target.
        """
        doc_str = str(doc_path)

        # Note: We don't update recorded_hash here because that
        # represents "when last acknowledged". Instead, the
        # current_hash is computed on-demand during checks.

        # If this document has dependencies, we might want to check
        # if any of its dependencies have changed (but that's done
        # separately in check_document).
        pass

    def check_dependents(self, target_path: Path) -> list[Path]:
        """
        Find all documents that depend on the given target.

        Called when a target file changes to identify affected documents.

        Returns list of document paths that have stale dependencies.
        """
        target_str = str(target_path)
        stale_docs = []

        # Find all documents that have this target as a dependency
        for source_str, deps in self._registry.items():
            if target_str in deps:
                info = deps[target_str]
                # Compute current hash
                current_hash = self._compute_hash(target_path)
                if current_hash != info.recorded_hash:
                    stale_docs.append(Path(source_str))

        return stale_docs


__all__ = [
    "compute_file_hash",
    "compute_document_hash",
    "DependencyHashInfo",
    "DocumentDependencyStatus",
    "DependencyHashTracker",
]
