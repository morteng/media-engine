"""
Deliverable Packager Module

Creates self-contained deliverable packages with:
- All HTML documents with embedded fonts
- Navigation indexes (root + per-language)
- Bundled assets (fonts, diagrams, videos)
- Design tokens and branding applied throughout
"""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from rich.console import Console

from ..assets.bundler import bundle_project_assets, create_shared_css
from ..assets.fonts import generate_font_faces
from ..templates.html_index import (
    DeliverableCategory,
    DeliverableItem,
    FormatLink,
    LanguageInfo,
    render_language_index,
    render_project_index,
)

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


@dataclass
class PublishConfig:
    """Configuration for publishing deliverables."""

    output_dir: Path
    include_fonts: bool = True
    include_diagrams: bool = True
    include_videos: bool = True
    include_source: bool = False
    generate_indexes: bool = True
    zip_output: bool = False
    console_output: bool = True


@dataclass
class PublishResult:
    """Result of publishing operation."""

    output_dir: Path
    root_index: Optional[Path] = None
    language_indexes: Dict[str, Path] = field(default_factory=dict)
    documents_copied: int = 0
    assets_bundled: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


def collect_deliverables(
    project: "Project",
    language: str,
    output_dir: Optional[Path] = None,
) -> List[DeliverableCategory]:
    """
    Collect all deliverables for a language into categories.

    Organizes deliverables by registered pack categories:
    - Proposal: Main documentation
    - Investor Pack: Pitch materials
    - Pilot Pack: Customer engagement
    - Videos: Video content
    - Data: Spreadsheets and data files

    Args:
        project: Project to collect from
        language: Language code
        output_dir: Output directory to scan (defaults to project output dir)

    Returns:
        List of categorized deliverables
    """
    categories = []
    base_dir = output_dir if output_dir else project.output_dir
    lang_output = base_dir / language

    # File type icons
    ICONS = {
        "html": "📄",
        "pdf": "📕",
        "pptx": "📊",
        "xlsx": "📈",
        "mp4": "🎬",
        "png": "🖼️",
        "svg": "🎨",
    }

    # Deliverable name registry - maps filename patterns to display names
    # These match the registered pack item names
    DELIVERABLE_NAMES = {
        # Proposal
        "proposal.html": "Full Proposal",
        "proposal.pdf": "Full Proposal (PDF)",
        # Investor Pack
        "ROP_Executive_Summary.pdf": "Executive Summary",
        "ROP_Pitch_Deck.pdf": "Pitch Deck (PDF)",
        "ROP_Data_Sheet.pdf": "Data Sheet",
        "ROP_One_Pager.pdf": "One Pager",
        "pitch_deck.pptx": "Pitch Deck",
        "pitch_deck.pdf": "Pitch Deck (PDF)",
        # Pilot Pack
        "pilot_proposal.pdf": "Pilot Proposal",
        "pilot_deck.pdf": "Pilot Presentation",
        "roi_calculator.xlsx": "ROI Calculator",
        # Videos - English
        "01-overview.mp4": "Overview",
        "02-teaser.mp4": "Teaser",
        "03-training.mp4": "Training",
        "03-platform-overview.mp4": "Platform Overview",
        "mvp-full-demo.mp4": "Full Demo",
        "mvp-full-demo-en.mp4": "Full Demo",
        "mvp-tight.mp4": "MVP Demo",
        "highlight-en.mp4": "Highlight",
        "teaser.mp4": "Teaser (Short)",
        "highlight.webm": "Highlight (WebM)",
        # Videos - Norwegian
        "highlight-no.mp4": "Høydepunkt",
        "teaser-no.mp4": "Teaser",
        "full-demo-no.mp4": "Full Demo",
    }

    # Pack membership - which files belong to which pack
    INVESTOR_PACK_FILES = {
        "ROP_Executive_Summary.pdf",
        "ROP_Pitch_Deck.pdf",
        "ROP_Data_Sheet.pdf",
        "ROP_One_Pager.pdf",
        "pitch_deck.pptx",
        "pitch_deck.pdf",
    }

    PILOT_PACK_FILES = {
        "pilot_proposal.pdf",
        "pilot_deck.pdf",
        "roi_calculator.xlsx",
    }

    # =========================================
    # PROPOSAL - Main documentation
    # =========================================
    proposal_items = []

    # Group proposal formats (HTML + PDF)
    proposal_formats = []
    proposal_html = lang_output / "proposal.html"
    proposal_pdf = lang_output / "proposal.pdf"

    if proposal_html.exists():
        proposal_formats.append(
            FormatLink(file_type="html", path="proposal.html", label="View")
        )
    if proposal_pdf.exists():
        proposal_formats.append(
            FormatLink(file_type="pdf", path="proposal.pdf", label="PDF")
        )

    if proposal_formats:
        proposal_items.append(
            DeliverableItem(
                name="Full Proposal",
                path="",
                description="Complete documentation",
                icon="📖",
                formats=proposal_formats,
            )
        )

    if proposal_items:
        categories.append(
            DeliverableCategory(
                name="Proposal",
                icon="📖",
                items=proposal_items,
            )
        )

    # =========================================
    # INVESTOR PACK - Pitch materials
    # =========================================
    investor_items = []

    # Group Pitch Deck formats together (HTML, PDF, PPTX)
    pitch_deck_formats = []
    presentations_dir = lang_output / "presentations"

    # Check for HTML presentation
    html_presentation = presentations_dir / "pitch_deck.html" if presentations_dir.exists() else None
    if html_presentation and html_presentation.exists():
        pitch_deck_formats.append(
            FormatLink(file_type="html", path="presentations/pitch_deck.html", label="View")
        )

    # Check for PDF
    if (lang_output / "pitch_deck.pdf").exists():
        pitch_deck_formats.append(
            FormatLink(file_type="pdf", path="pitch_deck.pdf", label="PDF")
        )
    elif (lang_output / "ROP_Pitch_Deck.pdf").exists():
        pitch_deck_formats.append(
            FormatLink(file_type="pdf", path="ROP_Pitch_Deck.pdf", label="PDF")
        )

    # Check for PPTX
    pptx_path = presentations_dir / "pitch_deck.pptx" if presentations_dir.exists() else None
    if pptx_path and pptx_path.exists():
        pitch_deck_formats.append(
            FormatLink(file_type="pptx", path="presentations/pitch_deck.pptx", label="PPTX")
        )

    if pitch_deck_formats:
        investor_items.append(
            DeliverableItem(
                name="Pitch Deck",
                path="",
                description="Investor presentation",
                icon="📊",
                formats=pitch_deck_formats,
            )
        )

    # Add other investor pack PDFs (non-pitch deck)
    for pdf_file in sorted(lang_output.glob("*.pdf")):
        if pdf_file.name in INVESTOR_PACK_FILES and "pitch" not in pdf_file.name.lower():
            investor_items.append(
                DeliverableItem(
                    name=DELIVERABLE_NAMES.get(pdf_file.name, pdf_file.stem),
                    path=pdf_file.name,
                    icon=ICONS["pdf"],
                    file_type="pdf",
                )
            )

    if investor_items:
        categories.append(
            DeliverableCategory(
                name="Investor Pack",
                icon="💼",
                items=investor_items,
            )
        )

    # =========================================
    # PILOT PACK - Customer engagement
    # =========================================
    pilot_items = []

    for pdf_file in sorted(lang_output.glob("*.pdf")):
        if pdf_file.name in PILOT_PACK_FILES:
            pilot_items.append(
                DeliverableItem(
                    name=DELIVERABLE_NAMES.get(pdf_file.name, pdf_file.stem),
                    path=pdf_file.name,
                    icon=ICONS["pdf"],
                    file_type="pdf",
                )
            )

    # Check for spreadsheets
    spreadsheets_dir = lang_output / "spreadsheets"
    if spreadsheets_dir.exists():
        for xlsx_file in sorted(spreadsheets_dir.glob("*.xlsx")):
            pilot_items.append(
                DeliverableItem(
                    name=DELIVERABLE_NAMES.get(xlsx_file.name, xlsx_file.stem),
                    path=f"spreadsheets/{xlsx_file.name}",
                    icon=ICONS["xlsx"],
                    file_type="xlsx",
                )
            )

    if pilot_items:
        categories.append(
            DeliverableCategory(
                name="Pilot Pack",
                icon="🚀",
                items=pilot_items,
            )
        )

    # =========================================
    # VIDEOS - Video content
    # =========================================
    video_items = []
    videos_dir = lang_output / "videos"
    if videos_dir.exists():
        for video in sorted(videos_dir.glob("*.mp4")):
            video_items.append(
                DeliverableItem(
                    name=DELIVERABLE_NAMES.get(video.name, video.stem),
                    path=f"videos/{video.name}",
                    icon=ICONS["mp4"],
                    file_type="mp4",
                )
            )

    if video_items:
        categories.append(
            DeliverableCategory(
                name="Videos",
                icon="🎬",
                items=video_items,
            )
        )

    # =========================================
    # DIAGRAMS - Visual assets
    # =========================================
    diagram_items = []
    diagrams_dir = lang_output / "diagrams"
    if diagrams_dir.exists():
        for diagram in sorted(diagrams_dir.glob("*.png")):
            diagram_items.append(
                DeliverableItem(
                    name=DELIVERABLE_NAMES.get(diagram.name, diagram.stem),
                    path=f"diagrams/{diagram.name}",
                    icon=ICONS["png"],
                    file_type="png",
                )
            )
        for diagram in sorted(diagrams_dir.glob("*.svg")):
            diagram_items.append(
                DeliverableItem(
                    name=DELIVERABLE_NAMES.get(diagram.name, diagram.stem),
                    path=f"diagrams/{diagram.name}",
                    icon=ICONS["svg"],
                    file_type="svg",
                )
            )

    if diagram_items:
        categories.append(
            DeliverableCategory(
                name="Diagrams",
                icon="🖼️",
                items=diagram_items,
            )
        )

    # =========================================
    # DEMOS - Interactive HTML demos
    # =========================================
    demo_items = []
    demos_dir = lang_output / "demos"

    # Demo name mapping for clean display
    DEMO_NAMES = {
        "interactive-demo.html": "Interactive Platform Demo",
        "guest-form.html": "Guest Form Demo",
        "gjesteskjema.html": "Gjesteskjema Demo",
        "index.html": "Demo Overview",
    }

    if demos_dir.exists():
        for demo in sorted(demos_dir.glob("*.html")):
            # Skip index.html as it's a navigation page
            if demo.name == "index.html":
                continue
            demo_items.append(
                DeliverableItem(
                    name=DEMO_NAMES.get(demo.name, demo.stem.replace("-", " ").replace("_", " ").title()),
                    path=f"demos/{demo.name}",
                    description="Interactive demo",
                    icon="🎮",
                    file_type="html",
                )
            )

    if demo_items:
        categories.append(
            DeliverableCategory(
                name="Interactive Demos",
                icon="🎮",
                items=demo_items,
            )
        )

    return categories


