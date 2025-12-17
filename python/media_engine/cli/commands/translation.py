"""Translation command - translation tracking."""

import json
import sys

from rich import box
from rich.console import Console
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_translation(args):
    """Translation tracking commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...cms.translation import TranslationTracker

    tracker = TranslationTracker(project)

    if args.translation_command == "status":
        _translation_status(tracker, args)
    elif args.translation_command == "outdated":
        _translation_outdated(tracker, args)
    elif args.translation_command == "missing":
        _translation_missing(tracker, project, args)
    else:
        console.print("[red]Unknown translation command[/red]")
        sys.exit(1)


def _translation_status(tracker, args):
    """Show translation status."""
    statuses = tracker.get_all_statuses()

    if args.json:
        output = [
            {
                "source": str(s.source_path),
                "translation": str(s.translation_path),
                "source_version": s.source_version,
                "translated_version": s.translated_version,
                "is_outdated": s.is_outdated,
                "source_language": s.source_language,
                "target_language": s.target_language,
            }
            for s in statuses
        ]
        print(json.dumps(output, indent=2))
        return

    if not statuses:
        console.print("[dim]No translations found[/dim]")
        return

    console.print("\n[bold]Translation Status[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Source", style="cyan")
    table.add_column("Translation", style="cyan")
    table.add_column("Lang", justify="center")
    table.add_column("Source Ver", justify="center")
    table.add_column("Trans Ver", justify="center")
    table.add_column("Status", justify="center")

    for status in statuses:
        status_color = "red" if status.is_outdated else "green"
        status_text = "outdated" if status.is_outdated else "current"

        table.add_row(
            status.source_title[:30],
            status.translation_title[:30],
            status.target_language,
            status.source_version,
            status.translated_version,
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    outdated_count = sum(1 for s in statuses if s.is_outdated)
    if outdated_count > 0:
        console.print(f"\n[yellow]⚠ {outdated_count} translation(s) need updating[/yellow]")
    else:
        console.print("\n[green]✓ All translations are current[/green]")


def _translation_outdated(tracker, args):
    """Show only outdated translations."""
    outdated = tracker.get_outdated_translations()

    if args.json:
        output = [
            {
                "source": str(s.source_path),
                "translation": str(s.translation_path),
                "source_version": s.source_version,
                "translated_version": s.translated_version,
                "target_language": s.target_language,
            }
            for s in outdated
        ]
        print(json.dumps(output, indent=2))
        return

    if not outdated:
        console.print("[green]✓ No outdated translations[/green]")
        return

    console.print("\n[bold]Outdated Translations[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Translation", style="cyan")
    table.add_column("Lang")
    table.add_column("Source Ver", justify="center")
    table.add_column("Trans Ver", justify="center")
    table.add_column("Behind", justify="center")

    for status in outdated:
        table.add_row(
            status.translation_title[:40],
            status.target_language,
            status.source_version,
            status.translated_version,
            f"[red]{status.source_version}[/red]",
        )

    console.print(table)
    console.print(f"\n[yellow]⚠ {len(outdated)} translation(s) need updating[/yellow]")


def _translation_missing(tracker, project, args):
    """Show missing translations."""
    target_lang = args.lang or "no"  # Default to Norwegian

    missing = tracker.get_missing_translations(target_lang)

    if args.json:
        output = [
            {
                "title": doc.title,
                "path": str(doc.path),
            }
            for doc in missing
        ]
        print(json.dumps(output, indent=2))
        return

    if not missing:
        console.print(f"[green]✓ All source documents have {target_lang} translations[/green]")
        return

    console.print(f"\n[bold]Missing Translations ({target_lang})[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Source Document", style="cyan")
    table.add_column("Version")

    for doc in missing:
        table.add_row(doc.title, doc.version)

    console.print(table)
    console.print(
        f"\n[yellow]⚠ {len(missing)} document(s) need translation to {target_lang}[/yellow]"
    )
