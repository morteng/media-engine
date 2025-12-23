"""Coverage analysis for documentation completeness.

Identifies gaps in documentation where derived documents
should exist but don't, based on document type patterns
and project conventions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .types import CoverageGap, DocumentType

if TYPE_CHECKING:
    from .graph import HierarchyGraph


class GapPriority(Enum):
    """Priority of documentation gaps."""

    CRITICAL = "critical"   # Must have - blocks release
    HIGH = "high"           # Should have - important
    MEDIUM = "medium"       # Nice to have - improves quality
    LOW = "low"             # Optional - enhancement


class GapType(Enum):
    """Types of documentation gaps."""

    MISSING_DERIVED = "missing_derived"       # Source without required derivative
    MISSING_TRANSLATION = "missing_translation"  # Content not in all languages
    MISSING_OPERATIONS = "missing_operations"    # Architecture without runbook
    ORPHAN_DOCUMENT = "orphan_document"          # No parent or derivation
    INCOMPLETE_CHAIN = "incomplete_chain"        # Broken derivation chain


# Standard derivation patterns: source_type -> expected derived types
DERIVATION_PATTERNS = {
    DocumentType.REQUIREMENTS: [
        (DocumentType.ARCHITECTURE, GapPriority.CRITICAL, "Architecture from requirements"),
        (DocumentType.IMPLEMENTATION, GapPriority.HIGH, "Implementation guides needed"),
    ],
    DocumentType.ARCHITECTURE: [
        (DocumentType.IMPLEMENTATION, GapPriority.HIGH, "Implementation guides needed"),
        (DocumentType.OPERATIONS, GapPriority.MEDIUM, "Operations runbook recommended"),
        (DocumentType.API_REFERENCE, GapPriority.HIGH, "API reference should be generated"),
    ],
    DocumentType.STRATEGY: [
        (DocumentType.PITCH, GapPriority.MEDIUM, "Pitch deck might be needed"),
        (DocumentType.MARKETING, GapPriority.LOW, "Marketing materials optional"),
    ],
    DocumentType.RESEARCH: [
        (DocumentType.REQUIREMENTS, GapPriority.HIGH, "Research should inform requirements"),
    ],
}


@dataclass
class CoverageReport:
    """Documentation coverage analysis report."""

    gaps: list[CoverageGap] = field(default_factory=list)
    coverage_score: float = 100.0  # 0-100
    generated_at: datetime = field(default_factory=datetime.now)

    # Statistics
    total_documents: int = 0
    source_documents: int = 0
    derived_documents: int = 0
    orphan_documents: int = 0
    missing_translations: int = 0

    @property
    def critical_gaps(self) -> list[CoverageGap]:
        """Get critical priority gaps."""
        return [g for g in self.gaps if g.priority == "critical"]

    @property
    def high_gaps(self) -> list[CoverageGap]:
        """Get high priority gaps."""
        return [g for g in self.gaps if g.priority == "high"]

    @property
    def by_type(self) -> dict[str, int]:
        """Count gaps by type."""
        counts: dict[str, int] = {}
        for gap in self.gaps:
            counts[gap.gap_type] = counts.get(gap.gap_type, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coverage_score": round(self.coverage_score, 1),
            "total_gaps": len(self.gaps),
            "critical_gaps": len(self.critical_gaps),
            "high_gaps": len(self.high_gaps),
            "gaps_by_type": self.by_type,
            "statistics": {
                "total_documents": self.total_documents,
                "source_documents": self.source_documents,
                "derived_documents": self.derived_documents,
                "orphan_documents": self.orphan_documents,
                "missing_translations": self.missing_translations,
            },
            "gaps": [g.to_dict() for g in self.gaps],
            "generated_at": self.generated_at.isoformat(),
        }


class CoverageAnalyzer:
    """Analyzes documentation coverage and identifies gaps."""

    def __init__(self, graph: "HierarchyGraph"):
        self.graph = graph
        self.registry = graph.registry

    def analyze(self, languages: Optional[list[str]] = None) -> CoverageReport:
        """
        Perform full coverage analysis.

        Args:
            languages: List of target languages to check (for translation gaps)

        Returns:
            Complete coverage report
        """
        gaps: list[CoverageGap] = []
        all_nodes = self.registry.get_all_nodes()

        # Categorize documents
        source_docs = []
        derived_docs = []
        orphans = []

        for node in all_nodes:
            if node.derived_from:
                derived_docs.append(node)
            elif node.doc_type in DocumentType.source_types():
                source_docs.append(node)

            # Check for orphans (no parent and no derivation source)
            is_orphan = (
                not node.parent
                and not node.derived_from
                and node.doc_type not in DocumentType.source_types()
            )
            if is_orphan:
                orphans.append(node)

        # 1. Check for missing derived documents
        for source in source_docs:
            expected = DERIVATION_PATTERNS.get(source.doc_type, [])
            existing_types = self._get_derivative_types(source.path)

            for expected_type, priority, reason in expected:
                if expected_type not in existing_types:
                    gaps.append(
                        CoverageGap(
                            gap_type="missing_derived",
                            expected_doc_type=expected_type,
                            should_derive_from=source.path,
                            suggested_path=self._suggest_path(source.path, expected_type),
                            priority=priority.value,
                            reason=reason,
                        )
                    )

        # 2. Check for orphan documents
        for orphan in orphans:
            gaps.append(
                CoverageGap(
                    gap_type="orphan_document",
                    expected_doc_type=orphan.doc_type,
                    should_derive_from=orphan.path,  # Self-reference for orphans
                    suggested_path=str(orphan.path),
                    priority="medium",
                    reason="Document has no parent and doesn't derive from any source",
                )
            )

        # 3. Check for incomplete derivation chains
        for derived in derived_docs:
            for source in derived.derived_from:
                source_node = self.registry.get_node(source.path)
                if not source_node:
                    gaps.append(
                        CoverageGap(
                            gap_type="incomplete_chain",
                            expected_doc_type=derived.doc_type,
                            should_derive_from=source.path,
                            suggested_path=str(source.path),
                            priority="high",
                            reason=f"Source document {source.path} not found",
                        )
                    )

        # 4. Check for missing translations (if languages provided)
        if languages and len(languages) > 1:
            translation_gaps = self._check_translation_coverage(languages)
            gaps.extend(translation_gaps)

        # Calculate coverage score
        total_expected = len(source_docs) * 2  # Rough estimate
        total_actual = len(derived_docs)
        coverage_score = min(100.0, (total_actual / max(total_expected, 1)) * 100)

        # Penalize for gaps
        critical_penalty = len([g for g in gaps if g.priority == "critical"]) * 10
        high_penalty = len([g for g in gaps if g.priority == "high"]) * 5
        coverage_score = max(0, coverage_score - critical_penalty - high_penalty)

        return CoverageReport(
            gaps=gaps,
            coverage_score=coverage_score,
            total_documents=len(all_nodes),
            source_documents=len(source_docs),
            derived_documents=len(derived_docs),
            orphan_documents=len(orphans),
            missing_translations=len([g for g in gaps if g.gap_type == "missing_translation"]),
        )

    def _get_derivative_types(self, source_path: Path) -> set[DocumentType]:
        """Get document types of all derivatives of a source."""
        derivatives = self.registry.get_derivatives(source_path)
        types = set()
        for deriv_path in derivatives:
            node = self.registry.get_node(deriv_path)
            if node:
                types.add(node.doc_type)
        return types

    def _suggest_path(self, source_path: Path, target_type: DocumentType) -> str:
        """Suggest a path for a missing derived document."""
        # Use source name with target type folder
        source_name = source_path.stem
        type_folder = target_type.value.replace("_", "-")
        return f"{type_folder}/{source_name}.md"

    def _check_translation_coverage(self, languages: list[str]) -> list[CoverageGap]:
        """Check if all documents are translated to all languages."""
        gaps = []
        primary_lang = languages[0]

        # Get documents in primary language
        primary_docs = [
            node for node in self.registry.get_all_nodes()
            if primary_lang in str(node.path)
        ]

        for doc in primary_docs:
            for target_lang in languages[1:]:
                # Check if translation exists
                translated_path = self._get_translation_path(doc.path, primary_lang, target_lang)
                if not self.registry.get_node(translated_path):
                    gaps.append(
                        CoverageGap(
                            gap_type="missing_translation",
                            expected_doc_type=doc.doc_type,
                            should_derive_from=doc.path,
                            suggested_path=str(translated_path),
                            priority="medium",
                            reason=f"Missing {target_lang} translation",
                        )
                    )

        return gaps

    def _get_translation_path(self, source_path: Path, source_lang: str, target_lang: str) -> Path:
        """Get expected path for a translation."""
        path_str = str(source_path)
        return Path(path_str.replace(f"/{source_lang}/", f"/{target_lang}/"))

    def get_suggestions(self) -> list[dict[str, Any]]:
        """Get prioritized suggestions for improving coverage."""
        report = self.analyze()
        suggestions = []

        # Critical gaps first
        for gap in report.critical_gaps:
            suggestions.append({
                "priority": "critical",
                "action": "create",
                "target": gap.suggested_path,
                "reason": gap.reason,
                "source": str(gap.should_derive_from),
            })

        # High priority gaps
        for gap in report.high_gaps:
            suggestions.append({
                "priority": "high",
                "action": "create",
                "target": gap.suggested_path,
                "reason": gap.reason,
                "source": str(gap.should_derive_from),
            })

        return suggestions

    def get_completeness_by_type(self) -> dict[str, dict[str, Any]]:
        """Get completeness metrics grouped by document type."""
        all_nodes = self.registry.get_all_nodes()
        by_type: dict[str, dict[str, Any]] = {}

        for node in all_nodes:
            type_name = node.doc_type.value
            if type_name not in by_type:
                by_type[type_name] = {
                    "count": 0,
                    "with_parent": 0,
                    "with_derivation": 0,
                    "stale": 0,
                }

            by_type[type_name]["count"] += 1
            if node.parent:
                by_type[type_name]["with_parent"] += 1
            if node.derived_from:
                by_type[type_name]["with_derivation"] += 1
            if node.is_stale:
                by_type[type_name]["stale"] += 1

        return by_type


__all__ = [
    "GapPriority",
    "GapType",
    "CoverageReport",
    "CoverageAnalyzer",
    "DERIVATION_PATTERNS",
]
