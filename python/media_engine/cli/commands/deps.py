"""Dependency tracking commands using the Unified Relationship Registry."""

import json
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_deps(args):
    """Dependency tracking commands using the unified registry."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...relationships import get_registry_manager, init_registry_manager

    registry_manager = get_registry_manager(project)
    if registry_manager is None:
        registry_manager = init_registry_manager(project)

    if args.deps_command == "status":
        _deps_status(registry_manager, args)
    elif args.deps_command == "stale":
        _deps_stale(registry_manager, args)
    elif args.deps_command == "sync":
        _deps_sync(registry_manager, args)
    elif args.deps_command == "check":
        _deps_check(registry_manager, args)
    elif args.deps_command == "refresh":
        _deps_refresh(registry_manager, args)
    else:
        console.print("[red]Unknown deps command[/red]")
        sys.exit(1)


def _deps_status(manager, args):
    """Show dependency status for all documents."""
    registry = manager.registry
    stale_docs = manager.get_stale_documents()

    # Build status list
    statuses = []
    for node in registry.all_nodes():
        outgoing = registry.get_outgoing_edges(node.path)
        stale_edges = [e for e in outgoing if e.is_stale]

        statuses.append({
            "path": str(node.path),
            "title": node.title or node.path.stem,
            "total_dependencies": len(outgoing),
            "stale_dependencies": len(stale_edges),
            "is_stale": node.is_stale,
        })

    if args.json:
        print(json.dumps(statuses, indent=2))
        return

    if not statuses:
        console.print("[dim]No documents found. Run `media-engine deps refresh` first.[/dim]")
        return

    console.print("\n[bold]Dependency Status[/bold]")

    table = Table(box=box.ROUNDED)
    table.add_column("Document", style="cyan")
    table.add_column("Dependencies", justify="center")
    table.add_column("Stale", justify="center")
    table.add_column("Status", justify="center")

    for status in sorted(statuses, key=lambda s: s["stale_dependencies"], reverse=True):
        status_color = "red" if status["is_stale"] else "green"
        status_text = "stale" if status["is_stale"] else "current"

        table.add_row(
            status["title"][:40],
            str(status["total_dependencies"]),
            str(status["stale_dependencies"]) if status["stale_dependencies"] > 0 else "-",
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    stale_count = len(stale_docs)
    if stale_count > 0:
        console.print(f"\n[yellow]⚠ {stale_count} document(s) have stale dependencies[/yellow]")
    else:
        console.print("\n[green]✓ All dependencies are current[/green]")


def _deps_stale(manager, args):
    """Show only documents with stale dependencies."""
    registry = manager.registry
    stale_docs = manager.get_stale_documents()

    if args.json:
        output = []
        for doc in stale_docs:
            outgoing = registry.get_outgoing_edges(doc.path)
            stale_edges = [e for e in outgoing if e.is_stale]

            output.append({
                "path": str(doc.path),
                "title": doc.title,
                "reasons": doc.stale_reasons,
                "stale_count": len(stale_edges),
                "stale_deps": [
                    {
                        "target": str(e.target),
                        "type": e.edge_type.value,
                        "reason": e.stale_reason,
                    }
                    for e in stale_edges
                ],
            })
        print(json.dumps(output, indent=2))
        return

    if not stale_docs:
        console.print("[green]✓ No stale dependencies[/green]")
        return

    console.print("\n[bold]Documents with Stale Dependencies[/bold]")
    console.print("[dim]These documents reference content that has changed[/dim]\n")

    for doc in stale_docs:
        console.print(f"[cyan]{doc.title or doc.path.stem}[/cyan]")

        # Show stale edges
        outgoing = registry.get_outgoing_edges(doc.path)
        for edge in outgoing:
            if edge.is_stale:
                target_name = edge.target.name
                edge_type = edge.edge_type.value
                console.print(f"  └─ [{edge_type}] {target_name}")
                if edge.stale_reason:
                    console.print(f"     [dim]{edge.stale_reason}[/dim]")

        # Show staleness reasons from node
        if doc.stale_reasons:
            console.print(f"  [dim]Reasons: {', '.join(doc.stale_reasons)}[/dim]")

        console.print()

    console.print(f"[yellow]⚠ {len(stale_docs)} document(s) need review[/yellow]")


def _deps_sync(manager, args):
    """Mark all dependencies as fresh (synced with current state)."""
    if args.dry_run:
        stale_docs = manager.get_stale_documents()
        console.print("\n[bold]Dry Run - Would mark fresh:[/bold]")
        console.print(f"  Stale documents: {len(stale_docs)}")
        return

    console.print("[dim]Marking all documents as fresh...[/dim]")
    manager.mark_all_fresh()

    console.print("\n[green]✓ All documents marked as fresh[/green]")


def _deps_check(manager, args):
    """Check a specific document's dependencies."""
    doc_path = Path(args.document).resolve()

    if not doc_path.exists():
        # Try relative to content dir
        doc_path = manager.project.content_dir / args.document
        if not doc_path.exists():
            doc_path = doc_path.with_suffix(".md")

    if not doc_path.exists():
        console.print(f"[red]Document not found: {args.document}[/red]")
        sys.exit(1)

    registry = manager.registry
    node = registry.get_node(doc_path)
    outgoing = registry.get_outgoing_edges(doc_path)

    if args.json:
        output = {
            "path": str(doc_path),
            "title": node.title if node else doc_path.stem,
            "is_stale": node.is_stale if node else False,
            "stale_reasons": node.stale_reasons if node else [],
            "total_dependencies": len(outgoing),
            "stale_dependencies": len([e for e in outgoing if e.is_stale]),
            "dependencies": [
                {
                    "target": str(e.target),
                    "type": e.edge_type.value,
                    "is_stale": e.is_stale,
                    "stale_reason": e.stale_reason,
                    "source_hash": e.source_hash,
                    "target_hash": e.target_hash,
                }
                for e in outgoing
            ],
        }
        print(json.dumps(output, indent=2))
        return

    title = node.title if node else doc_path.stem
    console.print(f"\n[bold]{title}[/bold]")
    console.print(f"[dim]{doc_path}[/dim]\n")

    if not outgoing:
        console.print("[dim]No dependencies for this document[/dim]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Dependency", style="cyan")
    table.add_column("Type")
    table.add_column("Target Hash", justify="center")
    table.add_column("Status", justify="center")

    stale_count = 0
    for edge in outgoing:
        status_color = "red" if edge.is_stale else "green"
        status_text = "stale" if edge.is_stale else "current"
        if edge.is_stale:
            stale_count += 1

        target_hash = edge.target_hash[:8] if edge.target_hash else "-"
        target_name = edge.target.name

        table.add_row(
            target_name,
            edge.edge_type.value,
            target_hash,
            f"[{status_color}]{status_text}[/{status_color}]",
        )

    console.print(table)

    if stale_count > 0:
        console.print(f"\n[yellow]⚠ {stale_count} stale dependencies[/yellow]")
    else:
        console.print("\n[green]✓ All dependencies current[/green]")


def _deps_refresh(manager, args):
    """Refresh dependency graph and scan all documents."""
    console.print("[dim]Refreshing unified registry...[/dim]")

    result = manager.refresh()

    console.print(f"  Found {result['documents']} documents")
    console.print(f"  Found {result['relationships']} relationships")
    console.print(f"  Elapsed: {result['elapsed_seconds']:.2f}s")

    console.print("\n[green]✓ Registry refreshed[/green]")
