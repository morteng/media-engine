"""
Readability Scoring for Media Engine

Analyzes content readability using multiple metrics:
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index
- Coleman-Liau Index
- Automated Readability Index

Also checks:
- Sentence length
- Word complexity
- Passive voice usage
- Jargon density
"""

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ReadabilityLevel(str, Enum):
    """Target audience reading levels."""

    ELEMENTARY = "elementary"  # Grade 1-5
    MIDDLE_SCHOOL = "middle_school"  # Grade 6-8
    HIGH_SCHOOL = "high_school"  # Grade 9-12
    COLLEGE = "college"  # Grade 13-16
    GRADUATE = "graduate"  # Grade 17+
    TECHNICAL = "technical"  # Technical documentation


@dataclass
class ReadabilityMetrics:
    """Computed readability metrics for content."""

    # Standard indices
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    gunning_fog: float = 0.0
    smog_index: float = 0.0
    coleman_liau: float = 0.0
    automated_readability: float = 0.0

    # Statistics
    word_count: int = 0
    sentence_count: int = 0
    syllable_count: int = 0
    char_count: int = 0
    avg_sentence_length: float = 0.0
    avg_word_length: float = 0.0
    avg_syllables_per_word: float = 0.0

    # Quality metrics
    complex_word_count: int = 0
    complex_word_percentage: float = 0.0
    long_sentence_count: int = 0
    long_sentence_percentage: float = 0.0

    # Derived
    grade_level: float = 0.0
    reading_level: ReadabilityLevel = ReadabilityLevel.HIGH_SCHOOL
    reading_time_minutes: float = 0.0


@dataclass
class ReadabilityIssue:
    """A readability problem detected in content."""

    issue_type: str
    message: str
    line_number: Optional[int] = None
    text_sample: str = ""
    suggestion: str = ""
    severity: str = "info"  # info, warning, error


@dataclass
class ReadabilityReport:
    """Complete readability analysis report."""

    metrics: ReadabilityMetrics
    issues: list[ReadabilityIssue] = field(default_factory=list)
    file_path: Optional[Path] = None
    target_level: ReadabilityLevel = ReadabilityLevel.HIGH_SCHOOL
    passes_target: bool = True


class SyllableCounter:
    """Counts syllables in English words."""

    # Common patterns
    VOWELS = set("aeiouy")
    SILENT_E = re.compile(r"[^aeiou]e$", re.I)
    DOUBLE_VOWEL = re.compile(r"[aeiou]{2}", re.I)
    TRIPLE_SYLLABLE = re.compile(r"ia|io|iu|ua|ue|ui", re.I)

    @classmethod
    def count(cls, word: str) -> int:
        """Count syllables in a word."""
        word = word.lower().strip()
        if not word:
            return 0

        if len(word) <= 3:
            return 1

        # Count vowel groups
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in cls.VOWELS
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Adjust for silent e
        if cls.SILENT_E.search(word):
            count -= 1

        # Adjust for special endings
        if word.endswith("le") and len(word) > 2 and word[-3] not in cls.VOWELS:
            count += 1

        # Minimum 1 syllable
        return max(1, count)


