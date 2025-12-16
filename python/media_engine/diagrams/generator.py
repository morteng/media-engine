"""
Diagram Generator Module

Generates diagrams from YAML definitions using matplotlib.
Supports light and dark themes with configurable styling.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import yaml
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ..core.theme import COPPER_AND_CREAM, Theme

# Default theme for diagrams
DEFAULT_THEME = COPPER_AND_CREAM


@dataclass
class DiagramConfig:
    """Configuration for diagram generation."""

    width: float = 12
    height: float = 8
    dpi: int = 150
    format: str = "png"  # png, svg, pdf
    dark_mode: bool = False
    font_scale: float = 1.0


@dataclass
class Box:
    """A box element in a diagram."""

    id: str
    label: str
    x: float
    y: float
    width: float = 1.5
    height: float = 0.8
    color: Optional[str] = None
    text_color: Optional[str] = None
    style: str = "rounded"  # rounded, square, circle


@dataclass
class Arrow:
    """An arrow connection between boxes."""

    from_id: str
    to_id: str
    label: str = ""
    style: str = "solid"  # solid, dashed
    color: Optional[str] = None
    curved: bool = False


@dataclass
class DiagramDefinition:
    """Complete diagram definition."""

    title: str
    description: str = ""
    boxes: list[Box] = field(default_factory=list)
    arrows: list[Arrow] = field(default_factory=list)
    config: DiagramConfig = field(default_factory=DiagramConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "DiagramDefinition":
        """Create from dictionary/YAML data."""
        boxes = []
        for box_data in data.get("boxes", []):
            boxes.append(
                Box(
                    id=box_data["id"],
                    label=box_data["label"],
                    x=box_data["x"],
                    y=box_data["y"],
                    width=box_data.get("width", 1.5),
                    height=box_data.get("height", 0.8),
                    color=box_data.get("color"),
                    text_color=box_data.get("text_color"),
                    style=box_data.get("style", "rounded"),
                )
            )

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
                )
            )

        config_data = data.get("config", {})
        config = DiagramConfig(
            width=config_data.get("width", 12),
            height=config_data.get("height", 8),
            dpi=config_data.get("dpi", 150),
            format=config_data.get("format", "png"),
            dark_mode=config_data.get("dark_mode", False),
            font_scale=config_data.get("font_scale", 1.0),
        )

        return cls(
            title=data.get("title", "Diagram"),
            description=data.get("description", ""),
            boxes=boxes,
            arrows=arrows,
            config=config,
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "DiagramDefinition":
        """Load from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class DiagramGenerator:
    """Generate diagrams from definitions."""

    def __init__(self, theme: Optional[Theme] = None):
        self.theme = theme or DEFAULT_THEME

    def generate(
        self,
        definition: DiagramDefinition,
        output_path: Path,
    ) -> Path:
        """Generate diagram and save to file."""
        config = definition.config

        # Get colors based on theme and dark mode
        colors = self._get_colors(config.dark_mode)

        # Create figure
        fig, ax = plt.subplots(figsize=(config.width, config.height))
        fig.patch.set_facecolor(colors["background"])
        ax.set_facecolor(colors["background"])

        # Remove axes
        ax.axis("off")

        # Build box lookup for arrow connections
        box_lookup = {box.id: box for box in definition.boxes}

        # Draw boxes
        for box in definition.boxes:
            self._draw_box(ax, box, colors, config)

        # Draw arrows
        for arrow in definition.arrows:
            if arrow.from_id in box_lookup and arrow.to_id in box_lookup:
                from_box = box_lookup[arrow.from_id]
                to_box = box_lookup[arrow.to_id]
                self._draw_arrow(ax, from_box, to_box, arrow, colors, config)

        # Add title
        if definition.title:
            ax.set_title(
                definition.title,
                fontsize=14 * config.font_scale,
                fontweight="bold",
                color=colors["text"],
                pad=20,
            )

        # Auto-scale to content
        ax.autoscale()
        ax.set_aspect("equal", adjustable="box")

        # Add padding
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        padding = 0.5
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)

        # Save
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        plt.tight_layout()
        plt.savefig(
            output_path,
            dpi=config.dpi,
            facecolor=colors["background"],
            edgecolor="none",
            bbox_inches="tight",
            format=output_path.suffix[1:] or config.format,
        )
        plt.close(fig)

        return output_path

    def generate_both_themes(
        self,
        definition: DiagramDefinition,
        output_dir: Path,
        base_name: str,
    ) -> tuple[Path, Path]:
        """Generate both light and dark theme versions."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Light theme
        definition.config.dark_mode = False
        light_path = output_dir / f"{base_name}_light.{definition.config.format}"
        self.generate(definition, light_path)

        # Dark theme
        definition.config.dark_mode = True
        dark_path = output_dir / f"{base_name}_dark.{definition.config.format}"
        self.generate(definition, dark_path)

        return light_path, dark_path

    def _get_colors(self, dark_mode: bool) -> dict[str, str]:
        """Get color palette based on theme and mode."""
        if dark_mode:
            return {
                "background": self.theme.dark.background,
                "text": self.theme.dark.text,
                "primary": self.theme.colors.primary,
                "secondary": self.theme.colors.secondary,
                "accent": self.theme.dark.accent,
                "box_fill": "#2a2825",
                "box_border": self.theme.dark.accent,
                "arrow": self.theme.dark.muted,
            }
        else:
            return {
                "background": self.theme.colors.background,
                "text": self.theme.colors.text,
                "primary": self.theme.colors.primary,
                "secondary": self.theme.colors.secondary,
                "accent": self.theme.colors.accent,
                "box_fill": "#ffffff",
                "box_border": self.theme.colors.primary,
                "arrow": self.theme.colors.muted,
            }

    def _draw_box(
        self,
        ax: plt.Axes,
        box: Box,
        colors: dict[str, str],
        config: DiagramConfig,
    ):
        """Draw a box element."""
        fill_color = box.color or colors["box_fill"]
        border_color = colors["box_border"]
        text_color = box.text_color or colors["text"]

        if box.style == "circle":
            # Draw circle
            circle = plt.Circle(
                (box.x, box.y),
                box.width / 2,
                facecolor=fill_color,
                edgecolor=border_color,
                linewidth=2,
            )
            ax.add_patch(circle)
        else:
            # Draw rectangle (rounded or square)
            if box.style == "rounded":
                fancy_box = FancyBboxPatch(
                    (box.x - box.width / 2, box.y - box.height / 2),
                    box.width,
                    box.height,
                    boxstyle="round,pad=0.05,rounding_size=0.1",
                    facecolor=fill_color,
                    edgecolor=border_color,
                    linewidth=2,
                )
            else:
                fancy_box = FancyBboxPatch(
                    (box.x - box.width / 2, box.y - box.height / 2),
                    box.width,
                    box.height,
                    boxstyle="square,pad=0.05",
                    facecolor=fill_color,
                    edgecolor=border_color,
                    linewidth=2,
                )
            ax.add_patch(fancy_box)

        # Add label
        ax.text(
            box.x,
            box.y,
            box.label,
            ha="center",
            va="center",
            fontsize=10 * config.font_scale,
            fontweight="bold",
            color=text_color,
            wrap=True,
        )

    def _draw_arrow(
        self,
        ax: plt.Axes,
        from_box: Box,
        to_box: Box,
        arrow: Arrow,
        colors: dict[str, str],
        config: DiagramConfig,
    ):
        """Draw an arrow between boxes."""
        arrow_color = arrow.color or colors["arrow"]

        # Calculate connection points
        start = self._get_connection_point(from_box, to_box)
        end = self._get_connection_point(to_box, from_box)

        # Arrow style
        linestyle = "--" if arrow.style == "dashed" else "-"

        if arrow.curved:
            # Curved arrow
            connection_style = "arc3,rad=0.2"
        else:
            connection_style = "arc3,rad=0"

        fancy_arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=15,
            color=arrow_color,
            linestyle=linestyle,
            linewidth=1.5,
            connectionstyle=connection_style,
        )
        ax.add_patch(fancy_arrow)

        # Add label if present
        if arrow.label:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            ax.text(
                mid_x,
                mid_y + 0.15,
                arrow.label,
                ha="center",
                va="bottom",
                fontsize=8 * config.font_scale,
                color=colors["text"],
                style="italic",
            )

    def _get_connection_point(self, from_box: Box, to_box: Box) -> tuple[float, float]:
        """Calculate edge connection point from from_box toward to_box."""
        dx = to_box.x - from_box.x
        dy = to_box.y - from_box.y

        # Determine which edge to connect from
        if abs(dx) > abs(dy):
            # Connect horizontally
            if dx > 0:
                return (from_box.x + from_box.width / 2, from_box.y)
            else:
                return (from_box.x - from_box.width / 2, from_box.y)
        else:
            # Connect vertically
            if dy > 0:
                return (from_box.x, from_box.y + from_box.height / 2)
            else:
                return (from_box.x, from_box.y - from_box.height / 2)


def generate_diagram(
    definition: DiagramDefinition | dict | Path,
    output_path: Path,
    theme: Optional[Theme] = None,
) -> Path:
    """Convenience function to generate a diagram."""
    generator = DiagramGenerator(theme=theme)

    if isinstance(definition, Path):
        definition = DiagramDefinition.from_yaml(definition)
    elif isinstance(definition, dict):
        definition = DiagramDefinition.from_dict(definition)

    return generator.generate(definition, output_path)


def generate_diagram_set(
    definition: DiagramDefinition | dict | Path,
    output_dir: Path,
    base_name: str,
    theme: Optional[Theme] = None,
) -> tuple[Path, Path]:
    """Generate both light and dark theme versions."""
    generator = DiagramGenerator(theme=theme)

    if isinstance(definition, Path):
        definition = DiagramDefinition.from_yaml(definition)
    elif isinstance(definition, dict):
        definition = DiagramDefinition.from_dict(definition)

    return generator.generate_both_themes(definition, output_dir, base_name)
