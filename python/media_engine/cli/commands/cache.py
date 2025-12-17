"""Cache command - cache management."""

import sys

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_cache(args):
    """Cache management commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    if args.cache_command == "status":
        status = project.get_status()
        cache = status["cache"]

        console.print("[bold]Cache Status[/bold]")
        console.print(f"  Voiceover files: {cache['voiceover_items']}")
        console.print(f"  Builds tracked: {cache['builds_tracked']}")

        # Show cache directory size
        cache_dir = project.cache_dir
        if cache_dir.exists():
            total_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
            console.print(f"  Cache size: {total_size / 1024 / 1024:.1f} MB")
        else:
            console.print("  Cache size: 0 MB")

    elif args.cache_command == "clear":
        cache_type = None
        if args.voiceover:
            cache_type = "voiceover"
        elif args.builds:
            cache_type = "builds"
        else:
            cache_type = "all"

        count = project.clear_cache(cache_type)
        console.print(f"[green]Cleared {count} cached items[/green]")
