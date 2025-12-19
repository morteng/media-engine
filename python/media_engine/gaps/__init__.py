"""
Content Gap Analysis for Media Engine

Identifies missing content by analyzing:
- Topic coverage vs expected topics
- Cross-references that don't exist
- Translation completeness
- Schema coverage
- Feature documentation coverage

Helps ensure comprehensive documentation.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GapType(str, Enum):
    """Types of content gaps."""

    MISSING_TOPIC = "missing_topic"
    MISSING_TRANSLATION = "missing_translation"
    MISSING_REFERENCE = "missing_reference"
    INCOMPLETE_SECTION = "incomplete_section"
    STALE_CONTENT = "stale_content"
    MISSING_EXAMPLE = "missing_example"
    MISSING_SCHEMA = "missing_schema"
    ORPHAN_CONTENT = "orphan_content"


class GapSeverity(str, Enum):
    """Severity of content gaps."""

    CRITICAL = "critical"  # Blocks publishing
    HIGH = "high"  # Should fix soon
    MEDIUM = "medium"  # Should address
    LOW = "low"  # Nice to have


@dataclass
class ContentGap:
    """A detected content gap."""

    gap_type: GapType
    severity: GapSeverity
    description: str
    location: Optional[str] = None
    suggestion: str = ""
    related_content: list[str] = field(default_factory=list)


@dataclass
class TopicCoverage:
    """Coverage analysis for a topic."""

    topic: str
    covered: bool
    documents: list[str] = field(default_factory=list)
    subtopics_total: int = 0
    subtopics_covered: int = 0


class TopicAnalyzer:
    """Analyzes topic coverage against expected topics."""

    def __init__(self, project):
        self.project = project

    def extract_topics_from_content(self) -> dict[str, list[str]]:
        """Extract topics from existing content based on headings."""
        from ..cms.document import Document

        topics = {}

        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                doc = Document.load(chapter)

                # Extract headings as topics
                headings = re.findall(r"^#+\s+(.+)$", doc.content, re.MULTILINE)

                rel_path = str(chapter.relative_to(self.project.root))

                for heading in headings:
                    topic = heading.strip().lower()
                    if topic not in topics:
                        topics[topic] = []
                    if rel_path not in topics[topic]:
                        topics[topic].append(rel_path)

        return topics

    def check_expected_topics(self, expected: list[str]) -> list[ContentGap]:
        """Check if expected topics are covered."""
        existing = self.extract_topics_from_content()
        existing_lower = {k.lower(): v for k, v in existing.items()}
        gaps = []

        for topic in expected:
            topic_lower = topic.lower()

            # Check for exact match or partial match
            covered = False
            matching_docs = []

            for existing_topic, docs in existing_lower.items():
                if topic_lower in existing_topic or existing_topic in topic_lower:
                    covered = True
                    matching_docs.extend(docs)

            if not covered:
                gaps.append(
                    ContentGap(
                        gap_type=GapType.MISSING_TOPIC,
                        severity=GapSeverity.MEDIUM,
                        description=f"Topic '{topic}' is not covered in documentation",
                        suggestion=f"Add a section or document covering: {topic}",
                    )
                )

        return gaps


class ReferenceAnalyzer:
    """Analyzes cross-references for broken or missing links."""

    # Pattern for internal references
    REF_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def __init__(self, project):
        self.project = project

    def find_broken_references(self) -> list[ContentGap]:
        """Find references to non-existent content."""
        from ..cms.document import Document

        gaps = []
        all_paths = set()

        # Collect all document paths
        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                rel = str(chapter.relative_to(self.project.content_dir))
                all_paths.add(rel)
                # Also add without extension
                all_paths.add(rel.rsplit(".", 1)[0])

        # Check references in each document
        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                doc = Document.load(chapter)
                doc_rel = str(chapter.relative_to(self.project.root))

                for match in self.REF_PATTERN.finditer(doc.content):
                    text, url = match.groups()

                    # Skip external URLs
                    if url.startswith(("http://", "https://", "mailto:", "#")):
                        continue

                    # Resolve relative path
                    if url.startswith("/"):
                        target = url.lstrip("/")
                    else:
                        target = str(
                            (chapter.parent / url).resolve().relative_to(self.project.content_dir)
                        )

                    # Remove anchor
                    target = target.split("#")[0]

                    # Check if target exists
                    target_path = self.project.content_dir / target
                    if not target_path.exists() and target not in all_paths:
                        # Check with .md extension
                        if not (self.project.content_dir / f"{target}.md").exists():
                            gaps.append(
                                ContentGap(
                                    gap_type=GapType.MISSING_REFERENCE,
                                    severity=GapSeverity.HIGH,
                                    description=f"Reference to '{url}' does not exist",
                                    location=doc_rel,
                                    suggestion=f"Create '{target}' or fix the reference",
                                )
                            )

        return gaps


class TranslationGapAnalyzer:
    """Analyzes translation completeness."""

    def __init__(self, project):
        self.project = project
        self.source_lang = project.source_language

    def find_missing_translations(self) -> list[ContentGap]:
        """Find content that hasn't been translated."""
        gaps = []

        # Get source documents
        source_docs = {}
        for chapter in self.project.list_chapters(self.source_lang):
            rel = str(chapter.relative_to(self.project.content_dir / self.source_lang))
            source_docs[rel] = chapter

        # Check each target language
        for lang in self.project.languages:
            if lang == self.source_lang:
                continue

            lang_dir = self.project.content_dir / lang
            existing = set()

            if lang_dir.exists():
                for chapter in self.project.list_chapters(lang):
                    rel = str(chapter.relative_to(lang_dir))
                    existing.add(rel)

            # Find missing
            for rel, source_path in source_docs.items():
                if rel not in existing:
                    gaps.append(
                        ContentGap(
                            gap_type=GapType.MISSING_TRANSLATION,
                            severity=GapSeverity.MEDIUM,
                            description=f"'{rel}' not translated to {lang}",
                            location=str(source_path.relative_to(self.project.root)),
                            suggestion=f"Create translation: {lang}/{rel}",
                            related_content=[str(source_path)],
                        )
                    )

        return gaps


