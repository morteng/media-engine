"""Dependency tracking commands with hash-based change detection."""

import json
import sys

from rich import box
from rich.console import Console
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_deps(args):
    """Dependency tracking commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...dependencies import DependencyGraph, DependencyHashTracker

    graph = DependencyGraph(project)
    tracker = DependencyHashTracker(project)

    if args.deps_command == "status":
        _deps_status(tracker, args)
    elif args.deps_command == "stale":
        _deps_stale(tracker, args)
    elif args.deps_command == "sync":
        _deps_sync(graph, tracker, args)
    elif args.deps_command == "check":
        _deps_check(tracker, args)
    elif args.deps_command == "refresh":
        _deps_refresh(graph, tracker, args)
    else:
        console.print("[red]Unknown deps command[/red]")
        sys.exit(1)


def _deps_status(tracker, args):
    """Show dependency status for all documents."""
    statuses = tracker.get_all_statuses()

    if args.json:
        output = [
            {
                "path": str(s.path),
                "title": s.title,
                "total_dependencies": s.total_dependencies,
                "stale_dependencies": s.stale_dependencies,
                "is_stale": s.is_stale,
            }
            for s in statuses
        ]
        print(json.dumps(output, indent=2))
        return

    if not statuses:
        console.print("[dim]No dependencies tracked yet. Run `media-engine deps sync` first.[/dim]")
        return

    console.print("\n[bold]Dependency Status[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Document", style="cyan")
    table.add_column("Dependencies", justify="center")
    table.add_column("Stale", justify="center")
    table.add_column("Status", justify="center")

    for status in sorted(statuses, key=lambda s: s.stale_dependencies, reverse=True):
        status_color = "red" if status.is_stale else "green"
        status_text = status.status_label

        table.add_row(
            status.title[:40],
            str(status.total_dependencies),
            str(status.stale_dependencies) if status.stale_dependencies > 0 else "-",
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    stale_count = sum(1 for s in statuses if s.is_stale)
    if stale_count > 0:
        console.print(f"\n[yellow]⚠ {stale_count} document(s) have stale dependencies[/yellow]")
    else:
        console.print("\n[green]✓ All dependencies are current[/green]")


def _deps_stale(tracker, args):
    """Show only documents with stale dependencies."""
    stale = tracker.get_all_stale()

    if args.json:
        output = [
            {
                "path": str(s.path),
                "title": s.title,
                "stale_count": s.stale_dependencies,
                "stale_deps": [
                    {
                        "target": d.target_path,
                        "type": d.dep_type,
                        "old_hash": d.recorded_hash[:8],
                        "new_hash": d.current_hash[:8],
                    }
                    for d in s.dependencies
                    if d.is_stale
                ],
            }
            for s in stale
        ]
        print(json.dumps(output, indent=2))
        return

    if not stale:
        console.print("[green]✓ No stale dependencies[/green]")
        return

    console.print("\n[bold]Documents with Stale Dependencies[/bold]")
    console.print("[dim]These documents reference content that has changed[/dim]\n")

    for status in stale:
        console.print(f"[cyan]{status.title}[/cyan]")
        for dep in status.dependencies:
            if dep.is_stale:
                old_hash = dep.recorded_hash[:8] if dep.recorded_hash else "none"
                new_hash = dep.current_hash[:8] if dep.current_hash else "none"
                console.print(
                    f"  └─ [{dep.dep_type}] {dep.target_path}"
                )
                console.print(
                    f"     [dim]{old_hash} → {new_hash}[/dim]"
                )
        console.print()

    console.print(f"[yellow]⚠ {len(stale)} document(s) need review[/yellow]")


def _deps_sync(graph, tracker, args):
    """Sync dependency hashes from the dependency graph."""
    if args.refresh:
        console.print("[dim]Refreshing dependency graph...[/dim]")
        graph.refresh()

    if args.dry_run:
        report = graph.generate_report()
        console.print("\n[bold]Dry Run - Would sync:[/bold]")
        console.print(f"  Documents: {report['summary']['total_documents']}")
        console.print(f"  Dependencies: {report['summary']['total_dependencies']}")
        return

    console.print("[dim]Syncing dependency hashes...[/dim]")
    synced = tracker.sync_from_graph(graph)

    console.print(f"\n[green]✓ Synced {synced} dependency hashes[/green]")


def _deps_check(tracker, args):
    """Check a specific document's dependencies."""
    from pathlib import Path

    doc_path = Path(args.document).resolve()

    if not doc_path.exists():
        console.print(f"[red]Document not found: {args.document}[/red]")
        sys.exit(1)

    status = tracker.check_document(doc_path)

    if args.json:
        output = {
            "path": str(status.path),
            "title": status.title,
            "total_dependencies": status.total_dependencies,
            "stale_dependencies": status.stale_dependencies,
            "is_stale": status.is_stale,
            "dependencies": [
                {
                    "target": d.target_path,
                    "type": d.dep_type,
                    "recorded_hash": d.recorded_hash,
                    "current_hash": d.current_hash,
                    "is_stale": d.is_stale,
                }
                for d in status.dependencies
            ],
        }
        print(json.dumps(output, indent=2))
        return

    console.print(f"\n[bold]{status.title}[/bold]")
    console.print(f"[dim]{status.path}[/dim]\n")

    if not status.dependencies:
        console.print("[dim]No dependencies tracked for this document[/dim]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Dependency", style="cyan")
    table.add_column("Type")
    table.add_column("Recorded", justify="center")
    table.add_column("Current", justify="center")
    table.add_column("Status", justify="center")

    for dep in status.dependencies:
        status_color = "red" if dep.is_stale else "green"
        status_text = "stale" if dep.is_stale else "current"

        rec_hash = dep.recorded_hash[:8] if dep.recorded_hash else "-"
        cur_hash = dep.current_hash[:8] if dep.current_hash else "-"

        # Shorten the target path for display
        target_name = Path(dep.target_path).name

        table.add_row(
            target_name,
            dep.dep_type,
            rec_hash,
            cur_hash,
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    if status.is_stale:
        console.print(f"\n[yellow]⚠ {status.stale_dependencies} stale dependencies[/yellow]")
    else:
        console.print("\n[green]✓ All dependencies current[/green]")


def _deps_refresh(graph, tracker, args):
    """Refresh dependency graph and sync hashes."""
    console.print("[dim]Refreshing dependency graph...[/dim]")
    graph.refresh()

    report = graph.generate_report()
    console.print(f"  Found {report['summary']['total_documents']} documents")
    console.print(f"  Found {report['summary']['total_dependencies']} dependencies")

    if not args.no_sync:
        console.print("\n[dim]Syncing dependency hashes...[/dim]")
        synced = tracker.sync_from_graph(graph)
        console.print(f"  Synced {synced} hashes")

    console.print("\n[green]✓ Dependency graph refreshed[/green]")
