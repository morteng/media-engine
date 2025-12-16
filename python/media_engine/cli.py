#!/usr/bin/env python3
"""
Media Engine CLI

Agent-friendly command line interface for media production.

Usage:
    media-engine status [--json]
    media-engine build [--only FORMAT] [--force] [--lang LANG]
    media-engine publish [--formats LIST]
    media-engine stale [--json]
    media-engine cache status
    media-engine cache clear [--voiceover] [--builds]
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

from .core import Project, find_project
from .cms import Document, DocumentCollection


console = Console()


def cmd_status(args):
    """Show project status."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found in current directory or parents[/red]")
        sys.exit(1)

    # Check for specific view
    view = getattr(args, 'view', None)

    if args.json:
        status = project.get_status()
        print(json.dumps(status, indent=2, default=str))
        return

    # Import status module
    from .status import (
        get_project_dashboard,
        print_dashboard,
        print_document_status,
        print_video_status,
        print_quality_status,
        print_deliverable_status,
    )
    from .status.views import print_build_tree, print_cache_status

    if view == "docs":
        print_document_status(project, getattr(args, 'lang', None))
    elif view == "videos":
        print_video_status(project, getattr(args, 'lang', None))
    elif view == "quality":
        print_quality_status(project, getattr(args, 'lang', None))
    elif view == "deliverables":
        print_deliverable_status(project)
    elif view == "tree":
        print_build_tree(project)
    elif view == "cache":
        print_cache_status(project)
    else:
        # Default: comprehensive dashboard
        dashboard = get_project_dashboard(project)
        print_dashboard(dashboard)


def cmd_build(args):
    """Build media outputs."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    console.print(f"[bold]Building {project.config.name}[/bold]")

    # Determine what to build
    formats = args.only.split(",") if args.only else ["html", "pdf"]
    languages = args.lang.split(",") if args.lang else list(project.languages.keys())

    results = {
        "built": [],
        "skipped": [],
        "failed": [],
    }

    for lang in languages:
        for fmt in formats:
            output_key = f"{lang}/{fmt}"

            # Get dependencies (all chapters for now)
            deps = project.list_chapters(lang)

            if not deps:
                console.print(f"  [dim]{output_key}: no content[/dim]")
                continue

            # Check if rebuild needed
            if not args.force and not project.should_rebuild(output_key, deps):
                console.print(f"  [dim]{output_key}: up to date[/dim]")
                results["skipped"].append(output_key)
                continue

            # Build
            console.print(f"  [yellow]Building {output_key}...[/yellow]")
            try:
                output_path = _build_format(project, lang, fmt, deps)
                if output_path:
                    project.record_build(output_key, output_path, deps)
                    console.print(f"  [green]{output_key}: {output_path.name}[/green]")
                    results["built"].append(str(output_path))
                else:
                    console.print(f"  [yellow]{output_key}: builder not implemented[/yellow]")
                    results["skipped"].append(output_key)
            except Exception as e:
                console.print(f"  [red]{output_key}: {e}[/red]")
                results["failed"].append(output_key)

    # Summary
    console.print()
    console.print(f"Built: {len(results['built'])}, Skipped: {len(results['skipped'])}, Failed: {len(results['failed'])}")

    if args.json:
        print(json.dumps(results, indent=2))


def _build_format(project: Project, lang: str, fmt: str, deps: list[Path]) -> Path | None:
    """Build a specific format. Returns output path or None if not implemented."""
    output_dir = project.output_dir / lang
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "html":
        return _build_html(project, lang, deps, output_dir)
    elif fmt == "pdf":
        return _build_pdf(project, lang, deps, output_dir)
    elif fmt == "pptx":
        return _build_pptx(project, lang, output_dir)
    elif fmt == "xlsx":
        return _build_xlsx(project, lang, output_dir)
    elif fmt == "diagrams":
        return _build_diagrams(project, lang, output_dir)
    elif fmt == "video":
        return _build_video(project, lang, output_dir)

    return None


def _build_html(project: Project, lang: str, deps: list[Path], output_dir: Path) -> Path:
    """Build HTML from markdown chapters."""
    from .builders.html import HTMLBuilder, HTMLConfig

    builder = HTMLBuilder(theme=project.theme)

    # Combine all chapter content
    combined_content = []
    for dep in sorted(deps):
        doc = Document.load(dep)
        combined_content.append(doc.content)

    content = "\n\n---\n\n".join(combined_content)
    config = HTMLConfig(include_toc=True, lang=lang)

    html = builder.build(content, project.config.name, config)
    output_path = output_dir / "proposal.html"
    return builder.save(html, output_path)


def _build_pdf(project: Project, lang: str, deps: list[Path], output_dir: Path) -> Path | None:
    """Build PDF from HTML."""
    # First build HTML
    html_path = _build_html(project, lang, deps, output_dir)

    # Try to convert to PDF using weasyprint or wkhtmltopdf
    pdf_path = output_dir / "proposal.pdf"

    try:
        # Try weasyprint first
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return pdf_path
    except ImportError:
        pass

    try:
        # Fall back to wkhtmltopdf via subprocess
        import subprocess
        result = subprocess.run(
            ["wkhtmltopdf", "--quiet", str(html_path), str(pdf_path)],
            capture_output=True,
        )
        if result.returncode == 0:
            return pdf_path
    except FileNotFoundError:
        pass

    # No PDF converter available
    console.print("  [dim]PDF: install weasyprint or wkhtmltopdf for PDF output[/dim]")
    return None


def _build_pptx(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build PowerPoint presentation from slides definition."""
    from .builders.pptx import PPTXBuilder

    # Look for slides definition
    slides_yaml = project.get_content_path(lang, "slides", "pitch_deck.yaml")
    slides_md = project.get_content_path(lang, "slides", "pitch_deck.md")

    builder = PPTXBuilder(theme=project.theme)

    if slides_yaml.exists():
        builder.build_from_yaml(slides_yaml)
    elif slides_md.exists():
        builder.build_from_markdown(slides_md)
    else:
        # No slides definition found
        return None

    output_path = output_dir / "pitch_deck.pptx"
    return builder.save(output_path)


