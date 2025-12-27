"""
CLI commands for publication management.

Publications are deliverables composed of source files that can be
rendered to multiple output formats (PDF, HTML, PPTX, etc.).
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def add_publications_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add publications subparser."""
    parser = subparsers.add_parser(
        "publications",
        help="Manage publications (deliverables)",
        description="Manage project publications - composite documents rendered to PDF, HTML, PPTX, etc.",
    )

    sub = parser.add_subparsers(dest="publications_cmd", help="Publications commands")

    # List publications
    list_parser = sub.add_parser("list", help="List all publications")
    list_parser.add_argument("--format", choices=["table", "json"], default="table")

    # Status
    status_parser = sub.add_parser("status", help="Show publication status")
    status_parser.add_argument("publication", nargs="?", help="Publication ID")

    # Build
    build_parser = sub.add_parser("build", help="Build a publication")
    build_parser.add_argument("publication", help="Publication ID")
    build_parser.add_argument("--format", "-f", help="Output format (pdf, html, pptx)")
    build_parser.add_argument("--language", "-l", default="en", help="Language")
    build_parser.add_argument("--output", "-o", help="Output directory")
    build_parser.add_argument("--all-formats", action="store_true", help="Build all formats")
    build_parser.add_argument("--all-languages", action="store_true", help="Build all languages")

    # Build all
    build_all_parser = sub.add_parser("build-all", help="Build all publications")
    build_all_parser.add_argument("--output", "-o", help="Output directory")

    # Components
    components_parser = sub.add_parser("components", help="List publication components")
    components_parser.add_argument("publication", help="Publication ID")

    # Stale
    sub.add_parser("stale", help="Show stale publications")


def cmd_publications(args: argparse.Namespace) -> int:
    """Handle publications commands."""
    from ... import find_project

    console = Console()
    project = find_project()

    if not project:
        console.print("[red]No project found[/red]")
        return 1

    cmd = getattr(args, "publications_cmd", None)

    if cmd == "list" or cmd is None:
        return _list_publications(project, args, console)
    elif cmd == "status":
        return _publication_status(project, args, console)
    elif cmd == "build":
        return _build_publication(project, args, console)
    elif cmd == "build-all":
        return _build_all_publications(project, args, console)
    elif cmd == "components":
        return _list_components(project, args, console)
    elif cmd == "stale":
        return _show_stale(project, args, console)
    else:
        console.print("[yellow]Use: publications list|status|build|build-all|components|stale[/yellow]")
        return 0


def _list_publications(project, args, console) -> int:
    """List all publications."""
    from ...publications import PublicationRegistry

    registry = PublicationRegistry(project)
    publications = registry.list()

    if not publications:
        console.print("[yellow]No publications defined[/yellow]")
        console.print("Add publications to project.yaml under the 'publications:' key")
        return 0

    table = Table(title="Publications")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Formats")
    table.add_column("Languages")
    table.add_column("Status")

    for pub in publications:
        stale = registry.get_stale_components(pub.id)
        status = "[green]Ready[/green]" if not stale else f"[yellow]{len(stale)} stale[/yellow]"

        table.add_row(
            pub.id,
            pub.title,
            pub.publication_type.value,
            ", ".join(f.value for f in pub.formats),
            ", ".join(pub.languages),
            status,
        )

    console.print(table)
    return 0


def _publication_status(project, args, console) -> int:
    """Show publication status."""
    from ...publications import PublicationRegistry, PublicationTracker

    registry = PublicationRegistry(project)
    tracker = PublicationTracker(project, registry)

    if args.publication:
        # Single publication status
        status = registry.get_publication_status(args.publication)
        if "error" in status:
            console.print(f"[red]{status['error']}[/red]")
            return 1

        console.print(Panel(f"[bold]{status['title']}[/bold]", title=status["id"]))
        console.print(f"  Type: {status['type']}")
        console.print(f"  Status: {status['status']}")
        console.print(f"  Components: {status['component_count']}")
        console.print(f"  Stale: {status['stale_component_count']}")

        if status['stale_components']:
            console.print("\n  [yellow]Stale components:[/yellow]")
            for comp in status['stale_components'][:10]:
                console.print(f"    - {comp}")

        console.print("\n  [bold]Build Status:[/bold]")
        for fmt, langs in status['build_status'].items():
            for lang, info in langs.items():
                status_str = "[green]Built[/green]" if info['status'] == 'complete' else f"[yellow]{info['status']}[/yellow]"
                console.print(f"    {fmt}/{lang}: {status_str}")
    else:
        # Overview of all publications
        overview = tracker.get_publication_overview()
        console.print(f"\n[bold]Publications Overview[/bold] ({overview['total']} total)\n")

        table = Table()
        table.add_column("Publication", style="cyan")
        table.add_column("Type")
        table.add_column("Components")
        table.add_column("Stale")
        table.add_column("Status")

        for pub in overview['publications']:
            status = "[green]Ready[/green]" if pub['stale_count'] == 0 else f"[yellow]{pub['stale_count']} stale[/yellow]"
            table.add_row(
                pub['title'],
                pub['type'],
                str(pub['component_count']),
                str(pub['stale_count']),
                status,
            )

        console.print(table)

    return 0


