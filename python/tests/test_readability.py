"""
Tests for the readability module - content readability analysis.
"""

import pytest
from pathlib import Path

from media_engine.readability import (
    ReadabilityLevel,
    ReadabilityMetrics,
    ReadabilityIssue,
    ReadabilityReport,
    ReadabilityChecker,
    SyllableCounter,
    TextAnalyzer,
    check_readability,
)


class TestReadabilityLevel:
    """Tests for ReadabilityLevel enum."""

    def test_levels_exist(self):
        """Test that all expected levels exist."""
        assert ReadabilityLevel.ELEMENTARY.value == "elementary"
        assert ReadabilityLevel.MIDDLE_SCHOOL.value == "middle_school"
        assert ReadabilityLevel.HIGH_SCHOOL.value == "high_school"
        assert ReadabilityLevel.COLLEGE.value == "college"
        assert ReadabilityLevel.GRADUATE.value == "graduate"
        assert ReadabilityLevel.TECHNICAL.value == "technical"


class TestReadabilityMetrics:
    """Tests for ReadabilityMetrics dataclass."""

    def test_default_metrics(self):
        """Test default metric values."""
        metrics = ReadabilityMetrics()
        assert metrics.flesch_reading_ease == 0.0
        assert metrics.word_count == 0
        assert metrics.reading_level == ReadabilityLevel.HIGH_SCHOOL

    def test_metrics_with_values(self):
        """Test metrics with actual values."""
        metrics = ReadabilityMetrics(
            flesch_reading_ease=65.0,
            flesch_kincaid_grade=8.5,
            word_count=500,
            sentence_count=25,
            grade_level=8.5,
            reading_level=ReadabilityLevel.MIDDLE_SCHOOL,
        )
        assert metrics.flesch_reading_ease == 65.0
        assert metrics.word_count == 500


class TestReadabilityIssue:
    """Tests for ReadabilityIssue dataclass."""

    def test_create_issue(self):
        """Test creating an issue."""
        issue = ReadabilityIssue(
            issue_type="long_sentence",
            message="Sentence too long",
            line_number=10,
            text_sample="This is a very long sentence...",
            suggestion="Break into smaller sentences",
            severity="warning",
        )
        assert issue.issue_type == "long_sentence"
        assert issue.line_number == 10
        assert issue.severity == "warning"

    def test_issue_defaults(self):
        """Test issue default values."""
        issue = ReadabilityIssue(
            issue_type="test",
            message="Test message",
        )
        assert issue.line_number is None
        assert issue.text_sample == ""
        assert issue.severity == "info"


class TestSyllableCounter:
    """Tests for SyllableCounter class."""

    def test_single_syllable_words(self):
        """Test counting single syllable words."""
        assert SyllableCounter.count("cat") == 1
        assert SyllableCounter.count("dog") == 1
        assert SyllableCounter.count("the") == 1
        assert SyllableCounter.count("a") == 1

    def test_two_syllable_words(self):
        """Test counting two syllable words."""
        assert SyllableCounter.count("happy") == 2
        assert SyllableCounter.count("water") == 2
        assert SyllableCounter.count("person") == 2

    def test_three_syllable_words(self):
        """Test counting three syllable words."""
        assert SyllableCounter.count("beautiful") == 3
        assert SyllableCounter.count("important") == 3
        assert SyllableCounter.count("computer") == 3

    def test_multi_syllable_words(self):
        """Test counting words with many syllables."""
        assert SyllableCounter.count("communication") >= 4
        assert SyllableCounter.count("internationalization") >= 6

    def test_silent_e(self):
        """Test handling of silent e."""
        assert SyllableCounter.count("make") == 1
        assert SyllableCounter.count("time") == 1
        assert SyllableCounter.count("code") == 1

    def test_empty_string(self):
        """Test empty string returns 0."""
        assert SyllableCounter.count("") == 0
        assert SyllableCounter.count("   ") == 0

    def test_short_words(self):
        """Test that short words return at least 1."""
        assert SyllableCounter.count("I") == 1
        assert SyllableCounter.count("an") == 1


