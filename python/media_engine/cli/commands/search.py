"""Search commands - search and index."""

import json
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_search(args):
    """Search project documents."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...search import SearchIndex, build_search_index

    query = args.query

    # Build or load index
    index_path = project.cache_dir / "search_index.json"

    if args.rebuild or not index_path.exists():
        console.print("[bold]Building search index...[/bold]")
        index = build_search_index(project, console_output=not args.json)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index.save(index_path)
    else:
        index = SearchIndex.load(index_path)

    # Search
    results = index.search(query, limit=args.limit)

    if args.json:
        output = {
            "query": query,
            "results": [
                {
                    "id": r.entry.id,
                    "title": r.entry.title,
                    "path": r.entry.path,
                    "score": r.score,
                    "excerpt": r.entry.excerpt,
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2))
        return

    if not results:
        console.print(f"[dim]No results for: {query}[/dim]")
        return

    console.print(f"\n[bold]Search results for: {query}[/bold]\n")

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Title", style="cyan", width=35)
    table.add_column("Type", width=12)
    table.add_column("Excerpt", width=50)

    for result in results:
        excerpt = (
            result.entry.excerpt[:47] + "..."
            if len(result.entry.excerpt) > 50
            else result.entry.excerpt
        )
        table.add_row(
            f"{result.score:.0f}",
            result.entry.title,
            result.entry.type,
            excerpt,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} results[/dim]")


def cmd_index(args):
    """Build or update search index."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...search import build_search_index

    index = build_search_index(project, console_output=True)

    # Save index
    output_path = Path(args.output) if args.output else project.cache_dir / "search_index.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    index.save(output_path)

    console.print(f"\n[green]✓ Index saved to {output_path}[/green]")
    console.print(f"  Entries: {len(index.entries)}")
