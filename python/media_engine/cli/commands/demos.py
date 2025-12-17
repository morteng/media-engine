"""Demos command - build interactive demos."""

import json
import sys
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_demos(args):
    """Build interactive demos."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...demos import DemoBuilder, DemoLoader

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
