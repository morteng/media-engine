"""Hierarchy commands - document hierarchy and information flow."""

import json
import sys

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

    # Import here to avoid circular imports
    from ...hierarchy import HierarchyGraph, HierarchyValidator, StalenessChecker

    graph = HierarchyGraph(project)

    # Handle subcommands
    if hasattr(args, "hierarchy_command"):
        if args.hierarchy_command == "status":
            _show_status(graph, args)
        elif args.hierarchy_command == "tree":
            _show_tree(graph, args)
        elif args.hierarchy_command == "stale":
            _show_stale(graph, args)
        elif args.hierarchy_command == "validate":
            _validate_hierarchy(graph, args)
        elif args.hierarchy_command == "refresh":
            _refresh_hierarchy(graph, args)
        elif args.hierarchy_command == "nav":
            _show_navigation(graph, args)
        elif args.hierarchy_command == "anchors":
            _show_anchors(graph, args)
        elif args.hierarchy_command == "impact":
            _show_impact(graph, args)
        elif args.hierarchy_command == "coverage":
            _show_coverage(graph, args)
        else:
            _show_status(graph, args)
    else:
        _show_status(graph, args)


def _show_status(graph, args):
    """Show hierarchy status overview."""
    report = graph.registry.generate_report()

    if hasattr(args, "json") and args.json:
        print(json.dumps(report, indent=2))
        return

    # Summary panel
    summary = report["summary"]
    by_type = report.get("by_type", {})
    by_lifecycle = report.get("by_lifecycle", {})

    summary_text = f"""[bold]Total documents:[/bold] {summary['total_nodes']}
[bold]Root documents:[/bold] {summary['root_count']}
[yellow]Stale documents:[/yellow] {summary['stale_count']}
[bold]Consistency anchors:[/bold] {summary['anchor_count']}"""

    console.print(Panel(summary_text, title="Document Hierarchy", expand=False))

    # Type breakdown
    if by_type:
        console.print("\n[bold]By Document Type:[/bold]")
        type_table = Table(show_header=False, box=box.SIMPLE)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right")
        for doc_type, count in sorted(by_type.items()):
            type_table.add_row(doc_type, str(count))
        console.print(type_table)

    # Lifecycle breakdown
    if by_lifecycle:
        console.print("\n[bold]By Lifecycle:[/bold]")
        lifecycle_table = Table(show_header=False, box=box.SIMPLE)
        lifecycle_table.add_column("Lifecycle", style="green")
        lifecycle_table.add_column("Count", justify="right")
        for lifecycle, count in sorted(by_lifecycle.items()):
            lifecycle_table.add_row(lifecycle, str(count))
        console.print(lifecycle_table)


def _show_tree(graph, args):
    """Show hierarchy as ASCII tree."""
    root_path = None
    if hasattr(args, "root") and args.root:
        from pathlib import Path

        root_path = Path(args.root)

    if hasattr(args, "dot") and args.dot:
        # Output DOT format for Graphviz
        print(graph.to_dot())
        return

    # ASCII tree
    tree_str = graph.to_tree_string(root_path)

    if not tree_str.strip():
        console.print("[yellow]No hierarchy data found. Run 'media-engine hierarchy refresh' first.[/yellow]")
        return

    console.print(Panel(tree_str, title="Document Hierarchy Tree", expand=False))


def _show_stale(graph, args):
    """Show stale documents."""
    from ...hierarchy import StalenessChecker

    checker = StalenessChecker(graph)
    report = checker.check_all()

    if hasattr(args, "json") and args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Summary
    summary_text = f"""[bold]Total documents:[/bold] {report.total_documents}
[yellow]Stale documents:[/yellow] {report.stale_count}
[dim]Stale percentage:[/dim] {report.stale_percentage:.1f}%"""

    console.print(Panel(summary_text, title="Staleness Report", expand=False))

    # Stale documents table
    if report.stale_documents:
        console.print("\n[bold]Stale Documents:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Document", style="cyan")
        table.add_column("Reason", style="yellow")
        table.add_column("Stale Sources")

        for info in report.stale_documents:
            sources = ", ".join(str(s.name) for s in info.stale_sources[:3])
            if len(info.stale_sources) > 3:
                sources += f" (+{len(info.stale_sources) - 3} more)"
            table.add_row(
                str(info.document.name),
                info.reason.value,
                sources or "-",
            )

        console.print(table)

    # By reason breakdown
    if report.by_reason:
        console.print("\n[bold]By Reason:[/bold]")
        for reason, count in report.by_reason.items():
            console.print(f"  {reason}: {count}")