def generate_navigation_indexes(
    project: "Project",
    output_dir: Path,
    console_output: bool = True,
) -> Dict[str, Path]:
    """
    Generate navigation indexes for all languages and root.

    Args:
        project: Project to generate indexes for
        output_dir: Output directory
        console_output: Whether to print progress

    Returns:
        Dictionary of generated index paths
    """
    indexes = {}

    # Collect language info
    languages = []
    for lang in project.languages:
        lang_config = project.languages.get(lang)
        lang_name = getattr(lang_config, "name", lang.upper()) if lang_config else lang.upper()
        languages.append(
            LanguageInfo(
                code=lang,
                name=lang_name,
                path=f"{lang}/index.html",
            )
        )

    # Generate per-language indexes
    for lang_info in languages:
        lang_dir = output_dir / lang_info.code
        lang_dir.mkdir(parents=True, exist_ok=True)

        categories = collect_deliverables(project, lang_info.code, output_dir)

        # Get theme for rendering
        theme = project.theme if hasattr(project, "theme") else None

        # Check for logo (svg or png)
        logo_path = None
        if (output_dir / "shared" / "logo.svg").exists():
            logo_path = "../shared/logo.svg"
        elif (output_dir / "shared" / "logo.png").exists():
            logo_path = "../shared/logo.png"

        index_html = render_language_index(
            project_name=project.name,
            lang_code=lang_info.code,
            lang_name=lang_info.name,
            categories=categories,
            theme=theme,
            logo_path=logo_path,
        )

        index_path = lang_dir / "index.html"
        index_path.write_text(index_html)
        indexes[lang_info.code] = index_path

        if console_output:
            console.print(f"  [green]✓[/green] Generated {lang_info.code}/index.html")

    # Generate root index
    theme = project.theme if hasattr(project, "theme") else None

    # Check for logo (svg or png)
    root_logo_path = None
    if (output_dir / "shared" / "logo.svg").exists():
        root_logo_path = "shared/logo.svg"
    elif (output_dir / "shared" / "logo.png").exists():
        root_logo_path = "shared/logo.png"

    root_html = render_project_index(
        project_name=project.name,
        languages=languages,
        theme=theme,
        tagline=getattr(project, "tagline", ""),
        logo_path=root_logo_path,
    )

    root_index = output_dir / "index.html"
    root_index.write_text(root_html)
    indexes["root"] = root_index

    if console_output:
        console.print("  [green]✓[/green] Generated root index.html")

    return indexes


