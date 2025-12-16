"""
Quality assurance checks for documents.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from collections import Counter

from .document import Document, DocumentCollection


@dataclass
class QualityIssue:
    """Represents a quality issue found in a document."""
    category: str  # completeness, consistency, readability, links, terminology
    severity: str  # error, warning, info
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        loc = f":{self.line}" if self.line else ""
        return f"[{self.severity.upper()}] {self.category}{loc}: {self.message}"


@dataclass
class QualityReport:
    """Quality report for a document."""
    document_path: str
    issues: list[QualityIssue] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    def add_issue(
        self,
        category: str,
        severity: str,
        message: str,
        line: Optional[int] = None,
        suggestion: Optional[str] = None
    ) -> None:
        self.issues.append(QualityIssue(
            category=category,
            severity=severity,
            message=message,
            line=line,
            suggestion=suggestion
        ))


class QualityChecker:
    """Performs quality checks on documents."""

    # Common terminology that should be consistent
    TERMINOLOGY = {
        # Preferred term -> alternatives to flag
        "ROP": ["rop", "R.O.P."],
        "Kjøkkensjef": ["Kjokkensjef", "Kitchen Chef AI", "kitchen chef"],
        "multi-location": ["multilocation", "multi location"],
        "real-time": ["realtime", "real time"],
        "AI-first": ["AI first", "ai-first", "ai first"],
        "frontmatter": ["front-matter", "front matter"],
    }

    # Words that suggest incomplete content
    INCOMPLETE_MARKERS = [
        r'\bTODO\b',
        r'\bTBD\b',
        r'\bFIXME\b',
        r'\bXXX\b',
        r'\[placeholder\]',
        r'\{\{[^}]+\}\}',
        r'\[TBD\]',
        r'\[TODO\]',
        r'\.\.\.',  # Ellipsis that might indicate incomplete
        r'\[insert .+\]',
        r'\[add .+\]',
    ]

    # Jargon that should be defined in glossary
    TECHNICAL_JARGON = [
        "POS", "API", "SDK", "CMS", "CRUD", "webhook",
        "86'd", "frontmatter", "pgvector", "FastAPI",
    ]

    def __init__(self, docs_dir: Path, glossary: Optional[dict] = None):
        self.docs_dir = docs_dir
        self.glossary = glossary or {}

    def check_document(self, doc: Document) -> QualityReport:
        """Run all quality checks on a document."""
        report = QualityReport(document_path=str(doc.path))

        # Run all checks
        self._check_completeness(doc, report)
        self._check_consistency(doc, report)
        self._check_readability(doc, report)
        self._check_structure(doc, report)
        self._check_terminology(doc, report)
        self._check_links(doc, report)
        self._check_citations(doc, report)
        self._check_images(doc, report)

        # Calculate metrics
        report.metrics = self._calculate_metrics(doc)

        return report

    def check_collection(self, collection: DocumentCollection) -> dict[str, QualityReport]:
        """Run quality checks on all documents in a collection."""
        reports = {}
        for doc in collection.all_documents:
            reports[str(doc.path)] = self.check_document(doc)
        return reports

    def _check_completeness(self, doc: Document, report: QualityReport) -> None:
        """Check for incomplete content markers."""
        lines = doc.content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.INCOMPLETE_MARKERS:
                if re.search(pattern, line, re.IGNORECASE):
                    report.add_issue(
                        category="completeness",
                        severity="warning",
                        message=f"Incomplete content marker found: {line.strip()[:50]}",
                        line=i,
                        suggestion="Complete or remove placeholder content"
                    )
                    break

        # Check for empty sections
        for line_num, heading in doc.find_empty_sections():
            report.add_issue(
                category="completeness",
                severity="warning",
                message=f"Empty section: {heading}",
                line=line_num,
                suggestion="Add content or remove empty section"
            )

    def _check_consistency(self, doc: Document, report: QualityReport) -> None:
        """Check for consistency issues."""
        content = doc.content

        # Check title matches H1
        headings = doc.get_headings()
        h1_headings = [h for h in headings if h[1] == 1]
        if h1_headings:
            h1_text = h1_headings[0][2]
            if doc.title and h1_text != doc.title:
                report.add_issue(
                    category="consistency",
                    severity="warning",
                    message=f"Title mismatch: frontmatter '{doc.title}' vs H1 '{h1_text}'",
                    suggestion="Ensure frontmatter title matches document H1"
                )

        # Check heading hierarchy (no skipped levels)
        prev_level = 0
        for line_num, level, text in headings:
            if level > prev_level + 1:
                report.add_issue(
                    category="consistency",
                    severity="warning",
                    message=f"Skipped heading level: H{prev_level} to H{level}",
                    line=line_num,
                    suggestion=f"Use H{prev_level + 1} instead of H{level}"
                )
            prev_level = level

        # Check for inconsistent list markers
        bullet_types = re.findall(r'^(\s*)([*\-+])\s', content, re.MULTILINE)
        if bullet_types:
            markers = set(m[1] for m in bullet_types)
            if len(markers) > 1:
                report.add_issue(
                    category="consistency",
                    severity="info",
                    message=f"Mixed list markers used: {markers}",
                    suggestion="Use consistent list markers (prefer -)"
                )

    def _check_readability(self, doc: Document, report: QualityReport) -> None:
        """Check readability metrics."""
        # Calculate average sentence length
        # Remove code blocks first
        text = re.sub(r'```[\s\S]*?```', '', doc.content)
        text = re.sub(r'`[^`]+`', '', text)

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_words > 25:
                report.add_issue(
                    category="readability",
                    severity="info",
                    message=f"High average sentence length: {avg_words:.1f} words",
                    suggestion="Consider breaking long sentences for clarity"
                )

        # Check for very long paragraphs
        paragraphs = re.split(r'\n\n+', doc.content)
        for i, para in enumerate(paragraphs):
            if not para.startswith('#') and not para.startswith('```'):
                word_count = len(para.split())
                if word_count > 200:
                    report.add_issue(
                        category="readability",
                        severity="info",
                        message=f"Long paragraph ({word_count} words)",
                        suggestion="Consider breaking into smaller paragraphs"
                    )

    def _check_structure(self, doc: Document, report: QualityReport) -> None:
        """Check document structure."""
        headings = doc.get_headings()

        # Should have at least one H1
        h1_count = sum(1 for h in headings if h[1] == 1)
        if h1_count == 0:
            report.add_issue(
                category="structure",
                severity="error",
                message="Document has no H1 heading",
                suggestion="Add a main title with # at the start"
            )
        elif h1_count > 1:
            report.add_issue(
                category="structure",
                severity="warning",
                message=f"Document has {h1_count} H1 headings (should have 1)",
                suggestion="Use H2 for sections, keep single H1 for title"
            )

        # Should have some structure (at least H2s for chapters)
        if doc.doc_type == "chapter" and len(headings) < 3:
            report.add_issue(
                category="structure",
                severity="info",
                message="Document has minimal structure",
                suggestion="Consider adding more section headings"
            )

    def _check_terminology(self, doc: Document, report: QualityReport) -> None:
        """Check for terminology consistency."""
        content = doc.content
        lines = content.split('\n')

        for preferred, alternatives in self.TERMINOLOGY.items():
            for alt in alternatives:
                # Case-sensitive search for most
                pattern = r'\b' + re.escape(alt) + r'\b'
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        report.add_issue(
                            category="terminology",
                            severity="info",
                            message=f"Use '{preferred}' instead of '{alt}'",
                            line=i,
                            suggestion=f"Replace with standard term: {preferred}"
                        )

        # Check for undefined jargon (if glossary provided)
        if self.glossary:
            for jargon in self.TECHNICAL_JARGON:
                if jargon in content and jargon not in self.glossary:
                    report.add_issue(
                        category="terminology",
                        severity="info",
                        message=f"Technical term '{jargon}' not in glossary",
                        suggestion="Consider adding to glossary or explaining on first use"
                    )

    def _check_links(self, doc: Document, report: QualityReport) -> None:
        """Check internal links are valid."""
        links = doc.find_internal_links()

        for link in links:
            # Resolve link path relative to document
            if link.startswith('/'):
                link_path = self.docs_dir.parent / link[1:]
            else:
                link_path = doc.path.parent / link

            # Remove any anchor
            link_path = Path(str(link_path).split('#')[0])

            if not link_path.exists():
                report.add_issue(
                    category="links",
                    severity="error",
                    message=f"Broken link: {link}",
                    suggestion="Fix path or remove broken link"
                )

    def _check_citations(self, doc: Document, report: QualityReport) -> None:
        """Check citations match references."""
        citations = doc.find_citations()
        references = doc.references

        ref_ids = {r.get("id") for r in references if "id" in r}
        max_ref_id = max(ref_ids) if ref_ids else 0

        # Check for citations without references
        for cite_num in citations:
            if cite_num not in ref_ids:
                report.add_issue(
                    category="citations",
                    severity="error",
                    message=f"Citation [{cite_num}] has no reference in frontmatter",
                    suggestion="Add reference to frontmatter or remove citation"
                )

        # Check for unused references
        citation_set = set(citations)
        for ref in references:
            ref_id = ref.get("id")
            if ref_id and ref_id not in citation_set:
                report.add_issue(
                    category="citations",
                    severity="warning",
                    message=f"Reference [{ref_id}] '{ref.get('title', '')}' is not cited",
                    suggestion="Add citation or remove unused reference"
                )

    def _check_images(self, doc: Document, report: QualityReport) -> None:
        """Check image references are valid."""
        images = doc.find_images()

        for img_path in images:
            # Skip external URLs
            if img_path.startswith(('http://', 'https://')):
                continue

            # Resolve image path
            if img_path.startswith('/'):
                full_path = self.docs_dir.parent / img_path[1:]
            else:
                full_path = doc.path.parent / img_path

            if not full_path.exists():
                report.add_issue(
                    category="images",
                    severity="error",
                    message=f"Missing image: {img_path}",
                    suggestion="Generate image or fix path"
                )

    def _calculate_metrics(self, doc: Document) -> dict:
        """Calculate quality metrics for a document."""
        content = doc.content

        # Word count (excluding code)
        text = re.sub(r'```[\s\S]*?```', '', content)
        text = re.sub(r'`[^`]+`', '', text)
        words = len(text.split())

        # Heading count
        headings = doc.get_headings()

        # Code block count
        code_blocks = len(re.findall(r'```', content)) // 2

        # Table count
        tables = len(re.findall(r'^\|.+\|$', content, re.MULTILINE))

        # Image count
        images = len(doc.find_images())

        # Link count
        links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))

        return {
            "word_count": words,
            "heading_count": len(headings),
            "code_blocks": code_blocks,
            "tables": tables,
            "images": images,
            "links": links,
            "todos": len(doc.find_todos()),
        }


def generate_quality_summary(reports: dict[str, QualityReport]) -> str:
    """Generate a summary of quality reports."""
    lines = ["# Quality Report Summary", ""]

    total_errors = sum(r.error_count for r in reports.values())
    total_warnings = sum(r.warning_count for r in reports.values())
    passed = sum(1 for r in reports.values() if r.passed)

    lines.append(f"**Documents:** {len(reports)}")
    lines.append(f"**Passed:** {passed}/{len(reports)}")
    lines.append(f"**Total Errors:** {total_errors}")
    lines.append(f"**Total Warnings:** {total_warnings}")
    lines.append("")

    # Documents with errors
    if total_errors > 0:
        lines.append("## Documents with Errors")
        lines.append("")
        for path, report in reports.items():
            if report.error_count > 0:
                lines.append(f"### {Path(path).name}")
                for issue in report.issues:
                    if issue.severity == "error":
                        lines.append(f"- {issue}")
                lines.append("")

    # Top issues by category
    all_issues = []
    for report in reports.values():
        all_issues.extend(report.issues)

    if all_issues:
        category_counts = Counter(i.category for i in all_issues)
        lines.append("## Issues by Category")
        lines.append("")
        for category, count in category_counts.most_common():
            lines.append(f"- **{category}**: {count}")

    return "\n".join(lines)
