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


def cmd_search(args):
    """Search project documents."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .search import build_search_index, search_documents, SearchIndex

    query = args.query

    # Build or load index
    index_path = project.cache_dir / "search_index.json"

    if args.rebuild or not index_path.exists():
        console.print("[bold]Building search index...[/bold]")
        index = build_search_index(project, console_output=not args.json)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index.save(index_path)
    else:
        index = SearchIndex.load(index_path)

    # Search
    results = index.search(query, limit=args.limit)

    if args.json:
        output = {
            "query": query,
            "results": [
                {
                    "id": r.entry.id,
                    "title": r.entry.title,
                    "path": r.entry.path,
                    "score": r.score,
                    "excerpt": r.entry.excerpt,
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2))
        return

    if not results:
        console.print(f"[dim]No results for: {query}[/dim]")
        return

    console.print(f"\n[bold]Search results for: {query}[/bold]\n")

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Title", style="cyan", width=35)
    table.add_column("Type", width=12)
    table.add_column("Excerpt", width=50)

    for result in results:
        excerpt = result.entry.excerpt[:47] + "..." if len(result.entry.excerpt) > 50 else result.entry.excerpt
        table.add_row(
            f"{result.score:.0f}",
            result.entry.title,
            result.entry.type,
            excerpt,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} results[/dim]")


def cmd_validate(args):
    """Run validation checks on project."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .validation import validate_project, validate_references

    # Determine schema path
    schema_path = None
    if args.schema:
        schema_path = Path(args.schema)
        if not schema_path.exists():
            console.print(f"[red]Schema file not found: {schema_path}[/red]")
            sys.exit(1)

    if args.refs_only:
        # Only check references
        errors = validate_references(project, console_output=True)
        if errors and not args.json:
            sys.exit(1)
        return

    # Full validation
    report = validate_project(project, schema_path, console_output=not args.json)

    if args.json:
        output = {
            "passed": report.passed,
            "files_checked": report.files_checked,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": [
                {
                    "type": i.type,
                    "severity": i.severity,
                    "file": str(i.file_path),
                    "line": i.line,
                    "message": i.message,
                    "field": i.field,
                }
                for i in report.issues
            ],
        }
        print(json.dumps(output, indent=2))

    if not report.passed:
        sys.exit(1)


def cmd_pack(args):
    """Generate curated packs for specific audiences."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .packs import generate_investor_pack, generate_pilot_pack

    pack_type = args.type
    output_dir = Path(args.output) if args.output else project.output_dir

    if pack_type == "investor":
        result = generate_investor_pack(
            project,
            output_dir,
            create_zip=not args.no_zip,
            console_output=True,
        )
    elif pack_type == "pilot":
        result = generate_pilot_pack(
            project,
            output_dir,
            create_zip=not args.no_zip,
            console_output=True,
        )
    else:
        console.print(f"[red]Unknown pack type: {pack_type}[/red]")
        console.print("[dim]Available: investor, pilot[/dim]")
        sys.exit(1)

    if not result.success:
        console.print(f"[yellow]Pack generated with missing items[/yellow]")
        for item in result.items_missing:
            console.print(f"  [red]Missing: {item}[/red]")
        sys.exit(1)


def cmd_index(args):
    """Build or update search index."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .search import build_search_index

    index = build_search_index(project, console_output=True)

    # Save index
    output_path = Path(args.output) if args.output else project.cache_dir / "search_index.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    index.save(output_path)

    console.print(f"\n[green]✓ Index saved to {output_path}[/green]")
    console.print(f"  Entries: {len(index.entries)}")


