"""
D2 Diagram Engine

Generates diagrams using the D2 CLI tool (https://d2lang.com).
Supports sketch mode, multiple layouts, and animations.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .base import DiagramEngine, EngineCapability, EngineInfo

if TYPE_CHECKING:
    from ..definition import Arrow, Box, DiagramConfig, DiagramDefinition


class D2Engine(DiagramEngine):
    """
    D2-based diagram engine.

    Uses the D2 CLI tool for rendering diagrams with support for:
    - Sketch mode (hand-drawn appearance)
    - Multiple layouts (dagre, elk, tala)
    - Animated connections
    - Icons and layers
    """

    # D2 layout engines
    LAYOUTS = ["dagre", "elk", "tala"]

    # D2 themes (built-in)
    D2_THEMES = {
        "neutral": 0,
        "neutral_grey": 1,
        "flagship_terrastruct": 3,
        "cool_classics": 4,
        "mixed_berry_blue": 5,
        "grape_soda": 6,
        "aubergine": 7,
        "colorblind_clear": 8,
        "vanilla_nitro_cola": 100,
        "orange_creamsicle": 101,
        "shirley_temple": 102,
        "earth_tones": 103,
        "everglade_green": 104,
        "buttered_toast": 105,
        "terminal": 200,
        "terminal_grayscale": 201,
        "origami": 302,
    }

    @classmethod
    def get_info(cls) -> EngineInfo:
        """Get engine metadata."""
        return EngineInfo(
            name="d2",
            version="1.0.0",
            capabilities=[
                EngineCapability.DARK_MODE,
                EngineCapability.SKETCH_MODE,
                EngineCapability.ANIMATION,
                EngineCapability.LAYERS,
                EngineCapability.ICONS,
                EngineCapability.CUSTOM_FONTS,
            ],
            formats=["svg", "png", "pdf"],
            description="D2 declarative diagram engine with sketch mode and animations",
            installed=cls.is_available(),
        )

    @classmethod
    def is_available(cls) -> bool:
        """Check if D2 CLI is installed."""
        return shutil.which("d2") is not None

    @classmethod
    def get_install_hint(cls) -> str:
        """Get installation instructions for D2."""
        return (
            "Install D2: brew install d2 (macOS) or "
            "curl -fsSL https://d2lang.com/install.sh | sh (Linux)"
        )

    def generate(
        self,
        definition: "DiagramDefinition",
        output_path: Path,
        engine_options: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Generate diagram using D2 CLI."""
        config = definition.config
        options = {**config.engine_options, **(engine_options or {})}

        # Get colors
        colors = self.get_colors(config.dark_mode)

        # Generate D2 source
        d2_source = self._generate_d2_source(definition, colors, options)

        # Write to temp file and render
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".d2", delete=False
        ) as f:
            f.write(d2_source)
            d2_file = Path(f.name)

        try:
            self._run_d2(d2_file, output_path, config, options)
        finally:
            d2_file.unlink(missing_ok=True)

        return output_path

    def _generate_d2_source(
        self,
        definition: "DiagramDefinition",
        colors: dict[str, str],
        options: dict[str, Any],
    ) -> str:
        """Generate D2 source code from definition."""
        lines = []

        # Direction
        direction = options.get("direction", "right")
        lines.append(f"direction: {direction}")
        lines.append("")

        # Global styles
        lines.append("# Global styles")
        lines.append("style: {")
        lines.append(f'  fill: "{colors["background"]}"')
        lines.append("}")
        lines.append("")

        # Title as top-level text if present
        if definition.title:
            lines.append(f'title: "{definition.title}" {{')
            lines.append("  style: {")
            lines.append(f'    font-color: "{colors["text"]}"')
            lines.append("    font-size: 24")
            lines.append("    bold: true")
            lines.append("  }")
            lines.append("}")
            lines.append("")

        # Layers (if defined)
        layers_by_id = {layer.id: layer for layer in definition.layers}

        # Group boxes by layer
        boxes_by_layer: dict[str, list] = {"_root": []}
        for box in definition.boxes:
            layer_id = box.layer or "_root"
            if layer_id not in boxes_by_layer:
                boxes_by_layer[layer_id] = []
            boxes_by_layer[layer_id].append(box)

        # Render layers and boxes
        for layer_id, boxes in boxes_by_layer.items():
            if layer_id != "_root" and layer_id in layers_by_id:
                layer = layers_by_id[layer_id]
                lines.append(f"{layer.id}: {layer.label or layer.id} {{")
                lines.append("  style: {")
                if layer.color:
                    layer_color = self.resolve_color(
                        layer.color,
                        definition.config.dark_mode,
                        default_key="secondary",
                    )
                    lines.append(f'    fill: "{layer_color}"')
                lines.append("    opacity: 0.1")
                lines.append("  }")
                lines.append("")

                for box in boxes:
                    box_lines = self._render_box(box, colors, definition.config, indent=2)
                    lines.extend(box_lines)

                lines.append("}")
                lines.append("")
            else:
                # Root level boxes
                for box in boxes:
                    box_lines = self._render_box(box, colors, definition.config, indent=0)
                    lines.extend(box_lines)

        lines.append("")

        # Render arrows
        lines.append("# Connections")
        for arrow in definition.arrows:
            arrow_lines = self._render_arrow(arrow, colors, definition.config)
            lines.extend(arrow_lines)

        return "\n".join(lines)

    def _render_box(
        self,
        box: "Box",
        colors: dict[str, str],
        config: "DiagramConfig",
        indent: int = 0,
    ) -> list[str]:
        """Render a box as D2 source."""
        prefix = "  " * indent
        lines = []

        # Box declaration with label
        label = box.label.replace('"', '\\"')
        lines.append(f'{prefix}{box.id}: "{label}" {{')

        # Shape mapping
        shape_map = {
            "rounded": "rectangle",
            "square": "square",
            "circle": "circle",
            "diamond": "diamond",
            "cylinder": "cylinder",
            "hexagon": "hexagon",
            "parallelogram": "parallelogram",
            "cloud": "cloud",
            "queue": "queue",
            "package": "package",
            "class": "class",
            "stored_data": "stored_data",
        }
        d2_shape = shape_map.get(box.style, "rectangle")
        lines.append(f"{prefix}  shape: {d2_shape}")

        # Icon if specified
        if box.icon:
            lines.append(f'{prefix}  icon: "{box.icon}"')

        # Tooltip
        if box.tooltip:
            tooltip = box.tooltip.replace('"', '\\"')
            lines.append(f'{prefix}  tooltip: "{tooltip}"')

        # Styles
        lines.append(f"{prefix}  style: {{")

        # Fill color
        fill_color = self.resolve_color(
            box.color, config.dark_mode, default_key="box_fill"
        )
        lines.append(f'{prefix}    fill: "{fill_color}"')

        # Border color
        border_color = self.resolve_color(
            box.border_color, config.dark_mode, default_key="box_border"
        )
        lines.append(f'{prefix}    stroke: "{border_color}"')

        # Text color
        text_color = self.resolve_color(
            box.text_color, config.dark_mode, default_key="text"
        )
        lines.append(f'{prefix}    font-color: "{text_color}"')

        # Font size
        if box.font_size:
            lines.append(f"{prefix}    font-size: {int(box.font_size)}")

        # Border radius for rectangles
        if box.style == "rounded":
            lines.append(f"{prefix}    border-radius: 8")

        lines.append(f"{prefix}  }}")
        lines.append(f"{prefix}}}")

        return lines

    def _render_arrow(
        self,
        arrow: "Arrow",
        colors: dict[str, str],
        config: "DiagramConfig",
    ) -> list[str]:
        """Render an arrow as D2 source."""
        lines = []

        # Connection syntax
        if arrow.bidirectional:
            connector = "<->"
        else:
            connector = "->"

        # From/to with optional ports
        from_part = arrow.from_id
        if arrow.from_port:
            from_part = f"{arrow.from_id}.{arrow.from_port}"

        to_part = arrow.to_id
        if arrow.to_port:
            to_part = f"{arrow.to_id}.{arrow.to_port}"

        # Label
        if arrow.label:
            label = arrow.label.replace('"', '\\"')
            lines.append(f'{from_part} {connector} {to_part}: "{label}" {{')
        else:
            lines.append(f"{from_part} {connector} {to_part} {{")

        # Style
        lines.append("  style: {")

        # Arrow color
        arrow_color = self.resolve_color(
            arrow.color, config.dark_mode, default_key="arrow"
        )
        lines.append(f'    stroke: "{arrow_color}"')

        # Line style
        if arrow.style == "dashed":
            lines.append("    stroke-dash: 5")
        elif arrow.style == "dotted":
            lines.append("    stroke-dash: 2")

        # Animation
        if arrow.animated:
            lines.append("    animated: true")

        lines.append("  }")
        lines.append("}")

        return lines

    def _run_d2(
        self,
        d2_file: Path,
        output_path: Path,
        config: "DiagramConfig",
        options: dict[str, Any],
    ) -> None:
        """Run D2 CLI to generate output."""
        cmd = ["d2"]

        # Layout engine
        layout = options.get("layout", "dagre")
        if layout in self.LAYOUTS:
            cmd.extend(["--layout", layout])

        # Sketch mode
        if options.get("sketch", False):
            cmd.append("--sketch")

        # Theme
        theme = options.get("theme", "neutral")
        if config.dark_mode and "dark" not in theme:
            # Use terminal theme for dark mode if not specified
            theme = options.get("dark_theme", "terminal")

        if theme in self.D2_THEMES:
            cmd.extend(["--theme", str(self.D2_THEMES[theme])])
        elif isinstance(theme, int):
            cmd.extend(["--theme", str(theme)])

        # Padding
        pad = options.get("pad", 20)
        cmd.extend(["--pad", str(pad)])

        # Center
        if options.get("center", True):
            cmd.append("--center")

        # Font (if specified)
        font = options.get("font")
        if font:
            cmd.extend(["--font-regular", font])

        # Animation interval for GIFs/animated SVGs
        if options.get("animate_interval"):
            cmd.extend(["--animate-interval", str(options["animate_interval"])])

        # Input and output
        cmd.append(str(d2_file))
        cmd.append(str(output_path))

        # Run D2
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(f"D2 failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("D2 rendering timed out after 60 seconds")
        except FileNotFoundError:
            raise RuntimeError(
                "D2 CLI not found. Install with: brew install d2"
            )

    def generate_both_themes(
        self,
        definition: "DiagramDefinition",
        output_dir: Path,
        base_name: str,
        engine_options: Optional[dict[str, Any]] = None,
    ) -> tuple[Path, Path]:
        """Generate both light and dark theme versions."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        options = {**definition.config.engine_options, **(engine_options or {})}

        # Light theme
        definition.config.dark_mode = False
        light_options = {**options}
        light_options.setdefault("theme", "neutral")
        light_path = output_dir / f"{base_name}_light.{definition.config.format}"
        self.generate(definition, light_path, light_options)

        # Dark theme
        definition.config.dark_mode = True
        dark_options = {**options}
        dark_options.setdefault("theme", "terminal")
        dark_path = output_dir / f"{base_name}_dark.{definition.config.format}"
        self.generate(definition, dark_path, dark_options)

        # Reset
        definition.config.dark_mode = False

        return light_path, dark_path
