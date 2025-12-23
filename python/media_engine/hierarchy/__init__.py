"""
Document Hierarchy and Information Flow

This module provides tools for managing document hierarchy,
tracking derivation relationships, and detecting staleness.

Key concepts:
- **Document Types**: Classify documents by their role (strategy, architecture, etc.)
- **Hierarchy**: Parent-child relationships with sequence ordering
- **Derivation**: Track which documents derive from which sources
- **Staleness**: Detect when derived documents need updating
- **Consistency**: Track key facts that must match across documents
"""

from .anchors import (
    Anchor,
    AnchorChange,
    AnchorChangeType,
    AnchorReference,
    AnchorRegistry,
    AnchorValidationResult,
)
from .coverage import (
    DERIVATION_PATTERNS,
    CoverageAnalyzer,
    CoverageReport,
    GapPriority,
    GapType,
)
from .graph import HierarchyGraph
from .impact import (
    ImpactAnalyzer,
    ImpactItem,
    ImpactReport,
    ImpactSeverity,
    ImpactType,
)
from .registry import HierarchyRegistry
from .staleness import StalenessChecker, StalenessReport
from .types import (
    # Navigation
    Breadcrumb,
    ConsistencyAnchor,
    CoverageGap,
    # Core data classes
    DerivationSource,
    # Enums
    DocumentType,
    HierarchyNode,
    # Validation and analysis
    HierarchyValidationError,
    ImpactedDocument,
    Lifecycle,
    NavigationContext,
    RelationshipType,
    StalenessInfo,
    StalenessReason,
)
from .validation import HierarchyValidator, ValidationResult

__all__ = [
    # Enums
    "DocumentType",
    "Lifecycle",
    "RelationshipType",
    "StalenessReason",
    # Core data classes
    "DerivationSource",
    "ConsistencyAnchor",
    "HierarchyNode",
    # Navigation
    "Breadcrumb",
    "NavigationContext",
    # Validation and analysis
    "HierarchyValidationError",
    "StalenessInfo",
    "ImpactedDocument",
    "CoverageGap",
    # Registry, Graph, and Validation
    "HierarchyRegistry",
    "HierarchyGraph",
    "HierarchyValidator",
    "ValidationResult",
    # Staleness
    "StalenessChecker",
    "StalenessReport",
    # Anchors
    "AnchorChangeType",
    "Anchor",
    "AnchorReference",
    "AnchorChange",
    "AnchorValidationResult",
    "AnchorRegistry",
    # Impact Analysis
    "ImpactType",
    "ImpactSeverity",
    "ImpactItem",
    "ImpactReport",
    "ImpactAnalyzer",
    # Coverage Analysis
    "GapPriority",
    "GapType",
    "CoverageReport",
    "CoverageAnalyzer",
    "DERIVATION_PATTERNS",
]