def cmd_translation(args):
    """Translation tracking commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .cms.translation import TranslationTracker

    tracker = TranslationTracker(project)

    if args.translation_command == "status":
        _translation_status(tracker, args)
    elif args.translation_command == "outdated":
        _translation_outdated(tracker, args)
    elif args.translation_command == "missing":
        _translation_missing(tracker, project, args)
    else:
        console.print("[red]Unknown translation command[/red]")
        sys.exit(1)


def _translation_status(tracker, args):
    """Show translation status."""
    statuses = tracker.get_all_statuses()

    if args.json:
        output = [
            {
                "source": str(s.source_path),
                "translation": str(s.translation_path),
                "source_version": s.source_version,
                "translated_version": s.translated_version,
                "is_outdated": s.is_outdated,
                "source_language": s.source_language,
                "target_language": s.target_language,
            }
            for s in statuses
        ]
        print(json.dumps(output, indent=2))
        return

    if not statuses:
        console.print("[dim]No translations found[/dim]")
        return

    console.print(f"\n[bold]Translation Status[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Source", style="cyan")
    table.add_column("Translation", style="cyan")
    table.add_column("Lang", justify="center")
    table.add_column("Source Ver", justify="center")
    table.add_column("Trans Ver", justify="center")
    table.add_column("Status", justify="center")

    for status in statuses:
        status_color = "red" if status.is_outdated else "green"
        status_text = "outdated" if status.is_outdated else "current"

        table.add_row(
            status.source_title[:30],
            status.translation_title[:30],
            status.target_language,
            status.source_version,
            status.translated_version,
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    outdated_count = sum(1 for s in statuses if s.is_outdated)
    if outdated_count > 0:
        console.print(f"\n[yellow]⚠ {outdated_count} translation(s) need updating[/yellow]")
    else:
        console.print(f"\n[green]✓ All translations are current[/green]")


def _translation_outdated(tracker, args):
    """Show only outdated translations."""
    outdated = tracker.get_outdated_translations()

    if args.json:
        output = [
            {
                "source": str(s.source_path),
                "translation": str(s.translation_path),
                "source_version": s.source_version,
                "translated_version": s.translated_version,
                "target_language": s.target_language,
            }
            for s in outdated
        ]
        print(json.dumps(output, indent=2))
        return

    if not outdated:
        console.print("[green]✓ No outdated translations[/green]")
        return

    console.print(f"\n[bold]Outdated Translations[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Translation", style="cyan")
    table.add_column("Lang")
    table.add_column("Source Ver", justify="center")
    table.add_column("Trans Ver", justify="center")
    table.add_column("Behind", justify="center")

    for status in outdated:
        table.add_row(
            status.translation_title[:40],
            status.target_language,
            status.source_version,
            status.translated_version,
            f"[red]{status.source_version}[/red]",
        )

    console.print(table)
    console.print(f"\n[yellow]⚠ {len(outdated)} translation(s) need updating[/yellow]")


def _translation_missing(tracker, project, args):
    """Show missing translations."""
    target_lang = args.lang or "no"  # Default to Norwegian

    missing = tracker.get_missing_translations(target_lang)

    if args.json:
        output = [
            {
                "title": doc.title,
                "path": str(doc.path),
            }
            for doc in missing
        ]
        print(json.dumps(output, indent=2))
        return

    if not missing:
        console.print(f"[green]✓ All source documents have {target_lang} translations[/green]")
        return

    console.print(f"\n[bold]Missing Translations ({target_lang})[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Source Document", style="cyan")
    table.add_column("Version")

    for doc in missing:
        table.add_row(doc.title, doc.version)

    console.print(table)
    console.print(f"\n[yellow]⚠ {len(missing)} document(s) need translation to {target_lang}[/yellow]")


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


def cmd_dashboard(args):
    """Launch web dashboard."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    try:
        from .web import run_dashboard
    except ImportError:
        console.print("[red]Web dependencies not installed.[/red]")
        console.print("Install with: [cyan]pip install media-engine[web][/cyan]")
        sys.exit(1)

    console.print(f"[bold]Launching dashboard for {project.config.name}[/bold]")
    console.print(f"  URL: [cyan]http://{args.host}:{args.port}[/cyan]")

    run_dashboard(
        project_path=project.root,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )


