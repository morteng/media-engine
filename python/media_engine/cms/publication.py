"""
Publication management - composite documents with identity.

A Publication is a collection of chapters that form a complete document
with its own metadata, version, and translation tracking.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from media_engine.core import compute_content_hash


@dataclass
class ChapterRef:
    """Reference to a chapter within a publication."""
    path: str
    required: bool = True
    sections: list[str] = field(default_factory=list)  # Optional section filter


@dataclass
class SlideRef:
    """Reference to a slide in a presentation."""
    slide_type: str  # title, section, content, two_column, image, quote
    title: str = ""
    source: str = ""  # Source chapter to extract from
    extract: str = ""  # What to extract: summary, key_points, etc.
    max_points: int = 5


@dataclass
class DataSourceRef:
    """Reference to a data source for spreadsheets."""
    source: str
    category: str = ""
    extract: str = ""
    sheet: str = ""


@dataclass
class OutputConfig:
    """Output format configuration for a publication."""
    format: str  # html, pdf, pptx, xlsx, epub
    template: str = "default"
    filename: str = ""
    single_file: bool = True
    toc: bool = True
    cover_page: bool = False
    speaker_notes: bool = False


@dataclass
class PublicationMetadata:
    """Metadata for a publication."""
    version: str = "1.0.0"
    status: str = "draft"  # draft | in_review | approved | published
    author: str = ""
    copyright: str = ""
    license: str = ""
    isbn: Optional[str] = None
    edition: str = ""
    publication_date: Optional[str] = None
    target_audience: str = ""
    reading_time: str = ""


@dataclass
class Publication:
    """A composite document with its own identity."""

    path: Path
    title: str
    subtitle: str = ""
    description: str = ""
    language: str = "en"
    pub_type: str = "book"  # book, deck, spreadsheet, report

    # For translations
    source_document: Optional[str] = None
    source_hash: Optional[str] = None

    metadata: PublicationMetadata = field(default_factory=PublicationMetadata)
    outputs: list[OutputConfig] = field(default_factory=list)
    chapters: list[ChapterRef] = field(default_factory=list)
    slides: list[SlideRef] = field(default_factory=list)  # For deck type
    data_sources: list[DataSourceRef] = field(default_factory=list)  # For spreadsheet type
    appendices: list[ChapterRef] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)

    # Front/back matter configuration
    front_matter: list[dict] = field(default_factory=list)
    back_matter: list[dict] = field(default_factory=list)

    # Quality requirements
    quality: dict = field(default_factory=dict)

    # Computed fields
    _content_hash: Optional[str] = field(default=None, repr=False)

    @classmethod
    def load(cls, path: Path) -> "Publication":
        """Load a publication from a YAML file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Parse chapters
        chapters = []
        for ch in data.get('chapters', []):
            if isinstance(ch, str):
                chapters.append(ChapterRef(path=ch))
            else:
                chapters.append(ChapterRef(
                    path=ch.get('path', ''),
                    required=ch.get('required', True),
                    sections=ch.get('sections', []),
                ))

        # Parse outputs
        outputs = []
        for out in data.get('outputs', []):
            outputs.append(OutputConfig(
                format=out.get('format', 'html'),
                template=out.get('template', 'default'),
                filename=out.get('filename', ''),
                single_file=out.get('single_file', True),
                toc=out.get('toc', True),
                cover_page=out.get('cover_page', False),
                speaker_notes=out.get('speaker_notes', False),
            ))

        # Parse metadata
        meta_data = data.get('metadata', {})
        metadata = PublicationMetadata(
            version=meta_data.get('version', '1.0.0'),
            status=meta_data.get('status', 'draft'),
            author=meta_data.get('author', ''),
            copyright=meta_data.get('copyright', ''),
            license=meta_data.get('license', ''),
            isbn=meta_data.get('isbn'),
            edition=meta_data.get('edition', ''),
            publication_date=meta_data.get('publication_date'),
            target_audience=meta_data.get('target_audience', ''),
            reading_time=meta_data.get('reading_time', ''),
        )

        # Parse appendices
        appendices = []
        for app in data.get('appendices', []):
            if isinstance(app, str):
                appendices.append(ChapterRef(path=app))
            else:
                appendices.append(ChapterRef(
                    path=app.get('path', ''),
                    required=app.get('required', False),
                ))

        # Parse slides (for deck/presentation type)
        slides = []
        for slide in data.get('slides', []):
            slides.append(SlideRef(
                slide_type=slide.get('type', 'content'),
                title=slide.get('title', ''),
                source=slide.get('source', ''),
                extract=slide.get('extract', ''),
                max_points=slide.get('max_points', 5),
            ))

        # Parse data sources (for spreadsheet type)
        data_sources = []
        for ds_category, ds_list in data.get('data_sources', {}).items():
            if isinstance(ds_list, list):
                for ds in ds_list:
                    data_sources.append(DataSourceRef(
                        source=ds.get('source', ''),
                        category=ds.get('category', ds_category),
                        extract=ds.get('extract', ''),
                        sheet=ds.get('sheet', ''),
                    ))

        # Infer publication type from content
        pub_type = data.get('type', 'publication')
        if pub_type == 'publication':
            # Infer from content structure
            if slides:
                pub_type = 'deck'
            elif data_sources:
                pub_type = 'spreadsheet'
            elif chapters:
                pub_type = 'book'
            else:
                pub_type = 'book'  # Default

        return cls(
            path=path,
            title=data.get('title', 'Untitled'),
            subtitle=data.get('subtitle', ''),
            description=data.get('description', ''),
            language=data.get('language', 'en'),
            pub_type=pub_type,
            source_document=data.get('source_document'),
            source_hash=data.get('source_hash'),
            metadata=metadata,
            outputs=outputs,
            chapters=chapters,
            slides=slides,
            data_sources=data_sources,
            appendices=appendices,
            assets=data.get('assets', []),
            related=data.get('related', []),
            front_matter=data.get('front_matter', []),
            back_matter=data.get('back_matter', []),
            quality=data.get('quality', {}),
        )

    @property
    def content_hash(self) -> str:
        """Compute hash of publication definition."""
        if self._content_hash is None:
            content = self.path.read_text(encoding='utf-8')
            self._content_hash = compute_content_hash(content)
        return self._content_hash

    @property
    def is_translation(self) -> bool:
        """Check if this is a translation of another publication."""
        return self.source_document is not None

    @property
    def item_count(self) -> int:
        """Get count of primary items based on publication type."""
        if self.pub_type == 'deck':
            return len(self.slides)
        elif self.pub_type == 'spreadsheet':
            return len(self.data_sources)
        else:
            return len(self.chapters)

    @property
    def item_label(self) -> str:
        """Get label for item type based on publication type."""
        if self.pub_type == 'deck':
            return 'slides'
        elif self.pub_type == 'spreadsheet':
            return 'sources'
        else:
            return 'chapters'

    def get_chapter_paths(self, content_dir: Path) -> list[Path]:
        """Get resolved paths to all chapters."""
        lang_dir = content_dir / self.language
        paths = []
        for ch in self.chapters:
            chapter_path = lang_dir / ch.path
            if chapter_path.exists():
                paths.append(chapter_path)
            elif ch.required:
                raise FileNotFoundError(f"Required chapter not found: {ch.path}")
        return paths

    def validate(self, content_dir: Path) -> list[str]:
        """Validate publication structure. Returns list of issues."""
        issues = []
        lang_dir = content_dir / self.language

        # Check required chapters exist
        for ch in self.chapters:
            chapter_path = lang_dir / ch.path
            if not chapter_path.exists():
                if ch.required:
                    issues.append(f"Required chapter missing: {ch.path}")
                else:
                    issues.append(f"Optional chapter missing: {ch.path}")

        # Check assets exist
        for asset in self.assets:
            asset_path = lang_dir / asset
            if not asset_path.exists():
                issues.append(f"Asset missing: {asset}")

        # Check outputs have valid formats
        valid_formats = {'html', 'pdf', 'pptx', 'xlsx', 'epub'}
        for output in self.outputs:
            if output.format not in valid_formats:
                issues.append(f"Invalid output format: {output.format}")

        return issues


