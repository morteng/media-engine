"""
Media Engine Templates Module

Professional HTML templates with:
- Sidebar navigation
- Theme toggle (light/dark)
- Reading progress bar
- Print-optimized styles
- Self-contained offline support
"""

from .html_document import (
    DocumentTemplate,
    CoverConfig,
    ChapterConfig,
    render_document,
)
from .html_index import (
    IndexTemplate,
    render_language_index,
    render_project_index,
)
from .components import (
    ThemeToggle,
    ReadingProgress,
    BackToTop,
    Sidebar,
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
