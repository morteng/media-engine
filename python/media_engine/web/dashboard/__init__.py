"""
Media Engine Dashboard HTML Generator

This module assembles the complete dashboard HTML from modular components.
"""

from .styles import get_styles
from .layout import get_body_start, get_body_end
from .tabs import (
    get_overview_tab,
    get_documents_tab,
    get_media_tab,
    get_packs_tab,
    get_assets_tab,
    get_translations_tab,
    get_quality_tab,
    get_activity_tab,
)
from .scripts import get_javascript


def generate_dashboard_html() -> str:
    """Generate complete embedded dashboard HTML.

    Assembles all dashboard components (styles, layout, tabs, and scripts)
    into a single HTML document.

    Returns:
        Complete HTML string for the Media Engine Dashboard.
    """
    return (
        get_styles()
        + get_body_start()
        + get_overview_tab()
        + get_documents_tab()
        + get_media_tab()
        + get_packs_tab()
        + get_assets_tab()
        + get_translations_tab()
        + get_quality_tab()
        + get_activity_tab()
        + get_body_end()
        + get_javascript()
        + "</body></html>"
    )


__all__ = ["generate_dashboard_html"]
