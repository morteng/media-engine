"""Build command - build media outputs."""

import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console

from ...cms import Document
from ...core import Project, find_project

console = Console()


def cmd_build(args):
    """Build media outputs."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    console.print(f"[bold]Building {project.config.name}[/bold]")

    # Check for provenance issues (unverified/expired claims)
    _check_provenance_warnings(project)

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
                output_path = _build_format(project, lang, fmt, deps, args)
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
    console.print(
        f"Built: {len(results['built'])}, Skipped: {len(results['skipped'])}, Failed: {len(results['failed'])}"
    )

    if args.json:
        print(json.dumps(results, indent=2))


def _build_format(project: Project, lang: str, fmt: str, deps: list[Path], args) -> Path | None:
    """Build a specific format. Returns output path or None if not implemented."""
    output_dir = project.output_dir / lang
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "html":
        return _build_html(project, lang, deps, output_dir)
    elif fmt == "pdf":
        return _build_pdf(project, lang, deps, output_dir)
    elif fmt == "pptx":
        return _build_pptx(project, lang, output_dir)
    elif fmt == "presentation":
        return _build_presentation_html(project, lang, output_dir)
    elif fmt == "xlsx":
        return _build_xlsx(project, lang, output_dir)
    elif fmt == "diagrams":
        return _build_diagrams(project, lang, output_dir)
    elif fmt == "video":
        return _build_video(project, lang, output_dir, args)
    elif fmt == "demos":
        return _build_demos(project, lang, output_dir)

    return None


def _build_html(project: Project, lang: str, deps: list[Path], output_dir: Path) -> Path:
    """Build HTML from markdown chapters."""
    from ...builders.html import HTMLBuilder, HTMLConfig

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
    from ...builders.pptx import PPTXBuilder

    # Look for slides definition
    slides_yaml = project.get_content_path(lang, "slides", "pitch_deck.yaml")
    slides_md = project.get_content_path(lang, "slides", "pitch_deck.md")

    # Look for logo (check brand folder first, then assets)
    logo_path = None
    brand_logo_paths = [
        project.root / "docs" / "brand" / "logo" / "pikkolo-hub-full-light.svg",
        project.root / "docs" / "brand" / "logo" / "logo.svg",
        project.root / "docs" / "brand" / "logo" / "logo.png",
        project.root / "assets" / "logo.svg",
        project.root / "assets" / "logo.png",
    ]
    for path in brand_logo_paths:
        if path.exists():
            logo_path = path
            break

    builder = PPTXBuilder(theme=project.theme, logo_path=logo_path)

    if slides_yaml.exists():
        builder.build_from_yaml(slides_yaml)
    elif slides_md.exists():
        builder.build_from_markdown(slides_md)
    else:
        # No slides definition found
        return None

    output_path = output_dir / "pitch_deck.pptx"
    return builder.save(output_path)


def _build_presentation_html(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build HTML presentation from slides definition."""
    from ...templates.html_presentation import (
        PresentationTemplate,
        build_presentation_from_yaml,
    )

    # Look for slides definition
    slides_yaml = project.get_content_path(lang, "slides", "pitch_deck.yaml")

    if not slides_yaml.exists():
        return None

    # Parse slides from YAML
    title, slides = build_presentation_from_yaml(slides_yaml, project.theme)

    # Find logo paths
    logo_path = None
    logo_path_light = None
    shared_dir = (
        project.output_dir.parent / "shared" if project.output_dir.parent.exists() else None
    )

    # Check for logo in shared directory (relative path for HTML)
    if shared_dir and (shared_dir / "logo.svg").exists():
        logo_path = "../../shared/logo.svg"
        logo_path_light = "../../shared/logo-light.svg"
    elif shared_dir and (shared_dir / "logo.png").exists():
        logo_path = "../../shared/logo.png"
        logo_path_light = "../../shared/logo-light.png"

    # Render HTML presentation
    template = PresentationTemplate(theme=project.theme)
    html = template.render(
        title=title,
        slides=slides,
        logo_path=logo_path,
        logo_path_light=logo_path_light,
        fonts_css_path="../../shared/fonts.css",
        lang=lang,
    )

    # Save to presentations subdirectory
    presentations_dir = output_dir / "presentations"
    presentations_dir.mkdir(parents=True, exist_ok=True)
    output_path = presentations_dir / "pitch_deck.html"
    output_path.write_text(html)

    console.print(f"    [dim]Generated {output_path.name}[/dim]")
    return output_path


