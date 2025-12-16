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
    publish_project,
    generate_navigation_indexes,
)

__all__ = [
    "PublishConfig",
    "PublishResult",
    "publish_project",
    "generate_navigation_indexes",
]
