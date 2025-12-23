"""Notes command - General notes management."""

import json
import sys

from rich.console import Console
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_notes(args):
    """General notes management."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...notes import (
        NotePriority,
        NotesRegistry,
        NoteStatus,
        NoteType,
        generate_export,
        migrate_scene_notes,
        write_exports,
    )

    registry = NotesRegistry(project)

    if args.notes_command == "list":
        notes = registry.get_all()

        # Apply filters
        if getattr(args, "status", None):
            notes = [n for n in notes if n.status == NoteStatus(args.status)]
        if getattr(args, "type", None):
            notes = [n for n in notes if n.note_type == NoteType(args.type)]
        if getattr(args, "priority", None):
            notes = [n for n in notes if n.priority == NotePriority(args.priority)]
        if getattr(args, "pending", False):
            notes = [n for n in notes if n.status == NoteStatus.PENDING]

        if getattr(args, "json", False):
            print(
                json.dumps({"count": len(notes), "notes": [n.to_dict() for n in notes]}, indent=2)
            )
        else:
            table = Table(title=f"Notes ({len(notes)})")
            table.add_column("ID", style="dim")
            table.add_column("Type", style="cyan")
            table.add_column("Target")
            table.add_column("Text")
            table.add_column("Status")
            table.add_column("Priority")

            status_colors = {"pending": "yellow", "completed": "green", "archived": "dim"}
            priority_colors = {
                "critical": "red bold",
                "high": "red",
                "medium": "yellow",
                "low": "dim",
            }

            for note in notes:
                target_display = note.target_path
                if len(target_display) > 30:
                    target_display = "..." + target_display[-27:]

                text_display = note.text
                if len(text_display) > 40:
                    text_display = text_display[:37] + "..."

                table.add_row(
                    note.note_id,
                    note.note_type.value,
                    target_display,
                    text_display,
                    f"[{status_colors[note.status.value]}]{note.status.value}[/]",
                    f"[{priority_colors[note.priority.value]}]{note.priority.value}[/]",
                )

            console.print(table)

    elif args.notes_command == "add":
        if not getattr(args, "type", None) or not getattr(args, "target", None):
            console.print(
                "[red]Usage: media-engine notes add --type <type> --target <path> --text <text>[/red]"
            )
            sys.exit(1)

        note = registry.add(
            note_type=NoteType(args.type),
            target_path=args.target,
            text=args.text,
            target_id=getattr(args, "target_id", None),
            priority=NotePriority(getattr(args, "priority", "medium")),
            tags=([t.strip() for t in args.tags.split(",")] if getattr(args, "tags", None) else []),
        )
        console.print(f"[green]Note added with ID: {note.note_id}[/green]")

    elif args.notes_command == "complete":
        note = registry.complete(args.note_id)
        if note:
            console.print(f"[green]Note {args.note_id} marked as completed[/green]")
        else:
            console.print(f"[red]Note {args.note_id} not found[/red]")

    elif args.notes_command == "archive":
        note = registry.archive(args.note_id)
        if note:
            console.print(f"[green]Note {args.note_id} archived[/green]")
        else:
            console.print(f"[red]Note {args.note_id} not found[/red]")

    elif args.notes_command == "reopen":
        note = registry.reopen(args.note_id)
        if note:
            console.print(f"[green]Note {args.note_id} reopened[/green]")
        else:
            console.print(f"[red]Note {args.note_id} not found[/red]")

    elif args.notes_command == "delete":
        if registry.delete(args.note_id):
            console.print(f"[green]Note {args.note_id} deleted[/green]")
        else:
            console.print(f"[red]Note {args.note_id} not found[/red]")

    elif args.notes_command == "report":
        report = registry.generate_report()
        if getattr(args, "json", False):
            print(json.dumps(report.to_dict(), indent=2))
        else:
            console.print("[bold]Notes Report[/bold]")
            console.print(f"  Total: {report.total_notes}")
            console.print(f"  [yellow]Pending: {report.pending_count}[/yellow]")
            console.print(f"  [green]Completed: {report.completed_count}[/green]")
            console.print(f"  [dim]Archived: {report.archived_count}[/dim]")

            if report.by_type:
                console.print("\n[bold]By Type:[/bold]")
                for t, count in report.by_type.items():
                    console.print(f"  {t}: {count}")

            if report.by_priority:
                console.print("\n[bold]By Priority:[/bold]")
                priority_colors = {
                    "critical": "red bold",
                    "high": "red",
                    "medium": "yellow",
                    "low": "dim",
                }
                for p, count in report.by_priority.items():
                    console.print(f"  [{priority_colors.get(p, '')}]{p}[/]: {count}")

            if report.pending_notes:
                console.print(
                    f"\n[bold yellow]Top Pending ({len(report.pending_notes)}):[/bold yellow]"
                )
                for note in report.pending_notes[:5]:
                    text = note.text[:50] + "..." if len(note.text) > 50 else note.text
                    console.print(f"  [{note.priority.value}] {text}")

    elif args.notes_command == "export":
        export_data = generate_export(registry, project)
        write_exports(project, export_data)

        console.print(f"[green]Exported {export_data['total_pending']} pending notes[/green]")
        console.print("  JSON: .media-engine/notes-export.json")
        console.print("  Markdown: .media-engine/notes-export.md")

    elif args.notes_command == "migrate":
        console.print("[bold]Migrating scene notes to general notes system...[/bold]")
        result = migrate_scene_notes(project)

        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            console.print(f"[green]{result['message']}[/green]")
            if result["errors"]:
                console.print(f"[yellow]Errors: {len(result['errors'])}[/yellow]")
                for err in result["errors"][:5]:
                    console.print(f"  {err['file']}: {err['error']}")

    else:
        console.print(
            "[yellow]Usage: media-engine notes <list|add|complete|archive|reopen|delete|report|export|migrate>[/yellow]"
        )
