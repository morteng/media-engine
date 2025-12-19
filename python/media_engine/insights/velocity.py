"""
Content Velocity Metrics

Tracks how fast documentation is being updated, identifying active vs stagnant
areas and measuring documentation health over time.

Metrics:
- Commits per period
- Lines changed per period
- Documents modified per period
- Contributor analysis
- Area breakdown
"""

import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..core.project import Project


@dataclass
class Contributor:
    """A documentation contributor."""

    name: str
    email: str
    commits: int
    lines_added: int
    lines_removed: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "email": self.email,
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
        }


@dataclass
class AreaMetrics:
    """Metrics for a content area."""

    area: str
    commits: int
    lines_added: int
    lines_removed: int
    documents_modified: int
    trend: str  # "up", "down", "stable"
    trend_percent: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "area": self.area,
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "documents_modified": self.documents_modified,
            "trend": self.trend,
            "trend_percent": self.trend_percent,
        }


@dataclass
class VelocityMetrics:
    """Velocity metrics for a period."""

    period: str  # "week", "month", "quarter"
    start_date: datetime
    end_date: datetime
    commits: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    documents_modified: int = 0
    documents_created: int = 0
    top_contributors: list[Contributor] = field(default_factory=list)
    area_breakdown: dict[str, AreaMetrics] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "period": self.period,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "documents_modified": self.documents_modified,
            "documents_created": self.documents_created,
            "top_contributors": [c.to_dict() for c in self.top_contributors],
            "area_breakdown": {k: v.to_dict() for k, v in self.area_breakdown.items()},
        }


