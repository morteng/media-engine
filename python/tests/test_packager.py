"""
Tests for media_engine.publish.packager module.
"""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from media_engine.publish.packager import (
    PublishConfig,
    PublishResult,
    collect_deliverables,
    copy_documents,
    create_zip_archive,
    generate_navigation_indexes,
    publish_project,
)
from media_engine.templates.html_index import DeliverableCategory, DeliverableItem


class TestPublishConfig:
    """Tests for PublishConfig dataclass."""

    def test_default_values(self, temp_dir):
        """Test default configuration values."""
        config = PublishConfig(output_dir=temp_dir)
        assert config.output_dir == temp_dir
        assert config.include_fonts is True
        assert config.include_diagrams is True
        assert config.include_videos is True
        assert config.include_source is False
        assert config.generate_indexes is True
        assert config.zip_output is False
        assert config.console_output is True

    def test_custom_values(self, temp_dir):
        """Test custom configuration values."""
        config = PublishConfig(
            output_dir=temp_dir,
            include_fonts=False,
            include_diagrams=False,
            include_videos=False,
            include_source=True,
            generate_indexes=False,
            zip_output=True,
            console_output=False,
        )
        assert config.include_fonts is False
        assert config.include_diagrams is False
        assert config.include_videos is False
        assert config.include_source is True
        assert config.generate_indexes is False
        assert config.zip_output is True
        assert config.console_output is False


