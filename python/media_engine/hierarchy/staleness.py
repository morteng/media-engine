"""
Staleness Propagation for Media Engine

Detects when derived documents need updating because their
source documents have changed. Propagates staleness through
the hierarchy graph.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .types import (
    ImpactedDocument,
    StalenessInfo,
    StalenessReason,
)

if TYPE_CHECKING:
    from .graph import HierarchyGraph

logger = logging.getLogger(__name__)


@dataclass
class StalenessReport:
    """Report of staleness analysis across the project."""

    stale_documents: list[StalenessInfo]
    total_documents: int
    stale_count: int
    by_reason: dict[str, int] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def stale_percentage(self) -> float:
        """Percentage of documents that are stale."""
        if self.total_documents == 0:
            return 0.0
        return (self.stale_count / self.total_documents) * 100

    def to_dict(self) -> dict:
        return {
            "stale_documents": [s.to_dict() for s in self.stale_documents],
            "total_documents": self.total_documents,
            "stale_count": self.stale_count,
            "stale_percentage": round(self.stale_percentage, 2),
            "by_reason": self.by_reason,
            "generated_at": self.generated_at.isoformat(),
        }


class StalenessChecker:
    """
    Checks and propagates document staleness through the hierarchy.

    Staleness reasons:
    - SOURCE_UPDATED: A source document has a newer version
    - PARENT_UPDATED: Parent document was modified
    - DERIVATION_MISMATCH: Source version doesn't match derived_from
    - TIME_BASED: Document hasn't been reviewed in freshness_days
    - CASCADE: Child of a stale document
    """

    def __init__(self, graph: "HierarchyGraph"):
        self.graph = graph
        self.registry = graph.registry

    def check_document(self, path: Path) -> Optional[StalenessInfo]:
        """
        Check if a single document is stale.

        Returns StalenessInfo if stale, None if fresh.
        """
        node = self.registry.get_node(path)
        if not node:
            return None

        stale_sources = []
        reasons = []

        # Check derivation sources
        for source in node.derived_from:
            source_node = self.registry.get_node(source.path)
            if source_node:
                # Check if source version is newer
                if self._is_version_newer(source.version, self._get_current_version(source.path)):
                    stale_sources.append(source.path)
                    reasons.append(StalenessReason.SOURCE_UPDATED)

                # Check if source is stale (transitive)
                if source_node.is_stale:
                    stale_sources.append(source.path)
                    reasons.append(StalenessReason.TRANSITIVE)

        # Check parent staleness (also transitive)
        if node.parent:
            parent_node = self.registry.get_node(node.parent)
            if parent_node and parent_node.is_stale:
                stale_sources.append(node.parent)
                reasons.append(StalenessReason.TRANSITIVE)

        if not reasons:
            return None

        # Use most specific reason
        primary_reason = self._get_primary_reason(reasons)

        return StalenessInfo(
            document=path,
            reason=primary_reason,
            stale_sources=stale_sources,
            detected_at=datetime.now(),
            days_stale=0,  # Would need last_modified comparison
        )

    def check_all(self) -> StalenessReport:
        """
        Check all documents for staleness.

        Returns a comprehensive staleness report.
        """
        stale_docs = []
        by_reason: dict[str, int] = {}
        total = 0

        for node in self.registry.get_all_nodes():
            total += 1
            info = self.check_document(node.path)
            if info:
                stale_docs.append(info)
                reason_key = info.reason.value
                by_reason[reason_key] = by_reason.get(reason_key, 0) + 1

        return StalenessReport(
            stale_documents=stale_docs,
            total_documents=total,
            stale_count=len(stale_docs),
            by_reason=by_reason,
        )

    def propagate_staleness(self, source_path: Path) -> list[ImpactedDocument]:
        """
        Find all documents impacted when a source becomes stale.

        Propagates staleness through:
        1. Derivation relationships (documents that derive from source)
        2. Hierarchy (children of stale document)
        """
        impacted = []
        visited = set()

        def propagate(path: Path, depth: int, via_relationship: str):
            path_str = str(path)
            if path_str in visited:
                return
            visited.add(path_str)

            node = self.registry.get_node(path)
            if not node:
                return

            # Find derivatives (documents that derive from this one)
            derivatives = self.graph.get_derivatives(path)
            for deriv_path in derivatives:
                if str(deriv_path) not in visited:
                    impacted.append(
                        ImpactedDocument(
                            path=deriv_path,
                            impact_type="derived",
                            impact_reason=f"Derives from updated: {path.name}",
                            severity="high",
                            suggested_action="Review and update",
                        )
                    )
                    propagate(deriv_path, depth + 1, "derivation")

            # Find children in hierarchy
            children = self.graph.get_children(path)
            for child_path in children:
                if str(child_path) not in visited:
                    impacted.append(
                        ImpactedDocument(
                            path=child_path,
                            impact_type="child",
                            impact_reason=f"Child of stale: {path.name}",
                            severity="medium",
                            suggested_action="Check if update needed",
                        )
                    )
                    propagate(child_path, depth + 1, "hierarchy")

        # Start propagation from source
        propagate(source_path, 0, "source")

        return impacted

    def mark_stale(
        self,
        path: Path,
        reason: StalenessReason,
        sources: Optional[list[Path]] = None,
        propagate: bool = True,
        _visited: Optional[set[str]] = None,
    ) -> bool:
        """
        Mark a document as stale and propagate to dependents.

        Args:
            path: Document path to mark stale
            reason: Why the document is stale
            sources: Source documents that caused staleness
            propagate: Whether to propagate staleness to dependents
            _visited: Internal parameter to prevent infinite loops

        Returns True if document was marked stale.
        """
        # Initialize visited set for cycle detection
        if _visited is None:
            _visited = set()

        path_str = str(path)
        if path_str in _visited:
            # Already processed this document - avoid infinite loop
            return False
        _visited.add(path_str)

        node = self.registry.get_node(path)
        if not node:
            return False

        node.is_stale = True
        node.stale_reason = reason
        node.stale_sources = sources or []
        self.registry.set_node(node)

        # Propagate to dependents (if enabled)
        if propagate:
            # Get impacted documents (this uses its own visited set internally)
            impacted = self.propagate_staleness(path)

            # Mark each impacted document as stale, sharing the visited set
            for impact in impacted:
                impact_path_str = str(impact.path)
                if impact_path_str not in _visited:
                    self.mark_stale(
                        impact.path,
                        StalenessReason.TRANSITIVE,
                        [path],
                        propagate=False,  # Don't re-propagate to avoid exponential growth
                        _visited=_visited,
                    )

        return True

    def mark_fresh(self, path: Path) -> bool:
        """
        Mark a document as fresh (not stale).

        Does NOT automatically refresh dependents.
        """
        node = self.registry.get_node(path)
        if not node:
            return False

        node.is_stale = False
        node.stale_reason = None
        node.stale_sources = []
        self.registry.set_node(node)

        return True

    def get_stale_chain(self, path: Path) -> list[Path]:
        """
        Get the chain of staleness back to root cause.

        Returns paths from the given document back to the
        original document that caused staleness.
        """
        chain = []
        visited = set()

        def trace_back(current: Path):
            if str(current) in visited:
                return
            visited.add(str(current))
            chain.append(current)

            node = self.registry.get_node(current)
            if not node or not node.stale_sources:
                return

            # Trace first stale source
            for source in node.stale_sources:
                trace_back(source)

        trace_back(path)
        return chain

    def _is_version_newer(
        self, old_version: Optional[str], new_version: Optional[str]
    ) -> bool:
        """Compare semantic versions, return True if new > old."""
        if not old_version or not new_version:
            return False

        try:
            old_parts = [int(p) for p in old_version.split(".")]
            new_parts = [int(p) for p in new_version.split(".")]

            for old_p, new_p in zip(old_parts, new_parts):
                if new_p > old_p:
                    return True
                if new_p < old_p:
                    return False
            return len(new_parts) > len(old_parts)
        except (ValueError, AttributeError):
            return False

    def _get_current_version(self, path: Path) -> Optional[str]:
        """Get the current version of a document."""
        from ..cms.document import Document

        try:
            doc = Document.load(path)
            return doc.metadata.get("version")
        except Exception:
            return None

    def _get_primary_reason(self, reasons: list[StalenessReason]) -> StalenessReason:
        """Get the most important staleness reason from a list."""
        # Priority order (most important first)
        priority = [
            StalenessReason.SOURCE_UPDATED,
            StalenessReason.VERSION_MISMATCH,
            StalenessReason.ANCHOR_CHANGED,
            StalenessReason.EXPIRED,
            StalenessReason.TRANSITIVE,
        ]

        for reason in priority:
            if reason in reasons:
                return reason

        return reasons[0] if reasons else StalenessReason.EXPIRED


__all__ = ["StalenessChecker", "StalenessReport"]
