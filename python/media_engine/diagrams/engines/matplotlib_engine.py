"""
Matplotlib Diagram Engine

Default diagram engine using matplotlib for rendering.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .base import DiagramEngine, EngineCapability, EngineInfo

if TYPE_CHECKING:
    from ..definition import Arrow, Box, DiagramConfig, DiagramDefinition


class MatplotlibEngine(DiagramEngine):
    """
    Matplotlib-based diagram engine.

    This is the default engine that uses matplotlib for rendering.
    It supports basic shapes, arrows, and dark mode.
    """

    @classmethod
    def get_info(cls) -> EngineInfo:
        """Get engine metadata."""
        return EngineInfo(
            name="matplotlib",
            version="1.0.0",
            capabilities=[
                EngineCapability.DARK_MODE,
            ],
            formats=["png", "svg", "pdf"],
            description="Default matplotlib-based engine for simple diagrams",
            installed=True,
        )

    @classmethod
    def is_available(cls) -> bool:
        """Matplotlib is always available (core dependency)."""
        import importlib.util

        return importlib.util.find_spec("matplotlib") is not None

    @classmethod
    def get_install_hint(cls) -> str:
        """Matplotlib should always be installed."""
        return "pip install matplotlib"

    def generate(
        self,
        definition: "DiagramDefinition",
        output_path: Path,
        engine_options: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Generate diagram using matplotlib."""
        config = definition.config
        options = {**config.engine_options, **(engine_options or {})}

        # Get colors based on theme and dark mode
        colors = self.get_colors(config.dark_mode)

        # Create figure
        fig, ax = plt.subplots(figsize=(config.width, config.height))
        fig.patch.set_facecolor(colors["background"])
        ax.set_facecolor(colors["background"])

        # Remove axes
        ax.axis("off")

        # Build box lookup for arrow connections
        box_lookup = {box.id: box for box in definition.boxes}

        # Auto-layout if coordinates are missing
        self._auto_layout_if_needed(definition.boxes)

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

        # Handle transparent background option
        transparent = options.get("transparent", False)

        plt.tight_layout()
        plt.savefig(
            output_path,
            dpi=config.dpi,
            facecolor=colors["background"] if not transparent else "none",
            edgecolor="none",
            bbox_inches="tight",
            format=output_path.suffix[1:] or config.format,
            transparent=transparent,
        )
        plt.close(fig)

        return output_path

    def _draw_box(
        self,
        ax: plt.Axes,
        box: "Box",
        colors: dict[str, str],
        config: "DiagramConfig",
    ) -> None:
        """Draw a box element."""
        # Resolve colors
        fill_color = self.resolve_color(
            box.color, config.dark_mode, default_key="box_fill"
        )
        border_color = self.resolve_color(
            box.border_color, config.dark_mode, default_key="box_border"
        )
        text_color = self.resolve_color(
            box.text_color, config.dark_mode, default_key="text"
        )

        # Font size
        font_size = box.font_size or (10 * config.font_scale)

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
        elif box.style == "diamond":
            # Draw diamond as rotated rectangle
            from matplotlib.patches import RegularPolygon

            diamond = RegularPolygon(
                (box.x, box.y),
                numVertices=4,
                radius=max(box.width, box.height) / 1.5,
                orientation=0,
                facecolor=fill_color,
                edgecolor=border_color,
                linewidth=2,
            )
            ax.add_patch(diamond)
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
            else:  # square, cylinder, or default
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
            fontsize=font_size,
            fontweight="bold",
            color=text_color,
            wrap=True,
        )

    def _draw_arrow(
        self,
        ax: plt.Axes,
        from_box: "Box",
        to_box: "Box",
        arrow: "Arrow",
        colors: dict[str, str],
        config: "DiagramConfig",
    ) -> None:
        """Draw an arrow between boxes."""
        # Resolve arrow color
        arrow_color = self.resolve_color(
            arrow.color, config.dark_mode, default_key="arrow"
        )

        # Calculate connection points
        if arrow.from_port and arrow.to_port:
            start = self._get_port_position(from_box, arrow.from_port)
            end = self._get_port_position(to_box, arrow.to_port)
        else:
            start = self._get_connection_point(from_box, to_box)
            end = self._get_connection_point(to_box, from_box)

        # Arrow style
        if arrow.style == "dashed":
            linestyle = "--"
        elif arrow.style == "dotted":
            linestyle = ":"
        else:
            linestyle = "-"

        # Connection style
        if arrow.curved:
            connection_style = "arc3,rad=0.2"
        else:
            connection_style = "arc3,rad=0"

        # Arrow style - handle bidirectional
        if arrow.bidirectional:
            arrow_style = "<|-|>"
        else:
            arrow_style = "-|>"

        fancy_arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle=arrow_style,
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

    def _get_connection_point(
        self, from_box: "Box", to_box: "Box"
    ) -> tuple[float, float]:
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

    def _get_port_position(
        self, box: "Box", port: str
    ) -> tuple[float, float]:
        """Get position for a specific port on a box."""
        port = port.lower()
        if port == "top":
            return (box.x, box.y + box.height / 2)
        elif port == "bottom":
            return (box.x, box.y - box.height / 2)
        elif port == "left":
            return (box.x - box.width / 2, box.y)
        elif port == "right":
            return (box.x + box.width / 2, box.y)
        else:
            # Default to center
            return (box.x, box.y)

    def _auto_layout_if_needed(self, boxes: list["Box"]) -> None:
        """
        Apply simple grid auto-layout if any boxes lack coordinates.

        This allows diagrams designed for auto-layout engines (like D2)
        to render with matplotlib as a fallback.
        """
        # Check if any boxes need layout
        needs_layout = any(box.x is None or box.y is None for box in boxes)
        if not needs_layout:
            return

        # Simple grid layout
        n = len(boxes)
        if n == 0:
            return

        # Calculate grid dimensions (roughly square)
        import math
        cols = max(1, int(math.ceil(math.sqrt(n))))
        rows = max(1, int(math.ceil(n / cols)))

        # Spacing between boxes
        spacing_x = 3.0
        spacing_y = 2.0

        for i, box in enumerate(boxes):
            if box.x is None:
                col = i % cols
                box.x = col * spacing_x
            if box.y is None:
                row = i // cols
                # Invert Y so first boxes are at top
                box.y = (rows - 1 - row) * spacing_y
