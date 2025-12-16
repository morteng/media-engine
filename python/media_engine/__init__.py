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
    core: Configuration and theming utilities
"""

__version__ = "0.1.0"

# Re-export commonly used items
from .core.theme import Theme, COPPER_AND_CREAM, load_theme
from .core.project import Project, find_project
from .cms import Document, DocumentCollection
from .templates import DocumentTemplate, render_document
from .assets import download_google_fonts, bundle_project_assets
from .quality import run_quality_checks, QualityReport
from .publish import publish_project, PublishConfig
from .status import get_project_dashboard, print_dashboard

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
]
