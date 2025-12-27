"""
AI Research Store

Persistent storage for research findings that inform documentation.
Tracks sources, links research to documents, and monitors freshness.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ResearchStatus(str, Enum):
    """Research item status."""
    CURRENT = "current"
    STALE = "stale"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass
class ResearchSource:
    """A source for research."""
    url: Optional[str] = None
    title: Optional[str] = None
    fetched_at: Optional[str] = None
    content_hash: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "fetched_at": self.fetched_at,
            "content_hash": self.content_hash,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchSource":
        return cls(
            url=data.get("url"),
            title=data.get("title"),
            fetched_at=data.get("fetched_at"),
            content_hash=data.get("content_hash"),
            notes=data.get("notes", ""),
        )


@dataclass
class ResearchItem:
    """A research item with content and metadata."""
    id: str
    topic: str
    content: str
    status: ResearchStatus = ResearchStatus.CURRENT
    sources: List[ResearchSource] = field(default_factory=list)
    affects_documents: List[str] = field(default_factory=list)
    affects_publications: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_verified: Optional[str] = None
    created_by: Optional[str] = None  # session ID

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "content": self.content,
            "status": self.status.value,
            "sources": [s.to_dict() for s in self.sources],
            "affects_documents": self.affects_documents,
            "affects_publications": self.affects_publications,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_verified": self.last_verified,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchItem":
        return cls(
            id=data["id"],
            topic=data["topic"],
            content=data.get("content", ""),
            status=ResearchStatus(data.get("status", "current")),
            sources=[ResearchSource.from_dict(s) for s in data.get("sources", [])],
            affects_documents=data.get("affects_documents", []),
            affects_publications=data.get("affects_publications", []),
            tags=data.get("tags", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_verified=data.get("last_verified"),
            created_by=data.get("created_by"),
        )


class ResearchStore:
    """
    Persistent storage for AI research findings.

    Research items:
    - Store findings from web searches, documentation, etc.
    - Link to documents they inform
    - Track staleness and trigger updates
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.research_dir = self.project_root / ".media-engine" / "ai" / "research"
        self.research_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.research_dir / "index.json"

    def _load_index(self) -> Dict[str, Any]:
        """Load research index."""
        if not self.index_path.exists():
            return {"items": {}, "updated_at": None}
        try:
            with open(self.index_path) as f:
                return json.load(f)
        except Exception:
            return {"items": {}, "updated_at": None}

    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save research index."""
        index["updated_at"] = datetime.now().isoformat()
        with open(self.index_path, "w") as f:
            json.dump(index, f, indent=2)

    def _item_path(self, item_id: str) -> Path:
        """Get path for a research item's content file."""
        return self.research_dir / f"{item_id}.md"

    def store(
        self,
        topic: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        affects_documents: Optional[List[str]] = None,
        affects_publications: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> ResearchItem:
        """
        Store a new research item.

        Args:
            topic: Research topic/title
            content: Research content (markdown)
            sources: List of source URLs/references
            affects_documents: Documents this research informs
            affects_publications: Publications this affects
            tags: Tags for categorization
            session_id: AI session that created this

        Returns:
            The created research item
        """
        # Generate ID from topic
        item_id = topic.lower().replace(" ", "_").replace("-", "_")[:50]

        # Check if exists, update if so
        existing = self.get(item_id)
        if existing:
            return self.update(
                item_id,
                content=content,
                sources=sources,
                affects_documents=affects_documents,
                affects_publications=affects_publications,
            )

        item = ResearchItem(
            id=item_id,
            topic=topic,
            content=content,
            sources=[ResearchSource.from_dict(s) for s in (sources or [])],
            affects_documents=affects_documents or [],
            affects_publications=affects_publications or [],
            tags=tags or [],
            created_by=session_id,
        )

        # Save content to file
        with open(self._item_path(item_id), "w") as f:
            f.write(f"# {topic}\n\n{content}")

        # Update index
        index = self._load_index()
        index["items"][item_id] = item.to_dict()
        self._save_index(index)

        return item

    def get(self, item_id: str) -> Optional[ResearchItem]:
        """Get a research item by ID."""
        index = self._load_index()
        if item_id not in index["items"]:
            return None

        item = ResearchItem.from_dict(index["items"][item_id])

        # Load content from file if exists
        content_path = self._item_path(item_id)
        if content_path.exists():
            item.content = content_path.read_text()

        return item

    def update(
        self,
        item_id: str,
        content: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        affects_documents: Optional[List[str]] = None,
        affects_publications: Optional[List[str]] = None,
        status: Optional[ResearchStatus] = None,
    ) -> Optional[ResearchItem]:
        """Update an existing research item."""
        item = self.get(item_id)
        if not item:
            return None

        if content is not None:
            item.content = content
            with open(self._item_path(item_id), "w") as f:
                f.write(f"# {item.topic}\n\n{content}")

        if sources is not None:
            item.sources = [ResearchSource.from_dict(s) for s in sources]

        if affects_documents is not None:
            item.affects_documents = affects_documents

        if affects_publications is not None:
            item.affects_publications = affects_publications

        if status is not None:
            item.status = status

        item.updated_at = datetime.now().isoformat()

        # Update index
        index = self._load_index()
        index["items"][item_id] = item.to_dict()
        self._save_index(index)

        return item

    def list_items(
        self,
        status: Optional[ResearchStatus] = None,
        tag: Optional[str] = None,
        affects_document: Optional[str] = None,
    ) -> List[ResearchItem]:
        """List research items with optional filters."""
        index = self._load_index()
        items = []

        for item_id, item_data in index["items"].items():
            item = ResearchItem.from_dict(item_data)

            if status and item.status != status:
                continue
            if tag and tag not in item.tags:
                continue
            if affects_document and affects_document not in item.affects_documents:
                continue

            items.append(item)

        # Sort by updated_at descending
        items.sort(key=lambda i: i.updated_at, reverse=True)
        return items

    def search(self, query: str) -> List[ResearchItem]:
        """Search research items by topic or content."""
        query_lower = query.lower()
        results = []

        for item in self.list_items():
            if query_lower in item.topic.lower():
                results.append(item)
            elif self._item_path(item.id).exists():
                content = self._item_path(item.id).read_text()
                if query_lower in content.lower():
                    results.append(item)

        return results

    def link_to_document(
        self,
        item_id: str,
        document_path: str,
    ) -> Optional[ResearchItem]:
        """Link research to a document it informs."""
        item = self.get(item_id)
        if not item:
            return None

        if document_path not in item.affects_documents:
            item.affects_documents.append(document_path)

            index = self._load_index()
            index["items"][item_id] = item.to_dict()
            self._save_index(index)

        return item

    def get_research_for_document(self, document_path: str) -> List[ResearchItem]:
        """Get all research items that affect a document."""
        return self.list_items(affects_document=document_path)

    def mark_verified(self, item_id: str) -> Optional[ResearchItem]:
        """Mark research as verified/current."""
        item = self.get(item_id)
        if not item:
            return None

        item.status = ResearchStatus.CURRENT
        item.last_verified = datetime.now().isoformat()

        index = self._load_index()
        index["items"][item_id] = item.to_dict()
        self._save_index(index)

        return item

    def mark_stale(self, item_id: str) -> Optional[ResearchItem]:
        """Mark research as stale (needs refresh)."""
        return self.update(item_id, status=ResearchStatus.STALE)

    def get_stale(self) -> List[ResearchItem]:
        """Get all stale research items."""
        return self.list_items(status=ResearchStatus.STALE)

    def check_freshness(self, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        Check freshness of all research items.

        Returns items that may be stale based on age.
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()

        possibly_stale = []
        for item in self.list_items(status=ResearchStatus.CURRENT):
            check_date = item.last_verified or item.updated_at
            if check_date < cutoff_str:
                possibly_stale.append({
                    "id": item.id,
                    "topic": item.topic,
                    "last_verified": item.last_verified,
                    "updated_at": item.updated_at,
                    "days_old": (datetime.now() - datetime.fromisoformat(check_date)).days,
                    "affects_documents": item.affects_documents,
                })

        return possibly_stale

    def delete(self, item_id: str) -> bool:
        """Delete a research item."""
        index = self._load_index()
        if item_id not in index["items"]:
            return False

        del index["items"][item_id]
        self._save_index(index)

        # Remove content file
        content_path = self._item_path(item_id)
        if content_path.exists():
            content_path.unlink()

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get research store statistics."""
        items = self.list_items()

        by_status = {}
        for status in ResearchStatus:
            by_status[status.value] = len([i for i in items if i.status == status])

        all_tags = set()
        for item in items:
            all_tags.update(item.tags)

        return {
            "total": len(items),
            "by_status": by_status,
            "tags": list(all_tags),
            "documents_covered": len(set(
                doc for item in items for doc in item.affects_documents
            )),
        }
