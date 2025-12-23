"""Tests for insights module."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for insights testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "no" / "chapters").mkdir(parents=True)
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Insights Test Project",
        "description": "A test project for insights",
        "languages": ["en", "no"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample documents
    doc1 = content_dir / "en" / "chapters" / "01_intro.md"
    doc1.write_text("""---
title: Introduction
status: draft
version: 1.0.0
---

# Introduction

This is the introduction chapter with comprehensive content about the project.
It contains multiple sentences to enable readability analysis.
The text should be long enough to test various metrics.
""")

    doc2 = content_dir / "en" / "chapters" / "02_features.md"
    doc2.write_text("""---
title: Features
status: final
version: 2.0.0
---

# Features

This chapter describes features of the system.
We have many great features to discuss here.
""")

    # Create Norwegian translation
    trans1 = content_dir / "no" / "chapters" / "01_intro.md"
    trans1.write_text("""---
title: Introduksjon
language: "no"
source_document: en/chapters/01_intro.md
source_version: 1.0.0
---

# Introduksjon

Dette er introduksjonskapittelet med omfattende innhold om prosjektet.
Det inneholder flere setninger for å muliggjøre lesbarhetanalyse.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestHealthScorer:
    """Tests for HealthScorer."""

    def test_health_scorer_import(self):
        """Test HealthScorer can be imported."""
        from media_engine.insights import HealthScorer

        assert HealthScorer is not None

    def test_health_scorer_init(self, project):
        """Test HealthScorer initialization."""
        from media_engine.insights import HealthScorer

        scorer = HealthScorer(project)
        assert scorer is not None

    def test_score_project(self, project):
        """Test scoring project health."""
        from media_engine.insights import HealthScorer

        scorer = HealthScorer(project)
        score = scorer.score_project()

        assert hasattr(score, "overall")
        assert 0 <= score.overall <= 100


class TestConsistencyChecker:
    """Tests for ConsistencyChecker."""

    def test_consistency_checker_import(self):
        """Test ConsistencyChecker can be imported."""
        from media_engine.insights import ConsistencyChecker

        assert ConsistencyChecker is not None

    def test_consistency_checker_init(self, project):
        """Test ConsistencyChecker initialization."""
        from media_engine.insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        assert checker is not None

    def test_check_project(self, project):
        """Test running consistency checks."""
        from media_engine.insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        results = checker.check_project()

        assert isinstance(results, list)


class TestDuplicateDetector:
    """Tests for DuplicateDetector."""

    def test_duplicate_detector_import(self):
        """Test DuplicateDetector can be imported."""
        from media_engine.insights import DuplicateDetector

        assert DuplicateDetector is not None

    def test_duplicate_detector_init(self, project):
        """Test DuplicateDetector initialization."""
        from media_engine.insights import DuplicateDetector

        detector = DuplicateDetector(project)
        assert detector is not None

    def test_find_exact_duplicates(self, project):
        """Test detecting duplicates."""
        from media_engine.insights import DuplicateDetector

        detector = DuplicateDetector(project)
        duplicates = detector.find_exact_duplicates()

        assert isinstance(duplicates, list)


class TestTerminologyChecker:
    """Tests for TerminologyChecker."""

    def test_terminology_checker_import(self):
        """Test TerminologyChecker can be imported."""
        from media_engine.insights import TerminologyChecker

        assert TerminologyChecker is not None

    def test_terminology_checker_init(self, project):
        """Test TerminologyChecker initialization."""
        from media_engine.insights import TerminologyChecker

        checker = TerminologyChecker(project)
        assert checker is not None


class TestParityAnalyzer:
    """Tests for ParityAnalyzer."""

    def test_parity_analyzer_import(self):
        """Test ParityAnalyzer can be imported."""
        from media_engine.insights import ParityAnalyzer

        assert ParityAnalyzer is not None

    def test_parity_analyzer_init(self, project):
        """Test ParityAnalyzer initialization."""
        from media_engine.insights import ParityAnalyzer

        analyzer = ParityAnalyzer(project)
        assert analyzer is not None


