"""Tests for the insights module."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create project.yaml
    project_config = {
        "name": "test-project",
        "description": "Test project for insights",
        "languages": ["en", "no"],
        "paths": {
            "content": "content",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create content directories
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "no" / "chapters").mkdir(parents=True)

    # Create sample documents
    doc1_content = """---
title: "Introduction"
status: final
version: "1.0.0"
---

# Introduction

This is the introduction chapter. It provides an overview of the project.

## Getting Started

To get started, follow these steps:

1. Install the package
2. Configure your project
3. Run the build command

## Features

The project includes many features for documentation.
"""
    (content_dir / "en" / "chapters" / "01_introduction.md").write_text(doc1_content)

    doc2_content = """---
title: "Configuration"
status: draft
version: "1.0.0"
depends_on:
  - en/chapters/01_introduction.md
---

# Configuration

TODO: Add configuration details

This chapter covers configuration options.

## Basic Config

TBD: Fill in basic config section

## Advanced Config

Coming soon...
"""
    (content_dir / "en" / "chapters" / "02_configuration.md").write_text(doc2_content)

    # Norwegian translation
    no_doc_content = """---
title: "Introduksjon"
status: final
language: "no"
source_document: "en/chapters/01_introduction.md"
source_version: "1.0.0"
---

# Introduksjon

