"""
Tests for media_engine.core.sections module - section-level content tracking.
"""


from media_engine.core.sections import (
    ChangeType,
    DocumentSections,
    Section,
    SectionChangeReport,
    SectionDiff,
    analyze_changes,
    compare_sections,
    get_unchanged_sections,
    parse_sections,
)


class TestSection:
    """Tests for Section dataclass."""

    def test_section_creation(self):
        """Test creating a section with basic attributes."""
        section = Section(
            heading="Introduction",
            level=1,
            content="This is the intro content.",
            content_hash="abc123",
            line_start=1,
            line_end=5,
        )
        assert section.heading == "Introduction"
        assert section.level == 1
        assert section.content_hash == "abc123"

    def test_normalized_heading(self):
        """Test heading normalization for cross-language matching."""
        section = Section(
            heading="1. Introduction",
            level=1,
            content="Content",
            content_hash="abc123",
            line_start=1,
            line_end=5,
        )
        # Numbered prefix should be stripped
        assert section.normalized_heading == "introduction"

    def test_normalized_heading_chapter_prefix(self):
        """Test normalization strips chapter prefixes."""
        section = Section(
            heading="Chapter 1: Getting Started",
            level=1,
            content="Content",
            content_hash="abc123",
            line_start=1,
            line_end=5,
        )
        assert section.normalized_heading == "getting started"

    def test_to_dict(self):
        """Test section serialization."""
        section = Section(
            heading="Overview",
            level=2,
            content="Overview content",
            content_hash="def456",
            line_start=10,
            line_end=20,
        )
        data = section.to_dict()
        assert data["heading"] == "Overview"
        assert data["level"] == 2
        assert data["content_hash"] == "def456"
        assert "content" not in data  # Content not serialized

    def test_from_dict(self):
        """Test section deserialization."""
        data = {
            "heading": "Overview",
            "level": 2,
            "content_hash": "def456",
            "line_start": 10,
            "line_end": 20,
            "normalized_heading": "overview",
        }
        section = Section.from_dict(data, content="Restored content")
        assert section.heading == "Overview"
        assert section.level == 2
        assert section.content == "Restored content"


class TestParseSections:
    """Tests for parse_sections function."""

    def test_simple_document(self):
        """Test parsing a simple markdown document."""
        content = """# Title

Introduction text here.

## Section One

Section one content.

## Section Two

Section two content.
"""
        sections = parse_sections(content)
        assert len(sections.sections) == 3
        assert sections.sections[0].heading == "Title"
        assert sections.sections[0].level == 1
        assert sections.sections[1].heading == "Section One"
        assert sections.sections[2].heading == "Section Two"

    def test_nested_headings(self):
        """Test parsing document with nested headings."""
        content = """# Main

## Sub One

### Sub Sub

## Sub Two
"""
        sections = parse_sections(content)
        assert len(sections.sections) == 4
        levels = [s.level for s in sections.sections]
        assert levels == [1, 2, 3, 2]

    def test_content_before_first_heading(self):
        """Test handling content before first heading."""
        content = """Some intro text before any heading.

# First Heading

Content here.
"""
        sections = parse_sections(content)
        # Should have an (Introduction) pseudo-section
        intro_sections = [s for s in sections.sections if s.heading == "(Introduction)"]
        assert len(intro_sections) == 1
        assert "intro text" in intro_sections[0].content

    def test_empty_document(self):
        """Test parsing empty document."""
        sections = parse_sections("")
        assert len(sections.sections) == 0
        assert sections.document_hash != ""  # Hash of empty string

    def test_section_content_hashes(self):
        """Test that each section gets a unique hash."""
        content = """# One

Content A

# Two

Content B
"""
        sections = parse_sections(content)
        hashes = [s.content_hash for s in sections.sections]
        # All hashes should be different since content is different
        assert len(hashes) == len(set(hashes))

    def test_get_hashes(self):
        """Test getting heading -> hash mapping."""
        content = """# First

First content.

# Second

Second content.
"""
        sections = parse_sections(content)
        hashes = sections.get_hashes()
        assert "First" in hashes
        assert "Second" in hashes
        assert len(hashes) == 2


