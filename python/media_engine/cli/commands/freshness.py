"""Freshness commands - content freshness tracking and reporting."""

import json
import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...core import find_project
from ...freshness import ContentRegistry, FreshnessStatus, scan_project

console = Console()


def cmd_freshness(args):
    """Run freshness checks and report on content status."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    # Initialize registry
    registry = ContentRegistry(project)
    registry.load()

    # Scan and register content if --scan or registry is empty
    if args.scan or not registry.items:
        console.print("[bold]Scanning project content...[/bold]")
        count = scan_project(project, registry)
        console.print(f"  Registered {count} items")

    # Refresh freshness status
    report = registry.refresh()

    # Save updated registry
    registry.save()

    # Output based on format
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Filter by type if specified
    if args.type:
        from ...freshness import ContentType

        try:
            filter_type = ContentType(args.type)
            report.stale_items = [i for i in report.stale_items if i.content_type == filter_type]
            report.expired_items = [i for i in report.expired_items if i.content_type == filter_type]
        except ValueError:
            console.print(f"[red]Unknown content type: {args.type}[/red]")
            sys.exit(1)

    # Summary panel
    summary_text = f"""[bold]Total items:[/bold] {report.total_items}
[green]Fresh:[/green] {report.fresh_count}
[yellow]Stale:[/yellow] {report.stale_count}
[red]Expired:[/red] {report.expired_count}
[dim]Missing:[/dim] {report.missing_count}
[magenta]Untracked:[/magenta] {report.untracked_count}
[blue]Ignored:[/blue] {report.ignored_count}"""

    console.print(Panel(summary_text, title=f"Content Freshness - {project.name}", expand=False))

    # Show active ignore patterns if requested
    if args.show_ignored or args.ignored:
        patterns = registry.get_ignore_patterns()
        console.print(f"\n[bold]Active ignore patterns:[/bold] {len(patterns)}")
        for p in patterns[:10]:
            console.print(f"  [dim]{p}[/dim]")
        if len(patterns) > 10:
            console.print(f"  [dim]... and {len(patterns) - 10} more[/dim]")

    # Stale items table
    if report.stale_items and (args.stale or not args.untracked):
        table = Table(title="Stale Items (rebuild needed)", box=box.ROUNDED)
        table.add_column("Type", style="cyan", width=15)
        table.add_column("Path", style="white")
        table.add_column("Reason", style="yellow")

        for item in report.stale_items:
            # Find which dependency is newer
            reason = "Dependencies newer than output"
            for dep in item.depends_on:
                dep_path = project.root / dep
                if dep_path.exists():
                    item_path = project.root / item.path
                    if item_path.exists():
                        dep_mtime = dep_path.stat().st_mtime
                        item_mtime = item_path.stat().st_mtime
                        if dep_mtime > item_mtime:
                            reason = f"{dep.name} changed"
                            break

            table.add_row(
                item.content_type.value.replace("_", " ").title(),
                str(item.path),
                reason,
            )

        console.print(table)

    # Expired items table
    if report.expired_items and (args.stale or not args.untracked):
        table = Table(title="Expired Items (content too old)", box=box.ROUNDED)
        table.add_column("Type", style="cyan", width=15)
        table.add_column("Path", style="white")
        table.add_column("Age (days)", justify="right", style="red")
        table.add_column("Max Age", justify="right", style="dim")

        for item in report.expired_items:
            if item.last_modified:
                from datetime import datetime

                age = (datetime.now() - item.last_modified).days
            else:
                age = "?"

            table.add_row(
                item.content_type.value.replace("_", " ").title(),
                str(item.path),
                str(age),
                str(item.freshness_days or "-"),
            )

        console.print(table)

    # Untracked files table
    if report.untracked_files and (args.untracked or not args.stale):
        table = Table(title="Untracked Files", box=box.ROUNDED)
        table.add_column("Path", style="magenta")
        table.add_column("Suggestion", style="dim")

        for path in report.untracked_files[:20]:  # Limit display
            # Suggest action based on path
            suggestion = ""
            path_str = str(path)
            if "/audio/" in path_str or path_str.endswith(".mp3"):
                suggestion = "Add to .mediaignore"
            elif ".cache" in path_str:
                suggestion = "Add to .mediaignore"
            elif "/slides/" in path_str:
                suggestion = "Add to documents.yaml"
            elif "/demos/" in path_str or "/demo/" in path_str:
                suggestion = "Add to documents.yaml"
            elif path_str.endswith(".md"):
                suggestion = "Register in documents.yaml"
            table.add_row(str(path), suggestion)

        if len(report.untracked_files) > 20:
            table.add_row(f"... and {len(report.untracked_files) - 20} more", "")

        console.print(table)

    # Ignored files table
    if report.ignored_files and args.ignored:
        table = Table(title="Ignored Files", box=box.ROUNDED)
        table.add_column("Path", style="blue")
        table.add_column("Matched Pattern", style="dim")

        for path in report.ignored_files[:20]:  # Limit display
            # Find matching pattern
            matched = ""
            for pattern in registry.get_ignore_patterns():
                if registry._should_ignore(path):
                    matched = pattern
                    break
            table.add_row(str(path), matched)

        if len(report.ignored_files) > 20:
            table.add_row(f"... and {len(report.ignored_files) - 20} more", "")

        console.print(table)

    # Suggestions
    if report.stale_count > 0 or report.expired_count > 0:
        console.print()
        console.print("[bold]Suggestions:[/bold]")
        if report.stale_count > 0:
            console.print("  Run [cyan]media-engine build --force[/cyan] to rebuild stale content")
        if report.expired_count > 0:
            console.print("  Review and update expired content to refresh timestamps")

    # Exit with error if there are issues
    if report.stale_count > 0 or report.missing_count > 0:
        sys.exit(1)
