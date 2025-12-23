"""Quality commands - quality checks and stale content."""

import json
import sys

from rich import box
from rich.console import Console
from rich.table import Table

from ...cms import Document
from ...core import find_project

console = Console()


def cmd_quality(args):
    """Run quality checks on project content."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...quality import run_quality_checks

    # Determine if hierarchy checks should be included
    include_hierarchy = True
    if hasattr(args, "no_hierarchy") and args.no_hierarchy:
        include_hierarchy = False

    # Get type filter if specified
    type_filter = getattr(args, "type", None)

    report = run_quality_checks(
        project, console_output=not type_filter, include_hierarchy=include_hierarchy
    )

    # Filter issues by type if specified
    if type_filter:
        filtered_issues = [i for i in report.issues if type_filter in i.type]
        # Update report with filtered issues
        report.issues = filtered_issues
        # Print filtered report
        from ...quality.checks import print_quality_report

        print_quality_report(report)

    if args.json:
        import json

        issues_data = [
            {
                "type": i.type,
                "severity": i.severity,
                "file": str(i.file_path),
                "line": i.line,
                "message": i.message,
                "context": i.context,
            }
            for i in report.issues
        ]
        print(
            json.dumps(
                {
                    "passed": report.passed,
                    "files_checked": report.files_checked,
                    "error_count": report.error_count,
                    "warning_count": report.warning_count,
                    "issues": issues_data,
                },
                indent=2,
            )
        )
        return

    if not report.passed:
        sys.exit(1)


def cmd_stale(args):
    """List stale content."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    stale_items = []

    for lang in project.languages:
        for chapter_path in project.list_chapters(lang):
            try:
                doc = Document.load(chapter_path)
                if doc.is_stale:
                    stale_items.append(
                        {
                            "path": str(chapter_path.relative_to(project.root)),
                            "language": lang,
                            "title": doc.title,
                            "days_since_modified": doc.days_since_modified,
                            "freshness_days": doc.freshness_days,
                            "status": doc.freshness_status,
                        }
                    )
            except Exception:
                pass

    if args.json:
        print(json.dumps(stale_items, indent=2))
        return

    if not stale_items:
        console.print("[green]No stale content found[/green]")
        return

    table = Table(title="Stale Content", box=box.ROUNDED)
    table.add_column("Document", style="cyan")
    table.add_column("Lang", justify="center")
    table.add_column("Days Old", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Status", justify="center")

    for item in stale_items:
        status_color = "yellow" if item["status"] == "stale" else "red"
        table.add_row(
            item["title"],
            item["language"],
            str(item["days_since_modified"]),
            str(item["freshness_days"]),
            f"[{status_color}]{item['status']}[/{status_color}]",
        )

    console.print(table)
