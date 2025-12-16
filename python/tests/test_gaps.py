"""
Tests for the gaps module - content gap analysis.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from media_engine.gaps import (
    ContentGap,
    ContentGapAnalyzer,
    GapSeverity,
    GapType,
    OrphanAnalyzer,
    ReferenceAnalyzer,
    SchemaGapAnalyzer,
    TopicAnalyzer,
    TopicCoverage,
    TranslationGapAnalyzer,
    analyze_gaps,
)


class TestGapType:
    """Tests for GapType enum."""

    def test_gap_types_exist(self):
        """Test that all expected gap types exist."""
        assert GapType.MISSING_TOPIC.value == "missing_topic"
        assert GapType.MISSING_TRANSLATION.value == "missing_translation"
        assert GapType.MISSING_REFERENCE.value == "missing_reference"
        assert GapType.INCOMPLETE_SECTION.value == "incomplete_section"
        assert GapType.STALE_CONTENT.value == "stale_content"
        assert GapType.MISSING_EXAMPLE.value == "missing_example"
        assert GapType.MISSING_SCHEMA.value == "missing_schema"
        assert GapType.ORPHAN_CONTENT.value == "orphan_content"

    def test_gap_type_is_string_enum(self):
        """Test that gap type is a string enum."""
        assert isinstance(GapType.MISSING_TOPIC, str)
        assert GapType.MISSING_TOPIC == "missing_topic"


class TestGapSeverity:
    """Tests for GapSeverity enum."""

    def test_severity_levels_exist(self):
        """Test that all severity levels exist."""
        assert GapSeverity.CRITICAL.value == "critical"
        assert GapSeverity.HIGH.value == "high"
        assert GapSeverity.MEDIUM.value == "medium"
        assert GapSeverity.LOW.value == "low"

    def test_severity_is_string_enum(self):
        """Test that severity is a string enum."""
        assert isinstance(GapSeverity.CRITICAL, str)
        assert GapSeverity.CRITICAL == "critical"


class TestContentGap:
    """Tests for ContentGap dataclass."""

    def test_basic_gap(self):
        """Test creating a basic gap."""
        gap = ContentGap(
            gap_type=GapType.MISSING_TOPIC,
            severity=GapSeverity.MEDIUM,
            description="Missing topic: authentication",
        )
        assert gap.gap_type == GapType.MISSING_TOPIC
        assert gap.severity == GapSeverity.MEDIUM
        assert gap.location is None
        assert gap.related_content == []

    def test_gap_with_all_fields(self):
        """Test gap with all fields populated."""
        gap = ContentGap(
            gap_type=GapType.MISSING_TRANSLATION,
            severity=GapSeverity.HIGH,
            description="Document not translated",
            location="en/guide.md",
            suggestion="Create no/guide.md",
            related_content=["en/guide.md"],
        )
        assert gap.location == "en/guide.md"
        assert gap.suggestion == "Create no/guide.md"
        assert len(gap.related_content) == 1


class TestTopicCoverage:
    """Tests for TopicCoverage dataclass."""

    def test_basic_coverage(self):
        """Test creating basic topic coverage."""
        coverage = TopicCoverage(
            topic="authentication",
            covered=True,
        )
        assert coverage.topic == "authentication"
        assert coverage.covered is True
        assert coverage.documents == []

    def test_coverage_with_documents(self):
        """Test coverage with documents listed."""
        coverage = TopicCoverage(
            topic="api",
            covered=True,
            documents=["api.md", "reference/api.md"],
            subtopics_total=5,
            subtopics_covered=3,
        )
        assert len(coverage.documents) == 2
        assert coverage.subtopics_total == 5
        assert coverage.subtopics_covered == 3


class TestTopicAnalyzer:
    """Tests for TopicAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en"]
        return project

    def test_extract_topics_from_content(self, mock_project, tmp_path):
        """Test extracting topics from headings."""
        # Create test document
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

# Introduction

Some content here.

## Getting Started

More content.

### Installation

