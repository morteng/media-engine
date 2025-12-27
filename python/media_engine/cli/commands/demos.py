"""Demos command - build interactive demos and capture video clips."""

import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_demos(args):
    """Build interactive demos and capture video clips."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    if args.demos_command == "list":
        from ...demos import DemoLoader

        loader = DemoLoader(project)
        demos = loader.list_demos()
        if args.json:
            print(json.dumps([str(d) for d in demos], indent=2))
        else:
            console.print(f"[bold]Interactive Demos ({len(demos)}):[/bold]")
            for demo in demos:
                console.print(f"  {demo.relative_to(project.content_dir)}")

    elif args.demos_command == "build":
        from ...demos import DemoBuilder

        builder = DemoBuilder(project)
        output_dir = Path(args.output) if args.output else None
        generated = builder.build_all_demos(output_dir)
        if args.json:
            print(json.dumps([str(g) for g in generated], indent=2))
        else:
            console.print(f"[green]Built {len(generated)} demos[/green]")
            for g in generated:
                console.print(f"  {g}")

    elif args.demos_command == "capture":
        # Capture demo video clips for video production
        _cmd_capture(args, project)

    elif args.demos_command == "definitions":
        # List demo definitions (YAML files)
        _cmd_definitions(args, project)

    else:
        console.print("[yellow]Usage: media-engine demos <list|build|capture|definitions>[/yellow]")


def _cmd_definitions(args, project):
    """List demo definition files."""
    demos_dir = project.content_dir / "demos"
    if not demos_dir.exists():
        console.print("[yellow]No demos/ directory found[/yellow]")
        return

    definitions = list(demos_dir.glob("*.yaml"))
    if not definitions:
        console.print("[yellow]No demo definitions found[/yellow]")
        return

    if args.json:
        print(json.dumps([str(d) for d in definitions], indent=2))
    else:
        console.print(f"[bold]Demo Definitions ({len(definitions)}):[/bold]")
        for d in definitions:
            # Parse and show basic info
            try:
                import yaml

                with open(d, "r") as f:
                    data = yaml.safe_load(f)
                name = data.get("name", d.stem)
                states = len(data.get("states", {}))
                sequences = len(data.get("sequences", {}))
                console.print(f"  [cyan]{d.name}[/cyan]: {name}")
                console.print(f"    States: {states}, Sequences: {sequences}")
            except Exception:
                console.print(f"  [yellow]{d.name}[/yellow] (parse error)")


def _cmd_capture(args, project):
    """Capture demo video clips using Playwright."""
    from ...video.demo_capture import (
        capture_all_states,
        capture_for_video_script,
        load_demo_definition,
    )

    # Determine demo definition path
    if args.definition:
        definition_path = Path(args.definition)
    else:
        # Default to first definition in demos/ directory
        demos_dir = project.content_dir / "demos"
        definitions = list(demos_dir.glob("*.yaml"))
        if not definitions:
            console.print("[red]No demo definition found. Specify with --definition[/red]")
            sys.exit(1)
        definition_path = definitions[0]
        console.print(f"[dim]Using definition: {definition_path.name}[/dim]")

    if not definition_path.exists():
        console.print(f"[red]Demo definition not found: {definition_path}[/red]")
        sys.exit(1)

    # Determine output directory
    output_dir = Path(args.output) if args.output else project.root / "remotion" / "public" / "demos"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load definition for preview
    definition = load_demo_definition(definition_path)
    console.print(f"[bold]Demo: {definition.name}[/bold]")
    console.print(f"  URL: {definition.url}")
    console.print(f"  Viewport: {definition.viewport_width}x{definition.viewport_height}")
    console.print(f"  States: {len(definition.states)}")
    console.print(f"  Output: {output_dir}")
    console.print()

    # Capture based on mode
    if args.script:
        # Capture states needed by video script
        script_path = Path(args.script)
        if not script_path.exists():
            console.print(f"[red]Script not found: {script_path}[/red]")
            sys.exit(1)

        console.print(f"[cyan]Capturing states for video script: {script_path.name}[/cyan]")
        results = asyncio.run(
            capture_for_video_script(
                script_path=script_path,
                definition_path=definition_path,
                output_dir=output_dir,
                fps=args.fps,
                headless=not args.no_headless,
            )
        )
    else:
        # Capture specified states or all
        states = args.states if args.states else None
        duration = args.duration

        if states:
            console.print(f"[cyan]Capturing {len(states)} states[/cyan]")
        else:
            console.print(f"[cyan]Capturing all {len(definition.states)} states[/cyan]")

        results = asyncio.run(
            capture_all_states(
                definition_path=definition_path,
                output_dir=output_dir,
                states=states,
                duration=duration,
                fps=args.fps,
                headless=not args.no_headless,
            )
        )

    # Report results
    if args.json:
        print(json.dumps({k: str(v) for k, v in results.items()}, indent=2))
    else:
        console.print()
        console.print(f"[green]Captured {len(results)} demo clips[/green]")
        for state_id, path in results.items():
            console.print(f"  [cyan]{state_id}[/cyan]: {path.name}")