def _validate_hierarchy(graph, args):
    """Validate hierarchy structure."""
    from ...hierarchy import HierarchyValidator

    validator = HierarchyValidator(graph)
    result = validator.validate_all()

    if hasattr(args, "json") and args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    # Summary
    status = "[green]Valid[/green]" if result.is_valid else "[red]Invalid[/red]"
    summary_text = f"""[bold]Status:[/bold] {status}
[red]Errors:[/red] {result.error_count}
[yellow]Warnings:[/yellow] {result.warning_count}"""

    console.print(Panel(summary_text, title="Hierarchy Validation", expand=False))

    # Errors table
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  [red]•[/red] [{error.error_type}] {error.document.name}: {error.message}")

    # Warnings table
    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]•[/yellow] [{warning.error_type}] {warning.document.name}: {warning.message}")

    if result.is_valid and not result.warnings:
        console.print("\n[green]✓ Hierarchy is valid with no warnings[/green]")


def _refresh_hierarchy(graph, args):
    """Refresh hierarchy from document frontmatter."""
    console.print("[bold]Refreshing hierarchy from documents...[/bold]")

    graph.refresh()
    report = graph.registry.generate_report()

    console.print(f"[green]✓[/green] Loaded {report['summary']['total_nodes']} documents")
    console.print(f"[green]✓[/green] Found {report['summary']['root_count']} root documents")
    console.print(f"[green]✓[/green] Registered {report['summary']['anchor_count']} consistency anchors")


def _show_navigation(graph, args):
    """Show navigation context for a document."""
    from pathlib import Path

    if not hasattr(args, "document") or not args.document:
        console.print("[red]Please specify a document path with --document[/red]")
        sys.exit(1)

    doc_path = Path(args.document)
    context = graph.get_navigation_context(doc_path)

    if not context:
        console.print(f"[red]Document not found in hierarchy: {doc_path}[/red]")
        sys.exit(1)

    if hasattr(args, "json") and args.json:
        print(json.dumps(context.to_dict(), indent=2))
        return

    # Breadcrumbs
    breadcrumb_str = graph.format_breadcrumb_string(doc_path)
    console.print(Panel(breadcrumb_str, title="Breadcrumbs", expand=False))

    # Navigation info
    nav_text = f"""[bold]Title:[/bold] {context.title}
[bold]Position:[/bold] {context.position_in_siblings} of {context.total_siblings}"""

    if context.parent:
        nav_text += f"\n[bold]Parent:[/bold] {context.parent.title}"

    if context.previous_sibling:
        nav_text += f"\n[bold]Previous:[/bold] {context.previous_sibling.name}"

    if context.next_sibling:
        nav_text += f"\n[bold]Next:[/bold] {context.next_sibling.name}"

    console.print(Panel(nav_text, title="Navigation", expand=False))

    # Children
    if context.children:
        console.print("\n[bold]Children:[/bold]")
        for child in context.children:
            console.print(f"  • {child.title} ({child.path.name})")


