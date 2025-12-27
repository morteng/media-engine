"""
Background pre-processor for dashboard data.

Pre-computes expensive operations in the background and serves
cached results for instant UI response. Integrates with the file
watcher to invalidate cache incrementally.
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class CacheStatus(Enum):
    """Status of a cache entry."""
    FRESH = "fresh"       # Data is up-to-date
    STALE = "stale"       # Data needs refresh
    COMPUTING = "computing"  # Currently being computed
    ERROR = "error"       # Computation failed


@dataclass
class CacheEntry:
    """A cached computation result."""
    key: str
    data: Any
    status: CacheStatus
    computed_at: datetime
    computation_time_ms: float
    error: Optional[str] = None
    depends_on: set[str] = field(default_factory=set)  # Categories this depends on


class PreprocessorCache:
    """
    In-memory cache with optional disk persistence.

    Stores pre-computed results and tracks dependencies to know
    what to invalidate when files change.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cache_dir = project_root / ".media-engine" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._memory_cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # Track what categories each cache key depends on
        # When a category changes, invalidate all dependent keys
        self._category_deps: dict[str, set[str]] = {}

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry by key."""
        with self._lock:
            return self._memory_cache.get(key)

    def set(
        self,
        key: str,
        data: Any,
        depends_on: set[str] = None,
        computation_time_ms: float = 0,
    ) -> CacheEntry:
        """Store a cache entry."""
        with self._lock:
            entry = CacheEntry(
                key=key,
                data=data,
                status=CacheStatus.FRESH,
                computed_at=datetime.now(),
                computation_time_ms=computation_time_ms,
                depends_on=depends_on or set(),
            )
            self._memory_cache[key] = entry

            # Update category dependencies
            for category in (depends_on or set()):
                if category not in self._category_deps:
                    self._category_deps[category] = set()
                self._category_deps[category].add(key)

            return entry

    def mark_stale(self, key: str) -> None:
        """Mark a cache entry as stale."""
        with self._lock:
            if key in self._memory_cache:
                self._memory_cache[key].status = CacheStatus.STALE

    def mark_computing(self, key: str) -> None:
        """Mark a cache entry as being computed."""
        with self._lock:
            if key in self._memory_cache:
                self._memory_cache[key].status = CacheStatus.COMPUTING

    def set_error(self, key: str, error: str) -> None:
        """Mark a cache entry as errored."""
        with self._lock:
            if key in self._memory_cache:
                self._memory_cache[key].status = CacheStatus.ERROR
                self._memory_cache[key].error = error

    def invalidate_category(self, category: str) -> list[str]:
        """
        Invalidate all cache entries that depend on a category.

        Returns list of invalidated keys.
        """
        with self._lock:
            invalidated = []
            keys_to_invalidate = self._category_deps.get(category, set()).copy()

            for key in keys_to_invalidate:
                if key in self._memory_cache:
                    self._memory_cache[key].status = CacheStatus.STALE
                    invalidated.append(key)

            return invalidated

    def invalidate_all(self) -> None:
        """Mark all cache entries as stale."""
        with self._lock:
            for entry in self._memory_cache.values():
                entry.status = CacheStatus.STALE

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = len(self._memory_cache)
            by_status = {}
            for entry in self._memory_cache.values():
                status = entry.status.value
                by_status[status] = by_status.get(status, 0) + 1

            return {
                "total_entries": total,
                "by_status": by_status,
                "categories": list(self._category_deps.keys()),
            }

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._memory_cache.clear()
            self._category_deps.clear()


# Define what computations to pre-process and their dependencies
PREPROCESSOR_TASKS = {
    "health": {
        "depends_on": {"documents", "translations", "quality"},
        "priority": 1,  # Lower = higher priority
    },
    "statistics": {
        "depends_on": {"documents", "translations", "media"},
        "priority": 1,
    },
    "translations": {
        "depends_on": {"documents", "translations"},
        "priority": 2,
    },
    "quality": {
        "depends_on": {"documents", "quality"},
        "priority": 2,
    },
    "freshness": {
        "depends_on": {"documents", "freshness"},
        "priority": 2,
    },
    "incomplete": {
        "depends_on": {"documents"},
        "priority": 3,
    },
    "consistency": {
        "depends_on": {"documents"},
        "priority": 3,
    },
    "parity": {
        "depends_on": {"documents", "translations"},
        "priority": 3,
    },
    "graph": {
        "depends_on": {"documents"},
        "priority": 4,
    },
    "velocity": {
        "depends_on": {"documents", "project"},
        "priority": 5,
    },
    "terms": {
        "depends_on": {"documents"},
        "priority": 5,
    },
    "duplicates": {
        "depends_on": {"documents"},
        "priority": 5,
    },
    "project_status": {
        "depends_on": {"documents", "translations", "project", "quality"},
        "priority": 1,
    },
    # Advanced analytics tasks (expensive - lower priority)
    "semantic_analysis": {
        "depends_on": {"documents"},
        "priority": 6,
    },
    "knowledge_graph_enhanced": {
        "depends_on": {"documents"},
        "priority": 6,
    },
    "predictive_freshness": {
        "depends_on": {"documents", "freshness"},
        "priority": 7,
    },
    "enhanced_codesync": {
        "depends_on": {"documents"},
        "priority": 7,
    },
    "quality_summary": {
        "depends_on": {"documents", "translations", "quality", "freshness"},
        "priority": 2,  # High priority since it's on the main dashboard
    },
    "advanced_insights": {
        "depends_on": {"documents"},
        "priority": 8,  # Low priority - very expensive (~30 seconds)
    },
}


class BackgroundPreprocessor:
    """
    Background service that pre-computes expensive dashboard data.

    Integrates with file watcher to refresh only what changed.
    """

    def __init__(self, project: "Project"):
        self.project = project
        self.cache = PreprocessorCache(project.root)

        self._running = False
        self._task_queue: asyncio.Queue = None
        self._worker_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Track what needs refreshing
        self._pending_refreshes: set[str] = set()
        self._refresh_lock = threading.Lock()

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the background preprocessor."""
        self._loop = loop
        self._running = True
        self._task_queue = asyncio.Queue()

        # Start worker task
        self._worker_task = loop.create_task(self._worker())

        # Queue initial computation of all tasks
        self._queue_all_tasks()

        logger.info("Background preprocessor started")

    def stop(self) -> None:
        """Stop the background preprocessor."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
        logger.info("Background preprocessor stopped")

    def _queue_all_tasks(self) -> None:
        """Queue all preprocessor tasks for computation."""
        # Sort by priority
        sorted_tasks = sorted(
            PREPROCESSOR_TASKS.items(),
            key=lambda x: x[1]["priority"]
        )

        for task_name, _ in sorted_tasks:
            if self._loop and self._task_queue:
                self._loop.call_soon_threadsafe(
                    self._task_queue.put_nowait,
                    task_name
                )

    def on_file_change(self, categories: set[str]) -> None:
        """
        Handle file change notification from watcher.

        Invalidates relevant cache entries and queues refresh.
        """
        invalidated = set()

        # Map watcher categories to our categories
        category_mapping = {
            "en_chapters": "documents",
            "en_scripts": "documents",
            "no_chapters": {"documents", "translations"},
            "no_scripts": {"documents", "translations"},
            "config": "project",
            "brand": "brand",
            "registry": "freshness",
            "content": "documents",
            "other": "documents",
        }

        for cat in categories:
            mapped = category_mapping.get(cat, "documents")
            if isinstance(mapped, str):
                mapped = {mapped}

            for m in mapped:
                keys = self.cache.invalidate_category(m)
                invalidated.update(keys)

        # Queue refresh for invalidated keys
        if invalidated and self._loop and self._task_queue:
            # Sort by priority and queue
            sorted_tasks = sorted(
                [(k, PREPROCESSOR_TASKS.get(k, {"priority": 10})) for k in invalidated],
                key=lambda x: x[1]["priority"]
            )

            for task_name, _ in sorted_tasks:
                self._loop.call_soon_threadsafe(
                    self._task_queue.put_nowait,
                    task_name
                )

            logger.debug(f"Queued refresh for: {invalidated}")

    async def _worker(self) -> None:
        """Background worker that processes computation tasks."""
        while self._running:
            try:
                # Wait for a task with timeout
                try:
                    task_name = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Skip if already fresh
                entry = self.cache.get(task_name)
                if entry and entry.status == CacheStatus.FRESH:
                    continue

                # Skip if already computing
                if entry and entry.status == CacheStatus.COMPUTING:
                    continue

                # Compute the task
                await self._compute_task(task_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Preprocessor worker error: {e}")

    async def _compute_task(self, task_name: str) -> None:
        """Compute a single preprocessor task."""
        self.cache.mark_computing(task_name)
        start_time = time.time()

        try:
            # Run computation in thread pool to not block event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._compute_task_sync,
                task_name
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Store result
            task_config = PREPROCESSOR_TASKS.get(task_name, {})
            self.cache.set(
                task_name,
                result,
                depends_on=task_config.get("depends_on", set()),
                computation_time_ms=elapsed_ms,
            )

            logger.debug(f"Computed {task_name} in {elapsed_ms:.0f}ms")

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to compute {task_name}: {e}")
            self.cache.set_error(task_name, str(e))

    def _compute_task_sync(self, task_name: str) -> Any:
        """Synchronous computation of a task."""
        project = self.project

        if task_name == "health":
            from ..insights import HealthScorer
            scorer = HealthScorer(project)
            health = scorer.score_project()
            return health.to_dict()

        elif task_name == "statistics":
            from ..insights import StatisticsCollector
            collector = StatisticsCollector(project)
            stats = collector.collect()
            return stats.to_dict()

        elif task_name == "translations":
            from ..cms.translation import TranslationTracker
            tracker = TranslationTracker(project)
            statuses = tracker.get_all_statuses()
            return {
                "total": len(statuses),
                "statuses": [s.to_dict() for s in statuses],
            }

        elif task_name == "quality":
            from ..quality import run_quality_checks
            report = run_quality_checks(project, console_output=False)
            return {
                "total": len(report.issues),
                "errors": report.error_count,
                "warnings": report.warning_count,
                "issues": [
                    {
                        "type": i.type,
                        "severity": i.severity,
                        "file_path": str(i.file_path) if i.file_path else None,
                        "line": i.line,
                        "message": i.message,
                        "context": i.context,
                    }
                    for i in report.issues
                ],
            }

        elif task_name == "freshness":
            from ..freshness import FreshnessScanner
            scanner = FreshnessScanner(project)
            stale = scanner.find_stale(days=30)
            return {
                "stale_count": len(stale),
                "stale_items": [
                    {"path": str(s.path), "days_stale": s.days_since_update}
                    for s in stale[:50]
                ],
            }

        elif task_name == "incomplete":
            from ..insights import IncompleteTracker
            tracker = IncompleteTracker(project)
            items = tracker.scan_project()
            summary = tracker.get_summary()
            return {
                "total": summary["total"],
                "debt_score": summary["debt_score"],
                "items": [i.to_dict() for i in items[:20]],
            }

        elif task_name == "consistency":
            from ..insights import ConsistencyChecker
            checker = ConsistencyChecker(project)
            issues = checker.check_project()
            return {
                "total": len(issues),
                "issues": [i.to_dict() for i in issues[:20]],
            }

        elif task_name == "parity":
            from ..insights import ParityAnalyzer
            analyzer = ParityAnalyzer(project)
            report = analyzer.analyze()
            return report.to_dict()

        elif task_name == "graph":
            from ..insights import KnowledgeGraph
            graph = KnowledgeGraph(project)
            nodes, edges = graph.build_graph()
            hubs = graph.find_hubs()
            orphans = graph.find_orphans()
            return {
                "nodes": [n.to_dict() for n in nodes],
                "links": [e.to_dict() for e in edges],
                "hubs": len(hubs),
                "orphans": len(orphans),
            }

        elif task_name == "velocity":
            from ..insights import VelocityTracker
            tracker = VelocityTracker(project)
            metrics = tracker.get_metrics(days=30)
            return metrics.to_dict()

        elif task_name == "terms":
            from ..insights import TerminologyChecker
            checker = TerminologyChecker(project)
            issues = checker.find_inconsistencies()
            return {
                "total": len(issues),
                "issues": [i.to_dict() for i in issues[:20]],
            }

        elif task_name == "duplicates":
            from ..insights import DuplicateDetector
            detector = DuplicateDetector(project)
            report = detector.generate_report()
            matches = report.exact_duplicates + report.similar_content
            return {
                "total": len(matches),
                "matches": [m.to_dict() for m in matches[:20]],
            }

        elif task_name == "project_status":
            return project.get_status()

        elif task_name == "semantic_analysis":
            try:
                from ..semantic import SemanticAnalyzer
                analyzer = SemanticAnalyzer(project)
                dups = analyzer.find_near_duplicates(threshold=0.9)
                return {
                    "available": True,
                    "near_duplicates": len(dups),
                    "duplicates": [d.to_dict() for d in dups[:20]],
                }
            except ImportError:
                return {"available": False, "reason": "semantic module not installed"}
            except Exception as e:
                return {"available": True, "error": str(e)}

        elif task_name == "knowledge_graph_enhanced":
            try:
                from ..knowledge import KnowledgeGraph as EnhancedKG
                kg = EnhancedKG(project)
                kg.build()
                orphans = kg.find_orphan_concepts()
                return {
                    "available": True,
                    "orphan_count": len(orphans),
                    "orphans": orphans[:20] if orphans else [],
                    "node_count": kg.graph.number_of_nodes() if hasattr(kg, "graph") else 0,
                    "edge_count": kg.graph.number_of_edges() if hasattr(kg, "graph") else 0,
                }
            except ImportError as e:
                return {"available": False, "reason": f"networkx package required: {e}"}
            except Exception as e:
                return {"available": True, "error": str(e)}

        elif task_name == "predictive_freshness":
            try:
                from ..freshness.predictive import FreshnessPredictor
                predictor = FreshnessPredictor(project)
                predictor.train_from_history(days=60)
                predictions = predictor.predict_all()
                high_risk = [p for p in predictions if p.risk_level in ("high", "critical")]
                return {
                    "available": True,
                    "high_risk_count": len(high_risk),
                    "predictions": [
                        {
                            "path": str(p.path),
                            "risk_level": p.risk_level,
                            "staleness_probability": round(p.staleness_risk, 2),
                        }
                        for p in high_risk[:20]
                    ],
                }
            except ImportError:
                return {"available": False, "reason": "predictive freshness module not installed"}
            except Exception as e:
                return {"available": True, "error": str(e)}

        elif task_name == "enhanced_codesync":
            try:
                from ..codesync import EnhancedCodeSyncChecker
                checker = EnhancedCodeSyncChecker(project)
                report = checker.generate_summary()
                total_issues = report.get("total_issues", 0)
                return {
                    "available": True,
                    "total_issues": total_issues,
                    "summary": report,
                }
            except ImportError:
                return {"available": False, "reason": "codesync module not installed"}
            except Exception as e:
                return {"available": True, "error": str(e)}

        elif task_name == "quality_summary":
            # Comprehensive quality summary - aggregates multiple analyses
            from ..insights import HealthScorer
            summary = {
                "overall_score": 0,
                "grade": "N/A",
                "status": "unknown",
                "key_metrics": [],
                "critical_issues": [],
                "recommendations": [],
                "advanced_available": {
                    "semantic": False,
                    "knowledge_graph": False,
                    "norwegian_readability": False,
                    "predictive_freshness": False,
                    "enhanced_codesync": False,
                    "advanced_analysis": False,
                },
                "advanced_highlights": {},
            }

            # Core health score
            try:
                scorer = HealthScorer(project)
                health = scorer.score_project()
                summary["overall_score"] = health.overall
                summary["grade"] = health.grade
                summary["status"] = health.status
                summary["key_metrics"] = [
                    {"name": k, "score": v}
                    for k, v in health.components.items()
                ]
                summary["critical_issues"] = [
                    i.to_dict() for i in health.issues if i.severity == "critical"
                ][:5]
                summary["recommendations"] = health.recommendations[:5]
            except Exception as e:
                summary["health_error"] = str(e)

            # Use cached advanced analysis results if available
            semantic = self.cache.get("semantic_analysis")
            if semantic and semantic.status == CacheStatus.FRESH:
                summary["advanced_available"]["semantic"] = semantic.data.get("available", False)
                if semantic.data.get("near_duplicates", 0) > 0:
                    summary["advanced_highlights"]["semantic"] = {
                        "near_duplicates": semantic.data["near_duplicates"],
                        "message": f"Found {semantic.data['near_duplicates']} near-duplicate content pairs",
                    }

            kg = self.cache.get("knowledge_graph_enhanced")
            if kg and kg.status == CacheStatus.FRESH:
                summary["advanced_available"]["knowledge_graph"] = kg.data.get("available", False)
                if kg.data.get("orphan_count", 0) > 0:
                    summary["advanced_highlights"]["knowledge_graph"] = {
                        "orphan_concepts": kg.data["orphan_count"],
                        "message": f"Found {kg.data['orphan_count']} orphan concepts without connections",
                    }

            pf = self.cache.get("predictive_freshness")
            if pf and pf.status == CacheStatus.FRESH:
                summary["advanced_available"]["predictive_freshness"] = pf.data.get("available", False)
                if pf.data.get("high_risk_count", 0) > 0:
                    summary["advanced_highlights"]["predictive_freshness"] = {
                        "high_risk_count": pf.data["high_risk_count"],
                        "message": f"{pf.data['high_risk_count']} documents predicted to become stale soon",
                    }

            cs = self.cache.get("enhanced_codesync")
            if cs and cs.status == CacheStatus.FRESH:
                summary["advanced_available"]["enhanced_codesync"] = cs.data.get("available", False)
                if cs.data.get("total_issues", 0) > 0:
                    summary["advanced_highlights"]["enhanced_codesync"] = {
                        "issues": cs.data["total_issues"],
                        "message": f"{cs.data['total_issues']} code-documentation sync issues found",
                    }

            # Check module availability without running full analysis
            import importlib.util

            if importlib.util.find_spec("media_engine.readability.norwegian"):
                summary["advanced_available"]["norwegian_readability"] = True

            if importlib.util.find_spec("media_engine.advanced"):
                summary["advanced_available"]["advanced_analysis"] = True

            return summary

        else:
            raise ValueError(f"Unknown task: {task_name}")

    def get_cached(self, key: str, max_age_seconds: float = 300) -> Optional[Any]:
        """
        Get cached data if fresh enough.

        Returns None if cache miss or data is too old.
        """
        entry = self.cache.get(key)

        if not entry:
            return None

        if entry.status == CacheStatus.ERROR:
            return None

        # Check age
        age = (datetime.now() - entry.computed_at).total_seconds()
        if age > max_age_seconds:
            return None

        return entry.data

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any]) -> Any:
        """
        Get from cache or compute synchronously.

        This is a fallback for when we need data immediately.
        """
        # Try cache first
        entry = self.cache.get(key)
        if entry and entry.status == CacheStatus.FRESH:
            return entry.data

        # Compute synchronously
        start_time = time.time()
        result = compute_fn()
        elapsed_ms = (time.time() - start_time) * 1000

        # Cache the result
        task_config = PREPROCESSOR_TASKS.get(key, {})
        self.cache.set(
            key,
            result,
            depends_on=task_config.get("depends_on", set()),
            computation_time_ms=elapsed_ms,
        )

        return result

    def get_cache_stats(self) -> dict:
        """Get preprocessor cache statistics."""
        stats = self.cache.get_stats()

        # Add task-specific info
        task_status = {}
        for task_name in PREPROCESSOR_TASKS:
            entry = self.cache.get(task_name)
            if entry:
                task_status[task_name] = {
                    "status": entry.status.value,
                    "computed_at": entry.computed_at.isoformat(),
                    "computation_time_ms": entry.computation_time_ms,
                    "error": entry.error,
                }
            else:
                task_status[task_name] = {"status": "not_computed"}

        stats["tasks"] = task_status
        return stats


# Global instance
_preprocessor: Optional[BackgroundPreprocessor] = None


def get_preprocessor() -> Optional[BackgroundPreprocessor]:
    """Get the global preprocessor instance."""
    return _preprocessor


def start_preprocessor(
    project: "Project",
    loop: asyncio.AbstractEventLoop,
) -> BackgroundPreprocessor:
    """Start the global preprocessor."""
    global _preprocessor

    if _preprocessor:
        _preprocessor.stop()

    _preprocessor = BackgroundPreprocessor(project)
    _preprocessor.start(loop)
    return _preprocessor


def stop_preprocessor() -> None:
    """Stop the global preprocessor."""
    global _preprocessor
    if _preprocessor:
        _preprocessor.stop()
        _preprocessor = None
