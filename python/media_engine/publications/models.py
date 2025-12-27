"""
Data models for publications.

Publications are the core deliverables that users create and distribute.
Each publication is composed of source components and can be rendered
to multiple output formats in multiple languages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class PublicationType(Enum):
    """Types of publications."""
    BOOK = "book"              # Multi-chapter documentation
    DECK = "deck"              # Presentation/slides
    VIDEO = "video"            # Video production
    REPORT = "report"          # Single document report
    WEBSITE = "website"        # Static website
    PACKAGE = "package"        # Downloadable package/bundle


class ComponentType(Enum):
    """Types of components that make up a publication."""
    CHAPTER = "chapter"        # Markdown chapter
    SECTION = "section"        # Markdown section (part of chapter)
    SLIDE = "slide"            # Presentation slide
    DIAGRAM = "diagram"        # YAML diagram definition
    ASSET = "asset"            # Image, video, audio file
    SCRIPT = "script"          # Video/audio script
    SCENE = "scene"            # Video scene
    DATA = "data"              # Data file (CSV, JSON, YAML)
    TEMPLATE = "template"      # Template file


class OutputFormat(Enum):
    """Output formats for publications."""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    MP4 = "mp4"
    WEBM = "webm"
    EPUB = "epub"
    MD = "md"


class PublicationStatus(Enum):
    """Status of a publication."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BuildStatus(Enum):
    """Status of a publication build."""
    PENDING = "pending"
    BUILDING = "building"
    COMPLETE = "complete"
    FAILED = "failed"
    STALE = "stale"


class DerivationMode(Enum):
    """How a derived publication relates to its source."""
    AUTO = "auto"          # Auto-regenerate when source changes
    MANUAL = "manual"      # Flag as stale, human reviews
    HYBRID = "hybrid"      # Some sections auto, some manual


@dataclass
class ComponentReference:
    """Reference to content in another publication."""
    publication_id: str
    section: Optional[str] = None
    anchor: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "publication_id": self.publication_id,
            "section": self.section,
            "anchor": self.anchor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentReference":
        return cls(
            publication_id=data["publication_id"],
            section=data.get("section"),
            anchor=data.get("anchor"),
        )


@dataclass
class PublicationComponent:
    """A component (source file) within a publication."""
    source: Path                              # Path to source file
    component_type: ComponentType = ComponentType.CHAPTER
    title: Optional[str] = None               # Display title
    render_as: Optional[str] = None           # svg, png, etc.
    options: dict = field(default_factory=dict)
    references: list[ComponentReference] = field(default_factory=list)
    order: int = 0                            # Order within publication

    # Tracking
    content_hash: Optional[str] = None
    last_modified: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "source": str(self.source),
            "type": self.component_type.value,
            "title": self.title,
            "render_as": self.render_as,
            "options": self.options,
            "references": [r.to_dict() for r in self.references],
            "order": self.order,
            "content_hash": self.content_hash,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PublicationComponent":
        return cls(
            source=Path(data["source"]),
            component_type=ComponentType(data.get("type", "chapter")),
            title=data.get("title"),
            render_as=data.get("render_as"),
            options=data.get("options", {}),
            references=[
                ComponentReference.from_dict(r) for r in data.get("references", [])
            ],
            order=data.get("order", 0),
            content_hash=data.get("content_hash"),
            last_modified=datetime.fromisoformat(data["last_modified"])
            if data.get("last_modified")
            else None,
        )