def cmd_provenance(args):
    """Provenance and approval tracking."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .provenance import ProvenanceTracker

    tracker = ProvenanceTracker(project)

    if args.provenance_command == "report":
        report = tracker.generate_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            console.print("[bold]Provenance Report[/bold]")
            console.print(f"  Documents tracked: {report['summary']['total_documents']}")
            console.print(f"  Total claims: {report['summary']['total_claims']}")
            console.print(f"  Verified: {report['summary']['verified_claims']}")
            console.print(f"  Unverified: {report['summary']['unverified_claims']}")
            console.print(f"  Expired: {report['summary']['expired_claims']}")
            console.print(f"  Expiring soon: {report['summary']['expiring_soon']}")
            console.print("\n[bold]By Status:[/bold]")
            for status, count in report['by_status'].items():
                console.print(f"  {status}: {count}")

    elif args.provenance_command == "claims":
        unverified = tracker.get_all_unverified()
        expired = tracker.get_all_expired()
        expiring = tracker.get_expiring_soon()

        if args.json:
            print(json.dumps({
                "unverified": [(str(p), c.to_dict()) for p, c in unverified],
                "expired": [(str(p), c.to_dict()) for p, c in expired],
                "expiring_soon": [(str(p), c.to_dict()) for p, c in expiring],
            }, indent=2))
        else:
            if unverified:
                console.print(f"[bold yellow]Unverified Claims ({len(unverified)}):[/bold yellow]")
                for path, claim in unverified[:10]:
                    console.print(f"  {path.name}: {claim.text[:50]}...")
            if expired:
                console.print(f"[bold red]Expired Claims ({len(expired)}):[/bold red]")
                for path, claim in expired[:10]:
                    console.print(f"  {path.name}: {claim.text[:50]}...")
            if expiring:
                console.print(f"[bold yellow]Expiring Soon ({len(expiring)}):[/bold yellow]")
                for path, claim in expiring[:10]:
                    days = claim.days_until_expiry()
                    console.print(f"  {path.name}: {claim.text[:50]}... ({days}d)")

    elif args.provenance_command == "queue":
        queue = tracker.get_review_queue()
        if args.json:
            print(json.dumps([str(p) for p in queue], indent=2))
        else:
            console.print(f"[bold]Review Queue ({len(queue)} documents):[/bold]")
            for doc_path in queue:
                console.print(f"  {doc_path.name}")

    else:
        console.print("[yellow]Usage: media-engine provenance <report|claims|queue>[/yellow]")


def cmd_integrity(args):
    """Asset and terminology integrity."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .integrity import AssetIntegrityChecker, TerminologyChecker

    if args.integrity_command == "verify":
        checker = AssetIntegrityChecker(project)
        results = checker.verify_all()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            console.print("[bold]Asset Integrity Check[/bold]")
            console.print(f"  Valid: {len(results['valid'])}")
            console.print(f"  Modified: {len(results['modified'])}")
            console.print(f"  Missing: {len(results['missing'])}")
            console.print(f"  Untracked: {len(results['untracked'])}")

            if results['modified']:
                console.print("\n[bold red]Modified assets:[/bold red]")
                for item in results['modified']:
                    console.print(f"  {item['path']}")

    elif args.integrity_command == "record":
        checker = AssetIntegrityChecker(project)
        count = checker.record_all()
        console.print(f"[green]Recorded checksums for {count} assets[/green]")

    elif args.integrity_command == "terms":
        checker = TerminologyChecker(project)
        issues = checker.check_all_documents()

        if args.json:
            print(json.dumps(issues, indent=2))
        else:
            total = sum(len(i) for i in issues.values())
            console.print(f"[bold]Terminology Check ({total} issues):[/bold]")
            for doc_path, doc_issues in issues.items():
                console.print(f"\n  {Path(doc_path).name}:")
                for issue in doc_issues[:3]:
                    console.print(f"    Avoid '{issue['found']}', prefer '{issue['preferred']}'")

    else:
        console.print("[yellow]Usage: media-engine integrity <verify|record|terms>[/yellow]")


def cmd_readability(args):
    """Readability analysis."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .readability import check_readability, ReadabilityLevel

    target = ReadabilityLevel(args.target) if args.target else ReadabilityLevel.HIGH_SCHOOL
    report = check_readability(project, target_level=target)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print("[bold]Readability Analysis[/bold]")
        console.print(f"  Target level: {report['target_level']}")
        console.print(f"  Documents: {s['total_documents']}")
        console.print(f"  Passing: {s['passing']} ({s['pass_rate']}%)")
        console.print(f"  Average grade level: {s['average_grade_level']}")
        console.print(f"  Total reading time: {s['total_reading_time_minutes']:.1f} min")

        if s['failing'] > 0:
            console.print(f"\n[yellow]Documents above target level:[/yellow]")
            for doc in report['documents']:
                if not doc['passes_target']:
                    console.print(f"  {doc['file']}: grade {doc['grade_level']}")


def cmd_gaps(args):
    """Content gap analysis."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .gaps import analyze_gaps

    topics = args.topics.split(",") if args.topics else []
    report = analyze_gaps(project, expected_topics=topics)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print("[bold]Content Gap Analysis[/bold]")
        console.print(f"  Total gaps found: {s['total_gaps']}")
        console.print(f"  Critical: {s['critical']}")
        console.print(f"  High: {s['high']}")
        console.print(f"  Medium: {s['medium']}")
        console.print(f"  Low: {s['low']}")

        if s['total_gaps'] > 0:
            console.print("\n[bold]By Type:[/bold]")
            for gap_type, gaps in report['by_type'].items():
                console.print(f"  {gap_type}: {len(gaps)}")


