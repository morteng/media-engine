"""
Status Consistency Checker

Detects and flags documents where the declared status doesn't match the actual
content state, helping maintain accurate metadata.

Detection rules:
- Draft with complete content -> "Ready for review?"
- Final with TODO/TBD markers -> "Has incomplete markers"
- Final with missing sections -> "Incomplete content"
- In review unchanged for >14 days -> "Stale review"
- Approved with source changes -> "Needs re-approval"
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from ..core.project import Project
from .incomplete import IncompleteTracker


@dataclass
class ConsistencyIssue:
    """A detected status/content mismatch."""

    document: Path
    issue_type: str  # "status_mismatch", "stale_review", "needs_reapproval", "incomplete_final"
    declared: str  # Declared status
    detected: str  # Detected/suggested status
    confidence: float  # 0.0 - 1.0
    recommendation: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "issue_type": self.issue_type,
            "declared": self.declared,
            "detected": self.detected,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "details": self.details,
        }


# Completeness indicators
COMPLETENESS_SIGNALS = {
    "positive": [
        r"\b(?:example|sample|demo)\b",  # Has examples
        r"```[\w]*\n.+\n```",  # Has code blocks
        r"^\|.*\|.*\|$",  # Has tables
        r"^\s*[-*]\s+\w",  # Has bullet lists
        r"^\d+\.\s+\w",  # Has numbered lists
    ],
    "negative": [
        r"\bTODO\b",
        r"\bTBD\b",
        r"\bFIXME\b",
        r"\bcoming soon\b",
        r"\bplaceholder\b",
        r"\[insert\s+.+?\]",
    ],
}

# Minimum content thresholds
MIN_CONTENT_WORDS = 100
MIN_SECTIONS = 2


@dataclass
class ConsistencyChecker:
    """
    Checks for consistency between document status and content.

    Usage:
        checker = ConsistencyChecker(project)
        issues = checker.check_project()
        for issue in issues:
            print(f"{issue.document}: {issue.issue_type} - {issue.recommendation}")
    """

    project: Project
    stale_review_days: int = 14
    incomplete_tracker: Optional[IncompleteTracker] = None

    def __post_init__(self):
        if self.incomplete_tracker is None:
            self.incomplete_tracker = IncompleteTracker(self.project)

    def check_document(self, doc_path: Path) -> list[ConsistencyIssue]:
        """
        Check a single document for status/content consistency.

        Args:
            doc_path: Path to the document

        Returns:
            List of ConsistencyIssue instances
        """
        # Resolve path
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path
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

        issues: list[ConsistencyIssue] = []
        frontmatter, body = self._parse_frontmatter(content)

        declared_status = frontmatter.get("status", "draft")
        last_modified = self._get_last_modified(full_path)

        # Analyze content completeness
        completeness = self._analyze_completeness(body, doc_path)
        incomplete_items = self.incomplete_tracker.scan_document(doc_path)
        has_incomplete_markers = len(incomplete_items) > 0

        # Check: Draft that appears complete
        if declared_status == "draft" and completeness["score"] >= 0.8 and not has_incomplete_markers:
            issues.append(
                ConsistencyIssue(
                    document=doc_path,
                    issue_type="status_mismatch",
                    declared="draft",
                    detected="in_review",
                    confidence=completeness["score"],
                    recommendation="Document appears complete. Consider moving to 'in_review' status.",
                    details={
                        "word_count": completeness["word_count"],
                        "sections": completeness["sections"],
                        "has_examples": completeness["has_examples"],
                    },
                )
            )

        # Check: Final/published with incomplete markers
        if declared_status in ("final", "published", "approved") and has_incomplete_markers:
            high_priority = [i for i in incomplete_items if i.priority == "high"]
            issues.append(
                ConsistencyIssue(
                    document=doc_path,
                    issue_type="incomplete_final",
                    declared=declared_status,
                    detected="draft",
                    confidence=0.9,
                    recommendation=f"Document marked '{declared_status}' but has {len(incomplete_items)} incomplete markers.",
                    details={
                        "incomplete_count": len(incomplete_items),
                        "high_priority_count": len(high_priority),
                        "markers": [i.content for i in incomplete_items[:5]],
                    },
                )
            )

        # Check: Final with low completeness
        if declared_status in ("final", "published") and completeness["score"] < 0.5:
            issues.append(
                ConsistencyIssue(
                    document=doc_path,
                    issue_type="status_mismatch",
                    declared=declared_status,
                    detected="draft",
                    confidence=0.7,
                    recommendation=f"Document marked '{declared_status}' but appears incomplete (score: {completeness['score']:.0%}).",
                    details={
                        "completeness_score": completeness["score"],
                        "word_count": completeness["word_count"],
                        "missing": completeness.get("missing", []),
                    },
                )
            )

        # Check: Stale review
        if declared_status == "in_review" and last_modified:
            days_since_modified = (datetime.now() - last_modified).days
            if days_since_modified > self.stale_review_days:
                issues.append(
                    ConsistencyIssue(
                        document=doc_path,
                        issue_type="stale_review",
                        declared="in_review",
                        detected="in_review (stale)",
                        confidence=0.8,
                        recommendation=f"Document has been in review for {days_since_modified} days. Consider completing review or reverting to draft.",
                        details={
                            "days_in_review": days_since_modified,
                            "last_modified": last_modified.isoformat(),
                            "threshold_days": self.stale_review_days,
                        },
                    )
                )

        # Check: Approved but source changed (for translations)
        if declared_status == "approved":
            source_doc = frontmatter.get("source_document")
            source_version = frontmatter.get("source_version")
            if source_doc and source_version:
                # Check if source has newer version
                source_path = self.project.content_dir / source_doc
                if source_path.exists():
                    source_content = source_path.read_text(encoding="utf-8")
                    source_fm, _ = self._parse_frontmatter(source_content)
                    current_source_version = source_fm.get("version", "0.0.0")
                    if self._version_newer(current_source_version, source_version):
                        issues.append(
                            ConsistencyIssue(
                                document=doc_path,
                                issue_type="needs_reapproval",
                                declared="approved",
                                detected="needs_review",
                                confidence=0.95,
                                recommendation=f"Source document updated to v{current_source_version}. Translation approved for v{source_version} needs re-approval.",
                                details={
                                    "source_document": source_doc,
                                    "approved_version": source_version,
                                    "current_version": current_source_version,
                                },
                            )
                        )

        return issues

    def check_project(self) -> list[ConsistencyIssue]:
        """
        Check all documents in the project for consistency issues.

        Returns:
            List of all ConsistencyIssue instances
        """
        issues: list[ConsistencyIssue] = []

        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                issues.extend(self.check_document(md_file))

        # Sort by confidence (highest first)
        issues.sort(key=lambda x: (-x.confidence, str(x.document)))

        return issues

    def suggest_status(self, doc_path: Path) -> str:
        """
        Suggest the appropriate status for a document based on content analysis.

        Args:
            doc_path: Path to the document

        Returns:
            Suggested status string
        """
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path

        if not full_path.exists():
            return "draft"

        content = full_path.read_text(encoding="utf-8")
        frontmatter, body = self._parse_frontmatter(content)

        completeness = self._analyze_completeness(body, doc_path)
        incomplete_items = self.incomplete_tracker.scan_document(doc_path)

        if len(incomplete_items) > 0:
            return "draft"
        elif completeness["score"] >= 0.8:
            return "final"
        elif completeness["score"] >= 0.5:
            return "in_review"
        else:
            return "draft"

    def get_summary(self) -> dict:
        """Get a summary of consistency issues across the project."""
        issues = self.check_project()

        by_type: dict[str, int] = {}
        by_document: dict[str, int] = {}

        for issue in issues:
            by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1
            doc_key = str(issue.document)
            by_document[doc_key] = by_document.get(doc_key, 0) + 1

        return {
            "total": len(issues),
            "by_type": by_type,
            "documents_affected": len(by_document),
            "issues": [i.to_dict() for i in issues],
        }

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}, content

        try:
            end_idx = content.index("---", 3)
            frontmatter = yaml.safe_load(content[3:end_idx]) or {}
            body = content[end_idx + 3:].strip()
            return frontmatter, body
        except (ValueError, yaml.YAMLError):
            return {}, content

    def _get_last_modified(self, path: Path) -> Optional[datetime]:
        """Get the last modification time of a file."""
        try:
            stat = path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        except OSError:
            return None

    def _analyze_completeness(self, body: str, doc_path: Path) -> dict:
        """Analyze content completeness."""
        word_count = len(body.split())

        # Count sections (headings)
        sections = len(re.findall(r"^#{1,6}\s+.+$", body, re.MULTILINE))

        # Check for positive signals
        positive_signals = 0
        for pattern in COMPLETENESS_SIGNALS["positive"]:
            if re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
                positive_signals += 1

        # Check for negative signals
        negative_signals = 0
        for pattern in COMPLETENESS_SIGNALS["negative"]:
            if re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
                negative_signals += 1

        # Calculate completeness score
        score = 0.0
        missing = []

        # Word count contribution (40%)
        if word_count >= MIN_CONTENT_WORDS:
            score += 0.4
        else:
            score += 0.4 * (word_count / MIN_CONTENT_WORDS)
            missing.append(f"Low word count ({word_count}/{MIN_CONTENT_WORDS})")

        # Sections contribution (20%)
        if sections >= MIN_SECTIONS:
            score += 0.2
        else:
            score += 0.2 * (sections / MIN_SECTIONS)
            missing.append(f"Few sections ({sections}/{MIN_SECTIONS})")

        # Positive signals contribution (30%)
        max_positive = len(COMPLETENESS_SIGNALS["positive"])
        score += 0.3 * (positive_signals / max_positive)
        if positive_signals < 2:
            missing.append("Few examples or formatting")

        # Negative signals penalty (10%)
        if negative_signals == 0:
            score += 0.1
        else:
            score += 0.1 * max(0, 1 - negative_signals * 0.2)
            missing.append(f"{negative_signals} incomplete markers")

        return {
            "score": min(1.0, score),
            "word_count": word_count,
            "sections": sections,
            "has_examples": positive_signals >= 2,
            "has_incomplete": negative_signals > 0,
            "missing": missing,
        }

    def _version_newer(self, current: str, reference: str) -> bool:
        """Check if current version is newer than reference."""
        try:
            current_parts = [int(x) for x in current.split(".")]
            reference_parts = [int(x) for x in reference.split(".")]

            # Pad to same length
            max_len = max(len(current_parts), len(reference_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            reference_parts.extend([0] * (max_len - len(reference_parts)))

            return current_parts > reference_parts
        except (ValueError, AttributeError):
            return False


def check_project_consistency(project: Project) -> list[ConsistencyIssue]:
    """Convenience function to check project consistency."""
    checker = ConsistencyChecker(project)
    return checker.check_project()