class TestPublishResult:
    """Tests for PublishResult dataclass."""

    def test_default_values(self, temp_dir):
        """Test default result values."""
        result = PublishResult(output_dir=temp_dir)
        assert result.output_dir == temp_dir
        assert result.root_index is None
        assert result.language_indexes == {}
        assert result.documents_copied == 0
        assert result.assets_bundled == 0
        assert result.success is True
        assert result.errors == []

    def test_with_values(self, temp_dir):
        """Test result with values."""
        root = temp_dir / "index.html"
        result = PublishResult(
            output_dir=temp_dir,
            root_index=root,
            language_indexes={"en": temp_dir / "en/index.html"},
            documents_copied=10,
            assets_bundled=5,
            success=True,
            errors=[],
        )
        assert result.root_index == root
        assert "en" in result.language_indexes
        assert result.documents_copied == 10
        assert result.assets_bundled == 5

    def test_with_errors(self, temp_dir):
        """Test result with errors."""
        result = PublishResult(
            output_dir=temp_dir,
            success=False,
            errors=["Error 1", "Error 2"],
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert "Error 1" in result.errors


class TestCollectDeliverables:
    """Tests for collect_deliverables function."""

    def test_empty_output_dir(self, temp_dir):
        """Test collecting from empty directory."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create empty language dir
        (temp_dir / "en").mkdir(parents=True)

        categories = collect_deliverables(mock_project, "en")

        # Should return empty list or minimal categories
        assert isinstance(categories, list)

    def test_proposal_html(self, temp_dir):
        """Test collecting proposal HTML."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create proposal HTML
        lang_dir = temp_dir / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "proposal.html").write_text("<html>Proposal</html>")

        categories = collect_deliverables(mock_project, "en")

        # Should have proposal category
        assert len(categories) > 0
        proposal_cat = next((c for c in categories if c.name == "Proposal"), None)
        assert proposal_cat is not None
        assert len(proposal_cat.items) == 1
        assert proposal_cat.items[0].name == "Full Proposal"

    def test_proposal_multiple_formats(self, temp_dir):
        """Test collecting proposal in multiple formats."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create proposal in HTML and PDF
        lang_dir = temp_dir / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "proposal.html").write_text("<html>Proposal</html>")
        (lang_dir / "proposal.pdf").write_text("PDF content")

        categories = collect_deliverables(mock_project, "en")

        proposal_cat = next((c for c in categories if c.name == "Proposal"), None)
        assert proposal_cat is not None
        assert len(proposal_cat.items) == 1
        # Should have both HTML and PDF formats
        assert len(proposal_cat.items[0].formats) == 2

    def test_investor_pack_pdfs(self, temp_dir):
        """Test collecting investor pack PDFs."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create investor pack PDFs
        lang_dir = temp_dir / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "ROP_Executive_Summary.pdf").write_text("Executive summary")
        (lang_dir / "ROP_Data_Sheet.pdf").write_text("Data sheet")

        categories = collect_deliverables(mock_project, "en")

        investor_cat = next((c for c in categories if c.name == "Investor Pack"), None)
        assert investor_cat is not None
        assert len(investor_cat.items) >= 2

    def test_pitch_deck_formats(self, temp_dir):
        """Test collecting pitch deck in multiple formats."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create pitch deck in multiple formats
        lang_dir = temp_dir / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "pitch_deck.pdf").write_text("PDF")
        presentations_dir = lang_dir / "presentations"
        presentations_dir.mkdir()
        (presentations_dir / "pitch_deck.pptx").write_text("PPTX")

        categories = collect_deliverables(mock_project, "en")

        investor_cat = next((c for c in categories if c.name == "Investor Pack"), None)
        assert investor_cat is not None
        pitch_item = next((i for i in investor_cat.items if i.name == "Pitch Deck"), None)
        assert pitch_item is not None

    def test_pitch_deck_html_presentation(self, temp_dir):
        """Test collecting HTML pitch deck presentation."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create HTML presentation
        lang_dir = temp_dir / "en"
        presentations_dir = lang_dir / "presentations"
        presentations_dir.mkdir(parents=True)
        (presentations_dir / "pitch_deck.html").write_text("<html>Presentation</html>")

        categories = collect_deliverables(mock_project, "en")

        investor_cat = next((c for c in categories if c.name == "Investor Pack"), None)
        assert investor_cat is not None
        pitch_item = next((i for i in investor_cat.items if i.name == "Pitch Deck"), None)
        assert pitch_item is not None
        # Should have HTML format
        html_format = next((f for f in pitch_item.formats if f.file_type == "html"), None)
        assert html_format is not None

    def test_pitch_deck_rop_pdf(self, temp_dir):
        """Test collecting ROP_Pitch_Deck.pdf alternative format."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create ROP_Pitch_Deck.pdf (alternative naming)
        lang_dir = temp_dir / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "ROP_Pitch_Deck.pdf").write_text("PDF content")

        categories = collect_deliverables(mock_project, "en")

        investor_cat = next((c for c in categories if c.name == "Investor Pack"), None)
        assert investor_cat is not None
        pitch_item = next((i for i in investor_cat.items if i.name == "Pitch Deck"), None)
        assert pitch_item is not None

    def test_pilot_pack_files(self, temp_dir):
        """Test collecting pilot pack files."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create pilot pack files
        lang_dir = temp_dir / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "pilot_proposal.pdf").write_text("Pilot proposal")

        # Add spreadsheet
        spreadsheets_dir = lang_dir / "spreadsheets"
        spreadsheets_dir.mkdir()
        (spreadsheets_dir / "roi_calculator.xlsx").write_text("XLSX content")

        categories = collect_deliverables(mock_project, "en")

        pilot_cat = next((c for c in categories if c.name == "Pilot Pack"), None)
        assert pilot_cat is not None
        assert len(pilot_cat.items) >= 2

    def test_videos(self, temp_dir):
        """Test collecting video files."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create video files
        lang_dir = temp_dir / "en"
        videos_dir = lang_dir / "videos"
        videos_dir.mkdir(parents=True)
        (videos_dir / "01-overview.mp4").write_text("Video content")
        (videos_dir / "02-teaser.mp4").write_text("Video content")

        categories = collect_deliverables(mock_project, "en")

        video_cat = next((c for c in categories if c.name == "Videos"), None)
        assert video_cat is not None
        assert len(video_cat.items) == 2
        assert video_cat.icon == "🎬"

    def test_diagrams(self, temp_dir):
        """Test collecting diagram files."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create diagram files
        lang_dir = temp_dir / "en"
        diagrams_dir = lang_dir / "diagrams"
        diagrams_dir.mkdir(parents=True)
        (diagrams_dir / "architecture.png").write_text("PNG")
        (diagrams_dir / "flowchart.svg").write_text("<svg></svg>")

        categories = collect_deliverables(mock_project, "en")

        diagram_cat = next((c for c in categories if c.name == "Diagrams"), None)
        assert diagram_cat is not None
        assert len(diagram_cat.items) == 2

    def test_interactive_demos(self, temp_dir):
        """Test collecting interactive demos."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir
        mock_project.languages = ["en"]

        # Create demo files
        lang_dir = temp_dir / "en"
        demos_dir = lang_dir / "demos"
        demos_dir.mkdir(parents=True)
        (demos_dir / "interactive-demo.html").write_text("<html>Demo</html>")
        (demos_dir / "guest-form.html").write_text("<html>Form</html>")
        (demos_dir / "index.html").write_text("<html>Index</html>")  # Should be skipped

        categories = collect_deliverables(mock_project, "en")

        demo_cat = next((c for c in categories if c.name == "Interactive Demos"), None)
        assert demo_cat is not None
        # Should skip index.html
        assert len(demo_cat.items) == 2

    def test_custom_output_dir(self, temp_dir):
        """Test using custom output directory."""
        mock_project = Mock()
        mock_project.output_dir = temp_dir / "default"
        mock_project.languages = ["en"]

        # Create files in custom output dir
        custom_output = temp_dir / "custom"
        lang_dir = custom_output / "en"
        lang_dir.mkdir(parents=True)
        (lang_dir / "proposal.html").write_text("<html>Proposal</html>")

        categories = collect_deliverables(mock_project, "en", output_dir=custom_output)

        # Should find files in custom dir
        assert len(categories) > 0


class TestGenerateNavigationIndexes:
    """Tests for generate_navigation_indexes function."""

    def test_generate_for_single_language(self, temp_dir):
        """Test generating indexes for single language."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir
        mock_project.tagline = "A test project"

        # Create language config
        mock_lang = Mock()
        mock_lang.name = "English"
        mock_project.languages = {"en": mock_lang}

        # Create theme
        mock_theme = Mock()
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"
        mock_project.theme = mock_theme

        # Create shared dir with logo
        shared_dir = temp_dir / "shared"
        shared_dir.mkdir()
        (shared_dir / "logo.svg").write_text("<svg></svg>")

        # Create language output dir
        (temp_dir / "en").mkdir()

        indexes = generate_navigation_indexes(mock_project, temp_dir, console_output=False)

        # Should create root and language indexes
        assert "root" in indexes
        assert "en" in indexes
        assert indexes["root"].exists()
        assert indexes["en"].exists()

    def test_generate_for_multiple_languages(self, temp_dir):
        """Test generating indexes for multiple languages."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir
        mock_project.tagline = "A test project"

        # Create language configs
        mock_en = Mock()
        mock_en.name = "English"
        mock_no = Mock()
        mock_no.name = "Norwegian"
        mock_project.languages = {"en": mock_en, "no": mock_no}

        # Create theme
        mock_theme = Mock()
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"
        mock_project.theme = mock_theme

        # Create language output dirs
        (temp_dir / "en").mkdir()
        (temp_dir / "no").mkdir()

        indexes = generate_navigation_indexes(mock_project, temp_dir, console_output=False)

        # Should create indexes for both languages
        assert "root" in indexes
        assert "en" in indexes
        assert "no" in indexes
        assert len(indexes) == 3

    def test_generate_with_logo_png(self, temp_dir):
        """Test generating with PNG logo instead of SVG."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir
        mock_project.tagline = ""

        # Create language config
        mock_lang = Mock()
        mock_lang.name = "English"
        mock_project.languages = {"en": mock_lang}

        # Create theme
        mock_theme = Mock()
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"
        mock_project.theme = mock_theme

        # Create shared dir with PNG logo (no SVG)
        shared_dir = temp_dir / "shared"
        shared_dir.mkdir()
        (shared_dir / "logo.png").write_text("PNG content")

        # Create language output dir
        (temp_dir / "en").mkdir()

        indexes = generate_navigation_indexes(mock_project, temp_dir, console_output=False)

        # Should still create indexes successfully
        assert len(indexes) == 2
        assert indexes["root"].exists()

    def test_generate_without_logo(self, temp_dir):
        """Test generating without any logo file."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir
        mock_project.tagline = ""

        # Create language config
        mock_lang = Mock()
        mock_lang.name = "English"
        mock_project.languages = {"en": mock_lang}

        # Create theme
        mock_theme = Mock()
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"
        mock_project.theme = mock_theme

        # Create language output dir (no logo)
        (temp_dir / "en").mkdir()

        indexes = generate_navigation_indexes(mock_project, temp_dir, console_output=False)

        # Should still create indexes successfully
        assert len(indexes) == 2

    def test_generate_with_console_output(self, temp_dir):
        """Test generating indexes with console output enabled."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir
        mock_project.tagline = ""

        # Create language config
        mock_lang = Mock()
        mock_lang.name = "English"
        mock_project.languages = {"en": mock_lang}

        # Create theme
        mock_theme = Mock()
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"
        mock_project.theme = mock_theme

        # Create language output dir
        (temp_dir / "en").mkdir()

        indexes = generate_navigation_indexes(mock_project, temp_dir, console_output=True)

        # Should still create indexes successfully
        assert len(indexes) == 2


