"""
Predictive Freshness Analysis for Media Engine

Uses historical patterns and ML to predict content staleness:
- Learn from git history patterns
- Predict staleness risk before it happens
- Prioritize review based on predicted decay
- Factor in external dependencies and code changes

This is a proactive approach vs. reactive threshold-based detection.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


@dataclass
class DocumentHistory:
    """Historical data for a document."""

    path: Path
    creation_date: datetime
    last_modified: datetime
    modification_count: int
    avg_days_between_updates: float
    days_since_last_update: int
    has_code_references: bool
    referenced_code_changed: bool
    word_count: int
    link_count: int

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "creation_date": self.creation_date.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "modification_count": self.modification_count,
            "avg_days_between_updates": round(self.avg_days_between_updates, 1),
            "days_since_last_update": self.days_since_last_update,
            "has_code_references": self.has_code_references,
            "referenced_code_changed": self.referenced_code_changed,
            "word_count": self.word_count,
            "link_count": self.link_count,
        }


@dataclass
class StalenessPrediction:
    """Prediction of staleness risk for a document."""

    path: Path
    staleness_risk: float  # 0.0 - 1.0
    risk_level: str  # "low", "medium", "high", "critical"
    predicted_stale_date: Optional[datetime]
    days_until_stale: Optional[int]
    contributing_factors: list[str]
    confidence: float  # Model confidence 0-1
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "staleness_risk": round(self.staleness_risk, 3),
            "risk_level": self.risk_level,
            "predicted_stale_date": (
                self.predicted_stale_date.isoformat() if self.predicted_stale_date else None
            ),
            "days_until_stale": self.days_until_stale,
            "contributing_factors": self.contributing_factors,
            "confidence": round(self.confidence, 2),
            "recommendation": self.recommendation,
        }


@dataclass
class FreshnessPattern:
    """Detected freshness pattern for a document type."""

    document_type: str
    avg_lifetime_days: float
    update_frequency_days: float
    staleness_threshold_days: int
    sample_size: int

    def to_dict(self) -> dict:
        return {
            "document_type": self.document_type,
            "avg_lifetime_days": round(self.avg_lifetime_days, 1),
            "update_frequency_days": round(self.update_frequency_days, 1),
            "staleness_threshold_days": self.staleness_threshold_days,
            "sample_size": self.sample_size,
        }


@dataclass
class PredictiveFreshnessReport:
    """Complete predictive freshness report."""

    predictions: list[StalenessPrediction]
    patterns: list[FreshnessPattern]
    high_risk_count: int
    review_priority_queue: list[dict]  # Sorted by urgency
    model_accuracy: Optional[float]
    generated_at: datetime

    def to_dict(self) -> dict:
        return {
            "predictions": [p.to_dict() for p in self.predictions],
            "patterns": [p.to_dict() for p in self.patterns],
            "high_risk_count": self.high_risk_count,
            "review_priority_queue": self.review_priority_queue[:20],
            "model_accuracy": round(self.model_accuracy, 2) if self.model_accuracy else None,
            "generated_at": self.generated_at.isoformat(),
        }


class GitHistoryAnalyzer:
    """
    Analyzes git history for document patterns.

    Extracts:
    - Modification frequency
    - Update patterns
    - Co-change patterns with code
    """

    def __init__(self, project):
        self.project = project
        self._history_cache: dict[str, list[datetime]] = {}

    def get_document_history(self, doc_path: Path) -> Optional[DocumentHistory]:
        """Get historical data for a document."""
        import subprocess

        full_path = self.project.content_dir / doc_path

        if not full_path.exists():
            return None

        try:
            # Get git log for this file
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--format=%aI",  # ISO date
                    "--",
                    str(full_path),
                ],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return None

            # Parse dates
            dates = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        dates.append(datetime.fromisoformat(line.replace("Z", "+00:00")))
                    except ValueError:
                        pass

            if not dates:
                # Use file mtime
                mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                dates = [mtime]

            # Calculate metrics
            dates.sort()
            creation_date = dates[0]
            last_modified = dates[-1]
            modification_count = len(dates)

            if len(dates) > 1:
                intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_interval = sum(intervals) / len(intervals)
            else:
                avg_interval = 0

            days_since = (datetime.now() - last_modified).days

            # Check for code references
            content = full_path.read_text(encoding="utf-8")
            has_code_refs = bool(re.search(r"`[a-zA-Z_][a-zA-Z0-9_]+`", content))

            # Check if referenced code changed
            code_changed = self._check_code_references_changed(content, last_modified)

            return DocumentHistory(
                path=doc_path,
                creation_date=creation_date.replace(tzinfo=None),
                last_modified=last_modified.replace(tzinfo=None),
                modification_count=modification_count,
                avg_days_between_updates=avg_interval,
                days_since_last_update=days_since,
                has_code_references=has_code_refs,
                referenced_code_changed=code_changed,
                word_count=len(content.split()),
                link_count=len(re.findall(r"\[([^\]]+)\]\([^)]+\)", content)),
            )

        except Exception:
            return None

    def _check_code_references_changed(self, content: str, doc_modified: datetime) -> bool:
        """Check if any referenced code files changed after document."""
        import subprocess

        # Extract code file references
        code_refs = re.findall(r"`([a-zA-Z_][a-zA-Z0-9_/\.]+\.[a-z]+)`", content)

        for ref in code_refs:
            # Try to find the file
            possible_paths = [
                self.project.root / ref,
                self.project.root / "python" / ref,
                self.project.root / "src" / ref,
            ]

            for path in possible_paths:
                if path.exists():
                    try:
                        result = subprocess.run(
                            ["git", "log", "-1", "--format=%aI", "--", str(path)],
                            cwd=self.project.root,
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            code_date = datetime.fromisoformat(
                                result.stdout.strip().replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                            if code_date > doc_modified:
                                return True
                    except Exception:
                        pass
                    break

        return False

    def get_all_histories(self) -> list[DocumentHistory]:
        """Get history for all documents."""
        histories = []

        if not self.project.content_dir.exists():
            return histories

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                history = self.get_document_history(rel_path)
                if history:
                    histories.append(history)
            except (OSError, ValueError):
                pass

        return histories


class FreshnessPredictor:
    """
    Predicts content staleness using historical patterns.

    Features used for prediction:
    - Days since last update
    - Historical update frequency
    - Code reference changes
    - Document type patterns
    - Word count (larger docs = more likely to need updates)
    - External link count (more links = more dependencies)

    Usage:
        from media_engine.freshness.predictive import FreshnessPredictor

        predictor = FreshnessPredictor(project)
        predictor.train()  # Learn from history

        # Predict staleness for a document
        prediction = predictor.predict(doc_path)

        # Get priority queue
        queue = predictor.get_review_priority()

        # Full report
        report = predictor.generate_report()
    """

    # Default weights for prediction features
    DEFAULT_WEIGHTS = {
        "days_since_update": 0.25,
        "update_frequency_ratio": 0.20,
        "code_reference_change": 0.20,
        "document_type_pattern": 0.15,
        "content_size": 0.10,
        "external_dependencies": 0.10,
    }

    # Risk thresholds
    RISK_THRESHOLDS = {
        "low": 0.25,
        "medium": 0.50,
        "high": 0.75,
        "critical": 1.0,
    }

    def __init__(self, project, weights: dict = None):
        """
        Initialize freshness predictor.

        Args:
            project: Media Engine project
            weights: Custom feature weights (optional)
        """
        self.project = project
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.git_analyzer = GitHistoryAnalyzer(project)

        # Learned parameters
        self._patterns: dict[str, FreshnessPattern] = {}
        self._global_avg_lifetime = 90.0  # Default 90 days
        self._trained = False

    def train(self) -> None:
        """Learn freshness patterns from git history."""
        histories = self.git_analyzer.get_all_histories()

        if not histories:
            self._trained = True
            return

        # Group by document type (based on path patterns)
        by_type: dict[str, list[DocumentHistory]] = defaultdict(list)

        for history in histories:
            doc_type = self._classify_document_type(history.path)
            by_type[doc_type].append(history)

        # Calculate patterns per type
        for doc_type, type_histories in by_type.items():
            if len(type_histories) < 2:
                continue

            avg_lifetime = sum(h.days_since_last_update for h in type_histories) / len(
                type_histories
            )

            avg_frequency = sum(
                h.avg_days_between_updates for h in type_histories if h.avg_days_between_updates > 0
            )
            if avg_frequency:
                avg_frequency /= len([h for h in type_histories if h.avg_days_between_updates > 0])
            else:
                avg_frequency = 30.0

            # Staleness threshold = 2x average update frequency
            threshold = int(avg_frequency * 2)

            self._patterns[doc_type] = FreshnessPattern(
                document_type=doc_type,
                avg_lifetime_days=avg_lifetime,
                update_frequency_days=avg_frequency,
                staleness_threshold_days=threshold,
                sample_size=len(type_histories),
            )

        # Global average
        all_lifetimes = [h.days_since_last_update for h in histories]
        self._global_avg_lifetime = sum(all_lifetimes) / len(all_lifetimes)

        self._trained = True

    def _classify_document_type(self, path: Path) -> str:
        """Classify document into a type based on path."""
        path_str = str(path).lower()

        if "chapter" in path_str or "/ch" in path_str:
            return "chapter"
        elif "api" in path_str or "reference" in path_str:
            return "api_reference"
        elif "guide" in path_str or "tutorial" in path_str:
            return "tutorial"
        elif "readme" in path_str or "intro" in path_str:
            return "introduction"
        elif "script" in path_str:
            return "script"
        else:
            return "general"

    def predict(self, doc_path: Path) -> StalenessPrediction:
        """
        Predict staleness risk for a document.

        Args:
            doc_path: Path to document

        Returns:
            StalenessPrediction with risk score and factors
        """
        if not self._trained:
            self.train()

        history = self.git_analyzer.get_document_history(doc_path)

        if not history:
            return StalenessPrediction(
                path=doc_path,
                staleness_risk=0.5,
                risk_level="medium",
                predicted_stale_date=None,
                days_until_stale=None,
                contributing_factors=["No history available"],
                confidence=0.3,
                recommendation="Review document - no history available",
            )

        factors = []
        risk_components = []

        # Get type-specific pattern
        doc_type = self._classify_document_type(doc_path)
        pattern = self._patterns.get(doc_type)
        threshold = pattern.staleness_threshold_days if pattern else int(self._global_avg_lifetime)

        # 1. Days since update factor
        days_ratio = history.days_since_last_update / max(1, threshold)
        days_risk = min(1.0, days_ratio)
        risk_components.append(days_risk * self.weights["days_since_update"])

        if days_ratio > 1.5:
            factors.append(
                f"Not updated in {history.days_since_last_update} days (threshold: {threshold})"
            )
        elif days_ratio > 0.8:
            factors.append(
                f"Approaching update threshold ({history.days_since_last_update}/{threshold} days)"
            )

        # 2. Update frequency ratio
        if history.avg_days_between_updates > 0:
            freq_ratio = history.days_since_last_update / history.avg_days_between_updates
            freq_risk = min(1.0, (freq_ratio - 1) / 2) if freq_ratio > 1 else 0
            risk_components.append(freq_risk * self.weights["update_frequency_ratio"])

            if freq_ratio > 2:
                factors.append(
                    f"Overdue based on update pattern (usually every {history.avg_days_between_updates:.0f} days)"
                )

        # 3. Code reference changes
        if history.has_code_references:
            if history.referenced_code_changed:
                risk_components.append(1.0 * self.weights["code_reference_change"])
                factors.append("Referenced code has changed since last update")
            else:
                risk_components.append(0.0)
        else:
            risk_components.append(0.0)

        # 4. Document type pattern
        if pattern:
            type_risk = min(1.0, history.days_since_last_update / pattern.avg_lifetime_days)
            risk_components.append(type_risk * self.weights["document_type_pattern"])

            if type_risk > 1.0:
                factors.append(f"Older than typical {doc_type} document")

        # 5. Content size factor (larger docs need more frequent updates)
        size_risk = min(1.0, history.word_count / 2000) * 0.3
        risk_components.append(size_risk * self.weights["content_size"])

        # 6. External dependencies
        if history.link_count > 5:
            dep_risk = min(1.0, history.link_count / 20)
            risk_components.append(dep_risk * self.weights["external_dependencies"])
            if history.link_count > 10:
                factors.append(f"Many external dependencies ({history.link_count} links)")

        # Calculate total risk
        total_risk = min(1.0, sum(risk_components))

        # Determine risk level
        if total_risk < self.RISK_THRESHOLDS["low"]:
            risk_level = "low"
        elif total_risk < self.RISK_THRESHOLDS["medium"]:
            risk_level = "medium"
        elif total_risk < self.RISK_THRESHOLDS["high"]:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Predict stale date
        if total_risk < 1.0 and threshold > history.days_since_last_update:
            days_until = threshold - history.days_since_last_update
            predicted_date = datetime.now() + timedelta(days=days_until)
        else:
            days_until = 0
            predicted_date = datetime.now()

        # Generate recommendation
        if risk_level == "critical":
            recommendation = "Immediate review required - likely outdated"
        elif risk_level == "high":
            recommendation = "Schedule review soon - high staleness risk"
        elif risk_level == "medium":
            recommendation = "Monitor - approaching update threshold"
        else:
            recommendation = "No action needed - content appears fresh"

        # Calculate confidence based on data quality
        confidence = min(0.9, 0.5 + (history.modification_count * 0.05))

        if not factors:
            factors.append("Content appears up to date")

        return StalenessPrediction(
            path=doc_path,
            staleness_risk=total_risk,
            risk_level=risk_level,
            predicted_stale_date=predicted_date,
            days_until_stale=days_until,
            contributing_factors=factors,
            confidence=confidence,
            recommendation=recommendation,
        )

    def get_review_priority(self, top_n: int = 20) -> list[dict]:
        """
        Get prioritized review queue.

        Args:
            top_n: Number of documents to return

        Returns:
            List of documents sorted by urgency
        """
        predictions = []

        if not self.project.content_dir.exists():
            return predictions

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                prediction = self.predict(rel_path)
                predictions.append(
                    {
                        "path": str(rel_path),
                        "risk": prediction.staleness_risk,
                        "risk_level": prediction.risk_level,
                        "days_until_stale": prediction.days_until_stale,
                        "factors": prediction.contributing_factors,
                        "recommendation": prediction.recommendation,
                    }
                )
            except (OSError, ValueError):
                pass

        # Sort by risk (highest first)
        predictions.sort(key=lambda x: -x["risk"])

        return predictions[:top_n]

    def generate_report(self) -> PredictiveFreshnessReport:
        """Generate comprehensive predictive freshness report."""
        if not self._trained:
            self.train()

        predictions = []

        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                try:
                    rel_path = md_file.relative_to(self.project.content_dir)
                    prediction = self.predict(rel_path)
                    predictions.append(prediction)
                except (OSError, ValueError):
                    pass

        high_risk = sum(1 for p in predictions if p.risk_level in ("high", "critical"))

        priority_queue = self.get_review_priority(20)

        return PredictiveFreshnessReport(
            predictions=predictions,
            patterns=list(self._patterns.values()),
            high_risk_count=high_risk,
            review_priority_queue=priority_queue,
            model_accuracy=None,  # Would need historical validation data
            generated_at=datetime.now(),
        )


def predict_freshness(project) -> PredictiveFreshnessReport:
    """Convenience function for freshness prediction."""
    predictor = FreshnessPredictor(project)
    return predictor.generate_report()


__all__ = [
    "FreshnessPredictor",
    "GitHistoryAnalyzer",
    "DocumentHistory",
    "StalenessPrediction",
    "FreshnessPattern",
    "PredictiveFreshnessReport",
    "predict_freshness",
]
