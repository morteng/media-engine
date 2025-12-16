"""
Tests for media_engine.builders module.
"""

from media_engine.builders.html import HTMLBuilder, HTMLConfig
from media_engine.builders.pptx import PPTXBuilder, SlideContent
from media_engine.builders.xlsx import Column, XLSXBuilder
from media_engine.core.theme import COPPER_AND_CREAM


class TestHTMLBuilder:
    """Tests for HTMLBuilder class."""

    def test_build_basic_html(self):
        """Test building basic HTML from markdown."""
        builder = HTMLBuilder()
        html = builder.build("# Hello World\n\nThis is a test.", "Test")

        assert "<!DOCTYPE html>" in html
        assert "<title>Test</title>" in html
        assert "Hello World" in html
        assert "This is a test" in html

    def test_build_with_theme(self):
        """Test HTML uses theme colors."""
        builder = HTMLBuilder(theme=COPPER_AND_CREAM)
        html = builder.build("# Test", "Test")

        assert COPPER_AND_CREAM.colors.primary in html
        assert COPPER_AND_CREAM.colors.accent in html

    def test_build_with_toc(self):
        """Test HTML with table of contents."""
        builder = HTMLBuilder()
        config = HTMLConfig(include_toc=True)
        content = "# Heading 1\n\nContent\n\n## Heading 2\n\nMore content"
        html = builder.build(content, "Test", config)

        assert "Contents" in html or "toc" in html

    def test_build_from_file(self, sample_markdown):
        """Test building HTML from file."""
        builder = HTMLBuilder()
        html = builder.build_from_file(sample_markdown)

        assert "<!DOCTYPE html>" in html
        assert "Test Document" in html

    def test_save_html(self, temp_dir):
        """Test saving HTML to file."""
        builder = HTMLBuilder()
        html = builder.build("# Test", "Test")
        output_path = temp_dir / "test.html"

        result = builder.save(html, output_path)

        assert result.exists()
        assert result.read_text() == html


class TestPPTXBuilder:
    """Tests for PPTXBuilder class."""

    def test_create_builder(self):
        """Test creating PPTX builder."""
        builder = PPTXBuilder()
        assert builder.prs is not None

    def test_create_builder_with_theme(self):
        """Test creating builder with theme."""
        builder = PPTXBuilder(theme=COPPER_AND_CREAM)
        assert builder.theme.name == "Copper & Cream"

    def test_add_title_slide(self):
        """Test adding title slide."""
        builder = PPTXBuilder()
        builder.add_title_slide("Title", "Subtitle")
        assert len(builder.prs.slides) == 1

    def test_add_content_slide(self):
        """Test adding content slide."""
        builder = PPTXBuilder()
        builder.add_content_slide("Title", ["Point 1", "Point 2"])
        assert len(builder.prs.slides) == 1

    def test_add_quote_slide(self):
        """Test adding quote slide."""
        builder = PPTXBuilder()
        builder.add_quote_slide("A great quote", "Author")
        assert len(builder.prs.slides) == 1

    def test_add_section_slide(self):
        """Test adding section divider."""
        builder = PPTXBuilder()
        builder.add_section_slide("Section 1")
        assert len(builder.prs.slides) == 1

    def test_multiple_slides(self):
        """Test adding multiple slides."""
        builder = PPTXBuilder()
        builder.add_title_slide("Title", "Subtitle")
        builder.add_content_slide("Content", ["Point 1"])
        builder.add_quote_slide("Quote", "Author")
        assert len(builder.prs.slides) == 3

    def test_save_pptx(self, temp_dir):
        """Test saving PPTX file."""
        builder = PPTXBuilder()
        builder.add_title_slide("Test Presentation")
        output_path = temp_dir / "test.pptx"

        result = builder.save(output_path)

        assert result.exists()
        assert result.stat().st_size > 0

    def test_build_from_yaml(self, temp_dir):
        """Test building from YAML file."""
        yaml_content = """
title: "Test Deck"
slides:
  - type: title
    title: "Test Title"
  - type: content
    title: "Content"
    bullets:
      - "Point 1"
      - "Point 2"
"""
        yaml_path = temp_dir / "slides.yaml"
        yaml_path.write_text(yaml_content)

        builder = PPTXBuilder()
        builder.build_from_yaml(yaml_path)

        assert len(builder.prs.slides) == 3  # title + 2 slides

    def test_build_from_markdown(self, temp_dir):
        """Test building from Markdown file."""
        md_content = """# Main Title
Subtitle text

---

## Content Slide
- Point 1
- Point 2

---

> A great quote
> — Author
"""
        md_path = temp_dir / "slides.md"
        md_path.write_text(md_content)

        builder = PPTXBuilder()
        builder.build_from_markdown(md_path)

        assert len(builder.prs.slides) >= 2