Install steps.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = TopicAnalyzer(mock_project)
        topics = analyzer.extract_topics_from_content()

        # Should find headings
        assert "introduction" in topics
        assert "getting started" in topics
        assert "installation" in topics

    def test_check_expected_topics_covered(self, mock_project, tmp_path):
        """Test checking for covered topics."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

# Authentication

How to authenticate.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = TopicAnalyzer(mock_project)
        gaps = analyzer.check_expected_topics(["authentication"])

        assert len(gaps) == 0

    def test_check_expected_topics_missing(self, mock_project, tmp_path):
        """Test checking for missing topics."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

# Introduction

Basic intro.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = TopicAnalyzer(mock_project)
        gaps = analyzer.check_expected_topics(["authentication", "api"])

        assert len(gaps) == 2
        assert all(g.gap_type == GapType.MISSING_TOPIC for g in gaps)

    def test_partial_topic_match(self, mock_project, tmp_path):
        """Test partial topic matching."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

# API Reference

API documentation.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = TopicAnalyzer(mock_project)
        # "api" should match "api reference"
        gaps = analyzer.check_expected_topics(["api"])

        assert len(gaps) == 0


class TestReferenceAnalyzer:
    """Tests for ReferenceAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en"]
        return project

    def test_no_broken_references(self, mock_project, tmp_path):
        """Test document with valid references."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)

        doc1 = doc_dir / "index.md"
        doc1.write_text("""---
title: Index
---

See [guide](guide.md) for more.
""")

        doc2 = doc_dir / "guide.md"
        doc2.write_text("""---
title: Guide
---

