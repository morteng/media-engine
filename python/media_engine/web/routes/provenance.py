"""
Provenance API routes.

Provides endpoints for claim tracking, verification, and approval workflows.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_provenance_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register provenance API routes."""
    from fastapi import HTTPException
    from pydantic import BaseModel

    from ...provenance import (
        ApprovalStatus,
        ProvenanceTracker,
    )

    class AddClaimRequest(BaseModel):
        document_path: str
        claim_text: str
        source: str
        source_url: str | None = None
        source_type: str = "internal"

    class VerifyClaimRequest(BaseModel):
        document_path: str
        claim_id: str
        verifier: str
        expiry_days: int = 365

    class ApprovalRequest(BaseModel):
        document_path: str
        user: str
        comments: str | None = None
        version: str | None = None

    @router.get("/api/provenance")
    async def get_provenance_report():
        """Get comprehensive provenance report."""
        project = get_project()
        tracker = ProvenanceTracker(project)
        report = tracker.generate_report()

        return report

    @router.get("/api/provenance/claims")
    async def get_all_claims():
        """Get all claims across the project."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        claims = []
        for path, prov in tracker._provenance.items():
            for claim in prov.claims:
                claims.append({
                    "document_path": path,
                    "claim_id": claim.claim_id,
                    "text": claim.text,
                    "source": claim.source,
                    "source_url": claim.source_url,
                    "source_type": claim.source_type,
                    "status": claim.status.value,
                    "verified_by": claim.verified_by,
                    "verified_date": claim.verified_date,
                    "expires": claim.expires,
                    "is_expired": claim.is_expired(),
                    "days_until_expiry": claim.days_until_expiry(),
                })

        return {"claims": claims, "total": len(claims)}

    @router.get("/api/provenance/claims/unverified")
    async def get_unverified_claims():
        """Get all unverified claims."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        claims = []
        for path, claim in tracker.get_all_unverified():
            claims.append({
                "document_path": str(path),
                "claim_id": claim.claim_id,
                "text": claim.text,
                "source": claim.source,
                "source_url": claim.source_url,
                "source_type": claim.source_type,
            })

        return {"claims": claims, "total": len(claims)}

    @router.get("/api/provenance/claims/expired")
    async def get_expired_claims():
        """Get all expired claims."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        claims = []
        for path, claim in tracker.get_all_expired():
            claims.append({
                "document_path": str(path),
                "claim_id": claim.claim_id,
                "text": claim.text,
                "source": claim.source,
                "expires": claim.expires,
                "verified_by": claim.verified_by,
            })

        return {"claims": claims, "total": len(claims)}

    @router.get("/api/provenance/claims/expiring")
    async def get_expiring_claims():
        """Get claims expiring within 30 days."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        claims = []
        for path, claim in tracker.get_expiring_soon(days=30):
            claims.append({
                "document_path": str(path),
                "claim_id": claim.claim_id,
                "text": claim.text,
                "source": claim.source,
                "expires": claim.expires,
                "days_until_expiry": claim.days_until_expiry(),
            })

        return {"claims": claims, "total": len(claims)}

    @router.post("/api/provenance/claims")
    async def add_claim(request: AddClaimRequest):
        """Add a new claim to a document."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        claim = tracker.add_claim(
            document_path=Path(request.document_path),
            claim_text=request.claim_text,
            source=request.source,
            source_url=request.source_url,
            source_type=request.source_type,
        )

        await manager.broadcast({
            "type": "provenance_updated",
            "action": "claim_added",
            "document_path": request.document_path,
            "claim_id": claim.claim_id,
        })

        return {"success": True, "claim_id": claim.claim_id}

    @router.post("/api/provenance/claims/verify")
    async def verify_claim(request: VerifyClaimRequest):
        """Verify a claim."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        result = tracker.verify_claim(
            document_path=Path(request.document_path),
            claim_id=request.claim_id,
            verifier=request.verifier,
            expiry_days=request.expiry_days,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Claim not found")

        await manager.broadcast({
            "type": "provenance_updated",
            "action": "claim_verified",
            "document_path": request.document_path,
            "claim_id": request.claim_id,
        })

        return {"success": True}

    @router.get("/api/provenance/approvals")
    async def get_approval_status():
        """Get document approval status distribution."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        by_status = {}
        for status in ApprovalStatus:
            docs = tracker.get_documents_by_status(status)
            by_status[status.value] = {
                "count": len(docs),
                "documents": [str(d) for d in docs],
            }

        return {"by_status": by_status}

    @router.get("/api/provenance/review-queue")
    async def get_review_queue():
        """Get documents in review queue."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        queue = []
        for doc_path in tracker.get_review_queue():
            prov = tracker.get(doc_path)
            latest_approval = prov.approvals[-1] if prov.approvals else None
            queue.append({
                "document_path": str(doc_path),
                "status": prov.current_status.value,
                "requester": latest_approval.approver if latest_approval else None,
                "requested_at": latest_approval.timestamp if latest_approval else None,
                "comments": latest_approval.comments if latest_approval else None,
                "unverified_claims": len(prov.unverified_claims),
                "expired_claims": len(prov.expired_claims),
            })

        return {"queue": queue, "total": len(queue)}

    @router.post("/api/provenance/request-approval")
    async def request_approval(request: ApprovalRequest):
        """Request approval for a document."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        tracker.request_approval(
            document_path=Path(request.document_path),
            requester=request.user,
            comments=request.comments,
        )

        await manager.broadcast({
            "type": "provenance_updated",
            "action": "approval_requested",
            "document_path": request.document_path,
        })

        return {"success": True}

    @router.post("/api/provenance/approve")
    async def approve_document(request: ApprovalRequest):
        """Approve a document."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        tracker.approve_document(
            document_path=Path(request.document_path),
            approver=request.user,
            comments=request.comments,
            version=request.version,
        )

        await manager.broadcast({
            "type": "provenance_updated",
            "action": "document_approved",
            "document_path": request.document_path,
        })

        return {"success": True}

    @router.post("/api/provenance/reject")
    async def reject_document(request: ApprovalRequest):
        """Reject a document (request changes)."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        if not request.comments:
            raise HTTPException(status_code=400, detail="Comments required for rejection")

        tracker.reject_document(
            document_path=Path(request.document_path),
            reviewer=request.user,
            comments=request.comments,
        )

        await manager.broadcast({
            "type": "provenance_updated",
            "action": "document_rejected",
            "document_path": request.document_path,
        })

        return {"success": True}

    @router.post("/api/provenance/publish")
    async def publish_document(request: ApprovalRequest):
        """Mark a document as published."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        if not request.version:
            raise HTTPException(status_code=400, detail="Version required for publishing")

        tracker.publish_document(
            document_path=Path(request.document_path),
            publisher=request.user,
            version=request.version,
        )

        await manager.broadcast({
            "type": "provenance_updated",
            "action": "document_published",
            "document_path": request.document_path,
        })

        return {"success": True}

    @router.get("/api/provenance/document/{document_path:path}")
    async def get_document_provenance(document_path: str):
        """Get provenance details for a specific document."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        prov = tracker.get(Path(document_path))

        return {
            "document_path": str(prov.document_path),
            "status": prov.current_status.value,
            "claims": [c.to_dict() for c in prov.claims],
            "approvals": [a.to_dict() for a in prov.approvals],
            "dependencies": prov.dependencies,
            "external_refs": prov.external_refs,
            "unverified_claims": len(prov.unverified_claims),
            "expired_claims": len(prov.expired_claims),
            "expiring_soon": len(prov.claims_expiring_soon),
        }

    @router.get("/api/provenance/publish-readiness/{document_path:path}")
    async def check_publish_readiness(document_path: str):
        """Check if a document is ready to publish."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        readiness = tracker.check_publish_readiness(Path(document_path))

        return readiness

    @router.post("/api/provenance/scan")
    async def scan_documents_for_claims():
        """Scan all documents for potential claims."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        results = tracker.scan_all_documents()

        return {
            "documents_scanned": len(results),
            "total_claims_found": sum(len(c) for c in results.values()),
            "results": results,
        }

    @router.post("/api/provenance/validate-urls")
    async def validate_urls():
        """Validate all external URLs in claims."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        results = tracker.validate_all_urls()

        return results

    @router.get("/api/provenance/issues")
    async def get_claim_issues():
        """Get documents with claim issues for freshness integration."""
        project = get_project()
        tracker = ProvenanceTracker(project)

        issues = tracker.get_documents_with_claim_issues()

        return {
            "issues": [
                {
                    "document_path": str(path),
                    "issue_type": issue_type,
                    "count": count,
                }
                for path, issue_type, count in issues
            ],
            "total": len(issues),
        }
