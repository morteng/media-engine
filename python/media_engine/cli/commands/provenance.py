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

    elif args.provenance_command == "scan":
        console.print("[bold]Scanning documents for potential claims...[/bold]")
        results = tracker.scan_all_documents()

        total_claims = sum(len(claims) for claims in results.values())

        if args.json:
            print(
                json.dumps(
                    {
                        "documents_scanned": len(results),
                        "total_claims_found": total_claims,
                        "by_document": results,
                    },
                    indent=2,
                )
            )
        else:
            if total_claims == 0:
                console.print("[green]No potential claims found[/green]")
            else:
                console.print(
                    f"Found [yellow]{total_claims}[/yellow] potential claims in [cyan]{len(results)}[/cyan] documents:\n"
                )
                for doc_path, claims in list(results.items())[:10]:
                    console.print(f"[bold]{doc_path}[/bold]")
                    for claim in claims[:5]:
                        console.print(f'  [{claim["type"]}] "{claim["match"]}"')
                    if len(claims) > 5:
                        console.print(f"  ... and {len(claims) - 5} more")
                    console.print()

                if len(results) > 10:
                    console.print(f"[dim]... and {len(results) - 10} more documents[/dim]")

                console.print("\nTo add claims for tracking, use the dashboard or MCP tools.")

    elif args.provenance_command == "validate-urls":
        console.print("[bold]Validating external URLs in claims...[/bold]")
        results = tracker.validate_all_urls()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            console.print(f"Total URLs: {results['total_urls']}")
            console.print(f"[green]Valid: {results['valid']}[/green]")
            console.print(f"[red]Invalid: {results['invalid']}[/red]")

            invalid_results = [r for r in results["results"] if not r["valid"]]
            if invalid_results:
                console.print("\n[bold red]Invalid URLs:[/bold red]")
                for result in invalid_results[:10]:
                    console.print(f"  {result['url']}")
                    console.print(f"    Error: {result.get('error', 'Unknown')}")

    elif args.provenance_command == "add":
        if not hasattr(args, "document") or not args.document:
            console.print(
                "[red]Usage: media-engine provenance add --document <path> --claim <text> --source <source>[/red]"
            )
            sys.exit(1)

        from pathlib import Path

        claim = tracker.add_claim(
            document_path=Path(args.document),
            claim_text=args.claim,
            source=args.source,
            source_url=getattr(args, "url", None),
            source_type=getattr(args, "type", "internal"),
        )

        console.print(f"[green]Claim added with ID: {claim.claim_id}[/green]")

    elif args.provenance_command == "verify":
        if (
            not hasattr(args, "document")
            or not args.document
            or not hasattr(args, "claim_id")
            or not args.claim_id
        ):
            console.print(
                "[red]Usage: media-engine provenance verify --document <path> --claim-id <id> --verifier <name>[/red]"
            )
            sys.exit(1)

        from pathlib import Path

        result = tracker.verify_claim(
            document_path=Path(args.document),
            claim_id=args.claim_id,
            verifier=args.verifier,
            expiry_days=getattr(args, "expiry_days", 365),
        )

        if result:
            console.print(f"[green]Claim {args.claim_id} verified by {args.verifier}[/green]")
        else:
            console.print(f"[red]Claim {args.claim_id} not found[/red]")

    else:
        console.print(
            "[yellow]Usage: media-engine provenance <report|claims|queue|scan|validate-urls|add|verify>[/yellow]"
        )
