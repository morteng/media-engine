"""
Publications module for Media Engine.

Publications are the deliverables users care about - PDFs, presentations,
videos, etc. Each publication is composed of source files (chapters,
diagrams, scripts) and can be rendered to multiple output formats.

This module provides:
- Publication data model and registry
- Component tracking and dependency management
- Build status tracking per format/language
- Derivation support (one publication derived from another)
"""

from .builder import PublicationBuilder
from .models import (
    BuildStatus,
    ComponentType,
    DerivationMode,
    OutputFormat,
    Publication,
    PublicationBuild,
    PublicationComponent,
    PublicationStatus,
    PublicationType,
)
from .registry import PublicationRegistry
from .tracker import PublicationTracker

__all__ = [
    # Models
    "Publication",
    "PublicationComponent",
    "PublicationType",
    "ComponentType",
    "OutputFormat",
    "PublicationStatus",
    "BuildStatus",
    "PublicationBuild",
    "DerivationMode",
    # Registry
    "PublicationRegistry",
    # Builder
    "PublicationBuilder",
    # Tracker
    "PublicationTracker",
]