@dataclass
class PublicationStatus:
    """Status of a publication including translation state."""
    publication: Publication
    is_valid: bool
    issues: list[str]
    chapter_count: int
    missing_chapters: int
    translation_current: bool = True
    source_changed: bool = False


class PublicationRegistry:
    """Registry for managing publications in a project."""

    def __init__(self, project):
        self.project = project
        self._publications: dict[str, Publication] = {}
        self._load_publications()

    def _load_publications(self):
        """Scan and load all publications."""
        content_dir = self.project.content_dir

        for lang in self.project.languages:
            pub_dir = content_dir / lang / "publications"
            if pub_dir.exists():
                for pub_file in pub_dir.glob("*.yaml"):
                    try:
                        pub = Publication.load(pub_file)
                        key = f"{lang}/{pub_file.stem}"
                        self._publications[key] = pub
                    except Exception as e:
                        print(f"Warning: Failed to load publication {pub_file}: {e}")

    def list_publications(self, language: str = None) -> list[Publication]:
        """List all publications, optionally filtered by language."""
        pubs = list(self._publications.values())
        if language:
            pubs = [p for p in pubs if p.language == language]
        return pubs

    def get_publication(self, key: str) -> Optional[Publication]:
        """Get a publication by key (e.g., 'en/documentation')."""
        return self._publications.get(key)

    def get_status(self, publication: Publication) -> PublicationStatus:
        """Get detailed status of a publication."""
        issues = publication.validate(self.project.content_dir)

        # Count chapters
        chapter_count = len(publication.chapters)
        missing = len([i for i in issues if "missing" in i.lower()])

        # Check translation status
        translation_current = True
        source_changed = False

        if publication.is_translation and publication.source_document:
            source_path = self.project.content_dir / publication.source_document
            if source_path.exists():
                source_pub = Publication.load(source_path)
                if publication.source_hash != source_pub.content_hash:
                    translation_current = False
                    source_changed = True

        return PublicationStatus(
            publication=publication,
            is_valid=len([i for i in issues if "Required" in i]) == 0,
            issues=issues,
            chapter_count=chapter_count,
            missing_chapters=missing,
            translation_current=translation_current,
            source_changed=source_changed,
        )

    def get_all_status(self) -> list[PublicationStatus]:
        """Get status for all publications."""
        return [self.get_status(p) for p in self._publications.values()]

    def get_translation_pairs(self) -> list[tuple[Publication, Publication]]:
        """Get pairs of source and translated publications."""
        pairs = []
        for pub in self._publications.values():
            if pub.is_translation and pub.source_document:
                pub.source_document.replace('.yaml', '').replace('/', '/')
                # Find by path matching
                for key, source_pub in self._publications.items():
                    if pub.source_document in str(source_pub.path):
                        pairs.append((source_pub, pub))
                        break
        return pairs
