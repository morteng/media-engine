"""
Provenance and version tracking for documents.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from ..core.hashing import compute_content_hash
from .document import Document, DocumentCollection


@dataclass
class ChangeRecord:
    """Record of a document change."""

    timestamp: str
    version_before: str
    version_after: str
    change_type: str  # major, minor, patch
    summary: str
    author: str
    content_hash: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeRecord":
        return cls(**data)


@dataclass
class DocumentProvenance:
    """Provenance information for a document."""

    path: str
    created: str
    changes: list[ChangeRecord] = field(default_factory=list)
    current_hash: str = ""
    review_history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "created": self.created,
            "changes": [c.to_dict() for c in self.changes],
            "current_hash": self.current_hash,
            "review_history": self.review_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentProvenance":
        changes = [ChangeRecord.from_dict(c) for c in data.get("changes", [])]
        return cls(
            path=data["path"],
            created=data.get("created", ""),
            changes=changes,
            current_hash=data.get("current_hash", ""),
            review_history=data.get("review_history", []),
        )


class ProvenanceTracker:
    """Tracks document provenance and version history."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.index_dir = docs_dir / ".index"
        self.provenance_file = self.index_dir / "provenance.json"
        self.provenance: dict[str, DocumentProvenance] = {}
        self._loaded = False

    def _ensure_index_dir(self) -> None:
        """Ensure index directory exists."""
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Load provenance data from disk."""
        self._ensure_index_dir()

        if self.provenance_file.exists():
            try:
                with open(self.provenance_file) as f:
                    data = json.load(f)
                for path, prov_data in data.items():
                    self.provenance[path] = DocumentProvenance.from_dict(prov_data)
            except Exception as e:
                print(f"Warning: Failed to load provenance: {e}")
                self.provenance = {}

        self._loaded = True

    def save(self) -> None:
        """Save provenance data to disk."""
        self._ensure_index_dir()

        data = {path: prov.to_dict() for path, prov in self.provenance.items()}
        with open(self.provenance_file, "w") as f:
            json.dump(data, f, indent=2)

    def ensure_loaded(self) -> None:
        """Ensure provenance is loaded."""
        if not self._loaded:
            self.load()

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute hash of document content."""
        return compute_content_hash(content)

    def get_provenance(self, doc: Document) -> DocumentProvenance:
        """Get or create provenance for a document."""
        self.ensure_loaded()

        path_str = str(doc.path.relative_to(self.docs_dir))

        if path_str not in self.provenance:
            # Create new provenance record
            self.provenance[path_str] = DocumentProvenance(
                path=path_str,
                created=datetime.now().isoformat(),
                current_hash=self.compute_content_hash(doc.content),
            )

        return self.provenance[path_str]

    def record_change(
        self, doc: Document, change_type: str, summary: str, author: str = "AI-assisted"
    ) -> ChangeRecord:
        """Record a change to a document."""
        self.ensure_loaded()

        prov = self.get_provenance(doc)
        old_version = doc.version

        # Increment version
        new_version = doc.increment_version(change_type)
        new_hash = self.compute_content_hash(doc.content)

        # Create change record
        record = ChangeRecord(
            timestamp=datetime.now().isoformat(),
            version_before=old_version,
            version_after=new_version,
            change_type=change_type,
            summary=summary,
            author=author,
            content_hash=new_hash,
        )

        prov.changes.append(record)
        prov.current_hash = new_hash

        # Update document metadata
        doc.update_modified(summary)

        self.save()
        return record

    def record_review(
        self,
        doc: Document,
        reviewer: str,
        approved: bool,
        comments: Optional[str] = None,
        project=None,
    ) -> None:
        """Record a review of a document.

        Args:
            doc: Document being reviewed
            reviewer: Name of reviewer
            approved: Whether the document was approved
            comments: Optional review comments
            project: Optional Project instance to sync with main provenance system
        """
        self.ensure_loaded()

        prov = self.get_provenance(doc)

        review = {
            "timestamp": datetime.now().isoformat(),
            "reviewer": reviewer,
            "approved": approved,
            "version": doc.version,
            "comments": comments,
        }

        prov.review_history.append(review)

        # Update document metadata
        doc.metadata["last_reviewed"] = date.today().isoformat()
        if "reviewers" not in doc.metadata:
            doc.metadata["reviewers"] = []
        if reviewer not in doc.metadata["reviewers"]:
            doc.metadata["reviewers"].append(reviewer)

        self.save()

        # Sync with main provenance system if project is provided
        if project is not None:
            self._sync_with_main_provenance(doc, reviewer, approved, comments, project)

    def _sync_with_main_provenance(
        self, doc: Document, reviewer: str, approved: bool, comments: Optional[str], project
    ) -> None:
        """Sync review status with main provenance system."""
        try:
            from ..provenance import ProvenanceTracker as MainProvenanceTracker

            main_tracker = MainProvenanceTracker(project)

            # Get document path relative to project root
            try:
                doc_path = doc.path.relative_to(project.root)
            except ValueError:
                doc_path = doc.path

            if approved:
                main_tracker.approve_document(
                    document_path=doc_path,
                    approver=reviewer,
                    comments=comments,
                    version=doc.version,
                )
            else:
                main_tracker.reject_document(
                    document_path=doc_path,
                    reviewer=reviewer,
                    comments=comments or "Changes requested",
                )

        except Exception:
            # Main provenance system not available - silently continue
            pass

    def has_changed(self, doc: Document) -> bool:
        """Check if document content has changed since last tracked."""
        self.ensure_loaded()

        prov = self.get_provenance(doc)
        current_hash = self.compute_content_hash(doc.content)
        return current_hash != prov.current_hash

    def get_change_history(self, doc: Document) -> list[ChangeRecord]:
        """Get change history for a document."""
        self.ensure_loaded()
        prov = self.get_provenance(doc)
        return prov.changes

    def get_review_history(self, doc: Document) -> list[dict]:
        """Get review history for a document."""
        self.ensure_loaded()
        prov = self.get_provenance(doc)
        return prov.review_history

    def suggest_version_bump(self, doc: Document, changes_description: str) -> str:
        """Suggest appropriate version bump based on changes."""
        # Simple heuristic based on keywords
        description_lower = changes_description.lower()

        major_keywords = [
            "breaking",
            "restructure",
            "rewrite",
            "overhaul",
            "major",
            "completely",
            "redesign",
        ]
        minor_keywords = [
            "add",
            "new section",
            "new feature",
            "significant",
            "diagram",
            "update",
            "enhance",
            "improve",
            "expand",
        ]

        for keyword in major_keywords:
            if keyword in description_lower:
                return "major"

        for keyword in minor_keywords:
            if keyword in description_lower:
                return "minor"

        return "patch"

    def generate_changelog(self, doc: Document, limit: int = 10) -> str:
        """Generate a changelog for a document."""
        history = self.get_change_history(doc)

        if not history:
            return "No change history available."

        lines = [f"# Changelog for {doc.title}", ""]

        for record in reversed(history[-limit:]):
            date_str = record.timestamp[:10]
            lines.append(f"## [{record.version_after}] - {date_str}")
            lines.append(f"- {record.summary}")
            lines.append(f"  - Type: {record.change_type}")
            lines.append(f"  - Author: {record.author}")
            lines.append("")

        return "\n".join(lines)

    def sync_all(self, collection: DocumentCollection) -> dict[str, bool]:
        """Sync provenance for all documents in collection."""
        self.ensure_loaded()

        results = {}
        for doc in collection.all_documents:
            path_str = str(doc.path.relative_to(self.docs_dir))
            changed = self.has_changed(doc)
            results[path_str] = changed

            # Update hash if document exists but hash is missing
            prov = self.get_provenance(doc)
            if not prov.current_hash:
                prov.current_hash = self.compute_content_hash(doc.content)

        self.save()
        return results