class SchemaGapAnalyzer:
    """Analyzes schema coverage for documentation."""

    def __init__(self, project):
        self.project = project

    def find_undocumented_schema_fields(self) -> list[ContentGap]:
        """Find schema fields that aren't documented."""
        gaps = []

        # Load schema if exists
        schema_path = self.project.root / "schema.yaml"
        if not schema_path.exists():
            return gaps

        import yaml

        with open(schema_path) as f:
            schema = yaml.safe_load(f)

        if not schema or "properties" not in schema:
            return gaps

        # Collect all documented terms
        documented = set()
        from ..cms.document import Document

        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                doc = Document.load(chapter)
                content_lower = doc.content.lower()

                # Extract code blocks and terms
                for term in schema.get("properties", {}).keys():
                    if term.lower() in content_lower:
                        documented.add(term)

        # Find undocumented
        for field_name, field_config in schema.get("properties", {}).items():
            if field_name not in documented:
                gaps.append(
                    ContentGap(
                        gap_type=GapType.MISSING_SCHEMA,
                        severity=GapSeverity.LOW,
                        description=f"Schema field '{field_name}' is not documented",
                        suggestion=f"Add documentation for: {field_name}",
                    )
                )

        return gaps


class OrphanAnalyzer:
    """Finds orphan content not linked from anywhere."""

    def __init__(self, project):
        self.project = project

    def find_orphan_documents(self) -> list[ContentGap]:
        """Find documents not linked from any other document."""
        from ..cms.document import Document

        gaps = []
        all_docs = {}
        linked_docs = set()

        # Collect all documents
        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                rel = str(chapter.relative_to(self.project.content_dir))
                all_docs[rel] = chapter

        # Find all internal links
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for rel, path in all_docs.items():
            doc = Document.load(path)

            for match in link_pattern.finditer(doc.content):
                url = match.group(2)

                # Skip external
                if url.startswith(("http://", "https://", "mailto:")):
                    continue

                # Resolve path
                if url.startswith("/"):
                    target = url.lstrip("/")
                else:
                    target = str(
                        (path.parent / url).resolve().relative_to(self.project.content_dir)
                    )

                target = target.split("#")[0]
                if not target.endswith(".md"):
                    target += ".md"

                linked_docs.add(target)

        # Find orphans (excluding index files)
        for rel, path in all_docs.items():
            name = path.stem.lower()
            if name in ("index", "readme", "00_", "01_introduction", "introduksjon"):
                continue

            if rel not in linked_docs:
                # Check if it's a chapter 1 (entry point)
                if "01_" in path.name or "introduction" in path.name.lower():
                    continue

                gaps.append(
                    ContentGap(
                        gap_type=GapType.ORPHAN_CONTENT,
                        severity=GapSeverity.LOW,
                        description=f"'{rel}' is not linked from any other document",
                        location=rel,
                        suggestion="Add a link to this document from relevant content",
                    )
                )

        return gaps


