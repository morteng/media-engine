"""
Search Indexer Module

Builds full-text search indexes from project documents.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


@dataclass
class IndexEntry:
    """A single entry in the search index."""
    id: str
    title: str
    path: str
    language: str
    type: str  # chapter, research, deliverable
    content: str  # Full text content for searching
    excerpt: str  # First ~200 chars for preview
    headings: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    last_modified: Optional[str] = None
    version: Optional[str] = None
    word_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return asdict(self)


@dataclass
class SearchResult:
    """A search result with relevance score."""
    entry: IndexEntry
    score: float
    matches: List[str] = field(default_factory=list)


@dataclass
class SearchIndex:
    """Full-text search index."""
    entries: List[IndexEntry] = field(default_factory=list)
    created_at: str = ""
    version: str = "1.0"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def add(self, entry: IndexEntry):
        """Add an entry to the index."""
        self.entries.append(entry)

    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search the index for matching documents.

        Simple scoring algorithm:
        - Title match: 10 points
        - Heading match: 5 points
        - Tag match: 3 points
        - Content match: 1 point per occurrence
        """
        query_lower = query.lower()
        query_words = query_lower.split()
        results = []

        for entry in self.entries:
            score = 0.0
            matches = []

            # Title matches
            title_lower = entry.title.lower()
            for word in query_words:
                if word in title_lower:
                    score += 10
                    matches.append(f"title: {entry.title}")

            # Heading matches
            for heading in entry.headings:
                heading_lower = heading.lower()
                for word in query_words:
                    if word in heading_lower:
                        score += 5
                        matches.append(f"heading: {heading}")

            # Tag matches
            for tag in entry.tags:
                tag_lower = tag.lower()
                for word in query_words:
                    if word in tag_lower:
                        score += 3
                        matches.append(f"tag: {tag}")

            # Content matches (count occurrences)
            content_lower = entry.content.lower()
            for word in query_words:
                count = content_lower.count(word)
                if count > 0:
                    score += count
                    matches.append(f"content: {count} matches")

            if score > 0:
                results.append(SearchResult(
                    entry=entry,
                    score=score,
                    matches=list(set(matches)),  # Dedupe
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def to_json(self) -> str:
        """Export index as JSON string."""
        return json.dumps({
            "version": self.version,
            "created_at": self.created_at,
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }, indent=2)

    def save(self, path: Path):
        """Save index to file."""
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "SearchIndex":
        """Load index from file."""
        data = json.loads(path.read_text())
        index = cls(
            created_at=data.get("created_at", ""),
            version=data.get("version", "1.0"),
        )
        for entry_data in data.get("entries", []):
            index.entries.append(IndexEntry(**entry_data))
        return index


def extract_headings(content: str) -> List[str]:
    """Extract markdown headings from content."""
    headings = []
    for match in re.finditer(r'^#{1,6}\s+(.+)$', content, re.MULTILINE):
        headings.append(match.group(1).strip())
    return headings


def extract_excerpt(content: str, max_length: int = 200) -> str:
    """Extract first paragraph as excerpt."""
    # Remove frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Remove headings
    content = re.sub(r'^#{1,6}\s+.+$', '', content, flags=re.MULTILINE)

    # Get first substantial paragraph
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    for para in paragraphs:
        # Skip code blocks, lists, etc.
        if para.startswith('```') or para.startswith('-') or para.startswith('|'):
            continue
        if len(para) > 50:
            if len(para) > max_length:
                return para[:max_length].rsplit(' ', 1)[0] + '...'
            return para

    return ""


def clean_content(content: str) -> str:
    """Clean content for indexing."""
    # Remove frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Remove code blocks
    content = re.sub(r'```[\s\S]*?```', '', content)

    # Remove inline code
    content = re.sub(r'`[^`]+`', '', content)

    # Remove links but keep text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

    # Remove images
    content = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', content)

    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content)

    return content.strip()


def index_document(
    path: Path,
    language: str,
    doc_type: str,
) -> Optional[IndexEntry]:
    """
    Index a single document.

    Args:
        path: Path to document
        language: Language code
        doc_type: Document type (chapter, research, deliverable)

    Returns:
        IndexEntry or None if document can't be indexed
    """
    try:
        from ..cms import Document
        doc = Document.load(path)

        content = clean_content(doc.content)
        headings = extract_headings(doc.content)
        excerpt = extract_excerpt(doc.content)

        # Extract tags from frontmatter
        tags = doc.frontmatter.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        return IndexEntry(
            id=f"{language}/{doc_type}/{path.stem}",
            title=doc.title,
            path=str(path),
            language=language,
            type=doc_type,
            content=content,
            excerpt=excerpt,
            headings=headings,
            tags=tags,
            last_modified=doc.frontmatter.get('last_modified'),
            version=doc.frontmatter.get('version'),
            word_count=len(content.split()),
        )
    except Exception as e:
        console.print(f"[yellow]Warning: Could not index {path}: {e}[/yellow]")
        return None


def build_search_index(
    project: "Project",
    console_output: bool = True,
) -> SearchIndex:
    """
    Build full-text search index for a project.

    Args:
        project: Project to index
        console_output: Whether to print progress

    Returns:
        SearchIndex with all indexed documents
    """
    index = SearchIndex()

    if console_output:
        console.print("[bold]Building search index...[/bold]")

    for language in project.languages:
        # Index chapters
        for chapter_path in project.list_chapters(language):
            entry = index_document(chapter_path, language, "chapter")
            if entry:
                index.add(entry)
                if console_output:
                    console.print(f"  [dim]Indexed: {entry.title}[/dim]")

        # Index research documents if they exist
        research_dir = project.get_content_path(language, "research")
        if research_dir.exists():
            for research_path in research_dir.glob("*.md"):
                entry = index_document(research_path, language, "research")
                if entry:
                    index.add(entry)
                    if console_output:
                        console.print(f"  [dim]Indexed: {entry.title}[/dim]")

        # Index deliverables
        deliverables_base = project.root / "docs" / "deliverables"
        if deliverables_base.exists():
            for md_file in deliverables_base.rglob("*.md"):
                entry = index_document(md_file, language, "deliverable")
                if entry:
                    index.add(entry)

    if console_output:
        console.print(f"[green]✓ Indexed {len(index.entries)} documents[/green]")

    return index


def search_documents(
    project: "Project",
    query: str,
    limit: int = 20,
    index_path: Optional[Path] = None,
) -> List[SearchResult]:
    """
    Search project documents.

    Args:
        project: Project to search
        query: Search query
        limit: Maximum results to return
        index_path: Path to existing index (builds new if not provided)

    Returns:
        List of SearchResult
    """
    # Try to load existing index
    if index_path and index_path.exists():
        index = SearchIndex.load(index_path)
    else:
        # Build fresh index
        index = build_search_index(project, console_output=False)

    return index.search(query, limit)
