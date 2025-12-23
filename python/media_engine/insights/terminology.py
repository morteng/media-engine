"""
Terminology Consistency Checker

Detects when the same concept uses different terminology across documents,
ensuring consistent language throughout the documentation.

Detection methods:
- Synonym detection (user/customer/client)
- Capitalization variations (Media Engine/media engine)
- Abbreviation consistency (CLI defined vs used)
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..core.project import Project


@dataclass
class Location:
    """Location of a term occurrence."""

    document: Path
    line_number: int
    context: str  # Surrounding text

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "line_number": self.line_number,
            "context": self.context,
        }


@dataclass
class TermInconsistency:
    """A detected terminology inconsistency."""

    term_group: list[str]
    occurrences: dict[str, list[Location]]  # term -> locations
    recommended: str
    severity: str  # "high", "medium", "low"
    issue_type: str  # "synonym", "capitalization", "abbreviation"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "term_group": self.term_group,
            "occurrences": {
                term: [loc.to_dict() for loc in locs] for term, locs in self.occurrences.items()
            },
            "recommended": self.recommended,
            "severity": self.severity,
            "issue_type": self.issue_type,
        }

    @property
    def total_occurrences(self) -> int:
        """Total number of occurrences across all terms."""
        return sum(len(locs) for locs in self.occurrences.values())


@dataclass
class TermDefinition:
    """Definition of a canonical term."""

    canonical: str
    alternatives: list[str]
    definition: str = ""
    context: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "canonical": self.canonical,
            "alternatives": self.alternatives,
            "definition": self.definition,
            "context": self.context,
        }


# Common synonym groups (can be extended via terminology.yaml)
DEFAULT_SYNONYM_GROUPS = [
    {"canonical": "user", "alternatives": ["customer", "client", "end user", "end-user"]},
    {"canonical": "document", "alternatives": ["file", "page", "doc"]},
    {"canonical": "build", "alternatives": ["generate", "create", "produce"]},
    {"canonical": "project", "alternatives": ["repo", "repository", "codebase"]},
    {"canonical": "configure", "alternatives": ["setup", "set up", "config"]},
]

# Abbreviations that should be defined before use
COMMON_ABBREVIATIONS = [
    "CLI",
    "API",
    "HTML",
    "PDF",
    "YAML",
    "JSON",
    "MCP",
    "URL",
]


@dataclass
class TerminologyChecker:
    """
    Checks for terminology consistency across documents.

    Usage:
        checker = TerminologyChecker(project)
        issues = checker.find_inconsistencies()
        for issue in issues:
            print(f"Inconsistent: {issue.term_group} - use '{issue.recommended}'")
    """

    project: Project
    term_registry: dict[str, TermDefinition] = field(default_factory=dict)

    def __post_init__(self):
        # Load default synonyms
        for group in DEFAULT_SYNONYM_GROUPS:
            self.term_registry[group["canonical"]] = TermDefinition(
                canonical=group["canonical"],
                alternatives=group["alternatives"],
            )

        # Try to load custom registry
        self._load_custom_registry()

    def _load_custom_registry(self) -> None:
        """Load custom terminology from terminology.yaml."""
        registry_path = self.project.root / "terminology.yaml"
        if not registry_path.exists():
            registry_path = self.project.root / ".media-engine" / "terminology.yaml"

        if registry_path.exists():
            try:
                data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
                if data and "terms" in data:
                    for key, term_data in data["terms"].items():
                        self.term_registry[key] = TermDefinition(
                            canonical=term_data.get("canonical", key),
                            alternatives=term_data.get("alternatives", []),
                            definition=term_data.get("definition", ""),
                            context=term_data.get("context", ""),
                        )
            except (yaml.YAMLError, OSError):
                pass

    def load_term_registry(self, path: Path) -> None:
        """Load a custom terminology registry."""
        if not path.exists():
            return

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if data and "terms" in data:
                for key, term_data in data["terms"].items():
                    self.term_registry[key] = TermDefinition(
                        canonical=term_data.get("canonical", key),
                        alternatives=term_data.get("alternatives", []),
                        definition=term_data.get("definition", ""),
                        context=term_data.get("context", ""),
                    )
        except (yaml.YAMLError, OSError):
            pass

    def find_inconsistencies(self) -> list[TermInconsistency]:
        """
        Find all terminology inconsistencies in the project.

        Returns:
            List of TermInconsistency instances
        """
        issues: list[TermInconsistency] = []

        # Find synonym inconsistencies
        issues.extend(self._find_synonym_issues())

        # Find capitalization inconsistencies
        issues.extend(self._find_capitalization_issues())

        # Find undefined abbreviations
        issues.extend(self._find_abbreviation_issues())

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        issues.sort(key=lambda x: severity_order.get(x.severity, 2))

        return issues

    def find_capitalization_issues(self) -> list[TermInconsistency]:
        """Find capitalization variations only."""
        return self._find_capitalization_issues()

    def find_undefined_abbreviations(self) -> list[str]:
        """Find abbreviations used without definition."""
        issues = self._find_abbreviation_issues()
        return [issue.recommended for issue in issues]

    def suggest_standardization(self) -> dict[str, str]:
        """
        Get suggestions for term standardization.

        Returns:
            Dict mapping non-canonical terms to canonical versions
        """
        suggestions: dict[str, str] = {}

        for term_def in self.term_registry.values():
            for alt in term_def.alternatives:
                suggestions[alt] = term_def.canonical

        return suggestions

    def get_term_usage(self, term: str) -> dict[str, list[Location]]:
        """
        Get all locations where a term (or its alternatives) is used.

        Args:
            term: Term to search for

        Returns:
            Dict mapping term variations to their locations
        """
        term_lower = term.lower()

        # Get the term group
        term_def = self.term_registry.get(term_lower)
        if term_def:
            search_terms = [term_def.canonical] + term_def.alternatives
        else:
            search_terms = [term]

        usage: dict[str, list[Location]] = defaultdict(list)

        if not self.project.content_dir.exists():
            return usage

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel_path = md_file.relative_to(self.project.content_dir)
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for search_term in search_terms:
                        pattern = re.compile(rf"\b{re.escape(search_term)}\b", re.IGNORECASE)
                        if pattern.search(line):
                            # Find actual case used
                            match = pattern.search(line)
                            if match:
                                actual_term = match.group(0)
                                usage[actual_term].append(
                                    Location(
                                        document=rel_path,
                                        line_number=line_num,
                                        context=line.strip()[:100],
                                    )
                                )

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        return dict(usage)

    def _find_synonym_issues(self) -> list[TermInconsistency]:
        """Find documents using non-canonical terms."""
        issues: list[TermInconsistency] = []

        for term_def in self.term_registry.values():
            usage = self.get_term_usage(term_def.canonical)

            # Check if multiple terms from the group are used
            terms_used = [t for t in usage.keys() if usage[t]]
            if len(terms_used) > 1:
                # Calculate severity based on usage disparity
                total = sum(len(usage[t]) for t in terms_used)
                canonical_count = len(usage.get(term_def.canonical, []))
                severity = "high" if canonical_count < total * 0.5 else "medium"

                issues.append(
                    TermInconsistency(
                        term_group=terms_used,
                        occurrences={t: usage[t] for t in terms_used},
                        recommended=term_def.canonical,
                        severity=severity,
                        issue_type="synonym",
                    )
                )

        return issues

    def _find_capitalization_issues(self) -> list[TermInconsistency]:
        """Find capitalization variations of the same term."""
        issues: list[TermInconsistency] = []
        term_variations: dict[str, dict[str, list[Location]]] = defaultdict(
            lambda: defaultdict(list)
        )

        if not self.project.content_dir.exists():
            return issues

        # Collect all multi-word terms and their variations
        multi_word_pattern = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)+)\b")

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel_path = md_file.relative_to(self.project.content_dir)
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    # Find potential multi-word terms
                    for match in multi_word_pattern.finditer(line):
                        term = match.group(1)
                        key = term.lower()

                        # Skip very common phrases
                        if key in ("the project", "the document", "the file"):
                            continue

                        term_variations[key][term].append(
                            Location(
                                document=rel_path,
                                line_number=line_num,
                                context=line.strip()[:100],
                            )
                        )

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Find terms with multiple variations
        for key, variations in term_variations.items():
            if len(variations) > 1:
                # Recommend most common variant
                recommended = max(variations.keys(), key=lambda t: len(variations[t]))

                issues.append(
                    TermInconsistency(
                        term_group=list(variations.keys()),
                        occurrences=dict(variations),
                        recommended=recommended,
                        severity="low",
                        issue_type="capitalization",
                    )
                )

        return issues

    def _find_abbreviation_issues(self) -> list[TermInconsistency]:
        """Find abbreviations used without definition."""
        issues: list[TermInconsistency] = []

        if not self.project.content_dir.exists():
            return issues

        for abbrev in COMMON_ABBREVIATIONS:
            usage: dict[str, list[Location]] = defaultdict(list)
            defined_in: set[str] = set()

            for md_file in self.project.content_dir.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    rel_path = md_file.relative_to(self.project.content_dir)
                    lines = content.split("\n")

                    # Check if abbreviation is defined in this doc
                    definition_pattern = re.compile(
                        rf"\([^)]*{abbrev}[^)]*\)|{abbrev}\s*[-:]\s*\w",
                        re.IGNORECASE,
                    )
                    if definition_pattern.search(content):
                        defined_in.add(str(rel_path))

                    # Find usages
                    abbrev_pattern = re.compile(rf"\b{abbrev}\b")
                    for line_num, line in enumerate(lines, 1):
                        if abbrev_pattern.search(line):
                            usage[abbrev].append(
                                Location(
                                    document=rel_path,
                                    line_number=line_num,
                                    context=line.strip()[:100],
                                )
                            )

                except (OSError, UnicodeDecodeError, ValueError):
                    pass

            # Report if used in documents where not defined
            if usage[abbrev]:
                docs_with_usage = set(str(loc.document) for loc in usage[abbrev])
                undefined_docs = docs_with_usage - defined_in

                if undefined_docs and len(undefined_docs) > len(docs_with_usage) * 0.5:
                    issues.append(
                        TermInconsistency(
                            term_group=[abbrev],
                            occurrences=usage,
                            recommended=f"Define {abbrev} on first use",
                            severity="low",
                            issue_type="abbreviation",
                        )
                    )

        return issues


def check_terminology(project: Project) -> list[TermInconsistency]:
    """Convenience function to check terminology consistency."""
    checker = TerminologyChecker(project)
    return checker.find_inconsistencies()
