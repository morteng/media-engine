"""Hierarchy commands - document hierarchy using the Unified Relationship Registry."""

import json
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from ...core import find_project

console = Console()


def cmd_hierarchy(args):
    """Entry point for hierarchy commands."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...relationships import get_registry_manager, init_registry_manager

    registry_manager = get_registry_manager(project)
    if registry_manager is None:
        registry_manager = init_registry_manager(project)

    # Handle subcommands
    if hasattr(args, "hierarchy_command"):
        if args.hierarchy_command == "status":
            _show_status(registry_manager, args)
        elif args.hierarchy_command == "tree":
            _show_tree(registry_manager, args)
        elif args.hierarchy_command == "stale":
            _show_stale(registry_manager, args)
        elif args.hierarchy_command == "validate":
            _validate_hierarchy(registry_manager, args)
        elif args.hierarchy_command == "refresh":
            _refresh_hierarchy(registry_manager, args)
        elif args.hierarchy_command == "nav":
            _show_navigation(registry_manager, args)
        elif args.hierarchy_command == "anchors":
            _show_anchors(registry_manager, args)
        elif args.hierarchy_command == "impact":
            _show_impact(registry_manager, args)
        elif args.hierarchy_command == "coverage":
            _show_coverage(registry_manager, args)
        else:
            _show_status(registry_manager, args)
    else:
        _show_status(registry_manager, args)


def _show_status(manager, args):
    """Show hierarchy status overview."""
    report = manager.registry.generate_report()

    if hasattr(args, "json") and args.json:
        print(json.dumps(report, indent=2))
        return

    summary = report["summary"]

    summary_text = f"""[bold]Total documents:[/bold] {summary['total_documents']}
[bold]Root documents:[/bold] {summary['root_documents']}
[yellow]Stale documents:[/yellow] {summary['stale_documents']}
[bold]Consistency anchors:[/bold] {summary['anchors']}"""

    console.print(Panel(summary_text, title="Document Hierarchy", expand=False))

    # Type breakdown
    by_type = report.get("by_doc_type", {})
    if by_type:
        console.print("\n[bold]By Document Type:[/bold]")
        type_table = Table(show_header=False, box=box.SIMPLE)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right")
        for doc_type, count in sorted(by_type.items()):
            type_table.add_row(doc_type, str(count))
        console.print(type_table)

    # Lifecycle breakdown
    by_lifecycle = report.get("by_lifecycle", {})
    if by_lifecycle:
        console.print("\n[bold]By Lifecycle:[/bold]")
        lifecycle_table = Table(show_header=False, box=box.SIMPLE)
        lifecycle_table.add_column("Lifecycle", style="green")
        lifecycle_table.add_column("Count", justify="right")
        for lifecycle, count in sorted(by_lifecycle.items()):
            lifecycle_table.add_row(lifecycle, str(count))
        console.print(lifecycle_table)


def _show_tree(manager, args):
    """Show hierarchy as ASCII tree."""
    registry = manager.registry

    root_path = None
    if hasattr(args, "root") and args.root:
        root_path = Path(args.root)

    if hasattr(args, "dot") and args.dot:
        # Output DOT format for Graphviz
        print(_generate_dot(registry))
        return

    # Build tree structure
    roots = registry.get_roots()
    if not roots:
        console.print("[yellow]No hierarchy data found. Run 'media-engine hierarchy refresh' first.[/yellow]")
        return

    # Filter to specific root if specified
    if root_path:
        matching_roots = [r for r in roots if str(root_path) in str(r)]
        if matching_roots:
            roots = matching_roots

    # Build Rich tree
    for root in sorted(roots):
        tree = _build_rich_tree(registry, root)
        if tree:
            console.print(tree)
            console.print()


def _build_rich_tree(registry, root_path, visited=None) -> Tree:
    """Build a Rich Tree from registry hierarchy."""
    if visited is None:
        visited = set()

    path_str = str(root_path)
    if path_str in visited:
        return None
    visited.add(path_str)

    node = registry.get_node(root_path)
    if not node:
        return None

    # Create tree node with status indicator
    status = "[red]●[/red] " if node.is_stale else "[green]●[/green] "
    title = node.title or root_path.stem
    label = f"{status}[bold]{title}[/bold] [dim]({root_path.name})[/dim]"

    tree = Tree(label)

    # Add children
    children = registry.get_children(root_path)
    for child_path in sorted(children):
        child_tree = _build_rich_tree(registry, child_path, visited.copy())
        if child_tree:
            tree.add(child_tree)

    return tree


def _show_stale(manager, args):
    """Show stale documents."""
    stale_docs = manager.get_stale_documents()

    if hasattr(args, "json") and args.json:
        output = [
            {
                "path": str(doc.path),
                "title": doc.title,
                "reasons": doc.stale_reasons,
            }
            for doc in stale_docs
        ]
        print(json.dumps(output, indent=2))
        return

    total_docs = len(list(manager.registry.all_nodes()))
    stale_count = len(stale_docs)
    stale_pct = (stale_count / total_docs * 100) if total_docs > 0 else 0

    summary_text = f"""[bold]Total documents:[/bold] {total_docs}
