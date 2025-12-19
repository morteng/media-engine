"""
Content Freshness Tracking Module

Provides a unified system for tracking content freshness across all project
content types, including documents, videos, demos, and deliverables.

Key Features:
- Central registry of all tracked content with dependency chains
- Automatic freshness computation based on file modification times
- Detection of stale content (dependencies newer than output)
- Detection of expired content (too old based on freshness_days)
- Detection of untracked files (not in registry)
- Impact analysis (what needs to rebuild when a file changes)

Usage:
    from media_engine.freshness import ContentRegistry, ContentType

    registry = ContentRegistry(project)
    registry.load()

    # Register content with dependencies
    registry.register(
        path=Path("docs/deliverables/assets/videos/no/teaser-no.mp4"),
        content_type=ContentType.VIDEO_RENDER,
        depends_on=[
            Path("docs/deliverables/video/scripts/no/teaser.yaml"),
            Path("docs/deliverables/demo/shared/demo-core.js"),
            Path("docs/deliverables/demo/shared/logo.svg"),
        ]
    )

    # Get freshness report
    report = registry.refresh()
    print(f"Stale items: {report.stale_count}")
    print(f"Untracked files: {report.untracked_count}")

    # Find what needs to rebuild when a file changes
    affected = registry.get_impact(Path("docs/deliverables/demo/shared/logo.svg"))

    registry.save()
"""

from .registry import ContentRegistry
from .scanner import scan_project
from .types import ContentType, FreshnessReport, FreshnessStatus, TrackedItem

__all__ = [
    "ContentRegistry",
    "ContentType",
    "FreshnessReport",
    "FreshnessStatus",
    "TrackedItem",
    "scan_project",
]
