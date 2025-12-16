"""
Pack Generator Module

Creates curated ZIP packages for specific audiences.
"""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


@dataclass
class PackItem:
    """An item to include in a pack."""
    source: str  # Source path pattern or literal path
    destination: str  # Destination path in the pack
    required: bool = True  # Whether item must exist
    description: str = ""


@dataclass
class PackConfig:
    """Configuration for a pack."""
    name: str
    description: str = ""
    items: List[PackItem] = field(default_factory=list)
    include_fonts: bool = True
    include_theme_css: bool = True
    include_readme: bool = True
    languages: Optional[List[str]] = None  # None = all languages


@dataclass
class PackResult:
    """Result of pack generation."""
    name: str
    output_path: Path
    items_included: int = 0
    items_missing: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


# Default pack configurations
INVESTOR_PACK_CONFIG = PackConfig(
    name="investor-pack",
    description="Materials for investor presentations",
    items=[
        PackItem(
            source="docs/deliverables/investor/executive_summary.md",
            destination="01_Executive_Summary.md",
            description="High-level overview",
        ),
        PackItem(
            source="docs/deliverables/investor/pitch_deck_standard.md",
            destination="02_Pitch_Deck.md",
            description="Standard pitch deck",
        ),
        PackItem(
            source="docs/deliverables/investor/data_sheet.md",
            destination="03_Data_Sheet.md",
            description="Product data sheet",
        ),
        PackItem(
            source="docs/proposal/output/proposal.pdf",
            destination="04_Full_Proposal.pdf",
            required=False,
            description="Complete proposal document",
        ),
        PackItem(
            source="docs/proposal/output/pitch_deck.pptx",
            destination="05_Pitch_Deck.pptx",
            required=False,
            description="PowerPoint presentation",
        ),
        PackItem(
            source="docs/deliverables/assets/videos/en/teaser.mp4",
            destination="videos/Teaser.mp4",
            required=False,
            description="Teaser video",
        ),
        PackItem(
            source="docs/deliverables/assets/diagrams/*.svg",
            destination="diagrams/",
            required=False,
            description="Architecture diagrams",
        ),
    ],
)


PILOT_PACK_CONFIG = PackConfig(
    name="pilot-pack",
    description="Materials for pilot customer engagement",
    items=[
        PackItem(
            source="docs/deliverables/pilot/pilot_proposal.md",
            destination="01_Pilot_Proposal.md",
            description="Pilot program proposal",
        ),
        PackItem(
            source="docs/deliverables/pilot/pilot_deck.md",
            destination="02_Pilot_Presentation.md",
            description="Pilot presentation",
        ),
        PackItem(
            source="docs/deliverables/legal/pilot_agreement_template.md",
            destination="03_Pilot_Agreement_Template.md",
            required=False,
            description="Agreement template",
        ),
        PackItem(
            source="docs/proposal/output/roi_calculator.xlsx",
            destination="04_ROI_Calculator.xlsx",
            required=False,
            description="ROI calculator spreadsheet",
        ),
        PackItem(
            source="docs/deliverables/demo/en/interactive-demo.html",
            destination="demo/Interactive_Demo.html",
            required=False,
            description="Interactive demo",
        ),
        PackItem(
            source="docs/deliverables/assets/videos/en/mvp-full-demo.mp4",
            destination="videos/MVP_Demo.mp4",
            required=False,
            description="Full demo video",
        ),
        PackItem(
            source="docs/deliverables/sales/before_after.md",
            destination="05_Before_After_Comparison.md",
            required=False,
            description="Before/after comparison",
        ),
    ],
)


def resolve_source_path(
    project: "Project",
    source: str,
    language: Optional[str] = None,
) -> List[Path]:
    """
    Resolve a source path pattern to actual files.

    Args:
        project: Project root
        source: Source path or glob pattern
        language: Optional language to substitute

    Returns:
        List of resolved paths
    """
    # Substitute language placeholder
    if language and "{lang}" in source:
        source = source.replace("{lang}", language)

    source_path = project.root / source

    # Check if it's a glob pattern
    if "*" in source:
        parent = source_path.parent
        pattern = source_path.name
        if parent.exists():
            return list(parent.glob(pattern))
        return []

    # Literal path
    if source_path.exists():
        return [source_path]

    return []


def copy_item(
    source: Path,
    dest_dir: Path,
    dest_name: Optional[str] = None,
) -> bool:
    """
    Copy a file to the destination.

    Args:
        source: Source file path
        dest_dir: Destination directory
        dest_name: Optional destination filename

    Returns:
        True if successful
    """
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / (dest_name or source.name)
        shutil.copy2(source, dest_path)
        return True
    except Exception:
        return False


