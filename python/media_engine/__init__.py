"""
Media Engine - Agent-based media production framework.

Modules:
    cms: Document management with frontmatter, versioning, quality checks
    video: Timeline sequencing, capture, voiceover, captions
    diagrams: Matplotlib-based diagram generation
    builders: HTML, PPTX, XLSX generation
    templates: Professional HTML templates with sidebar, theme toggle
    assets: Font downloading, asset bundling
    quality: Content quality checks (placeholders, terminology, encoding)
    publish: Complete deliverable packaging with navigation
    status: Comprehensive project status dashboards and views
    search: Full-text search index generation
    validation: Schema and reference validation
    packs: Curated deliverable packages (investor, pilot)
    core: Configuration and theming utilities
"""

__version__ = "0.1.0"

# Re-export commonly used items
from .assets import bundle_project_assets, download_google_fonts
from .cms import Document, DocumentCollection
from .core.project import Project, find_project
from .core.theme import COPPER_AND_CREAM, Theme, load_theme
from .packs import PackResult, generate_investor_pack, generate_pilot_pack
from .publish import PublishConfig, publish_project
from .quality import QualityReport, run_quality_checks
from .search import SearchIndex, build_search_index
from .status import get_project_dashboard, print_dashboard
from .templates import DocumentTemplate, render_document
from .validation import ValidationReport, validate_project

__all__ = [
    "__version__",
    # Theme
    "Theme",
    "COPPER_AND_CREAM",
    "load_theme",
    # Project
    "Project",
    "find_project",
    # CMS
    "Document",
    "DocumentCollection",
    # Templates
    "DocumentTemplate",
    "render_document",
    # Assets
    "download_google_fonts",
    "bundle_project_assets",
    # Quality
    "run_quality_checks",
    "QualityReport",
    # Publish
    "publish_project",
    "PublishConfig",
    # Status
    "get_project_dashboard",
    "print_dashboard",
    # Search
    "SearchIndex",
    "build_search_index",
    # Validation
    "validate_project",
    "ValidationReport",
    # Packs
    "generate_investor_pack",
    "generate_pilot_pack",
    "PackResult",
]