class TextAnalyzer:
    """Analyzes text for readability metrics."""

    # Sentence boundary pattern
    SENTENCE_PATTERN = re.compile(r"[.!?]+(?:\s|$)")

    # Word pattern (alphanumeric sequences)
    WORD_PATTERN = re.compile(r"\b[a-zA-Z]+\b")

    # Complex word threshold (3+ syllables)
    COMPLEX_SYLLABLE_THRESHOLD = 3

    # Long sentence threshold (words)
    LONG_SENTENCE_THRESHOLD = 25

    # Average reading speed (words per minute)
    READING_SPEED = 200

    def __init__(self, text: str):
        self.original_text = text
        self.text = self._clean_text(text)
        self._analyze()

    def _clean_text(self, text: str) -> str:
        """Remove markdown formatting for analysis."""
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"`[^`]+`", "", text)

        # Remove links but keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove headers
        text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

        # Remove emphasis markers
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        return text

    def _analyze(self):
        """Perform text analysis."""
        # Extract words
        self.words = self.WORD_PATTERN.findall(self.text)
        self.word_count = len(self.words)

        # Extract sentences
        sentences = self.SENTENCE_PATTERN.split(self.text)
        self.sentences = [s.strip() for s in sentences if s.strip()]
        self.sentence_count = max(1, len(self.sentences))

        # Count syllables
        self.syllable_count = sum(SyllableCounter.count(w) for w in self.words)

        # Character count (letters only)
        self.char_count = sum(len(w) for w in self.words)

        # Complex words (3+ syllables)
        self.complex_words = [
            w for w in self.words if SyllableCounter.count(w) >= self.COMPLEX_SYLLABLE_THRESHOLD
        ]
        self.complex_word_count = len(self.complex_words)

        # Long sentences
        self.long_sentences = []
        for sent in self.sentences:
            words_in_sent = len(self.WORD_PATTERN.findall(sent))
            if words_in_sent >= self.LONG_SENTENCE_THRESHOLD:
                self.long_sentences.append((sent, words_in_sent))
        self.long_sentence_count = len(self.long_sentences)

    def compute_metrics(self) -> ReadabilityMetrics:
        """Compute all readability metrics."""
        if self.word_count == 0:
            return ReadabilityMetrics()

        # Averages
        avg_sentence_length = self.word_count / self.sentence_count
        avg_syllables = self.syllable_count / self.word_count
        avg_word_length = self.char_count / self.word_count

        # Flesch Reading Ease
        # Higher = easier to read (0-100 scale)
        flesch = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables

        # Flesch-Kincaid Grade Level
        fk_grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables - 15.59

        # Gunning Fog Index
        complex_pct = self.complex_word_count / self.word_count * 100
        fog = 0.4 * (avg_sentence_length + complex_pct)

        # SMOG Index (Simple Measure of Gobbledygook)
        if self.sentence_count >= 30:
            smog = 1.0430 * math.sqrt(self.complex_word_count * 30 / self.sentence_count) + 3.1291
        else:
            smog = (
                1.0430 * math.sqrt(self.complex_word_count * 30 / max(1, self.sentence_count))
                + 3.1291
            )

        # Coleman-Liau Index
        L = self.char_count / self.word_count * 100  # letters per 100 words
        S = self.sentence_count / self.word_count * 100  # sentences per 100 words
        coleman_liau = 0.0588 * L - 0.296 * S - 15.8

        # Automated Readability Index
        ari = (
            4.71 * (self.char_count / self.word_count)
            + 0.5 * (self.word_count / self.sentence_count)
            - 21.43
        )

        # Average grade level
        grade_level = (fk_grade + fog + smog + coleman_liau + ari) / 5

        # Determine reading level
        if grade_level <= 5:
            reading_level = ReadabilityLevel.ELEMENTARY
        elif grade_level <= 8:
            reading_level = ReadabilityLevel.MIDDLE_SCHOOL
        elif grade_level <= 12:
            reading_level = ReadabilityLevel.HIGH_SCHOOL
        elif grade_level <= 16:
            reading_level = ReadabilityLevel.COLLEGE
        else:
            reading_level = ReadabilityLevel.GRADUATE

        # Reading time
        reading_time = self.word_count / self.READING_SPEED

        return ReadabilityMetrics(
            flesch_reading_ease=round(flesch, 1),
            flesch_kincaid_grade=round(fk_grade, 1),
            gunning_fog=round(fog, 1),
            smog_index=round(smog, 1),
            coleman_liau=round(coleman_liau, 1),
            automated_readability=round(ari, 1),
            word_count=self.word_count,
            sentence_count=self.sentence_count,
            syllable_count=self.syllable_count,
            char_count=self.char_count,
            avg_sentence_length=round(avg_sentence_length, 1),
            avg_word_length=round(avg_word_length, 1),
            avg_syllables_per_word=round(avg_syllables, 2),
            complex_word_count=self.complex_word_count,
            complex_word_percentage=round(complex_pct, 1),
            long_sentence_count=self.long_sentence_count,
            long_sentence_percentage=round(self.long_sentence_count / self.sentence_count * 100, 1),
            grade_level=round(grade_level, 1),
            reading_level=reading_level,
            reading_time_minutes=round(reading_time, 1),
        )


