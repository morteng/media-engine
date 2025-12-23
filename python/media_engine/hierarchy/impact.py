"""Impact analysis for document changes.

Determines what documents are affected when a document changes,
including:
- Direct derivatives (documents that derive from the changed document)
- Transitive derivatives (derivatives of derivatives)
- Child documents (structural children)
- Anchor references (documents that reference anchors)
- Translation pairs
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .graph import HierarchyGraph


class ImpactType(Enum):
    """Types of impact a change can have."""

    DERIVED = "derived"             # Document derives from changed doc
    TRANSITIVE = "transitive"       # Derives indirectly
    CHILD = "child"                 # Structural child
    ANCHOR_REF = "anchor_reference" # References an anchor
    TRANSLATION = "translation"     # Translation pair


class ImpactSeverity(Enum):
    """Severity of the impact."""

    CRITICAL = "critical"   # Must be reviewed immediately
    HIGH = "high"           # Should be reviewed soon
    MEDIUM = "medium"       # Review when possible
    LOW = "low"             # Informational


@dataclass
class ImpactItem:
    """A single impacted document."""

    path: Path
    impact_type: ImpactType
    severity: ImpactSeverity
    reason: str
    depth: int = 0  # Distance from original change
    suggested_action: str = "Review for updates"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "impact_type": self.impact_type.value,
            "severity": self.severity.value,
            "reason": self.reason,
            "depth": self.depth,
            "suggested_action": self.suggested_action,
        }


@dataclass
class ImpactReport:
    """Complete impact analysis report."""

    changed_document: Path
    change_type: str  # "content", "metadata", "delete", "anchor"
    change_description: str
    impacted_documents: list[ImpactItem] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_impacted(self) -> int:
        """Total number of impacted documents."""
        return len(self.impacted_documents)

    @property
    def by_severity(self) -> dict[str, int]:
        """Count by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for item in self.impacted_documents:
            counts[item.severity.value] += 1
        return counts

    @property
    def by_type(self) -> dict[str, int]:
        """Count by impact type."""
        counts: dict[str, int] = {}
        for item in self.impacted_documents:
            type_name = item.impact_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    @property
    def has_critical(self) -> bool:
        """Whether any critical impacts exist."""
        return any(i.severity == ImpactSeverity.CRITICAL for i in self.impacted_documents)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "changed_document": str(self.changed_document),
            "change_type": self.change_type,
            "change_description": self.change_description,
            "total_impacted": self.total_impacted,
            "by_severity": self.by_severity,
            "by_type": self.by_type,
            "has_critical": self.has_critical,
            "impacted_documents": [i.to_dict() for i in self.impacted_documents],
            "generated_at": self.generated_at.isoformat(),
        }


