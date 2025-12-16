"""
Media Engine Search Module

Full-text search indexing:
- Document content indexing
- Frontmatter metadata indexing
- JSON search index export
"""

from .indexer import (
    SearchIndex,
    SearchResult,
    IndexEntry,
    build_search_index,
    search_documents,
)

__all__ = [
    "SearchIndex",
    "SearchResult",
    "IndexEntry",
    "build_search_index",
    "search_documents",
]
