"""Dashboard tab components."""

from .overview import get_overview_tab
from .documents import get_documents_tab
from .media import get_media_tab
from .packs import get_packs_tab
from .assets import get_assets_tab
from .translations import get_translations_tab
from .quality import get_quality_tab
from .activity import get_activity_tab

__all__ = [
    "get_overview_tab",
    "get_documents_tab",
    "get_media_tab",
    "get_packs_tab",
    "get_assets_tab",
    "get_translations_tab",
    "get_quality_tab",
    "get_activity_tab",
]
