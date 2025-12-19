"""
Media Engine Insights Module

Comprehensive project intelligence and analytics for documentation health,
content quality, and actionable recommendations.

Key Features:
- Content Health Scoring: Aggregate quality metrics (0-100 scale)
- Incomplete Content Detection: TODO/TBD/FIXME scanning
- Status Consistency: Detect metadata/content mismatches
- Project Statistics: Document counts, activity, breakdowns
- Translation Parity: Cross-language coverage matrix
- Terminology Checking: Consistent term usage
- Duplicate Detection: Find similar/repeated content
- Content Velocity: Track documentation activity over time
- Code-Doc Sync: Detect stale references to code
- Knowledge Graph: Document relationships visualization
- Reading Paths: Auto-generated learning journeys

Usage:
    from media_engine.insights import HealthScorer, IncompleteTracker

    # Get project health score
    scorer = HealthScorer(project)
    health = scorer.score_project()
    print(f"Project health: {health.overall}/100")

    # Find incomplete content
    tracker = IncompleteTracker(project)
    items = tracker.scan_project()
    print(f"Found {len(items)} incomplete items")
"""

from .codesync import CodeReference, CodeSyncChecker, SyncStatus
from .consistency import ConsistencyChecker, ConsistencyIssue
from .duplicates import DuplicateDetector, DuplicateMatch
from .graph import GraphEdge, GraphNode, KnowledgeGraph
from .health import HealthIssue, HealthScore, HealthScorer
from .incomplete import IncompleteItem, IncompleteTracker
from .parity import ParityAnalyzer, ParityReport
from .paths import PathGenerator, PathNode, ReadingPath
from .statistics import ProjectStatistics, StatisticsCollector
from .terminology import TermInconsistency, TerminologyChecker
from .velocity import VelocityMetrics, VelocityTracker

__all__ = [
    # Incomplete content
    "IncompleteTracker",
    "IncompleteItem",
    # Consistency
    "ConsistencyChecker",
    "ConsistencyIssue",
    # Statistics
    "StatisticsCollector",
    "ProjectStatistics",
    # Health
    "HealthScorer",
    "HealthScore",
    "HealthIssue",
    # Parity
    "ParityAnalyzer",
    "ParityReport",
    # Terminology
    "TerminologyChecker",
    "TermInconsistency",
    # Duplicates
    "DuplicateDetector",
    "DuplicateMatch",
    # Velocity
    "VelocityTracker",
    "VelocityMetrics",
    # Code sync
    "CodeSyncChecker",
    "CodeReference",
    "SyncStatus",
    # Knowledge graph
    "KnowledgeGraph",
    "GraphNode",
    "GraphEdge",
    # Reading paths
    "PathGenerator",
    "ReadingPath",
    "PathNode",
]
