"""
Translation Parity Matrix

Creates a visual translation parity matrix showing asset coverage across
all languages, making translation gaps immediately visible.

Features:
- Asset count by type and language
- Coverage percentage calculations
- Missing file identification
- Effort estimation (word count)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..core.project import Project


@dataclass
class TranslationEffort:
    """Estimated translation effort for a language."""

    language: str
    missing_files: int
    word_count: int
    estimated_hours: float  # Based on ~250 words/hour

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "language": self.language,
            "missing_files": self.missing_files,
            "word_count": self.word_count,
            "estimated_hours": self.estimated_hours,
        }


@dataclass
class ParityReport:
    """Complete parity analysis report."""

    matrix: dict[str, dict[str, int]]  # category -> lang -> count
    missing: dict[str, list[str]]  # lang -> missing file paths
    coverage: dict[str, float]  # lang -> percentage
    effort_estimate: dict[str, TranslationEffort]
    primary_language: str = "en"
    languages: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "matrix": self.matrix,
            "missing": self.missing,
            "coverage": self.coverage,
            "effort_estimate": {k: v.to_dict() for k, v in self.effort_estimate.items()},
            "primary_language": self.primary_language,
            "languages": self.languages,
            "categories": self.categories,
        }

    def format_table(self) -> str:
        """Format as ASCII table."""
        if not self.categories or not self.languages:
            return "No content found"

        lines = []

        # Header
        header = f"{'Asset Type':<20}"
        for lang in self.languages:
            header += f"{lang:>8}"
        header += f"{'Coverage':>12}"
        lines.append(header)
        lines.append("─" * len(header))

        # Rows
        for category in self.categories:
            row = f"{category:<20}"
            for lang in self.languages:
                count = self.matrix.get(category, {}).get(lang, 0)
                row += f"{count:>8}"

            # Calculate category coverage
            primary_count = self.matrix.get(category, {}).get(self.primary_language, 0)
            if primary_count > 0:
                total = sum(self.matrix.get(category, {}).values())
                target_total = primary_count * len(self.languages)
                pct = (total / target_total) * 100 if target_total > 0 else 0
                status = "✓" if pct >= 100 else "⚠️" if pct >= 50 else "❌"
                row += f"{pct:>8.0f}%  {status}"
            else:
                row += f"{'N/A':>12}"

            lines.append(row)

        # Total row
        lines.append("─" * len(header))
        total_row = f"{'TOTAL':<20}"
        for lang in self.languages:
            total = sum(self.matrix.get(cat, {}).get(lang, 0) for cat in self.categories)
            total_row += f"{total:>8}"
        total_row += f"{self.coverage.get(self.primary_language, 0):>8.0f}%"
        lines.append(total_row)

        return "\n".join(lines)


@dataclass
class ParityAnalyzer:
    """
    Analyzes translation parity across languages.

    Usage:
        analyzer = ParityAnalyzer(project)
        report = analyzer.analyze()
        print(report.format_table())

        # Get missing files for a language
        missing = analyzer.get_missing_for_language("no")
    """

    project: Project
    primary_language: str = "en"
    words_per_hour: int = 250  # Translation speed estimate

    def analyze(self) -> ParityReport:
        """
        Analyze translation parity across all languages.

        Returns:
            ParityReport with complete parity analysis
        """
        matrix: dict[str, dict[str, int]] = {}
        files_by_lang: dict[str, set[str]] = {}
        languages: set[str] = set()
        categories: set[str] = set()

        if not self.project.content_dir.exists():
            return ParityReport(
                matrix={},
                missing={},
                coverage={},
                effort_estimate={},
                primary_language=self.primary_language,
            )

        # Scan all content files
        for content_file in self.project.content_dir.rglob("*"):
            if not content_file.is_file():
                continue

            # Skip non-content files
            if content_file.suffix not in (".md", ".yaml", ".yml", ".json"):
                continue

            try:
                rel_path = content_file.relative_to(self.project.content_dir)
                parts = rel_path.parts

                if len(parts) < 2:
                    continue

                # First part is language
                lang = parts[0]
                languages.add(lang)

                # Second part is category
                category = parts[1]
                categories.add(category)

                # Track file (without language prefix)
                file_key = "/".join(parts[1:])
                if lang not in files_by_lang:
                    files_by_lang[lang] = set()
                files_by_lang[lang].add(file_key)

                # Update matrix
                if category not in matrix:
                    matrix[category] = {}
                matrix[category][lang] = matrix[category].get(lang, 0) + 1

            except ValueError:
                continue

        # Sort languages and categories
        sorted_langs = sorted(languages)
        if self.primary_language in sorted_langs:
            sorted_langs.remove(self.primary_language)
            sorted_langs.insert(0, self.primary_language)

        sorted_categories = sorted(categories)

        # Calculate coverage and missing files
        coverage: dict[str, float] = {}
        missing: dict[str, list[str]] = {}
        effort_estimate: dict[str, TranslationEffort] = {}

        primary_files = files_by_lang.get(self.primary_language, set())
        primary_total = len(primary_files)

        for lang in sorted_langs:
            lang_files = files_by_lang.get(lang, set())

            if lang == self.primary_language:
                coverage[lang] = 100.0
                missing[lang] = []
            else:
                # Files in primary but not in this language
                missing_files = primary_files - lang_files
                missing[lang] = sorted(list(missing_files))

                # Coverage percentage
                if primary_total > 0:
                    coverage[lang] = (len(lang_files) / primary_total) * 100
                else:
                    coverage[lang] = 100.0

            # Calculate effort estimate
            effort_estimate[lang] = self._estimate_effort(lang, missing.get(lang, []))

        return ParityReport(
            matrix=matrix,
            missing=missing,
            coverage=coverage,
            effort_estimate=effort_estimate,
            primary_language=self.primary_language,
            languages=sorted_langs,
            categories=sorted_categories,
        )

    def get_missing_for_language(self, lang: str) -> list[Path]:
        """
        Get list of missing translations for a specific language.

        Args:
            lang: Target language code

        Returns:
            List of paths that need translation
        """
        report = self.analyze()
        missing_keys = report.missing.get(lang, [])

        # Convert to full paths
        return [
            self.project.content_dir / self.primary_language / key
            for key in missing_keys
        ]

    def estimate_effort(self, lang: str) -> TranslationEffort:
        """
        Estimate translation effort for a language.

        Args:
            lang: Target language code

        Returns:
            TranslationEffort with word count and time estimate
        """
        report = self.analyze()
        return report.effort_estimate.get(
            lang,
            TranslationEffort(language=lang, missing_files=0, word_count=0, estimated_hours=0),
        )

    def get_category_coverage(self) -> dict[str, dict[str, float]]:
        """
        Get coverage percentage by category and language.

        Returns:
            Dict of category -> lang -> percentage
        """
        report = self.analyze()
        category_coverage: dict[str, dict[str, float]] = {}

        for category in report.categories:
            category_coverage[category] = {}
            primary_count = report.matrix.get(category, {}).get(self.primary_language, 0)

            for lang in report.languages:
                lang_count = report.matrix.get(category, {}).get(lang, 0)
                if primary_count > 0:
                    category_coverage[category][lang] = (lang_count / primary_count) * 100
                else:
                    category_coverage[category][lang] = 100.0

        return category_coverage

    def _estimate_effort(self, lang: str, missing_files: list[str]) -> TranslationEffort:
        """Calculate translation effort estimate."""
        if not missing_files or lang == self.primary_language:
            return TranslationEffort(
                language=lang,
                missing_files=0,
                word_count=0,
                estimated_hours=0,
            )

        total_words = 0

        for file_key in missing_files:
            # Look up source file
            source_path = self.project.content_dir / self.primary_language / file_key

            if source_path.exists() and source_path.suffix == ".md":
                try:
                    content = source_path.read_text(encoding="utf-8")
                    total_words += len(content.split())
                except (OSError, UnicodeDecodeError):
                    # Estimate based on average document size
                    total_words += 500

        estimated_hours = total_words / self.words_per_hour if total_words > 0 else 0

        return TranslationEffort(
            language=lang,
            missing_files=len(missing_files),
            word_count=total_words,
            estimated_hours=round(estimated_hours, 1),
        )


def analyze_parity(project: Project, primary_language: str = "en") -> ParityReport:
    """Convenience function to analyze translation parity."""
    analyzer = ParityAnalyzer(project, primary_language=primary_language)
    return analyzer.analyze()
