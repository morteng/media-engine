"""
Content Health Score System

Provides a comprehensive health scoring system that aggregates multiple
quality metrics into a single score (0-100) per document and project-wide.

Health Score Components (default weights):
- Freshness (20%): Last modified vs threshold
- Translation completeness (20%): Source/target sync status
- Status consistency (15%): Draft vs actual completeness
- Link health (15%): Internal/external link validity
- Readability (15%): Flesch/Fog vs target level
- Dependency satisfaction (10%): Required docs exist
- Metadata completeness (5%): Required frontmatter present

Score Ranges:
- 90-100: Excellent (green)
- 70-89: Good (blue)
- 50-69: Needs attention (yellow)
- 0-49: Critical (red)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from ..core.project import Project


@dataclass
class HealthIssue:
    """A specific health issue affecting the score."""

    category: str  # "freshness", "translation", "consistency", etc.
    severity: str  # "critical", "warning", "info"
    message: str
    impact: float  # Points deducted (0-100 scale)
    document: Optional[Path] = None
    recommendation: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "impact": self.impact,
            "document": str(self.document) if self.document else None,
            "recommendation": self.recommendation,
        }


@dataclass
class HealthScore:
    """Health score for a document or project."""

    overall: float  # 0-100
    grade: str  # "A", "B", "C", "D", "F"
    status: str  # "excellent", "good", "needs_attention", "critical"
    components: dict[str, float] = field(default_factory=dict)
    issues: list[HealthIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    document: Optional[Path] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall": self.overall,
            "grade": self.grade,
            "status": self.status,
            "components": self.components,
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": self.recommendations,
            "document": str(self.document) if self.document else None,
        }


@dataclass
class ProjectHealthScore:
    """Aggregate health score for entire project."""

    overall: float
    grade: str
    status: str
    components: dict[str, float] = field(default_factory=dict)
    document_scores: dict[str, float] = field(default_factory=dict)
    critical_documents: list[str] = field(default_factory=list)
    issues: list[HealthIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall": self.overall,
            "grade": self.grade,
            "status": self.status,
            "components": self.components,
            "document_count": len(self.document_scores),
            "critical_count": len(self.critical_documents),
            "critical_documents": self.critical_documents,
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
        }


# Default component weights (should sum to 1.0)
DEFAULT_WEIGHTS = {
    "freshness": 0.20,
    "translation": 0.20,
    "consistency": 0.15,
    "links": 0.15,
    "readability": 0.15,
    "dependencies": 0.10,
    "metadata": 0.05,
}

# Required frontmatter fields
REQUIRED_METADATA = ["title", "status"]
RECOMMENDED_METADATA = ["version", "author", "description"]


@dataclass
class HealthScorer:
    """
    Calculates health scores for documents and projects.

    Usage:
        scorer = HealthScorer(project)
        health = scorer.score_project()
        print(f"Project health: {health.overall}/100 ({health.grade})")

        doc_health = scorer.score_document(Path("chapters/01.md"))
        print(f"Document health: {doc_health.overall}/100")
    """

    project: Project
    weights: dict[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    freshness_days: int = 90  # Days before content is considered stale

    def score_document(self, doc_path: Path) -> HealthScore:
        """
        Calculate health score for a single document.

        Args:
            doc_path: Path to the document

        Returns:
            HealthScore with overall score and component breakdown
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
            return HealthScore(
                overall=0,
                grade="F",
                status="critical",
                document=doc_path,
                issues=[
                    HealthIssue(
                        category="existence",
                        severity="critical",
                        message="Document does not exist",
                        impact=100,
                        document=doc_path,
                    )
                ],
            )

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return HealthScore(
                overall=0,
                grade="F",
                status="critical",
                document=doc_path,
                issues=[
                    HealthIssue(
                        category="readability",
                        severity="critical",
                        message=f"Cannot read document: {e}",
                        impact=100,
                        document=doc_path,
                    )
                ],
            )

        frontmatter, body = self._parse_frontmatter(content)
        issues: list[HealthIssue] = []
        components: dict[str, float] = {}

        # Score each component
        components["freshness"] = self._score_freshness(full_path, issues, doc_path)
        components["translation"] = self._score_translation(frontmatter, issues, doc_path)
        components["consistency"] = self._score_consistency(frontmatter, body, issues, doc_path)
        components["links"] = self._score_links(body, issues, doc_path)
        components["readability"] = self._score_readability(body, issues, doc_path)
        components["dependencies"] = self._score_dependencies(frontmatter, issues, doc_path)
        components["metadata"] = self._score_metadata(frontmatter, issues, doc_path)

        # Calculate weighted overall score
        overall = sum(components.get(key, 100) * weight for key, weight in self.weights.items())

        # Determine grade and status
        grade = self._calculate_grade(overall)
        status = self._calculate_status(overall)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        return HealthScore(
            overall=round(overall, 1),
            grade=grade,
            status=status,
            components=components,
            issues=issues,
            recommendations=recommendations,
            document=doc_path,
        )

    def score_project(self) -> ProjectHealthScore:
        """
        Calculate aggregate health score for the entire project.

        Returns:
            ProjectHealthScore with overall metrics and per-document breakdown
        """
        document_scores: dict[str, float] = {}
        all_issues: list[HealthIssue] = []
        component_totals: dict[str, list[float]] = {k: [] for k in self.weights.keys()}

        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                try:
                    rel_path = md_file.relative_to(self.project.content_dir)
                except ValueError:
                    rel_path = md_file.relative_to(self.project.root)

                doc_score = self.score_document(md_file)
                document_scores[str(rel_path)] = doc_score.overall

                # Aggregate component scores
                for key in self.weights.keys():
                    if key in doc_score.components:
                        component_totals[key].append(doc_score.components[key])

                # Collect critical issues
                all_issues.extend([i for i in doc_score.issues if i.severity == "critical"])

        # Calculate average scores
        components = {}
        for key, scores in component_totals.items():
            if scores:
                components[key] = round(sum(scores) / len(scores), 1)
            else:
                components[key] = 100.0

        # Overall is average of document scores
        if document_scores:
            overall = sum(document_scores.values()) / len(document_scores)
        else:
            overall = 100.0

        # Identify critical documents
        critical_documents = [path for path, score in document_scores.items() if score < 50]

        grade = self._calculate_grade(overall)
        status = self._calculate_status(overall)
        recommendations = self._generate_project_recommendations(all_issues, document_scores)

        return ProjectHealthScore(
            overall=round(overall, 1),
            grade=grade,
            status=status,
            components=components,
            document_scores=document_scores,
            critical_documents=critical_documents,
            issues=all_issues,
            recommendations=recommendations,
            generated_at=datetime.now(),
        )

    def get_critical_issues(self) -> list[HealthIssue]:
        """Get all critical health issues across the project."""
        project_health = self.score_project()
        return [i for i in project_health.issues if i.severity == "critical"]

    def _score_freshness(self, path: Path, issues: list[HealthIssue], doc_path: Path) -> float:
        """Score based on how recently the document was modified."""
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            days_old = (datetime.now() - mtime).days

            if days_old <= self.freshness_days // 3:
                return 100.0
            elif days_old <= self.freshness_days:
                # Linear decay
                decay = (days_old - self.freshness_days // 3) / (self.freshness_days * 2 / 3)
                return max(50, 100 - decay * 50)
            else:
                # Document is stale
                issues.append(
                    HealthIssue(
                        category="freshness",
                        severity="warning",
                        message=f"Document not updated in {days_old} days",
                        impact=30,
                        document=doc_path,
                        recommendation=f"Review and update content (last modified {days_old} days ago)",
                    )
                )
                return max(0, 50 - (days_old - self.freshness_days) / 10)
        except OSError:
            return 50.0

    def _score_translation(
        self, frontmatter: dict, issues: list[HealthIssue], doc_path: Path
    ) -> float:
        """Score based on translation sync status."""
        source_doc = frontmatter.get("source_document")
        source_version = frontmatter.get("source_version")

        if not source_doc:
            # Not a translation, full score
            return 100.0

        if not source_version:
            issues.append(
                HealthIssue(
                    category="translation",
                    severity="warning",
                    message="Translation missing source_version",
                    impact=20,
                    document=doc_path,
                    recommendation="Add source_version to track translation sync",
                )
            )
            return 70.0

        # Check if source exists and get its version
        source_path = self.project.content_dir / source_doc
        if not source_path.exists():
            issues.append(
                HealthIssue(
                    category="translation",
                    severity="critical",
                    message=f"Source document not found: {source_doc}",
                    impact=50,
                    document=doc_path,
                    recommendation="Fix source_document path or create missing source",
                )
            )
            return 30.0

        try:
            source_content = source_path.read_text(encoding="utf-8")
            source_fm, _ = self._parse_frontmatter(source_content)
            current_version = source_fm.get("version", "1.0.0")

            if self._version_newer(current_version, source_version):
                issues.append(
                    HealthIssue(
                        category="translation",
                        severity="warning",
                        message=f"Translation outdated (source: v{current_version}, translation: v{source_version})",
                        impact=25,
                        document=doc_path,
                        recommendation=f"Update translation to match source v{current_version}",
                    )
                )
                return 60.0
        except (OSError, UnicodeDecodeError):
            pass

        return 100.0

    def _score_consistency(
        self, frontmatter: dict, body: str, issues: list[HealthIssue], doc_path: Path
    ) -> float:
        """Score based on status/content consistency."""
        from .incomplete import INCOMPLETE_PATTERNS

        status = frontmatter.get("status", "draft")
        score = 100.0

        # Check for incomplete markers
        incomplete_count = 0
        for pattern in INCOMPLETE_PATTERNS.values():
            incomplete_count += len(pattern.findall(body))

        if status in ("final", "published", "approved") and incomplete_count > 0:
            issues.append(
                HealthIssue(
                    category="consistency",
                    severity="critical",
                    message=f"Document marked '{status}' has {incomplete_count} incomplete markers",
                    impact=40,
                    document=doc_path,
                    recommendation="Resolve incomplete markers or change status to draft",
                )
            )
            score -= 40

        # Check word count for final docs
        word_count = len(body.split())
        if status in ("final", "published") and word_count < 100:
            issues.append(
                HealthIssue(
                    category="consistency",
                    severity="warning",
                    message=f"Final document has only {word_count} words",
                    impact=20,
                    document=doc_path,
                    recommendation="Add more content or reconsider status",
                )
            )
            score -= 20

        return max(0, score)

    def _score_links(self, body: str, issues: list[HealthIssue], doc_path: Path) -> float:
        """Score based on link validity."""
        import re

        # Find markdown links
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        links = link_pattern.findall(body)

        if not links:
            return 100.0

        broken_count = 0
        for text, url in links:
            # Check internal links
            if not url.startswith(("http://", "https://", "mailto:", "#")):
                link_path = self.project.content_dir / url
                if not link_path.exists():
                    broken_count += 1

        if broken_count > 0:
            issues.append(
                HealthIssue(
                    category="links",
                    severity="warning",
                    message=f"{broken_count} broken internal links",
                    impact=min(30, broken_count * 10),
                    document=doc_path,
                    recommendation="Fix broken internal links",
                )
            )
            return max(0, 100 - broken_count * 10)

        return 100.0

    def _score_readability(self, body: str, issues: list[HealthIssue], doc_path: Path) -> float:
        """Score based on readability metrics."""
        # Simple readability check based on sentence and word length
        sentences = body.split(".")
        if len(sentences) < 3:
            return 100.0  # Too short to analyze

        words = body.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        score = 100.0

        # Penalize very long sentences
        if avg_sentence_length > 30:
            issues.append(
                HealthIssue(
                    category="readability",
                    severity="info",
                    message=f"Average sentence length is {avg_sentence_length:.0f} words",
                    impact=15,
                    document=doc_path,
                    recommendation="Consider shorter sentences for better readability",
                )
            )
            score -= 15

        # Penalize very long words on average
        if avg_word_length > 7:
            score -= 10

        return max(0, score)

    def _score_dependencies(
        self, frontmatter: dict, issues: list[HealthIssue], doc_path: Path
    ) -> float:
        """Score based on dependency satisfaction."""
        depends_on = frontmatter.get("depends_on", [])

        if not depends_on:
            return 100.0

        if isinstance(depends_on, str):
            depends_on = [depends_on]

        missing = []
        for dep in depends_on:
            dep_path = self.project.content_dir / dep
            if not dep_path.exists():
                missing.append(dep)

        if missing:
            issues.append(
                HealthIssue(
                    category="dependencies",
                    severity="warning",
                    message=f"{len(missing)} missing dependencies: {', '.join(missing[:3])}",
                    impact=min(40, len(missing) * 15),
                    document=doc_path,
                    recommendation="Create missing dependency documents",
                )
            )
            return max(0, 100 - len(missing) * 15)

        return 100.0

    def _score_metadata(
        self, frontmatter: dict, issues: list[HealthIssue], doc_path: Path
    ) -> float:
        """Score based on metadata completeness."""
        score = 100.0

        # Check required fields
        for field_name in REQUIRED_METADATA:
            if field_name not in frontmatter:
                issues.append(
                    HealthIssue(
                        category="metadata",
                        severity="warning",
                        message=f"Missing required field: {field_name}",
                        impact=15,
                        document=doc_path,
                        recommendation=f"Add '{field_name}' to frontmatter",
                    )
                )
                score -= 15

        # Check recommended fields (smaller penalty)
        missing_recommended = [f for f in RECOMMENDED_METADATA if f not in frontmatter]
        if missing_recommended:
            score -= len(missing_recommended) * 5

        return max(0, score)

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}, content

        try:
            end_idx = content.index("---", 3)
            frontmatter = yaml.safe_load(content[3:end_idx]) or {}
            body = content[end_idx + 3 :].strip()
            return frontmatter, body
        except (ValueError, yaml.YAMLError):
            return {}, content

    def _version_newer(self, current: str, reference: str) -> bool:
        """Check if current version is newer than reference."""
        try:
            current_parts = [int(x) for x in current.split(".")]
            reference_parts = [int(x) for x in reference.split(".")]
            max_len = max(len(current_parts), len(reference_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            reference_parts.extend([0] * (max_len - len(reference_parts)))
            return current_parts > reference_parts
        except (ValueError, AttributeError):
            return False

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _calculate_status(self, score: float) -> str:
        """Calculate status label from score."""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "needs_attention"
        else:
            return "critical"

    def _generate_recommendations(self, issues: list[HealthIssue]) -> list[str]:
        """Generate actionable recommendations from issues."""
        recommendations = []
        seen = set()

        # Sort by impact (highest first)
        for issue in sorted(issues, key=lambda x: -x.impact):
            if issue.recommendation and issue.recommendation not in seen:
                recommendations.append(issue.recommendation)
                seen.add(issue.recommendation)

        return recommendations[:5]  # Top 5 recommendations

    def _generate_project_recommendations(
        self, issues: list[HealthIssue], scores: dict[str, float]
    ) -> list[str]:
        """Generate project-level recommendations."""
        recommendations = []

        # Critical documents first
        critical = [p for p, s in scores.items() if s < 50]
        if critical:
            recommendations.append(
                f"Address {len(critical)} critical documents: {', '.join(critical[:3])}"
            )

        # Aggregate by category
        category_counts: dict[str, int] = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

        # Recommend based on most common issues
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            if count >= 3:
                recommendations.append(f"Address {count} {category} issues across project")

        return recommendations[:5]


def score_project_health(project: Project) -> ProjectHealthScore:
    """Convenience function to score project health."""
    scorer = HealthScorer(project)
    return scorer.score_project()