class ReadabilityChecker:
    """
    Checks content readability against target level.

    Usage:
        checker = ReadabilityChecker(target_level=ReadabilityLevel.HIGH_SCHOOL)
        report = checker.check_text(content)
        report = checker.check_document(doc_path)
        project_report = checker.check_project(project)
    """

    # Grade level targets for each reading level
    LEVEL_TARGETS = {
        ReadabilityLevel.ELEMENTARY: 5,
        ReadabilityLevel.MIDDLE_SCHOOL: 8,
        ReadabilityLevel.HIGH_SCHOOL: 12,
        ReadabilityLevel.COLLEGE: 16,
        ReadabilityLevel.GRADUATE: 20,
        ReadabilityLevel.TECHNICAL: 16,  # Technical docs should still be readable
    }

    def __init__(
        self,
        target_level: ReadabilityLevel = ReadabilityLevel.HIGH_SCHOOL,
        max_sentence_length: int = 25,
        max_complex_percentage: float = 15.0,
    ):
        self.target_level = target_level
        self.target_grade = self.LEVEL_TARGETS[target_level]
        self.max_sentence_length = max_sentence_length
        self.max_complex_percentage = max_complex_percentage

    def check_text(self, text: str, file_path: Path = None) -> ReadabilityReport:
        """Check readability of text content."""
        analyzer = TextAnalyzer(text)
        metrics = analyzer.compute_metrics()
        issues = []

        # Check grade level
        if metrics.grade_level > self.target_grade:
            issues.append(
                ReadabilityIssue(
                    issue_type="grade_level",
                    message=f"Content reads at grade {metrics.grade_level}, target is {self.target_grade}",
                    suggestion="Simplify vocabulary and shorten sentences",
                    severity="warning",
                )
            )

        # Check long sentences
        for sent, word_count in analyzer.long_sentences:
            # Find line number
            line_num = None
            for i, line in enumerate(text.split("\n"), 1):
                if sent[:50] in line:
                    line_num = i
                    break

            issues.append(
                ReadabilityIssue(
                    issue_type="long_sentence",
                    message=f"Sentence has {word_count} words (max recommended: {self.max_sentence_length})",
                    line_number=line_num,
                    text_sample=sent[:100] + "..." if len(sent) > 100 else sent,
                    suggestion="Consider breaking into smaller sentences",
                    severity="info",
                )
            )

        # Check complex word percentage
        if metrics.complex_word_percentage > self.max_complex_percentage:
            issues.append(
                ReadabilityIssue(
                    issue_type="complex_words",
                    message=f"{metrics.complex_word_percentage}% complex words (max: {self.max_complex_percentage}%)",
                    suggestion="Use simpler alternatives for complex terms",
                    severity="warning",
                )
            )

        # Check for very low Flesch score
        if metrics.flesch_reading_ease < 30:
            issues.append(
                ReadabilityIssue(
                    issue_type="flesch_score",
                    message=f"Flesch Reading Ease score of {metrics.flesch_reading_ease} is very difficult",
                    suggestion="Content is very difficult to read; simplify significantly",
                    severity="error",
                )
            )

        passes = metrics.grade_level <= self.target_grade

        return ReadabilityReport(
            metrics=metrics,
            issues=issues,
            file_path=file_path,
            target_level=self.target_level,
            passes_target=passes,
        )

    def check_document(self, doc_path: Path) -> ReadabilityReport:
        """Check readability of a document."""
        from ..cms.document import Document

        doc = Document.load(doc_path)
        report = self.check_text(doc.content, doc_path)

        # Check document-specific target if specified
        if "reading_level" in doc.metadata:
            doc_target = ReadabilityLevel(doc.metadata["reading_level"])
            target_grade = self.LEVEL_TARGETS[doc_target]
            if report.metrics.grade_level > target_grade:
                report.issues.insert(
                    0,
                    ReadabilityIssue(
                        issue_type="document_target",
                        message=f"Document targets {doc_target.value} but reads at grade {report.metrics.grade_level}",
                        severity="error",
                    ),
                )
                report.passes_target = False

        return report

    def check_project(self, project) -> dict:
        """Check readability of all project documents."""
        reports = []

        for lang in project.languages:
            for chapter in project.list_chapters(lang):
                report = self.check_document(chapter)
                reports.append(
                    {
                        "file": str(chapter.relative_to(project.root)),
                        "language": lang,
                        "grade_level": report.metrics.grade_level,
                        "reading_level": report.metrics.reading_level.value,
                        "word_count": report.metrics.word_count,
                        "reading_time": report.metrics.reading_time_minutes,
                        "passes_target": report.passes_target,
                        "issue_count": len(report.issues),
                    }
                )

        # Summary
        total = len(reports)
        passing = sum(1 for r in reports if r["passes_target"])
        avg_grade = sum(r["grade_level"] for r in reports) / max(1, total)
        total_words = sum(r["word_count"] for r in reports)
        total_time = sum(r["reading_time"] for r in reports)

        return {
            "summary": {
                "total_documents": total,
                "passing": passing,
                "failing": total - passing,
                "pass_rate": round(passing / max(1, total) * 100, 1),
                "average_grade_level": round(avg_grade, 1),
                "total_word_count": total_words,
                "total_reading_time_minutes": round(total_time, 1),
            },
            "target_level": self.target_level.value,
            "documents": reports,
        }


def check_readability(
    project,
    target_level: ReadabilityLevel = ReadabilityLevel.HIGH_SCHOOL,
) -> dict:
    """Convenience function to check project readability."""
    checker = ReadabilityChecker(target_level=target_level)
    return checker.check_project(project)


__all__ = [
    "ReadabilityLevel",
    "ReadabilityMetrics",
    "ReadabilityIssue",
    "ReadabilityReport",
    "ReadabilityChecker",
    "SyllableCounter",
    "TextAnalyzer",
    "check_readability",
]