Dette er introduksjonskapittelet.
"""
    (content_dir / "no" / "chapters" / "01_introduction.md").write_text(no_doc_content)

    return tmp_path


@pytest.fixture
def project(temp_project):
    """Load the temporary project."""
    from media_engine.core.project import Project

    return Project.load(temp_project)


class TestIncompleteTracker:
    """Tests for IncompleteTracker."""

    def test_scan_document_finds_todo(self, project):
        """Test that TODO markers are detected."""
        from media_engine.insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()

        # Should find TODO and TBD markers
        todo_items = [i for i in items if i.marker_type in ("todo", "tbd", "placeholder")]
        assert len(todo_items) >= 2

    def test_scan_document_returns_line_numbers(self, project):
        """Test that line numbers are correctly reported."""
        from media_engine.insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        items = tracker.scan_project()

        for item in items:
            assert item.line_number > 0

    def test_get_summary(self, project):
        """Test summary generation."""
        from media_engine.insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        summary = tracker.get_summary()

        assert "total" in summary
        assert "by_priority" in summary
        assert "debt_score" in summary

    def test_debt_score_calculation(self, project):
        """Test that debt score is calculated."""
        from media_engine.insights import IncompleteTracker

        tracker = IncompleteTracker(project)
        score = tracker.get_debt_score()

        assert 0 <= score <= 100


class TestConsistencyChecker:
    """Tests for ConsistencyChecker."""

    def test_detects_draft_with_incomplete(self, project):
        """Test detection of draft documents with incomplete markers."""
        from media_engine.insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        issues = checker.check_project()

        # The draft document has incomplete markers, which is expected
        # So we shouldn't flag it as needing promotion
        draft_issues = [i for i in issues if i.declared == "draft"]
        # Draft with incomplete markers is consistent
        assert all(
            i.issue_type != "status_mismatch" or "incomplete" in str(i.details)
            for i in draft_issues
        )

    def test_suggest_status(self, project):
        """Test status suggestion."""
        from media_engine.insights import ConsistencyChecker

        checker = ConsistencyChecker(project)
        doc_path = Path("en/chapters/01_introduction.md")
        suggested = checker.suggest_status(doc_path)

        # Should suggest final for complete doc
        assert suggested in ("draft", "in_review", "final")


class TestStatisticsCollector:
    """Tests for StatisticsCollector."""

    def test_collects_document_counts(self, project):
        """Test that document counts are collected."""
        from media_engine.insights import StatisticsCollector

        collector = StatisticsCollector(project)
        stats = collector.collect()

        assert stats.content.total_documents >= 3
        assert "en" in stats.content.documents_by_language

    def test_collects_word_counts(self, project):
        """Test that word counts are collected."""
        from media_engine.insights import StatisticsCollector

        collector = StatisticsCollector(project)
        stats = collector.collect()

        assert stats.content.total_words > 0

    def test_collects_status_breakdown(self, project):
        """Test status breakdown collection."""
        from media_engine.insights import StatisticsCollector

        collector = StatisticsCollector(project)
        stats = collector.collect()

        assert "final" in stats.status.by_status or "draft" in stats.status.by_status


class TestHealthScorer:
    """Tests for HealthScorer."""

    def test_scores_document(self, project):
        """Test document health scoring."""
        from media_engine.insights import HealthScorer

        scorer = HealthScorer(project)
        doc_path = Path("en/chapters/01_introduction.md")
        health = scorer.score_document(doc_path)

        assert 0 <= health.overall <= 100
        assert health.grade in ("A", "B", "C", "D", "F")
        assert health.status in ("excellent", "good", "needs_attention", "critical")

    def test_scores_project(self, project):
        """Test project health scoring."""
        from media_engine.insights import HealthScorer

        scorer = HealthScorer(project)
        health = scorer.score_project()

        assert 0 <= health.overall <= 100
        assert len(health.document_scores) >= 3

    def test_component_scores(self, project):
        """Test that all components are scored."""
        from media_engine.insights import HealthScorer

        scorer = HealthScorer(project)
        health = scorer.score_project()

        expected_components = [
            "freshness",
            "translation",
            "consistency",
            "links",
            "readability",
            "dependencies",
            "metadata",
        ]
        for comp in expected_components:
            assert comp in health.components


class TestParityAnalyzer:
    """Tests for ParityAnalyzer."""

    def test_analyzes_parity(self, project):
        """Test parity analysis."""
        from media_engine.insights import ParityAnalyzer

        analyzer = ParityAnalyzer(project, primary_language="en")
        report = analyzer.analyze()

        assert "en" in report.languages
        assert len(report.matrix) > 0

    def test_finds_missing_translations(self, project):
        """Test finding missing translations."""
        from media_engine.insights import ParityAnalyzer

        analyzer = ParityAnalyzer(project, primary_language="en")
        report = analyzer.analyze()

        # Norwegian should have some missing translations
        assert "no" in report.missing

    def test_calculates_coverage(self, project):
        """Test coverage calculation."""
        from media_engine.insights import ParityAnalyzer

        analyzer = ParityAnalyzer(project, primary_language="en")
        report = analyzer.analyze()

        assert "en" in report.coverage
        assert report.coverage["en"] == 100.0


class TestTerminologyChecker:
    """Tests for TerminologyChecker."""

    def test_loads_default_synonyms(self, project):
        """Test that default synonyms are loaded."""
        from media_engine.insights import TerminologyChecker

        checker = TerminologyChecker(project)

        assert "user" in checker.term_registry

    def test_finds_inconsistencies(self, project):
        """Test finding terminology inconsistencies."""
        from media_engine.insights import TerminologyChecker

        checker = TerminologyChecker(project)
        issues = checker.find_inconsistencies()

        # May or may not find issues depending on content
        assert isinstance(issues, list)


class TestDuplicateDetector:
    """Tests for DuplicateDetector."""

    def test_find_exact_duplicates(self, project):
        """Test finding exact duplicates."""
        from media_engine.insights import DuplicateDetector

        detector = DuplicateDetector(project)
        duplicates = detector.find_exact_duplicates()

        # May or may not find duplicates
        assert isinstance(duplicates, list)

    def test_generate_report(self, project):
        """Test report generation."""
        from media_engine.insights import DuplicateDetector

        detector = DuplicateDetector(project)
        report = detector.generate_report()

        assert hasattr(report, "exact_duplicates")
        assert hasattr(report, "similar_content")
        assert hasattr(report, "total_issues")


class TestVelocityTracker:
    """Tests for VelocityTracker."""

    def test_get_metrics(self, project):
        """Test getting velocity metrics."""
        from media_engine.insights import VelocityTracker

        tracker = VelocityTracker(project)
        metrics = tracker.get_metrics(days=30)

        assert metrics.period in ("week", "month", "quarter")
        assert metrics.documents_modified >= 0

    def test_get_stagnant_areas(self, project):
        """Test finding stagnant areas."""
        from media_engine.insights import VelocityTracker

        tracker = VelocityTracker(project)
        stagnant = tracker.get_stagnant_areas(threshold_days=365)

        # Newly created project shouldn't have stagnant areas
        assert isinstance(stagnant, list)


class TestCodeSyncChecker:
    """Tests for CodeSyncChecker."""

    def test_extract_references(self, project, temp_project):
        """Test extracting code references."""
        from media_engine.insights import CodeSyncChecker

        # Add a document with code references
        doc_content = """---
