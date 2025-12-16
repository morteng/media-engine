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
    IndexTemplate,
    render_language_index,
    render_project_index,
)

__all__ = [
    "DocumentTemplate",
    "CoverConfig",
    "ChapterConfig",
    "render_document",
    "IndexTemplate",
    "render_language_index",
    "render_project_index",
    "ThemeToggle",
    "ReadingProgress",
    "BackToTop",
    "Sidebar",
]