def _build_publication(project, args, console) -> int:
    """Build a publication."""
    from ...publications import OutputFormat, PublicationBuilder, PublicationRegistry

    registry = PublicationRegistry(project)
    pub = registry.get(args.publication)

    if not pub:
        console.print(f"[red]Publication not found: {args.publication}[/red]")
        return 1

    builder = PublicationBuilder(project, registry)
    output_dir = Path(args.output) if args.output else project.root / "dist"

    if args.all_formats and args.all_languages:
        # Build everything
        console.print(f"[bold]Building all formats and languages for {pub.title}...[/bold]")
        builds = builder.build_all(pub, output_dir)
        for build in builds:
            if build.status.value == "complete":
                console.print(f"  [green]Built[/green] {build.format.value}/{build.language}: {build.output_path}")
            else:
                console.print(f"  [red]Failed[/red] {build.format.value}/{build.language}: {build.error}")
    else:
        # Build specific format/language
        fmt = OutputFormat(args.format) if args.format else pub.formats[0]
        lang = args.language

        console.print(f"[bold]Building {pub.title} ({fmt.value}/{lang})...[/bold]")
        build = builder.build(pub, fmt, lang, output_dir)

        if build.status.value == "complete":
            console.print(f"[green]Built successfully:[/green] {build.output_path}")
        else:
            console.print(f"[red]Build failed:[/red] {build.error}")
            return 1

    return 0


def _build_all_publications(project, args, console) -> int:
    """Build all publications."""
    from ...publications import PublicationBuilder, PublicationRegistry

    registry = PublicationRegistry(project)
    publications = registry.list()

    if not publications:
        console.print("[yellow]No publications to build[/yellow]")
        return 0

    builder = PublicationBuilder(project, registry)
    output_dir = Path(args.output) if args.output else project.root / "dist"

    console.print(f"[bold]Building {len(publications)} publications...[/bold]\n")

    total_builds = 0
    failed_builds = 0

    for pub in publications:
        console.print(f"[cyan]{pub.title}[/cyan]")
        builds = builder.build_all(pub, output_dir)
        for build in builds:
            total_builds += 1
            if build.status.value == "complete":
                console.print(f"  [green]OK[/green] {build.format.value}/{build.language}")
            else:
                failed_builds += 1
                console.print(f"  [red]FAIL[/red] {build.format.value}/{build.language}: {build.error}")

    console.print(f"\n[bold]Summary:[/bold] {total_builds - failed_builds}/{total_builds} successful")

    return 1 if failed_builds > 0 else 0


def _list_components(project, args, console) -> int:
    """List publication components."""
    from ...publications import PublicationRegistry

    registry = PublicationRegistry(project)
    pub = registry.get(args.publication)

    if not pub:
        console.print(f"[red]Publication not found: {args.publication}[/red]")
        return 1

    console.print(f"\n[bold]{pub.title}[/bold] - Components\n")

    # Show parts
    if pub.parts:
        for part in pub.parts:
            console.print(f"[cyan]{part.title}[/cyan]")
            for comp in part.components:
                status = "[green]OK[/green]" if (project.root / comp.source).exists() else "[red]Missing[/red]"
                console.print(f"  {status} {comp.source}")

    # Show standalone components
    if pub.components:
        if pub.parts:
            console.print("\n[cyan]Other Components[/cyan]")
        for comp in pub.components:
            status = "[green]OK[/green]" if (project.root / comp.source).exists() else "[red]Missing[/red]"
            console.print(f"  {status} {comp.source}")

    return 0


def _show_stale(project, args, console) -> int:
    """Show stale publications."""
    from ...publications import PublicationRegistry, PublicationTracker

    registry = PublicationRegistry(project)
    tracker = PublicationTracker(project, registry)

    stale = tracker.get_stale_publications()

    if not stale:
        console.print("[green]All publications are up to date![/green]")
        return 0

    console.print(f"\n[yellow]{len(stale)} stale publications:[/yellow]\n")

    for pub in stale:
        console.print(f"[bold]{pub['title']}[/bold]")
        console.print(f"  Stale components: {pub['stale_count']}")
        for comp in pub['stale_components'][:5]:
            console.print(f"    - {comp}")
        if pub['stale_count'] > 5:
            console.print(f"    ... and {pub['stale_count'] - 5} more")
        console.print()

    return 0