class ContentGapAnalyzer:
    """
    Comprehensive content gap analysis.

    Usage:
        analyzer = ContentGapAnalyzer(project)
        report = analyzer.analyze()
    """

    def __init__(self, project, expected_topics: list[str] = None):
        self.project = project
        self.expected_topics = expected_topics or []

        self.topic_analyzer = TopicAnalyzer(project)
        self.reference_analyzer = ReferenceAnalyzer(project)
        self.translation_analyzer = TranslationGapAnalyzer(project)
        self.schema_analyzer = SchemaGapAnalyzer(project)
        self.orphan_analyzer = OrphanAnalyzer(project)

    def analyze(
        self,
        check_topics: bool = True,
        check_references: bool = True,
        check_translations: bool = True,
        check_schema: bool = True,
        check_orphans: bool = True,
    ) -> dict:
        """
        Run comprehensive gap analysis.

        Returns:
            Analysis report with all detected gaps
        """
        gaps = []

        if check_topics and self.expected_topics:
            gaps.extend(self.topic_analyzer.check_expected_topics(self.expected_topics))

        if check_references:
            gaps.extend(self.reference_analyzer.find_broken_references())

        if check_translations:
            gaps.extend(self.translation_analyzer.find_missing_translations())

        if check_schema:
            gaps.extend(self.schema_analyzer.find_undocumented_schema_fields())

        if check_orphans:
            gaps.extend(self.orphan_analyzer.find_orphan_documents())

        # Group by type
        by_type = {}
        for gap in gaps:
            if gap.gap_type not in by_type:
                by_type[gap.gap_type] = []
            by_type[gap.gap_type].append(
                {
                    "severity": gap.severity.value,
                    "description": gap.description,
                    "location": gap.location,
                    "suggestion": gap.suggestion,
                }
            )

        # Group by severity
        by_severity = {s: 0 for s in GapSeverity}
        for gap in gaps:
            by_severity[gap.severity] += 1

        return {
            "summary": {
                "total_gaps": len(gaps),
                "critical": by_severity[GapSeverity.CRITICAL],
                "high": by_severity[GapSeverity.HIGH],
                "medium": by_severity[GapSeverity.MEDIUM],
                "low": by_severity[GapSeverity.LOW],
                "blocks_publish": by_severity[GapSeverity.CRITICAL] > 0,
            },
            "by_type": {k.value: v for k, v in by_type.items()},
            "gaps": [
                {
                    "type": g.gap_type.value,
                    "severity": g.severity.value,
                    "description": g.description,
                    "location": g.location,
                    "suggestion": g.suggestion,
                }
                for g in gaps
            ],
        }


def analyze_gaps(project, expected_topics: list[str] = None) -> dict:
    """Convenience function to analyze content gaps."""
    analyzer = ContentGapAnalyzer(project, expected_topics=expected_topics)
    return analyzer.analyze()


__all__ = [
    "GapType",
    "GapSeverity",
    "ContentGap",
    "ContentGapAnalyzer",
    "analyze_gaps",
]
