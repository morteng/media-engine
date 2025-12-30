"""Relationships commands - unified document relationship management."""

import json
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_relationships(args):
    """Entry point for relationships commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...relationships import get_registry_manager, init_registry_manager

    registry_manager = get_registry_manager(project)
    if registry_manager is None:
        registry_manager = init_registry_manager(project)

    registry = registry_manager.registry

    # Handle subcommands
    if hasattr(args, "relationships_command"):
        if args.relationships_command == "status":
            _show_status(project, registry, args)
        elif args.relationships_command == "refresh":
            _refresh(project, registry, args)
        elif args.relationships_command == "stale":
            _show_stale(project, registry, args)
        elif args.relationships_command == "impact":
            _show_impact(project, registry, args)
        elif args.relationships_command == "graph":
            _export_graph(project, registry, args)
        elif args.relationships_command == "sync":
            _sync(project, registry, args)
        elif args.relationships_command == "anchors":
            _show_anchors(project, registry, args)
        elif args.relationships_command == "orphans":
            _show_orphans(project, registry, registry_manager, args)
        elif args.relationships_command == "assets":
            _show_assets(project, registry, registry_manager, args)
        else:
            _show_status(project, registry, args)
    else:
        _show_status(project, registry, args)


def _show_status(project, registry, args):
    """Show relationship summary."""
    report = registry.generate_report()

    if hasattr(args, "json") and args.json:
        print(json.dumps(report, indent=2))
        return

    summary = report["summary"]

    # Summary panel
    summary_text = f"""[bold]Documents:[/bold] {summary['total_documents']}
