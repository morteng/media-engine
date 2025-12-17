"""Dashboard command - launch web dashboard."""

import sys

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_dashboard(args):
    """Launch web dashboard."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    try:
        from ...web import run_dashboard
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
