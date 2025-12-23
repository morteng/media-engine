"""
Norwegian Readability Analysis for Media Engine

Implements Scandinavian readability metrics:
- LIX (Läsbarhetsindex) - Standard Scandinavian metric
- RIX - Simplified LIX variant
- Compound word analysis for Norwegian/Swedish
- Norwegian-specific syllable counting

Reference:
- LIX developed by Carl-Hugo Björnsson (1968)
- Standard in Nordic countries for readability assessment
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class NorwegianReadabilityLevel(str, Enum):
    """Norwegian reading levels based on LIX scores."""

    VERY_EASY = "very_easy"  # LIX < 25: Children's books
    EASY = "easy"  # LIX 25-34: Simple texts
    MEDIUM = "medium"  # LIX 35-44: Normal newspaper
    DIFFICULT = "difficult"  # LIX 45-54: Official documents
    VERY_DIFFICULT = "very_difficult"  # LIX > 54: Technical/academic


@dataclass
class NorwegianReadabilityMetrics:
    """Norwegian-specific readability metrics."""

    # LIX score (primary metric)
    lix: float
    lix_level: NorwegianReadabilityLevel

    # RIX score (simplified variant)
    rix: float

    # Basic statistics
    word_count: int
    sentence_count: int
    long_word_count: int  # Words > 6 characters
    long_word_percentage: float

    # Norwegian-specific
    compound_word_count: int
    avg_word_length: float
    avg_sentence_length: float

    # Estimated reading level
    school_year: int  # Norwegian school year (1-13)
    reading_time_minutes: float

    def to_dict(self) -> dict:
        return {
            "lix": round(self.lix, 1),
            "lix_level": self.lix_level.value,
            "rix": round(self.rix, 2),
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "long_word_count": self.long_word_count,
            "long_word_percentage": round(self.long_word_percentage, 1),
            "compound_word_count": self.compound_word_count,
            "avg_word_length": round(self.avg_word_length, 1),
            "avg_sentence_length": round(self.avg_sentence_length, 1),
            "school_year": self.school_year,
            "reading_time_minutes": round(self.reading_time_minutes, 1),
        }


@dataclass
class NorwegianReadabilityIssue:
    """A readability issue specific to Norwegian text."""

    issue_type: str
    message: str
    line_number: Optional[int] = None
    text_sample: str = ""
    suggestion: str = ""
    severity: str = "info"


@dataclass
class NorwegianReadabilityReport:
    """Complete Norwegian readability analysis report."""

    metrics: NorwegianReadabilityMetrics
    issues: list[NorwegianReadabilityIssue]
    file_path: Optional[Path] = None
    target_level: NorwegianReadabilityLevel = NorwegianReadabilityLevel.MEDIUM
    passes_target: bool = True
    compound_words: list[str] = None  # List of detected compound words

    def to_dict(self) -> dict:
        return {
            "metrics": self.metrics.to_dict(),
            "issues": [
                {
                    "type": i.issue_type,
                    "message": i.message,
                    "severity": i.severity,
                }
                for i in self.issues
            ],
            "file_path": str(self.file_path) if self.file_path else None,
            "target_level": self.target_level.value,
            "passes_target": self.passes_target,
            "compound_words_sample": (self.compound_words or [])[:10],
        }


class NorwegianSyllableCounter:
    """
    Counts syllables in Norwegian words.

    Norwegian syllable rules differ from English:
    - Vowels: a, e, i, o, u, y, æ, ø, å
    - Diphthongs: ai, au, ei, øy, etc.
    - Compound words need special handling
    """

    VOWELS = set("aeiouyæøå")

    # Norwegian diphthongs (count as single syllable)
    DIPHTHONGS = [
        "ai",
        "au",
        "ei",
        "øy",
        "oy",
        "ui",
        "ia",
        "ie",
        "io",
        "iu",
    ]

    @classmethod
    def count(cls, word: str) -> int:
        """Count syllables in a Norwegian word."""
        word = word.lower().strip()
        if not word:
            return 0

        if len(word) <= 2:
            return 1

        # Replace diphthongs with single vowel marker
        for diph in cls.DIPHTHONGS:
            word = word.replace(diph, "a")

        # Count vowel groups
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in cls.VOWELS
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Minimum 1 syllable
        return max(1, count)


class NorwegianTextAnalyzer:
    """
    Analyzes Norwegian text for readability metrics.

    Implements LIX and RIX formulas with Norwegian-specific adaptations.
    """

    # Sentence boundaries
    SENTENCE_PATTERN = re.compile(r"[.!?:]+(?:\s|$)")

    # Word pattern (including Norwegian characters)
    WORD_PATTERN = re.compile(r"\b[a-zA-ZæøåÆØÅ]+\b")

    # Long word threshold for LIX (characters)
    LONG_WORD_THRESHOLD = 6

    # Common Norwegian compound word patterns
    COMPOUND_PATTERNS = [
        # Common suffixes that indicate compound
        r"\w{4,}(hus|bil|mann|dame|barn|bok|skole|kontor|arbeid)\b",
        # Common prefixes
        r"\b(for|sam|med|mot|inn|ut|på|av)\w{4,}",
        # Words with multiple clear parts (long words likely compound)
        r"\b\w{12,}\b",
    ]

    # Norwegian reading speed (words per minute)
    READING_SPEED = 180  # Slightly slower than English due to compound words

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

        # Remove headers markers
        text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

        # Remove emphasis
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)

        # Remove HTML
        text = re.sub(r"<[^>]+>", "", text)

        return text

    def _analyze(self):
        """Perform text analysis."""
        # Extract words (including Norwegian characters)
        self.words = self.WORD_PATTERN.findall(self.text)
        self.word_count = len(self.words)

        # Extract sentences
        sentences = self.SENTENCE_PATTERN.split(self.text)
        self.sentences = [s.strip() for s in sentences if s.strip()]
        self.sentence_count = max(1, len(self.sentences))

        # Count long words (> 6 characters)
        self.long_words = [w for w in self.words if len(w) > self.LONG_WORD_THRESHOLD]
        self.long_word_count = len(self.long_words)

        # Detect compound words
        self.compound_words = self._detect_compound_words()

        # Character count
        self.char_count = sum(len(w) for w in self.words)

    def _detect_compound_words(self) -> list[str]:
        """Detect Norwegian compound words."""
        compounds = []

        for word in self.words:
            if len(word) < 8:
                continue

            # Check against compound patterns
            for pattern in self.COMPOUND_PATTERNS:
                if re.match(pattern, word, re.IGNORECASE):
                    compounds.append(word)
                    break

        return list(set(compounds))

    def compute_lix(self) -> float:
        """
        Compute LIX (Läsbarhetsindex) score.

        Formula:
        LIX = (word_count / sentence_count) + (long_words * 100 / word_count)

        where long_words = words with more than 6 characters
        """
        if self.word_count == 0:
            return 0.0

        avg_sentence_length = self.word_count / self.sentence_count
        long_word_percentage = self.long_word_count * 100 / self.word_count

        return avg_sentence_length + long_word_percentage

    def compute_rix(self) -> float:
        """
        Compute RIX score (simplified LIX variant).

        Formula:
        RIX = long_words / sentence_count

        Interpretation:
        - RIX < 1.0: Very easy
        - RIX 1.0-2.0: Easy
        - RIX 2.0-3.0: Medium
        - RIX 3.0-4.0: Difficult
        - RIX > 4.0: Very difficult
        """
        return self.long_word_count / self.sentence_count

    def compute_metrics(self) -> NorwegianReadabilityMetrics:
        """Compute all Norwegian readability metrics."""
        if self.word_count == 0:
            return NorwegianReadabilityMetrics(
                lix=0,
                lix_level=NorwegianReadabilityLevel.VERY_EASY,
                rix=0,
                word_count=0,
                sentence_count=0,
                long_word_count=0,
                long_word_percentage=0,
                compound_word_count=0,
                avg_word_length=0,
                avg_sentence_length=0,
                school_year=1,
                reading_time_minutes=0,
            )

        lix = self.compute_lix()
        rix = self.compute_rix()

        # Determine LIX level
        if lix < 25:
            lix_level = NorwegianReadabilityLevel.VERY_EASY
        elif lix < 35:
            lix_level = NorwegianReadabilityLevel.EASY
        elif lix < 45:
            lix_level = NorwegianReadabilityLevel.MEDIUM
        elif lix < 55:
            lix_level = NorwegianReadabilityLevel.DIFFICULT
        else:
            lix_level = NorwegianReadabilityLevel.VERY_DIFFICULT

        # Estimate school year from LIX
        # Rough mapping: LIX 20 = year 1, LIX 55+ = year 13+
        school_year = min(13, max(1, int((lix - 15) / 3)))

        return NorwegianReadabilityMetrics(
            lix=lix,
            lix_level=lix_level,
            rix=rix,
            word_count=self.word_count,
            sentence_count=self.sentence_count,
            long_word_count=self.long_word_count,
            long_word_percentage=self.long_word_count * 100 / self.word_count,
            compound_word_count=len(self.compound_words),
            avg_word_length=self.char_count / self.word_count,
            avg_sentence_length=self.word_count / self.sentence_count,
            school_year=school_year,
            reading_time_minutes=self.word_count / self.READING_SPEED,
        )


class NorwegianReadabilityChecker:
    """
    Checks Norwegian text readability against target level.

    Usage:
        checker = NorwegianReadabilityChecker()
        report = checker.check_text(content)

        # Or with specific target
        checker = NorwegianReadabilityChecker(
            target_level=NorwegianReadabilityLevel.EASY
        )
        report = checker.check_document(doc_path)
    """

    # LIX targets for each level
    LIX_TARGETS = {
        NorwegianReadabilityLevel.VERY_EASY: 25,
        NorwegianReadabilityLevel.EASY: 35,
        NorwegianReadabilityLevel.MEDIUM: 45,
        NorwegianReadabilityLevel.DIFFICULT: 55,
        NorwegianReadabilityLevel.VERY_DIFFICULT: 100,
    }

    def __init__(
        self,
        target_level: NorwegianReadabilityLevel = NorwegianReadabilityLevel.MEDIUM,
        max_sentence_length: int = 25,
        max_long_word_percentage: float = 40.0,
    ):
        self.target_level = target_level
        self.target_lix = self.LIX_TARGETS[target_level]
        self.max_sentence_length = max_sentence_length
        self.max_long_word_percentage = max_long_word_percentage

    def check_text(
        self,
        text: str,
        file_path: Path = None,
    ) -> NorwegianReadabilityReport:
        """Check readability of Norwegian text."""
        analyzer = NorwegianTextAnalyzer(text)
        metrics = analyzer.compute_metrics()
        issues = []

        # Check LIX against target
        if metrics.lix > self.target_lix:
            issues.append(
                NorwegianReadabilityIssue(
                    issue_type="lix_score",
                    message=f"LIX score {metrics.lix:.1f} exceeds target {self.target_lix} ({self.target_level.value})",
                    suggestion="Bruk kortere setninger og enklere ord",
                    severity="warning",
                )
            )

        # Check for very long sentences
        for i, sent in enumerate(analyzer.sentences):
            words_in_sent = len(analyzer.WORD_PATTERN.findall(sent))
            if words_in_sent > self.max_sentence_length:
                issues.append(
                    NorwegianReadabilityIssue(
                        issue_type="long_sentence",
                        message=f"Setning med {words_in_sent} ord (maks anbefalt: {self.max_sentence_length})",
                        text_sample=sent[:80] + "..." if len(sent) > 80 else sent,
                        suggestion="Del opp i kortere setninger",
                        severity="info",
                    )
                )

        # Check long word percentage
        if metrics.long_word_percentage > self.max_long_word_percentage:
            issues.append(
                NorwegianReadabilityIssue(
                    issue_type="long_words",
                    message=f"{metrics.long_word_percentage:.1f}% lange ord (maks: {self.max_long_word_percentage}%)",
                    suggestion="Erstatt noen sammensatte ord med enklere alternativer",
                    severity="warning",
                )
            )

        # Check for excessive compound words
        compound_percentage = metrics.compound_word_count * 100 / max(1, metrics.word_count)
        if compound_percentage > 10:
            issues.append(
                NorwegianReadabilityIssue(
                    issue_type="compound_words",
                    message=f"Mange sammensatte ord ({metrics.compound_word_count} funnet)",
                    text_sample=", ".join(analyzer.compound_words[:5]),
                    suggestion="Vurder å dele opp noen sammensatte ord eller bruke enklere alternativer",
                    severity="info",
                )
            )

        # Check for very high LIX (academic level)
        if metrics.lix > 55:
            issues.append(
                NorwegianReadabilityIssue(
                    issue_type="academic_level",
                    message=f"Teksten er på akademisk nivå (LIX {metrics.lix:.1f})",
                    suggestion="For bredere publikum, forenkle teksten betydelig",
                    severity="error" if metrics.lix > 65 else "warning",
                )
            )

        passes = metrics.lix <= self.target_lix

        return NorwegianReadabilityReport(
            metrics=metrics,
            issues=issues,
            file_path=file_path,
            target_level=self.target_level,
            passes_target=passes,
            compound_words=analyzer.compound_words,
        )

    def check_document(self, doc_path: Path) -> NorwegianReadabilityReport:
        """Check readability of a document."""
        content = doc_path.read_text(encoding="utf-8")

        # Remove frontmatter
        if content.startswith("---"):
            try:
                end = content.index("---", 3)
                content = content[end + 3 :]
            except ValueError:
                pass

        return self.check_text(content, doc_path)

    def check_project(self, project, language: str = "no") -> dict:
        """
        Check readability of Norwegian content in project.

        Args:
            project: Media Engine project
            language: Language code to check ("no", "nb", "nn")

        Returns:
            Summary dict with all reports
        """
        reports = []
        lang_dir = project.content_dir / language

        if not lang_dir.exists():
            return {"error": f"Language directory not found: {language}"}

        for md_file in lang_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(project.content_dir)
                report = self.check_document(md_file)
                reports.append(
                    {
                        "file": str(rel_path),
                        "lix": report.metrics.lix,
                        "lix_level": report.metrics.lix_level.value,
                        "word_count": report.metrics.word_count,
                        "reading_time": report.metrics.reading_time_minutes,
                        "passes_target": report.passes_target,
                        "issue_count": len(report.issues),
                    }
                )
            except (OSError, UnicodeDecodeError):
                pass

        if not reports:
            return {"error": "No documents found"}

        # Summary
        total = len(reports)
        passing = sum(1 for r in reports if r["passes_target"])
        avg_lix = sum(r["lix"] for r in reports) / total
        total_words = sum(r["word_count"] for r in reports)
        total_time = sum(r["reading_time"] for r in reports)

        return {
            "summary": {
                "language": language,
                "total_documents": total,
                "passing": passing,
                "failing": total - passing,
                "pass_rate": round(passing / total * 100, 1),
                "average_lix": round(avg_lix, 1),
                "total_word_count": total_words,
                "total_reading_time_minutes": round(total_time, 1),
            },
            "target_level": self.target_level.value,
            "target_lix": self.target_lix,
            "documents": reports,
        }


def check_norwegian_readability(
    project,
    target_level: NorwegianReadabilityLevel = NorwegianReadabilityLevel.MEDIUM,
) -> dict:
    """Convenience function to check Norwegian readability in project."""
    checker = NorwegianReadabilityChecker(target_level=target_level)
    return checker.check_project(project)


__all__ = [
    "NorwegianReadabilityLevel",
    "NorwegianReadabilityMetrics",
    "NorwegianReadabilityIssue",
    "NorwegianReadabilityReport",
    "NorwegianSyllableCounter",
    "NorwegianTextAnalyzer",
    "NorwegianReadabilityChecker",
    "check_norwegian_readability",
]
