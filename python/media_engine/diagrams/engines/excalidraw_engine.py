"""
Excalidraw Diagram Engine

Generates hand-drawn style diagrams using Excalidraw format.
Uses Kroki.io API for PNG/SVG export, with fallback to local .excalidraw JSON.
"""

import base64
import json
import urllib.error
import urllib.request
import uuid
import zlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .base import DiagramEngine, EngineCapability, EngineInfo

if TYPE_CHECKING:
    from ..definition import Arrow, Box, DiagramConfig, DiagramDefinition


class ExcalidrawEngine(DiagramEngine):
    """
    Excalidraw-based diagram engine.

    Creates hand-drawn style diagrams in Excalidraw format.
    Uses Kroki.io API for PNG/SVG rendering.
    """

    # Kroki.io endpoint
    KROKI_URL = "https://kroki.io/excalidraw"

    # Element spacing
    DEFAULT_BOX_WIDTH = 150
    DEFAULT_BOX_HEIGHT = 80
    HORIZONTAL_GAP = 50
    VERTICAL_GAP = 40

    @classmethod
    def get_info(cls) -> EngineInfo:
        """Get engine metadata."""
        return EngineInfo(
            name="excalidraw",
            version="1.0.0",
            capabilities=[
                EngineCapability.DARK_MODE,
                EngineCapability.SKETCH_MODE,  # Always sketch-like
                EngineCapability.GROUPS,
            ],
            formats=["svg", "png", "excalidraw"],
            description="Hand-drawn style diagrams via Excalidraw/Kroki.io",
            installed=True,  # Always available (uses HTTP API)
        )

    @classmethod
    def is_available(cls) -> bool:
        """Excalidraw engine is always available via Kroki.io."""
        return True

    @classmethod
    def get_install_hint(cls) -> str:
        """No installation needed."""
        return "No installation required - uses Kroki.io API"

    def generate(
        self,
        definition: "DiagramDefinition",
        output_path: Path,
        engine_options: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Generate diagram using Excalidraw format."""
        config = definition.config
        options = {**config.engine_options, **(engine_options or {})}

        # Get colors
        colors = self.get_colors(config.dark_mode)

        # Generate Excalidraw JSON
        excalidraw_data = self._generate_excalidraw(definition, colors, options)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # If output is .excalidraw, just save JSON
        if output_path.suffix == ".excalidraw":
            with open(output_path, "w") as f:
                json.dump(excalidraw_data, f, indent=2)
            return output_path

        # Otherwise, use Kroki.io to render
        output_format = output_path.suffix[1:] or config.format
        if output_format not in ["svg", "png"]:
            output_format = "svg"

        try:
            rendered = self._render_via_kroki(excalidraw_data, output_format)
            with open(output_path, "wb") as f:
                f.write(rendered)
        except Exception as e:
            # Fallback: save as .excalidraw
            fallback_path = output_path.with_suffix(".excalidraw")
            with open(fallback_path, "w") as f:
                json.dump(excalidraw_data, f, indent=2)
            import warnings
            warnings.warn(
                f"Kroki.io rendering failed ({e}), saved as {fallback_path}"
            )
            return fallback_path

        return output_path

    def _generate_excalidraw(
        self,
        definition: "DiagramDefinition",
        colors: dict[str, str],
        options: dict[str, Any],
    ) -> dict:
        """Generate Excalidraw JSON structure."""
        elements = []
        box_positions = {}

        # Layout parameters
        roughness = options.get("roughness", 1)  # 0=smooth, 1=artist, 2=cartoonist
        stroke_width = options.get("stroke_width", 1)

        # Calculate box positions using grid layout
        positions = self._calculate_layout(definition, options)

        # Create box elements
        for box in definition.boxes:
            pos = positions.get(box.id, {"x": 0, "y": 0})
            width = box.width * 100 if box.width else self.DEFAULT_BOX_WIDTH
            height = box.height * 100 if box.height else self.DEFAULT_BOX_HEIGHT

            box_element = self._create_box_element(
                box, pos["x"], pos["y"], width, height,
                colors, definition.config, roughness, stroke_width
            )
            elements.append(box_element)

            # Store center position for arrows
            box_positions[box.id] = {
                "x": pos["x"] + width / 2,
                "y": pos["y"] + height / 2,
                "width": width,
                "height": height,
            }

            # Add label as text element
            label_element = self._create_text_element(
                box.label,
                pos["x"] + width / 2,
                pos["y"] + height / 2,
                colors,
                definition.config,
                box.font_size or 16,
            )
            elements.append(label_element)

        # Create arrow elements
        for arrow in definition.arrows:
            if arrow.from_id in box_positions and arrow.to_id in box_positions:
                from_pos = box_positions[arrow.from_id]
                to_pos = box_positions[arrow.to_id]

                arrow_element = self._create_arrow_element(
                    arrow, from_pos, to_pos,
                    colors, definition.config, roughness, stroke_width
                )
                elements.append(arrow_element)

                # Add arrow label if present
                if arrow.label:
                    mid_x = (from_pos["x"] + to_pos["x"]) / 2
                    mid_y = (from_pos["y"] + to_pos["y"]) / 2 - 15
                    label_element = self._create_text_element(
                        arrow.label, mid_x, mid_y,
                        colors, definition.config, 12
                    )
                    elements.append(label_element)

        # Build Excalidraw document
        return {
            "type": "excalidraw",
            "version": 2,
            "source": "media-engine",
            "elements": elements,
            "appState": {
                "viewBackgroundColor": colors["background"],
                "gridSize": None,
                "theme": "dark" if definition.config.dark_mode else "light",
            },
            "files": {},
        }

    def _calculate_layout(
        self,
        definition: "DiagramDefinition",
        options: dict[str, Any],
    ) -> dict[str, dict[str, float]]:
        """Calculate positions for all boxes."""
        positions = {}
        direction = options.get("direction", "right")

        # Use specified positions if available, otherwise auto-layout
        boxes_with_pos = [b for b in definition.boxes if b.x is not None and b.y is not None]
        boxes_without_pos = [b for b in definition.boxes if b.x is None or b.y is None]

        # Handle explicitly positioned boxes
        for box in boxes_with_pos:
            positions[box.id] = {
                "x": box.x * 100,  # Scale coordinates
                "y": box.y * 100,
            }

        # Auto-layout remaining boxes
        if boxes_without_pos:
            cols = options.get("columns", 4)
            start_x = options.get("start_x", 50)
            start_y = options.get("start_y", 50)

            for i, box in enumerate(boxes_without_pos):
                if direction in ["right", "left"]:
                    row = i // cols
                    col = i % cols
                else:
                    col = i // cols
                    row = i % cols

                width = box.width * 100 if box.width else self.DEFAULT_BOX_WIDTH
                height = box.height * 100 if box.height else self.DEFAULT_BOX_HEIGHT

                positions[box.id] = {
                    "x": start_x + col * (width + self.HORIZONTAL_GAP),
                    "y": start_y + row * (height + self.VERTICAL_GAP),
                }

        return positions

    def _create_box_element(
        self,
        box: "Box",
        x: float,
        y: float,
        width: float,
        height: float,
        colors: dict[str, str],
        config: "DiagramConfig",
        roughness: int,
        stroke_width: int,
    ) -> dict:
        """Create an Excalidraw rectangle/ellipse element."""
        fill_color = self.resolve_color(
            box.color, config.dark_mode, default_key="box_fill"
        )
        stroke_color = self.resolve_color(
            box.border_color, config.dark_mode, default_key="box_border"
        )

        # Shape type
        if box.style == "circle":
            element_type = "ellipse"
        elif box.style == "diamond":
            element_type = "diamond"
        else:
            element_type = "rectangle"

        return {
            "id": self._generate_id(),
            "type": element_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "angle": 0,
            "strokeColor": stroke_color,
            "backgroundColor": fill_color,
            "fillStyle": "solid",
            "strokeWidth": stroke_width,
            "strokeStyle": "solid",
            "roughness": roughness,
            "opacity": 100,
            "groupIds": [box.group] if box.group else [],
            "roundness": {"type": 3} if box.style == "rounded" else None,
            "seed": self._random_seed(),
            "version": 1,
            "versionNonce": self._random_seed(),
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
        }

    def _create_text_element(
        self,
        text: str,
        x: float,
        y: float,
        colors: dict[str, str],
        config: "DiagramConfig",
        font_size: float,
    ) -> dict:
        """Create an Excalidraw text element."""
        text_color = colors["text"]

        return {
            "id": self._generate_id(),
            "type": "text",
            "x": x,
            "y": y,
            "width": len(text) * font_size * 0.6,
            "height": font_size * 1.5,
            "angle": 0,
            "strokeColor": text_color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "groupIds": [],
            "roundness": None,
            "seed": self._random_seed(),
            "version": 1,
            "versionNonce": self._random_seed(),
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
            "text": text,
            "fontSize": font_size,
            "fontFamily": 1,  # Virgil (hand-drawn)
            "textAlign": "center",
            "verticalAlign": "middle",
            "baseline": font_size,
            "containerId": None,
            "originalText": text,
        }

    def _create_arrow_element(
        self,
        arrow: "Arrow",
        from_pos: dict,
        to_pos: dict,
        colors: dict[str, str],
        config: "DiagramConfig",
        roughness: int,
        stroke_width: int,
    ) -> dict:
        """Create an Excalidraw arrow element."""
        stroke_color = self.resolve_color(
            arrow.color, config.dark_mode, default_key="arrow"
        )

        # Calculate edge connection points
        start_x, start_y = self._get_edge_point(from_pos, to_pos)
        end_x, end_y = self._get_edge_point(to_pos, from_pos)

        # Line style
        stroke_style = "solid"
        if arrow.style == "dashed":
            stroke_style = "dashed"
        elif arrow.style == "dotted":
            stroke_style = "dotted"

        # Arrow heads
        start_arrowhead = "arrow" if arrow.bidirectional else None
        end_arrowhead = "arrow"

        # Build points array (relative to element position)
        points = [
            [0, 0],
            [end_x - start_x, end_y - start_y],
        ]

        return {
            "id": self._generate_id(),
            "type": "arrow",
            "x": start_x,
            "y": start_y,
            "width": abs(end_x - start_x),
            "height": abs(end_y - start_y),
            "angle": 0,
            "strokeColor": stroke_color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": stroke_width,
            "strokeStyle": stroke_style,
            "roughness": roughness,
            "opacity": 100,
            "groupIds": [],
            "roundness": {"type": 2},
            "seed": self._random_seed(),
            "version": 1,
            "versionNonce": self._random_seed(),
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
            "points": points,
            "lastCommittedPoint": None,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": start_arrowhead,
            "endArrowhead": end_arrowhead,
        }

    def _get_edge_point(
        self,
        from_box: dict,
        to_box: dict,
    ) -> tuple[float, float]:
        """Calculate edge point from from_box toward to_box."""
        dx = to_box["x"] - from_box["x"]
        dy = to_box["y"] - from_box["y"]

        half_w = from_box["width"] / 2
        half_h = from_box["height"] / 2

        if abs(dx) > abs(dy):
            # Horizontal connection
            if dx > 0:
                return from_box["x"] + half_w, from_box["y"]
            else:
                return from_box["x"] - half_w, from_box["y"]
        else:
            # Vertical connection
            if dy > 0:
                return from_box["x"], from_box["y"] + half_h
            else:
                return from_box["x"], from_box["y"] - half_h

    def _render_via_kroki(
        self,
        excalidraw_data: dict,
        output_format: str,
    ) -> bytes:
        """Render Excalidraw JSON via Kroki.io API."""
        # Encode diagram
        json_str = json.dumps(excalidraw_data)
        compressed = zlib.compress(json_str.encode("utf-8"), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")

        # Build URL
        url = f"{self.KROKI_URL}/{output_format}/{encoded}"

        # Make request
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "media-engine/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Kroki.io API error: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Kroki.io connection failed: {e.reason}")

    def _generate_id(self) -> str:
        """Generate a unique element ID."""
        return uuid.uuid4().hex[:20]

    def _random_seed(self) -> int:
        """Generate a random seed for Excalidraw roughness."""
        import random
        return random.randint(1, 2147483647)

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
        light_path = output_dir / f"{base_name}_light.{definition.config.format}"
        self.generate(definition, light_path, options)

        # Dark theme
        definition.config.dark_mode = True
        dark_path = output_dir / f"{base_name}_dark.{definition.config.format}"
        self.generate(definition, dark_path, options)

        # Reset
        definition.config.dark_mode = False

        return light_path, dark_path
