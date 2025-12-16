"""
Document and DocumentCollection classes for managing markdown documents with frontmatter.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Any

import frontmatter
import yaml


@dataclass
class Document:
    """Represents a single markdown document with frontmatter."""

    path: Path
    content: str = ""
    metadata: dict = field(default_factory=dict)
    raw_content: str = ""

    # Computed properties
    _parsed: bool = False

    @classmethod
    def load(cls, path: Path) -> "Document":
        """Load a document from a file path."""
        doc = cls(path=path)
        doc.reload()
        return doc

    def reload(self) -> None:
        """Reload document from disk."""
        if not self.path.exists():
            raise FileNotFoundError(f"Document not found: {self.path}")

        with open(self.path, "r", encoding="utf-8") as f:
            self.raw_content = f.read()

        post = frontmatter.loads(self.raw_content)
        self.metadata = dict(post.metadata)
        self.content = post.content
        self._parsed = True

    def save(self) -> None:
        """Save document back to disk."""
        post = frontmatter.Post(self.content, **self.metadata)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    # Metadata accessors
    @property
    def title(self) -> str:
        return self.metadata.get("title", self.path.stem)

    @property
    def version(self) -> str:
        return self.metadata.get("version", "0.0.0")

    @property
    def status(self) -> str:
        return self.metadata.get("status", "draft")

    @property
    def accuracy(self) -> str:
        return self.metadata.get("accuracy", "draft")

    @property
    def last_modified(self) -> Optional[date]:
        lm = self.metadata.get("last_modified")
        if isinstance(lm, date):
            return lm
        if isinstance(lm, str):
            try:
                return datetime.fromisoformat(lm).date()
            except ValueError:
                return None
        return None

    @property
    def last_reviewed(self) -> Optional[date]:
        lr = self.metadata.get("last_reviewed")
        if isinstance(lr, date):
            return lr
        if isinstance(lr, str):
            try:
                return datetime.fromisoformat(lr).date()
            except ValueError:
                return None
        return None

    @property
    def freshness_days(self) -> int:
        return self.metadata.get("freshness_days", 60)

    @property
    def days_since_modified(self) -> Optional[int]:
        if self.last_modified:
            return (date.today() - self.last_modified).days
        return None

    @property
    def days_since_reviewed(self) -> Optional[int]:
        if self.last_reviewed:
            return (date.today() - self.last_reviewed).days
        return None

    @property
    def is_stale(self) -> bool:
        days = self.days_since_modified
        if days is None:
            return True
        return days > self.freshness_days

    @property
    def freshness_status(self) -> str:
        """Return freshness status: fresh, stale, or expired."""
        days = self.days_since_modified
        if days is None:
            return "unknown"
        if days <= self.freshness_days * 0.5:
            return "fresh"
        elif days <= self.freshness_days:
            return "stale"
        else:
            return "expired"

    @property
    def references(self) -> list[dict]:
        return self.metadata.get("references", [])

    @property
    def depends_on(self) -> list[str]:
        return self.metadata.get("depends_on", [])

    @property
    def tags(self) -> list[str]:
        return self.metadata.get("tags", [])

    @property
    def reference_id(self) -> Optional[str]:
        """For research documents, return the reference ID."""
        return self.metadata.get("reference_id")

    @property
    def category(self) -> Optional[str]:
        """Document category (for research docs)."""
        return self.metadata.get("category")

    @property
    def doc_type(self) -> str:
        """Determine document type from path."""
        parts = self.path.parts
        # New structure
        if "source" in parts:
            # Find the category after "source"
            try:
                idx = parts.index("source")
                if idx + 1 < len(parts):
                    return f"source/{parts[idx + 1]}"
            except ValueError:
                pass
            return "source"
        elif "deliverables" in parts:
            # Find the audience after "deliverables"
            try:
                idx = parts.index("deliverables")
                if idx + 1 < len(parts):
                    return f"deliverable/{parts[idx + 1]}"
            except ValueError:
                pass
            return "deliverable"
        elif "project" in parts:
            return "project"
        # Legacy structure
        elif "chapters" in parts:
            return "chapter"
        elif "research" in parts:
            return "research"
        elif "appendices" in parts:
            return "appendix"
        return "unknown"

    @property
    def chapter_number(self) -> Optional[int]:
        """Extract chapter number from filename."""
        match = re.match(r"^(\d+)_", self.path.stem)
        if match:
            return int(match.group(1))
        return None

    # Content analysis
    def find_internal_links(self) -> list[str]:
        """Find all internal markdown links."""
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = []
        for match in re.finditer(pattern, self.content):
            link = match.group(2)
            if not link.startswith(("http://", "https://", "#")):
                links.append(link)
        return links

    def find_citations(self) -> list[int]:
        """Find all citation numbers [1], [2], etc."""
        pattern = r'\[(\d+)\]'
        return [int(m.group(1)) for m in re.finditer(pattern, self.content)]

    def find_images(self) -> list[str]:
        """Find all image references."""
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return [m.group(2) for m in re.finditer(pattern, self.content)]

    def find_todos(self) -> list[tuple[int, str]]:
        """Find TODO, TBD, placeholder markers with line numbers."""
        todos = []
        patterns = [
            r'TODO:?\s*(.*)',
            r'TBD:?\s*(.*)',
            r'\[placeholder\]',
            r'\{\{[^}]+\}\}',
            r'FIXME:?\s*(.*)',
        ]
        for i, line in enumerate(self.content.split('\n'), 1):
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    todos.append((i, line.strip()))
                    break
        return todos

    def find_empty_sections(self) -> list[tuple[int, str]]:
        """Find section headers followed by no content."""
        empty = []
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#'):
                # Check if next non-empty line is another header or end
                j = i + 1
                has_content = False
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('#') or next_line == '---':
                        break
                    if next_line and not next_line.startswith('```'):
                        has_content = True
                        break
                    j += 1
                if not has_content and j < len(lines):
                    empty.append((i + 1, line.strip()))
        return empty

    def get_headings(self) -> list[tuple[int, int, str]]:
        """Get all headings with (line_number, level, text)."""
        headings = []
        for i, line in enumerate(self.content.split('\n'), 1):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append((i, level, text))
        return headings

    def word_count(self) -> int:
        """Count words in content (excluding code blocks)."""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', self.content)
        text = re.sub(r'`[^`]+`', '', text)
        # Count words
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    # Version management
    def increment_version(self, bump: str = "patch") -> str:
        """Increment version number. bump: major, minor, or patch."""
        parts = self.version.split(".")
        if len(parts) != 3:
            parts = ["0", "1", "0"]

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        self.metadata["version"] = new_version
        return new_version

    def update_modified(self, changes: Optional[str] = None) -> None:
        """Update last_modified date and optionally changes note."""
        self.metadata["last_modified"] = date.today().isoformat()
        if changes:
            self.metadata["changes"] = changes

    def __repr__(self) -> str:
        return f"Document({self.path.name}, v{self.version}, {self.status})"


class DocumentCollection:
    """Collection of documents with indexing and querying."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.documents: dict[Path, Document] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Load all documents from the docs directory."""
        self.documents.clear()

        # New structure: source documents
        source_dir = self.docs_dir / "source"
        if source_dir.exists():
            for md_file in source_dir.rglob("*.md"):
                try:
                    doc = Document.load(md_file)
                    self.documents[md_file] = doc
                except Exception as e:
                    print(f"Warning: Failed to load {md_file}: {e}")

        # New structure: deliverables
        deliverables_dir = self.docs_dir / "deliverables"
        if deliverables_dir.exists():
            for md_file in deliverables_dir.rglob("*.md"):
                try:
                    doc = Document.load(md_file)
                    self.documents[md_file] = doc
                except Exception as e:
                    print(f"Warning: Failed to load {md_file}: {e}")

        # Legacy structure: proposal chapters and research
        for subdir in ["proposal/chapters", "proposal/research", "proposal/appendices"]:
            dir_path = self.docs_dir / subdir
            if dir_path.exists():
                for md_file in dir_path.glob("*.md"):
                    try:
                        doc = Document.load(md_file)
                        self.documents[md_file] = doc
                    except Exception as e:
                        print(f"Warning: Failed to load {md_file}: {e}")

        # Project documentation
        project_dir = self.docs_dir / "project"
        if project_dir.exists():
            for md_file in project_dir.rglob("*.md"):
                try:
                    doc = Document.load(md_file)
                    self.documents[md_file] = doc
                except Exception as e:
                    print(f"Warning: Failed to load {md_file}: {e}")

        self._loaded = True

    def ensure_loaded(self) -> None:
        """Ensure documents are loaded."""
        if not self._loaded:
            self.load_all()

    @property
    def chapters(self) -> list[Document]:
        """Get all chapter documents, sorted by number."""
        self.ensure_loaded()
        chapters = [d for d in self.documents.values() if d.doc_type == "chapter"]
        return sorted(chapters, key=lambda d: d.chapter_number or 999)

    @property
    def research(self) -> list[Document]:
        """Get all research documents."""
        self.ensure_loaded()
        return [d for d in self.documents.values() if d.doc_type == "research"]

    @property
    def appendices(self) -> list[Document]:
        """Get all appendix documents."""
        self.ensure_loaded()
        return [d for d in self.documents.values() if d.doc_type == "appendix"]

    @property
    def all_documents(self) -> list[Document]:
        """Get all documents."""
        self.ensure_loaded()
        return list(self.documents.values())

    def get_by_path(self, path: Path) -> Optional[Document]:
        """Get document by path."""
        self.ensure_loaded()
        return self.documents.get(path)

    def get_by_stem(self, stem: str) -> Optional[Document]:
        """Get document by filename stem."""
        self.ensure_loaded()
        for doc in self.documents.values():
            if doc.path.stem == stem:
                return doc
        return None

    def get_by_reference_id(self, ref_id: str) -> Optional[Document]:
        """Get research document by reference ID."""
        self.ensure_loaded()
        for doc in self.documents.values():
            if doc.reference_id == ref_id:
                return doc
        return None

    def filter_by_status(self, status: str) -> list[Document]:
        """Get documents with specific status."""
        self.ensure_loaded()
        return [d for d in self.documents.values() if d.status == status]

    def filter_by_tag(self, tag: str) -> list[Document]:
        """Get documents with specific tag."""
        self.ensure_loaded()
        return [d for d in self.documents.values() if tag in d.tags]

    def filter_stale(self) -> list[Document]:
        """Get documents that are stale or expired."""
        self.ensure_loaded()
        return [d for d in self.documents.values() if d.is_stale]

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        self.ensure_loaded()
        docs = self.all_documents

        by_status = {}
        by_type = {}
        stale_count = 0
        total_words = 0

        for doc in docs:
            by_status[doc.status] = by_status.get(doc.status, 0) + 1
            by_type[doc.doc_type] = by_type.get(doc.doc_type, 0) + 1
            if doc.is_stale:
                stale_count += 1
            total_words += doc.word_count()

        return {
            "total": len(docs),
            "by_status": by_status,
            "by_type": by_type,
            "stale_count": stale_count,
            "total_words": total_words,
        }