class TestCopyDocuments:
    """Tests for copy_documents function."""

    def test_copy_html_files(self, temp_dir):
        """Test copying HTML files."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "proposal.html").write_text("<html>Proposal</html>")
        (src_dir / "index.html").write_text("<html>Index</html>")

        mock_project.output_dir = temp_dir / "src"

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy both HTML files
        assert count == 2
        assert (dest_dir / "en" / "proposal.html").exists()
        assert (dest_dir / "en" / "index.html").exists()

    def test_copy_pdf_files(self, temp_dir):
        """Test copying PDF files."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "proposal.pdf").write_text("PDF content")
        (src_dir / "pitch_deck.pdf").write_text("PDF content")

        mock_project.output_dir = temp_dir / "src"

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy both PDF files
        assert count == 2
        assert (dest_dir / "en" / "proposal.pdf").exists()

    def test_copy_pptx_to_presentations(self, temp_dir):
        """Test copying PPTX files to presentations subfolder."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create source PPTX
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "pitch_deck.pptx").write_text("PPTX content")

        mock_project.output_dir = temp_dir / "src"

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy to presentations subfolder
        assert count == 1
        assert (dest_dir / "en" / "presentations" / "pitch_deck.pptx").exists()

    def test_copy_xlsx_to_spreadsheets(self, temp_dir):
        """Test copying XLSX files to spreadsheets subfolder."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create source XLSX
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "data.xlsx").write_text("XLSX content")

        mock_project.output_dir = temp_dir / "src"

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy to spreadsheets subfolder
        assert count == 1
        assert (dest_dir / "en" / "spreadsheets" / "data.xlsx").exists()

    def test_copy_subdirectories(self, temp_dir):
        """Test copying subdirectory contents."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create source subdirectories
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)

        # Presentations
        presentations_dir = src_dir / "presentations"
        presentations_dir.mkdir()
        (presentations_dir / "slide1.html").write_text("<html>Slide 1</html>")

        # Demos
        demos_dir = src_dir / "demos"
        demos_dir.mkdir()
        (demos_dir / "demo1.html").write_text("<html>Demo 1</html>")

        mock_project.output_dir = temp_dir / "src"

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy all files
        assert count >= 2
        assert (dest_dir / "en" / "presentations" / "slide1.html").exists()
        assert (dest_dir / "en" / "demos" / "demo1.html").exists()

    def test_copy_deliverables_to_root(self, temp_dir):
        """Test copying deliverables to language root instead of subfolder."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create deliverables subfolder
        src_dir = temp_dir / "src" / "en"
        deliverables_dir = src_dir / "deliverables"
        deliverables_dir.mkdir(parents=True)
        (deliverables_dir / "package.pdf").write_text("PDF content")

        mock_project.output_dir = temp_dir / "src"

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy to lang root, not deliverables subfolder
        assert count >= 1
        assert (dest_dir / "en" / "package.pdf").exists()
        assert not (dest_dir / "en" / "deliverables" / "package.pdf").exists()

    def test_copy_multiple_languages(self, temp_dir):
        """Test copying documents for multiple languages."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en", "no"]

        # Create source files for both languages
        src_dir = temp_dir / "src"
        (src_dir / "en").mkdir(parents=True)
        (src_dir / "no").mkdir(parents=True)
        (src_dir / "en" / "proposal.html").write_text("<html>English</html>")
        (src_dir / "no" / "proposal.html").write_text("<html>Norwegian</html>")

        mock_project.output_dir = src_dir

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy both languages
        assert count == 2
        assert (dest_dir / "en" / "proposal.html").exists()
        assert (dest_dir / "no" / "proposal.html").exists()

    def test_skip_nonexistent_language_dir(self, temp_dir):
        """Test skipping languages without output directory."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en", "no"]

        # Create source files only for English
        src_dir = temp_dir / "src"
        (src_dir / "en").mkdir(parents=True)
        (src_dir / "en" / "proposal.html").write_text("<html>English</html>")
        # No "no" directory created

        mock_project.output_dir = src_dir

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should only copy English
        assert count == 1
        assert (dest_dir / "en" / "proposal.html").exists()
        assert not (dest_dir / "no").exists()

    def test_copy_legacy_demos(self, temp_dir):
        """Test copying legacy demo directory structure."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create legacy demo directory structure
        legacy_demo_dir = temp_dir / "docs" / "deliverables" / "demo" / "en"
        legacy_demo_dir.mkdir(parents=True)
        (legacy_demo_dir / "demo1.html").write_text("<html>Demo 1</html>")
        (legacy_demo_dir / "demo2.html").write_text("<html>Demo 2</html>")

        # Create shared demo files
        shared_demo_dir = temp_dir / "docs" / "deliverables" / "demo" / "shared"
        shared_demo_dir.mkdir(parents=True)
        (shared_demo_dir / "style.css").write_text("/* CSS */")

        # Create shared fonts subdirectory
        fonts_dir = shared_demo_dir / "fonts"
        fonts_dir.mkdir()
        (fonts_dir / "font.woff2").write_text("FONT")

        # Create demo assets
        demo_assets_dir = temp_dir / "docs" / "deliverables" / "assets"
        demo_assets_dir.mkdir(parents=True)
        (demo_assets_dir / "logo.png").write_text("PNG")

        # Mock output dir
        src_dir = temp_dir / "src"
        (src_dir / "en").mkdir(parents=True)

        mock_project.output_dir = src_dir

        # Copy to destination
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=False)

        # Should copy legacy demos and shared files
        assert (dest_dir / "en" / "demos" / "demo1.html").exists()
        assert (dest_dir / "en" / "demos" / "demo2.html").exists()
        assert (dest_dir / "en" / "shared" / "style.css").exists()
        assert (dest_dir / "en" / "shared" / "fonts" / "font.woff2").exists()
        assert (dest_dir / "en" / "assets" / "logo.png").exists()

    def test_copy_with_console_output(self, temp_dir):
        """Test copying documents with console output enabled."""
        mock_project = Mock()
        mock_project.root = temp_dir
        mock_project.languages = ["en"]

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "proposal.html").write_text("<html>Proposal</html>")

        mock_project.output_dir = temp_dir / "src"

        # Copy with console output enabled
        dest_dir = temp_dir / "dest"
        count = copy_documents(mock_project, dest_dir, console_output=True)

        # Should still work
        assert count == 1
        assert (dest_dir / "en" / "proposal.html").exists()


class TestCreateZipArchive:
    """Tests for create_zip_archive function."""

    def test_create_zip(self, temp_dir):
        """Test creating ZIP archive."""
        # Create source directory with files
        src_dir = temp_dir / "source"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("Content 1")
        (src_dir / "file2.txt").write_text("Content 2")

        # Create ZIP
        output_path = temp_dir / "archive"
        zip_path = create_zip_archive(src_dir, output_path, console_output=False)

        # Should create ZIP file
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert zip_path.name == "archive.zip"

    def test_zip_contains_files(self, temp_dir):
        """Test ZIP contains all source files."""
        import zipfile

        # Create source directory
        src_dir = temp_dir / "source"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("Content 1")
        subdir = src_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("Content 2")

        # Create ZIP
        output_path = temp_dir / "archive"
        zip_path = create_zip_archive(src_dir, output_path, console_output=False)

        # Verify contents
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert any("file1.txt" in name for name in names)
            assert any("file2.txt" in name for name in names)

    def test_zip_with_console_output(self, temp_dir):
        """Test creating ZIP with console output enabled."""
        # Create source directory
        src_dir = temp_dir / "source"
        src_dir.mkdir()
        (src_dir / "file.txt").write_text("Content")

        # Create ZIP with console output
        output_path = temp_dir / "archive"
        zip_path = create_zip_archive(src_dir, output_path, console_output=True)

        # Should still create ZIP
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"


class TestPublishProject:
    """Tests for publish_project function."""

    @patch("media_engine.publish.packager.bundle_project_assets")
    @patch("media_engine.publish.packager.create_shared_css")
    @patch("media_engine.publish.packager.generate_font_faces")
    def test_publish_basic(
        self,
        mock_font_faces,
        mock_shared_css,
        mock_bundle,
        temp_dir,
    ):
        """Test basic publishing workflow."""
        # Setup mocks
        mock_bundle_result = Mock()
        mock_bundle_result.files_copied = 10
        shared_dir = temp_dir / "shared"
        shared_dir.mkdir(parents=True)
        mock_bundle_result.shared_dir = shared_dir
        mock_bundle_result.fonts_dir = None
        mock_bundle.return_value = mock_bundle_result
        mock_shared_css.return_value = "/* CSS */"

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"
        mock_project.languages = ["en"]

        # Create theme
        mock_theme = Mock()
        mock_project.theme = mock_theme

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "proposal.html").write_text("<html>Proposal</html>")

        # Create mock language config
        mock_lang = Mock()
        mock_lang.name = "English"
        mock_project.languages = {"en": mock_lang}

        # Setup theme for index generation
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"

        # Publish
        output_dir = temp_dir / "publish"
        config = PublishConfig(output_dir=output_dir, console_output=False)

        result = publish_project(mock_project, config)

        # Verify result
        assert result.success is True
        assert result.documents_copied >= 1
        assert result.assets_bundled == 10
        assert mock_bundle.called

    @patch("media_engine.publish.packager.bundle_project_assets")
    def test_publish_without_indexes(self, mock_bundle, temp_dir):
        """Test publishing without generating indexes."""
        # Setup mocks
        mock_bundle_result = Mock()
        mock_bundle_result.files_copied = 5
        mock_bundle_result.shared_dir = None
        mock_bundle_result.fonts_dir = None
        mock_bundle.return_value = mock_bundle_result

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"
        mock_project.languages = ["en"]

        # Create theme
        mock_theme = Mock()
        mock_project.theme = mock_theme

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "proposal.html").write_text("<html>Proposal</html>")

        # Publish without indexes
        output_dir = temp_dir / "publish"
        config = PublishConfig(
            output_dir=output_dir,
            generate_indexes=False,
            console_output=False,
        )

        result = publish_project(mock_project, config)

        # Should not generate indexes
        assert result.success is True
        assert result.root_index is None
        assert len(result.language_indexes) == 0

    @patch("media_engine.publish.packager.bundle_project_assets")
    @patch("media_engine.publish.packager.create_zip_archive")
    def test_publish_with_zip(self, mock_zip, mock_bundle, temp_dir):
        """Test publishing with ZIP output."""
        # Setup mocks
        mock_bundle_result = Mock()
        mock_bundle_result.files_copied = 5
        mock_bundle_result.shared_dir = None
        mock_bundle_result.fonts_dir = None
        mock_bundle.return_value = mock_bundle_result

        mock_zip.return_value = temp_dir / "archive.zip"

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"
        mock_project.languages = ["en"]

        # Create theme
        mock_theme = Mock()
        mock_project.theme = mock_theme

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)

        # Publish with ZIP
        output_dir = temp_dir / "publish"
        config = PublishConfig(
            output_dir=output_dir,
            zip_output=True,
            generate_indexes=False,
            console_output=False,
        )

        result = publish_project(mock_project, config)

        # Should create ZIP
        assert result.success is True
        assert mock_zip.called

    @patch("media_engine.publish.packager.bundle_project_assets")
    def test_publish_with_fonts(self, mock_bundle, temp_dir):
        """Test publishing with font generation."""
        # Setup mocks
        mock_bundle_result = Mock()
        mock_bundle_result.files_copied = 5
        mock_bundle_result.shared_dir = temp_dir / "shared"
        mock_bundle_result.shared_dir.mkdir()
        mock_bundle_result.fonts_dir = temp_dir / "shared" / "fonts"
        mock_bundle_result.fonts_dir.mkdir()
        mock_bundle.return_value = mock_bundle_result

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"
        mock_project.languages = ["en"]

        # Create theme
        mock_theme = Mock()
        mock_project.theme = mock_theme

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)

        # Publish with fonts
        output_dir = temp_dir / "publish"
        config = PublishConfig(
            output_dir=output_dir,
            include_fonts=True,
            generate_indexes=False,
            console_output=False,
        )

        with patch("media_engine.publish.packager.create_shared_css") as mock_css, patch(
            "media_engine.publish.packager.generate_font_faces"
        ) as mock_fonts:
            mock_css.return_value = "/* CSS */"
            mock_fonts.return_value = "/* Fonts */"

            result = publish_project(mock_project, config)

            # Should generate font CSS
            assert result.success is True
            assert mock_fonts.called

    @patch("media_engine.publish.packager.bundle_project_assets")
    def test_publish_handles_errors(self, mock_bundle, temp_dir):
        """Test publishing handles errors gracefully."""
        # Make bundle raise an error
        mock_bundle.side_effect = Exception("Bundle failed")

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"

        # Publish
        output_dir = temp_dir / "publish"
        config = PublishConfig(output_dir=output_dir, console_output=False)

        result = publish_project(mock_project, config)

        # Should handle error
        assert result.success is False
        assert len(result.errors) > 0
        assert "Bundle failed" in result.errors[0]

    @patch("media_engine.publish.packager.bundle_project_assets")
    def test_publish_without_assets(self, mock_bundle, temp_dir):
        """Test publishing without fonts, diagrams, or videos."""
        # Setup mocks
        mock_bundle_result = Mock()
        mock_bundle_result.files_copied = 0
        mock_bundle_result.shared_dir = None
        mock_bundle_result.fonts_dir = None
        mock_bundle.return_value = mock_bundle_result

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"
        mock_project.languages = ["en"]

        # Create theme
        mock_theme = Mock()
        mock_project.theme = mock_theme

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)

        # Publish without assets
        output_dir = temp_dir / "publish"
        config = PublishConfig(
            output_dir=output_dir,
            include_fonts=False,
            include_diagrams=False,
            include_videos=False,
            generate_indexes=False,
            console_output=False,
        )

        result = publish_project(mock_project, config)

        # Verify bundle was called with correct flags
        assert result.success is True
        call_args = mock_bundle.call_args
        assert call_args[1]["include_fonts"] is False
        assert call_args[1]["include_diagrams"] is False
        assert call_args[1]["include_videos"] is False

    @patch("media_engine.publish.packager.bundle_project_assets")
    @patch("media_engine.publish.packager.create_shared_css")
    @patch("media_engine.publish.packager.create_zip_archive")
    def test_publish_with_full_console_output(
        self,
        mock_zip,
        mock_shared_css,
        mock_bundle,
        temp_dir,
    ):
        """Test publishing with full console output to cover all print statements."""
        # Setup mocks
        mock_bundle_result = Mock()
        mock_bundle_result.files_copied = 5
        shared_dir = temp_dir / "shared"
        shared_dir.mkdir(parents=True)
        mock_bundle_result.shared_dir = shared_dir
        mock_bundle_result.fonts_dir = None
        mock_bundle.return_value = mock_bundle_result
        mock_shared_css.return_value = "/* CSS */"
        mock_zip.return_value = temp_dir / "archive.zip"

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.root = temp_dir
        mock_project.output_dir = temp_dir / "src"
        mock_project.languages = ["en"]

        # Create theme
        mock_theme = Mock()
        mock_theme.colors.background = "#ffffff"
        mock_theme.colors.text = "#000000"
        mock_theme.colors.accent = "#0066cc"
        mock_theme.colors.surface = "#f5f5f5"
        mock_theme.colors.muted = "#666666"
        mock_theme.colors.border = "#dddddd"
        mock_theme.dark.background = "#1a1a1a"
        mock_theme.dark.text = "#ffffff"
        mock_theme.dark.accent = "#0088ff"
        mock_theme.dark.surface = "#2a2a2a"
        mock_theme.dark.muted = "#999999"
        mock_theme.dark.border = "#333333"
        mock_theme.typography.heading = "Arial"
        mock_theme.typography.body = "Helvetica"
        mock_project.theme = mock_theme

        # Create mock language config
        mock_lang = Mock()
        mock_lang.name = "English"
        mock_project.languages = {"en": mock_lang}

        # Create source files
        src_dir = temp_dir / "src" / "en"
        src_dir.mkdir(parents=True)
        (src_dir / "proposal.html").write_text("<html>Proposal</html>")

        # Publish with all console output enabled
        output_dir = temp_dir / "publish"
        config = PublishConfig(
            output_dir=output_dir,
            console_output=True,  # Enable console output
            generate_indexes=True,
            zip_output=True,
        )

        result = publish_project(mock_project, config)

        # Verify success and console output paths were executed
        assert result.success is True
        assert result.root_index is not None
        assert mock_zip.called
