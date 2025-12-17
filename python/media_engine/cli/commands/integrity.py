"""Integrity command - asset and terminology integrity."""

import json
import sys
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_integrity(args):
    """Asset and terminology integrity."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...integrity import AssetIntegrityChecker, TerminologyChecker

    if args.integrity_command == "verify":
        checker = AssetIntegrityChecker(project)
        results = checker.verify_all()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            console.print("[bold]Asset Integrity Check[/bold]")
            console.print(f"  Valid: {len(results['valid'])}")
            console.print(f"  Modified: {len(results['modified'])}")
            console.print(f"  Missing: {len(results['missing'])}")
            console.print(f"  Untracked: {len(results['untracked'])}")

            if results["modified"]:
                console.print("\n[bold red]Modified assets:[/bold red]")
                for item in results["modified"]:
                    console.print(f"  {item['path']}")

    elif args.integrity_command == "record":
        checker = AssetIntegrityChecker(project)
        count = checker.record_all()
        console.print(f"[green]Recorded checksums for {count} assets[/green]")

    elif args.integrity_command == "terms":
        checker = TerminologyChecker(project)
        issues = checker.check_all_documents()

        if args.json:
            print(json.dumps(issues, indent=2))
        else:
            total = sum(len(i) for i in issues.values())
            console.print(f"[bold]Terminology Check ({total} issues):[/bold]")
            for doc_path, doc_issues in issues.items():
                console.print(f"\n  {Path(doc_path).name}:")
                for issue in doc_issues[:3]:
                    console.print(f"    Avoid '{issue['found']}', prefer '{issue['preferred']}'")

    else:
        console.print("[yellow]Usage: media-engine integrity <verify|record|terms>[/yellow]")
