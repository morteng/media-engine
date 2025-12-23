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


# Import base patterns from centralized settings
from ..settings.defaults import QUALITY as QUALITY_SETTINGS


def _build_incomplete_patterns() -> dict[str, re.Pattern]:
    """Build incomplete patterns from settings with capture groups for content."""
    # Base marker patterns derived from centralized settings
    # These capture the marker and up to 100 chars of context
    patterns: dict[str, re.Pattern] = {}

    # Map settings patterns to named pattern types
    marker_names = {
        r"\bTODO\b": "todo",
        r"\bTBD\b": "tbd",
        r"\bFIXME\b": "fixme",
        r"\bXXX\b": "xxx",
    }

    for base_pattern in QUALITY_SETTINGS.placeholder_patterns:
        name = marker_names.get(base_pattern)
        if name:
            # Add capture group for context
            patterns[name] = re.compile(f"{base_pattern}:?\\s*(.{{0,100}})", re.IGNORECASE)

    # Add HACK pattern (not in settings but commonly used)
    patterns["hack"] = re.compile(r"\bHACK\b:?\s*(.{0,100})", re.IGNORECASE)

    # Extended patterns for natural language placeholders
    patterns["placeholder"] = re.compile(
        r"(coming soon|placeholder|\[insert\s+.+?\]|\[add\s+.+?\]|"
        r"to be (determined|decided|written|added|completed))",
        re.IGNORECASE,
    )

    # Pattern for truncated code blocks
    patterns["truncated"] = re.compile(r"```[\s\S]*?\.\.\.[^\w][\s\S]*?```")

    return patterns


# Detection patterns for incomplete content
INCOMPLETE_PATTERNS: dict[str, re.Pattern] = _build_incomplete_patterns()

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

        # Track code block state and frontmatter state
        in_code_block = False
        in_frontmatter = False

        # Scan for pattern-based markers
        for line_num, line in enumerate(lines, start=1):
            # Track frontmatter (YAML between --- markers at start)
            if line.strip() == "---":
                if line_num == 1:
                    in_frontmatter = True
                    continue
                elif in_frontmatter:
                    in_frontmatter = False
                    continue

            # Skip frontmatter content
            if in_frontmatter:
                continue

            # Track code block state
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip content inside code blocks
            if in_code_block:
                continue

            # Skip markdown headings (they often contain these terms as section titles)
            if line.strip().startswith("#"):
                continue

            for marker_type, pattern in self.patterns.items():
                if marker_type == "truncated":
                    continue  # Handle separately (multi-line)

                # Remove inline code before checking (content in backticks)
                line_without_code = re.sub(r"`[^`]+`", "", line)

                # Skip lines that are documenting patterns (contain documentation words)
                # Includes Norwegian terms (markører, oppdager, sjekk, etc.)
                doc_pattern = r"(markers?|patterns?|detects?|checks?|found|flagged|types?|examples?|markør|oppdager|sjekk|placeholder\s+pattern|content\s+placeholder|addressed|severity|warning|error|issues?)"
                if re.search(doc_pattern, line_without_code, re.IGNORECASE):
                    continue

                # Skip lines that mention "placeholders" (plural) in parentheses - documentation context
                if re.search(r"\(.*placeholders.*\)", line_without_code, re.IGNORECASE):
                    continue

                # Skip if line contains multiple placeholder words (documentation)
                placeholder_words = re.findall(
                    r"\b(TODO|TBD|FIXME|XXX|HACK)\b", line_without_code, re.IGNORECASE
                )
                if len(placeholder_words) >= 2:
                    continue

                # Skip table rows documenting patterns (| pattern | description |)
                if line.strip().startswith("|"):
                    # Tables often document patterns with backticks
                    continue

                matches = pattern.finditer(line_without_code)
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
        items.sort(
            key=lambda x: (priority_order.get(x.priority, 2), str(x.document), x.line_number)
        )

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
                        context=code_content[:200] + "..."
                        if len(code_content) > 200
                        else code_content,
                    )
                )

        return items

    def _find_empty_sections(
        self, doc_path: Path, content: str, lines: list[str], doc_status: str
    ) -> list[IncompleteItem]:
        """Find sections with headings but no content."""
        items: list[IncompleteItem] = []

        # Find all headings, but filter out those inside code blocks
        all_headings = list(HEADING_PATTERN.finditer(content))

        # Track which character positions are inside code blocks
        in_code_positions = set()
        for code_match in re.finditer(r"```[\s\S]*?```", content):
            for pos in range(code_match.start(), code_match.end()):
                in_code_positions.add(pos)

        # Filter headings to only those outside code blocks
        headings = [h for h in all_headings if h.start() not in in_code_positions]

        for i, match in enumerate(headings):
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()
            heading_pos = match.end()

            # Find next heading of same or higher level
            next_heading_pos = len(content)

            for next_match in headings[i + 1 :]:
                next_level = len(next_match.group(1))
                if next_level <= heading_level:
                    next_heading_pos = next_match.start()
                    break

            # Extract content between headings
            section_content = content[heading_pos:next_heading_pos].strip()

            # Skip if section contains code block (considered valid content)
            if "```" in section_content:
                continue

            # Skip if section contains a list (bullet or numbered)
            if re.search(r"^\s*[-*+\d]\.*\s+", section_content, re.MULTILINE):
                continue

            # Skip if section contains any real text content (more than just whitespace)
            # Remove blank lines and check for actual content
            section_lines = [line for line in section_content.split("\n") if line.strip()]
            if section_lines:
                continue

            # Section is truly empty
            line_num = content[: match.start()].count("\n") + 1

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
