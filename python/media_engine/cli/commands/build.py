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
    console.print(
        f"Built: {len(results['built'])}, Skipped: {len(results['skipped'])}, Failed: {len(results['failed'])}"
    )

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


def _build_video(project: Project, lang: str, output_dir: Path) -> Path | None:
    """Build video from script definitions."""
    from ...video import VideoBuilder, VideoScript

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
                console.print(
                    f"    [yellow]{script_file.stem}: no voice_id configured (skipping voiceover)[/yellow]"
                )
                # Still export props for Remotion
                props_path = videos_output / f"{script_file.stem}.props.json"
                _export_video_props_only(script, props_path, project)
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


def _export_video_props_only(script, output_path: Path, project: Project):
    """Export Remotion props without generating voiceover."""
    import json

    fps = 30
    if project.config.video:
        fps = getattr(project.config.video, "fps", 30)

    props = {
        "title": script.title,
        "name": script.name,
        "language": script.language,
        "fps": fps,
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
