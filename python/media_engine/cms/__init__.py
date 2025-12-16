"""
ROP Document CMS - Claude Code Native Document Management System

A comprehensive system for managing documentation with:
- Frontmatter schema validation
- Provenance and version tracking
- Design system integration
- Quality assurance checks
- Cross-reference management
- Search indexing
- Document graph visualization
- Multi-format output
"""

from .document import Document, DocumentCollection
from .schema import SchemaValidator, DesignSystem
from .quality import QualityChecker
from .references import ReferenceManager
from .index import SearchIndex
from .provenance import ProvenanceTracker
from .graph import DocumentGraph, DocumentGraphBuilder, GraphNode, GraphEdge
from .translation import TranslationTracker, TranslationStatus

__all__ = [
    "Document",
    "DocumentCollection",
    "SchemaValidator",
    "DesignSystem",
    "QualityChecker",
    "ReferenceManager",
    "SearchIndex",
    "ProvenanceTracker",
    "DocumentGraph",
    "DocumentGraphBuilder",
    "GraphNode",
    "GraphEdge",
    "TranslationTracker",
    "TranslationStatus",
]
