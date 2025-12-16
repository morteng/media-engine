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
from .graph import DocumentGraph, DocumentGraphBuilder, GraphEdge, GraphNode
from .index import SearchIndex
from .provenance import ProvenanceTracker
from .quality import QualityChecker
from .references import ReferenceManager
from .schema import DesignSystem, SchemaValidator
from .translation import TranslationStatus, TranslationTracker

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
