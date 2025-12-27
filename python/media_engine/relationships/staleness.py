"""
Staleness Tracker for Unified Relationship Registry

Detects and propagates staleness through the relationship graph:
- Hash-based change detection
- Transitive propagation through derivation chains
- Anchor change detection
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Set

from ..core import compute_document_hash, compute_file_hash
from .types import ChangeInfo, EdgeType, RelationshipEdge, StalenessStatus

if TYPE_CHECKING:
    from .registry import UnifiedRegistry


class StalenessTracker:
    """
    Tracks and propagates staleness through the relationship graph.

    Detects:
    - Direct staleness: target content changed since edge was recorded
    - Transitive staleness: a dependency became stale
    - Anchor staleness: a consistency anchor value changed
    """

    def __init__(self, registry: "UnifiedRegistry"):
        self.registry = registry

    def check_all(self) -> list[StalenessStatus]:
        """Check staleness for all documents."""
        results = []

        for node in self.registry.all_nodes():
            status = self.check_document(node.path)
            if status.is_stale:
                results.append(status)

        return results

    def check_document(self, doc_path: Path) -> StalenessStatus:
        """Check staleness for a single document."""
        stale_edges = []
        transitive_sources = []
        suggested_actions = []

        # Check all outgoing edges
        for edge in self.registry.get_outgoing_edges(doc_path):
            is_edge_stale, reason = self._check_edge_staleness(edge)

            if is_edge_stale:
                edge.is_stale = True
                edge.stale_reason = reason
                stale_edges.append(edge)

                # Add suggested action
                action = self._suggest_action(edge)
                if action and action not in suggested_actions:
                    suggested_actions.append(action)

        # Check for transitive staleness (through derivation/translation)
        transitive = self._check_transitive_staleness(doc_path)
        transitive_sources.extend(transitive)

        is_stale = len(stale_edges) > 0 or len(transitive_sources) > 0

        return StalenessStatus(
            document=doc_path,
            is_stale=is_stale,
            stale_edges=stale_edges,
            transitive_sources=transitive_sources,
            suggested_actions=suggested_actions,
        )

    def _check_edge_staleness(self, edge: RelationshipEdge) -> tuple[bool, Optional[str]]:
        """Check if an edge is stale based on hash comparison."""
        if not edge.target_hash:
            # No hash recorded - assume not stale (new edge)
            return False, None

        target = edge.target

        # Compute current hash
        if edge.edge_type == EdgeType.USES_ASSET:
            current_hash = compute_file_hash(target) if target.exists() else None
        else:
            current_hash = compute_document_hash(target) if target.exists() else None

        if current_hash is None:
            # Target doesn't exist - broken reference
            return True, "target_missing"

        if current_hash != edge.target_hash:
            return True, "content_changed"

        return False, None

    def _check_transitive_staleness(self, doc_path: Path) -> list[Path]:
        """Check for transitive staleness through derivation chains."""
        transitive_sources = []

        # Get documents we derive from or translate
        derivation_types = EdgeType.derivation_types() | {EdgeType.TRANSLATES}

        for edge in self.registry.get_outgoing_edges(doc_path):
            if edge.edge_type not in derivation_types:
                continue

            # Check if source document is itself stale
            source_status = self._get_cached_staleness(edge.target)
            if source_status and source_status.is_stale:
                transitive_sources.append(edge.target)

        return transitive_sources

    def _get_cached_staleness(self, doc_path: Path) -> Optional[StalenessStatus]:
        """Get staleness status with caching to avoid cycles."""
        # Simple check - just look at the node's stale flag
        node = self.registry.get_node(doc_path)
        if node and node.is_stale:
            return StalenessStatus(
                document=doc_path,
                is_stale=True,
                stale_edges=[],
                transitive_sources=[],
                suggested_actions=[],
            )
        return None

    def _suggest_action(self, edge: RelationshipEdge) -> Optional[str]:
        """Suggest an action based on edge type and staleness reason."""
        if edge.edge_type == EdgeType.TRANSLATES:
            return f"Update translation: review changes in {edge.target.name}"

        if edge.edge_type in EdgeType.derivation_types():
            return f"Sync with source: {edge.target.name} has changed"

        if edge.edge_type == EdgeType.REFERENCES:
            if edge.stale_reason == "target_missing":
                return f"Fix broken link to {edge.target}"
            return f"Review linked content: {edge.target.name}"

        if edge.edge_type == EdgeType.USES_ASSET:
            if edge.stale_reason == "target_missing":
                return f"Fix missing asset: {edge.target}"
            return f"Review asset change: {edge.target.name}"

        if edge.edge_type == EdgeType.ANCHOR_REF:
            return f"Verify anchor value from {edge.target.name}"

        return None

    def propagate_staleness(self, changed_doc: Path) -> Set[Path]:
        """
        Propagate staleness from a changed document.

        Returns all documents that need updating because of this change.
        """
        affected = set()

        # Find all documents that depend on the changed document
        for edge in self.registry.get_incoming_edges(changed_doc):
            source = edge.source

            # Mark the edge as stale
            self.registry.mark_edge_stale(edge, "source_updated")
            affected.add(source)

            # Recursively propagate for derivation relationships
            if edge.edge_type in EdgeType.derivation_types():
                transitive = self.propagate_staleness(source)
                affected.update(transitive)

        return affected

    def mark_fresh(self, doc_path: Path, edge_type: Optional[EdgeType] = None):
        """
        Mark a document's relationships as fresh.

        Updates hashes to current values and clears staleness.
        """
        for edge in self.registry.get_outgoing_edges(doc_path):
            if edge_type and edge.edge_type != edge_type:
                continue

            # Update hash
            if edge.edge_type == EdgeType.USES_ASSET:
                edge.target_hash = compute_file_hash(edge.target) if edge.target.exists() else None
            else:
                edge.target_hash = compute_document_hash(edge.target) if edge.target.exists() else None

            edge.is_stale = False
            edge.stale_reason = None
            edge.recorded_at = datetime.now()

        # Update node
        node = self.registry.get_node(doc_path)
        if node:
            node.is_stale = False
            node.stale_reasons = []

        self.registry.save()

    def detect_changes(self, doc_path: Path) -> Optional[ChangeInfo]:
        """
        Detect if a document has changed and return change info.
        """
        node = self.registry.get_node(doc_path)
        if not node:
            return None

        current_hash = compute_document_hash(doc_path) if doc_path.exists() else None

        if current_hash != node.content_hash:
            # Document has changed
            affected = self.propagate_staleness(doc_path)

            return ChangeInfo(
                document=doc_path,
                change_type="content" if current_hash else "deleted",
                old_hash=node.content_hash,
                new_hash=current_hash,
                affected_documents=list(affected),
            )

        return None

    def get_stale_report(self) -> dict:
        """Generate a report of all stale relationships."""
        all_statuses = self.check_all()

        by_type = {}
        for status in all_statuses:
            for edge in status.stale_edges:
                edge_type = edge.edge_type.value
                if edge_type not in by_type:
                    by_type[edge_type] = []
                by_type[edge_type].append({
                    "source": str(edge.source),
                    "target": str(edge.target),
                    "reason": edge.stale_reason,
                })

        return {
            "total_stale_documents": len(all_statuses),
            "stale_by_type": by_type,
            "all_stale": [s.to_dict() for s in all_statuses],
        }


__all__ = ["StalenessTracker"]