def _build_xlsx(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build Excel spreadsheet from data definition."""
    from .builders.xlsx import XLSXBuilder

    # Look for data definition
    data_yaml = project.get_content_path(lang, "data", "calculator.yaml")

    if not data_yaml.exists():
        return None

    builder = XLSXBuilder(theme=project.theme)
    builder.build_from_yaml(data_yaml)

    output_path = output_dir / "calculator.xlsx"
    return builder.save(output_path)


def _build_diagrams(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build diagrams from YAML definitions."""
    from .diagrams import DiagramGenerator, DiagramDefinition

    diagrams_dir = project.get_content_path(lang, "diagrams")
    if not diagrams_dir.exists():
        return None

    diagram_files = list(diagrams_dir.glob("*.yaml"))
    if not diagram_files:
        return None

    generator = DiagramGenerator(theme=project.theme)
    diagrams_output = output_dir / "diagrams"
    diagrams_output.mkdir(parents=True, exist_ok=True)

    generated = []
    for diagram_file in diagram_files:
        definition = DiagramDefinition.from_yaml(diagram_file)
        base_name = diagram_file.stem

        # Generate both light and dark themes
        light_path, dark_path = generator.generate_both_themes(
            definition, diagrams_output, base_name
        )
        generated.extend([light_path, dark_path])
        console.print(f"    [dim]Generated {base_name} (light + dark)[/dim]")

    return diagrams_output if generated else None


def _build_video(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build video from script definitions."""
    import asyncio
    from .video import VideoBuilder, VideoScript

    scripts_dir = project.get_content_path(lang, "scripts")
    if not scripts_dir.exists():
        return None

    script_files = list(scripts_dir.glob("*.yaml"))
    if not script_files:
        return None

    builder = VideoBuilder(project=project)
    videos_output = output_dir / "videos"
    videos_output.mkdir(parents=True, exist_ok=True)

    generated = []
    for script_file in script_files:
        try:
            # Parse script to validate it
            script = VideoScript.from_yaml(script_file)

            # Check if script has voiceover text
            has_text = any(scene.text for scene in script.scenes)
            if not has_text:
                console.print(f"    [dim]{script_file.stem}: no voiceover text[/dim]")
                continue

            # Check for voice_id configuration
            lang_config = project.languages.get(lang)
            voice_id = None
            if lang_config:
                voice_id = lang_config.voice_id
            if not voice_id:
                voice_id = project.config.voiceover.voice_id if project.config.voiceover else None

            if not voice_id:
                console.print(f"    [yellow]{script_file.stem}: no voice_id configured (skipping voiceover)[/yellow]")
                # Still export props for Remotion
                props_path = videos_output / f"{script_file.stem}.props.json"
                _export_video_props_only(script, props_path, project)
                generated.append(props_path)
                console.print(f"    [dim]Exported {script_file.stem}.props.json[/dim]")
                continue

            # Build with voiceover
            result = asyncio.run(builder.build(
                script_path=script_file,
                output_dir=videos_output,
                render=False,  # Don't render, just generate assets
            ))

            if result.success:
                if result.audio_path:
                    generated.append(result.audio_path)
                    console.print(f"    [dim]Generated {result.audio_path.name}[/dim]")
                if result.captions_path:
                    generated.append(result.captions_path)
                    console.print(f"    [dim]Generated {result.captions_path.name}[/dim]")
                if result.props_path:
                    generated.append(result.props_path)
                    console.print(f"    [dim]Generated {result.props_path.name}[/dim]")
            else:
                console.print(f"    [red]{script_file.stem}: {result.error}[/red]")

        except Exception as e:
            console.print(f"    [red]{script_file.stem}: {e}[/red]")

    return videos_output if generated else None


def _export_video_props_only(script, output_path: Path, project: Project):
    """Export Remotion props without generating voiceover."""
    import json

    fps = 30
    if project.config.video:
        fps = getattr(project.config.video, 'fps', 30)

    props = {
        "title": script.title,
        "name": script.name,
        "language": script.language,
        "fps": fps,
        "scenes": [],
    }

    for scene in script.scenes:
        props["scenes"].append({
            "id": scene.id,
            "type": scene.type,
            "title": scene.title,
            "text": scene.text,
            "visual": scene.visual,
        })

    output_path.write_text(json.dumps(props, indent=2))


def cmd_publish(args):
    """Publish complete deliverable package."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .publish import publish_project, PublishConfig

    # Determine output directory
    output_dir = Path(args.output) if args.output else project.publish_dir

    config = PublishConfig(
        output_dir=output_dir,
        include_fonts=not args.no_fonts,
        include_diagrams=not args.no_diagrams,
        include_videos=not args.no_videos,
        generate_indexes=not args.no_index,
        zip_output=args.zip,
        console_output=True,
    )

    result = publish_project(project, config)

    if not result.success:
        console.print(f"[red]Publishing failed: {', '.join(result.errors)}[/red]")
        sys.exit(1)


def cmd_quality(args):
    """Run quality checks on project content."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .quality import run_quality_checks

    report = run_quality_checks(project, console_output=True)

    if args.json:
        import json
        issues_data = [
            {
                "type": i.type,
                "severity": i.severity,
                "file": str(i.file_path),
                "line": i.line,
                "message": i.message,
                "context": i.context,
            }
            for i in report.issues
        ]
        print(json.dumps({
            "passed": report.passed,
            "files_checked": report.files_checked,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": issues_data,
        }, indent=2))
        return

    if not report.passed:
        sys.exit(1)


def cmd_stale(args):
    """List stale content."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    stale_items = []

    for lang in project.languages:
        for chapter_path in project.list_chapters(lang):
            try:
                doc = Document.load(chapter_path)
                if doc.is_stale:
                    stale_items.append({
                        "path": str(chapter_path.relative_to(project.root)),
                        "language": lang,
                        "title": doc.title,
                        "days_since_modified": doc.days_since_modified,
                        "freshness_days": doc.freshness_days,
                        "status": doc.freshness_status,
                    })
            except Exception:
                pass

    if args.json:
        print(json.dumps(stale_items, indent=2))
        return

    if not stale_items:
        console.print("[green]No stale content found[/green]")
        return

    table = Table(title="Stale Content", box=box.ROUNDED)
    table.add_column("Document", style="cyan")
    table.add_column("Lang", justify="center")
    table.add_column("Days Old", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Status", justify="center")

    for item in stale_items:
        status_color = "yellow" if item["status"] == "stale" else "red"
        table.add_row(
            item["title"],
            item["language"],
            str(item["days_since_modified"]),
            str(item["freshness_days"]),
            f"[{status_color}]{item['status']}[/{status_color}]",
        )

    console.print(table)


def cmd_cache(args):
    """Cache management commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    if args.cache_command == "status":
        status = project.get_status()
        cache = status["cache"]

        console.print(f"[bold]Cache Status[/bold]")
        console.print(f"  Voiceover files: {cache['voiceover_items']}")
        console.print(f"  Builds tracked: {cache['builds_tracked']}")

        # Show cache directory size
        cache_dir = project.cache_dir
        if cache_dir.exists():
            total_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
            console.print(f"  Cache size: {total_size / 1024 / 1024:.1f} MB")
        else:
            console.print(f"  Cache size: 0 MB")

    elif args.cache_command == "clear":
        cache_type = None
        if args.voiceover:
            cache_type = "voiceover"
        elif args.builds:
            cache_type = "builds"
        else:
            cache_type = "all"

        count = project.clear_cache(cache_type)
        console.print(f"[green]Cleared {count} cached items[/green]")


def cmd_init(args):
    """Initialize a new project."""
    project_dir = Path(args.directory or ".").resolve()
    project_name = args.name or project_dir.name

    console.print(f"[bold]Initializing project: {project_name}[/bold]")

    # Create directory structure
    dirs = [
        "content/en/chapters",
        "content/en/scripts",
        "assets/brand",
        "output",
    ]

    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
        console.print(f"  [dim]Created {d}/[/dim]")

    # Create project.yaml
    project_yaml = project_dir / "project.yaml"
    if not project_yaml.exists():
        project_yaml.write_text(f"""# Media Engine Project Configuration

project:
  name: "{project_name}"
  description: ""

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
      voice_id: ""

voiceover:
  provider: "elevenlabs"
  stability: 0.5
  similarity_boost: 0.75

video:
  width: 1920
  height: 1080
  fps: 30

paths:
  content: "content"
  assets: "assets"
  output: "output"
""")
        console.print(f"  [green]Created project.yaml[/green]")

    # Create theme.yaml
    theme_yaml = project_dir / "theme.yaml"
    if not theme_yaml.exists():
        theme_yaml.write_text("""# Design System Theme

name: "Default Theme"

colors:
  primary: "#2c2522"
  secondary: "#4a4340"
  accent: "#0066cc"
  background: "#ffffff"
  text: "#2c2522"

  dark:
    background: "#1a1a1a"
    text: "#f0f0f0"
    accent: "#3399ff"

typography:
  heading: "Georgia"
  body: "Helvetica Neue"
  code: "Menlo"
  base_size: 16
  scale: 1.25
""")
        console.print(f"  [green]Created theme.yaml[/green]")

    # Create sample chapter
    sample_chapter = project_dir / "content/en/chapters/01_introduction.md"
    if not sample_chapter.exists():
        sample_chapter.write_text(f"""---
title: "Introduction"
version: "0.1.0"
status: "draft"
last_modified: "{datetime.now().strftime('%Y-%m-%d')}"
freshness_days: 30
---

# Introduction

Welcome to {project_name}.

## Getting Started

This is your first chapter. Edit this file to add your content.
""")
        console.print(f"  [green]Created sample chapter[/green]")

    console.print(f"\n[bold green]Project initialized![/bold green]")
    console.print(f"  Run [cyan]media-engine status[/cyan] to see project status")
    console.print(f"  Run [cyan]media-engine build[/cyan] to build outputs")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="media-engine",
        description="Agent-based media production framework",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("view", nargs="?",
                               choices=["docs", "videos", "quality", "deliverables", "tree", "cache"],
                               help="Specific view: docs, videos, quality, deliverables, tree, cache")
    status_parser.add_argument("--lang", help="Filter by language")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # build
    build_parser = subparsers.add_parser("build", help="Build media outputs")
    build_parser.add_argument("--only", help="Only build specific formats (comma-separated)")
    build_parser.add_argument("--force", action="store_true", help="Force rebuild all")
    build_parser.add_argument("--lang", help="Only build specific languages (comma-separated)")
    build_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    # publish
    publish_parser = subparsers.add_parser("publish", help="Publish complete deliverable package")
    publish_parser.add_argument("--output", "-o", help="Output directory (default: project publish_dir)")
    publish_parser.add_argument("--no-fonts", action="store_true", help="Skip font bundling")
    publish_parser.add_argument("--no-diagrams", action="store_true", help="Skip diagram bundling")
    publish_parser.add_argument("--no-videos", action="store_true", help="Skip video bundling")
    publish_parser.add_argument("--no-index", action="store_true", help="Skip navigation index generation")
    publish_parser.add_argument("--zip", action="store_true", help="Create ZIP archive")

    # quality
    quality_parser = subparsers.add_parser("quality", help="Run quality checks")
    quality_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # stale
    stale_parser = subparsers.add_parser("stale", help="List stale content")
    stale_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # cache
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command")

    cache_status = cache_subparsers.add_parser("status", help="Show cache status")
    cache_clear = cache_subparsers.add_parser("clear", help="Clear cache")
    cache_clear.add_argument("--voiceover", action="store_true", help="Clear voiceover cache only")
    cache_clear.add_argument("--builds", action="store_true", help="Clear builds cache only")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("directory", nargs="?", help="Project directory")
    init_parser.add_argument("--name", help="Project name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "status": cmd_status,
        "build": cmd_build,
        "publish": cmd_publish,
        "quality": cmd_quality,
        "stale": cmd_stale,
        "cache": cmd_cache,
        "init": cmd_init,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