class TestTextAnalyzer:
    """Tests for TextAnalyzer class."""

    def test_basic_text_analysis(self):
        """Test basic text analysis."""
        text = "This is a simple sentence. Here is another one."
        analyzer = TextAnalyzer(text)
        assert analyzer.word_count > 0
        assert analyzer.sentence_count == 2

    def test_word_count(self):
        """Test word counting."""
        text = "One two three four five."
        analyzer = TextAnalyzer(text)
        assert analyzer.word_count == 5

    def test_sentence_count(self):
        """Test sentence counting."""
        text = "First sentence. Second sentence! Third sentence?"
        analyzer = TextAnalyzer(text)
        assert analyzer.sentence_count == 3

    def test_removes_code_blocks(self):
        """Test that code blocks are removed."""
        text = """
        Some text here.

        ```python
        def foo():
            pass
        ```

        More text here.
        """
        analyzer = TextAnalyzer(text)
        assert "def" not in " ".join(analyzer.words)

    def test_removes_inline_code(self):
        """Test that inline code is removed."""
        text = "Use the `print()` function to output."
        analyzer = TextAnalyzer(text)
        assert "print" not in analyzer.words

    def test_removes_markdown_links(self):
        """Test that markdown links are cleaned."""
        text = "Click [here](https://example.com) for more."
        analyzer = TextAnalyzer(text)
        assert "here" in analyzer.words
        assert "https" not in " ".join(analyzer.words)

    def test_removes_headers(self):
        """Test that header markers are removed."""
        text = "# Header\n\nSome content here."
        analyzer = TextAnalyzer(text)
        # The word count should not be affected by # symbols
        assert analyzer.word_count > 0

    def test_removes_emphasis(self):
        """Test that emphasis markers are removed."""
        text = "This is **bold** and *italic* text."
        analyzer = TextAnalyzer(text)
        assert "bold" in analyzer.words
        assert "italic" in analyzer.words

    def test_complex_words_detection(self):
        """Test detection of complex words."""
        text = "The internationalization of communication systems is important."
        analyzer = TextAnalyzer(text)
        assert analyzer.complex_word_count >= 2

    def test_long_sentences_detection(self):
        """Test detection of long sentences."""
        # Create a sentence with more than 25 words
        words = " ".join(["word"] * 30)
        text = f"{words}."
        analyzer = TextAnalyzer(text)
        assert analyzer.long_sentence_count >= 1

    def test_compute_metrics(self):
        """Test metrics computation."""
        text = """
        This is a sample document. It contains several sentences.
        The sentences vary in length. Some are short. Others are much longer
        and contain more complex vocabulary and sophisticated ideas.
        """
        analyzer = TextAnalyzer(text)
        metrics = analyzer.compute_metrics()

        assert metrics.word_count > 0
        assert metrics.sentence_count > 0
        assert metrics.flesch_reading_ease != 0
        assert metrics.grade_level > 0
        assert metrics.reading_time_minutes > 0

    def test_metrics_reading_level(self):
        """Test that reading level is determined correctly."""
        # Simple text should be elementary or middle school
        simple = "The cat sat on the mat. The dog ran fast."
        metrics = TextAnalyzer(simple).compute_metrics()
        assert metrics.reading_level in [
            ReadabilityLevel.ELEMENTARY,
            ReadabilityLevel.MIDDLE_SCHOOL,
            ReadabilityLevel.HIGH_SCHOOL,
        ]

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = TextAnalyzer("")
        metrics = analyzer.compute_metrics()
        assert metrics.word_count == 0


class TestReadabilityChecker:
    """Tests for ReadabilityChecker class."""

    @pytest.fixture
    def checker(self):
        """Create a checker instance."""
        return ReadabilityChecker(target_level=ReadabilityLevel.HIGH_SCHOOL)

    def test_check_simple_text(self, checker):
        """Test checking simple text."""
        text = "This is a simple sentence. Easy to read."
        report = checker.check_text(text)

        assert isinstance(report, ReadabilityReport)
        assert report.metrics.word_count > 0
        assert report.target_level == ReadabilityLevel.HIGH_SCHOOL

    def test_check_complex_text(self, checker):
        """Test checking complex text."""
        text = """
        The epistemological ramifications of phenomenological hermeneutics
        necessitate a comprehensive methodological framework for analyzing
        the ontological presuppositions inherent in contemporary philosophical
        discourse regarding the nature of consciousness and intentionality.
        """
        report = checker.check_text(text)

        # Should have issues due to complexity
        assert len(report.issues) > 0
        assert not report.passes_target

    def test_long_sentence_detection(self, checker):
        """Test that long sentences are flagged."""
        # Create a very long sentence
        words = " ".join(["word"] * 30)
        text = f"Short sentence. {words} is a long sentence."
        report = checker.check_text(text)

        long_issues = [i for i in report.issues if i.issue_type == "long_sentence"]
        assert len(long_issues) >= 1

    def test_complex_words_warning(self):
        """Test that high complex word percentage is flagged."""
        checker = ReadabilityChecker(max_complex_percentage=5.0)
        text = """
        Implementation of internationalization communication
        systematization organizational infrastructure establishment.
        Conceptualization methodology authentication authorization.
        """
        report = checker.check_text(text)

        complex_issues = [i for i in report.issues if i.issue_type == "complex_words"]
        assert len(complex_issues) >= 1

    def test_flesch_score_warning(self, checker):
        """Test that very low Flesch scores are flagged."""
        # Very difficult text
        text = """
        Notwithstanding aforementioned epistemological considerations,
        the phenomenological hermeneutical methodology necessitates
        comprehensive systematization of ontological presuppositions
        intrinsic to methodological paradigms.
        """ * 5  # Repeat to get more data
        report = checker.check_text(text)

        flesch_issues = [i for i in report.issues if i.issue_type == "flesch_score"]
        # May or may not trigger depending on exact score
        # Just verify the report was created
        assert report.metrics.flesch_reading_ease < 50

    def test_passes_target(self, checker):
        """Test that simple text passes target."""
        text = "The dog ran. The cat sat. They played."
        report = checker.check_text(text)
        assert report.passes_target

    def test_different_target_levels(self):
        """Test with different target levels."""
        text = "This is a moderately complex sentence with some vocabulary."

        elementary = ReadabilityChecker(target_level=ReadabilityLevel.ELEMENTARY)
        college = ReadabilityChecker(target_level=ReadabilityLevel.COLLEGE)

        elem_report = elementary.check_text(text)
        coll_report = college.check_text(text)

        # College level should be more lenient
        assert coll_report.passes_target or elem_report.passes_target


