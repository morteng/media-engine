"""Publish command - publish complete deliverable package."""

import sys
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_publish(args):
    """Publish complete deliverable package."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...publish import PublishConfig, publish_project

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
