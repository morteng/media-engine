"""Pack command - generate curated packs for specific audiences."""

import sys
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_pack(args):
    """Generate curated packs for specific audiences."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...packs import generate_investor_pack, generate_pilot_pack

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
        console.print("[yellow]Pack generated with missing items[/yellow]")
        for item in result.items_missing:
            console.print(f"  [red]Missing: {item}[/red]")
        sys.exit(1)
