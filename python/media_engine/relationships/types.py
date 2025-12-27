"""
Unified Relationship Types for Media Engine

Defines the core data structures for the unified relationship registry.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EdgeType(Enum):
    """
    All relationship types in a unified enumeration.

    Consolidates relationships from:
    - Dependencies (reference, asset, translation, explicit)
    - Hierarchy (parent, derived_from with sub-types)
    - Translation (source_document)
    - Anchors (anchor_ref)
    """

    # Structural hierarchy
    PARENT = "parent"               # parent_document relationship
    CHILD = "child"                 # Inverse of parent (computed)

    # Derivation relationships (semantic)
    IMPLEMENTS = "implements"       # Realizes requirements
    EXTENDS = "extends"             # Builds upon source
    SUMMARIZES = "summarizes"       # Condensed view
    SUPPLEMENTS = "supplements"     # Adds without replacing
    VISUALIZES = "visualizes"       # Diagram representation
    TRANSLATES = "translates"       # Language translation
    GENERATES = "generates"         # Auto-generated

    # Content references (detected from content)
    REFERENCES = "references"       # Markdown link [text](doc.md)
    USES_ASSET = "uses_asset"       # Image/file reference

    # Consistency constraints
    ANCHOR_REF = "anchor_ref"       # References a consistency anchor

    # Explicit dependency (generic)
    DEPENDS_ON = "depends_on"       # Explicit depends_on field

    @classmethod
    def derivation_types(cls) -> set["EdgeType"]:
        """Semantic derivation relationships."""
        return {
            cls.IMPLEMENTS, cls.EXTENDS, cls.SUMMARIZES,
            cls.SUPPLEMENTS, cls.VISUALIZES, cls.TRANSLATES, cls.GENERATES
        }

    @classmethod
    def structural_types(cls) -> set["EdgeType"]:
        """Structural hierarchy relationships."""
        return {cls.PARENT, cls.CHILD}

    @classmethod
    def content_types(cls) -> set["EdgeType"]:
        """Relationships detected from content."""
        return {cls.REFERENCES, cls.USES_ASSET}

    @classmethod
    def from_legacy_dep_type(cls, dep_type: str) -> "EdgeType":
        """Convert legacy dependency type to EdgeType."""
        mapping = {
            "reference": cls.REFERENCES,
            "asset": cls.USES_ASSET,
            "translation": cls.TRANSLATES,
            "explicit": cls.DEPENDS_ON,
        }
        return mapping.get(dep_type, cls.DEPENDS_ON)

    @classmethod
    def from_relationship_type(cls, rel_type: str) -> "EdgeType":
        """Convert hierarchy RelationshipType to EdgeType."""
        mapping = {
            "implements": cls.IMPLEMENTS,
            "extends": cls.EXTENDS,
            "summarizes": cls.SUMMARIZES,
            "supplements": cls.SUPPLEMENTS,
            "visualizes": cls.VISUALIZES,
            "translates": cls.TRANSLATES,
            "generates": cls.GENERATES,
        }
        return mapping.get(rel_type, cls.DEPENDS_ON)


@dataclass
class RelationshipEdge:
    """
    A directed edge in the relationship graph.

    Represents: source --[edge_type]--> target

    Includes:
    - Edge metadata (type, context)
    - Hash-based change detection
    - Staleness status
    """

    source: Path
    target: Path
    edge_type: EdgeType

    # Context about the relationship
    context: Optional[str] = None       # e.g., "Link: Chapter Title" or anchor ID
    line_number: Optional[int] = None   # Where in source file
    version: Optional[str] = None       # Source version (for derivation)

    # Hash-based change detection
    target_hash: Optional[str] = None   # Hash when relationship recorded
    recorded_at: Optional[datetime] = None

    # Staleness
    is_stale: bool = False
    stale_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": str(self.source),
            "target": str(self.target),
            "edge_type": self.edge_type.value,
            "context": self.context,
            "line_number": self.line_number,
            "version": self.version,
            "target_hash": self.target_hash,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "is_stale": self.is_stale,
            "stale_reason": self.stale_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationshipEdge":
        """Create from dictionary."""
        return cls(
            source=Path(data["source"]),
            target=Path(data["target"]),
            edge_type=EdgeType(data["edge_type"]),
            context=data.get("context"),
            line_number=data.get("line_number"),
            version=data.get("version"),
            target_hash=data.get("target_hash"),
            recorded_at=(
                datetime.fromisoformat(data["recorded_at"])
                if data.get("recorded_at") else None
            ),
            is_stale=data.get("is_stale", False),
            stale_reason=data.get("stale_reason"),
        )


@dataclass
class DocumentNode:
    """
    A document in the relationship graph.

    Stores document-level metadata and aggregated relationship info.
    """

    path: Path
    title: str = ""
    language: Optional[str] = None

    # Document classification
    doc_type: str = "chapter"
    lifecycle: str = "living"
    status: str = "draft"

    # Content hash for change detection
    content_hash: Optional[str] = None
    last_modified: Optional[datetime] = None

    # Governance
    owner: Optional[str] = None
    approvers: list[str] = field(default_factory=list)

    # Consistency anchors defined in this document
    anchors: dict[str, Any] = field(default_factory=dict)

    # Aggregate staleness (computed from edges)
    is_stale: bool = False
    stale_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "title": self.title,
            "language": self.language,
            "doc_type": self.doc_type,
            "lifecycle": self.lifecycle,
            "status": self.status,
            "content_hash": self.content_hash,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "owner": self.owner,
            "approvers": self.approvers,
            "anchors": self.anchors,
            "is_stale": self.is_stale,
            "stale_reasons": self.stale_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentNode":
        """Create from dictionary."""
        return cls(
            path=Path(data["path"]),
            title=data.get("title", ""),
            language=data.get("language"),
            doc_type=data.get("doc_type", "chapter"),
            lifecycle=data.get("lifecycle", "living"),
            status=data.get("status", "draft"),
            content_hash=data.get("content_hash"),
            last_modified=(
                datetime.fromisoformat(data["last_modified"])
                if data.get("last_modified") else None
            ),
            owner=data.get("owner"),
            approvers=data.get("approvers", []),
            anchors=data.get("anchors", {}),
            is_stale=data.get("is_stale", False),
            stale_reasons=data.get("stale_reasons", []),
        )


@dataclass
class StalenessStatus:
    """
    Detailed staleness status for a document.
    """

    document: Path
    is_stale: bool
    stale_edges: list[RelationshipEdge] = field(default_factory=list)
    transitive_sources: list[Path] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "is_stale": self.is_stale,
            "stale_edges": [e.to_dict() for e in self.stale_edges],
            "transitive_sources": [str(p) for p in self.transitive_sources],
            "suggested_actions": self.suggested_actions,
        }


@dataclass
class ChangeInfo:
    """
    Information about a detected change.
    """

    document: Path
    change_type: str  # content, metadata, deleted, created
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    affected_edges: list[RelationshipEdge] = field(default_factory=list)
    affected_documents: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "change_type": self.change_type,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "affected_edges": [e.to_dict() for e in self.affected_edges],
            "affected_documents": [str(p) for p in self.affected_documents],
        }


__all__ = [
    "EdgeType",
    "RelationshipEdge",
    "DocumentNode",
    "StalenessStatus",
    "ChangeInfo",
]
