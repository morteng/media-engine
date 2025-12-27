"""
Engagement Metrics Integration for Media Engine

Integrates user engagement data with content quality assessment:
- Import analytics from various sources (GA, Plausible, Fathom)
- Correlate quality metrics with user engagement
- Identify underperforming content
- Suggest content priorities based on usage

Engagement data helps answer: "Is high-quality content actually being used?"
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


class AnalyticsSource(str, Enum):
    """Supported analytics providers."""

    GOOGLE_ANALYTICS = "google_analytics"
    PLAUSIBLE = "plausible"
    FATHOM = "fathom"
    SIMPLE_ANALYTICS = "simple_analytics"
    UMAMI = "umami"
    MANUAL = "manual"  # Manually provided data


@dataclass
class PageMetrics:
    """Engagement metrics for a single page/document."""

    path: str
    page_views: int = 0
    unique_visitors: int = 0
    avg_time_on_page_seconds: float = 0.0
    bounce_rate: float = 0.0  # 0-100%
    exit_rate: float = 0.0  # 0-100%
    scroll_depth_avg: float = 0.0  # 0-100%
    search_appearances: int = 0  # Internal search hits
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "page_views": self.page_views,
            "unique_visitors": self.unique_visitors,
            "avg_time_on_page_seconds": round(self.avg_time_on_page_seconds, 1),
            "bounce_rate": round(self.bounce_rate, 1),
            "exit_rate": round(self.exit_rate, 1),
            "scroll_depth_avg": round(self.scroll_depth_avg, 1),
            "search_appearances": self.search_appearances,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


@dataclass
class SearchQuery:
    """A search query and its metrics."""

    query: str
    count: int
    click_count: int
    avg_position: float  # Average result position when shown
    no_results_count: int  # Times query returned no results


@dataclass
class EngagementScore:
    """Calculated engagement score for a document."""

    path: Path
    engagement_score: float  # 0-100
    engagement_level: str  # "high", "medium", "low", "very_low"
    quality_score: Optional[float]  # From health scorer if available
    quality_engagement_gap: float  # Difference between quality and engagement
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "engagement_score": round(self.engagement_score, 1),
            "engagement_level": self.engagement_level,
            "quality_score": round(self.quality_score, 1) if self.quality_score else None,
            "quality_engagement_gap": round(self.quality_engagement_gap, 1),
            "recommendations": self.recommendations,
        }


@dataclass
class ContentPriority:
    """Content priority based on engagement and quality."""

    path: Path
    priority_score: float  # Higher = more important
    priority_reason: str
    current_performance: str
    suggested_action: str

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "priority_score": round(self.priority_score, 2),
            "priority_reason": self.priority_reason,
            "current_performance": self.current_performance,
            "suggested_action": self.suggested_action,
        }


@dataclass
class EngagementReport:
    """Complete engagement analysis report."""

    source: AnalyticsSource
    period_start: datetime
    period_end: datetime
    total_page_views: int
    total_unique_visitors: int
    page_metrics: list[PageMetrics]
    engagement_scores: list[EngagementScore]
    content_priorities: list[ContentPriority]
    top_search_queries: list[dict]
    underperforming_content: list[dict]
    correlation_quality_engagement: Optional[float]

    def to_dict(self) -> dict:
        return {
            "source": self.source.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_page_views": self.total_page_views,
            "total_unique_visitors": self.total_unique_visitors,
            "page_metrics": [m.to_dict() for m in self.page_metrics[:20]],
            "engagement_scores": [s.to_dict() for s in self.engagement_scores],
            "content_priorities": [p.to_dict() for p in self.content_priorities[:20]],
            "top_search_queries": self.top_search_queries[:20],
            "underperforming_content": self.underperforming_content[:10],
            "correlation_quality_engagement": (
                round(self.correlation_quality_engagement, 3)
                if self.correlation_quality_engagement
                else None
            ),
        }


class AnalyticsImporter:
    """
    Imports analytics data from various sources.

    Each importer method takes source-specific config and returns
    standardized PageMetrics.
    """

    def import_google_analytics(
        self,
        credentials_path: str,
        property_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[PageMetrics]:
        """
        Import from Google Analytics 4.

        Requires: google-analytics-data package
        """
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                DateRange,
                Dimension,
                Metric,
                RunReportRequest,
            )
        except ImportError:
            raise ImportError("google-analytics-data required: pip install google-analytics-data")

        client = BetaAnalyticsDataClient.from_service_account_file(credentials_path)

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="totalUsers"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate"),
            ],
            date_ranges=[
                DateRange(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )
            ],
        )

        response = client.run_report(request)

        metrics = []
        for row in response.rows:
            metrics.append(
                PageMetrics(
                    path=row.dimension_values[0].value,
                    page_views=int(row.metric_values[0].value),
                    unique_visitors=int(row.metric_values[1].value),
                    avg_time_on_page_seconds=float(row.metric_values[2].value),
                    bounce_rate=float(row.metric_values[3].value) * 100,
                    period_start=start_date,
                    period_end=end_date,
                )
            )

        return metrics

    def import_plausible(
        self,
        site_id: str,
        api_key: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[PageMetrics]:
        """
        Import from Plausible Analytics.

        Uses Plausible API.
        """
        import urllib.parse
        import urllib.request

        base_url = "https://plausible.io/api/v1/stats/breakdown"

        params = {
            "site_id": site_id,
            "period": "custom",
            "date": f"{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')}",
            "property": "event:page",
            "metrics": "visitors,pageviews,bounce_rate,visit_duration",
        }

        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {api_key}")

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())

        metrics = []
        for result in data.get("results", []):
            metrics.append(
                PageMetrics(
                    path=result["page"],
                    page_views=result.get("pageviews", 0),
                    unique_visitors=result.get("visitors", 0),
                    avg_time_on_page_seconds=result.get("visit_duration", 0),
                    bounce_rate=result.get("bounce_rate", 0),
                    period_start=start_date,
                    period_end=end_date,
                )
            )

        return metrics

    def import_manual(self, data: list[dict]) -> list[PageMetrics]:
        """
        Import manually provided analytics data.

        Args:
            data: List of dicts with at least 'path' and 'page_views' keys

        Returns:
            List of PageMetrics
        """
        metrics = []
        for item in data:
            metrics.append(
                PageMetrics(
                    path=item.get("path", ""),
                    page_views=item.get("page_views", 0),
                    unique_visitors=item.get("unique_visitors", 0),
                    avg_time_on_page_seconds=item.get("avg_time_on_page", 0),
                    bounce_rate=item.get("bounce_rate", 0),
                    exit_rate=item.get("exit_rate", 0),
                    scroll_depth_avg=item.get("scroll_depth", 0),
                    search_appearances=item.get("search_appearances", 0),
                )
            )
        return metrics

    def import_from_json(self, json_path: Path) -> list[PageMetrics]:
        """Import from a JSON file."""
        with open(json_path) as f:
            data = json.load(f)
        return self.import_manual(data if isinstance(data, list) else data.get("pages", []))


class EngagementAnalyzer:
    """
    Analyzes engagement metrics in context of content quality.

    Usage:
        from media_engine.engagement import EngagementAnalyzer

        analyzer = EngagementAnalyzer(project)

        # Import analytics
        analyzer.import_analytics(
            source=AnalyticsSource.PLAUSIBLE,
            site_id="mysite.com",
            api_key="...",
        )

        # Or import from file
        analyzer.import_from_file("analytics.json")

        # Calculate engagement scores
        scores = analyzer.calculate_engagement_scores()

        # Find underperforming content
        underperforming = analyzer.find_underperforming_content()

        # Get content priorities
        priorities = analyzer.suggest_content_priorities()

        # Full report
        report = analyzer.generate_report()
    """

    def __init__(self, project):
        """
        Initialize engagement analyzer.

        Args:
            project: Media Engine project
        """
        self.project = project
        self.importer = AnalyticsImporter()
        self._page_metrics: list[PageMetrics] = []
        self._analytics_source: AnalyticsSource = AnalyticsSource.MANUAL
        self._period_start: Optional[datetime] = None
        self._period_end: Optional[datetime] = None

    def import_analytics(
        self,
        source: AnalyticsSource,
        start_date: datetime = None,
        end_date: datetime = None,
        **kwargs,
    ) -> None:
        """
        Import analytics from specified source.

        Args:
            source: Analytics provider
            start_date: Start of analysis period
            end_date: End of analysis period
            **kwargs: Provider-specific arguments
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        self._period_start = start_date
        self._period_end = end_date
        self._analytics_source = source

        if source == AnalyticsSource.GOOGLE_ANALYTICS:
            self._page_metrics = self.importer.import_google_analytics(
                credentials_path=kwargs["credentials_path"],
                property_id=kwargs["property_id"],
                start_date=start_date,
                end_date=end_date,
            )
        elif source == AnalyticsSource.PLAUSIBLE:
            self._page_metrics = self.importer.import_plausible(
                site_id=kwargs["site_id"],
                api_key=kwargs["api_key"],
                start_date=start_date,
                end_date=end_date,
            )
        elif source == AnalyticsSource.MANUAL:
            self._page_metrics = self.importer.import_manual(kwargs.get("data", []))

    def import_from_file(self, path: Path) -> None:
        """Import analytics from JSON file."""
        self._page_metrics = self.importer.import_from_json(path)
        self._analytics_source = AnalyticsSource.MANUAL
        self._period_start = datetime.now() - timedelta(days=30)
        self._period_end = datetime.now()

    def _match_analytics_to_docs(self) -> dict[str, PageMetrics]:
        """Match analytics paths to project documents."""
        matches = {}

        if not self.project.content_dir.exists():
            return matches

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                doc_path = str(rel_path)

                # Try various URL patterns
                possible_urls = [
                    f"/{doc_path}",
                    f"/{doc_path.replace('.md', '')}",
                    f"/{doc_path.replace('.md', '.html')}",
                    f"/docs/{doc_path}",
                    f"/docs/{doc_path.replace('.md', '')}",
                ]

                for url in possible_urls:
                    for metrics in self._page_metrics:
                        if metrics.path == url or metrics.path.rstrip("/") == url.rstrip("/"):
                            matches[doc_path] = metrics
                            break
                    if doc_path in matches:
                        break

            except (OSError, ValueError):
                pass

        return matches

    def calculate_engagement_scores(self) -> list[EngagementScore]:
        """
        Calculate engagement scores for all documents.

        Engagement score formula:
        - Page views (normalized): 30%
        - Time on page: 25%
        - Inverse bounce rate: 25%
        - Scroll depth: 20%
        """
        matches = self._match_analytics_to_docs()
        scores = []

        # Calculate max values for normalization
        max_views = max((m.page_views for m in self._page_metrics), default=1)
        max_time = max((m.avg_time_on_page_seconds for m in self._page_metrics), default=1)

        # Get quality scores if available
        quality_scores = {}
        try:
            from ..insights.health import HealthScorer

            scorer = HealthScorer(self.project)
            project_health = scorer.score_project()
            quality_scores = project_health.document_scores
        except Exception:
            pass

        for doc_path, metrics in matches.items():
            # Normalize components
            views_score = (metrics.page_views / max_views) * 100
            time_score = min(100, (metrics.avg_time_on_page_seconds / max(60, max_time)) * 100)
            bounce_score = 100 - metrics.bounce_rate
            scroll_score = metrics.scroll_depth_avg

            # Weighted average
            engagement = (
                views_score * 0.30 + time_score * 0.25 + bounce_score * 0.25 + scroll_score * 0.20
            )

            # Determine level
            if engagement >= 70:
                level = "high"
            elif engagement >= 50:
                level = "medium"
            elif engagement >= 25:
                level = "low"
            else:
                level = "very_low"

            # Get quality score
            quality = quality_scores.get(doc_path)
            gap = (quality - engagement) if quality else 0

            # Generate recommendations
            recommendations = []
            if metrics.bounce_rate > 60:
                recommendations.append("High bounce rate - improve content hook or structure")
            if metrics.avg_time_on_page_seconds < 30:
                recommendations.append("Low time on page - content may be too brief or unclear")
            if gap > 30:
                recommendations.append(
                    "Quality is high but engagement is low - improve discoverability"
                )
            elif gap < -30:
                recommendations.append(
                    "Popular but quality issues - prioritize content improvement"
                )

            scores.append(
                EngagementScore(
                    path=Path(doc_path),
                    engagement_score=engagement,
                    engagement_level=level,
                    quality_score=quality,
                    quality_engagement_gap=gap,
                    recommendations=recommendations,
                )
            )

        return sorted(scores, key=lambda x: -x.engagement_score)

    def find_underperforming_content(
        self,
        quality_threshold: float = 70,
        engagement_threshold: float = 30,
    ) -> list[dict]:
        """
        Find high-quality content with low engagement.

        These are documents that are well-written but not being read.
        """
        scores = self.calculate_engagement_scores()
        underperforming = []

        for score in scores:
            if score.quality_score and score.quality_score >= quality_threshold:
                if score.engagement_score < engagement_threshold:
                    underperforming.append(
                        {
                            "path": str(score.path),
                            "quality_score": score.quality_score,
                            "engagement_score": score.engagement_score,
                            "gap": score.quality_engagement_gap,
                            "issue": "High quality but low engagement",
                            "suggestions": [
                                "Improve internal linking",
                                "Add to navigation/TOC",
                                "Promote in related content",
                                "Improve SEO/discoverability",
                            ],
                        }
                    )

        return sorted(underperforming, key=lambda x: -x["gap"])

    def suggest_content_priorities(self) -> list[ContentPriority]:
        """
        Suggest content priorities based on engagement and quality.

        Priority matrix:
        - High engagement, low quality: Fix immediately (users seeing poor content)
        - High quality, low engagement: Promote (hidden gems)
        - Low quality, high engagement: Critical fix (popular but problematic)
        - Low quality, low engagement: Low priority (revisit later)
        """
        scores = self.calculate_engagement_scores()
        priorities = []

        for score in scores:
            quality = score.quality_score or 50
            engagement = score.engagement_score

            if engagement >= 50 and quality < 50:
                # Popular but poor quality - critical
                priority = 100
                reason = "High traffic, low quality"
                performance = f"Popular ({engagement:.0f}) but problematic (quality {quality:.0f})"
                action = "Immediate quality improvement needed"
            elif quality >= 70 and engagement < 30:
                # Hidden gem - promote
                priority = 80
                reason = "Quality content with low visibility"
                performance = f"Good quality ({quality:.0f}) but underutilized ({engagement:.0f})"
                action = "Improve discoverability and promotion"
            elif engagement >= 50 and quality >= 70:
                # Working well - maintain
                priority = 40
                reason = "Performing well"
                performance = f"Strong engagement ({engagement:.0f}) and quality ({quality:.0f})"
                action = "Maintain and monitor"
            else:
                # Low priority
                priority = 20
                reason = "Low impact content"
                performance = f"Low engagement ({engagement:.0f}) and quality ({quality:.0f})"
                action = "Consider archiving or major revision"

            priorities.append(
                ContentPriority(
                    path=score.path,
                    priority_score=priority,
                    priority_reason=reason,
                    current_performance=performance,
                    suggested_action=action,
                )
            )

        return sorted(priorities, key=lambda x: -x.priority_score)

    def correlate_quality_engagement(self) -> Optional[float]:
        """
        Calculate correlation between quality and engagement.

        Returns Pearson correlation coefficient (-1 to 1).
        """
        scores = self.calculate_engagement_scores()

        # Filter to scores with both values
        pairs = [
            (s.quality_score, s.engagement_score) for s in scores if s.quality_score is not None
        ]

        if len(pairs) < 5:
            return None

        # Calculate Pearson correlation
        n = len(pairs)
        sum_x = sum(p[0] for p in pairs)
        sum_y = sum(p[1] for p in pairs)
        sum_xy = sum(p[0] * p[1] for p in pairs)
        sum_x2 = sum(p[0] ** 2 for p in pairs)
        sum_y2 = sum(p[1] ** 2 for p in pairs)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def generate_report(self) -> EngagementReport:
        """Generate comprehensive engagement report."""
        return EngagementReport(
            source=self._analytics_source,
            period_start=self._period_start or datetime.now() - timedelta(days=30),
            period_end=self._period_end or datetime.now(),
            total_page_views=sum(m.page_views for m in self._page_metrics),
            total_unique_visitors=sum(m.unique_visitors for m in self._page_metrics),
            page_metrics=sorted(self._page_metrics, key=lambda x: -x.page_views),
            engagement_scores=self.calculate_engagement_scores(),
            content_priorities=self.suggest_content_priorities(),
            top_search_queries=[],  # Would come from search analytics
            underperforming_content=self.find_underperforming_content(),
            correlation_quality_engagement=self.correlate_quality_engagement(),
        )


def analyze_engagement(
    project,
    analytics_file: Path = None,
) -> EngagementReport:
    """Convenience function for engagement analysis."""
    analyzer = EngagementAnalyzer(project)

    if analytics_file and analytics_file.exists():
        analyzer.import_from_file(analytics_file)

    return analyzer.generate_report()


__all__ = [
    "EngagementAnalyzer",
    "AnalyticsImporter",
    "AnalyticsSource",
    "PageMetrics",
    "SearchQuery",
    "EngagementScore",
    "ContentPriority",
    "EngagementReport",
    "analyze_engagement",
]