def _build_demos(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build interactive demos from YAML definitions."""
    from ...demos import DemoBuilder

    demos_dir = project.get_content_path(lang, "demos")
    if not demos_dir.exists():
        return None

    demo_files = list(demos_dir.glob("*.yaml"))
    if not demo_files:
        return None

    demos_output = output_dir / "demos"
    demos_output.mkdir(parents=True, exist_ok=True)

    generated = []
    for demo_file in demo_files:
        try:
            builder = DemoBuilder(theme=project.theme)
            html = builder.build_from_yaml(demo_file)

            output_path = demos_output / f"{demo_file.stem}.html"
            output_path.write_text(html)
            generated.append(output_path)
            console.print(f"    [dim]Generated {demo_file.stem}.html[/dim]")

        except Exception as e:
            console.print(f"    [red]{demo_file.stem}: {e}[/red]")

    return demos_output if generated else None


def _build_xlsx(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build Excel spreadsheet from data definition."""
    from ...builders.xlsx import XLSXBuilder

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
    from ...diagrams import DiagramDefinition, DiagramGenerator

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


def _build_video(project: Project, lang: str, output_dir: Path, args) -> Path | None:
    """Build video from script definitions."""
    from ...video import VideoBuilder, VideoConfig, VideoQuality, VideoScript

    scripts_dir = project.get_content_path(lang, "scripts")
    if not scripts_dir.exists():
        return None

    script_files = list(scripts_dir.glob("*.yaml"))
    if not script_files:
        return None

    # Create config based on quality setting
    quality_str = getattr(args, "quality", "production")
    quality = VideoQuality(quality_str)
    config = VideoConfig.from_quality(quality)

    # Show quality info
    if quality == VideoQuality.PREVIEW:
        console.print(
            f"    [yellow]Preview mode: {config.width}x{config.height} @ {config.fps}fps[/yellow]"
        )

    builder = VideoBuilder(project=project, config=config)
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
                console.print(
                    f"    [yellow]{script_file.stem}: no voice_id configured (skipping voiceover)[/yellow]"
                )
                # Still export props for Remotion
                props_path = videos_output / f"{script_file.stem}.props.json"
                _export_video_props_only(script, props_path, project, config)
                generated.append(props_path)
                console.print(f"    [dim]Exported {script_file.stem}.props.json[/dim]")
                continue

            # Build with voiceover
            result = asyncio.run(
                builder.build(
                    script_path=script_file,
                    output_dir=videos_output,
                    render=False,  # Don't render, just generate assets
                )
            )

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


def _export_video_props_only(script, output_path: Path, project: Project, config=None):
    """Export Remotion props without generating voiceover."""
    import json

    from ...video import VideoConfig

    # Use provided config or create default
    if config is None:
        config = VideoConfig()

    props = {
        "title": script.title,
        "name": script.name,
        "language": script.language,
        "fps": config.fps,
        "quality": config.quality.value,
        "is_releasable": config.is_releasable,
        "resolution": {
            "width": config.width,
            "height": config.height,
        },
        "scenes": [],
    }

    for scene in script.scenes:
        props["scenes"].append(
            {
                "id": scene.id,
                "type": scene.type,
                "title": scene.title,
                "text": scene.text,
                "visual": scene.visual,
            }
        )

    output_path.write_text(json.dumps(props, indent=2))


def _check_provenance_warnings(project: Project) -> None:
    """Check for provenance issues and display warnings."""
    try:
        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(project)
        issues = tracker.get_documents_with_claim_issues()

        if not issues:
            return

        # Count issues by type
        unverified_count = 0
        expired_count = 0
        expiring_count = 0
        affected_docs = set()

        for path, issue_type, count in issues:
            affected_docs.add(str(path))
            if issue_type == "unverified_claims":
                unverified_count += count
            elif issue_type == "expired_claims":
                expired_count += count
            elif issue_type == "expiring_claims":
                expiring_count += count

        # Show warnings
        console.print()
        console.print("[yellow bold]Provenance Warnings:[/yellow bold]")

        if unverified_count > 0:
            console.print(
                f"  [yellow]! {unverified_count} unverified claim(s) in {len(affected_docs)} document(s)[/yellow]"
            )

        if expired_count > 0:
            console.print(f"  [red]! {expired_count} expired claim(s) need re-verification[/red]")

        if expiring_count > 0:
            console.print(f"  [dim]! {expiring_count} claim(s) expiring within 30 days[/dim]")

        console.print()
        console.print("  Run [bold]media-engine provenance report[/bold] for details")
        console.print()

    except Exception:
        # Provenance module not available or failed - silently continue
        pass
