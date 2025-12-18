"""
Media Engine Templates Module

Professional HTML templates with:
- Sidebar navigation
- Theme toggle (light/dark)
- Reading progress bar
- Print-optimized styles
- Self-contained offline support
"""

from .components import (
    BackToTop,
    ReadingProgress,
    Sidebar,
    ThemeToggle,
)
from .html_document import (
    ChapterConfig,
    CoverConfig,
    DocumentTemplate,
    render_document,
)
from .html_index import (
    DeliverableCategory,
    DeliverableItem,
    FormatLink,
    IndexTemplate,
    LanguageInfo,
    render_language_index,
    render_project_index,
)
from .html_presentation import (
    PresentationTemplate,
    Slide,
    build_presentation_from_yaml,
    render_presentation,
)

__all__ = [
    "DocumentTemplate",
    "CoverConfig",
    "ChapterConfig",
    "render_document",
    "IndexTemplate",
    "render_language_index",
    "render_project_index",
    "DeliverableCategory",
    "DeliverableItem",
    "FormatLink",
    "LanguageInfo",
    "PresentationTemplate",
    "Slide",
    "build_presentation_from_yaml",
    "render_presentation",
    "ThemeToggle",
    "ReadingProgress",
    "BackToTop",
    "Sidebar",
]