@dataclass
class PublicationPart:
    """A logical grouping of components (like a book part)."""
    id: str
    title: str
    components: list[PublicationComponent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "components": [c.to_dict() for c in self.components],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PublicationPart":
        return cls(
            id=data["id"],
            title=data["title"],
            components=[
                PublicationComponent.from_dict(c) for c in data.get("components", [])
            ],
        )


@dataclass
class FormatOptions:
    """Build options for a specific output format."""
    format: OutputFormat
    template: Optional[str] = None
    options: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "format": self.format.value,
            "template": self.template,
            "options": self.options,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormatOptions":
        return cls(
            format=OutputFormat(data["format"]),
            template=data.get("template"),
            options=data.get("options", {}),
        )


@dataclass
class PublicationBuild:
    """Record of a publication build."""
    publication_id: str
    format: OutputFormat
    language: str
    status: BuildStatus
    output_path: Optional[Path] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    component_hashes: dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_stale(self) -> bool:
        """Check if build is stale based on component hashes."""
        # Will be computed by comparing with current hashes
        return self.status == BuildStatus.STALE

    def to_dict(self) -> dict:
        return {
            "publication_id": self.publication_id,
            "format": self.format.value,
            "language": self.language,
            "status": self.status.value,
            "output_path": str(self.output_path) if self.output_path else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "component_hashes": self.component_hashes,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PublicationBuild":
        return cls(
            publication_id=data["publication_id"],
            format=OutputFormat(data["format"]),
            language=data["language"],
            status=BuildStatus(data["status"]),
            output_path=Path(data["output_path"]) if data.get("output_path") else None,
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            component_hashes=data.get("component_hashes", {}),
            error=data.get("error"),
        )


@dataclass
class Publication:
    """
    A publication is a deliverable composed of source components.

    Publications can be rendered to multiple output formats (PDF, HTML, PPTX)
    in multiple languages. They track their components, build status, and
    can derive from other publications.
    """
    id: str
    title: str
    publication_type: PublicationType
    description: Optional[str] = None

    # Structure
    formats: list[OutputFormat] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    parts: list[PublicationPart] = field(default_factory=list)
    components: list[PublicationComponent] = field(default_factory=list)

    # Format-specific options
    format_options: dict[str, FormatOptions] = field(default_factory=dict)

    # Derivation
    derives_from: Optional[str] = None
    derivation_mode: DerivationMode = DerivationMode.MANUAL

    # Status
    status: PublicationStatus = PublicationStatus.DRAFT

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: str = "1.0.0"
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def get_all_components(self) -> list[PublicationComponent]:
        """Get all components, including those in parts."""
        all_components = list(self.components)
        for part in self.parts:
            all_components.extend(part.components)
        return sorted(all_components, key=lambda c: c.order)

    def get_component_paths(self) -> list[Path]:
        """Get all source file paths."""
        return [c.source for c in self.get_all_components()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.publication_type.value,
            "description": self.description,
            "formats": [f.value for f in self.formats],
            "languages": self.languages,
            "parts": [p.to_dict() for p in self.parts],
            "components": [c.to_dict() for c in self.components],
            "format_options": {
                k: v.to_dict() for k, v in self.format_options.items()
            },
            "derives_from": self.derives_from,
            "derivation_mode": self.derivation_mode.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
            "authors": self.authors,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Publication":
        """Create Publication from dictionary."""
        formats = [OutputFormat(f) for f in data.get("formats", [])]
        format_options = {}
        for k, v in data.get("format_options", {}).items():
            if isinstance(v, dict):
                v["format"] = k
                format_options[k] = FormatOptions.from_dict(v)

        return cls(
            id=data["id"],
            title=data["title"],
            publication_type=PublicationType(data.get("type", "book")),
            description=data.get("description"),
            formats=formats,
            languages=data.get("languages", ["en"]),
            parts=[PublicationPart.from_dict(p) for p in data.get("parts", [])],
            components=[
                PublicationComponent.from_dict(c) for c in data.get("components", [])
            ],
            format_options=format_options,
            derives_from=data.get("derives_from"),
            derivation_mode=DerivationMode(data.get("derivation_mode", "manual")),
            status=PublicationStatus(data.get("status", "draft")),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
            version=data.get("version", "1.0.0"),
            authors=data.get("authors", []),
            tags=data.get("tags", []),
        )
