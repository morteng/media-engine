"""Provenance tracking tools for MCP."""

import json
from pathlib import Path


def register_provenance_tools(mcp, server_instance):
    """Register provenance-related MCP tools."""

    @mcp.tool()
    async def provenance_report() -> str:
        """
        Get comprehensive provenance report for the project.

        Returns summary of claims, verification status, and approval workflow.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        report = tracker.generate_report()

        return json.dumps(report, indent=2)

    @mcp.tool()
    async def provenance_claims(status: str = None) -> str:
        """
        Get claims from the provenance system.

        Args:
            status: Filter by status: 'unverified', 'verified', 'expired', 'expiring' (optional)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)

        if status == "unverified":
            claims = tracker.get_all_unverified()
            return json.dumps(
                {
                    "status": "unverified",
                    "count": len(claims),
                    "claims": [
                        {"document": str(path), "text": claim.text, "source": claim.source}
                        for path, claim in claims
                    ],
                },
                indent=2,
            )
        elif status == "expired":
            claims = tracker.get_all_expired()
            return json.dumps(
                {
                    "status": "expired",
                    "count": len(claims),
                    "claims": [
                        {
                            "document": str(path),
                            "text": claim.text,
                            "expires": claim.expires,
                        }
                        for path, claim in claims
                    ],
                },
                indent=2,
            )
        elif status == "expiring":
            claims = tracker.get_expiring_soon(days=30)
            return json.dumps(
                {
                    "status": "expiring_soon",
                    "count": len(claims),
                    "claims": [
                        {
                            "document": str(path),
                            "text": claim.text,
                            "days_left": claim.days_until_expiry(),
                        }
                        for path, claim in claims
                    ],
                },
                indent=2,
            )
        else:
            # Return all claims
            all_claims = []
            for path, prov in tracker._provenance.items():
                for claim in prov.claims:
                    all_claims.append(
                        {
                            "document": path,
                            "claim_id": claim.claim_id,
                            "text": claim.text,
                            "source": claim.source,
                            "status": claim.status.value,
                            "is_expired": claim.is_expired(),
                        }
                    )

            return json.dumps(
                {"count": len(all_claims), "claims": all_claims},
                indent=2,
            )

    @mcp.tool()
    async def add_claim(
        document_path: str,
        claim_text: str,
        source: str,
        source_url: str = None,
        source_type: str = "internal",
    ) -> str:
        """
        Add a new claim to a document.

        Args:
            document_path: Path to the document (relative to project root)
            claim_text: The claim text to track
            source: Source attribution for the claim
            source_url: URL to source (optional)
            source_type: Type: 'internal', 'external', 'research', 'data'
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)

        claim = tracker.add_claim(
            document_path=Path(document_path),
            claim_text=claim_text,
            source=source,
            source_url=source_url,
            source_type=source_type,
        )

        return json.dumps(
            {
                "status": "added",
                "claim_id": claim.claim_id,
                "document": document_path,
            },
            indent=2,
        )

    @mcp.tool()
    async def verify_claim(
        document_path: str,
        claim_id: str,
        verifier: str,
        expiry_days: int = 365,
    ) -> str:
        """
        Verify a claim.

        Args:
            document_path: Path to the document
            claim_id: ID of the claim to verify
            verifier: Name of person verifying
            expiry_days: Days until verification expires (default: 365)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)

        result = tracker.verify_claim(
            document_path=Path(document_path),
            claim_id=claim_id,
            verifier=verifier,
            expiry_days=expiry_days,
        )

        if result:
            return json.dumps(
                {
                    "status": "verified",
                    "claim_id": claim_id,
                    "verifier": verifier,
                    "expires_in_days": expiry_days,
                },
                indent=2,
            )
        else:
            return json.dumps({"error": "Claim not found"}, indent=2)

    @mcp.tool()
    async def approval_status(document_path: str = None) -> str:
        """
        Get document approval status.

        Args:
            document_path: Specific document path (optional, returns all if not provided)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ApprovalStatus, ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)

        if document_path:
            prov = tracker.get(Path(document_path))
            return json.dumps(
                {
                    "document": document_path,
                    "status": prov.current_status.value,
                    "unverified_claims": len(prov.unverified_claims),
                    "expired_claims": len(prov.expired_claims),
                    "approval_history": [a.to_dict() for a in prov.approvals],
                },
                indent=2,
            )
        else:
            # Return counts by status
            by_status = {}
            for status in ApprovalStatus:
                docs = tracker.get_documents_by_status(status)
                by_status[status.value] = {
                    "count": len(docs),
                    "documents": [str(d) for d in docs[:10]],  # Limit to first 10
                }

            return json.dumps({"by_status": by_status}, indent=2)

    @mcp.tool()
    async def request_approval(
        document_path: str,
        requester: str,
        comments: str = None,
    ) -> str:
        """
        Request approval for a document.

        Args:
            document_path: Path to the document
            requester: Name of person requesting approval
            comments: Optional comments
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        tracker.request_approval(Path(document_path), requester, comments)

        return json.dumps(
            {
                "status": "in_review",
                "document": document_path,
                "requester": requester,
            },
            indent=2,
        )

    @mcp.tool()
    async def approve_document(
        document_path: str,
        approver: str,
        comments: str = None,
        version: str = None,
    ) -> str:
        """
        Approve a document.

        Args:
            document_path: Path to the document
            approver: Name of person approving
            comments: Optional comments
            version: Optional version string
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        tracker.approve_document(Path(document_path), approver, comments, version)

        return json.dumps(
            {
                "status": "approved",
                "document": document_path,
                "approver": approver,
            },
            indent=2,
        )

    @mcp.tool()
    async def publish_readiness(document_path: str) -> str:
        """
        Check if a document is ready to publish.

        Args:
            document_path: Path to the document
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        readiness = tracker.check_publish_readiness(Path(document_path))

        return json.dumps(readiness, indent=2)

    @mcp.tool()
    async def review_queue() -> str:
        """
        Get documents waiting for review.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        queue = tracker.get_review_queue()

        return json.dumps(
            {
                "count": len(queue),
                "documents": [str(d) for d in queue],
            },
            indent=2,
        )

    @mcp.tool()
    async def scan_for_claims() -> str:
        """
        Scan all project documents for potential claims that need tracking.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        results = tracker.scan_all_documents()

        return json.dumps(
            {
                "documents_scanned": len(results),
                "total_claims_found": sum(len(c) for c in results.values()),
                "by_document": {
                    path: [{"type": c["type"], "match": c["match"]} for c in claims]
                    for path, claims in list(results.items())[:20]  # Limit to 20 docs
                },
            },
            indent=2,
        )

    @mcp.tool()
    async def validate_claim_urls() -> str:
        """
        Validate all external URLs in claims.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...provenance import ProvenanceTracker

        tracker = ProvenanceTracker(server_instance.project)
        results = tracker.validate_all_urls()

        return json.dumps(results, indent=2)