[yellow]Stale documents:[/yellow] {stale_count}
[dim]Stale percentage:[/dim] {stale_pct:.1f}%"""

    console.print(Panel(summary_text, title="Staleness Report", expand=False))

    if stale_docs:
        console.print("\n[bold]Stale Documents:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Document", style="cyan")
        table.add_column("Reasons", style="yellow")

        for doc in stale_docs:
            reasons = ", ".join(doc.stale_reasons[:3]) if doc.stale_reasons else "-"
            if doc.stale_reasons and len(doc.stale_reasons) > 3:
                reasons += f" (+{len(doc.stale_reasons) - 3} more)"
            table.add_row(
                doc.title or doc.path.name,
                reasons,
            )

        console.print(table)
    else:
        console.print("\n[green]✓ No stale documents[/green]")


def _validate_hierarchy(manager, args):
    """Validate hierarchy structure."""
    registry = manager.registry

    errors = []
    warnings = []

    # Check for circular references
    for node in registry.all_nodes():
        ancestors = registry.get_ancestors(node.path)
        if node.path in ancestors:
            errors.append({
                "type": "circular_reference",
                "document": str(node.path),
                "message": "Document is its own ancestor"
            })

    # Check for orphan references
    for node in registry.all_nodes():
        for edge in registry.get_outgoing_edges(node.path):
            target_node = registry.get_node(edge.target)
            if not target_node:
                warnings.append({
                    "type": "broken_reference",
                    "document": str(node.path),
                    "message": f"References non-existent document: {edge.target}"
                })

    if hasattr(args, "json") and args.json:
        print(json.dumps({
            "is_valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }, indent=2))
        return

    status = "[green]Valid[/green]" if not errors else "[red]Invalid[/red]"
    summary_text = f"""[bold]Status:[/bold] {status}
[red]Errors:[/red] {len(errors)}
[yellow]Warnings:[/yellow] {len(warnings)}"""

    console.print(Panel(summary_text, title="Hierarchy Validation", expand=False))

    if errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in errors:
            console.print(f"  [red]•[/red] [{error['type']}] {Path(error['document']).name}: {error['message']}")

    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  [yellow]•[/yellow] [{warning['type']}] {Path(warning['document']).name}: {warning['message']}")

    if not errors and not warnings:
        console.print("\n[green]✓ Hierarchy is valid with no warnings[/green]")


def _refresh_hierarchy(manager, args):
    """Refresh hierarchy from document frontmatter."""
    console.print("[bold]Refreshing registry from documents...[/bold]")

    result = manager.refresh()

    console.print(f"[green]✓[/green] Loaded {result['documents']} documents")
    console.print(f"[green]✓[/green] Found {result['relationships']} relationships")
    console.print(f"[green]✓[/green] Elapsed: {result['elapsed_seconds']:.2f}s")


def _show_navigation(manager, args):
    """Show navigation context for a document."""
    if not hasattr(args, "document") or not args.document:
        console.print("[red]Please specify a document path with --document[/red]")
        sys.exit(1)

    registry = manager.registry
    doc_path = Path(args.document)

    # Resolve path
    if not doc_path.is_absolute():
        doc_path = manager.project.content_dir / args.document
        if not doc_path.exists():
            doc_path = doc_path.with_suffix(".md")

    node = registry.get_node(doc_path)
    if not node:
        console.print(f"[red]Document not found in hierarchy: {doc_path}[/red]")
        sys.exit(1)

    # Get navigation info
    parent = registry.get_parent(doc_path)
    children = registry.get_children(doc_path)
    ancestors = registry.get_ancestors(doc_path)
    siblings = registry.get_children(parent) if parent else []
    siblings = [s for s in siblings if s != doc_path]

    # Get position in siblings
    all_siblings = registry.get_children(parent) if parent else []
    position = 1
    for i, s in enumerate(sorted(all_siblings)):
        if s == doc_path:
            position = i + 1
            break

    if hasattr(args, "json") and args.json:
        print(json.dumps({
            "path": str(doc_path),
            "title": node.title,
            "position": position,
            "total_siblings": len(all_siblings),
            "parent": str(parent) if parent else None,
            "ancestors": [str(a) for a in ancestors],
            "children": [str(c) for c in children],
            "siblings": [str(s) for s in siblings],
        }, indent=2))
        return

    # Breadcrumbs
    breadcrumb_parts = []
    for ancestor in reversed(ancestors):
        ancestor_node = registry.get_node(ancestor)
        if ancestor_node:
            breadcrumb_parts.append(ancestor_node.title or ancestor.stem)
    breadcrumb_parts.append(node.title or doc_path.stem)
    breadcrumb_str = " > ".join(breadcrumb_parts)

    console.print(Panel(breadcrumb_str, title="Breadcrumbs", expand=False))

    # Navigation info
    nav_text = f"""[bold]Title:[/bold] {node.title}