def cmd_links(args):
    """Link validation."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .links import check_links

    console.print("[bold]Checking links...[/bold]")
    report = check_links(project, include_external=not args.internal_only)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print(f"  Total links: {s['total']}")
        console.print(f"  Valid: {s['valid']}")
        console.print(f"  [red]Broken: {s['broken']}[/red]")
        console.print(f"  [yellow]Timeout: {s['timeout']}[/yellow]")

        if report['broken_links']:
            console.print("\n[bold red]Broken Links:[/bold red]")
            for link in report['broken_links'][:10]:
                console.print(f"  {link['url']}")
                if link['file']:
                    console.print(f"    in {link['file']}:{link['line']}")


def cmd_security(args):
    """Security scan for sensitive content."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .security import SensitiveContentScanner

    scanner = SensitiveContentScanner()
    report = scanner.scan_project(project, include_assets=args.include_assets)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print("[bold]Security Scan[/bold]")
        console.print(f"  Total findings: {s['total']}")
        console.print(f"  [red]Critical: {s['critical']}[/red]")
        console.print(f"  [yellow]High: {s['high']}[/yellow]")
        console.print(f"  Medium: {s['medium']}")
        console.print(f"  Low: {s['low']}")

        if s['blocks_publish']:
            console.print("\n[bold red]⚠ CRITICAL ISSUES FOUND - Publishing blocked[/bold red]")

        if report['matches']:
            console.print("\n[bold]Findings:[/bold]")
            for match in report['matches'][:10]:
                level_color = {"critical": "red", "high": "yellow"}.get(match['level'], "white")
                console.print(f"  [{level_color}]{match['pattern']}[/{level_color}]: {match['redacted']}")
                if match['file']:
                    console.print(f"    in {match['file']}:{match['line']}")


