"""
Font Management Module

Downloads Google Fonts for offline use and generates @font-face declarations.
"""

import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from rich.console import Console

console = Console()


@dataclass
class FontConfig:
    """Configuration for a font family."""

    name: str
    weights: List[int] = field(default_factory=lambda: [400])
    italic: bool = False


# Common font configurations
COMMON_FONTS = {
    "Fraunces": FontConfig(name="Fraunces", weights=[300, 400, 600, 700]),
    "Source Sans 3": FontConfig(name="Source Sans 3", weights=[300, 400, 500, 600, 700]),
    "JetBrains Mono": FontConfig(name="JetBrains Mono", weights=[400, 500, 600]),
    "Inter": FontConfig(name="Inter", weights=[300, 400, 500, 600, 700]),
    "Roboto": FontConfig(name="Roboto", weights=[300, 400, 500, 700]),
}


def get_google_fonts_url(font_name: str, weights: List[int]) -> str:
    """Build Google Fonts CSS URL."""
    weights_str = ";".join(str(w) for w in sorted(weights))
    font_encoded = font_name.replace(" ", "+")
    return (
        f"https://fonts.googleapis.com/css2?family={font_encoded}:wght@{weights_str}&display=swap"
    )


def download_google_fonts(
    fonts: List[FontConfig],
    output_dir: Path,
    console_output: bool = True,
) -> Dict[str, List[Path]]:
    """
    Download Google Fonts WOFF2 files for offline use.

    Args:
        fonts: List of FontConfig to download
        output_dir: Directory to save fonts
        console_output: Whether to print progress

    Returns:
        Dictionary mapping font names to list of downloaded file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # User-Agent that requests woff2 format
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    downloaded = {}

    for font_config in fonts:
        font_name = font_config.name
        font_dir = output_dir / font_name.lower().replace(" ", "-")
        font_dir.mkdir(exist_ok=True)

        # Check if already downloaded
        existing = list(font_dir.glob("*.woff2"))
        if existing:
            downloaded[font_name] = existing
            if console_output:
                console.print(f"  [dim]{font_name}: already downloaded[/dim]")
            continue

        try:
            # Get CSS with font URLs
            css_url = get_google_fonts_url(font_name, font_config.weights)
            req = urllib.request.Request(css_url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                css_content = response.read().decode("utf-8")

            # Extract woff2 URLs
            woff2_urls = re.findall(
                r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", css_content
            )

            font_files = []
            for i, font_url in enumerate(woff2_urls[: len(font_config.weights)]):
                weight = font_config.weights[i] if i < len(font_config.weights) else 400
                filename = f"{font_name.lower().replace(' ', '-')}-{weight}.woff2"
                dest = font_dir / filename

                if not dest.exists():
                    if console_output:
                        console.print(f"  Downloading {font_name} {weight}...")

                    req = urllib.request.Request(font_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=30) as response:
                        with open(dest, "wb") as f:
                            f.write(response.read())

                font_files.append(dest)

            downloaded[font_name] = font_files

            if console_output:
                console.print(
                    f"  [green]✓[/green] {font_name}: {len(font_files)} weights downloaded"
                )

        except Exception as e:
            if console_output:
                console.print(f"  [yellow]{font_name}: download failed ({e})[/yellow]")
            downloaded[font_name] = []

    return downloaded


def generate_font_faces(
    fonts_dir: Path,
    fonts: List[FontConfig] = None,
    relative_path: str = "./fonts",
) -> str:
    """
    Generate @font-face CSS declarations for downloaded fonts.

    Args:
        fonts_dir: Directory containing font subdirectories
        fonts: List of FontConfig (for weight mapping)
        relative_path: Relative path to fonts in CSS

    Returns:
        CSS string with @font-face declarations
    """
    fonts_dir = Path(fonts_dir)
    if not fonts_dir.exists():
        return ""

    font_faces = ["/* Local Fonts */"]

    # Build config lookup
    font_configs = {fc.name: fc for fc in (fonts or [])}

    # Map of directory names to proper font family names
    font_name_map = {
        "inter": "Inter",
        "jetbrains-mono": "JetBrains Mono",
        "source-sans-3": "Source Sans 3",
        "fraunces": "Fraunces",
        "roboto": "Roboto",
    }

    for font_subdir in fonts_dir.iterdir():
        if not font_subdir.is_dir():
            continue

        font_files = sorted(font_subdir.glob("*.woff2"))
        if not font_files:
            continue

        # Determine font family name from directory (use map or title case)
        dir_name = font_subdir.name.lower()
        if dir_name in font_name_map:
            font_family = font_name_map[dir_name]
        else:
            # Fallback: title case with spaces
            font_family = " ".join(font_subdir.name.replace("-", " ").title().split())

        # Get weight config if available
        config = font_configs.get(font_family)
        weights = config.weights if config else [400]

        for i, font_file in enumerate(font_files):
            # Extract weight from filename or use config
            weight_match = re.search(r"-(\d{3})\.woff2$", font_file.name)
            if weight_match:
                weight = int(weight_match.group(1))
            elif i < len(weights):
                weight = weights[i]
            else:
                weight = 400

            font_faces.append(f"""
@font-face {{
    font-family: '{font_family}';
    font-weight: {weight};
    font-display: swap;
    src: url('{relative_path}/{font_subdir.name}/{font_file.name}') format('woff2');
}}""")

    return "\n".join(font_faces)


def download_theme_fonts(
    theme,
    output_dir: Path,
    console_output: bool = True,
) -> Dict[str, List[Path]]:
    """
    Download fonts specified in a theme.

    Args:
        theme: Theme object with typography settings
        output_dir: Directory to save fonts
        console_output: Whether to print progress

    Returns:
        Dictionary mapping font names to downloaded paths
    """
    fonts = []

    # Get fonts from theme typography
    heading_font = theme.typography.heading
    body_font = theme.typography.body
    code_font = theme.typography.code

    # Check if they're in common fonts
    for font_name in [heading_font, body_font, code_font]:
        if font_name in COMMON_FONTS:
            fonts.append(COMMON_FONTS[font_name])
        else:
            # Default config for unknown fonts
            fonts.append(FontConfig(name=font_name, weights=[400, 600, 700]))

    return download_google_fonts(fonts, output_dir, console_output)