def _show_anchors(graph, args):
    """Show consistency anchors."""
    from pathlib import Path

    from ...hierarchy import AnchorRegistry

    anchor_registry = AnchorRegistry(graph.registry)
    anchor_registry.build()

    if hasattr(args, "validate") and args.validate:
        # Validate references
        result = anchor_registry.validate_references()

        if hasattr(args, "json") and args.json:
            print(
                json.dumps(
                    {
                        "valid": result.valid,
                        "missing_anchors": [
                            {"ref_doc": str(r), "anchor": a, "source": str(s)}
                            for r, a, s in result.missing_anchors
                        ],
                        "value_mismatches": [
                            {"ref_doc": str(r), "anchor": a, "expected": e, "actual": act}
                            for r, a, e, act in result.value_mismatches
                        ],
                        "orphan_references": [
                            {"ref_doc": str(r), "anchor": a}
                            for r, a in result.orphan_references
                        ],
                    },
                    indent=2,
                )
            )
            return

        status = "[green]Valid[/green]" if result.valid else "[red]Invalid[/red]"
        console.print(Panel(f"[bold]Anchor References:[/bold] {status}", title="Anchor Validation", expand=False))

        if result.missing_anchors:
            console.print("\n[bold red]Missing Anchors:[/bold red]")
            for ref_doc, anchor, source in result.missing_anchors:
                console.print(f"  [red]•[/red] {ref_doc.name} references '{anchor}' in {source} (not found)")

        if result.orphan_references:
            console.print("\n[bold yellow]Orphan References:[/bold yellow]")
            for ref_doc, anchor in result.orphan_references:
                console.print(f"  [yellow]•[/yellow] {ref_doc.name} references '{anchor}' (source document not found)")

        if result.value_mismatches:
            console.print("\n[bold yellow]Value Mismatches:[/bold yellow]")
            for ref_doc, anchor, expected, actual in result.value_mismatches:
                console.print(f"  [yellow]•[/yellow] {ref_doc.name}:{anchor} expected '{expected}', actual '{actual}'")

        if result.valid and not result.value_mismatches:
            console.print("\n[green]All anchor references are valid[/green]")
        return

    # Default: show all anchors
    if hasattr(args, "json") and args.json:
        summary = anchor_registry.get_impact_summary()
        anchors = []
        for anchor in anchor_registry.get_all_anchors():
            refs = anchor_registry.get_referencing_documents(anchor.document_path, anchor.name)
            anchors.append(
                {
                    "name": anchor.name,
                    "value": anchor.value,
                    "document": str(anchor.document_path),
                    "description": anchor.description,
                    "referenced_by": [str(r) for r in refs],
                }
            )
        print(json.dumps({"summary": summary, "anchors": anchors}, indent=2))
        return

    summary = anchor_registry.get_impact_summary()

    summary_text = f"""[bold]Total anchors:[/bold] {summary['total_anchors']}
[bold]Total references:[/bold] {summary['total_references']}
[bold]Documents with anchors:[/bold] {summary['documents_with_anchors']}
[bold]Documents with refs:[/bold] {summary['documents_with_refs']}"""

    console.print(Panel(summary_text, title="Consistency Anchors", expand=False))

    # Anchor table
    all_anchors = anchor_registry.get_all_anchors()
    if all_anchors:
        console.print("\n[bold]Defined Anchors:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Anchor", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Document")
        table.add_column("Referenced By", justify="right")

        for anchor in all_anchors:
            refs = anchor_registry.get_referencing_documents(anchor.document_path, anchor.name)
            value_str = str(anchor.value)
            if len(value_str) > 30:
                value_str = value_str[:27] + "..."
            table.add_row(
                anchor.name,
                value_str,
                anchor.document_path.name if hasattr(anchor.document_path, "name") else str(anchor.document_path),
                str(len(refs)),
            )

        console.print(table)

    # Most referenced
    if summary.get("most_referenced"):
        console.print("\n[bold]Most Referenced:[/bold]")
        for key, count in summary["most_referenced"][:5]:
            doc, anchor = key.rsplit(":", 1)
            console.print(f"  {anchor} ({Path(doc).name}): {count} refs")


def _show_impact(graph, args):
    """Show impact analysis for a document change."""
    from pathlib import Path

    from ...hierarchy import ImpactAnalyzer

    if not hasattr(args, "document") or not args.document:
        console.print("[red]Please specify a document path with --document[/red]")
        sys.exit(1)

    # Resolve document path
    doc_path = Path(args.document)
    if not doc_path.is_absolute():
        # Try to find the document in the registry
        found = False
        for node_path in graph.registry._nodes:
            if node_path.endswith(str(doc_path)) or str(doc_path) in node_path:
                doc_path = Path(node_path)
                found = True
                break
        if not found:
            # Fall back to resolving relative to CWD
            doc_path = doc_path.resolve()

    analyzer = ImpactAnalyzer(graph)

    # Analyze change type
    change_type = getattr(args, "change_type", "content") or "content"
    description = getattr(args, "description", "") or f"Change to {doc_path.name}"

    if change_type == "delete":
        report = analyzer.analyze_deletion(doc_path)
    else:
        report = analyzer.analyze_change(doc_path, change_type, description)

    if hasattr(args, "json") and args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Summary panel
    status = "[red]Critical impacts![/red]" if report.has_critical else "[green]No critical impacts[/green]"
    summary_text = f"""[bold]Changed document:[/bold] {report.changed_document.name}
[bold]Change type:[/bold] {report.change_type}
[bold]Total impacted:[/bold] {report.total_impacted}
{status}"""

    console.print(Panel(summary_text, title="Impact Analysis", expand=False))

    # By severity
    by_sev = report.by_severity
    if any(v > 0 for v in by_sev.values()):
        console.print("\n[bold]By Severity:[/bold]")
        if by_sev["critical"] > 0:
            console.print(f"  [red]Critical:[/red] {by_sev['critical']}")
        if by_sev["high"] > 0:
            console.print(f"  [yellow]High:[/yellow] {by_sev['high']}")
        if by_sev["medium"] > 0:
            console.print(f"  [blue]Medium:[/blue] {by_sev['medium']}")
        if by_sev["low"] > 0:
            console.print(f"  [dim]Low:[/dim] {by_sev['low']}")

    # Impacted documents table
    if report.impacted_documents:
        console.print("\n[bold]Impacted Documents:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Document", style="cyan")
        table.add_column("Type")
        table.add_column("Severity")
        table.add_column("Reason")
        table.add_column("Action")

        severity_styles = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "dim",
        }

        for item in report.impacted_documents:
            style = severity_styles.get(item.severity.value, "white")
            table.add_row(
                str(item.path.name) if hasattr(item.path, "name") else str(item.path),
                item.impact_type.value,
                f"[{style}]{item.severity.value}[/{style}]",
                item.reason[:40] + "..." if len(item.reason) > 40 else item.reason,
                item.suggested_action[:30] + "..." if len(item.suggested_action) > 30 else item.suggested_action,
            )

        console.print(table)


