"""
Backward-compatible hierarchy module.

This module is deprecated. Use media_engine.relationships instead.

Provides compatibility wrappers for code that still imports from hierarchy.
"""

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Set

if TYPE_CHECKING:
    from ..core.project import Project


class HierarchyGraph:
    """
    Backward-compatible wrapper for hierarchy navigation.

    Wraps the relationships module to provide legacy API compatibility.
    """

    def __init__(self, project: "Project"):
        """Initialize with a project."""
        self.project = project
        self._registry = None

    @property
    def registry(self):
        """Get the underlying registry (for compatibility with AnchorRegistry)."""
        return self._get_registry()

    def _get_registry(self):
        """Lazily get the unified registry."""
        if self._registry is None:
            try:
                from ..relationships import get_registry_manager, init_registry_manager

                manager = get_registry_manager(self.project)
                if manager is None:
                    manager = init_registry_manager(self.project)
                self._registry = manager.registry
            except Exception:
                self._registry = None
        return self._registry

    def get_parent(self, doc_path: Path) -> Optional[Path]:
        """Get the parent document path."""
        registry = self._get_registry()
        if registry is None:
            return None
        try:
            return registry.get_parent(doc_path)
        except Exception:
            return None

    def get_children(self, doc_path: Path) -> List[Path]:
        """Get child document paths."""
        registry = self._get_registry()
        if registry is None:
            return []
        try:
            return registry.get_children(doc_path)
        except Exception:
            return []

    def get_ancestors(self, doc_path: Path) -> List[Path]:
        """Get ancestor document paths (from closest to furthest)."""
        ancestors = []
        current = doc_path
        visited: Set[Path] = set()

        while current:
            if current in visited:
                break
            visited.add(current)

            parent = self.get_parent(current)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        return ancestors


class ValidationError:
    """A validation error or warning."""

    def __init__(self, error_type: str, document: str, message: str):
        self.error_type = error_type
        self.document = document
        self.message = message


class ValidationResult:
    """Result of validation with errors and warnings."""

    def __init__(self, errors: List = None, warnings: List = None):
        self.errors = errors or []
        self.warnings = warnings or []
        self.valid = len(self.errors) == 0


class HierarchyValidator:
    """
    Backward-compatible validator for hierarchy structure.
    """

    def __init__(self, project: "Project"):
        """Initialize with a project."""
        # Accept either a Project or a HierarchyGraph
        if hasattr(project, "project"):
            # It's a HierarchyGraph, get the actual project
            self.project = project.project
        else:
            self.project = project

    def validate(self) -> ValidationResult:
        """Validate hierarchy and return issues."""
        errors = []
        warnings = []

        try:
            from ..relationships import get_registry_manager, init_registry_manager

            manager = get_registry_manager(self.project)
            if manager is None:
                manager = init_registry_manager(self.project)

            # Run staleness check
            stale = manager.get_stale_documents()
            for doc_path in stale[:20]:
                warnings.append(
                    ValidationError(
                        error_type="stale_document",
                        document=str(doc_path),
                        message=f"Document has stale dependencies: {doc_path}",
                    )
                )
        except Exception:
            # Log error but don't fail
            pass

        return ValidationResult(errors=errors, warnings=warnings)

    def validate_all(self) -> ValidationResult:
        """Validate all documents and return results."""
        return self.validate()


class StalenessReason:
    """Enum-like class for staleness reasons."""

    SOURCE_UPDATED = "source_updated"
    VERSION_MISMATCH = "version_mismatch"
    EXPIRED = "expired"
    ANCHOR_CHANGED = "anchor_changed"

    def __init__(self, value: str):
        self.value = value


class StaleDocumentInfo:
    """Information about a stale document."""

    def __init__(self, document: Path, stale_reason: Optional[StalenessReason] = None, stale_sources: List[Path] = None):
        self.document = document
        self.stale_reason = stale_reason
        self.stale_sources = stale_sources or []


class StalenessReport:
    """Report from staleness check."""

    def __init__(self, stale_documents: List[StaleDocumentInfo] = None):
        self.stale_documents = stale_documents or []


class StalenessChecker:
    """
    Backward-compatible staleness checker.
    """

    def __init__(self, project_or_graph):
        """Initialize with a project or HierarchyGraph."""
        # Accept either a Project or a HierarchyGraph
        if hasattr(project_or_graph, "project"):
            self.project = project_or_graph.project
        else:
            self.project = project_or_graph

    def get_stale_documents(self) -> List[Path]:
        """Get list of stale document paths."""
        try:
            from ..relationships import get_registry_manager, init_registry_manager

            manager = get_registry_manager(self.project)
            if manager is None:
                manager = init_registry_manager(self.project)
            return manager.get_stale_documents()
        except Exception:
            return []

    def check_all(self) -> StalenessReport:
        """Check all documents for staleness."""
        stale_paths = self.get_stale_documents()
        stale_infos = []

        for path in stale_paths:
            stale_infos.append(
                StaleDocumentInfo(
                    document=path,
                    stale_reason=StalenessReason(StalenessReason.SOURCE_UPDATED),
                    stale_sources=[],
                )
            )

        return StalenessReport(stale_documents=stale_infos)


# Re-exports from relationships module
__all__ = [
    "HierarchyGraph",
    "HierarchyValidator",
    "StalenessChecker",
    "StalenessReason",
    "StaleDocumentInfo",
    "StalenessReport",
    "ValidationError",
    "ValidationResult",
]
