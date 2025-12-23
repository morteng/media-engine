"""
Hierarchy Types for Media Engine

Defines document types, relationships, and hierarchy structures
for managing document organization and information flow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class DocumentType(Enum):
    """
    Hierarchical document type taxonomy.

    Documents are classified by their role in the information hierarchy:
    - Source documents: Authoritative truth
    - Derived documents: Must stay in sync with sources
    - Communication documents: Audience-specific views
    - Reference documents: Often generated
    """

    # Source documents (authoritative truth)
    STRATEGY = "strategy"           # Vision, business case, competitive analysis
    RESEARCH = "research"           # Market, technical, user research
    REQUIREMENTS = "requirements"   # PRD, specs, user stories

    # Derived documents (must stay in sync)
    ARCHITECTURE = "architecture"   # System design, API specs, data models
    IMPLEMENTATION = "implementation"  # Guides, tutorials, how-tos
    OPERATIONS = "operations"       # Runbooks, incident response, deployment

    # Communication documents (audience-specific)
    PITCH = "pitch"                 # Decks, investor materials
    MARKETING = "marketing"         # Landing pages, brochures
    USER_DOCS = "user_docs"         # End-user documentation
    TRAINING = "training"           # Courses, workshops

    # Reference documents (often generated)
    API_REFERENCE = "api_reference"  # API documentation
    CHANGELOG = "changelog"          # Release notes

    # Legacy/generic types (for backward compatibility)
    CHAPTER = "chapter"             # Generic documentation chapter
    SECTION = "section"             # Subsection of a chapter
    SCRIPT = "script"               # Video/audio script
    DIAGRAM = "diagram"             # Diagram definition
    DATA = "data"                   # Data/spreadsheet definition
    SLIDES = "slides"               # Presentation slides

    @classmethod
    def source_types(cls) -> set["DocumentType"]:
        """Get all source document types."""
        return {cls.STRATEGY, cls.RESEARCH, cls.REQUIREMENTS}

    @classmethod
    def derived_types(cls) -> set["DocumentType"]:
        """Get all derived document types."""
        return {cls.ARCHITECTURE, cls.IMPLEMENTATION, cls.OPERATIONS}

    @classmethod
    def communication_types(cls) -> set["DocumentType"]:
        """Get all communication document types."""
        return {cls.PITCH, cls.MARKETING, cls.USER_DOCS, cls.TRAINING}


class Lifecycle(Enum):
    """
    Document lifecycle state.

    Determines how document versions are managed.
    """

    LIVING = "living"           # Always tracks HEAD, continuously updated
    VERSIONED = "versioned"     # Frozen at milestones, explicit versions
    GENERATED = "generated"     # Auto-generated from code/data
    DEPRECATED = "deprecated"   # No longer maintained, kept for reference


class RelationshipType(Enum):
    """
    Types of derivation relationships between documents.
    """

    IMPLEMENTS = "implements"   # Realizes requirements in concrete form
    EXTENDS = "extends"         # Builds upon and expands source
    SUMMARIZES = "summarizes"   # Condensed view of source
    SUPPLEMENTS = "supplements" # Adds to without replacing
    VISUALIZES = "visualizes"   # Diagram/graph representation
    TRANSLATES = "translates"   # Language translation
    GENERATES = "generates"     # Auto-generated from source


class StalenessReason(Enum):
    """
    Reasons why a document might be stale.
    """

    SOURCE_UPDATED = "source_updated"       # Source document was modified
    VERSION_MISMATCH = "version_mismatch"   # Derived from older source version
    TRANSITIVE = "transitive"               # Stale via derivation chain
    EXPIRED = "expired"                     # Beyond freshness_days limit
    ANCHOR_CHANGED = "anchor_changed"       # Consistency anchor value changed


@dataclass
class DerivationSource:
    """
    A source document that another document derives from.

    Tracks the relationship between a derived document and its source,
    including version information for staleness detection.
    """

    path: Path
    version: Optional[str] = None
    relationship: RelationshipType = RelationshipType.IMPLEMENTS
    claims_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "version": self.version,
            "relationship": self.relationship.value,
            "claims_used": self.claims_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DerivationSource":
        """Create from dictionary."""
        return cls(
            path=Path(data["path"]),
            version=data.get("version"),
            relationship=RelationshipType(data.get("relationship", "implements")),
            claims_used=data.get("claims_used", []),
        )


@dataclass
class ConsistencyAnchor:
    """
    A key fact that must be consistent across documents.

    Anchors are defined in source documents and should match
    wherever they're referenced in derived documents.
    """

    id: str
    value: Any
    value_type: str  # numeric, string, list, boolean
    defined_in: Path
    referenced_in: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "value": self.value,
            "value_type": self.value_type,
            "defined_in": str(self.defined_in),
            "referenced_in": [str(p) for p in self.referenced_in],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsistencyAnchor":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            value=data["value"],
            value_type=data["value_type"],
            defined_in=Path(data["defined_in"]),
            referenced_in=[Path(p) for p in data.get("referenced_in", [])],
        )


@dataclass
class HierarchyNode:
    """
    A node in the document hierarchy tree.

    Represents a document's position in the structural hierarchy
    and its derivation relationships.
    """

    path: Path
    title: str = ""
    parent: Optional[Path] = None
    children: list[Path] = field(default_factory=list)
    level: int = 0
    sequence_order: int = 0
    doc_type: DocumentType = DocumentType.CHAPTER
    lifecycle: Lifecycle = Lifecycle.LIVING

    # Derivation relationships
    derived_from: list[DerivationSource] = field(default_factory=list)

    # Governance
    owner: Optional[str] = None
    approvers: list[str] = field(default_factory=list)

    # Staleness tracking
    is_stale: bool = False
    stale_reason: Optional[StalenessReason] = None
    stale_sources: list[Path] = field(default_factory=list)

    # Consistency anchors (key facts defined in this document)
    anchors: dict[str, Any] = field(default_factory=dict)

    # Raw metadata for additional fields (like anchor_refs)
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "title": self.title,
            "parent": str(self.parent) if self.parent else None,
            "children": [str(c) for c in self.children],
            "level": self.level,
            "sequence_order": self.sequence_order,
            "doc_type": self.doc_type.value,
            "lifecycle": self.lifecycle.value,
            "derived_from": [d.to_dict() for d in self.derived_from],
            "owner": self.owner,
            "approvers": self.approvers,
            "is_stale": self.is_stale,
            "stale_reason": self.stale_reason.value if self.stale_reason else None,
            "stale_sources": [str(p) for p in self.stale_sources],
            "anchors": self.anchors,
            "raw_metadata": self.raw_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HierarchyNode":
        """Create from dictionary."""
        return cls(
            path=Path(data["path"]),
            title=data.get("title", ""),
            parent=Path(data["parent"]) if data.get("parent") else None,
            children=[Path(c) for c in data.get("children", [])],
            level=data.get("level", 0),
            sequence_order=data.get("sequence_order", 0),
            doc_type=DocumentType(data.get("doc_type", "chapter")),
            lifecycle=Lifecycle(data.get("lifecycle", "living")),
            derived_from=[
                DerivationSource.from_dict(d) for d in data.get("derived_from", [])
            ],
            owner=data.get("owner"),
            approvers=data.get("approvers", []),
            is_stale=data.get("is_stale", False),
            stale_reason=(
                StalenessReason(data["stale_reason"]) if data.get("stale_reason") else None
            ),
            stale_sources=[Path(p) for p in data.get("stale_sources", [])],
            anchors=data.get("anchors", {}),
            raw_metadata=data.get("raw_metadata", {}),
        )


@dataclass
class Breadcrumb:
    """
    A single item in a breadcrumb navigation trail.
    """

    path: Path
    title: str
    doc_type: DocumentType
    level: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "title": self.title,
            "doc_type": self.doc_type.value,
            "level": self.level,
        }


@dataclass
class NavigationContext:
    """
    Full navigation context for a document.

    Provides all the information needed for navigation UI
    including breadcrumbs, siblings, and parent/child relationships.
    """

    document: Path
    title: str
    breadcrumbs: list[Breadcrumb]
    parent: Optional[Breadcrumb] = None
    children: list[Breadcrumb] = field(default_factory=list)
    previous_sibling: Optional[Path] = None
    next_sibling: Optional[Path] = None
    siblings: list[tuple[Path, str, int]] = field(default_factory=list)  # (path, title, order)
    position_in_siblings: int = 0
    total_siblings: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "title": self.title,
            "breadcrumbs": [b.to_dict() for b in self.breadcrumbs],
            "parent": self.parent.to_dict() if self.parent else None,
            "children": [c.to_dict() for c in self.children],
            "previous_sibling": str(self.previous_sibling) if self.previous_sibling else None,
            "next_sibling": str(self.next_sibling) if self.next_sibling else None,
            "siblings": [(str(p), t, o) for p, t, o in self.siblings],
            "position_in_siblings": self.position_in_siblings,
            "total_siblings": self.total_siblings,
        }


@dataclass
class HierarchyValidationError:
    """
    An error in hierarchy structure.
    """

    error_type: str  # circular, orphan, missing_parent, duplicate_order, etc.
    severity: str    # error, warning
    document: Path
    message: str
    related_documents: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": self.error_type,
            "severity": self.severity,
            "document": str(self.document),
            "message": self.message,
            "related_documents": [str(p) for p in self.related_documents],
        }


@dataclass
class StalenessInfo:
    """
    Staleness status information for a document.
    """

    document: Path
    is_stale: bool
    stale_reason: Optional[StalenessReason] = None
    stale_sources: list[Path] = field(default_factory=list)
    staleness_depth: int = 0  # How many levels from original change
    last_synced: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "is_stale": self.is_stale,
            "stale_reason": self.stale_reason.value if self.stale_reason else None,
            "stale_sources": [str(p) for p in self.stale_sources],
            "staleness_depth": self.staleness_depth,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
        }


@dataclass
class ImpactedDocument:
    """
    A document impacted by a change.
    """

    path: Path
    impact_type: str  # derived, references, translation, child
    impact_reason: str
    severity: str  # high, medium, low
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "impact_type": self.impact_type,
            "impact_reason": self.impact_reason,
            "severity": self.severity,
            "suggested_action": self.suggested_action,
        }


@dataclass
class CoverageGap:
    """
    A gap in documentation coverage.
    """

    gap_type: str  # missing_derivation, missing_translation, missing_operations
    expected_doc_type: DocumentType
    should_derive_from: Path
    suggested_path: str
    priority: str  # high, medium, low
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "gap_type": self.gap_type,
            "expected_doc_type": self.expected_doc_type.value,
            "should_derive_from": str(self.should_derive_from),
            "suggested_path": self.suggested_path,
            "priority": self.priority,
            "reason": self.reason,
        }


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
]
