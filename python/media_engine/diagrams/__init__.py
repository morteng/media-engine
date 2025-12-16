"""
Media Engine Diagrams Module

Provides diagram generation from YAML definitions:
    - DiagramGenerator: Generate diagrams with matplotlib
    - DiagramDefinition: Define boxes and arrows
    - Box, Arrow: Diagram elements
"""

from .generator import (
    DiagramGenerator,
    DiagramDefinition,
    DiagramConfig,
    Box,
    Arrow,
    generate_diagram,
    generate_diagram_set,
)

__all__ = [
    "DiagramGenerator",
    "DiagramDefinition",
    "DiagramConfig",
    "Box",
    "Arrow",
    "generate_diagram",
    "generate_diagram_set",
]