@dataclass
class VelocityTracker:
    """
    Tracks content velocity metrics from git history.

    Usage:
        tracker = VelocityTracker(project)
        metrics = tracker.get_metrics(days=30)
        print(f"Commits this month: {metrics.commits}")

        stagnant = tracker.get_stagnant_areas()
        print(f"Stagnant areas: {stagnant}")
    """

    project: Project

    def get_metrics(self, days: int = 30) -> VelocityMetrics:
        """
        Get velocity metrics for the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            VelocityMetrics for the period
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        period = "week" if days <= 7 else "month" if days <= 31 else "quarter"

        metrics = VelocityMetrics(
            period=period,
            start_date=start_date,
            end_date=end_date,
        )

        try:
            # Get commit count
            result = self._run_git(
                ["log", "--oneline", f"--since={start_date.isoformat()}", "--", "*.md"]
            )
            if result:
                metrics.commits = len([line for line in result.split("\n") if line.strip()])

            # Get detailed stats
            stats = self._get_detailed_stats(start_date)
            metrics.lines_added = stats["lines_added"]
            metrics.lines_removed = stats["lines_removed"]

            # Get modified documents
            result = self._run_git(
                ["log", "--name-only", "--format=", f"--since={start_date.isoformat()}", "--", "*.md"]
            )
            if result:
                files = set(line.strip() for line in result.split("\n") if line.strip())
                metrics.documents_modified = len(files)

            # Get contributors
            metrics.top_contributors = self._get_contributors(start_date)

            # Get area breakdown
            metrics.area_breakdown = self._get_area_breakdown(start_date, days)

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # Git not available
            pass

        return metrics

    def get_trend(self, periods: int = 6, period_days: int = 7) -> list[VelocityMetrics]:
        """
        Get velocity trend over multiple periods.

        Args:
            periods: Number of periods to analyze
            period_days: Days per period

        Returns:
            List of VelocityMetrics, oldest first
        """
        trends: list[VelocityMetrics] = []
        now = datetime.now()

        for i in range(periods - 1, -1, -1):
            end_date = now - timedelta(days=i * period_days)
            start_date = end_date - timedelta(days=period_days)

            period = "week" if period_days <= 7 else "month"

            metrics = VelocityMetrics(
                period=period,
                start_date=start_date,
                end_date=end_date,
            )

            try:
                result = self._run_git(
                    ["log", "--oneline",
                     f"--since={start_date.isoformat()}",
                     f"--until={end_date.isoformat()}",
                     "--", "*.md"]
                )
                if result:
                    metrics.commits = len([line for line in result.split("\n") if line.strip()])

            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

            trends.append(metrics)

        return trends

    def get_stagnant_areas(self, threshold_days: int = 90) -> list[str]:
        """
        Find content areas that haven't been updated.

        Args:
            threshold_days: Days without changes to be considered stagnant

        Returns:
            List of stagnant area paths
        """
        stagnant: list[str] = []
        threshold = datetime.now() - timedelta(days=threshold_days)

        if not self.project.content_dir.exists():
            return stagnant

        # Find all content directories
        areas: dict[str, datetime] = {}

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                if len(rel_path.parts) >= 2:
                    area = f"{rel_path.parts[0]}/{rel_path.parts[1]}"
                else:
                    area = rel_path.parts[0] if rel_path.parts else "root"

                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)

                if area not in areas or mtime > areas[area]:
                    areas[area] = mtime

            except (OSError, ValueError):
                pass

        # Find stagnant areas
        for area, last_modified in areas.items():
            if last_modified < threshold:
                stagnant.append(area)

        return stagnant

    def get_active_areas(self, threshold_commits: int = 5, days: int = 30) -> list[str]:
        """
        Find actively maintained content areas.

        Args:
            threshold_commits: Minimum commits to be considered active
            days: Period to analyze

        Returns:
            List of active area paths
        """
        active: list[str] = []
        start_date = datetime.now() - timedelta(days=days)

        try:
            result = self._run_git(
                ["log", "--name-only", "--format=",
                 f"--since={start_date.isoformat()}",
                 "--", "*.md"]
            )

            if result:
                area_counts: dict[str, int] = defaultdict(int)

                for line in result.split("\n"):
                    line = line.strip()
                    if line:
                        parts = Path(line).parts
                        if len(parts) >= 2:
                            area = f"{parts[0]}/{parts[1]}"
                            area_counts[area] += 1

                active = [area for area, count in area_counts.items()
                          if count >= threshold_commits]

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return active

    def get_contributor_stats(self, days: int = 30) -> list[Contributor]:
        """
        Get contributor statistics.

        Args:
            days: Period to analyze

        Returns:
            List of contributors sorted by commit count
        """
        return self._get_contributors(datetime.now() - timedelta(days=days))

    def _run_git(self, args: list[str]) -> Optional[str]:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    def _get_detailed_stats(self, since: datetime) -> dict[str, int]:
        """Get detailed line change statistics."""
        stats = {"lines_added": 0, "lines_removed": 0}

        result = self._run_git(
            ["log", "--numstat", "--format=",
             f"--since={since.isoformat()}",
             "--", "*.md"]
        )

        if result:
            for line in result.split("\n"):
                parts = line.split("\t")
                if len(parts) >= 2:
                    try:
                        added = int(parts[0]) if parts[0] != "-" else 0
                        removed = int(parts[1]) if parts[1] != "-" else 0
                        stats["lines_added"] += added
                        stats["lines_removed"] += removed
                    except ValueError:
                        pass

        return stats

    def _get_contributors(self, since: datetime) -> list[Contributor]:
        """Get contributor statistics."""
        contributors: dict[str, Contributor] = {}

        # Get commit counts per author
        result = self._run_git(
            ["log", "--format=%an|%ae",
             f"--since={since.isoformat()}",
             "--", "*.md"]
        )

        if result:
            for line in result.split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    name = parts[0].strip()
                    email = parts[1].strip() if len(parts) > 1 else ""

                    key = email or name
                    if key not in contributors:
                        contributors[key] = Contributor(
                            name=name,
                            email=email,
                            commits=0,
                            lines_added=0,
                            lines_removed=0,
                        )
                    contributors[key].commits += 1

        # Sort by commits
        return sorted(contributors.values(), key=lambda c: -c.commits)

    def _get_area_breakdown(self, since: datetime, days: int) -> dict[str, AreaMetrics]:
        """Get metrics breakdown by content area."""
        areas: dict[str, AreaMetrics] = {}

        # Get current period stats
        result = self._run_git(
            ["log", "--name-only", "--format=",
             f"--since={since.isoformat()}",
             "--", "*.md"]
        )

        if result:
            area_files: dict[str, set[str]] = defaultdict(set)

            for line in result.split("\n"):
                line = line.strip()
                if line:
                    parts = Path(line).parts
                    if len(parts) >= 2:
                        area = f"{parts[0]}/{parts[1]}"
                        area_files[area].add(line)

            # Get previous period for trend
            prev_since = since - timedelta(days=days)
            prev_result = self._run_git(
                ["log", "--name-only", "--format=",
                 f"--since={prev_since.isoformat()}",
                 f"--until={since.isoformat()}",
                 "--", "*.md"]
            )

            prev_counts: dict[str, int] = defaultdict(int)
            if prev_result:
                for line in prev_result.split("\n"):
                    line = line.strip()
                    if line:
                        parts = Path(line).parts
                        if len(parts) >= 2:
                            area = f"{parts[0]}/{parts[1]}"
                            prev_counts[area] += 1

            # Build metrics
            for area, files in area_files.items():
                current_count = len(files)
                prev_count = prev_counts.get(area, 0)

                if prev_count > 0:
                    trend_percent = ((current_count - prev_count) / prev_count) * 100
                else:
                    trend_percent = 100.0 if current_count > 0 else 0.0

                if trend_percent > 10:
                    trend = "up"
                elif trend_percent < -10:
                    trend = "down"
                else:
                    trend = "stable"

                areas[area] = AreaMetrics(
                    area=area,
                    commits=current_count,  # Approximation
                    lines_added=0,
                    lines_removed=0,
                    documents_modified=current_count,
                    trend=trend,
                    trend_percent=round(trend_percent, 1),
                )

        return areas


def get_velocity_metrics(project: Project, days: int = 30) -> VelocityMetrics:
    """Convenience function to get velocity metrics."""
    tracker = VelocityTracker(project)
    return tracker.get_metrics(days)
