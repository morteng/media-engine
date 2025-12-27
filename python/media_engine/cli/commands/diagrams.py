"""Diagrams command - manage and build diagrams."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ...core import find_project
from ...diagrams import (
    DiagramDefinition,
    DiagramGenerator,
    build_diagrams,
    get_available_engines,
    get_installed_engines,
)

console = Console()


def cmd_diagrams(args):
    """Diagram management command."""
    if args.diagrams_command == "build":
        _build_diagrams(args)
    elif args.diagrams_command == "list":
        _list_diagrams(args)
    elif args.diagrams_command == "engines":
        _list_engines(args)
    elif args.diagrams_command == "preview":
        _preview_diagram(args)
    elif args.diagrams_command == "info":
        _diagram_info(args)
    else:
        console.print("[yellow]Use: diagrams build|list|engines|preview|info[/yellow]")


def _build_diagrams(args):
    """Build diagrams for the project."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    languages = args.lang.split(",") if args.lang else [project.source_language]

    console.print(f"[bold]Building diagrams for {project.config.name}[/bold]")

    # Engine override
    engine = args.engine
    if engine:
        # Validate engine exists
        available = [e.name for e in get_available_engines()]
        if engine not in available:
            console.print(f"[red]Engine '{engine}' not found[/red]")
            console.print(f"[dim]Available: {', '.join(available)}[/dim]")
            sys.exit(1)

        # Check if installed
        installed = [e.name for e in get_installed_engines()]
        if engine not in installed:
            console.print(f"[yellow]Warning: Engine '{engine}' is not installed[/yellow]")

    results = {"built": [], "failed": []}

    for lang in languages:
        console.print(f"\n[cyan]Language: {lang}[/cyan]")

        try:
            paths = build_diagrams(
                project,
                language=lang,
                engine_override=engine,
                dark_mode=args.dark,
                output_dir=Path(args.output) if args.output else None,
            )

            for path in paths:
                console.print(f"  [green]✓[/green] {path.name}")
                results["built"].append(str(path))

            if not paths:
                console.print("  [dim]No diagrams found[/dim]")

        except Exception as e:
            console.print(f"  [red]✗ Error: {e}[/red]")
            results["failed"].append({"lang": lang, "error": str(e)})

    # Summary
    console.print()
    console.print(
        f"[bold]Built: {len(results['built'])}, Failed: {len(results['failed'])}[/bold]"
    )

    if args.json:
        print(json.dumps(results, indent=2))


def _list_diagrams(args):
    """List all diagrams in the project."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    languages = args.lang.split(",") if args.lang else list(project.languages.keys())

    diagrams = []
    for lang in languages:
        diagrams_dir = project.get_content_path(lang, "diagrams")
        if diagrams_dir.exists():
            for path in sorted(diagrams_dir.glob("*.yaml")):
                try:
                    definition = DiagramDefinition.from_yaml(path)
                    diagrams.append({
                        "path": str(path.relative_to(project.root)),
                        "language": lang,
                        "title": definition.title or path.stem,
                        "engine": definition.config.engine.value,
                        "format": definition.config.format,
                        "boxes": len(definition.boxes),
                        "arrows": len(definition.arrows),
                    })
                except Exception as e:
                    diagrams.append({
                        "path": str(path.relative_to(project.root)),
                        "language": lang,
                        "error": str(e),
                    })

    if args.json:
        print(json.dumps(diagrams, indent=2))
        return

    if not diagrams:
        console.print("[dim]No diagrams found[/dim]")
        return

    table = Table(title="Diagrams")
    table.add_column("Path", style="cyan")
    table.add_column("Title")
    table.add_column("Engine", style="yellow")
    table.add_column("Format")
    table.add_column("Elements", justify="right")

    for d in diagrams:
        if "error" in d:
            table.add_row(d["path"], f"[red]{d['error']}[/red]", "", "", "")
        else:
            elements = f"{d['boxes']} boxes, {d['arrows']} arrows"
            table.add_row(d["path"], d["title"], d["engine"], d["format"], elements)

    console.print(table)


def _list_engines(args):
    """List available diagram engines."""
    engines = get_available_engines()

    if args.json:
        data = [
            {
                "name": e.name,
                "version": e.version,
                "installed": e.installed,
                "formats": e.formats,
                "capabilities": [c.value for c in e.capabilities],
                "description": e.description,
            }
            for e in engines
        ]
        print(json.dumps(data, indent=2))
        return

    console.print("[bold]Diagram Engines[/bold]\n")

    for engine in engines:
        status = "[green]✓ installed[/green]" if engine.installed else "[red]✗ not installed[/red]"
        console.print(f"[bold cyan]{engine.name}[/bold cyan] {status}")
        console.print(f"  {engine.description}")
        console.print(f"  [dim]Formats:[/dim] {', '.join(engine.formats)}")

        caps = [c.value for c in engine.capabilities]
        if caps:
            console.print(f"  [dim]Capabilities:[/dim] {', '.join(caps)}")

        if not engine.installed:
            # Get install hint
            from ...diagrams.engines import get_engine
            engine_class = get_engine(engine.name)
            if engine_class:
                hint = engine_class.get_install_hint()
                console.print(f"  [yellow]Install:[/yellow] {hint}")

        console.print()


def _preview_diagram(args):
    """Preview a diagram definition."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    diagram_path = Path(args.file)
    if not diagram_path.is_absolute():
        diagram_path = project.root / diagram_path

    if not diagram_path.exists():
        console.print(f"[red]File not found: {diagram_path}[/red]")
        sys.exit(1)

    try:
        definition = DiagramDefinition.from_yaml(diagram_path)
    except Exception as e:
        console.print(f"[red]Error parsing diagram: {e}[/red]")
        sys.exit(1)

    if args.render:
        # Render to file
        output_dir = Path(args.output) if args.output else project.output_dir / "diagrams"
        output_dir.mkdir(parents=True, exist_ok=True)

        engine = args.engine or definition.config.engine.value

        generator = DiagramGenerator(
            brand=getattr(project, "brand_context", None),
            theme=getattr(project, "theme", None),
            engine=engine,
        )

        if args.dark:
            definition.config.dark_mode = True
            output_path = output_dir / f"{diagram_path.stem}_dark.{definition.config.format}"
        else:
            output_path = output_dir / f"{diagram_path.stem}.{definition.config.format}"

        result = generator.generate(definition, output_path, engine=engine)
        console.print(f"[green]Rendered:[/green] {result}")

        if args.open:
            import subprocess
            subprocess.run(["open", str(result)])
    else:
        # Just show info
        _show_diagram_info(definition, diagram_path)


