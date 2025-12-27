"""
Section-level content tracking for fine-grained change detection.

Parses documents into sections (by heading) and tracks changes at the
section level, enabling smarter translation and dependency tracking.

Instead of marking an entire document as outdated when any part changes,
this module identifies exactly which sections changed.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from .hashing import compute_content_hash


class ChangeType(Enum):
    """Type of change detected in a section."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class Section:
    """A section of a document defined by a heading."""

    heading: str
    level: int  # 1-6 for h1-h6
    content: str
    content_hash: str
    line_start: int
    line_end: int

    # Normalized heading for matching across translations
    normalized_heading: str = ""

    def __post_init__(self):
        if not self.normalized_heading:
            self.normalized_heading = self._normalize_heading(self.heading)

    @staticmethod
    def _normalize_heading(heading: str) -> str:
        """Normalize heading for cross-language matching."""
        # Remove numbering like "1.", "1.1", "Chapter 1:"
        normalized = re.sub(r'^[\d.]+\s*', '', heading)
        normalized = re.sub(r'^(Chapter|Section|Part)\s*\d*:?\s*', '', normalized, flags=re.IGNORECASE)
        # Lowercase and strip
        return normalized.lower().strip()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "heading": self.heading,
            "level": self.level,
            "content_hash": self.content_hash,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "normalized_heading": self.normalized_heading,
        }

    @classmethod
    def from_dict(cls, data: dict, content: str = "") -> "Section":
        """Create from dictionary."""
        return cls(
            heading=data["heading"],
            level=data["level"],
            content=content,
            content_hash=data["content_hash"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            normalized_heading=data.get("normalized_heading", ""),
        )


@dataclass
class SectionDiff:
    """A detected change in a section."""

    heading: str
    normalized_heading: str
    change_type: ChangeType
    old_hash: str = ""
    new_hash: str = ""
    old_line_range: tuple[int, int] = (0, 0)
    new_line_range: tuple[int, int] = (0, 0)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "heading": self.heading,
            "normalized_heading": self.normalized_heading,
            "change_type": self.change_type.value,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "old_line_range": list(self.old_line_range),
            "new_line_range": list(self.new_line_range),
        }


@dataclass
class DocumentSections:
    """All sections in a document with their hashes."""

    sections: list[Section]
    document_hash: str  # Hash of full document for quick comparison

    # Index for fast lookup
    _by_heading: dict[str, Section] = field(default_factory=dict, repr=False)
    _by_normalized: dict[str, Section] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._build_indexes()

    def _build_indexes(self):
        """Build lookup indexes."""
        self._by_heading = {s.heading: s for s in self.sections}
        self._by_normalized = {s.normalized_heading: s for s in self.sections}

    def get_by_heading(self, heading: str) -> Optional[Section]:
        """Get section by exact heading match."""
        return self._by_heading.get(heading)

    def get_by_normalized(self, normalized: str) -> Optional[Section]:
        """Get section by normalized heading (for cross-language matching)."""
        return self._by_normalized.get(normalized.lower().strip())

    def get_hashes(self) -> dict[str, str]:
        """Get heading -> hash mapping for storage."""
        return {s.heading: s.content_hash for s in self.sections}

    def get_normalized_hashes(self) -> dict[str, str]:
        """Get normalized_heading -> hash mapping."""
        return {s.normalized_heading: s.content_hash for s in self.sections}

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "sections": [s.to_dict() for s in self.sections],
            "document_hash": self.document_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentSections":
        """Create from dictionary."""
        sections = [Section.from_dict(s) for s in data.get("sections", [])]
        return cls(
            sections=sections,
            document_hash=data.get("document_hash", ""),
        )


# Heading pattern for markdown
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)


def parse_sections(content: str) -> DocumentSections:
    """
    Parse a markdown document into sections.

    Each section is defined by a heading and includes all content
    until the next heading of equal or higher level.

    Args:
        content: Markdown content (without frontmatter)

    Returns:
        DocumentSections with all sections and their hashes
    """
    lines = content.split('\n')
    sections: list[Section] = []

    # Find all headings with their positions
    headings: list[tuple[int, int, str]] = []  # (line_num, level, text)

    for i, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((i, level, text))

    # Content before first heading is "Introduction" section
    if headings:
        first_heading_line = headings[0][0]
        if first_heading_line > 0:
            intro_content = '\n'.join(lines[:first_heading_line]).strip()
            if intro_content:
                sections.append(Section(
                    heading="(Introduction)",
                    level=0,
                    content=intro_content,
                    content_hash=compute_content_hash(intro_content),
                    line_start=1,
                    line_end=first_heading_line,
                ))

    # Process each heading
    for i, (line_num, level, heading_text) in enumerate(headings):
        # Find end of this section (next heading of same or higher level)
        end_line = len(lines)
        for next_line, next_level, _ in headings[i + 1:]:
            if next_level <= level:
                end_line = next_line
                break
            # If we hit a lower-level heading, that's still part of this section
            # unless there's an equal or higher level after it
        else:
            # No heading of same or higher level found, go to end
            if i + 1 < len(headings):
                end_line = headings[i + 1][0]

        # Extract section content (excluding the heading line itself)
        section_lines = lines[line_num + 1:end_line]
        section_content = '\n'.join(section_lines).strip()

        sections.append(Section(
            heading=heading_text,
            level=level,
            content=section_content,
            content_hash=compute_content_hash(section_content),
            line_start=line_num + 1,  # 1-indexed
            line_end=end_line,
        ))

    # Compute full document hash
    doc_hash = compute_content_hash(content)

    return DocumentSections(sections=sections, document_hash=doc_hash)


