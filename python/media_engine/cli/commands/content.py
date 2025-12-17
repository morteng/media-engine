"""Content commands - readability, gaps, links, security, changelog."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_readability(args):
    """Readability analysis."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...readability import ReadabilityLevel, check_readability

    target = ReadabilityLevel(args.target) if args.target else ReadabilityLevel.HIGH_SCHOOL
    report = check_readability(project, target_level=target)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print("[bold]Readability Analysis[/bold]")
        console.print(f"  Target level: {report['target_level']}")
        console.print(f"  Documents: {s['total_documents']}")
        console.print(f"  Passing: {s['passing']} ({s['pass_rate']}%)")
        console.print(f"  Average grade level: {s['average_grade_level']}")
        console.print(f"  Total reading time: {s['total_reading_time_minutes']:.1f} min")

        if s["failing"] > 0:
            console.print("\n[yellow]Documents above target level:[/yellow]")
            for doc in report["documents"]:
                if not doc["passes_target"]:
                    console.print(f"  {doc['file']}: grade {doc['grade_level']}")


def cmd_gaps(args):
    """Content gap analysis."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...gaps import analyze_gaps

    topics = args.topics.split(",") if args.topics else []
    report = analyze_gaps(project, expected_topics=topics)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print("[bold]Content Gap Analysis[/bold]")
        console.print(f"  Total gaps found: {s['total_gaps']}")
        console.print(f"  Critical: {s['critical']}")
        console.print(f"  High: {s['high']}")
        console.print(f"  Medium: {s['medium']}")
        console.print(f"  Low: {s['low']}")

        if s["total_gaps"] > 0:
            console.print("\n[bold]By Type:[/bold]")
            for gap_type, gaps in report["by_type"].items():
                console.print(f"  {gap_type}: {len(gaps)}")


def cmd_links(args):
    """Link validation."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...links import check_links

    console.print("[bold]Checking links...[/bold]")
    report = check_links(project, include_external=not args.internal_only)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print(f"  Total links: {s['total']}")
        console.print(f"  Valid: {s['valid']}")
        console.print(f"  [red]Broken: {s['broken']}[/red]")
        console.print(f"  [yellow]Timeout: {s['timeout']}[/yellow]")

        if report["broken_links"]:
            console.print("\n[bold red]Broken Links:[/bold red]")
            for link in report["broken_links"][:10]:
                console.print(f"  {link['url']}")
                if link["file"]:
                    console.print(f"    in {link['file']}:{link['line']}")


def cmd_security(args):
    """Security scan for sensitive content."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...security import SensitiveContentScanner

    scanner = SensitiveContentScanner()
    report = scanner.scan_project(project, include_assets=args.include_assets)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        console.print("[bold]Security Scan[/bold]")
        console.print(f"  Total findings: {s['total']}")
        console.print(f"  [red]Critical: {s['critical']}[/red]")
        console.print(f"  [yellow]High: {s['high']}[/yellow]")
        console.print(f"  Medium: {s['medium']}")
        console.print(f"  Low: {s['low']}")

        if s["blocks_publish"]:
            console.print("\n[bold red]⚠ CRITICAL ISSUES FOUND - Publishing blocked[/bold red]")

        if report["matches"]:
            console.print("\n[bold]Findings:[/bold]")
            for match in report["matches"][:10]:
                level_color = {"critical": "red", "high": "yellow"}.get(match["level"], "white")
                console.print(
                    f"  [{level_color}]{match['pattern']}[/{level_color}]: {match['redacted']}"
                )
                if match["file"]:
                    console.print(f"    in {match['file']}:{match['line']}")


def cmd_changelog(args):
    """Generate changelog."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...changelog import generate_changelog

    since = None
    if args.since:
        since = datetime.fromisoformat(args.since)
    elif args.days:
        since = datetime.now() - timedelta(days=args.days)

    fmt = "json" if args.json else "markdown"
    changelog = generate_changelog(project, since=since, format=fmt)

    if args.output:
        Path(args.output).write_text(changelog)
        console.print(f"[green]Changelog written to {args.output}[/green]")
    else:
        print(changelog)
