"""
Project Statistics Collector

Surfaces comprehensive project statistics for at-a-glance metrics,
providing structured data for humans and AI agents.

Statistics categories:
- Content Volume: Documents, words, lines by language
- Status Breakdown: Draft/Review/Final/Published counts
- Activity Metrics: Recent changes, contributors
- Quality Metrics: Readability, link health, translation coverage
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import yaml

from ..core.project import Project


@dataclass
class ContentStats:
    """Statistics about content volume."""

    total_documents: int = 0
    documents_by_language: dict[str, int] = field(default_factory=dict)
    documents_by_type: dict[str, int] = field(default_factory=dict)
    total_words: int = 0
    words_by_language: dict[str, int] = field(default_factory=dict)
    total_lines: int = 0
    largest_documents: list[tuple[str, int]] = field(default_factory=list)
    smallest_documents: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class StatusStats:
    """Statistics about document status."""

    by_status: dict[str, int] = field(default_factory=dict)
    approval_queue_size: int = 0
    average_days_in_status: dict[str, float] = field(default_factory=dict)


@dataclass
class ActivityStats:
    """Statistics about recent activity."""

    documents_modified_week: int = 0
    documents_modified_month: int = 0
    documents_created_week: int = 0
    documents_created_month: int = 0
    contributors: list[str] = field(default_factory=list)
    commit_count_week: int = 0
    commit_count_month: int = 0
    recent_changes: list[dict] = field(default_factory=list)


@dataclass
class QualityStats:
    """Statistics about content quality."""

    average_readability: float = 0.0
    link_health_percent: float = 100.0
    translation_coverage: dict[str, float] = field(default_factory=dict)
    issues_by_severity: dict[str, int] = field(default_factory=dict)


@dataclass
class ProjectStatistics:
    """Complete project statistics."""

    content: ContentStats = field(default_factory=ContentStats)
    status: StatusStats = field(default_factory=StatusStats)
    activity: ActivityStats = field(default_factory=ActivityStats)
    quality: QualityStats = field(default_factory=QualityStats)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "content": {
                "total_documents": self.content.total_documents,
                "documents_by_language": self.content.documents_by_language,
                "documents_by_type": self.content.documents_by_type,
                "total_words": self.content.total_words,
                "words_by_language": self.content.words_by_language,
                "total_lines": self.content.total_lines,
                "largest_documents": self.content.largest_documents,
                "smallest_documents": self.content.smallest_documents,
            },
            "status": {
                "by_status": self.status.by_status,
                "approval_queue_size": self.status.approval_queue_size,
            },
            "activity": {
                "documents_modified_week": self.activity.documents_modified_week,
                "documents_modified_month": self.activity.documents_modified_month,
                "documents_created_week": self.activity.documents_created_week,
                "documents_created_month": self.activity.documents_created_month,
                "contributors": self.activity.contributors,
                "commit_count_week": self.activity.commit_count_week,
                "commit_count_month": self.activity.commit_count_month,
                "recent_changes": self.activity.recent_changes,
            },
            "quality": {
                "average_readability": self.quality.average_readability,
                "link_health_percent": self.quality.link_health_percent,
                "translation_coverage": self.quality.translation_coverage,
                "issues_by_severity": self.quality.issues_by_severity,
            },
            "generated_at": self.generated_at.isoformat(),
        }

    def summary_line(self) -> str:
        """Generate a one-line summary."""
        return (
            f"{self.content.total_documents} docs, "
            f"{self.content.total_words:,} words, "
            f"{self.activity.documents_modified_week} modified this week"
        )


@dataclass
class StatisticsCollector:
    """
    Collects comprehensive project statistics.

    Usage:
        collector = StatisticsCollector(project)
        stats = collector.collect()
        print(f"Total documents: {stats.content.total_documents}")
    """

    project: Project

    def collect(self) -> ProjectStatistics:
        """
        Collect all project statistics.

        Returns:
            ProjectStatistics with all metrics populated
        """
        stats = ProjectStatistics()
        stats.generated_at = datetime.now()

        # Collect each category
        stats.content = self._collect_content_stats()
        stats.status = self._collect_status_stats()
        stats.activity = self._collect_activity_stats()
        stats.quality = self._collect_quality_stats()

        return stats

    def get_summary(self) -> dict:
        """Get a quick summary of key metrics."""
        stats = self.collect()
        return {
            "documents": stats.content.total_documents,
            "words": stats.content.total_words,
            "languages": len(stats.content.documents_by_language),
            "modified_this_week": stats.activity.documents_modified_week,
            "contributors": len(stats.activity.contributors),
            "draft_count": stats.status.by_status.get("draft", 0),
            "final_count": stats.status.by_status.get("final", 0),
        }

    def _collect_content_stats(self) -> ContentStats:
        """Collect content volume statistics."""
        stats = ContentStats()

        if not self.project.content_dir.exists():
            return stats

        doc_sizes: list[tuple[str, int]] = []

        for md_file in self.project.content_dir.rglob("*.md"):
            stats.total_documents += 1

            # Determine language from path
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                parts = rel_path.parts
                if len(parts) > 0:
                    # First directory is typically language
                    lang = parts[0] if len(parts) > 1 else "default"
                    stats.documents_by_language[lang] = (
                        stats.documents_by_language.get(lang, 0) + 1
                    )

                    # Content type from second directory
                    if len(parts) > 1:
                        content_type = parts[1] if len(parts) > 2 else "root"
                        stats.documents_by_type[content_type] = (
                            stats.documents_by_type.get(content_type, 0) + 1
                        )
            except ValueError:
                pass

            # Count words and lines
            try:
                content = md_file.read_text(encoding="utf-8")
                words = len(content.split())
                lines = content.count("\n") + 1

                stats.total_words += words
                stats.total_lines += lines

                # Track by language
                if len(parts) > 0:
                    lang = parts[0] if len(parts) > 1 else "default"
                    stats.words_by_language[lang] = (
                        stats.words_by_language.get(lang, 0) + words
                    )

                doc_sizes.append((str(rel_path), words))
            except (OSError, UnicodeDecodeError):
                pass

        # Sort for largest/smallest
        doc_sizes.sort(key=lambda x: x[1], reverse=True)
        stats.largest_documents = doc_sizes[:5]
        stats.smallest_documents = doc_sizes[-5:][::-1] if len(doc_sizes) >= 5 else []

        return stats

    def _collect_status_stats(self) -> StatusStats:
        """Collect document status statistics."""
        stats = StatusStats()

        if not self.project.content_dir.exists():
            return stats

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                frontmatter = self._parse_frontmatter(content)

                status = frontmatter.get("status", "draft")
                stats.by_status[status] = stats.by_status.get(status, 0) + 1

                # Count approval queue
                if status == "in_review":
                    stats.approval_queue_size += 1

            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                stats.by_status["unknown"] = stats.by_status.get("unknown", 0) + 1

        return stats

    def _collect_activity_stats(self) -> ActivityStats:
        """Collect activity statistics from git."""
        stats = ActivityStats()

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Try to get git activity
        try:
            # Get commits in last week
            result = subprocess.run(
                ["git", "log", "--oneline", f"--since={week_ago.isoformat()}", "--", "*.md"],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                stats.commit_count_week = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Get commits in last month
            result = subprocess.run(
                ["git", "log", "--oneline", f"--since={month_ago.isoformat()}", "--", "*.md"],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                stats.commit_count_month = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Get contributors
            result = subprocess.run(
                ["git", "log", "--format=%an", f"--since={month_ago.isoformat()}", "--", "*.md"],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                stats.contributors = list(set(result.stdout.strip().split("\n")))

            # Get recent changes
            result = subprocess.run(
                ["git", "log", "--name-only", "--format=%H|%an|%s|%aI", "-10", "--", "*.md"],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                stats.recent_changes = self._parse_git_log(result.stdout)

            # Count modified files in last week
            result = subprocess.run(
                ["git", "diff", "--name-only", f"--since={week_ago.isoformat()}", "HEAD~100", "HEAD", "--", "*.md"],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Fallback: check file modification times
            if self.project.content_dir.exists():
                for md_file in self.project.content_dir.rglob("*.md"):
                    try:
                        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                        if mtime > week_ago:
                            stats.documents_modified_week += 1
                        if mtime > month_ago:
                            stats.documents_modified_month += 1
                    except OSError:
                        pass

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # Git not available or not a git repo
            # Fall back to file modification times
            if self.project.content_dir.exists():
                for md_file in self.project.content_dir.rglob("*.md"):
                    try:
                        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                        if mtime > week_ago:
                            stats.documents_modified_week += 1
                        if mtime > month_ago:
                            stats.documents_modified_month += 1
                    except OSError:
                        pass

        return stats

    def _collect_quality_stats(self) -> QualityStats:
        """Collect quality statistics."""
        stats = QualityStats()

        # Try to get readability scores
        try:
            from ..readability import ReadabilityAnalyzer

            analyzer = ReadabilityAnalyzer(self.project)
            results = analyzer.analyze_project()
            if results:
                total_score = sum(r.flesch_reading_ease for r in results)
                stats.average_readability = total_score / len(results)
        except (ImportError, Exception):
            pass

        # Try to get translation coverage
        try:
            from ..cms import get_translation_status

            trans_status = get_translation_status(self.project)
            for lang, info in trans_status.items():
                if isinstance(info, dict):
                    total = info.get("total", 0)
                    translated = info.get("translated", 0)
                    if total > 0:
                        stats.translation_coverage[lang] = (translated / total) * 100
        except (ImportError, Exception):
            pass

        return stats

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}

        try:
            end_idx = content.index("---", 3)
            return yaml.safe_load(content[3:end_idx]) or {}
        except (ValueError, yaml.YAMLError):
            return {}

    def _parse_git_log(self, output: str) -> list[dict]:
        """Parse git log output into structured data."""
        changes = []
        current_commit = None

        for line in output.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    current_commit = {
                        "hash": parts[0],
                        "author": parts[1],
                        "message": parts[2],
                        "date": parts[3],
                        "files": [],
                    }
                    changes.append(current_commit)
            elif line.strip() and current_commit:
                current_commit["files"].append(line.strip())

        return changes


def collect_project_statistics(project: Project) -> ProjectStatistics:
    """Convenience function to collect project statistics."""
    collector = StatisticsCollector(project)
    return collector.collect()