def parse_document_sections(doc_path: Path) -> DocumentSections:
    """
    Parse a markdown document file into sections.

    Automatically strips frontmatter before parsing.

    Args:
        doc_path: Path to markdown file

    Returns:
        DocumentSections with all sections and their hashes
    """
    if not doc_path.exists():
        return DocumentSections(sections=[], document_hash="")

    content = doc_path.read_text(encoding="utf-8")

    # Strip frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]

    return parse_sections(content)


def compare_sections(
    old_sections: DocumentSections,
    new_sections: DocumentSections,
    use_normalized: bool = False
) -> list[SectionDiff]:
    """
    Compare two versions of a document and find section-level changes.

    Args:
        old_sections: Previous version's sections
        new_sections: Current version's sections
        use_normalized: If True, match by normalized heading (for translations)

    Returns:
        List of SectionDiff describing each change
    """
    diffs: list[SectionDiff] = []

    if use_normalized:
        old_map = {s.normalized_heading: s for s in old_sections.sections}
        new_map = {s.normalized_heading: s for s in new_sections.sections}
    else:
        old_map = {s.heading: s for s in old_sections.sections}
        new_map = {s.heading: s for s in new_sections.sections}

    # Find modified and removed sections
    for key, old_section in old_map.items():
        if key in new_map:
            new_section = new_map[key]
            if old_section.content_hash != new_section.content_hash:
                diffs.append(SectionDiff(
                    heading=new_section.heading,
                    normalized_heading=new_section.normalized_heading,
                    change_type=ChangeType.MODIFIED,
                    old_hash=old_section.content_hash,
                    new_hash=new_section.content_hash,
                    old_line_range=(old_section.line_start, old_section.line_end),
                    new_line_range=(new_section.line_start, new_section.line_end),
                ))
        else:
            diffs.append(SectionDiff(
                heading=old_section.heading,
                normalized_heading=old_section.normalized_heading,
                change_type=ChangeType.REMOVED,
                old_hash=old_section.content_hash,
                old_line_range=(old_section.line_start, old_section.line_end),
            ))

    # Find added sections
    for key, new_section in new_map.items():
        if key not in old_map:
            diffs.append(SectionDiff(
                heading=new_section.heading,
                normalized_heading=new_section.normalized_heading,
                change_type=ChangeType.ADDED,
                new_hash=new_section.content_hash,
                new_line_range=(new_section.line_start, new_section.line_end),
            ))

    return diffs


def get_unchanged_sections(
    old_sections: DocumentSections,
    new_sections: DocumentSections,
    use_normalized: bool = False
) -> list[str]:
    """
    Get list of section headings that haven't changed.

    Args:
        old_sections: Previous version's sections
        new_sections: Current version's sections
        use_normalized: If True, match by normalized heading

    Returns:
        List of heading strings that are unchanged
    """
    if use_normalized:
        old_map = {s.normalized_heading: s.content_hash for s in old_sections.sections}
        new_map = {s.normalized_heading: s for s in new_sections.sections}
    else:
        old_map = {s.heading: s.content_hash for s in old_sections.sections}
        new_map = {s.heading: s for s in new_sections.sections}

    unchanged = []
    for key, new_section in new_map.items():
        if key in old_map and old_map[key] == new_section.content_hash:
            unchanged.append(new_section.heading)

    return unchanged


@dataclass
class SectionChangeReport:
    """Summary of changes between document versions."""

    total_sections_old: int
    total_sections_new: int
    added: list[SectionDiff]
    removed: list[SectionDiff]
    modified: list[SectionDiff]
    unchanged: list[str]

    @property
    def has_changes(self) -> bool:
        """True if any sections changed."""
        return bool(self.added or self.removed or self.modified)

    @property
    def change_summary(self) -> str:
        """Human-readable summary of changes."""
        parts = []
        if self.modified:
            parts.append(f"{len(self.modified)} modified")
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if not parts:
            return "No changes"
        return ", ".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "total_sections_old": self.total_sections_old,
            "total_sections_new": self.total_sections_new,
            "added": [d.to_dict() for d in self.added],
            "removed": [d.to_dict() for d in self.removed],
            "modified": [d.to_dict() for d in self.modified],
            "unchanged": self.unchanged,
            "has_changes": self.has_changes,
            "change_summary": self.change_summary,
        }


def analyze_changes(
    old_sections: DocumentSections,
    new_sections: DocumentSections,
    use_normalized: bool = False
) -> SectionChangeReport:
    """
    Analyze changes between two document versions.

    Provides a comprehensive report of what changed, what was added/removed,
    and what remains unchanged.

    Args:
        old_sections: Previous version's sections
        new_sections: Current version's sections
        use_normalized: If True, match by normalized heading (for translations)

    Returns:
        SectionChangeReport with full analysis
    """
    diffs = compare_sections(old_sections, new_sections, use_normalized)
    unchanged = get_unchanged_sections(old_sections, new_sections, use_normalized)

    return SectionChangeReport(
        total_sections_old=len(old_sections.sections),
        total_sections_new=len(new_sections.sections),
        added=[d for d in diffs if d.change_type == ChangeType.ADDED],
        removed=[d for d in diffs if d.change_type == ChangeType.REMOVED],
        modified=[d for d in diffs if d.change_type == ChangeType.MODIFIED],
        unchanged=unchanged,
    )


__all__ = [
    "ChangeType",
    "Section",
    "SectionDiff",
    "DocumentSections",
    "SectionChangeReport",
    "parse_sections",
    "parse_document_sections",
    "compare_sections",
    "get_unchanged_sections",
    "analyze_changes",
]