def copy_documents(
    project: "Project",
    output_dir: Path,
    console_output: bool = True,
) -> int:
    """
    Copy all generated documents to output directory.

    Args:
        project: Project to copy from
        output_dir: Output directory
        console_output: Whether to print progress

    Returns:
        Number of documents copied
    """
    count = 0

    for lang in project.languages:
        src_dir = project.output_dir / lang
        dest_dir = output_dir / lang

        if not src_dir.exists():
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy HTML files
        for html_file in src_dir.glob("*.html"):
            shutil.copy2(html_file, dest_dir / html_file.name)
            count += 1

        # Copy PDF files
        for pdf_file in src_dir.glob("*.pdf"):
            shutil.copy2(pdf_file, dest_dir / pdf_file.name)
            count += 1

        # Copy PPTX files (presentations)
        for pptx_file in src_dir.glob("*.pptx"):
            # Copy to presentations subfolder
            presentations_dir = dest_dir / "presentations"
            presentations_dir.mkdir(exist_ok=True)
            shutil.copy2(pptx_file, presentations_dir / pptx_file.name)
            count += 1

        # Copy XLSX files (spreadsheets)
        for xlsx_file in src_dir.glob("*.xlsx"):
            spreadsheets_dir = dest_dir / "spreadsheets"
            spreadsheets_dir.mkdir(exist_ok=True)
            shutil.copy2(xlsx_file, spreadsheets_dir / xlsx_file.name)
            count += 1

        # Copy subdirectories
        for subdir in ["presentations", "spreadsheets", "demos", "deliverables"]:
            src_subdir = src_dir / subdir
            if src_subdir.exists():
                # For deliverables, copy to root of lang dir, not subdir
                if subdir == "deliverables":
                    for f in src_subdir.glob("*.pdf"):
                        if f.is_file():
                            shutil.copy2(f, dest_dir / f.name)
                            count += 1
                else:
                    dest_subdir = dest_dir / subdir
                    dest_subdir.mkdir(exist_ok=True)
                    for f in src_subdir.glob("*"):
                        if f.is_file():
                            shutil.copy2(f, dest_subdir / f.name)
                            count += 1

        # Also check for legacy demos in docs/deliverables/demo/{lang}/
        legacy_demo_dir = project.root / "docs" / "deliverables" / "demo" / lang
        if legacy_demo_dir.exists():
            demos_dest = dest_dir / "demos"
            demos_dest.mkdir(exist_ok=True)
            for f in legacy_demo_dir.glob("*.html"):
                if f.is_file() and not f.is_symlink():
                    shutil.copy2(f, demos_dest / f.name)
                    count += 1

            # Copy shared demo files to lang/shared/ so relative paths work
            shared_demo_dir = project.root / "docs" / "deliverables" / "demo" / "shared"
            if shared_demo_dir.exists():
                lang_shared = dest_dir / "shared"
                lang_shared.mkdir(exist_ok=True)
                for f in shared_demo_dir.glob("*"):
                    if f.is_file():
                        shutil.copy2(f, lang_shared / f.name)
                        count += 1
                # Also copy fonts subdirectory if it exists
                fonts_dir = shared_demo_dir / "fonts"
                if fonts_dir.exists():
                    shutil.copytree(fonts_dir, lang_shared / "fonts", dirs_exist_ok=True)

            # Copy demo assets to lang/assets/ so relative paths work
            demo_assets_dir = project.root / "docs" / "deliverables" / "assets"
            if demo_assets_dir.exists():
                lang_assets = dest_dir / "assets"
                if not lang_assets.exists():
                    shutil.copytree(demo_assets_dir, lang_assets, dirs_exist_ok=True)
                    count += sum(1 for _ in lang_assets.rglob("*") if _.is_file())

    if console_output:
        console.print(f"  [green]✓[/green] Copied {count} documents")

    return count


