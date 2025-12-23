"""
Freshness Tracking Types

Defines content types, tracked items, and freshness status enums.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContentType(Enum):
    """Types of content that can be tracked."""

    # Source documents
    SOURCE_DOCUMENT = "source_document"  # Markdown chapters, YAML configs
    TRANSLATED_DOCUMENT = "translated_document"  # Translations with source reference

    # Video content
    VIDEO_SCRIPT = "video_script"  # YAML video definitions
    VIDEO_RENDER = "video_render"  # MP4/WebM outputs
    VOICEOVER_AUDIO = "voiceover_audio"  # Generated MP3

    # Demo content
    DEMO_HTML = "demo_html"  # Interactive demo pages
    DEMO_ASSET = "demo_asset"  # Demo CSS/JS/images
    DEMO_CAPTURE = "demo_capture"  # Screen-recorded video from demo

    # Diagrams
    DIAGRAM_SOURCE = "diagram_source"  # YAML diagram definitions
    DIAGRAM_RENDER = "diagram_render"  # PNG/SVG outputs

    # Final outputs
    DELIVERABLE = "deliverable"  # HTML, PDF, PPTX outputs

    # Configuration
    THEME = "theme"  # Theme YAML
    CONFIG = "config"  # Project config


class FreshnessStatus(Enum):
    """Freshness status of a tracked item."""

    FRESH = "fresh"  # Up to date, no action needed
    STALE = "stale"  # Dependencies are newer than output
    EXPIRED = "expired"  # Content is too old (based on freshness_days)
    UNTRACKED = "untracked"  # File exists but not registered
    MISSING = "missing"  # Registered but file doesn't exist
    CLAIMS_ISSUE = "claims_issue"  # Has unverified or expired claims


@dataclass
class TrackedItem:
    """A single tracked content item with dependency information."""

    path: Path  # Relative path from project root
    content_type: ContentType
    depends_on: List[Path] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    content_hash: str = ""  # SHA256[:16] of file content
    freshness_status: FreshnessStatus = FreshnessStatus.FRESH
    freshness_days: Optional[int] = None  # Max age in days before expired
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "type": self.content_type.value,
            "depends_on": [str(p) for p in self.depends_on],
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "content_hash": self.content_hash,
            "freshness_status": self.freshness_status.value,
            "freshness_days": self.freshness_days,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackedItem":
        """Create from dictionary."""
        return cls(
            path=Path(data["path"]),
            content_type=ContentType(data["type"]),
            depends_on=[Path(p) for p in data.get("depends_on", [])],
            last_modified=(
                datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None
            ),
            last_checked=(
                datetime.fromisoformat(data["last_checked"]) if data.get("last_checked") else None
            ),
            content_hash=data.get("content_hash", ""),
            freshness_status=FreshnessStatus(data.get("freshness_status", "fresh")),
            freshness_days=data.get("freshness_days"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FreshnessReport:
    """Summary report of content freshness."""

    project_name: str
    scan_time: datetime
    total_items: int = 0
    fresh_count: int = 0
    stale_count: int = 0
    expired_count: int = 0
    missing_count: int = 0
    untracked_count: int = 0
    ignored_count: int = 0
    claims_issue_count: int = 0
    stale_items: List[TrackedItem] = field(default_factory=list)
    expired_items: List[TrackedItem] = field(default_factory=list)
    missing_items: List[TrackedItem] = field(default_factory=list)
    claims_issue_items: List[TrackedItem] = field(default_factory=list)
    untracked_files: List[Path] = field(default_factory=list)
    ignored_files: List[Path] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "scan_time": self.scan_time.isoformat(),
            "summary": {
                "total": self.total_items,
                "fresh": self.fresh_count,
                "stale": self.stale_count,
                "expired": self.expired_count,
                "missing": self.missing_count,
                "untracked": self.untracked_count,
                "ignored": self.ignored_count,
                "claims_issue": self.claims_issue_count,
            },
            "stale_items": [item.to_dict() for item in self.stale_items],
            "expired_items": [item.to_dict() for item in self.expired_items],
            "missing_items": [item.to_dict() for item in self.missing_items],
            "claims_issue_items": [item.to_dict() for item in self.claims_issue_items],
            "untracked_files": [str(p) for p in self.untracked_files],
            "ignored_files": [str(p) for p in self.ignored_files],
        }
