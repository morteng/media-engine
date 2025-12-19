"""
Content Scanner

Auto-discovers and registers content from standard project locations.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from .registry import ContentRegistry
from .types import ContentType

if TYPE_CHECKING:
    from ..core.project import Project


def scan_project(project: "Project", registry: ContentRegistry) -> int:
    """
    Scan project and auto-register discovered content.

    Returns the number of items registered.
    """
    registered = 0

    # Scan source documents
    registered += _scan_source_documents(project, registry)

    # Scan video scripts and renders
    registered += _scan_video_content(project, registry)

    # Scan demo content
    registered += _scan_demo_content(project, registry)

    # Scan deliverables
    registered += _scan_deliverables(project, registry)

    # Scan config files
    registered += _scan_config_files(project, registry)

    return registered


def _scan_source_documents(project: "Project", registry: ContentRegistry) -> int:
    """Scan and register source documents."""
    registered = 0

    for lang in project.languages:
        # Chapters
        chapters_dir = project.content_dir / lang / "chapters"
        if chapters_dir.exists():
            for md_file in chapters_dir.glob("*.md"):
                registry.register(
                    path=md_file.relative_to(project.root),
                    content_type=ContentType.SOURCE_DOCUMENT,
                    depends_on=[project.root / "theme.yaml"] if (project.root / "theme.yaml").exists() else [],
                )
                registered += 1

        # Other content directories
        for subdir in ["scripts", "data"]:
            content_subdir = project.content_dir / lang / subdir
            if content_subdir.exists():
                for yaml_file in content_subdir.glob("*.yaml"):
                    registry.register(
                        path=yaml_file.relative_to(project.root),
                        content_type=ContentType.SOURCE_DOCUMENT,
                    )
                    registered += 1

    return registered


def _scan_video_content(project: "Project", registry: ContentRegistry) -> int:
    """Scan and register video scripts and renders with dependencies."""
    registered = 0

    # Look for video scripts in docs/deliverables/video/scripts/
    video_scripts_dir = project.root / "docs" / "deliverables" / "video" / "scripts"

    if not video_scripts_dir.exists():
        return 0

    # Get shared demo dependencies
    demo_shared = project.root / "docs" / "deliverables" / "demo" / "shared"
    shared_deps = []
    if demo_shared.exists():
        for ext in ["*.css", "*.js", "*.svg"]:
            for f in demo_shared.glob(ext):
                shared_deps.append(f.relative_to(project.root))

    # Scan video scripts per language
    for lang_dir in video_scripts_dir.iterdir():
        if not lang_dir.is_dir():
            continue

        lang = lang_dir.name

        for script_file in lang_dir.glob("*.yaml"):
            # Register the script
            registry.register(
                path=script_file.relative_to(project.root),
                content_type=ContentType.VIDEO_SCRIPT,
            )
            registered += 1

            # Parse script to find output filename and demo_url
            try:
                with open(script_file) as f:
                    script_data = yaml.safe_load(f)

                output_filename = script_data.get("output", {}).get("filename")
                if not output_filename:
                    output_filename = f"{script_file.stem}.mp4"

                demo_url = script_data.get("demo_url", "")

                # Build dependencies for the video render
                video_deps = [script_file.relative_to(project.root)]
                video_deps.extend(shared_deps)

                # Add specific demo HTML if referenced
                if demo_url:
                    if demo_url.startswith("demo/"):
                        demo_path = project.root / "docs" / "deliverables" / demo_url
                    else:
                        demo_path = project.root / "docs" / "deliverables" / "demo" / demo_url

                    if demo_path.exists():
                        video_deps.append(demo_path.relative_to(project.root))

                # Check if render exists
                videos_dir = project.root / "docs" / "deliverables" / "assets" / "videos" / lang
                render_path = videos_dir / output_filename

                if render_path.exists():
                    registry.register(
                        path=render_path.relative_to(project.root),
                        content_type=ContentType.VIDEO_RENDER,
                        depends_on=video_deps,
                    )
                    registered += 1

            except Exception:
                pass  # Skip malformed scripts

    return registered


def _scan_demo_content(project: "Project", registry: ContentRegistry) -> int:
    """Scan and register demo HTML and assets."""
    registered = 0

    demo_dir = project.root / "docs" / "deliverables" / "demo"
    if not demo_dir.exists():
        return 0

    # Shared assets
    shared_dir = demo_dir / "shared"
    if shared_dir.exists():
        for ext in ["*.css", "*.js", "*.svg", "*.png", "*.jpg"]:
            for f in shared_dir.glob(ext):
                registry.register(
                    path=f.relative_to(project.root),
                    content_type=ContentType.DEMO_ASSET,
                )
                registered += 1

    # Per-language demo pages
    for lang in project.languages:
        lang_demo_dir = demo_dir / lang
        if lang_demo_dir.exists():
            for html_file in lang_demo_dir.glob("*.html"):
                # Demo pages depend on shared assets
                deps = []
                if shared_dir.exists():
                    for ext in ["*.css", "*.js"]:
                        for f in shared_dir.glob(ext):
                            deps.append(f.relative_to(project.root))

                registry.register(
                    path=html_file.relative_to(project.root),
                    content_type=ContentType.DEMO_HTML,
                    depends_on=deps,
                )
                registered += 1

    return registered


def _scan_deliverables(project: "Project", registry: ContentRegistry) -> int:
    """Scan and register output deliverables."""
    registered = 0

    for lang in project.languages:
        output_dir = project.output_dir / lang

        if not output_dir.exists():
            continue

        # HTML outputs
        for html_file in output_dir.glob("*.html"):
            # HTML depends on source markdown and theme
            deps = []

            # Find corresponding source document
            # (simplified - assumes naming convention)
            source_name = html_file.stem + ".md"
            for subdir in ["chapters", ""]:
                source_path = project.content_dir / lang / subdir / source_name
                if source_path.exists():
                    deps.append(source_path.relative_to(project.root))
                    break

            if (project.root / "theme.yaml").exists():
                deps.append(Path("theme.yaml"))

            registry.register(
                path=html_file.relative_to(project.root),
                content_type=ContentType.DELIVERABLE,
                depends_on=deps,
            )
            registered += 1

        # PDF outputs
        for pdf_file in output_dir.glob("*.pdf"):
            registry.register(
                path=pdf_file.relative_to(project.root),
                content_type=ContentType.DELIVERABLE,
            )
            registered += 1

        # PPTX outputs
        for pptx_file in output_dir.glob("*.pptx"):
            registry.register(
                path=pptx_file.relative_to(project.root),
                content_type=ContentType.DELIVERABLE,
            )
            registered += 1

    return registered


def _scan_config_files(project: "Project", registry: ContentRegistry) -> int:
    """Scan and register configuration files."""
    registered = 0

    # Theme
    theme_path = project.root / "theme.yaml"
    if theme_path.exists():
        registry.register(
            path=Path("theme.yaml"),
            content_type=ContentType.THEME,
        )
        registered += 1

    # Project config
    config_path = project.root / "project.yaml"
    if config_path.exists():
        registry.register(
            path=Path("project.yaml"),
            content_type=ContentType.CONFIG,
        )
        registered += 1

    return registered
