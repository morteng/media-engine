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

    # Proposal/Document
    proposal_items = []
    proposal_path = lang_output / "proposal.html"
    if proposal_path.exists():
        proposal_items.append(
            DeliverableItem(
                name="Full Proposal",
                path="proposal.html",
                description="Complete proposal document",
                file_type="html",
            )
        )

    # Check for PDF version
    pdf_path = lang_output / "proposal.pdf"
    if pdf_path.exists():
        proposal_items.append(
            DeliverableItem(
                name="Full Proposal (PDF)",
                path="proposal.pdf",
                description="Printable PDF version",
                file_type="pdf",
            )
        )

    if proposal_items:
        categories.append(
            DeliverableCategory(
                name="Documentation",
                icon="document",
                items=proposal_items,
            )
        )

    # Presentations
    presentation_items = []
    presentations_dir = lang_output / "presentations"
    if presentations_dir.exists():
        for pres in presentations_dir.glob("*.html"):
            presentation_items.append(
                DeliverableItem(
                    name=pres.stem.replace("_", " ").title(),
                    path=f"presentations/{pres.name}",
                    file_type="html",
                )
            )
        for pres in presentations_dir.glob("*.pptx"):
            presentation_items.append(
                DeliverableItem(
                    name=f"{pres.stem.replace('_', ' ').title()} (PowerPoint)",
                    path=f"presentations/{pres.name}",
                    file_type="pptx",
                )
            )

    if presentation_items:
        categories.append(
            DeliverableCategory(
                name="Presentations",
                icon="presentation",
                items=presentation_items,
            )
        )

    # Videos
    video_items = []
    videos_dir = lang_output / "videos"
    if videos_dir.exists():
        for video in videos_dir.glob("*.mp4"):
            video_items.append(
                DeliverableItem(
                    name=video.stem.replace("-", " ").replace("_", " ").title(),
                    path=f"videos/{video.name}",
                    file_type="mp4",
                )
            )

    if video_items:
        categories.append(
            DeliverableCategory(
                name="Videos",
                icon="video",
                items=video_items,
            )
        )

    # Spreadsheets
    spreadsheet_items = []
    spreadsheets_dir = lang_output / "spreadsheets"
    if spreadsheets_dir.exists():
        for ss in spreadsheets_dir.glob("*.xlsx"):
            spreadsheet_items.append(
                DeliverableItem(
                    name=ss.stem.replace("_", " ").title(),
                    path=f"spreadsheets/{ss.name}",
                    file_type="xlsx",
                )
            )

    if spreadsheet_items:
        categories.append(
            DeliverableCategory(
                name="Spreadsheets",
                icon="spreadsheet",
                items=spreadsheet_items,
            )
        )

    # Diagrams
    diagram_items = []
    diagrams_dir = lang_output / "diagrams"
    if diagrams_dir.exists():
        for diagram in diagrams_dir.glob("*.png"):
            diagram_items.append(
                DeliverableItem(
                    name=diagram.stem.replace("_", " ").title(),
                    path=f"diagrams/{diagram.name}",
                    file_type="png",
                )
            )

    if diagram_items:
        categories.append(
            DeliverableCategory(
                name="Diagrams",
                icon="diagram",
                items=diagram_items,
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

        index_html = render_language_index(
            project_name=project.name,
            lang_code=lang_info.code,
            lang_name=lang_info.name,
            categories=categories,
            theme=theme,
            logo_path="../shared/logo.svg"
            if (output_dir / "shared" / "logo.svg").exists()
            else None,
        )

        index_path = lang_dir / "index.html"
        index_path.write_text(index_html)
        indexes[lang_info.code] = index_path

        if console_output:
            console.print(f"  [green]✓[/green] Generated {lang_info.code}/index.html")

    # Generate root index
    theme = project.theme if hasattr(project, "theme") else None

    root_html = render_project_index(
        project_name=project.name,
        languages=languages,
        theme=theme,
        tagline=getattr(project, "tagline", ""),
        logo_path="shared/logo.svg" if (output_dir / "shared" / "logo.svg").exists() else None,
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

        # Copy subdirectories
        for subdir in ["presentations", "spreadsheets", "deliverables"]:
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
