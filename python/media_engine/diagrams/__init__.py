"""
Media Engine Diagrams Module

Provides multi-engine diagram generation from YAML definitions:
    - DiagramGenerator: High-level API for diagram generation
    - DiagramDefinition: Define boxes, arrows, layers, and groups
    - Multiple engines: matplotlib (default), D2, Excalidraw
    - Full brand system integration for colors and fonts
"""

from .definition import (
    Arrow,
    Box,
    DiagramConfig,
    DiagramDefinition,
    DiagramEngineType,
    Group,
    Layer,
)
from .engines import (
    DiagramEngine,
    EngineCapability,
    EngineInfo,
    engine_summary,
    get_available_engines,
    get_best_engine,
    get_engine,
    get_engine_names,
    get_install_hints,
    get_installed_engines,
)
from .generator import (
    DiagramGenerator,
    build_diagrams,
    generate_diagram,
    generate_diagram_set,
)

__all__ = [
    # Generator (main API)
    "DiagramGenerator",
    "generate_diagram",
    "generate_diagram_set",
    "build_diagrams",
    # Definition types
    "DiagramDefinition",
    "DiagramConfig",
    "DiagramEngineType",
    "Box",
    "Arrow",
    "Layer",
    "Group",
    # Engine types
    "DiagramEngine",
    "EngineCapability",
    "EngineInfo",
    # Engine registry
    "get_engine",
    "get_available_engines",
    "get_installed_engines",
    "get_engine_names",
    "get_best_engine",
    "get_install_hints",
    "engine_summary",
]