The guide content.
""")

        mock_project.list_chapters = Mock(return_value=[doc1, doc2])

        analyzer = ReferenceAnalyzer(mock_project)
        gaps = analyzer.find_broken_references()

        # No broken references
        assert len([g for g in gaps if g.gap_type == GapType.MISSING_REFERENCE]) == 0

    def test_broken_internal_reference(self, mock_project, tmp_path):
        """Test document with broken reference."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)

        doc = doc_dir / "index.md"
        doc.write_text("""---
title: Index
---

See [nonexistent](nonexistent.md) for more.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = ReferenceAnalyzer(mock_project)
        gaps = analyzer.find_broken_references()

        broken = [g for g in gaps if g.gap_type == GapType.MISSING_REFERENCE]
        assert len(broken) >= 1

    def test_external_links_skipped(self, mock_project, tmp_path):
        """Test that external links are skipped."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)

        doc = doc_dir / "index.md"
        doc.write_text("""---
title: Index
---

See [Google](https://google.com) and [email](mailto:test@test.com).
Also check [anchor](#section).
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = ReferenceAnalyzer(mock_project)
        gaps = analyzer.find_broken_references()

        # External links and anchors should not generate gaps
        assert len(gaps) == 0


class TestTranslationGapAnalyzer:
    """Tests for TranslationGapAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project with multiple languages."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en", "no"]
        project.source_language = "en"
        return project

    def test_no_missing_translations(self, mock_project, tmp_path):
        """Test when all translations exist."""
        # Create source and translation
        en_dir = tmp_path / "content" / "en"
        en_dir.mkdir(parents=True)
        en_doc = en_dir / "guide.md"
        en_doc.write_text("---\ntitle: Guide\n---\nContent")

        no_dir = tmp_path / "content" / "no"
        no_dir.mkdir(parents=True)
        no_doc = no_dir / "guide.md"
        no_doc.write_text("---\ntitle: Veiledning\n---\nInnhold")

        def list_chapters(lang):
            if lang == "en":
                return [en_doc]
            else:
                return [no_doc]

        mock_project.list_chapters = Mock(side_effect=list_chapters)

        analyzer = TranslationGapAnalyzer(mock_project)
        gaps = analyzer.find_missing_translations()

        assert len(gaps) == 0

    def test_missing_translation(self, mock_project, tmp_path):
        """Test detecting missing translations."""
        en_dir = tmp_path / "content" / "en"
        en_dir.mkdir(parents=True)
        en_doc = en_dir / "guide.md"
        en_doc.write_text("---\ntitle: Guide\n---\nContent")

        no_dir = tmp_path / "content" / "no"
        no_dir.mkdir(parents=True)
        # No Norwegian translation

        def list_chapters(lang):
            if lang == "en":
                return [en_doc]
            else:
                return []

        mock_project.list_chapters = Mock(side_effect=list_chapters)

        analyzer = TranslationGapAnalyzer(mock_project)
        gaps = analyzer.find_missing_translations()

        assert len(gaps) == 1
        assert gaps[0].gap_type == GapType.MISSING_TRANSLATION


class TestSchemaGapAnalyzer:
    """Tests for SchemaGapAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en"]
        return project

    def test_no_schema_file(self, mock_project, tmp_path):
        """Test when no schema file exists."""
        mock_project.list_chapters = Mock(return_value=[])

        analyzer = SchemaGapAnalyzer(mock_project)
        gaps = analyzer.find_undocumented_schema_fields()

        assert len(gaps) == 0

    def test_documented_schema_fields(self, mock_project, tmp_path):
        """Test when all schema fields are documented."""
        # Create schema
        schema_path = tmp_path / "schema.yaml"
        schema_path.write_text("""
properties:
  title:
    type: string
  description:
    type: string
""")

        # Create document mentioning fields
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "schema.md"
        doc.write_text("""---
title: Schema Reference
---

## title

The title field specifies the document title.

## description

The description provides a summary.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = SchemaGapAnalyzer(mock_project)
        gaps = analyzer.find_undocumented_schema_fields()

        assert len(gaps) == 0

    def test_undocumented_schema_field(self, mock_project, tmp_path):
        """Test detecting undocumented schema fields."""
        schema_path = tmp_path / "schema.yaml"
        schema_path.write_text("""
properties:
  title:
    type: string
  secret_field:
    type: string
""")

        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "schema.md"
        doc.write_text("""---
title: Schema Reference
---

## title

Only title is documented.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = SchemaGapAnalyzer(mock_project)
        gaps = analyzer.find_undocumented_schema_fields()

        assert len(gaps) == 1
        assert gaps[0].gap_type == GapType.MISSING_SCHEMA
        assert "secret_field" in gaps[0].description


class TestOrphanAnalyzer:
    """Tests for OrphanAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en"]
        return project

    def test_no_orphans_with_links(self, mock_project, tmp_path):
        """Test no orphans when documents are linked."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)

        index = doc_dir / "index.md"
        index.write_text("""---
title: Index
---

See [guide](guide.md) for more.
""")

        guide = doc_dir / "guide.md"
        guide.write_text("""---
title: Guide
---

The guide content.
""")

        mock_project.list_chapters = Mock(return_value=[index, guide])

        analyzer = OrphanAnalyzer(mock_project)
        gaps = analyzer.find_orphan_documents()

        # Index shouldn't be orphan, guide is linked
        orphans = [g for g in gaps if g.gap_type == GapType.ORPHAN_CONTENT]
        assert len(orphans) == 0

    def test_orphan_detection(self, mock_project, tmp_path):
        """Test detecting orphan documents."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)

        index = doc_dir / "index.md"
        index.write_text("""---
title: Index
---

Welcome to the docs.
""")

        orphan = doc_dir / "orphan.md"
        orphan.write_text("""---
title: Orphan
---

This is not linked from anywhere.
""")

        mock_project.list_chapters = Mock(return_value=[index, orphan])

        analyzer = OrphanAnalyzer(mock_project)
        gaps = analyzer.find_orphan_documents()

        orphans = [g for g in gaps if g.gap_type == GapType.ORPHAN_CONTENT]
        assert len(orphans) >= 1

    def test_introduction_files_excluded(self, mock_project, tmp_path):
        """Test that introduction files are not flagged as orphans."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)

        intro = doc_dir / "01_introduction.md"
        intro.write_text("""---
title: Introduction
---

Welcome!
""")

        mock_project.list_chapters = Mock(return_value=[intro])

        analyzer = OrphanAnalyzer(mock_project)
        gaps = analyzer.find_orphan_documents()

        # Introduction files should be excluded
        orphans = [g for g in gaps if g.gap_type == GapType.ORPHAN_CONTENT]
        assert len(orphans) == 0


class TestContentGapAnalyzer:
    """Tests for ContentGapAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en"]
        project.source_language = "en"
        return project

    def test_analyzer_initialization(self, mock_project):
        """Test analyzer initialization."""
        analyzer = ContentGapAnalyzer(mock_project)
        assert analyzer.project == mock_project
        assert analyzer.expected_topics == []

    def test_analyzer_with_expected_topics(self, mock_project):
        """Test analyzer with expected topics."""
        topics = ["authentication", "authorization", "api"]
        analyzer = ContentGapAnalyzer(mock_project, expected_topics=topics)
        assert analyzer.expected_topics == topics

    def test_analyze_returns_report_structure(self, mock_project, tmp_path):
        """Test that analyze returns correct structure."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

# Test

Content.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = ContentGapAnalyzer(mock_project)
        report = analyzer.analyze()

        assert "summary" in report
        assert "by_type" in report
        assert "gaps" in report
        assert "total_gaps" in report["summary"]
        assert "critical" in report["summary"]
        assert "high" in report["summary"]
        assert "medium" in report["summary"]
        assert "low" in report["summary"]
        assert "blocks_publish" in report["summary"]

    def test_analyze_selective_checks(self, mock_project, tmp_path):
        """Test running selective checks."""
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

Content.
""")

        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = ContentGapAnalyzer(mock_project)
        report = analyzer.analyze(
            check_topics=False,
            check_references=True,
            check_translations=False,
            check_schema=False,
            check_orphans=False,
        )

        assert "summary" in report


class TestContentGapAnalyzerProject:
    """Tests for analyzing real projects."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_analyze_demo_project(self, demo_project):
        """Test analyzing demo project."""
        analyzer = ContentGapAnalyzer(demo_project)
        report = analyzer.analyze()

        assert "summary" in report
        assert report["summary"]["total_gaps"] >= 0

    def test_analyze_with_expected_topics(self, demo_project):
        """Test analyzing with expected topics."""
        topics = ["nonexistent_topic_xyz"]
        analyzer = ContentGapAnalyzer(demo_project, expected_topics=topics)
        report = analyzer.analyze()

        # Should find at least the missing topic
        assert report["summary"]["total_gaps"] >= 1


class TestAnalyzeGapsFunction:
    """Tests for the convenience function."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_analyze_gaps_function(self, demo_project):
        """Test the analyze_gaps convenience function."""
        report = analyze_gaps(demo_project)
        assert "summary" in report
        assert "gaps" in report

    def test_analyze_gaps_with_topics(self, demo_project):
        """Test analyze_gaps with expected topics."""
        topics = ["test_topic_missing"]
        report = analyze_gaps(demo_project, expected_topics=topics)
        assert report["summary"]["total_gaps"] >= 1


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = []
        project.source_language = "en"
        project.list_chapters = Mock(return_value=[])
        return project

    def test_empty_project(self, mock_project):
        """Test analyzing empty project."""
        analyzer = ContentGapAnalyzer(mock_project)
        report = analyzer.analyze()

        assert report["summary"]["total_gaps"] == 0

    def test_no_languages(self, mock_project):
        """Test project with no languages."""
        analyzer = ContentGapAnalyzer(mock_project)
        report = analyzer.analyze()

        assert "summary" in report

    def test_gap_severity_counts(self, mock_project, tmp_path):
        """Test severity counting in summary."""
        # Create documents that will generate gaps of different severities
        doc_dir = tmp_path / "content" / "en"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "test.md"
        doc.write_text("""---
title: Test
---

[broken](nonexistent.md)
""")

        mock_project.languages = ["en"]
        mock_project.list_chapters = Mock(return_value=[doc])

        analyzer = ContentGapAnalyzer(mock_project)
        report = analyzer.analyze(
            check_topics=False,
            check_translations=False,
            check_schema=False,
            check_orphans=False,
        )

        # Should count severities correctly
        total = sum(
            [
                report["summary"]["critical"],
                report["summary"]["high"],
                report["summary"]["medium"],
                report["summary"]["low"],
            ]
        )
        assert total == report["summary"]["total_gaps"]

    def test_blocks_publish_flag(self, mock_project):
        """Test blocks_publish flag."""
        analyzer = ContentGapAnalyzer(mock_project)
        report = analyzer.analyze()

        # With no critical gaps, should not block
        assert report["summary"]["blocks_publish"] == (report["summary"]["critical"] > 0)