def generate_readme(
    config: PackConfig,
    items_included: List[str],
    project_name: str,
) -> str:
    """Generate README content for the pack."""
    lines = [
        f"# {project_name} - {config.name.replace('-', ' ').title()}",
        "",
        config.description if config.description else "",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Contents",
        "",
    ]

    for item_path in sorted(items_included):
        lines.append(f"- {item_path}")

    lines.extend([
        "",
        "---",
        "",
        "For questions, contact the project team.",
    ])

    return "\n".join(lines)


def generate_pack(
    project: "Project",
    config: PackConfig,
    output_dir: Optional[Path] = None,
    create_zip: bool = True,
    console_output: bool = True,
) -> PackResult:
    """
    Generate a pack from configuration.

    Args:
        project: Project to generate pack from
        config: Pack configuration
        output_dir: Output directory (default: project output)
        create_zip: Whether to create ZIP archive
        console_output: Whether to print progress

    Returns:
        PackResult with generation details
    """
    if console_output:
        console.print(f"\n[bold]Generating {config.name}...[/bold]")

    # Determine output paths
    output_dir = output_dir or project.output_dir
    pack_dir = output_dir / config.name
    timestamp = datetime.now().strftime("%Y%m%d")

    # Clean existing pack directory
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True)

    result = PackResult(name=config.name, output_path=pack_dir)

    # Determine languages to include
    languages = config.languages or list(project.languages.keys())

    # Process each item
    items_included = []

    for item in config.items:
        # Resolve source path
        sources = resolve_source_path(project, item.source)

        if not sources:
            if item.required:
                result.items_missing.append(item.source)
                if console_output:
                    console.print(f"  [red]✗ Missing: {item.source}[/red]")
            else:
                if console_output:
                    console.print(f"  [dim]Skipped (not found): {item.source}[/dim]")
            continue

        # Copy files
        for source in sources:
            # Determine destination
            if item.destination.endswith("/"):
                # Directory destination
                dest_dir = pack_dir / item.destination
                dest_name = source.name
            else:
                # Specific file destination
                dest_path = pack_dir / item.destination
                dest_dir = dest_path.parent
                dest_name = dest_path.name

            if copy_item(source, dest_dir, dest_name):
                rel_path = (dest_dir / dest_name).relative_to(pack_dir)
                items_included.append(str(rel_path))
                result.items_included += 1
                if console_output:
                    console.print(f"  [green]✓[/green] {rel_path}")
            else:
                if console_output:
                    console.print(f"  [yellow]Failed to copy: {source}[/yellow]")

    # Copy shared assets (fonts, theme CSS)
    if config.include_fonts:
        fonts_src = project.root / "assets" / "fonts"
        if fonts_src.exists():
            fonts_dest = pack_dir / "shared" / "fonts"
            shutil.copytree(fonts_src, fonts_dest, dirs_exist_ok=True)
            if console_output:
                console.print(f"  [dim]Included fonts[/dim]")

    # Generate README
    if config.include_readme:
        readme_content = generate_readme(config, items_included, project.name)
        (pack_dir / "README.md").write_text(readme_content)
        if console_output:
            console.print(f"  [dim]Generated README.md[/dim]")

    # Create ZIP archive
    if create_zip:
        zip_name = f"{config.name}-{timestamp}"
        zip_path = shutil.make_archive(
            str(output_dir / zip_name),
            'zip',
            pack_dir,
        )
        result.output_path = Path(zip_path)
        if console_output:
            console.print(f"\n[green]✓ Created {Path(zip_path).name}[/green]")

    # Check for missing required items
    if result.items_missing:
        result.success = False
        if console_output:
            console.print(f"\n[yellow]Warning: {len(result.items_missing)} required items missing[/yellow]")
    else:
        result.success = True

    if console_output:
        console.print(f"[dim]Included {result.items_included} items[/dim]")

    return result


def generate_investor_pack(
    project: "Project",
    output_dir: Optional[Path] = None,
    create_zip: bool = True,
    console_output: bool = True,
) -> PackResult:
    """
    Generate investor materials pack.

    Args:
        project: Project to generate pack from
        output_dir: Output directory
        create_zip: Whether to create ZIP archive
        console_output: Whether to print progress

    Returns:
        PackResult
    """
    return generate_pack(
        project,
        INVESTOR_PACK_CONFIG,
        output_dir,
        create_zip,
        console_output,
    )


def generate_pilot_pack(
    project: "Project",
    output_dir: Optional[Path] = None,
    create_zip: bool = True,
    console_output: bool = True,
) -> PackResult:
    """
    Generate pilot customer pack.

    Args:
        project: Project to generate pack from
        output_dir: Output directory
        create_zip: Whether to create ZIP archive
        console_output: Whether to print progress

    Returns:
        PackResult
    """
    return generate_pack(
        project,
        PILOT_PACK_CONFIG,
        output_dir,
        create_zip,
        console_output,
    )