class TestDocumentSections:
    """Tests for DocumentSections dataclass."""

    def test_get_by_heading(self):
        """Test looking up sections by heading."""
        sections = [
            Section("Intro", 1, "content", "hash1", 1, 5),
            Section("Details", 2, "content", "hash2", 6, 10),
        ]
        doc = DocumentSections(sections=sections, document_hash="doc123")

        found = doc.get_by_heading("Intro")
        assert found is not None
        assert found.content_hash == "hash1"

        not_found = doc.get_by_heading("Missing")
        assert not_found is None

    def test_get_by_normalized(self):
        """Test looking up sections by normalized heading."""
        sections = [
            Section("1. Introduction", 1, "content", "hash1", 1, 5),
        ]
        doc = DocumentSections(sections=sections, document_hash="doc123")

        found = doc.get_by_normalized("introduction")
        assert found is not None
        assert found.heading == "1. Introduction"

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        sections = [
            Section("Intro", 1, "content", "hash1", 1, 5),
            Section("Details", 2, "content", "hash2", 6, 10),
        ]
        doc = DocumentSections(sections=sections, document_hash="doc123")

        data = doc.to_dict()
        restored = DocumentSections.from_dict(data)

        assert restored.document_hash == "doc123"
        assert len(restored.sections) == 2
        assert restored.get_by_heading("Intro") is not None


class TestCompareSections:
    """Tests for section comparison functions."""

    def test_detect_modified_section(self):
        """Test detecting a modified section."""
        old = DocumentSections(
            sections=[Section("Intro", 1, "old content", "hash_old", 1, 5)],
            document_hash="doc_old",
        )
        new = DocumentSections(
            sections=[Section("Intro", 1, "new content", "hash_new", 1, 5)],
            document_hash="doc_new",
        )

        diffs = compare_sections(old, new)
        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.MODIFIED
        assert diffs[0].heading == "Intro"

    def test_detect_added_section(self):
        """Test detecting a new section."""
        old = DocumentSections(
            sections=[Section("Intro", 1, "content", "hash1", 1, 5)],
            document_hash="doc_old",
        )
        new = DocumentSections(
            sections=[
                Section("Intro", 1, "content", "hash1", 1, 5),
                Section("New Section", 2, "new content", "hash2", 6, 10),
            ],
            document_hash="doc_new",
        )

        diffs = compare_sections(old, new)
        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.ADDED
        assert diffs[0].heading == "New Section"

    def test_detect_removed_section(self):
        """Test detecting a removed section."""
        old = DocumentSections(
            sections=[
                Section("Intro", 1, "content", "hash1", 1, 5),
                Section("Old Section", 2, "old content", "hash2", 6, 10),
            ],
            document_hash="doc_old",
        )
        new = DocumentSections(
            sections=[Section("Intro", 1, "content", "hash1", 1, 5)],
            document_hash="doc_new",
        )

        diffs = compare_sections(old, new)
        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.REMOVED
        assert diffs[0].heading == "Old Section"

    def test_unchanged_sections(self):
        """Test identifying unchanged sections."""
        sections = [
            Section("Intro", 1, "content", "hash1", 1, 5),
            Section("Details", 2, "details", "hash2", 6, 10),
        ]
        old = DocumentSections(sections=sections, document_hash="doc1")
        new = DocumentSections(sections=sections, document_hash="doc1")

        diffs = compare_sections(old, new)
        assert len(diffs) == 0  # No changes

        unchanged = get_unchanged_sections(old, new)
        assert "Intro" in unchanged
        assert "Details" in unchanged


