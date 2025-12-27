"""
Unified Relationship Registry for Media Engine

The single source of truth for all document relationships:
- Hierarchy (parent/child)
- Derivation (implements, extends, summarizes)
- Translation (source_document)
- Reference (markdown links)
- Asset (images, files)
- Anchor (consistency constraints)
- Dependencies (explicit depends_on)

All relationships include hash-based change detection for staleness tracking.

This module replaces the deprecated:
- hierarchy/ module
- dependencies/ module
- Translation tracking in frontmatter (still read but centrally managed)
"""

from .manager import (
    RegistryManager,
    get_registry_manager,
    init_registry_manager,
    reset_registry_manager,
)
from .registry import UnifiedRegistry
from .scanner import RelationshipScanner
from .staleness import StalenessTracker
from .types import (
    ChangeInfo,
    DocumentNode,
    EdgeType,
    RelationshipEdge,
    StalenessStatus,
)

__all__ = [
    # Types
    "EdgeType",
    "RelationshipEdge",
    "DocumentNode",
    "StalenessStatus",
    "ChangeInfo",
    # Core classes
    "UnifiedRegistry",
    "RelationshipScanner",
    "StalenessTracker",
    # Manager (singleton)
    "RegistryManager",
    "get_registry_manager",
    "init_registry_manager",
    "reset_registry_manager",
]
