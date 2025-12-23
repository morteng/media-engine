"""
Provenance Tracking for Media Engine

Tracks claims, sources, and verification status for all content.
Ensures 100% professional documentation with verified references.

Features:
- Claim tracking with source attribution
- Verification status and expiry
- Source link validation
- Approval workflows
- Dependency tracking between documents
"""

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ApprovalStatus(str, Enum):
    """Document approval workflow states."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ClaimStatus(str, Enum):
    """Claim verification status."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    EXPIRED = "expired"
    DISPUTED = "disputed"


@dataclass
class Claim:
    """
    A verifiable claim within a document.

    Claims are statements that require source attribution
    and periodic verification.
    """

    claim_id: str
    text: str
    source: str
    source_url: Optional[str] = None
    source_type: str = "internal"  # internal, external, research, data
    verified_by: Optional[str] = None
    verified_date: Optional[str] = None
    expires: Optional[str] = None
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    notes: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if claim verification has expired."""
        if not self.expires:
            return False
        try:
            exp_date = datetime.fromisoformat(self.expires).date()
            return date.today() > exp_date
        except ValueError:
            return False

    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry, or None if no expiry."""
        if not self.expires:
            return None
        try:
            exp_date = datetime.fromisoformat(self.expires).date()
            delta = exp_date - date.today()
            return delta.days
        except ValueError:
            return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Claim":
        data = data.copy()
        if "status" in data:
            data["status"] = ClaimStatus(data["status"])
        return cls(**data)


@dataclass
class Approval:
    """An approval record for a document."""

    approver: str
    status: ApprovalStatus
    timestamp: str
    comments: Optional[str] = None
    version: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Approval":
        data = data.copy()
        if "status" in data:
            data["status"] = ApprovalStatus(data["status"])
        return cls(**data)


