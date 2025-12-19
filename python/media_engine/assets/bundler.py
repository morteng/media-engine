"""
Asset Bundler Module

Bundles project assets for self-contained deliverable packages.
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from rich.console import Console

from .fonts import download_theme_fonts, generate_font_faces

if TYPE_CHECKING:
    from ..core.project import Project
    from ..core.theme import Theme

console = Console()


@dataclass
class AssetBundle:
    """Result of asset bundling."""

    output_dir: Path
    fonts_dir: Optional[Path] = None
    shared_dir: Optional[Path] = None
    files_copied: int = 0
    fonts_downloaded: Dict[str, List[Path]] = field(default_factory=dict)


def bundle_project_assets(
    project: "Project",
    output_dir: Path,
    include_fonts: bool = True,
    include_diagrams: bool = True,
    include_videos: bool = True,
    console_output: bool = True,
) -> AssetBundle:
    """
    Bundle all project assets for a self-contained package.

    Args:
        project: Project to bundle assets for
        output_dir: Root output directory
        include_fonts: Whether to download and include fonts
        include_diagrams: Whether to include diagrams
        include_videos: Whether to include video assets
        console_output: Whether to print progress

    Returns:
        AssetBundle with information about bundled assets
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = AssetBundle(output_dir=output_dir)

    # Create shared directory for CSS, JS, fonts
    shared_dir = output_dir / "shared"
    shared_dir.mkdir(exist_ok=True)
    result.shared_dir = shared_dir

    # Download and bundle fonts
    if include_fonts:
        if console_output:
            console.print("  [bold]Downloading fonts...[/bold]")

        fonts_dir = shared_dir / "fonts"
        result.fonts_downloaded = download_theme_fonts(
            project.theme,
            fonts_dir,
            console_output=console_output,
        )
        result.fonts_dir = fonts_dir

        # Generate font CSS
        font_css = generate_font_faces(fonts_dir)
        if font_css:
            (shared_dir / "fonts.css").write_text(font_css)

    # Copy diagrams to each language folder
    if include_diagrams:
        if console_output:
            console.print("  [bold]Copying diagrams...[/bold]")

        for lang in project.languages:
            diagrams_src = project.output_dir / lang / "diagrams"
            if diagrams_src.exists():
                diagrams_dest = output_dir / lang / "diagrams"
                diagrams_dest.mkdir(parents=True, exist_ok=True)

                for diagram in diagrams_src.glob("*"):
                    if diagram.is_file():
                        shutil.copy2(diagram, diagrams_dest / diagram.name)
                        result.files_copied += 1

    # Copy videos (all MP4 deliverables)
    if include_videos:
        if console_output:
            console.print("  [bold]Copying video deliverables...[/bold]")

        for lang in project.languages:
            assets_videos = project.assets_dir / "videos" / lang
            if assets_videos.exists():
                videos_dest = output_dir / lang / "videos"
                videos_dest.mkdir(parents=True, exist_ok=True)

                # Copy all MP4 files from the assets/videos/{lang} folder
                # Skip temp files and files with .temp in the name
                for video_file in assets_videos.glob("*.mp4"):
                    if video_file.is_file() and ".temp" not in video_file.name:
                        shutil.copy2(video_file, videos_dest / video_file.name)
                        result.files_copied += 1

    # Copy project logo if exists
    # Search in priority order, looking for common patterns
    logo_search_dirs = [
        # Brand folder (preferred for projects with brand guidelines)
        project.root / "docs" / "brand" / "logo",
        # Standard asset locations
        project.root / "assets",
        project.root,
    ]

    logo_found = False
    for search_dir in logo_search_dirs:
        if not search_dir.exists():
            continue

        # Look for logos with common naming patterns (dark mode version first)
        logo_patterns = [
            "*-full.svg",      # e.g., pikkolo-hub-full.svg (dark bg/light text)
            "*-icon.svg",      # e.g., pikkolo-hub-icon.svg
            "logo.svg",
            "logo.png",
            "*logo*.svg",      # Any file with 'logo' in name
            "*logo*.png",
        ]

        for pattern in logo_patterns:
            matches = list(search_dir.glob(pattern))
            if matches:
                # Prefer 'full' variant for main logo (but not the -light variant)
                logo_path = matches[0]
                for m in matches:
                    if "full" in m.name.lower() and "-light" not in m.name.lower():
                        logo_path = m
                        break

                ext = logo_path.suffix
                dest_name = f"logo{ext}"
                shutil.copy2(logo_path, shared_dir / dest_name)
                result.files_copied += 1
                if console_output:
                    console.print(f"  [green]✓[/green] Copied logo: {logo_path.name} → {dest_name}")

                # Also copy light variant if it exists
                light_variant = logo_path.parent / logo_path.name.replace("-full.", "-full-light.")
                if light_variant.exists():
                    shutil.copy2(light_variant, shared_dir / f"logo-light{ext}")
                    result.files_copied += 1
                    if console_output:
                        console.print(
                            f"  [green]✓[/green] Copied logo: {light_variant.name} → logo-light{ext}"
                        )

                logo_found = True
                break

        if logo_found:
            break

    if console_output:
        console.print(f"  [green]✓[/green] Bundled {result.files_copied} asset files")

    return result


def create_shared_css(
    theme: "Theme",
    fonts_path: str = "../shared/fonts",
    include_font_faces: bool = True,
) -> str:
    """
    Create shared CSS file with theme variables and optional font faces.

    Args:
        theme: Theme to generate CSS for
        fonts_path: Relative path to fonts directory
        include_font_faces: Whether to include @font-face declarations

    Returns:
        CSS string
    """
    css_parts = []

    # CSS Variables
    css_parts.append(f"""/* Theme Variables */
:root {{
    /* Typography */
    --font-heading: '{theme.typography.heading}', Georgia, serif;
    --font-body: '{theme.typography.body}', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-code: '{theme.typography.code}', 'SF Mono', Monaco, monospace;
    --base-size: {theme.typography.base_size}px;
    --scale: {theme.typography.scale};
}}

/* Dark theme */
:root, [data-theme="dark"] {{
    --bg-primary: {theme.dark.background};
    --bg-secondary: #242120;
    --bg-tertiary: #2e2a28;
    --text-primary: {theme.dark.text};
    --text-secondary: #b8b2ac;
    --text-muted: {theme.dark.muted};
    --border-color: {theme.dark.border};
    --accent-color: {theme.dark.accent};
}}

/* Light theme */
[data-theme="light"] {{
    --bg-primary: {theme.colors.background};
    --bg-secondary: #f7f4f1;
    --bg-tertiary: #efe9e4;
    --text-primary: {theme.colors.text};
    --text-secondary: {theme.colors.secondary};
    --text-muted: {theme.colors.muted};
    --border-color: {theme.colors.border};
    --accent-color: {theme.colors.accent};
}}""")

    return "\n\n".join(css_parts)
