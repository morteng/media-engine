"""
Quality Check Implementations

Checks content for common issues:
- Placeholder markers (TODO, TBD, FIXME)
- Terminology consistency against glossary
- Norwegian encoding issues
- Empty sections
- Hierarchy structure issues
- Voice/tone consistency against brand profile
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import yaml
from rich import box
from rich.console import Console
from rich.table import Table

from ..settings.defaults import QUALITY as QUALITY_SETTINGS

if TYPE_CHECKING:
    from ..brand.voice import VoiceProfile
    from ..core.project import Project

console = Console()


@dataclass
class QualityIssue:
    """A quality issue found in content."""

    type: str  # placeholder, terminology, encoding, empty
    severity: str  # error, warning, info
    file_path: Path
    line: int
    message: str
    context: str = ""


@dataclass
class QualityReport:
    """Report of all quality issues."""

    issues: List[QualityIssue] = field(default_factory=list)
    files_checked: int = 0
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def add(self, issue: QualityIssue):
        self.issues.append(issue)
        if issue.severity == "error":
            self.passed = False


# Build pattern list with messages from centralized settings
def _build_placeholder_patterns():
    """Build placeholder patterns from settings with descriptive messages."""
    pattern_messages = {
        r"\bTODO\b": "TODO marker found",
        r"\bTBD\b": "TBD marker found",
        r"\bFIXME\b": "FIXME marker found",
        r"\bXXX\b": "XXX marker found",
        r"\[placeholder\]": "Placeholder marker",
        r"\[TBD\]": "TBD marker",
        r"\[TODO\]": "TODO marker",
        r"<placeholder>": "Placeholder marker",
        r"\$\{.*?\}": "Template variable not replaced",
        r"\{\{.*?\}\}": "Template variable not replaced",
    }
    # Use patterns from settings, falling back to defaults
    patterns = []
    for pattern in QUALITY_SETTINGS.placeholder_patterns:
        message = pattern_messages.get(pattern, f"Pattern matched: {pattern}")
        patterns.append((pattern, message))
    return patterns


PLACEHOLDER_PATTERNS = _build_placeholder_patterns()


def check_placeholders(
    content: str,
    file_path: Path,
) -> List[QualityIssue]:
    """
    Check content for placeholder markers.

    Args:
        content: File content
        file_path: Path to file

    Returns:
        List of issues found
    """
    issues = []
    lines = content.split("\n")
    in_code_block = False

    for line_num, line in enumerate(lines, 1):
        # Track code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Skip content inside code blocks
        if in_code_block:
            continue

        # Skip table rows that appear to be documenting patterns
        # (lines starting with | that contain pattern names in a table format)
        if line.strip().startswith("|") and re.search(r"\|\s*`?(TODO|TBD|FIXME|XXX)`?\s*\|", line):
            continue

        # Remove inline code before checking (content in backticks)
        line_without_code = re.sub(r"`[^`]+`", "", line)

        # Skip lines that are just listing/documenting placeholder types
        # e.g., "- **Placeholder markers**: TODO, TBD, FIXME"
        # These are descriptions, not actual placeholders
        # Includes Norwegian terms (can appear in compound words like "Plassholdermarkører")
        doc_pattern = r"(markers?|patterns?|detects?|checks?|found|flagged|markør|oppdager|sjekk)"
        if re.search(doc_pattern, line_without_code, re.IGNORECASE):
            # Check if line contains multiple placeholder words (documentation)
            placeholder_words = re.findall(
                r"\b(TODO|TBD|FIXME|XXX)\b", line_without_code, re.IGNORECASE
            )
            if len(placeholder_words) >= 2:
                continue

        for pattern, message in PLACEHOLDER_PATTERNS:
            matches = re.finditer(pattern, line_without_code, re.IGNORECASE)
            for match in matches:
                issues.append(
                    QualityIssue(
                        type="placeholder",
                        severity="warning",
                        file_path=file_path,
                        line=line_num,
                        message=message,
                        context=line.strip()[:80],
                    )
                )

    return issues


# Norwegian character patterns for encoding issues
NORWEGIAN_ISSUES = [
    # Mojibake patterns (UTF-8 read as Latin-1)
    (r"Ã¦", "æ", "Encoding issue: should be æ"),
    (r"Ã¸", "ø", "Encoding issue: should be ø"),
    (r"Ã¥", "å", "Encoding issue: should be å"),
    (r"Ã†", "Æ", "Encoding issue: should be Æ"),
    (r"Ã˜", "Ø", "Encoding issue: should be Ø"),
    (r"Ã…", "Å", "Encoding issue: should be Å"),
    # Common typos
    (r"\baa\b", "å", "Possible typo: aa → å"),
    (r"\boe\b", "ø", "Possible typo: oe → ø"),
    (r"\bae\b", "æ", "Possible typo: ae → æ"),
]


def check_encoding(
    content: str,
    file_path: Path,
    language: str = "no",
) -> List[QualityIssue]:
    """
    Check content for encoding issues.

    Args:
        content: File content
        file_path: Path to file
        language: Language code (checks Norwegian by default)

    Returns:
        List of issues found
    """
    if language not in ("no", "nb", "nn"):
        return []

    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Skip lines that are documentation examples (patterns inside backticks)
        # Remove inline code before checking
        line_without_code = re.sub(r"`[^`]+`", "", line)

        for pattern, replacement, message in NORWEGIAN_ISSUES:
            if re.search(pattern, line_without_code):
                issues.append(
                    QualityIssue(
                        type="encoding",
                        severity="error" if "Encoding" in message else "warning",
                        file_path=file_path,
                        line=line_num,
                        message=message,
                        context=line.strip()[:80],
                    )
                )

    return issues


def load_glossary(glossary_path: Path) -> Dict[str, str]:
    """Load terminology glossary from YAML."""
    if not glossary_path.exists():
        return {}

    with open(glossary_path) as f:
        data = yaml.safe_load(f) or {}

    terms = {}
    for term_data in data.get("terms", []):
        preferred = term_data.get("preferred", "")
        for variant in term_data.get("avoid", []):
            terms[variant.lower()] = preferred

    return terms


def check_terminology(
    content: str,
    file_path: Path,
    glossary: Dict[str, str],
) -> List[QualityIssue]:
    """
    Check content for terminology consistency.

    Args:
        content: File content
        file_path: Path to file
        glossary: Dictionary of {incorrect: correct} terms

    Returns:
        List of issues found
    """
    if not glossary:
        return []

    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Skip code blocks
        if line.strip().startswith("```"):
            continue

        line_lower = line.lower()
        for incorrect, correct in glossary.items():
            if incorrect in line_lower:
                issues.append(
                    QualityIssue(
                        type="terminology",
                        severity="info",
                        file_path=file_path,
                        line=line_num,
                        message=f'Use "{correct}" instead of "{incorrect}"',
                        context=line.strip()[:80],
                    )
                )

    return issues


def check_empty_sections(
    content: str,
    file_path: Path,
) -> List[QualityIssue]:
    """
    Check for empty sections (headers with no content).

    Args:
        content: File content
        file_path: Path to file

    Returns:
        List of issues found
    """
    issues = []
    lines = content.split("\n")

    prev_header_line = None
    prev_header_text = None
    prev_header_level = 0
    in_code_block = False

    for line_num, line in enumerate(lines, 1):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            # Code block delimiter counts as content - reset header tracking
            prev_header_line = None
            prev_header_text = None
            continue

        # Skip lines inside code blocks (comments like # can look like headers)
        if in_code_block:
            continue

        # Check if current line is a header
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if header_match:
            current_level = len(header_match.group(1))

            # If previous was a header and we're on another header at same or higher level,
            # the first was empty. But sub-headers (lower level) are valid content.
            if prev_header_line is not None and current_level <= prev_header_level:
                issues.append(
                    QualityIssue(
                        type="empty",
                        severity="warning",
                        file_path=file_path,
                        line=prev_header_line,
                        message="Empty section - no content after header",
                        context=prev_header_text,
                    )
                )

            prev_header_line = line_num
            prev_header_text = line.strip()
            prev_header_level = current_level

        elif line.strip() and not line.startswith("#"):
            # Non-empty, non-header content resets the check
            prev_header_line = None
            prev_header_text = None

    return issues


def check_hierarchy(
    project: "Project",
    include_staleness: bool = True,
) -> List[QualityIssue]:
    """
    Check hierarchy structure for issues.

    Args:
        project: Project to check
        include_staleness: Include staleness checks

    Returns:
        List of hierarchy-related quality issues
    """
    from ..hierarchy import HierarchyGraph, HierarchyValidator, StalenessChecker
    from ..hierarchy.anchors import AnchorRegistry

    issues: List[QualityIssue] = []

    try:
        graph = HierarchyGraph(project)
    except Exception:
        return issues

    # Run hierarchy validation
    validator = HierarchyValidator(graph)
    result = validator.validate_all()

    # Map hierarchy errors to quality issues
    # Errors that should block publishing
    CRITICAL_TYPES = {
        "circular_reference",
        "missing_parent",
        "invalid_derivation",
    }

    for error in result.errors:
        severity = "error" if error.error_type in CRITICAL_TYPES else "warning"
        issues.append(
            QualityIssue(
                type=f"hierarchy_{error.error_type}",
                severity=severity,
                file_path=error.document,
                line=0,  # Hierarchy issues are document-level
                message=error.message,
                context="",
            )
        )

    for warning in result.warnings:
        issues.append(
            QualityIssue(
                type=f"hierarchy_{warning.error_type}",
                severity="warning",
                file_path=warning.document,
                line=0,
                message=warning.message,
                context="",
            )
        )

    # Check staleness
    if include_staleness:
        checker = StalenessChecker(graph)
        staleness_report = checker.check_all()

        for stale_info in staleness_report.stale_documents:
            if stale_info.stale_reason:
                sources = ", ".join(str(s.name) for s in stale_info.stale_sources[:3])
                message = f"Document is stale: {stale_info.stale_reason.value}"
                if sources:
                    message += f" (sources: {sources})"

                issues.append(
                    QualityIssue(
                        type="hierarchy_stale",
                        severity="warning",
                        file_path=stale_info.document,
                        line=0,
                        message=message,
                        context="",
                    )
                )

    # Check anchor references
    anchor_reg = AnchorRegistry(graph.registry)
    anchor_reg.build()
    anchor_result = anchor_reg.validate_references()

    if not anchor_result.valid:
        for ref_doc, anchor_name, source_doc in anchor_result.missing_anchors:
            issues.append(
                QualityIssue(
                    type="hierarchy_missing_anchor",
                    severity="error",
                    file_path=ref_doc,
                    line=0,
                    message=f"References missing anchor '{anchor_name}' in {source_doc.name}",
                    context="",
                )
            )

        for ref_doc, anchor_name in anchor_result.orphan_references:
            issues.append(
                QualityIssue(
                    type="hierarchy_orphan_reference",
                    severity="error",
                    file_path=ref_doc,
                    line=0,
                    message=f"References anchor '{anchor_name}' from non-existent document",
                    context="",
                )
            )

        for ref_doc, anchor_name, expected, actual in anchor_result.value_mismatches:
            issues.append(
                QualityIssue(
                    type="hierarchy_anchor_mismatch",
                    severity="warning",
                    file_path=ref_doc,
                    line=0,
                    message=f"Anchor '{anchor_name}' expected {expected}, got {actual}",
                    context="",
                )
            )

    return issues


def check_voice(
    content: str,
    file_path: Path,
    voice_profile: Optional["VoiceProfile"] = None,
    doc_type: Optional[str] = None,
    audience: Optional[str] = None,
) -> List[QualityIssue]:
    """
    Check content against brand voice guidelines.

    Args:
        content: File content
        file_path: Path to file
        voice_profile: Brand voice profile to check against
        doc_type: Document type for context-specific rules
        audience: Target audience for context-specific rules

    Returns:
        List of voice-related quality issues
    """
    from ..brand.voice_checker import check_document_voice

    issues = []

    result = check_document_voice(
        content=content,
        doc_path=file_path,
        voice_profile=voice_profile,
        doc_type=doc_type,
        audience=audience,
    )

    # Convert voice issues to quality issues
    for voice_issue in result.issues:
        issues.append(
            QualityIssue(
                type=f"voice_{voice_issue.type}",
                severity=voice_issue.severity,
                file_path=file_path,
                line=0,  # Voice checks are document-level
                message=voice_issue.message,
                context=voice_issue.suggestion if voice_issue.suggestion else "",
            )
        )

    return issues


def run_quality_checks(
    project: "Project",
    console_output: bool = True,
    include_hierarchy: bool = True,
    include_voice: bool = True,
) -> QualityReport:
    """
    Run all quality checks on a project.

    Args:
        project: Project to check
        console_output: Whether to print results
        include_hierarchy: Include hierarchy structure checks
        include_voice: Include voice/tone consistency checks

    Returns:
        QualityReport with all issues
    """
    report = QualityReport()

    # Load glossary if exists
    glossary_path = project.root / "glossary.yaml"
    glossary = load_glossary(glossary_path)

    # Load voice profile if available
    voice_profile = None
    if include_voice:
        voice_profile = _load_voice_profile(project)

    # Check all content files
    for lang in project.languages:
        project.languages.get(lang)

        # Check chapters
        for chapter_path in project.list_chapters(lang):
            content = chapter_path.read_text()
            report.files_checked += 1

            # Placeholder check
            report.issues.extend(check_placeholders(content, chapter_path))

            # Encoding check
            report.issues.extend(check_encoding(content, chapter_path, lang))

            # Terminology check
            report.issues.extend(check_terminology(content, chapter_path, glossary))

            # Empty sections
            report.issues.extend(check_empty_sections(content, chapter_path))

            # Voice/tone check
            if include_voice and voice_profile:
                # Extract doc_type from frontmatter if available
                doc_type = _extract_doc_type(content)
                report.issues.extend(
                    check_voice(content, chapter_path, voice_profile, doc_type)
                )

    # Hierarchy checks (project-level)
    if include_hierarchy:
        hierarchy_issues = check_hierarchy(project)
        report.issues.extend(hierarchy_issues)

    # Update passed status
    report.passed = report.error_count == 0

    if console_output:
        print_quality_report(report)

    return report


def _load_voice_profile(project: "Project") -> Optional["VoiceProfile"]:
    """Load voice profile from brand.yaml if available."""
    try:
        from ..brand.loader import load_brand_profile

        brand = load_brand_profile(project.root)
        if brand and brand.voice:
            return brand.voice
    except Exception:
        pass  # Voice profile not available

    return None


def _extract_doc_type(content: str) -> Optional[str]:
    """Extract document type from frontmatter."""
    # Simple frontmatter extraction
    if content.startswith("---"):
        try:
            end = content.find("---", 3)
            if end > 0:
                frontmatter = yaml.safe_load(content[3:end])
                if isinstance(frontmatter, dict):
                    return frontmatter.get("type") or frontmatter.get("doc_type")
        except Exception:
            pass
    return None


def print_quality_report(report: QualityReport):
    """Print quality report to console."""
    if not report.issues:
        console.print(f"\n[green]✓ All {report.files_checked} files passed quality checks[/green]")
        return

    console.print("\n[bold]Quality Report[/bold]")
    console.print(f"Files checked: {report.files_checked}")
    console.print(
        f"Issues found: {len(report.issues)} ({report.error_count} errors, {report.warning_count} warnings)"
    )
    console.print()

    # Group by file
    issues_by_file: Dict[Path, List[QualityIssue]] = {}
    for issue in report.issues:
        if issue.file_path not in issues_by_file:
            issues_by_file[issue.file_path] = []
        issues_by_file[issue.file_path].append(issue)

    for file_path, file_issues in issues_by_file.items():
        console.print(f"[bold]{file_path.name}[/bold]")

        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Line", style="dim", width=6)
        table.add_column("Type", width=12)
        table.add_column("Message")

        for issue in file_issues:
            severity_color = {
                "error": "red",
                "warning": "yellow",
                "info": "blue",
            }.get(issue.severity, "white")

            table.add_row(
                str(issue.line),
                f"[{severity_color}]{issue.type}[/{severity_color}]",
                issue.message,
            )

        console.print(table)
        console.print()

    if report.passed:
        console.print("[green]✓ Quality checks passed (warnings only)[/green]")
    else:
        console.print(f"[red]✗ Quality checks failed ({report.error_count} errors)[/red]")
