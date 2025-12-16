"""
Specialized Status Views

Individual view functions for specific status domains.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


def print_document_status(project: "Project", language: Optional[str] = None):
    """
    Print detailed document status.

    Shows all chapters with version, status, word count, and freshness.
    """
    from .dashboard import get_content_status

    languages = [language] if language else list(project.languages.keys())

    console.print()
    console.print(Panel("[bold]Document Status[/bold]", border_style="blue"))

    for lang in languages:
        content = get_content_status(project, lang)

        console.print(
            f"\n[bold cyan]{lang.upper()}[/bold cyan] - {len(content.chapters)} chapters, {content.total_words:,} words"
        )

        if not content.chapters:
            console.print("  [dim]No chapters found[/dim]")
            continue

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Chapter", style="cyan", width=30)
        table.add_column("Version", justify="center", width=10)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Words", justify="right", width=8)
        table.add_column("Age", justify="right", width=8)
        table.add_column("Fresh", justify="center", width=8)

        for doc in sorted(content.chapters, key=lambda d: d.path.name):
            # Status color
            status_color = {
                "final": "green",
                "review": "yellow",
                "draft": "dim",
            }.get(doc.status, "white")

            # Freshness color
            fresh_color = {
                "fresh": "green",
                "stale": "yellow",
                "expired": "red",
            }.get(doc.freshness_status, "white")

            # Title truncation
            title = doc.title[:28] + ".." if len(doc.title) > 30 else doc.title

            table.add_row(
                title,
                doc.version,
                f"[{status_color}]{doc.status}[/{status_color}]",
                f"{doc.word_count:,}",
                f"{doc.days_old}d",
                f"[{fresh_color}]{doc.freshness_status}[/{fresh_color}]",
            )

        console.print(table)

        # Summary
        final_count = sum(1 for c in content.chapters if c.status == "final")
        stale_count = sum(1 for c in content.chapters if c.freshness_status in ("stale", "expired"))
        console.print(
            f"  [dim]Final: {final_count}/{len(content.chapters)} | Stale: {stale_count}[/dim]"
        )


def print_video_status(project: "Project", language: Optional[str] = None):
    """
    Print detailed video production status.

    Shows all video scripts with production stage.
    """
    from .dashboard import get_video_status

    languages = [language] if language else list(project.languages.keys())

    console.print()
    console.print(Panel("[bold]Video Production Status[/bold]", border_style="blue"))

    for lang in languages:
        videos = get_video_status(project, lang)

        if not videos:
            console.print(f"\n[dim]{lang.upper()}: No video scripts found[/dim]")
            continue

        console.print(f"\n[bold cyan]{lang.upper()}[/bold cyan] - {len(videos)} scripts")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Script", style="cyan", width=25)
        table.add_column("Script", justify="center", width=8)
        table.add_column("Audio", justify="center", width=8)
        table.add_column("VTT", justify="center", width=8)
        table.add_column("MP4", justify="center", width=8)
        table.add_column("Status", justify="center", width=12)

        for video in sorted(videos, key=lambda v: v.script_name):
            status_color = {
                "complete": "green",
                "in_progress": "yellow",
                "not_started": "dim",
            }.get(video.status, "white")

            table.add_row(
                video.script_name,
                "[green]✓[/green]" if video.has_script else "[dim]–[/dim]",
                "[green]✓[/green]" if video.has_voiceover else "[dim]–[/dim]",
                "[green]✓[/green]" if video.has_captions else "[dim]–[/dim]",
                "[green]✓[/green]" if video.has_video else "[dim]–[/dim]",
                f"[{status_color}]{video.status.replace('_', ' ')}[/{status_color}]",
            )

        console.print(table)

        # Summary
        complete = sum(1 for v in videos if v.status == "complete")
        in_progress = sum(1 for v in videos if v.status == "in_progress")
        console.print(
            f"  [dim]Complete: {complete} | In Progress: {in_progress} | Not Started: {len(videos) - complete - in_progress}[/dim]"
        )


def print_quality_status(project: "Project", language: Optional[str] = None):
    """
    Print quality check summary.

    Shows placeholder, terminology, and encoding issues.
    """
    from ..quality import run_quality_checks

    console.print()
    console.print(Panel("[bold]Quality Check Status[/bold]", border_style="blue"))

    # Run quality checks
    report = run_quality_checks(project, console_output=False)

    if not report.issues:
        console.print("\n[green]✓ All content passed quality checks[/green]")
        console.print(f"  [dim]Files checked: {report.files_checked}[/dim]")
        return

    # Group issues by type
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}

    for issue in report.issues:
        by_type[issue.type] = by_type.get(issue.type, 0) + 1
        by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1

    console.print(
        f"\n[yellow]Found {len(report.issues)} issues in {report.files_checked} files[/yellow]\n"
    )

    # Summary by type
    type_table = Table(title="Issues by Type", box=box.SIMPLE, show_header=True)
    type_table.add_column("Type", style="cyan")
    type_table.add_column("Count", justify="right")

    for issue_type, count in sorted(by_type.items()):
        type_table.add_row(issue_type, str(count))

    console.print(type_table)

    # Summary by severity
    console.print()
    severity_table = Table(title="Issues by Severity", box=box.SIMPLE, show_header=True)
    severity_table.add_column("Severity", style="cyan")
    severity_table.add_column("Count", justify="right")

    for severity, count in sorted(by_severity.items()):
        color = {"error": "red", "warning": "yellow", "info": "blue"}.get(severity, "white")
        severity_table.add_row(f"[{color}]{severity}[/{color}]", str(count))

    console.print(severity_table)

    # Show first few issues as examples
    console.print("\n[bold]Sample Issues:[/bold]")
    for issue in report.issues[:5]:
        severity_color = {"error": "red", "warning": "yellow", "info": "blue"}.get(
            issue.severity, "white"
        )
        console.print(
            f"  [{severity_color}]{issue.type}[/{severity_color}] {issue.file_path.name}:{issue.line} - {issue.message}"
        )

    if len(report.issues) > 5:
        console.print(f"  [dim]... and {len(report.issues) - 5} more[/dim]")


def print_deliverable_status(project: "Project"):
    """
    Print deliverable status with completeness.

    Shows all expected deliverables and their build status.
    """
    from .dashboard import get_deliverable_status

    console.print()
    console.print(Panel("[bold]Deliverable Status[/bold]", border_style="blue"))

    deliverables = get_deliverable_status(project)

    # Group by language
    by_lang: Dict[str, List] = {}
    for d in deliverables:
        if d.language not in by_lang:
            by_lang[d.language] = []
        by_lang[d.language].append(d)

    for lang, lang_deliverables in sorted(by_lang.items()):
        console.print(f"\n[bold cyan]{lang.upper()}[/bold cyan]")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Deliverable", style="cyan", width=25)
        table.add_column("Type", justify="center", width=8)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Built", justify="right", width=18)

        for d in sorted(lang_deliverables, key=lambda x: (x.type, x.name)):
            status_str = "[green]✓[/green]" if d.exists else "[red]✗[/red]"
            built_str = d.last_built.strftime("%Y-%m-%d %H:%M") if d.last_built else "–"

            table.add_row(
                d.name,
                d.type.upper(),
                status_str,
                built_str,
            )

        console.print(table)

        # Summary
        built = sum(1 for d in lang_deliverables if d.exists)
        console.print(f"  [dim]Built: {built}/{len(lang_deliverables)}[/dim]")


def print_build_tree(project: "Project"):
    """
    Print build dependency tree.

    Shows what outputs depend on what sources.
    """
    console.print()
    console.print(Panel("[bold]Build Tree[/bold]", border_style="blue"))

    tree = Tree(f"[bold]{project.name}[/bold]")

    for lang in project.languages:
        lang_branch = tree.add(f"[cyan]{lang}[/cyan]")

        # Sources
        sources = lang_branch.add("[dim]sources[/dim]")
        chapters = list(project.list_chapters(lang))
        for chapter in chapters[:5]:
            sources.add(f"[dim]{chapter.name}[/dim]")
        if len(chapters) > 5:
            sources.add(f"[dim]... and {len(chapters) - 5} more[/dim]")

        # Outputs
        outputs = lang_branch.add("[dim]outputs[/dim]")
        output_dir = project.output_dir / lang
        if output_dir.exists():
            for output in output_dir.glob("*"):
                if output.is_file():
                    outputs.add(f"[green]{output.name}[/green]")
                elif output.is_dir():
                    dir_branch = outputs.add(f"[blue]{output.name}/[/blue]")
                    for child in list(output.glob("*"))[:3]:
                        dir_branch.add(f"[dim]{child.name}[/dim]")
        else:
            outputs.add("[dim]no outputs yet[/dim]")

    console.print(tree)


def print_cache_status(project: "Project"):
    """
    Print detailed cache status.

    Shows cache contents and sizes.
    """
    console.print()
    console.print(Panel("[bold]Cache Status[/bold]", border_style="blue"))

    cache_dir = project.cache_dir

    if not cache_dir.exists():
        console.print("\n[dim]No cache directory found[/dim]")
        return

    # Get cache subdirectories
    subdirs = [d for d in cache_dir.iterdir() if d.is_dir()]

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Cache", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")

    total_files = 0
    total_size = 0

    for subdir in subdirs:
        files = list(subdir.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        size = sum(f.stat().st_size for f in files if f.is_file())

        total_files += file_count
        total_size += size

        size_str = f"{size / 1024 / 1024:.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
        table.add_row(subdir.name, str(file_count), size_str)

    console.print(f"\n[bold]Cache directory:[/bold] {cache_dir}")
    console.print()
    console.print(table)

    total_str = (
        f"{total_size / 1024 / 1024:.1f} MB"
        if total_size > 1024 * 1024
        else f"{total_size / 1024:.1f} KB"
    )
    console.print(f"\n[dim]Total: {total_files} files, {total_str}[/dim]")
