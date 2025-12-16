"""
Tests for media_engine.diagrams module.
"""

import pytest
from pathlib import Path

from media_engine.diagrams import (
    DiagramGenerator,
    DiagramDefinition,
    DiagramConfig,
    Box,
    Arrow,
    generate_diagram,
    generate_diagram_set,
)
from media_engine.core.theme import Theme, COPPER_AND_CREAM


class TestDiagramDefinition:
    """Tests for DiagramDefinition class."""

    def test_create_from_dict(self):
        """Test creating definition from dictionary."""
        data = {
            "title": "Test Diagram",
            "description": "A test diagram",
            "boxes": [
                {"id": "a", "label": "Box A", "x": 0, "y": 0},
                {"id": "b", "label": "Box B", "x": 2, "y": 0},
            ],
            "arrows": [
                {"from": "a", "to": "b", "label": "connects"},
            ],
        }

        definition = DiagramDefinition.from_dict(data)

        assert definition.title == "Test Diagram"
        assert len(definition.boxes) == 2
        assert len(definition.arrows) == 1

    def test_box_defaults(self):
        """Test box default values."""
        data = {
            "title": "Test",
            "boxes": [{"id": "a", "label": "A", "x": 0, "y": 0}],
        }

        definition = DiagramDefinition.from_dict(data)
        box = definition.boxes[0]

        assert box.width == 1.5
        assert box.height == 0.8
        assert box.style == "rounded"
        assert box.color is None

    def test_box_custom_values(self):
        """Test box with custom values."""
        data = {
            "title": "Test",
            "boxes": [
                {
                    "id": "a",
                    "label": "A",
                    "x": 1,
                    "y": 2,
                    "width": 3.0,
                    "height": 1.5,
                    "style": "square",
                    "color": "#ff0000",
                }
            ],
        }

        definition = DiagramDefinition.from_dict(data)
        box = definition.boxes[0]

        assert box.width == 3.0
        assert box.height == 1.5
        assert box.style == "square"
        assert box.color == "#ff0000"

    def test_arrow_defaults(self):
        """Test arrow default values."""
        data = {
            "title": "Test",
            "boxes": [
                {"id": "a", "label": "A", "x": 0, "y": 0},
                {"id": "b", "label": "B", "x": 2, "y": 0},
            ],
            "arrows": [{"from": "a", "to": "b"}],
        }

        definition = DiagramDefinition.from_dict(data)
        arrow = definition.arrows[0]

        assert arrow.label == ""
        assert arrow.style == "solid"
        assert arrow.curved is False

    def test_config_defaults(self):
        """Test config default values."""
        data = {"title": "Test"}
        definition = DiagramDefinition.from_dict(data)

        assert definition.config.width == 12
        assert definition.config.height == 8
        assert definition.config.dpi == 150
        assert definition.config.format == "png"
        assert definition.config.dark_mode is False

    def test_config_custom(self):
        """Test custom config values."""
        data = {
            "title": "Test",
            "config": {
                "width": 16,
                "height": 12,
                "dpi": 300,
                "format": "svg",
            },
        }

        definition = DiagramDefinition.from_dict(data)

        assert definition.config.width == 16
        assert definition.config.height == 12
        assert definition.config.dpi == 300
        assert definition.config.format == "svg"


