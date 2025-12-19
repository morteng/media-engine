"""Dashboard tab components."""

from .overview import get_overview_tab
from .documents import get_documents_tab
from .media import get_media_tab
from .packs import get_packs_tab
from .assets import get_assets_tab
from .translations import get_translations_tab
from .quality import get_quality_tab
from .freshness import get_freshness_tab
from .provenance import get_provenance_tab
from .build import get_build_tab
from .search import get_search_tab
from .dependencies import get_dependencies_tab
from .activity import get_activity_tab

__all__ = [
    "get_overview_tab",
    "get_documents_tab",
    "get_media_tab",
    "get_packs_tab",
    "get_assets_tab",
    "get_translations_tab",
    "get_quality_tab",
    "get_freshness_tab",
    "get_provenance_tab",
    "get_build_tab",
    "get_search_tab",
    "get_dependencies_tab",
    "get_activity_tab",
]
