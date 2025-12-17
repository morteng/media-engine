"""Provenance command - provenance and approval tracking."""

import json
import sys

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_provenance(args):
    """Provenance and approval tracking."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...provenance import ProvenanceTracker

    tracker = ProvenanceTracker(project)

    if args.provenance_command == "report":
        report = tracker.generate_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            console.print("[bold]Provenance Report[/bold]")
            console.print(f"  Documents tracked: {report['summary']['total_documents']}")
            console.print(f"  Total claims: {report['summary']['total_claims']}")
            console.print(f"  Verified: {report['summary']['verified_claims']}")
            console.print(f"  Unverified: {report['summary']['unverified_claims']}")
            console.print(f"  Expired: {report['summary']['expired_claims']}")
            console.print(f"  Expiring soon: {report['summary']['expiring_soon']}")
            console.print("\n[bold]By Status:[/bold]")
            for status, count in report["by_status"].items():
                console.print(f"  {status}: {count}")

    elif args.provenance_command == "claims":
        unverified = tracker.get_all_unverified()
        expired = tracker.get_all_expired()
        expiring = tracker.get_expiring_soon()

        if args.json:
            print(
                json.dumps(
                    {
                        "unverified": [(str(p), c.to_dict()) for p, c in unverified],
                        "expired": [(str(p), c.to_dict()) for p, c in expired],
                        "expiring_soon": [(str(p), c.to_dict()) for p, c in expiring],
                    },
                    indent=2,
                )
            )
        else:
            if unverified:
                console.print(f"[bold yellow]Unverified Claims ({len(unverified)}):[/bold yellow]")
                for path, claim in unverified[:10]:
                    console.print(f"  {path.name}: {claim.text[:50]}...")
            if expired:
                console.print(f"[bold red]Expired Claims ({len(expired)}):[/bold red]")
                for path, claim in expired[:10]:
                    console.print(f"  {path.name}: {claim.text[:50]}...")
            if expiring:
                console.print(f"[bold yellow]Expiring Soon ({len(expiring)}):[/bold yellow]")
                for path, claim in expiring[:10]:
                    days = claim.days_until_expiry()
                    console.print(f"  {path.name}: {claim.text[:50]}... ({days}d)")

    elif args.provenance_command == "queue":
        queue = tracker.get_review_queue()
        if args.json:
            print(json.dumps([str(p) for p in queue], indent=2))
        else:
            console.print(f"[bold]Review Queue ({len(queue)} documents):[/bold]")
            for doc_path in queue:
                console.print(f"  {doc_path.name}")

    else:
        console.print("[yellow]Usage: media-engine provenance <report|claims|queue>[/yellow]")