def _show_coverage(graph, args):
    """Show coverage analysis."""
    from ...hierarchy import CoverageAnalyzer

    analyzer = CoverageAnalyzer(graph)
    report = analyzer.analyze()

    if hasattr(args, "json") and args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Summary panel
    score_color = "green" if report.coverage_score >= 80 else "yellow" if report.coverage_score >= 60 else "red"
    summary_text = f"""[bold]Coverage Score:[/bold] [{score_color}]{report.coverage_score:.1f}%[/{score_color}]
[bold]Total documents:[/bold] {report.total_documents}
[bold]Source documents:[/bold] {report.source_documents}
[bold]Derived documents:[/bold] {report.derived_documents}
[bold]Orphan documents:[/bold] {report.orphan_documents}
[bold]Total gaps:[/bold] {len(report.gaps)}"""

    console.print(Panel(summary_text, title="Documentation Coverage", expand=False))

    # Gaps by severity
    if report.gaps:
        console.print("\n[bold]Gaps by Priority:[/bold]")
        critical = len([g for g in report.gaps if g.priority == "critical"])
        high = len([g for g in report.gaps if g.priority == "high"])
        medium = len([g for g in report.gaps if g.priority == "medium"])
        low = len([g for g in report.gaps if g.priority == "low"])

        if critical > 0:
            console.print(f"  [red]Critical:[/red] {critical}")
        if high > 0:
            console.print(f"  [yellow]High:[/yellow] {high}")
        if medium > 0:
            console.print(f"  [blue]Medium:[/blue] {medium}")
        if low > 0:
            console.print(f"  [dim]Low:[/dim] {low}")

    # Gaps table
    if report.gaps:
        console.print("\n[bold]Coverage Gaps:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Expected")
        table.add_column("Source")
        table.add_column("Suggested Path")
        table.add_column("Priority")

        priority_styles = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "dim",
        }

        for gap in report.gaps[:20]:  # Limit to 20
            style = priority_styles.get(gap.priority, "white")
            table.add_row(
                gap.gap_type,
                gap.expected_doc_type.value if hasattr(gap.expected_doc_type, "value") else str(gap.expected_doc_type),
                str(gap.should_derive_from.name) if hasattr(gap.should_derive_from, "name") else str(gap.should_derive_from)[:30],
                gap.suggested_path[:30] + "..." if len(gap.suggested_path) > 30 else gap.suggested_path,
                f"[{style}]{gap.priority}[/{style}]",
            )

        console.print(table)

        if len(report.gaps) > 20:
            console.print(f"\n[dim]...and {len(report.gaps) - 20} more gaps[/dim]")

    # Suggestions
    if hasattr(args, "suggest") and args.suggest:
        suggestions = analyzer.get_suggestions()
        if suggestions:
            console.print("\n[bold]Suggestions:[/bold]")
            for s in suggestions[:10]:
                console.print(f"  [cyan]{s['priority']}[/cyan]: Create {s['target']}")
                console.print(f"     Reason: {s['reason']}")


def setup_parser(subparsers):
    """Setup the hierarchy command parser."""
    parser = subparsers.add_parser("hierarchy", help="Document hierarchy management")

    # Add subparsers for hierarchy commands
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
    refresh_parser = hierarchy_subparsers.add_parser("refresh", help="Refresh hierarchy from documents")

    # nav
    nav_parser = hierarchy_subparsers.add_parser("nav", help="Show navigation context for a document")
    nav_parser.add_argument("--document", "-d", required=True, help="Document path")
    nav_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # anchors
    anchors_parser = hierarchy_subparsers.add_parser("anchors", help="Show consistency anchors")
    anchors_parser.add_argument("--json", action="store_true", help="Output as JSON")
    anchors_parser.add_argument("--validate", action="store_true", help="Validate anchor references")

    # impact
    impact_parser = hierarchy_subparsers.add_parser("impact", help="Analyze impact of document changes")
    impact_parser.add_argument("--document", "-d", required=True, help="Document path to analyze")
    impact_parser.add_argument(
        "--change-type",
        "-t",
        choices=["content", "metadata", "delete", "anchor"],
        default="content",
        help="Type of change (default: content)",
    )
    impact_parser.add_argument("--description", help="Description of the change")
    impact_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # coverage
    coverage_parser = hierarchy_subparsers.add_parser("coverage", help="Analyze documentation coverage")
    coverage_parser.add_argument("--json", action="store_true", help="Output as JSON")
    coverage_parser.add_argument("--suggest", action="store_true", help="Show suggestions for filling gaps")

    parser.set_defaults(func=cmd_hierarchy)
    return parser
