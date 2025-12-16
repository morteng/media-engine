"""
Media Engine Publish Module

Complete deliverable packaging:
- Self-contained HTML with embedded fonts
- Navigation index generation (root + per-language)
- Asset bundling and packaging
"""

from .packager import (
    PublishConfig,
    PublishResult,
    generate_navigation_indexes,
    publish_project,
)

__all__ = [
    "PublishConfig",
    "PublishResult",
    "publish_project",
    "generate_navigation_indexes",
]
