"""CLI command modules."""

from .analyze import cmd_analyze
from .brand import cmd_brand
from .build import cmd_build
from .cache import cmd_cache
from .content import cmd_changelog, cmd_gaps, cmd_links, cmd_readability, cmd_security
from .dashboard import cmd_dashboard
from .demos import cmd_demos
from .deps import cmd_deps
from .diagrams import cmd_diagrams
from .freshness import cmd_freshness
from .hierarchy import cmd_hierarchy
from .init import cmd_init
from .insights import (
    cmd_consistency,
    cmd_duplicates,
    cmd_graph,
    cmd_health,
    cmd_incomplete,
    cmd_parity,
    cmd_path,
    cmd_stats,
    cmd_terms,
    cmd_velocity,
)
from .integrity import cmd_integrity
from .notes import cmd_notes
from .pack import cmd_pack
from .provenance import cmd_provenance
from .publications import cmd_publications
from .publish import cmd_publish
from .quality import cmd_quality, cmd_stale
from .relationships import cmd_relationships
from .release import cmd_release
from .search import cmd_index, cmd_search
from .status import cmd_status
from .translation import cmd_translation
from .validate import cmd_validate

__all__ = [
    "cmd_analyze",
    "cmd_status",
    "cmd_brand",
    "cmd_build",
    "cmd_publish",
    "cmd_release",
    "cmd_quality",
    "cmd_stale",
    "cmd_cache",
    "cmd_search",
    "cmd_index",
    "cmd_validate",
    "cmd_pack",
    "cmd_translation",
    "cmd_deps",
    "cmd_init",
    "cmd_dashboard",
    "cmd_provenance",
    "cmd_integrity",
    "cmd_notes",
    "cmd_readability",
    "cmd_gaps",
    "cmd_links",
    "cmd_security",
    "cmd_changelog",
    "cmd_demos",
    "cmd_diagrams",
    "cmd_freshness",
    "cmd_hierarchy",
    "cmd_relationships",
    # Insights commands
    "cmd_health",
    "cmd_stats",
    "cmd_incomplete",
    "cmd_consistency",
    "cmd_parity",
    "cmd_terms",
    "cmd_duplicates",
    "cmd_velocity",
    "cmd_graph",
    "cmd_path",
    # Publications
    "cmd_publications",
]