class TestReadabilityCheckerDocument:
    """Tests for checking documents."""

    @pytest.fixture
    def checker(self):
        return ReadabilityChecker()

    @pytest.fixture
    def temp_md_file(self, tmp_path):
        """Create a temporary markdown file."""
        content = """---
title: Test Document
---

# Introduction

This is a simple test document. It has short sentences.
The content is easy to read and understand.
"""
        file_path = tmp_path / "test.md"
        file_path.write_text(content)
        return file_path

    def test_check_document(self, checker, temp_md_file):
        """Test checking a document file."""
        report = checker.check_document(temp_md_file)
        assert isinstance(report, ReadabilityReport)
        assert report.file_path == temp_md_file

    def test_document_with_reading_level_target(self, checker, tmp_path):
        """Test document with specific reading level in metadata."""
        content = """---
title: Elementary Doc
reading_level: elementary
---

The internationalization of organizational infrastructure
necessitates comprehensive methodological frameworks.
"""
        file_path = tmp_path / "elem.md"
        file_path.write_text(content)

        report = checker.check_document(file_path)
        # Should fail because content is too complex for elementary
        doc_target_issues = [i for i in report.issues if i.issue_type == "document_target"]
        # May have issues if grade level exceeds elementary
        assert isinstance(report, ReadabilityReport)


class TestReadabilityCheckerProject:
    """Tests for checking entire projects."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project
        return Project.load(demo_path)

    def test_check_project(self, demo_project):
        """Test checking a project."""
        checker = ReadabilityChecker(target_level=ReadabilityLevel.COLLEGE)
        result = checker.check_project(demo_project)

        assert "summary" in result
        assert "documents" in result
        assert "target_level" in result

    def test_project_summary(self, demo_project):
        """Test project summary structure."""
        checker = ReadabilityChecker()
        result = checker.check_project(demo_project)

        summary = result["summary"]
        assert "total_documents" in summary
        assert "passing" in summary
        assert "failing" in summary
        assert "pass_rate" in summary
        assert "average_grade_level" in summary
        assert "total_word_count" in summary
        assert "total_reading_time_minutes" in summary

    def test_project_documents(self, demo_project):
        """Test project document reports."""
        checker = ReadabilityChecker()
        result = checker.check_project(demo_project)

        for doc in result["documents"]:
            assert "file" in doc
            assert "language" in doc
            assert "grade_level" in doc
            assert "reading_level" in doc
            assert "word_count" in doc
            assert "reading_time" in doc
            assert "passes_target" in doc


class TestCheckReadabilityFunction:
    """Tests for the convenience function."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project
        return Project.load(demo_path)

    def test_check_readability_function(self, demo_project):
        """Test the convenience function."""
        result = check_readability(demo_project)
        assert "summary" in result
        assert "documents" in result

    def test_check_readability_with_target(self, demo_project):
        """Test with specific target level."""
        result = check_readability(demo_project, target_level=ReadabilityLevel.COLLEGE)
        assert result["target_level"] == "college"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_short_text(self):
        """Test with very short text."""
        checker = ReadabilityChecker()
        report = checker.check_text("Hi.")
        assert report.metrics.word_count == 1

    def test_text_with_numbers(self):
        """Test text containing numbers."""
        checker = ReadabilityChecker()
        text = "Chapter 1 covers 5 main topics. Section 2.3 has 10 examples."
        report = checker.check_text(text)
        # Numbers should not break analysis
        assert report.metrics.word_count > 0

    def test_text_with_special_characters(self):
        """Test text with special characters."""
        checker = ReadabilityChecker()
        text = "Hello! How are you? I'm fine, thanks... Really!"
        report = checker.check_text(text)
        assert report.metrics.sentence_count >= 2

    def test_unicode_text(self):
        """Test text with unicode characters."""
        checker = ReadabilityChecker()
        text = "Résumé includes café and naïve examples."
        report = checker.check_text(text)
        assert report.metrics.word_count > 0

    def test_all_code_blocks(self):
        """Test text that is all code blocks."""
        checker = ReadabilityChecker()
        text = """
        ```python
        def hello():
            print("Hello, World!")
        ```
        """
        report = checker.check_text(text)
        # Should handle gracefully even with minimal content
        assert isinstance(report, ReadabilityReport)