class TestAnalyzeChanges:
    """Tests for analyze_changes function."""

    def test_full_analysis(self):
        """Test comprehensive change analysis."""
        old = DocumentSections(
            sections=[
                Section("Intro", 1, "content", "hash1", 1, 5),
                Section("Old", 2, "old content", "hash_old", 6, 10),
                Section("Details", 2, "details", "hash3", 11, 15),
            ],
            document_hash="doc_old",
        )
        new = DocumentSections(
            sections=[
                Section("Intro", 1, "changed!", "hash_new", 1, 5),
                Section("Details", 2, "details", "hash3", 6, 10),
                Section("New Section", 2, "new", "hash4", 11, 15),
            ],
            document_hash="doc_new",
        )

        report = analyze_changes(old, new)

        assert isinstance(report, SectionChangeReport)
        assert report.total_sections_old == 3
        assert report.total_sections_new == 3
        assert len(report.modified) == 1
        assert len(report.added) == 1
        assert len(report.removed) == 1
        assert len(report.unchanged) == 1
        assert report.has_changes is True
        assert "modified" in report.change_summary

    def test_no_changes(self):
        """Test report when nothing changed."""
        sections = [Section("Intro", 1, "content", "hash1", 1, 5)]
        doc = DocumentSections(sections=sections, document_hash="doc1")

        report = analyze_changes(doc, doc)

        assert report.has_changes is False
        assert report.change_summary == "No changes"
        assert len(report.unchanged) == 1

    def test_report_serialization(self):
        """Test SectionChangeReport to_dict."""
        report = SectionChangeReport(
            total_sections_old=5,
            total_sections_new=6,
            added=[
                SectionDiff("New", "new", ChangeType.ADDED, new_hash="abc")
            ],
            removed=[],
            modified=[],
            unchanged=["Intro", "Details"],
        )

        data = report.to_dict()
        assert data["total_sections_old"] == 5
        assert data["total_sections_new"] == 6
        assert len(data["added"]) == 1
        assert data["has_changes"] is True


class TestNormalizedMatching:
    """Tests for cross-language matching with normalized headings."""

    def test_match_by_normalized_heading(self):
        """Test matching sections across different numbering schemes."""
        old = DocumentSections(
            sections=[
                Section("1. Introduction", 1, "content", "hash1", 1, 5),
                Section("2. Overview", 2, "overview", "hash2", 6, 10),
            ],
            document_hash="doc_old",
        )
        new = DocumentSections(
            sections=[
                Section("Introduction", 1, "content", "hash1", 1, 5),
                Section("Overview", 2, "changed overview", "hash_new", 6, 10),
            ],
            document_hash="doc_new",
        )

        # With normalized matching, "1. Introduction" matches "Introduction"
        diffs = compare_sections(old, new, use_normalized=True)

        # Should detect only one modification (Overview changed)
        modified = [d for d in diffs if d.change_type == ChangeType.MODIFIED]
        assert len(modified) == 1
        assert modified[0].normalized_heading == "overview"

    def test_chapter_prefix_matching(self):
        """Test matching with Chapter prefixes."""
        old = DocumentSections(
            sections=[
                Section("Chapter 1: Getting Started", 1, "old", "hash1", 1, 5),
            ],
            document_hash="doc_old",
        )
        new = DocumentSections(
            sections=[
                Section("Getting Started", 1, "new", "hash2", 1, 5),
            ],
            document_hash="doc_new",
        )

        diffs = compare_sections(old, new, use_normalized=True)
        modified = [d for d in diffs if d.change_type == ChangeType.MODIFIED]
        assert len(modified) == 1  # Should match and detect modification


class TestSectionDiff:
    """Tests for SectionDiff dataclass."""

    def test_diff_serialization(self):
        """Test SectionDiff to_dict."""
        diff = SectionDiff(
            heading="Overview",
            normalized_heading="overview",
            change_type=ChangeType.MODIFIED,
            old_hash="old123",
            new_hash="new456",
            old_line_range=(5, 10),
            new_line_range=(5, 12),
        )

        data = diff.to_dict()
        assert data["heading"] == "Overview"
        assert data["change_type"] == "modified"
        assert data["old_hash"] == "old123"
        assert data["new_hash"] == "new456"
        assert data["old_line_range"] == [5, 10]
        assert data["new_line_range"] == [5, 12]