class TestXLSXBuilder:
    """Tests for XLSXBuilder class."""

    def test_create_builder(self):
        """Test creating XLSX builder."""
        builder = XLSXBuilder()
        assert builder.wb is not None

    def test_create_builder_with_theme(self):
        """Test creating builder with theme."""
        builder = XLSXBuilder(theme=COPPER_AND_CREAM)
        assert builder.theme.name == "Copper & Cream"

    def test_add_sheet(self):
        """Test adding worksheet."""
        builder = XLSXBuilder()
        columns = [Column(name="Name"), Column(name="Value")]
        rows = [["Item A", 100], ["Item B", 200]]

        builder.add_sheet("Data", columns=columns, rows=rows)

        assert "Data" in builder.wb.sheetnames

    def test_add_sheet_with_title(self):
        """Test adding worksheet with title."""
        builder = XLSXBuilder()
        columns = [Column(name="A"), Column(name="B")]

        builder.add_sheet("Sheet1", title="Test Title", columns=columns)

        ws = builder.wb["Sheet1"]
        assert ws.cell(row=1, column=1).value == "Test Title"

    def test_column_formatting(self):
        """Test column format styles."""
        builder = XLSXBuilder()
        columns = [
            Column(name="Currency", format="currency"),
            Column(name="Percent", format="percent"),
            Column(name="Number", format="number"),
        ]
        rows = [[1000, 0.15, 42]]

        builder.add_sheet("Formats", columns=columns, rows=rows)

        # Sheet should exist
        assert "Formats" in builder.wb.sheetnames

    def test_save_xlsx(self, temp_dir):
        """Test saving XLSX file."""
        builder = XLSXBuilder()
        columns = [Column(name="A"), Column(name="B")]
        builder.add_sheet("Data", columns=columns, rows=[["x", "y"]])

        output_path = temp_dir / "test.xlsx"
        result = builder.save(output_path)

        assert result.exists()
        assert result.stat().st_size > 0

    def test_build_from_yaml(self, temp_dir):
        """Test building from YAML file."""
        yaml_content = """
sheets:
  - name: "Data"
    columns:
      - name: "Name"
        width: 20
      - name: "Value"
        format: number
    rows:
      - ["Item A", 100]
      - ["Item B", 200]
"""
        yaml_path = temp_dir / "data.yaml"
        yaml_path.write_text(yaml_content)

        builder = XLSXBuilder()
        builder.build_from_yaml(yaml_path)

        assert "Data" in builder.wb.sheetnames

    def test_build_from_dict(self):
        """Test building from dictionary."""
        data = {
            "Sheet1": {
                "headers": ["Name", "Value"],
                "rows": [["A", 1], ["B", 2]],
            }
        }

        builder = XLSXBuilder()
        builder.build_from_dict(data)

        assert "Sheet1" in builder.wb.sheetnames


class TestSlideContent:
    """Tests for SlideContent dataclass."""

    def test_default_values(self):
        """Test default values."""
        content = SlideContent(type="content")
        assert content.type == "content"
        assert content.title == ""
        assert content.bullets == []

    def test_with_values(self):
        """Test with values."""
        content = SlideContent(
            type="content",
            title="My Title",
            bullets=["Point 1", "Point 2"],
        )
        assert content.title == "My Title"
        assert len(content.bullets) == 2


class TestColumn:
    """Tests for Column dataclass."""

    def test_default_values(self):
        """Test default values."""
        col = Column(name="Test")
        assert col.name == "Test"
        assert col.width == 12
        assert col.format == "general"

    def test_with_format(self):
        """Test with format."""
        col = Column(name="Price", width=15, format="currency")
        assert col.format == "currency"
        assert col.width == 15
