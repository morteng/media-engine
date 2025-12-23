"""Translation command - translation tracking with hash-based change detection."""

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
    elif args.translation_command == "sync":
        _translation_sync(tracker, args)
    else:
        console.print("[red]Unknown translation command[/red]")
        sys.exit(1)


def _translation_status(tracker, args):
    """Show translation status with hash-based tracking."""
    statuses = tracker.get_all_statuses()

    if args.json:
        output = [
            {
                "source": str(s.source_path),
                "translation": str(s.translation_path),
                "source_hash": s.source_content_hash,
                "translated_from_hash": s.translated_from_hash,
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
    table.add_column("Source Hash", justify="center")
    table.add_column("Trans Hash", justify="center")
    table.add_column("Status", justify="center")

    for status in statuses:
        status_color = "red" if status.is_outdated else "green"
        status_text = "outdated" if status.is_outdated else "current"

        # Truncate hashes for display
        src_hash = status.source_content_hash[:8] if status.source_content_hash else "-"
        trans_hash = status.translated_from_hash[:8] if status.translated_from_hash else "-"

        table.add_row(
            status.source_title[:30],
            status.translation_title[:30],
            status.target_language,
            src_hash,
            trans_hash,
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    outdated_count = sum(1 for s in statuses if s.is_outdated)
    if outdated_count > 0:
        console.print(f"\n[yellow]⚠ {outdated_count} translation(s) need updating[/yellow]")
    else:
        console.print("\n[green]✓ All translations are current[/green]")


def _translation_outdated(tracker, args):
    """Show only outdated translations (source content has changed)."""
    outdated = tracker.get_outdated_translations()

    if args.json:
        output = [
            {
                "source": str(s.source_path),
                "translation": str(s.translation_path),
                "source_hash": s.source_content_hash,
                "translated_from_hash": s.translated_from_hash,
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
    console.print("[dim]Source content has changed since translation was made[/dim]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Translation", style="cyan")
    table.add_column("Lang")
    table.add_column("Current Source Hash", justify="center")
    table.add_column("Translated From Hash", justify="center")

    for status in outdated:
        src_hash = status.source_content_hash[:8] if status.source_content_hash else "-"
        trans_hash = status.translated_from_hash[:8] if status.translated_from_hash else "-"

        table.add_row(
            status.translation_title[:40],
            status.target_language,
            f"[cyan]{src_hash}[/cyan]",
            f"[red]{trans_hash}[/red]",
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

    for doc in missing:
        table.add_row(doc.title)

    console.print(table)
    console.print(
        f"\n[yellow]⚠ {len(missing)} document(s) need translation to {target_lang}[/yellow]"
    )


def _translation_sync(tracker, args):
    """Sync translation hashes (mark as current with source)."""
    from ...cms.document import Document

    statuses = tracker.get_all_statuses()

    # Only sync current translations (not outdated)
    to_sync = [s for s in statuses if not s.is_outdated]

    if args.dry_run:
        console.print("\n[bold]Dry Run - Would sync:[/bold]")
        for s in to_sync:
            console.print(f"  • {s.translation_title}")
        console.print(f"\n[dim]Total: {len(to_sync)} translations[/dim]")
        return

    synced = 0
    errors = []

    for status in to_sync:
        try:
            trans_doc = Document.load(status.translation_path)
            result = tracker.mark_synced(trans_doc)
            if "error" in result:
                errors.append((status.translation_title, result["error"]))
            else:
                synced += 1
        except Exception as e:
            errors.append((status.translation_title, str(e)))

    console.print(f"\n[green]✓ Synced {synced} translation(s)[/green]")

    if errors:
        console.print(f"[red]✗ {len(errors)} error(s):[/red]")
        for title, error in errors:
            console.print(f"  • {title}: {error}")