[bold]Position:[/bold] {position} of {len(all_siblings)}"""

    if parent:
        parent_node = registry.get_node(parent)
        parent_title = parent_node.title if parent_node else parent.stem
        nav_text += f"\n[bold]Parent:[/bold] {parent_title}"

    # Previous/Next siblings
    sorted_siblings = sorted(all_siblings)
    idx = sorted_siblings.index(doc_path) if doc_path in sorted_siblings else -1
    if idx > 0:
        prev_node = registry.get_node(sorted_siblings[idx - 1])
        nav_text += f"\n[bold]Previous:[/bold] {prev_node.title if prev_node else sorted_siblings[idx-1].stem}"
    if idx >= 0 and idx < len(sorted_siblings) - 1:
        next_node = registry.get_node(sorted_siblings[idx + 1])
        nav_text += f"\n[bold]Next:[/bold] {next_node.title if next_node else sorted_siblings[idx+1].stem}"

    console.print(Panel(nav_text, title="Navigation", expand=False))

    if children:
        console.print("\n[bold]Children:[/bold]")
        for child in sorted(children):
            child_node = registry.get_node(child)
            child_title = child_node.title if child_node else child.stem
            console.print(f"  • {child_title} ({child.name})")


def _show_anchors(manager, args):
    """Show consistency anchors."""
    registry = manager.registry

    # Load anchor data from registry file
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

    summary = {
        "total_anchors": len(anchors_data),
        "total_references": sum(len(a.get("referenced_in", [])) for a in anchors_data.values()),
    }

    summary_text = f"""[bold]Total anchors:[/bold] {summary['total_anchors']}
[bold]Total references:[/bold] {summary['total_references']}"""

    console.print(Panel(summary_text, title="Consistency Anchors", expand=False))

    if anchors_data:
        console.print("\n[bold]Defined Anchors:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Anchor", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Document")
        table.add_column("Referenced By", justify="right")

        for anchor_id, anchor in anchors_data.items():
            defined_in = Path(anchor.get("defined_in", "")).name
            refs = len(anchor.get("referenced_in", []))
            value_str = str(anchor.get("value", ""))
            if len(value_str) > 30:
                value_str = value_str[:27] + "..."

            table.add_row(anchor_id, value_str, defined_in, str(refs))

        console.print(table)


def _show_impact(manager, args):
    """Show impact analysis for a document change."""
    if not hasattr(args, "document") or not args.document:
        console.print("[red]Please specify a document path with --document[/red]")
        sys.exit(1)

    registry = manager.registry
    doc_path = Path(args.document)

    # Resolve path
    if not doc_path.is_absolute():
        # Try to find in registry
        for node in registry.all_nodes():
            if str(doc_path) in str(node.path) or node.path.name == args.document:
                doc_path = node.path
                break
        else:
            doc_path = manager.project.content_dir / args.document
            if not doc_path.exists():
                doc_path = doc_path.with_suffix(".md")

    # Get impact set
    affected = manager.get_impact(doc_path)

    if hasattr(args, "json") and args.json:
        print(json.dumps({
            "changed_document": str(doc_path),
            "total_impacted": len(affected),
            "affected": [str(p) for p in affected],
        }, indent=2))
        return

    summary_text = f"""[bold]Changed document:[/bold] {doc_path.name}
