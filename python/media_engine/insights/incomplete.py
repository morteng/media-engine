"""
Incomplete Content Tracker

Scans documentation for incomplete markers (TODO, TBD, FIXME, placeholders)
and surfaces them as actionable documentation debt.

Detection patterns:
- TODO/TBD/FIXME/HACK/XXX markers
- Placeholder text (coming soon, [insert X here])
- Empty sections (headings with no content)
- Truncated code examples (...)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..core.project import Project


@dataclass
class IncompleteItem:
    """A detected incomplete content marker."""

    document: Path
    line_number: int
    marker_type: str  # "todo", "tbd", "fixme", "empty_section", "placeholder", "truncated"
    content: str
    priority: str  # "high", "medium", "low"
    context: str = ""  # Surrounding text for context

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "line_number": self.line_number,
            "marker_type": self.marker_type,
            "content": self.content,
            "priority": self.priority,
            "context": self.context,
        }


# Detection patterns for incomplete content
INCOMPLETE_PATTERNS: dict[str, re.Pattern] = {
    "todo": re.compile(r"\bTODO\b:?\s*(.{0,100})", re.IGNORECASE),
    "tbd": re.compile(r"\bTBD\b:?\s*(.{0,100})", re.IGNORECASE),
    "fixme": re.compile(r"\bFIXME\b:?\s*(.{0,100})", re.IGNORECASE),
    "hack": re.compile(r"\bHACK\b:?\s*(.{0,100})", re.IGNORECASE),
    "xxx": re.compile(r"\bXXX\b:?\s*(.{0,100})", re.IGNORECASE),
    "placeholder": re.compile(
        r"(coming soon|placeholder|\[insert\s+.+?\]|\[add\s+.+?\]|"
        r"to be (determined|decided|written|added|completed))",
        re.IGNORECASE,
    ),
    "truncated": re.compile(r"```[\s\S]*?\.\.\.[^\w][\s\S]*?```"),
}

# Pattern for detecting empty sections (heading followed by another heading or EOF)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


@dataclass
class IncompleteTracker:
    """
    Scans project documents for incomplete content markers.

    Usage:
        tracker = IncompleteTracker(project)
        items = tracker.scan_project()
        for item in items:
            print(f"{item.document}:{item.line_number} - {item.marker_type}: {item.content}")
    """

    project: Project
    patterns: dict[str, re.Pattern] = field(default_factory=lambda: INCOMPLETE_PATTERNS.copy())

    def scan_document(self, doc_path: Path) -> list[IncompleteItem]:
        """
        Scan a single document for incomplete markers.

        Args:
            doc_path: Path to the document (relative to content dir or absolute)

        Returns:
            List of IncompleteItem instances found in the document
        """
        # Resolve path
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path
            # Make path relative for storage
            try:
                doc_path = full_path.relative_to(self.project.content_dir)
            except ValueError:
                doc_path = full_path.relative_to(self.project.root)

        if not full_path.exists():
            return []

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        items: list[IncompleteItem] = []
        lines = content.split("\n")

        # Determine document status for priority calculation
        doc_status = self._get_document_status(full_path, content)

        # Scan for pattern-based markers
        for line_num, line in enumerate(lines, start=1):
            for marker_type, pattern in self.patterns.items():
                if marker_type == "truncated":
                    continue  # Handle separately (multi-line)

                matches = pattern.finditer(line)
                for match in matches:
                    matched_text = match.group(0)
                    context = self._get_context(lines, line_num - 1, 2)
                    priority = self._calculate_priority(marker_type, doc_status)

                    items.append(
                        IncompleteItem(
                            document=doc_path,
                            line_number=line_num,
                            marker_type=marker_type,
                            content=matched_text.strip(),
                            priority=priority,
                            context=context,
                        )
                    )

        # Scan for truncated code blocks
        items.extend(self._find_truncated_code(doc_path, content, lines, doc_status))

        # Scan for empty sections
        items.extend(self._find_empty_sections(doc_path, content, lines, doc_status))

        return items

    def scan_project(self) -> list[IncompleteItem]:
        """
        Scan all documents in the project for incomplete markers.

        Returns:
            List of all IncompleteItem instances found
        """
        items: list[IncompleteItem] = []

        # Scan markdown files in content directory
        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                items.extend(self.scan_document(md_file))

        # Sort by priority (high first) then by document
        priority_order = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: (priority_order.get(x.priority, 2), str(x.document), x.line_number))

        return items

    def get_by_priority(self, priority: str) -> list[IncompleteItem]:
        """Get all incomplete items with a specific priority."""
        return [item for item in self.scan_project() if item.priority == priority]

    def get_by_type(self, marker_type: str) -> list[IncompleteItem]:
        """Get all incomplete items of a specific type."""
        return [item for item in self.scan_project() if item.marker_type == marker_type]

    def get_debt_score(self) -> float:
        """
        Calculate a documentation debt score (0-100, lower is better).

        Score is based on count and severity of incomplete items.
        """
        items = self.scan_project()
        if not items:
            return 0.0

        # Weight by priority
        weights = {"high": 10, "medium": 5, "low": 2}
        total_weight = sum(weights.get(item.priority, 2) for item in items)

        # Normalize to 0-100 scale (cap at 100)
        # Assume 50 weighted points = 100% debt
        score = min(100, (total_weight / 50) * 100)
        return round(score, 1)

    def get_summary(self) -> dict:
        """Get a summary of incomplete content."""
        items = self.scan_project()

        by_priority = {"high": 0, "medium": 0, "low": 0}
        by_type: dict[str, int] = {}
        by_document: dict[str, int] = {}

        for item in items:
            by_priority[item.priority] = by_priority.get(item.priority, 0) + 1
            by_type[item.marker_type] = by_type.get(item.marker_type, 0) + 1
            doc_key = str(item.document)
            by_document[doc_key] = by_document.get(doc_key, 0) + 1

        return {
            "total": len(items),
            "by_priority": by_priority,
            "by_type": by_type,
            "by_document": by_document,
            "debt_score": self.get_debt_score(),
        }

    def _get_document_status(self, path: Path, content: str) -> str:
        """Extract document status from frontmatter."""
        import yaml

        # Check for YAML frontmatter
        if content.startswith("---"):
            try:
                end_idx = content.index("---", 3)
                frontmatter = yaml.safe_load(content[3:end_idx])
                if isinstance(frontmatter, dict):
                    return frontmatter.get("status", "draft")
            except (ValueError, yaml.YAMLError):
                pass
        return "draft"

    def _calculate_priority(self, marker_type: str, doc_status: str) -> str:
        """Calculate priority based on marker type and document status."""
        # High priority markers in non-draft docs
        high_priority_markers = {"todo", "tbd", "fixme"}

        if doc_status in ("final", "published", "approved"):
            return "high"
        elif doc_status == "in_review":
            return "medium"
        elif marker_type in high_priority_markers:
            return "medium"
        else:
            return "low"

    def _get_context(self, lines: list[str], line_idx: int, context_lines: int) -> str:
        """Get surrounding context lines."""
        start = max(0, line_idx - context_lines)
        end = min(len(lines), line_idx + context_lines + 1)
        return "\n".join(lines[start:end])

    def _find_truncated_code(
        self, doc_path: Path, content: str, lines: list[str], doc_status: str
    ) -> list[IncompleteItem]:
        """Find truncated code blocks with ellipsis."""
        items: list[IncompleteItem] = []

        # Pattern for code blocks with truncation indicators
        code_block_pattern = re.compile(r"```[\w]*\n([\s\S]*?)```", re.MULTILINE)

        for match in code_block_pattern.finditer(content):
            code_content = match.group(1)
            # Check for truncation indicators
            if re.search(r"\.\.\.[^\w\.]|^\s*\.\.\.\s*$", code_content, re.MULTILINE):
                # Find line number
                start_pos = match.start()
                line_num = content[:start_pos].count("\n") + 1

                items.append(
                    IncompleteItem(
                        document=doc_path,
                        line_number=line_num,
                        marker_type="truncated",
                        content="Truncated code example (...)",
                        priority=self._calculate_priority("truncated", doc_status),
                        context=code_content[:200] + "..." if len(code_content) > 200 else code_content,
                    )
                )

        return items

    def _find_empty_sections(
        self, doc_path: Path, content: str, lines: list[str], doc_status: str
    ) -> list[IncompleteItem]:
        """Find sections with headings but no content."""
        items: list[IncompleteItem] = []
        headings = list(HEADING_PATTERN.finditer(content))

        for i, match in enumerate(headings):
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()
            heading_pos = match.end()

            # Find next heading of same or higher level
            next_content_start = heading_pos
            next_heading_pos = len(content)

            for next_match in headings[i + 1 :]:
                next_level = len(next_match.group(1))
                if next_level <= heading_level:
                    next_heading_pos = next_match.start()
                    break

            # Extract content between headings
            section_content = content[next_content_start:next_heading_pos].strip()

            # Check if section is empty (only whitespace or very short)
            if len(section_content) < 10:
                line_num = content[:match.start()].count("\n") + 1
                items.append(
                    IncompleteItem(
                        document=doc_path,
                        line_number=line_num,
                        marker_type="empty_section",
                        content=f'Empty section: "{heading_text}"',
                        priority=self._calculate_priority("empty_section", doc_status),
                        context=f"## {heading_text}\n(no content)",
                    )
                )

        return items


def scan_project_incomplete(project: Project) -> list[IncompleteItem]:
    """Convenience function to scan a project for incomplete content."""
    tracker = IncompleteTracker(project)
    return tracker.scan_project()