class ImpactAnalyzer:
    """Analyzes the impact of document changes."""

    def __init__(self, graph: "HierarchyGraph"):
        self.graph = graph
        self.registry = graph.registry

    def analyze_change(
        self,
        document_path: Path,
        change_type: str = "content",
        change_description: str = "",
    ) -> ImpactReport:
        """
        Analyze the full impact of a change to a document.

        Args:
            document_path: Path to the changed document
            change_type: Type of change (content, metadata, delete, anchor)
            change_description: Human-readable description

        Returns:
            Complete impact report
        """
        impacted: list[ImpactItem] = []
        seen: set[str] = {str(document_path)}

        # 1. Find direct derivatives
        derivatives = self.registry.get_derivatives(document_path)
        for deriv in derivatives:
            if str(deriv) not in seen:
                seen.add(str(deriv))
                impacted.append(
                    ImpactItem(
                        path=deriv,
                        impact_type=ImpactType.DERIVED,
                        severity=ImpactSeverity.HIGH,
                        reason=f"Derives from {document_path.name}",
                        depth=1,
                        suggested_action="Review and update to match source changes",
                    )
                )

        # 2. Find transitive derivatives (depth 2+)
        transitive = self._find_transitive_derivatives(document_path, seen)
        impacted.extend(transitive)

        # 3. Find structural children
        children = self.registry.get_descendants(document_path)
        for child in children:
            if str(child) not in seen:
                seen.add(str(child))
                depth = self.graph.get_level(child) - self.graph.get_level(document_path)
                impacted.append(
                    ImpactItem(
                        path=child,
                        impact_type=ImpactType.CHILD,
                        severity=ImpactSeverity.MEDIUM,
                        reason=f"Child of {document_path.name}",
                        depth=depth,
                        suggested_action="Check if structural changes affect this document",
                    )
                )

        # 4. Find anchor references (if change_type involves anchors)
        if change_type in ("content", "anchor"):
            anchor_refs = self._find_anchor_references(document_path, seen)
            impacted.extend(anchor_refs)

        # Sort by severity then depth
        severity_order = {
            ImpactSeverity.CRITICAL: 0,
            ImpactSeverity.HIGH: 1,
            ImpactSeverity.MEDIUM: 2,
            ImpactSeverity.LOW: 3,
        }
        impacted.sort(key=lambda x: (severity_order[x.severity], x.depth))

        return ImpactReport(
            changed_document=document_path,
            change_type=change_type,
            change_description=change_description or f"Change to {document_path.name}",
            impacted_documents=impacted,
        )

    def _find_transitive_derivatives(
        self,
        source: Path,
        seen: set[str],
        max_depth: int = 5,
    ) -> list[ImpactItem]:
        """Find derivatives of derivatives up to max_depth."""
        transitive: list[ImpactItem] = []
        current_level = self.registry.get_derivatives(source)

        for depth in range(2, max_depth + 1):
            next_level = []
            for deriv in current_level:
                deriv_derivs = self.registry.get_derivatives(deriv)
                for dd in deriv_derivs:
                    if str(dd) not in seen:
                        seen.add(str(dd))
                        severity = (
                            ImpactSeverity.MEDIUM if depth <= 3 else ImpactSeverity.LOW
                        )
                        transitive.append(
                            ImpactItem(
                                path=dd,
                                impact_type=ImpactType.TRANSITIVE,
                                severity=severity,
                                reason=f"Derives from {source.name} (depth {depth})",
                                depth=depth,
                                suggested_action="Review after direct derivatives updated",
                            )
                        )
                        next_level.append(dd)
            current_level = next_level
            if not current_level:
                break

        return transitive

    def _find_anchor_references(
        self,
        document_path: Path,
        seen: set[str],
    ) -> list[ImpactItem]:
        """Find documents that reference anchors defined in the document."""
        from .anchors import AnchorRegistry

        anchor_refs: list[ImpactItem] = []

        # Build anchor registry
        anchor_reg = AnchorRegistry(self.registry)
        anchor_reg.build()

        # Get anchors defined in this document
        anchors = anchor_reg.get_document_anchors(document_path)
        if not anchors:
            return []

        for anchor_name in anchors.keys():
            refs = anchor_reg.get_referencing_documents(document_path, anchor_name)
            for ref_doc in refs:
                if str(ref_doc) not in seen:
                    seen.add(str(ref_doc))
                    anchor_refs.append(
                        ImpactItem(
                            path=ref_doc,
                            impact_type=ImpactType.ANCHOR_REF,
                            severity=ImpactSeverity.HIGH,
                            reason=f"References anchor '{anchor_name}' from {document_path.name}",
                            depth=1,
                            suggested_action="Verify anchor value is still correct",
                        )
                    )

        return anchor_refs

    def analyze_deletion(self, document_path: Path) -> ImpactReport:
        """
        Analyze impact of deleting a document.

        This is similar to analyze_change but treats all impacts as more severe.
        """
        report = self.analyze_change(
            document_path,
            change_type="delete",
            change_description=f"Deletion of {document_path.name}",
        )

        # Upgrade severity for deletions
        for item in report.impacted_documents:
            if item.impact_type == ImpactType.DERIVED:
                item.severity = ImpactSeverity.CRITICAL
                item.suggested_action = "Find new source or remove derivation"
            elif item.impact_type == ImpactType.ANCHOR_REF:
                item.severity = ImpactSeverity.CRITICAL
                item.suggested_action = "Remove anchor reference or find alternative source"
            elif item.impact_type == ImpactType.CHILD:
                item.severity = ImpactSeverity.HIGH
                item.suggested_action = "Reassign parent or delete child documents"

        return report

    def get_impact_chain(self, document_path: Path) -> list[list[Path]]:
        """
        Get all impact chains from a document.

        Returns a list of paths, where each path is a chain of derivations
        from the source document.
        """
        chains: list[list[Path]] = []
        derivatives = self.registry.get_derivatives(document_path)

        for deriv in derivatives:
            chain = [document_path, deriv]
            self._extend_chain(chain, chains)

        return chains

    def _extend_chain(self, current_chain: list[Path], all_chains: list[list[Path]]) -> None:
        """Recursively extend a derivation chain."""
        last = current_chain[-1]
        derivatives = self.registry.get_derivatives(last)

        if not derivatives:
            all_chains.append(current_chain.copy())
            return

        for deriv in derivatives:
            if deriv not in current_chain:  # Avoid cycles
                current_chain.append(deriv)
                self._extend_chain(current_chain, all_chains)
                current_chain.pop()

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of derivation relationships in the project.
        """
        all_nodes = self.registry.get_all_nodes()
        source_count = 0
        derived_count = 0
        max_depth = 0

        for node in all_nodes:
            if node.derived_from:
                derived_count += 1
            else:
                source_count += 1

            # Calculate max depth
            for source in node.derived_from:
                depth = self._get_derivation_depth(node.path, set())
                max_depth = max(max_depth, depth)

        return {
            "total_documents": len(all_nodes),
            "source_documents": source_count,
            "derived_documents": derived_count,
            "max_derivation_depth": max_depth,
        }

    def _get_derivation_depth(self, path: Path, seen: set[str]) -> int:
        """Get the maximum derivation depth of a document."""
        if str(path) in seen:
            return 0
        seen.add(str(path))

        node = self.registry.get_node(path)
        if not node or not node.derived_from:
            return 0

        max_depth = 0
        for source in node.derived_from:
            depth = 1 + self._get_derivation_depth(source.path, seen)
            max_depth = max(max_depth, depth)

        return max_depth


__all__ = [
    "ImpactType",
    "ImpactSeverity",
    "ImpactItem",
    "ImpactReport",
    "ImpactAnalyzer",
]