[bold]Total impacted:[/bold] {len(affected)}"""

    console.print(Panel(summary_text, title="Impact Analysis", expand=False))

    if affected:
        console.print("\n[bold]Impacted Documents:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Document", style="cyan")
        table.add_column("Type")
        table.add_column("Relationship")

        for affected_path in sorted(affected):
            node = registry.get_node(affected_path)
            if node:
                # Find what relationship connects them
                edges = registry.get_outgoing_edges(affected_path)
                rel_types = [e.edge_type.value for e in edges if e.target == doc_path]

                table.add_row(
                    node.title or affected_path.name,
                    node.doc_type or "document",
                    ", ".join(rel_types) if rel_types else "-",
                )

        console.print(table)
    else:
        console.print("\n[green]No documents are impacted by changes to this file.[/green]")


def _show_coverage(manager, args):
    """Show coverage analysis."""
    registry = manager.registry

    # Calculate coverage metrics
    all_nodes = list(registry.all_nodes())
    total = len(all_nodes)
    roots = len(registry.get_roots())
    orphans = len([n for n in all_nodes if not registry.get_parent(n.path) and not registry.get_children(n.path)])
    with_deps = len([n for n in all_nodes if registry.get_outgoing_edges(n.path)])

    coverage_score = ((total - orphans) / total * 100) if total > 0 else 0

    if hasattr(args, "json") and args.json:
        print(json.dumps({
            "coverage_score": coverage_score,
            "total_documents": total,
            "root_documents": roots,
            "orphan_documents": orphans,
            "documents_with_dependencies": with_deps,
        }, indent=2))
        return

    score_color = "green" if coverage_score >= 80 else "yellow" if coverage_score >= 60 else "red"
    summary_text = f"""[bold]Coverage Score:[/bold] [{score_color}]{coverage_score:.1f}%[/{score_color}]
[bold]Total documents:[/bold] {total}
[bold]Root documents:[/bold] {roots}
[bold]Orphan documents:[/bold] {orphans}
[bold]With dependencies:[/bold] {with_deps}"""

    console.print(Panel(summary_text, title="Documentation Coverage", expand=False))


def _generate_dot(registry) -> str:
    """Generate DOT format for Graphviz."""
    lines = ["digraph hierarchy {"]
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box, fontname=Arial];")
    lines.append("  edge [fontname=Arial, fontsize=10];")

    colors = {
        "parent": "black",
        "implements": "green",
        "extends": "blue",
        "summarizes": "purple",
        "translates": "orange",
        "references": "gray",
    }

    for node in registry.all_nodes():
        for edge in registry.get_outgoing_edges(node.path):
            source = node.path.stem
            target = edge.target.stem
            edge_type = edge.edge_type.value
            color = colors.get(edge_type, "gray")
            style = ", style=dashed" if edge.is_stale else ""

            lines.append(f'  "{source}" -> "{target}" [color={color}, label="{edge_type}"{style}];')

    lines.append("}")
    return "\n".join(lines)


def setup_parser(subparsers):
    """Setup the hierarchy command parser."""
    parser = subparsers.add_parser("hierarchy", help="Document hierarchy management")

    hierarchy_subparsers = parser.add_subparsers(dest="hierarchy_command")

    # status
    status_parser = hierarchy_subparsers.add_parser("status", help="Show hierarchy status")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # tree
    tree_parser = hierarchy_subparsers.add_parser("tree", help="Show hierarchy tree")
    tree_parser.add_argument("--root", help="Root document path")
    tree_parser.add_argument("--dot", action="store_true", help="Output DOT format for Graphviz")

    # stale
    stale_parser = hierarchy_subparsers.add_parser("stale", help="Show stale documents")
    stale_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # validate
    validate_parser = hierarchy_subparsers.add_parser("validate", help="Validate hierarchy structure")
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # refresh
    hierarchy_subparsers.add_parser("refresh", help="Refresh hierarchy from documents")

    # nav
    nav_parser = hierarchy_subparsers.add_parser("nav", help="Show navigation context for a document")
    nav_parser.add_argument("--document", "-d", required=True, help="Document path")
    nav_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # anchors
    anchors_parser = hierarchy_subparsers.add_parser("anchors", help="Show consistency anchors")
    anchors_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # impact
    impact_parser = hierarchy_subparsers.add_parser("impact", help="Analyze impact of document changes")
    impact_parser.add_argument("--document", "-d", required=True, help="Document path to analyze")
    impact_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # coverage
    coverage_parser = hierarchy_subparsers.add_parser("coverage", help="Analyze documentation coverage")
    coverage_parser.add_argument("--json", action="store_true", help="Output as JSON")

    parser.set_defaults(func=cmd_hierarchy)
    return parser