class TestStatisticsCollector:
    """Tests for StatisticsCollector."""

    def test_statistics_collector_import(self):
        """Test StatisticsCollector can be imported."""
        from media_engine.insights import StatisticsCollector

        assert StatisticsCollector is not None

    def test_statistics_collector_init(self, project):
        """Test StatisticsCollector initialization."""
        from media_engine.insights import StatisticsCollector

        collector = StatisticsCollector(project)
        assert collector is not None

    def test_collect(self, project):
        """Test collecting statistics."""
        from media_engine.insights import StatisticsCollector

        collector = StatisticsCollector(project)
        stats = collector.collect()

        # Stats is a ProjectStatistics object with content attribute
        assert hasattr(stats, "content")
        assert hasattr(stats.content, "total_documents")


class TestIncompleteTracker:
    """Tests for IncompleteTracker."""

    def test_incomplete_tracker_import(self):
        """Test IncompleteTracker can be imported."""
        from media_engine.insights import IncompleteTracker

        assert IncompleteTracker is not None

    def test_incomplete_tracker_init(self, project):
        """Test IncompleteTracker initialization."""
        from media_engine.insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        assert tracker is not None

    def test_scan_project(self, project):
        """Test scanning for incomplete content."""
        from media_engine.insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()

        assert isinstance(items, list)


class TestVelocityTracker:
    """Tests for VelocityTracker."""

    def test_velocity_tracker_import(self):
        """Test VelocityTracker can be imported."""
        from media_engine.insights import VelocityTracker

        assert VelocityTracker is not None

    def test_velocity_tracker_init(self, project):
        """Test VelocityTracker initialization."""
        from media_engine.insights import VelocityTracker

        tracker = VelocityTracker(project)
        assert tracker is not None


class TestCodeSyncChecker:
    """Tests for CodeSyncChecker."""

    def test_codesync_checker_import(self):
        """Test CodeSyncChecker can be imported."""
        from media_engine.insights import CodeSyncChecker

        assert CodeSyncChecker is not None

    def test_codesync_checker_init(self, project):
        """Test CodeSyncChecker initialization."""
        from media_engine.insights import CodeSyncChecker

        checker = CodeSyncChecker(project)
        assert checker is not None


class TestPathGenerator:
    """Tests for PathGenerator."""

    def test_path_generator_import(self):
        """Test PathGenerator can be imported."""
        from media_engine.insights import PathGenerator

        assert PathGenerator is not None

    def test_path_generator_init(self, project):
        """Test PathGenerator initialization."""
        from media_engine.insights import PathGenerator

        generator = PathGenerator(project)
        assert generator is not None


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""

    def test_knowledge_graph_import(self):
        """Test KnowledgeGraph can be imported."""
        from media_engine.insights import KnowledgeGraph

        assert KnowledgeGraph is not None

    def test_knowledge_graph_init(self, project):
        """Test KnowledgeGraph initialization."""
        from media_engine.insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        assert graph is not None


class TestInsightsModule:
    """General tests for insights module."""

    def test_insights_all_exports(self):
        """Test all exports from insights module."""
        from media_engine import insights

        # Check main analyzers exist
        assert hasattr(insights, "HealthScorer")
        assert hasattr(insights, "ConsistencyChecker")
        assert hasattr(insights, "DuplicateDetector")
        assert hasattr(insights, "TerminologyChecker")
        assert hasattr(insights, "ParityAnalyzer")
        assert hasattr(insights, "StatisticsCollector")
        assert hasattr(insights, "IncompleteTracker")
        assert hasattr(insights, "VelocityTracker")
        assert hasattr(insights, "CodeSyncChecker")
        assert hasattr(insights, "PathGenerator")
        assert hasattr(insights, "KnowledgeGraph")