def create_zip_archive(
    source_dir: Path,
    output_path: Path,
    console_output: bool = True,
) -> Path:
    """
    Create ZIP archive of the output directory.

    Args:
        source_dir: Directory to zip
        output_path: Output ZIP path (without .zip extension)
        console_output: Whether to print progress

    Returns:
        Path to created ZIP file
    """
    zip_path = shutil.make_archive(
        str(output_path),
        "zip",
        source_dir,
    )

    if console_output:
        console.print(f"  [green]✓[/green] Created {Path(zip_path).name}")

    return Path(zip_path)


def publish_project(
    project: "Project",
    config: PublishConfig,
) -> PublishResult:
    """
    Publish a complete deliverable package.

    Creates a self-contained directory with:
    - All documents (HTML, PDF, PPTX, XLSX)
    - Navigation indexes (root + per-language)
    - Bundled assets (fonts, diagrams, videos)
    - Shared resources (CSS, logo)

    Args:
        project: Project to publish
        config: Publishing configuration

    Returns:
        PublishResult with details of published content
    """
    result = PublishResult(output_dir=config.output_dir)

    if config.console_output:
        console.print(f"\n[bold]Publishing {project.name}[/bold]")
        console.print(f"Output: {config.output_dir}\n")

    try:
        # Create output directory
        config.output_dir.mkdir(parents=True, exist_ok=True)

        # Bundle assets (fonts, diagrams, videos)
        if config.console_output:
            console.print("[bold]Bundling assets...[/bold]")

        bundle = bundle_project_assets(
            project,
            config.output_dir,
            include_fonts=config.include_fonts,
            include_diagrams=config.include_diagrams,
            include_videos=config.include_videos,
            console_output=config.console_output,
        )
        result.assets_bundled = bundle.files_copied

        # Generate shared CSS
        if bundle.shared_dir:
            shared_css = create_shared_css(project.theme)
            (bundle.shared_dir / "theme.css").write_text(shared_css)

            # Generate font faces CSS if fonts were downloaded
            if bundle.fonts_dir and bundle.fonts_dir.exists():
                font_css = generate_font_faces(bundle.fonts_dir)
                if font_css:
                    (bundle.shared_dir / "fonts.css").write_text(font_css)

        # Copy documents
        if config.console_output:
            console.print("\n[bold]Copying documents...[/bold]")

        result.documents_copied = copy_documents(
            project,
            config.output_dir,
            config.console_output,
        )

        # Generate navigation indexes
        if config.generate_indexes:
            if config.console_output:
                console.print("\n[bold]Generating navigation indexes...[/bold]")

            indexes = generate_navigation_indexes(
                project,
                config.output_dir,
                config.console_output,
            )
            result.root_index = indexes.get("root")
            result.language_indexes = {k: v for k, v in indexes.items() if k != "root"}

        # Create ZIP if requested
        if config.zip_output:
            if config.console_output:
                console.print("\n[bold]Creating archive...[/bold]")

            timestamp = datetime.now().strftime("%Y%m%d")
            zip_name = f"{project.name.lower().replace(' ', '-')}-{timestamp}"
            create_zip_archive(
                config.output_dir,
                config.output_dir.parent / zip_name,
                config.console_output,
            )

        result.success = True

        if config.console_output:
            console.print("\n[green]✓ Published successfully![/green]")
            console.print(f"  Documents: {result.documents_copied}")
            console.print(f"  Assets: {result.assets_bundled}")
            if result.root_index:
                console.print(f"  Open: {result.root_index}")

    except Exception as e:
        result.success = False
        result.errors.append(str(e))
        if config.console_output:
            console.print(f"\n[red]✗ Publishing failed: {e}[/red]")

    return result