def cmd_changelog(args):
    """Generate changelog."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .changelog import generate_changelog
    from datetime import datetime, timedelta

    since = None
    if args.since:
        since = datetime.fromisoformat(args.since)
    elif args.days:
        since = datetime.now() - timedelta(days=args.days)

    fmt = "json" if args.json else "markdown"
    changelog = generate_changelog(project, since=since, format=fmt)

    if args.output:
        Path(args.output).write_text(changelog)
        console.print(f"[green]Changelog written to {args.output}[/green]")
    else:
        print(changelog)


def cmd_demos(args):
    """Build interactive demos."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from .demos import DemoBuilder, DemoLoader

    builder = DemoBuilder(project)
    loader = DemoLoader(project)

    if args.demos_command == "list":
        demos = loader.list_demos()
        if args.json:
            print(json.dumps([str(d) for d in demos], indent=2))
        else:
            console.print(f"[bold]Interactive Demos ({len(demos)}):[/bold]")
            for demo in demos:
                console.print(f"  {demo.relative_to(project.content_dir)}")

    elif args.demos_command == "build":
        output_dir = Path(args.output) if args.output else None
        generated = builder.build_all_demos(output_dir)
        if args.json:
            print(json.dumps([str(g) for g in generated], indent=2))
        else:
            console.print(f"[green]Built {len(generated)} demos[/green]")
            for g in generated:
                console.print(f"  {g}")

    else:
        console.print("[yellow]Usage: media-engine demos <list|build>[/yellow]")


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

    # search
    search_parser = subparsers.add_parser("search", help="Search project documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    search_parser.add_argument("--rebuild", action="store_true", help="Rebuild index")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate project content")
    validate_parser.add_argument("--schema", help="Path to custom schema file")
    validate_parser.add_argument("--refs-only", action="store_true", help="Only check references")
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # pack
    pack_parser = subparsers.add_parser("pack", help="Generate curated packs")
    pack_parser.add_argument("type", choices=["investor", "pilot"], help="Pack type")
    pack_parser.add_argument("--output", "-o", help="Output directory")
    pack_parser.add_argument("--no-zip", action="store_true", help="Don't create ZIP archive")

    # index
    index_parser = subparsers.add_parser("index", help="Build search index")
    index_parser.add_argument("--output", "-o", help="Output path for index file")

    # translation
    trans_parser = subparsers.add_parser("translation", help="Translation tracking")
    trans_subparsers = trans_parser.add_subparsers(dest="translation_command")

    trans_status = trans_subparsers.add_parser("status", help="Show translation status")
    trans_status.add_argument("--json", action="store_true", help="Output as JSON")

    trans_outdated = trans_subparsers.add_parser("outdated", help="Show outdated translations")
    trans_outdated.add_argument("--json", action="store_true", help="Output as JSON")

    trans_missing = trans_subparsers.add_parser("missing", help="Show missing translations")
    trans_missing.add_argument("--lang", help="Target language (default: no)")
    trans_missing.add_argument("--json", action="store_true", help="Output as JSON")

    # dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Launch web dashboard")
    dash_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dash_parser.add_argument("--port", "-p", type=int, default=8080, help="Port to bind to")
    dash_parser.add_argument("--no-browser", action="store_true", help="Don't open browser")

    # provenance
    prov_parser = subparsers.add_parser("provenance", help="Provenance and approval tracking")
    prov_subparsers = prov_parser.add_subparsers(dest="provenance_command")

    prov_report = prov_subparsers.add_parser("report", help="Generate provenance report")
    prov_report.add_argument("--json", action="store_true", help="Output as JSON")

    prov_claims = prov_subparsers.add_parser("claims", help="List claims needing verification")
    prov_claims.add_argument("--json", action="store_true", help="Output as JSON")

    prov_queue = prov_subparsers.add_parser("queue", help="Show review queue")
    prov_queue.add_argument("--json", action="store_true", help="Output as JSON")

    # integrity
    integ_parser = subparsers.add_parser("integrity", help="Asset and terminology integrity")
    integ_subparsers = integ_parser.add_subparsers(dest="integrity_command")

    integ_verify = integ_subparsers.add_parser("verify", help="Verify asset checksums")
    integ_verify.add_argument("--json", action="store_true", help="Output as JSON")

    integ_record = integ_subparsers.add_parser("record", help="Record asset checksums")

    integ_terms = integ_subparsers.add_parser("terms", help="Check terminology consistency")
    integ_terms.add_argument("--json", action="store_true", help="Output as JSON")

    # readability
    read_parser = subparsers.add_parser("readability", help="Readability analysis")
    read_parser.add_argument("--target", choices=["elementary", "middle_school", "high_school", "college", "graduate", "technical"],
                             help="Target reading level")
    read_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # gaps
    gaps_parser = subparsers.add_parser("gaps", help="Content gap analysis")
    gaps_parser.add_argument("--topics", help="Expected topics (comma-separated)")
    gaps_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # links
    links_parser = subparsers.add_parser("links", help="Link validation")
    links_parser.add_argument("--internal-only", action="store_true", help="Only check internal links")
    links_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # security
    sec_parser = subparsers.add_parser("security", help="Security scan for sensitive content")
    sec_parser.add_argument("--include-assets", action="store_true", help="Also scan YAML/JSON assets")
    sec_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # changelog
    change_parser = subparsers.add_parser("changelog", help="Generate changelog")
    change_parser.add_argument("--since", help="Start date (ISO format)")
    change_parser.add_argument("--days", type=int, help="Include last N days")
    change_parser.add_argument("--output", "-o", help="Output file")
    change_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # demos
    demos_parser = subparsers.add_parser("demos", help="Interactive HTML demos")
    demos_subparsers = demos_parser.add_subparsers(dest="demos_command")

    demos_list = demos_subparsers.add_parser("list", help="List available demos")
    demos_list.add_argument("--json", action="store_true", help="Output as JSON")

    demos_build = demos_subparsers.add_parser("build", help="Build demos to HTML")
    demos_build.add_argument("--output", "-o", help="Output directory")
    demos_build.add_argument("--json", action="store_true", help="Output as JSON")

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
        "search": cmd_search,
        "validate": cmd_validate,
        "pack": cmd_pack,
        "index": cmd_index,
        "translation": cmd_translation,
        "dashboard": cmd_dashboard,
        "provenance": cmd_provenance,
        "integrity": cmd_integrity,
        "readability": cmd_readability,
        "gaps": cmd_gaps,
        "links": cmd_links,
        "security": cmd_security,
        "changelog": cmd_changelog,
        "demos": cmd_demos,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
