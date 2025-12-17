"""CLI command modules."""

from .build import cmd_build
from .cache import cmd_cache
from .content import cmd_changelog, cmd_gaps, cmd_links, cmd_readability, cmd_security
from .dashboard import cmd_dashboard
from .demos import cmd_demos
from .init import cmd_init
from .integrity import cmd_integrity
from .pack import cmd_pack
from .provenance import cmd_provenance
from .publish import cmd_publish
from .quality import cmd_quality, cmd_stale
from .search import cmd_index, cmd_search
from .status import cmd_status
from .translation import cmd_translation
from .validate import cmd_validate

__all__ = [
    "cmd_status",
    "cmd_build",
    "cmd_publish",
    "cmd_quality",
    "cmd_stale",
    "cmd_cache",
    "cmd_search",
    "cmd_index",
    "cmd_validate",
    "cmd_pack",
    "cmd_translation",
    "cmd_init",
    "cmd_dashboard",
    "cmd_provenance",
    "cmd_integrity",
    "cmd_readability",
    "cmd_gaps",
    "cmd_links",
    "cmd_security",
    "cmd_changelog",
    "cmd_demos",
]
