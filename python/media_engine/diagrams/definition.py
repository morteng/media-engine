"""
Diagram Definition Module

Dataclasses for diagram definitions with support for multiple engines.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml


class DiagramEngineType(str, Enum):
    """Available diagram engines."""

    MATPLOTLIB = "matplotlib"
    D2 = "d2"
    EXCALIDRAW = "excalidraw"
    AUTO = "auto"  # Auto-select based on features used


@dataclass
class DiagramConfig:
    """Configuration for diagram generation."""

    width: float = 12
    height: float = 8
    dpi: int = 150
    format: str = "png"  # png, svg, pdf
    dark_mode: bool = False
    font_scale: float = 1.0

    # Engine selection
    engine: DiagramEngineType = DiagramEngineType.MATPLOTLIB

    # Engine-specific options
    # d2: {"sketch": True, "layout": "elk", "pad": 50}
    # excalidraw: {"roughness": 1, "strokeSharpness": "round"}
    # matplotlib: {"transparent": False}
    engine_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class Box:
    """A box/shape element in a diagram."""

    id: str
    label: str
    x: Optional[float] = None  # Optional for auto-layout engines
    y: Optional[float] = None  # Optional for auto-layout engines
    width: float = 1.5
    height: float = 0.8
    color: Optional[str] = None  # Fill color (hex or brand token)
    text_color: Optional[str] = None  # Text color
    border_color: Optional[str] = None  # Border color
    style: str = "rounded"  # rounded, square, circle, diamond, cylinder

    # Advanced options
    icon: Optional[str] = None  # Icon identifier (D2 feature)
    font_size: Optional[float] = None
    layer: Optional[str] = None  # Layer assignment
    group: Optional[str] = None  # Group membership
    tooltip: Optional[str] = None  # Hover tooltip


@dataclass
class Arrow:
    """An arrow/connection between elements."""

    from_id: str
    to_id: str
    label: str = ""
    style: str = "solid"  # solid, dashed, dotted
    color: Optional[str] = None
    curved: bool = False

    # Advanced options
    from_port: Optional[str] = None  # top, bottom, left, right
    to_port: Optional[str] = None
    bidirectional: bool = False  # <-> instead of ->
    animated: bool = False  # D2 animation feature


@dataclass
class Layer:
    """A layer containing elements (D2 feature)."""

    id: str
    label: str
    elements: list[str] = field(default_factory=list)
    color: Optional[str] = None
    style: str = "default"  # default, cloud, container


@dataclass
class Group:
    """A group of related elements (Excalidraw feature)."""

    id: str
    label: Optional[str] = None
    elements: list[str] = field(default_factory=list)
    style: Optional[str] = None


@dataclass
class DiagramDefinition:
    """Complete diagram definition."""

    title: str = ""
    description: str = ""
    boxes: list[Box] = field(default_factory=list)
    arrows: list[Arrow] = field(default_factory=list)
    layers: list[Layer] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)
    config: DiagramConfig = field(default_factory=DiagramConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "DiagramDefinition":
        """Create from dictionary/YAML data."""
        # Parse boxes
        boxes = []
        for box_data in data.get("boxes", []):
            boxes.append(
                Box(
                    id=box_data["id"],
                    label=box_data["label"],
                    x=box_data.get("x"),  # Optional for auto-layout
                    y=box_data.get("y"),  # Optional for auto-layout
                    width=box_data.get("width", 1.5),
                    height=box_data.get("height", 0.8),
                    color=box_data.get("color"),
                    text_color=box_data.get("text_color"),
                    border_color=box_data.get("border_color"),
                    style=box_data.get("style", "rounded"),
                    icon=box_data.get("icon"),
                    font_size=box_data.get("font_size"),
                    layer=box_data.get("layer"),
                    group=box_data.get("group"),
                    tooltip=box_data.get("tooltip"),
                )
            )

        # Parse arrows
        arrows = []
        for arrow_data in data.get("arrows", []):
            arrows.append(
                Arrow(
                    from_id=arrow_data["from"],
                    to_id=arrow_data["to"],
                    label=arrow_data.get("label", ""),
                    style=arrow_data.get("style", "solid"),
                    color=arrow_data.get("color"),
                    curved=arrow_data.get("curved", False),
                    from_port=arrow_data.get("from_port"),
                    to_port=arrow_data.get("to_port"),
                    bidirectional=arrow_data.get("bidirectional", False),
                    animated=arrow_data.get("animated", False),
                )
            )

        # Parse layers
        layers = []
        for layer_data in data.get("layers", []):
            layers.append(
                Layer(
                    id=layer_data["id"],
                    label=layer_data.get("label", layer_data["id"]),
                    elements=layer_data.get("elements", []),
                    color=layer_data.get("color"),
                    style=layer_data.get("style", "default"),
                )
            )

        # Parse groups
        groups = []
        for group_data in data.get("groups", []):
            groups.append(
                Group(
                    id=group_data["id"],
                    label=group_data.get("label"),
                    elements=group_data.get("elements", []),
                    style=group_data.get("style"),
                )
            )

        # Parse config
        config_data = data.get("config", {})
        engine_str = config_data.get("engine", "matplotlib")
        try:
            engine = DiagramEngineType(engine_str)
        except ValueError:
            engine = DiagramEngineType.MATPLOTLIB

        config = DiagramConfig(
            width=config_data.get("width", 12),
            height=config_data.get("height", 8),
            dpi=config_data.get("dpi", 150),
            format=config_data.get("format", "png"),
            dark_mode=config_data.get("dark_mode", False),
            font_scale=config_data.get("font_scale", 1.0),
            engine=engine,
            engine_options=config_data.get("engine_options", {}),
        )

        return cls(
            title=data.get("title", "Diagram"),
            description=data.get("description", ""),
            boxes=boxes,
            arrows=arrows,
            layers=layers,
            groups=groups,
            config=config,
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "DiagramDefinition":
        """Load from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "config": {
                "width": self.config.width,
                "height": self.config.height,
                "dpi": self.config.dpi,
                "format": self.config.format,
                "dark_mode": self.config.dark_mode,
                "font_scale": self.config.font_scale,
                "engine": self.config.engine.value,
                "engine_options": self.config.engine_options,
            },
            "boxes": [
                {
                    "id": b.id,
                    "label": b.label,
                    "x": b.x,
                    "y": b.y,
                    "width": b.width,
                    "height": b.height,
                    "color": b.color,
                    "text_color": b.text_color,
                    "border_color": b.border_color,
                    "style": b.style,
                    "icon": b.icon,
                    "font_size": b.font_size,
                    "layer": b.layer,
                    "group": b.group,
                    "tooltip": b.tooltip,
                }
                for b in self.boxes
            ],
            "arrows": [
                {
                    "from": a.from_id,
                    "to": a.to_id,
                    "label": a.label,
                    "style": a.style,
                    "color": a.color,
                    "curved": a.curved,
                    "from_port": a.from_port,
                    "to_port": a.to_port,
                    "bidirectional": a.bidirectional,
                    "animated": a.animated,
                }
                for a in self.arrows
            ],
            "layers": [
                {
                    "id": l.id,
                    "label": l.label,
                    "elements": l.elements,
                    "color": l.color,
                    "style": l.style,
                }
                for l in self.layers
            ],
            "groups": [
                {
                    "id": g.id,
                    "label": g.label,
                    "elements": g.elements,
                    "style": g.style,
                }
                for g in self.groups
            ],
        }

    def uses_advanced_features(self) -> bool:
        """Check if diagram uses features beyond basic matplotlib support."""
        # Check for D2/Excalidraw-specific features
        for box in self.boxes:
            if box.icon or box.layer or box.tooltip:
                return True
            if box.style in ("diamond", "cylinder"):
                return True

        for arrow in self.arrows:
            if arrow.bidirectional or arrow.animated:
                return True
            if arrow.from_port or arrow.to_port:
                return True

        if self.layers or self.groups:
            return True

        return False

    def get_suggested_engine(self) -> DiagramEngineType:
        """Suggest the best engine based on features used."""
        if self.config.engine != DiagramEngineType.AUTO:
            return self.config.engine

        # Check for D2-specific features
        has_d2_features = False
        for box in self.boxes:
            if box.icon or box.layer:
                has_d2_features = True
                break
        for arrow in self.arrows:
            if arrow.animated:
                has_d2_features = True
                break
        if self.layers:
            has_d2_features = True

        if has_d2_features:
            return DiagramEngineType.D2

        # Check for Excalidraw features (groups, hand-drawn style)
        if self.groups:
            return DiagramEngineType.EXCALIDRAW

        # Check engine options for hints
        if self.config.engine_options.get("sketch"):
            return DiagramEngineType.D2
        if self.config.engine_options.get("roughness"):
            return DiagramEngineType.EXCALIDRAW

        # Default to matplotlib
        return DiagramEngineType.MATPLOTLIB