class TestDiagramGenerator:
    """Tests for DiagramGenerator class."""

    def test_create_generator(self):
        """Test creating generator."""
        generator = DiagramGenerator()
        assert generator.theme is not None

    def test_create_with_theme(self):
        """Test creating generator with theme."""
        generator = DiagramGenerator(theme=COPPER_AND_CREAM)
        assert generator.theme.name == "Copper & Cream"

    def test_generate_simple_diagram(self, temp_dir):
        """Test generating a simple diagram."""
        definition = DiagramDefinition(
            title="Simple Test",
            boxes=[
                Box(id="a", label="Box A", x=0, y=0),
                Box(id="b", label="Box B", x=2, y=0),
            ],
            arrows=[Arrow(from_id="a", to_id="b")],
        )

        generator = DiagramGenerator()
        output_path = temp_dir / "test.png"
        result = generator.generate(definition, output_path)

        assert result.exists()
        assert result.stat().st_size > 0

    def test_generate_svg(self, temp_dir):
        """Test generating SVG format."""
        definition = DiagramDefinition(
            title="SVG Test",
            boxes=[Box(id="a", label="A", x=0, y=0)],
        )
        definition.config.format = "svg"

        generator = DiagramGenerator()
        output_path = temp_dir / "test.svg"
        result = generator.generate(definition, output_path)

        assert result.exists()
        assert result.suffix == ".svg"

    def test_generate_dark_mode(self, temp_dir):
        """Test generating dark mode diagram."""
        definition = DiagramDefinition(
            title="Dark Mode Test",
            boxes=[Box(id="a", label="A", x=0, y=0)],
        )
        definition.config.dark_mode = True

        generator = DiagramGenerator()
        output_path = temp_dir / "dark.png"
        result = generator.generate(definition, output_path)

        assert result.exists()

    def test_generate_both_themes(self, temp_dir):
        """Test generating both light and dark themes."""
        definition = DiagramDefinition(
            title="Both Themes",
            boxes=[Box(id="a", label="A", x=0, y=0)],
        )

        generator = DiagramGenerator()
        light, dark = generator.generate_both_themes(
            definition, temp_dir, "test_diagram"
        )

        assert light.exists()
        assert dark.exists()
        assert "light" in light.name
        assert "dark" in dark.name

    def test_box_styles(self, temp_dir):
        """Test different box styles."""
        definition = DiagramDefinition(
            title="Box Styles",
            boxes=[
                Box(id="rounded", label="Rounded", x=0, y=0, style="rounded"),
                Box(id="square", label="Square", x=2, y=0, style="square"),
                Box(id="circle", label="Circle", x=4, y=0, style="circle"),
            ],
        )

        generator = DiagramGenerator()
        output_path = temp_dir / "styles.png"
        result = generator.generate(definition, output_path)

        assert result.exists()

    def test_arrow_styles(self, temp_dir):
        """Test different arrow styles."""
        definition = DiagramDefinition(
            title="Arrow Styles",
            boxes=[
                Box(id="a", label="A", x=0, y=0),
                Box(id="b", label="B", x=2, y=0),
                Box(id="c", label="C", x=4, y=0),
            ],
            arrows=[
                Arrow(from_id="a", to_id="b", style="solid"),
                Arrow(from_id="b", to_id="c", style="dashed", curved=True),
            ],
        )

        generator = DiagramGenerator()
        output_path = temp_dir / "arrows.png"
        result = generator.generate(definition, output_path)

        assert result.exists()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_diagram_from_definition(self, temp_dir):
        """Test generate_diagram with DiagramDefinition."""
        definition = DiagramDefinition(
            title="Test",
            boxes=[Box(id="a", label="A", x=0, y=0)],
        )

        result = generate_diagram(definition, temp_dir / "test.png")
        assert result.exists()

    def test_generate_diagram_from_dict(self, temp_dir):
        """Test generate_diagram with dictionary."""
        data = {
            "title": "Test",
            "boxes": [{"id": "a", "label": "A", "x": 0, "y": 0}],
        }

        result = generate_diagram(data, temp_dir / "test.png")
        assert result.exists()

    def test_generate_diagram_from_yaml(self, temp_dir):
        """Test generate_diagram from YAML file."""
        yaml_content = """
title: "YAML Test"
boxes:
  - id: a
    label: "Box A"
    x: 0
    y: 0
"""
        yaml_path = temp_dir / "diagram.yaml"
        yaml_path.write_text(yaml_content)

        result = generate_diagram(yaml_path, temp_dir / "output.png")
        assert result.exists()

    def test_generate_diagram_set(self, temp_dir):
        """Test generate_diagram_set."""
        definition = DiagramDefinition(
            title="Test",
            boxes=[Box(id="a", label="A", x=0, y=0)],
        )

        light, dark = generate_diagram_set(definition, temp_dir, "my_diagram")

        assert light.exists()
        assert dark.exists()
        assert light.name == "my_diagram_light.png"
        assert dark.name == "my_diagram_dark.png"


class TestBox:
    """Tests for Box dataclass."""

    def test_required_fields(self):
        """Test required fields."""
        box = Box(id="test", label="Test", x=1.0, y=2.0)

        assert box.id == "test"
        assert box.label == "Test"
        assert box.x == 1.0
        assert box.y == 2.0

    def test_default_values(self):
        """Test default values."""
        box = Box(id="test", label="Test", x=0, y=0)

        assert box.width == 1.5
        assert box.height == 0.8
        assert box.color is None
        assert box.text_color is None
        assert box.style == "rounded"


class TestArrow:
    """Tests for Arrow dataclass."""

    def test_required_fields(self):
        """Test required fields."""
        arrow = Arrow(from_id="a", to_id="b")

        assert arrow.from_id == "a"
        assert arrow.to_id == "b"

    def test_default_values(self):
        """Test default values."""
        arrow = Arrow(from_id="a", to_id="b")

        assert arrow.label == ""
        assert arrow.style == "solid"
        assert arrow.color is None
        assert arrow.curved is False


class TestDiagramConfig:
    """Tests for DiagramConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = DiagramConfig()

        assert config.width == 12
        assert config.height == 8
        assert config.dpi == 150
        assert config.format == "png"
        assert config.dark_mode is False
        assert config.font_scale == 1.0

    def test_custom_values(self):
        """Test custom values."""
        config = DiagramConfig(
            width=20,
            height=15,
            dpi=300,
            format="svg",
            dark_mode=True,
            font_scale=1.5,
        )

        assert config.width == 20
        assert config.height == 15
        assert config.dpi == 300
        assert config.format == "svg"
        assert config.dark_mode is True
        assert config.font_scale == 1.5