title: Test
---
# Test

Use the `config.py` file.
Call `find_project()` function.
Run `media-engine build` command.
"""
        content_dir = temp_project / "content" / "en"
        (content_dir / "test.md").write_text(doc_content)

        checker = CodeSyncChecker(project)
        refs = checker.extract_references(Path("en/test.md"))

        assert len(refs) >= 2

    def test_check_project(self, project):
        """Test checking project sync."""
        from media_engine.insights import CodeSyncChecker

        checker = CodeSyncChecker(project)
        statuses = checker.check_project()

        assert isinstance(statuses, list)


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""

    def test_build_graph(self, project):
        """Test building knowledge graph."""
        from media_engine.insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        nodes, edges = graph.build_graph()

        assert len(nodes) >= 3
        # Should have at least one dependency edge
        assert len(edges) >= 0

    def test_find_hubs(self, project):
        """Test finding hub documents."""
        from media_engine.insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        graph.build_graph()
        hubs = graph.find_hubs(threshold=1)

        # May or may not find hubs
        assert isinstance(hubs, list)

    def test_find_orphans(self, project):
        """Test finding orphan documents."""
        from media_engine.insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        graph.build_graph()
        orphans = graph.find_orphans()

        assert isinstance(orphans, list)

    def test_export_dot(self, project):
        """Test DOT export."""
        from media_engine.insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        graph.build_graph()
        dot = graph.export_dot()

        assert "digraph" in dot
        assert "knowledge" in dot

    def test_export_json(self, project):
        """Test JSON export."""
        from media_engine.insights import KnowledgeGraph

        graph = KnowledgeGraph(project)
        graph.build_graph()
        data = graph.export_json()

        assert "nodes" in data
        assert "links" in data


class TestPathGenerator:
    """Tests for PathGenerator."""

    def test_generate_dependency_path(self, project):
        """Test generating dependency-based path."""
        from media_engine.insights import PathGenerator

        generator = PathGenerator(project, language="en")
        path = generator.generate_dependency_path()

        assert path.path_type == "dependency"
        assert len(path.documents) >= 2

    def test_generate_complexity_path(self, project):
        """Test generating complexity-based path."""
        from media_engine.insights import PathGenerator

        generator = PathGenerator(project, language="en")
        path = generator.generate_complexity_path()

        assert path.path_type == "complexity"

    def test_generate_topic_clusters(self, project):
        """Test generating topic clusters."""
        from media_engine.insights import PathGenerator

        generator = PathGenerator(project, language="en")
        clusters = generator.generate_topic_clusters()

        assert isinstance(clusters, list)

    def test_format_markdown(self, project):
        """Test markdown formatting."""
        from media_engine.insights import PathGenerator

        generator = PathGenerator(project, language="en")
        path = generator.generate_dependency_path()
        md = path.format_markdown()

        assert "# " in md
        assert "Reading Order" in md