def _diagram_info(args):
    """Show info about a diagram file."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    diagram_path = Path(args.file)
    if not diagram_path.is_absolute():
        diagram_path = project.root / diagram_path

    if not diagram_path.exists():
        console.print(f"[red]File not found: {diagram_path}[/red]")
        sys.exit(1)

    try:
        definition = DiagramDefinition.from_yaml(diagram_path)
    except Exception as e:
        console.print(f"[red]Error parsing diagram: {e}[/red]")
        sys.exit(1)

    if args.json:
        data = {
            "path": str(diagram_path),
            "title": definition.title,
            "config": {
                "engine": definition.config.engine.value,
                "format": definition.config.format,
                "width": definition.config.width,
                "height": definition.config.height,
                "dark_mode": definition.config.dark_mode,
            },
            "boxes": [
                {"id": b.id, "label": b.label, "style": b.style}
                for b in definition.boxes
            ],
            "arrows": [
                {"from": a.from_id, "to": a.to_id, "label": a.label}
                for a in definition.arrows
            ],
            "layers": [{"id": l.id, "label": l.label} for l in definition.layers],
            "groups": [{"id": g.id, "label": g.label} for g in definition.groups],
            "suggested_engine": definition.get_suggested_engine().value,
        }
        print(json.dumps(data, indent=2))
    else:
        _show_diagram_info(definition, diagram_path)


def _show_diagram_info(definition: DiagramDefinition, path: Path):
    """Display diagram information."""
    console.print(f"[bold]Diagram:[/bold] {path.name}")
    if definition.title:
        console.print(f"[bold]Title:[/bold] {definition.title}")

    console.print()
    console.print("[bold]Configuration[/bold]")
    console.print(f"  Engine: {definition.config.engine.value}")
    console.print(f"  Format: {definition.config.format}")
    console.print(f"  Size: {definition.config.width} x {definition.config.height}")
    console.print(f"  DPI: {definition.config.dpi}")
    console.print(f"  Suggested engine: {definition.get_suggested_engine().value}")

    if definition.config.engine_options:
        console.print(f"  Options: {definition.config.engine_options}")

    console.print()
    console.print("[bold]Elements[/bold]")
    console.print(f"  Boxes: {len(definition.boxes)}")
    for box in definition.boxes[:5]:
        console.print(f"    - {box.id}: {box.label} ({box.style})")
    if len(definition.boxes) > 5:
        console.print(f"    ... and {len(definition.boxes) - 5} more")

    console.print(f"  Arrows: {len(definition.arrows)}")
    for arrow in definition.arrows[:5]:
        label = f" ({arrow.label})" if arrow.label else ""
        console.print(f"    - {arrow.from_id} → {arrow.to_id}{label}")
    if len(definition.arrows) > 5:
        console.print(f"    ... and {len(definition.arrows) - 5} more")

    if definition.layers:
        console.print(f"  Layers: {len(definition.layers)}")
        for layer in definition.layers:
            console.print(f"    - {layer.id}: {layer.label or '(no label)'}")

    if definition.groups:
        console.print(f"  Groups: {len(definition.groups)}")
        for group in definition.groups:
            console.print(f"    - {group.id}: {group.label or '(no label)'}")