@dataclass
class DocumentProvenance:
    """
    Complete provenance record for a document.

    Tracks:
    - Claims and their verification
    - Approval workflow history
    - Dependencies on other documents
    - External references
    """

    document_path: Path
    claims: list[Claim] = field(default_factory=list)
    approvals: list[Approval] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # paths to dependent docs
    external_refs: list[dict] = field(default_factory=list)
    last_verified: Optional[str] = None
    verified_by: Optional[str] = None

    @property
    def current_status(self) -> ApprovalStatus:
        """Get current approval status."""
        if not self.approvals:
            return ApprovalStatus.DRAFT
        return self.approvals[-1].status

    @property
    def unverified_claims(self) -> list[Claim]:
        """Get claims that need verification."""
        return [c for c in self.claims if c.status == ClaimStatus.UNVERIFIED]

    @property
    def expired_claims(self) -> list[Claim]:
        """Get claims with expired verification."""
        return [c for c in self.claims if c.is_expired()]

    @property
    def claims_expiring_soon(self) -> list[Claim]:
        """Get claims expiring within 30 days."""
        result = []
        for claim in self.claims:
            days = claim.days_until_expiry()
            if days is not None and 0 < days <= 30:
                result.append(claim)
        return result

    def add_claim(self, claim: Claim):
        """Add a claim to track."""
        self.claims.append(claim)

    def verify_claim(self, claim_id: str, verifier: str, expiry_days: int = 365):
        """Mark a claim as verified."""
        for claim in self.claims:
            if claim.claim_id == claim_id:
                claim.status = ClaimStatus.VERIFIED
                claim.verified_by = verifier
                claim.verified_date = datetime.now().isoformat()
                exp = date.today()
                from datetime import timedelta

                exp = exp + timedelta(days=expiry_days)
                claim.expires = exp.isoformat()
                return True
        return False

    def request_approval(self, requester: str, comments: str = None):
        """Request approval for the document."""
        self.approvals.append(
            Approval(
                approver=requester,
                status=ApprovalStatus.IN_REVIEW,
                timestamp=datetime.now().isoformat(),
                comments=comments,
            )
        )

    def approve(self, approver: str, comments: str = None, version: str = None):
        """Approve the document."""
        self.approvals.append(
            Approval(
                approver=approver,
                status=ApprovalStatus.APPROVED,
                timestamp=datetime.now().isoformat(),
                comments=comments,
                version=version,
            )
        )

    def reject(self, reviewer: str, comments: str):
        """Request changes to the document."""
        self.approvals.append(
            Approval(
                approver=reviewer,
                status=ApprovalStatus.CHANGES_REQUESTED,
                timestamp=datetime.now().isoformat(),
                comments=comments,
            )
        )

    def publish(self, publisher: str, version: str):
        """Mark document as published."""
        self.approvals.append(
            Approval(
                approver=publisher,
                status=ApprovalStatus.PUBLISHED,
                timestamp=datetime.now().isoformat(),
                version=version,
            )
        )

    def to_dict(self) -> dict:
        return {
            "document_path": str(self.document_path),
            "claims": [c.to_dict() for c in self.claims],
            "approvals": [a.to_dict() for a in self.approvals],
            "dependencies": self.dependencies,
            "external_refs": self.external_refs,
            "last_verified": self.last_verified,
            "verified_by": self.verified_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentProvenance":
        return cls(
            document_path=Path(data["document_path"]),
            claims=[Claim.from_dict(c) for c in data.get("claims", [])],
            approvals=[Approval.from_dict(a) for a in data.get("approvals", [])],
            dependencies=data.get("dependencies", []),
            external_refs=data.get("external_refs", []),
            last_verified=data.get("last_verified"),
            verified_by=data.get("verified_by"),
        )


class ProvenanceTracker:
    """
    Tracks provenance for all documents in a project.

    Stores data in {project}/.media-engine/provenance.json
    """

    def __init__(self, project):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.data_path = self.data_dir / "provenance.json"
        self._provenance: dict[str, DocumentProvenance] = {}
        self._load()

    def _load(self):
        """Load provenance data from disk."""
        if self.data_path.exists():
            with open(self.data_path) as f:
                data = json.load(f)
                for path, prov_data in data.items():
                    self._provenance[path] = DocumentProvenance.from_dict(prov_data)

    def _save(self):
        """Save provenance data to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {path: prov.to_dict() for path, prov in self._provenance.items()}
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def _log_action(self, action: str, details: str = None, user: str = None):
        """Log provenance action to audit log."""
        try:
            from ..audit import log_action

            log_action(self.project, action, details=details, user=user)
        except Exception:
            pass  # Audit logging is optional

    def get(self, document_path: Path) -> DocumentProvenance:
        """Get or create provenance record for a document."""
        key = str(document_path)
        if key not in self._provenance:
            self._provenance[key] = DocumentProvenance(document_path=document_path)
        return self._provenance[key]

    def save(self):
        """Persist all changes."""
        self._save()

    def add_claim(
        self,
        document_path: Path,
        claim_text: str,
        source: str,
        source_url: str = None,
        source_type: str = "internal",
    ) -> Claim:
        """Add a claim to a document."""
        prov = self.get(document_path)

        # Generate claim ID
        import hashlib

        claim_id = hashlib.sha256(claim_text.encode()).hexdigest()[:8]

        claim = Claim(
            claim_id=claim_id,
            text=claim_text,
            source=source,
            source_url=source_url,
            source_type=source_type,
        )
        prov.add_claim(claim)
        self._save()
        self._log_action("claim_added", f"Claim '{claim_text[:50]}...' added to {document_path}")
        return claim

    def verify_claim(
        self,
        document_path: Path,
        claim_id: str,
        verifier: str,
        expiry_days: int = 365,
    ) -> bool:
        """Verify a claim."""
        prov = self.get(document_path)
        result = prov.verify_claim(claim_id, verifier, expiry_days)
        self._save()
        if result:
            self._log_action(
                "claim_verified", f"Claim {claim_id} verified in {document_path}", user=verifier
            )
        return result

    def get_all_unverified(self) -> list[tuple[Path, Claim]]:
        """Get all unverified claims across the project."""
        result = []
        for path, prov in self._provenance.items():
            for claim in prov.unverified_claims:
                result.append((Path(path), claim))
        return result

    def get_all_expired(self) -> list[tuple[Path, Claim]]:
        """Get all expired claims across the project."""
        result = []
        for path, prov in self._provenance.items():
            for claim in prov.expired_claims:
                result.append((Path(path), claim))
        return result

    def get_expiring_soon(self, days: int = 30) -> list[tuple[Path, Claim]]:
        """Get claims expiring within specified days."""
        result = []
        for path, prov in self._provenance.items():
            for claim in prov.claims:
                remaining = claim.days_until_expiry()
                if remaining is not None and 0 < remaining <= days:
                    result.append((Path(path), claim))
        return result

    def add_dependency(self, document_path: Path, depends_on: Path):
        """Add a dependency between documents."""
        prov = self.get(document_path)
        dep_str = str(depends_on)
        if dep_str not in prov.dependencies:
            prov.dependencies.append(dep_str)
            self._save()

    def get_dependents(self, document_path: Path) -> list[Path]:
        """Get documents that depend on the given document."""
        target = str(document_path)
        result = []
        for path, prov in self._provenance.items():
            if target in prov.dependencies:
                result.append(Path(path))
        return result

    def get_approval_status(self, document_path: Path) -> ApprovalStatus:
        """Get current approval status for a document."""
        return self.get(document_path).current_status

    def request_approval(self, document_path: Path, requester: str, comments: str = None):
        """Request approval for a document."""
        prov = self.get(document_path)
        prov.request_approval(requester, comments)
        self._save()
        self._log_action(
            "approval_requested", f"Approval requested for {document_path}", user=requester
        )

    def approve_document(
        self,
        document_path: Path,
        approver: str,
        comments: str = None,
        version: str = None,
    ):
        """Approve a document."""
        prov = self.get(document_path)
        prov.approve(approver, comments, version)
        self._save()
        self._log_action("approval_granted", f"Document {document_path} approved", user=approver)

    def reject_document(self, document_path: Path, reviewer: str, comments: str):
        """Request changes to a document."""
        prov = self.get(document_path)
        prov.reject(reviewer, comments)
        self._save()
        self._log_action(
            "approval_rejected", f"Changes requested for {document_path}: {comments}", user=reviewer
        )

    def publish_document(self, document_path: Path, publisher: str, version: str):
        """Mark a document as published."""
        prov = self.get(document_path)
        prov.publish(publisher, version)
        self._save()
        self._log_action(
            "document_published", f"Document {document_path} published as {version}", user=publisher
        )

    def get_documents_by_status(self, status: ApprovalStatus) -> list[Path]:
        """Get all documents with a specific approval status."""
        result = []
        for path, prov in self._provenance.items():
            if prov.current_status == status:
                result.append(Path(path))
        return result

    def get_review_queue(self) -> list[Path]:
        """Get documents waiting for review."""
        return self.get_documents_by_status(ApprovalStatus.IN_REVIEW)

    def generate_report(self) -> dict:
        """Generate a comprehensive provenance report."""
        total_docs = len(self._provenance)
        total_claims = sum(len(p.claims) for p in self._provenance.values())
        verified_claims = sum(
            len([c for c in p.claims if c.status == ClaimStatus.VERIFIED])
            for p in self._provenance.values()
        )
        expired_claims = len(self.get_all_expired())
        expiring_soon = len(self.get_expiring_soon())

        by_status = {}
        for status in ApprovalStatus:
            by_status[status.value] = len(self.get_documents_by_status(status))

        return {
            "summary": {
                "total_documents": total_docs,
                "total_claims": total_claims,
                "verified_claims": verified_claims,
                "unverified_claims": total_claims - verified_claims,
                "expired_claims": expired_claims,
                "expiring_soon": expiring_soon,
            },
            "by_status": by_status,
            "review_queue": [str(p) for p in self.get_review_queue()],
            "needs_attention": {
                "unverified": [(str(p), c.text) for p, c in self.get_all_unverified()[:10]],
                "expired": [(str(p), c.text) for p, c in self.get_all_expired()[:10]],
                "expiring_soon": [(str(p), c.text) for p, c in self.get_expiring_soon()[:10]],
            },
        }

    def scan_document_for_claims(self, document_path: Path) -> list[dict]:
        """
        Scan a document for potential claims and return them.

        Does not automatically add claims - returns candidates for review.
        """
        full_path = self.project.root / document_path
        if not full_path.exists():
            return []

        try:
            content = full_path.read_text(encoding="utf-8")
            return extract_claims_from_content(content)
        except Exception:
            return []

    def scan_all_documents(self) -> dict:
        """
        Scan all documents in the project for potential claims.

        Returns dict mapping document paths to lists of potential claims.
        """
        results = {}

        for lang in self.project.languages:
            # Scan chapters
            chapters_dir = self.project.content_dir / lang / "chapters"
            if chapters_dir.exists():
                for md_file in chapters_dir.glob("*.md"):
                    rel_path = md_file.relative_to(self.project.root)
                    claims = self.scan_document_for_claims(rel_path)
                    if claims:
                        results[str(rel_path)] = claims

        return results

    def get_documents_with_claim_issues(self) -> list[tuple[Path, str, int]]:
        """
        Get documents that have claim issues (unverified, expired, expiring soon).

        Returns list of (path, issue_type, count) tuples.
        Useful for freshness integration.
        """
        issues = []

        for path, prov in self._provenance.items():
            unverified = len(prov.unverified_claims)
            expired = len(prov.expired_claims)
            expiring = len(prov.claims_expiring_soon)

            if unverified > 0:
                issues.append((Path(path), "unverified_claims", unverified))
            if expired > 0:
                issues.append((Path(path), "expired_claims", expired))
            if expiring > 0:
                issues.append((Path(path), "expiring_claims", expiring))

        return issues

    def validate_all_urls(self) -> dict:
        """
        Validate all external URLs in claims.

        Returns dict with validation results.
        """
        urls_to_validate = []
        url_to_claims = {}

        for path, prov in self._provenance.items():
            for claim in prov.claims:
                if claim.source_url:
                    urls_to_validate.append(claim.source_url)
                    if claim.source_url not in url_to_claims:
                        url_to_claims[claim.source_url] = []
                    url_to_claims[claim.source_url].append((path, claim.claim_id))

        # Deduplicate
        unique_urls = list(set(urls_to_validate))

        # Validate
        results = validate_external_urls(unique_urls)

        # Map results back to claims
        for result in results:
            result["claims"] = url_to_claims.get(result["url"], [])

        return {
            "total_urls": len(unique_urls),
            "valid": len([r for r in results if r["valid"]]),
            "invalid": len([r for r in results if not r["valid"]]),
            "results": results,
        }

    def check_publish_readiness(self, document_path: Path) -> dict:
        """
        Check if a document is ready to publish.

        Returns dict with readiness status and any blocking issues.
        """
        prov = self.get(document_path)

        issues = []
        warnings = []

        # Check for unverified claims
        unverified = prov.unverified_claims
        if unverified:
            issues.append(f"{len(unverified)} unverified claim(s)")

        # Check for expired claims
        expired = prov.expired_claims
        if expired:
            issues.append(f"{len(expired)} expired claim(s)")

        # Check for claims expiring soon
        expiring = prov.claims_expiring_soon
        if expiring:
            warnings.append(f"{len(expiring)} claim(s) expiring within 30 days")

        # Check approval status
        status = prov.current_status
        if status not in [ApprovalStatus.APPROVED, ApprovalStatus.PUBLISHED]:
            issues.append(f"Document status is '{status.value}', not approved")

        return {
            "ready": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "status": status.value,
            "total_claims": len(prov.claims),
            "verified_claims": len([c for c in prov.claims if c.status == ClaimStatus.VERIFIED]),
        }


# === Reference Extraction ===


def extract_claims_from_content(content: str) -> list[dict]:
    """
    Extract potential claims from markdown content.

    Looks for patterns like:
    - Statistics: "50% faster", "10x improvement"
    - Comparisons: "better than", "compared to"
    - Absolute statements: "always", "never", "all"
    """
    patterns = [
        (r"\d+%\s+\w+", "statistic"),
        (r"\d+x\s+\w+", "multiplier"),
        (r"better than|worse than|faster than|slower than", "comparison"),
        (r"always|never|every|all\s+\w+", "absolute"),
        (r"according to|research shows|studies show", "citation"),
    ]

    claims = []
    for pattern, claim_type in patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            # Get surrounding context
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].strip()

            claims.append(
                {
                    "match": match.group(),
                    "type": claim_type,
                    "context": context,
                    "position": match.start(),
                }
            )

    return claims


def validate_external_urls(urls: list[str]) -> list[dict]:
    """
    Validate that external URLs are accessible.

    Returns list of validation results.
    """
    import urllib.error
    import urllib.request

    results = []
    for url in urls:
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "MediaEngine/1.0")
            with urllib.request.urlopen(req, timeout=10) as response:
                results.append(
                    {
                        "url": url,
                        "valid": True,
                        "status": response.status,
                    }
                )
        except urllib.error.URLError as e:
            results.append(
                {
                    "url": url,
                    "valid": False,
                    "error": str(e),
                }
            )
        except Exception as e:
            results.append(
                {
                    "url": url,
                    "valid": False,
                    "error": str(e),
                }
            )

    return results


__all__ = [
    "ApprovalStatus",
    "ClaimStatus",
    "Claim",
    "Approval",
    "DocumentProvenance",
    "ProvenanceTracker",
    "extract_claims_from_content",
    "validate_external_urls",
]