[bold]Relationships:[/bold] {summary['total_relationships']}
[yellow]Stale:[/yellow] {summary['stale_documents']}
[dim]Orphans:[/dim] {summary['orphan_documents']}
[dim]Roots:[/dim] {summary['root_documents']}
[bold]Anchors:[/bold] {summary['anchors']}"""

    console.print(Panel(summary_text, title="Unified Relationship Registry", expand=False))

    # Relationships by type
    by_type = report.get("by_type", {})
    if by_type:
        console.print("\n[bold]Relationships by Type:[/bold]")
        type_table = Table(show_header=False, box=box.SIMPLE)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right")
        for edge_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            type_table.add_row(edge_type, str(count))
        console.print(type_table)


def _refresh(project, registry, args):
    """Rebuild relationship graph from documents."""
    from ...relationships import get_registry_manager

    console.print("Scanning documents...")

    manager = get_registry_manager(project)
    result = manager.refresh()

    console.print(f"[green]Scanned {result['documents']} documents[/green]")
    console.print(f"[green]Found {result['relationships']} relationships[/green]")
    console.print(f"[green]Elapsed: {result['elapsed_seconds']:.2f}s[/green]")


def _show_stale(project, registry, args):
    """Show stale documents and relationships."""
    from ...relationships import get_registry_manager

    manager = get_registry_manager(project)
    stale_docs = manager.get_stale_documents()

    # Convert to status-like format
    stale_statuses = []
    for doc in stale_docs:
        edges = registry.get_outgoing_edges(doc.path)
        stale_edges = [e for e in edges if e.is_stale]
        stale_statuses.append({
            "document": doc.path,
            "title": doc.title,
            "stale_edges": stale_edges,
            "suggested_actions": [f"Review {doc.path.name}"] if stale_edges else [],
        })

    if hasattr(args, "json") and args.json:
        output = [{
            "path": str(s["document"]),
            "title": s["title"],
            "stale_edges": [{"target": str(e.target), "type": e.edge_type.value} for e in s["stale_edges"]],
        } for s in stale_statuses]
        print(json.dumps(output, indent=2))
        return

    if not stale_statuses:
        console.print("[green]No stale documents found.[/green]")
        return

    console.print(f"[yellow]Found {len(stale_statuses)} stale documents:[/yellow]\n")

    for status in stale_statuses:
        doc_name = status["document"].name
        console.print(f"[bold]{doc_name}[/bold]")

        for edge in status["stale_edges"]:
            target_name = edge.target.name
            edge_type = edge.edge_type.value
            reason = edge.stale_reason or "unknown"
            console.print(f"  [cyan]--[{edge_type}]-->[/cyan] {target_name}")
            console.print(f"     [dim]Reason: {reason}[/dim]")

        if status["suggested_actions"]:
            console.print("  [bold]Suggested actions:[/bold]")
            for action in status["suggested_actions"]:
                console.print(f"    [green]- {action}[/green]")

        console.print()


def _show_impact(project, registry, args):
    """Analyze impact of changing a document."""
    if not hasattr(args, "document") or not args.document:
        console.print("[red]Please specify a document with --document[/red]")
        return

    # Resolve document path
    doc_path = project.content_dir / args.document
    if not doc_path.exists():
        doc_path = doc_path.with_suffix(".md")

    if not doc_path.exists():
        console.print(f"[red]Document not found: {args.document}[/red]")
        return

    affected = registry.get_impact(doc_path)

    if hasattr(args, "json") and args.json:
        print(json.dumps({
            "document": str(doc_path),
            "affected": [str(p) for p in affected]
        }, indent=2))
        return

    if not affected:
        console.print(f"[green]No documents depend on {doc_path.name}[/green]")
        return

    console.print(f"[bold]Changing {doc_path.name} affects {len(affected)} documents:[/bold]\n")

    # Group by relationship type
    for affected_doc in sorted(affected):
        edges = registry.get_outgoing_edges(affected_doc)
        relevant = [e for e in edges if str(e.target) == str(doc_path)]

        if relevant:
            edge_types = [e.edge_type.value for e in relevant]
            console.print(f"  {affected_doc.name} [dim][{', '.join(edge_types)}][/dim]")
        else:
            console.print(f"  {affected_doc.name}")


def _export_graph(project, registry, args):
    """Export relationship graph for visualization."""
    output_format = getattr(args, "format", "dot") or "dot"
    output_path = getattr(args, "output", None)
    edge_types = getattr(args, "type", None)
    if edge_types:
        edge_types = [t.strip() for t in edge_types.split(",")]

    if output_format == "dot":
        content = _generate_dot(registry, edge_types)
    elif output_format == "mermaid":
        content = _generate_mermaid(registry, edge_types)
    else:
        content = json.dumps(registry.generate_report(), indent=2)

    if output_path:
        with open(output_path, "w") as f:
            f.write(content)
        console.print(f"[green]Graph exported to {output_path}[/green]")
    else:
        print(content)


def _sync(project, registry, args):
    """Mark relationships as fresh (update hashes)."""
    from ...relationships import get_registry_manager

    manager = get_registry_manager(project)

    sync_all = getattr(args, "all", False)
    document = getattr(args, "document", None)

    if sync_all:
        manager.mark_all_fresh()
        console.print("[green]All documents marked as fresh[/green]")
        return

    if not document:
        console.print("[yellow]Specify a document or use --all[/yellow]")
        return

    # Resolve document path
    doc_path = project.content_dir / document
    if not doc_path.exists():
        doc_path = doc_path.with_suffix(".md")

    if not doc_path.exists():
        console.print(f"[red]Document not found: {document}[/red]")
        return

    manager.mark_fresh(doc_path)
    console.print(f"[green]Marked {doc_path.name} as fresh[/green]")


def _show_anchors(project, registry, args):
    """Show consistency anchors."""
    if registry.data_path.exists():
        with open(registry.data_path) as f:
            data = json.load(f)
        anchors_data = data.get("anchors", {})
    else:
        anchors_data = {}

    if hasattr(args, "json") and args.json:
        print(json.dumps(anchors_data, indent=2))
        return

    if not anchors_data:
        console.print("[dim]No anchors defined[/dim]")
        return

    console.print(Panel("[bold]Consistency Anchors[/bold]", expand=False))

    table = Table(box=box.ROUNDED)
    table.add_column("Anchor", style="cyan")
    table.add_column("Value")
    table.add_column("Type", style="dim")
    table.add_column("Defined In")
    table.add_column("Refs", justify="right")

    for anchor_id, anchor in anchors_data.items():
        defined_in = Path(anchor["defined_in"]).name
        refs = len(anchor.get("referenced_in", []))
        value = str(anchor["value"])
        if len(value) > 30:
            value = value[:27] + "..."

        table.add_row(
            anchor_id,
            value,
            anchor["value_type"],
            defined_in,
            str(refs)
        )

    console.print(table)


def _generate_dot(registry, edge_types=None) -> str:
    """Generate DOT format for Graphviz."""
    lines = ["digraph relationships {"]
    lines.append("  rankdir=LR;")
    lines.append("  node [shape=box, fontname=Arial];")
    lines.append("  edge [fontname=Arial, fontsize=10];")

    colors = {
        "parent": "black",
        "implements": "green",
        "extends": "blue",
        "summarizes": "purple",
        "translates": "orange",
        "references": "gray",
        "uses_asset": "brown",
        "depends_on": "darkgreen",
        "anchor_ref": "red",
    }

    for node in registry.all_nodes():
        for edge in registry.get_outgoing_edges(node.path):
            if edge_types and edge.edge_type.value not in edge_types:
                continue

            source = node.path.stem
            target = edge.target.stem
            edge_type = edge.edge_type.value
            color = colors.get(edge_type, "gray")
            style = ', style=dashed' if edge.is_stale else ''

            lines.append(f'  "{source}" -> "{target}" [color={color}, label="{edge_type}"{style}];')

    lines.append("}")
    return "\n".join(lines)


def _generate_mermaid(registry, edge_types=None) -> str:
    """Generate Mermaid format for diagrams."""
    lines = ["graph LR"]

    for node in registry.all_nodes():
        for edge in registry.get_outgoing_edges(node.path):
            if edge_types and edge.edge_type.value not in edge_types:
                continue

            source = node.path.stem.replace("-", "_").replace(" ", "_")
            target = edge.target.stem.replace("-", "_").replace(" ", "_")
            edge_type = edge.edge_type.value

            arrow = "-..->" if edge.is_stale else "-->"
            lines.append(f"    {source} {arrow}|{edge_type}| {target}")

    return "\n".join(lines)


def _show_orphans(project, registry, registry_manager, args):
    """Show orphaned assets (not referenced by any document)."""
    orphans = registry_manager.get_orphan_assets()
    missing = registry_manager.get_missing_assets()

    if hasattr(args, "json") and args.json:
        output = {
            "orphans": [{"path": str(n.path), "type": n.doc_type} for n in orphans],
            "missing": [{"path": str(p), "referenced_by": str(e.source)} for p, e in missing],
        }
        print(json.dumps(output, indent=2))
        return

    # Show orphaned assets
    if orphans:
        console.print(Panel(f"[yellow]Found {len(orphans)} orphaned assets[/yellow]", expand=False))
        table = Table(box=box.ROUNDED)
        table.add_column("Asset", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Size", justify="right")

        for node in orphans:
            size = "-"
            if node.path.exists():
                size_bytes = node.path.stat().st_size
                if size_bytes > 1024 * 1024:
                    size = f"{size_bytes / (1024 * 1024):.1f} MB"
                elif size_bytes > 1024:
                    size = f"{size_bytes / 1024:.1f} KB"
                else:
                    size = f"{size_bytes} B"
            table.add_row(str(node.path.name), node.doc_type, size)

        console.print(table)
        console.print("\n[dim]These assets are not referenced by any document.[/dim]")
        console.print("[dim]Use --cleanup to remove them (dry run by default).[/dim]")
    else:
        console.print("[green]No orphaned assets found.[/green]")

    # Show missing assets
    if missing:
        console.print(f"\n[red]Found {len(missing)} missing assets:[/red]")
        for path, edge in missing:
            console.print(f"  [red]✗[/red] {path.name}")
            console.print(f"    [dim]Referenced by: {edge.source.name}[/dim]")

    # Handle cleanup flag
    if hasattr(args, "cleanup") and args.cleanup:
        dry_run = not getattr(args, "force", False)
        cleaned = registry_manager.cleanup_orphans(dry_run=dry_run)
        if dry_run:
            console.print(f"\n[yellow]Would remove {len(cleaned)} orphan assets (use --force to delete)[/yellow]")
        else:
            console.print(f"\n[green]Removed {len(cleaned)} orphan assets[/green]")


def _show_assets(project, registry, registry_manager, args):
    """Show all tracked assets and their usage."""
    usage = registry_manager.get_asset_usage()

    if hasattr(args, "json") and args.json:
        output = {
            path: [str(p) for p in users]
            for path, users in usage.items()
        }
        print(json.dumps(output, indent=2))
        return

    if not usage:
        console.print("[dim]No assets tracked yet. Run 'relationships refresh' first.[/dim]")
        return

    console.print(Panel(f"[bold]Tracked Assets: {len(usage)}[/bold]", expand=False))

    # Group by type
    by_type = {}
    for path_str, users in usage.items():
        path = Path(path_str)
        suffix = path.suffix.lower()
        asset_type = {
            ".mp4": "video",
            ".webm": "video",
            ".mov": "video",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".svg": "image",
            ".gif": "image",
            ".mp3": "audio",
            ".wav": "audio",
        }.get(suffix, "other")

        if asset_type not in by_type:
            by_type[asset_type] = []
        by_type[asset_type].append((path, users))

    for asset_type, assets in sorted(by_type.items()):
        console.print(f"\n[bold]{asset_type.upper()}[/bold] ({len(assets)} assets)")
        table = Table(box=box.SIMPLE)
        table.add_column("Asset", style="cyan")
        table.add_column("Used By", justify="right")
        table.add_column("Status")

        for path, users in sorted(assets, key=lambda x: -len(x[1])):
            status = "[green]✓[/green]" if path.exists() else "[red]✗ missing[/red]"
            table.add_row(path.name, str(len(users)), status)

        console.print(table)


__all__ = ["cmd_relationships"]
