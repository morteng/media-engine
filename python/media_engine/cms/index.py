"""
Search index generation for documents.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict

from .document import Document, DocumentCollection


@dataclass
class SearchResult:
    """A search result."""
    doc_path: str
    title: str
    score: float
    matches: list[str] = field(default_factory=list)
    context: str = ""

    def __str__(self) -> str:
        return f"{self.title} ({self.score:.2f})"


@dataclass
class IndexEntry:
    """An entry in the search index."""
    doc_path: str
    title: str
    content_text: str  # Plain text content (no markdown)
    headings: list[str]
    tags: list[str]
    status: str
    doc_type: str
    word_count: int


class SearchIndex:
    """Full-text search index for documents."""

    # Common stop words to exclude from indexing
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
        'have', 'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'can', 'just', 'should', 'now',
        # Norwegian common words
        'og', 'i', 'er', 'det', 'en', 'et', 'til', 'på', 'som', 'med',
        'for', 'av', 'har', 'de', 'ikke', 'om', 'vi', 'kan', 'den',
    }

    def __init__(self, docs_dir: Path, index_dir: Path = None):
        self.docs_dir = docs_dir
        self.index_dir = index_dir if index_dir else docs_dir / ".index"
        self.index_file = self.index_dir / "search_index.json"

        self.entries: dict[str, IndexEntry] = {}
        self.term_index: dict[str, list[tuple[str, int]]] = defaultdict(list)
        self.tag_index: dict[str, list[str]] = defaultdict(list)
        self.glossary: dict[str, str] = {}

        self._built = False

    def _ensure_index_dir(self) -> None:
        """Ensure index directory exists."""
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def build(self, collection: DocumentCollection) -> None:
        """Build the search index from a document collection."""
        self.entries.clear()
        self.term_index.clear()
        self.tag_index.clear()

        for doc in collection.all_documents:
            self._index_document(doc)

        self._built = True

    def _index_document(self, doc: Document) -> None:
        """Index a single document."""
        doc_path = str(doc.path.relative_to(self.docs_dir))

        # Extract plain text (remove markdown syntax)
        plain_text = self._extract_plain_text(doc.content)

        # Get headings
        headings = [h[2] for h in doc.get_headings()]

        # Create entry
        entry = IndexEntry(
            doc_path=doc_path,
            title=doc.title,
            content_text=plain_text,
            headings=headings,
            tags=doc.tags,
            status=doc.status,
            doc_type=doc.doc_type,
            word_count=doc.word_count(),
        )
        self.entries[doc_path] = entry

        # Index terms
        terms = self._tokenize(plain_text)
        term_counts: dict[str, int] = defaultdict(int)
        for term in terms:
            term_counts[term] += 1

        for term, count in term_counts.items():
            self.term_index[term].append((doc_path, count))

        # Index title terms with higher weight
        title_terms = self._tokenize(doc.title)
        for term in title_terms:
            # Add extra weight for title matches
            self.term_index[term].append((doc_path, 5))

        # Index heading terms
        for heading in headings:
            heading_terms = self._tokenize(heading)
            for term in heading_terms:
                self.term_index[term].append((doc_path, 3))

        # Index tags
        for tag in doc.tags:
            self.tag_index[tag.lower()].append(doc_path)

    def _extract_plain_text(self, content: str) -> str:
        """Extract plain text from markdown content."""
        text = content

        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', ' ', text)
        text = re.sub(r'`[^`]+`', ' ', text)

        # Remove images
        text = re.sub(r'!\[[^\]]*\]\([^)]+\)', ' ', text)

        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Remove markdown syntax
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # Lists
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # Numbered lists
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)  # Blockquotes

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into searchable terms."""
        # Lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-zA-ZæøåÆØÅ][a-zA-ZæøåÆØÅ0-9]*\b', text)

        # Filter stop words and short words
        terms = [
            w for w in words
            if w not in self.STOP_WORDS and len(w) > 2
        ]

        return terms

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search the index for matching documents."""
        if not self._built:
            return []

        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        # Score documents
        scores: dict[str, float] = defaultdict(float)
        matches: dict[str, list[str]] = defaultdict(list)

        for term in query_terms:
            # Exact matches
            if term in self.term_index:
                for doc_path, count in self.term_index[term]:
                    scores[doc_path] += count
                    if term not in matches[doc_path]:
                        matches[doc_path].append(term)

            # Prefix matches
            for indexed_term in self.term_index:
                if indexed_term.startswith(term) and indexed_term != term:
                    for doc_path, count in self.term_index[indexed_term]:
                        scores[doc_path] += count * 0.5
                        if indexed_term not in matches[doc_path]:
                            matches[doc_path].append(indexed_term)

        # Create results
        results = []
        for doc_path, score in sorted(scores.items(), key=lambda x: -x[1]):
            if doc_path in self.entries:
                entry = self.entries[doc_path]
                context = self._get_context(entry.content_text, query_terms)
                results.append(SearchResult(
                    doc_path=doc_path,
                    title=entry.title,
                    score=score,
                    matches=matches[doc_path],
                    context=context,
                ))

        return results[:limit]

    def _get_context(self, text: str, terms: list[str], context_size: int = 100) -> str:
        """Get context around matched terms."""
        text_lower = text.lower()
        for term in terms:
            pos = text_lower.find(term)
            if pos >= 0:
                start = max(0, pos - context_size // 2)
                end = min(len(text), pos + len(term) + context_size // 2)
                context = text[start:end]
                if start > 0:
                    context = "..." + context
                if end < len(text):
                    context = context + "..."
                return context
        return text[:context_size] + "..." if len(text) > context_size else text

    def search_by_tag(self, tag: str) -> list[str]:
        """Get all documents with a specific tag."""
        return self.tag_index.get(tag.lower(), [])

    def get_all_tags(self) -> dict[str, int]:
        """Get all tags with their counts."""
        return {tag: len(docs) for tag, docs in self.tag_index.items()}

    def get_related_documents(self, doc_path: str, limit: int = 5) -> list[tuple[str, float]]:
        """Find documents related to the given document."""
        if doc_path not in self.entries:
            return []

        entry = self.entries[doc_path]

        # Get terms from this document
        doc_terms = set(self._tokenize(entry.content_text))
        doc_terms.update(self._tokenize(entry.title))
        doc_terms.update(tag.lower() for tag in entry.tags)

        # Score other documents by term overlap
        scores: dict[str, float] = defaultdict(float)

        for term in doc_terms:
            if term in self.term_index:
                for other_path, count in self.term_index[term]:
                    if other_path != doc_path:
                        scores[other_path] += count

            # Tag matches have high weight
            if term in self.tag_index:
                for other_path in self.tag_index[term]:
                    if other_path != doc_path:
                        scores[other_path] += 10

        # Return top related
        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        return sorted_scores[:limit]

    def add_glossary_term(self, term: str, definition: str) -> None:
        """Add a term to the glossary."""
        self.glossary[term.lower()] = definition

    def load_glossary(self, glossary_path: Path) -> None:
        """Load glossary from a file (YAML or JSON)."""
        if not glossary_path.exists():
            return

        import yaml

        with open(glossary_path) as f:
            if glossary_path.suffix in ('.yaml', '.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        if isinstance(data, dict):
            for term, definition in data.items():
                self.add_glossary_term(term, definition)

    def lookup_glossary(self, term: str) -> Optional[str]:
        """Look up a term in the glossary."""
        return self.glossary.get(term.lower())

    def save(self) -> None:
        """Save the index to disk."""
        self._ensure_index_dir()

        # Serialize index
        data = {
            "entries": {
                path: {
                    "title": e.title,
                    "headings": e.headings,
                    "tags": e.tags,
                    "status": e.status,
                    "doc_type": e.doc_type,
                    "word_count": e.word_count,
                }
                for path, e in self.entries.items()
            },
            "term_index": dict(self.term_index),
            "tag_index": dict(self.tag_index),
            "glossary": self.glossary,
        }

        with open(self.index_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> bool:
        """Load the index from disk."""
        if not self.index_file.exists():
            return False

        try:
            with open(self.index_file) as f:
                data = json.load(f)

            # Reconstruct entries (without full content)
            for path, entry_data in data.get("entries", {}).items():
                self.entries[path] = IndexEntry(
                    doc_path=path,
                    title=entry_data["title"],
                    content_text="",  # Not stored
                    headings=entry_data.get("headings", []),
                    tags=entry_data.get("tags", []),
                    status=entry_data.get("status", ""),
                    doc_type=entry_data.get("doc_type", ""),
                    word_count=entry_data.get("word_count", 0),
                )

            self.term_index = defaultdict(list, {
                k: [tuple(x) for x in v]
                for k, v in data.get("term_index", {}).items()
            })
            self.tag_index = defaultdict(list, data.get("tag_index", {}))
            self.glossary = data.get("glossary", {})

            self._built = True
            return True

        except Exception as e:
            print(f"Warning: Failed to load index: {e}")
            return False

    def generate_tag_cloud(self) -> list[tuple[str, int, str]]:
        """Generate data for a tag cloud (tag, count, size_class)."""
        tags = self.get_all_tags()
        if not tags:
            return []

        max_count = max(tags.values())
        min_count = min(tags.values())
        range_count = max_count - min_count if max_count > min_count else 1

        result = []
        for tag, count in sorted(tags.items()):
            # Normalize to size classes (1-5)
            normalized = (count - min_count) / range_count
            size_class = min(5, max(1, int(normalized * 4) + 1))
            result.append((tag, count, f"size-{size_class}"))

        return result

    def generate_stats(self) -> dict[str, Any]:
        """Generate index statistics."""
        return {
            "total_documents": len(self.entries),
            "total_terms": len(self.term_index),
            "total_tags": len(self.tag_index),
            "glossary_terms": len(self.glossary),
            "total_words": sum(e.word_count for e in self.entries.values()),
            "by_status": self._count_by_field("status"),
            "by_type": self._count_by_field("doc_type"),
            "top_tags": sorted(
                self.get_all_tags().items(),
                key=lambda x: -x[1]
            )[:10],
        }

    def _count_by_field(self, field: str) -> dict[str, int]:
        """Count documents by a field value."""
        counts: dict[str, int] = defaultdict(int)
        for entry in self.entries.values():
            value = getattr(entry, field, "unknown")
            counts[value] += 1
        return dict(counts)
