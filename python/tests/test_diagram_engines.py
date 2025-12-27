"""
Tests for media_engine.diagrams multi-engine system.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from media_engine.diagrams import (
    Arrow,
    Box,
    DiagramConfig,
    DiagramDefinition,
    DiagramEngineType,
    DiagramGenerator,
    Group,
    Layer,
    engine_summary,
    generate_diagram,
    get_available_engines,
    get_engine,
    get_engine_names,
    get_installed_engines,
)
from media_engine.diagrams.brand_adapter import (
    get_engine_colors,
    get_font_family,
    resolve_color,
)
from media_engine.diagrams.engines import EngineCapability


class TestDiagramDefinition:
    """Tests for DiagramDefinition dataclass."""

    def test_default_config(self):
        """Test default diagram config values."""
        config = DiagramConfig()
        assert config.width == 12
        assert config.height == 8
        assert config.format == "png"
        assert config.engine == DiagramEngineType.MATPLOTLIB
        assert config.dark_mode is False

    def test_box_creation(self):
        """Test creating boxes with various styles."""
        box = Box(id="test", label="Test Box")
        assert box.id == "test"
        assert box.label == "Test Box"
        assert box.style == "rounded"  # default
        assert box.x is None
        assert box.y is None

    def test_box_with_styling(self):
        """Test box with custom styling."""
        box = Box(
            id="styled",
            label="Styled Box",
            style="circle",
            color="brand.primary",
            border_color="#333",
            icon="logos/aws",
            tooltip="This is a tooltip",
        )
        assert box.style == "circle"
        assert box.color == "brand.primary"
        assert box.border_color == "#333"
        assert box.icon == "logos/aws"
        assert box.tooltip == "This is a tooltip"

    def test_arrow_creation(self):
        """Test creating arrows."""
        arrow = Arrow(from_id="a", to_id="b")
        assert arrow.from_id == "a"
        assert arrow.to_id == "b"
        assert arrow.style == "solid"
        assert arrow.curved is False
        assert arrow.bidirectional is False
        assert arrow.animated is False

    def test_arrow_with_features(self):
        """Test arrow with bidirectional and animated features."""
        arrow = Arrow(
            from_id="api",
            to_id="db",
            label="queries",
            style="dashed",
            curved=True,
            bidirectional=True,
            animated=True,
            from_port="bottom",
            to_port="top",
        )
        assert arrow.label == "queries"
        assert arrow.style == "dashed"
        assert arrow.curved is True
        assert arrow.bidirectional is True
        assert arrow.animated is True
        assert arrow.from_port == "bottom"
        assert arrow.to_port == "top"

    def test_layer_creation(self):
        """Test creating layers."""
        layer = Layer(id="backend", label="Backend Services", color="#f0f0f0")
        assert layer.id == "backend"
        assert layer.label == "Backend Services"
        assert layer.color == "#f0f0f0"

    def test_group_creation(self):
        """Test creating groups."""
        group = Group(id="microservices", label="Microservices", elements=["api", "auth"])
        assert group.id == "microservices"
        assert group.label == "Microservices"
        assert group.elements == ["api", "auth"]

    def test_definition_from_dict(self):
        """Test creating definition from dict."""
        data = {
            "title": "System Architecture",
            "config": {
                "engine": "d2",
                "format": "svg",
                "engine_options": {"sketch": True},
            },
            "boxes": [
                {"id": "api", "label": "API Gateway"},
                {"id": "db", "label": "Database", "style": "cylinder"},
            ],
            "arrows": [
                {"from": "api", "to": "db", "label": "reads/writes"},
            ],
        }

        definition = DiagramDefinition.from_dict(data)
        assert definition.title == "System Architecture"
        assert definition.config.engine == DiagramEngineType.D2
        assert definition.config.format == "svg"
        assert definition.config.engine_options.get("sketch") is True
        assert len(definition.boxes) == 2
        assert len(definition.arrows) == 1
        assert definition.boxes[0].id == "api"
        assert definition.arrows[0].label == "reads/writes"

    def test_suggested_engine_simple(self):
        """Test suggested engine for simple diagrams."""
        definition = DiagramDefinition(
            boxes=[Box(id="a", label="A"), Box(id="b", label="B")],
            arrows=[Arrow(from_id="a", to_id="b")],
        )
        # Simple diagrams suggest matplotlib
        assert definition.get_suggested_engine() in [
            DiagramEngineType.MATPLOTLIB,
            DiagramEngineType.D2,
        ]

    def test_suggested_engine_with_layers(self):
        """Test suggested engine for diagrams with layers."""
        definition = DiagramDefinition(
            boxes=[Box(id="a", label="A", layer="frontend")],
            layers=[Layer(id="frontend", label="Frontend")],
            config=DiagramConfig(engine=DiagramEngineType.AUTO),  # Enable auto-detection
        )
        # Diagrams with layers suggest D2
        assert definition.get_suggested_engine() == DiagramEngineType.D2

    def test_suggested_engine_with_animation(self):
        """Test suggested engine for animated diagrams."""
        definition = DiagramDefinition(
            boxes=[Box(id="a", label="A"), Box(id="b", label="B")],
            arrows=[Arrow(from_id="a", to_id="b", animated=True)],
            config=DiagramConfig(engine=DiagramEngineType.AUTO),  # Enable auto-detection
        )
        # Animated diagrams suggest D2
        assert definition.get_suggested_engine() == DiagramEngineType.D2


class TestEngineRegistry:
    """Tests for engine registry functions."""

    def test_get_engine_names(self):
        """Test getting all engine names."""
        names = get_engine_names()
        assert "matplotlib" in names
        assert "d2" in names
        assert "excalidraw" in names

    def test_get_available_engines(self):
        """Test getting all available engines."""
        engines = get_available_engines()
        assert len(engines) >= 3
        names = [e.name for e in engines]
        assert "matplotlib" in names

    def test_get_installed_engines(self):
        """Test getting installed engines."""
        installed = get_installed_engines()
        # Matplotlib should always be installed
        names = [e.name for e in installed]
        assert "matplotlib" in names

    def test_get_engine_by_name(self):
        """Test getting engine by name."""
        engine_class = get_engine("matplotlib")
        assert engine_class is not None
        assert engine_class.is_available()

    def test_get_engine_case_insensitive(self):
        """Test getting engine with different case."""
        engine1 = get_engine("matplotlib")
        engine2 = get_engine("MATPLOTLIB")
        assert engine1 == engine2

    def test_get_nonexistent_engine(self):
        """Test getting non-existent engine."""
        engine = get_engine("nonexistent_engine")
        assert engine is None

    def test_engine_summary(self):
        """Test engine summary output."""
        summary = engine_summary()
        assert "matplotlib" in summary.lower()
        assert "installed" in summary.lower()


class TestMatplotlibEngine:
    """Tests for matplotlib engine."""

    def test_engine_is_available(self):
        """Test matplotlib is always available."""
        engine_class = get_engine("matplotlib")
        assert engine_class.is_available()

    def test_engine_capabilities(self):
        """Test matplotlib capabilities."""
        engine_class = get_engine("matplotlib")
        info = engine_class.get_info()
        assert EngineCapability.DARK_MODE in info.capabilities
        assert "png" in info.formats
        assert "svg" in info.formats

    def test_generate_simple_diagram(self):
        """Test generating a simple diagram."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"

            definition = DiagramDefinition(
                title="Test Diagram",
                boxes=[
                    Box(id="a", label="Box A", x=0, y=0),
                    Box(id="b", label="Box B", x=2, y=0),
                ],
                arrows=[Arrow(from_id="a", to_id="b")],
            )

            generator = DiagramGenerator()
            result = generator.generate(definition, output_path)

            assert result.exists()
            assert result.suffix == ".png"
            assert result.stat().st_size > 0

    def test_generate_dark_mode(self):
        """Test generating dark mode diagram."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_dark.png"

            definition = DiagramDefinition(
                boxes=[Box(id="a", label="Box A", x=0, y=0)],
                config=DiagramConfig(dark_mode=True),
            )

            generator = DiagramGenerator()
            result = generator.generate(definition, output_path)

            assert result.exists()

    def test_generate_both_themes(self):
        """Test generating both light and dark themes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            definition = DiagramDefinition(
                boxes=[
                    Box(id="a", label="Box A", x=0, y=0),
                    Box(id="b", label="Box B", x=2, y=0),
                ],
                arrows=[Arrow(from_id="a", to_id="b")],
            )

            generator = DiagramGenerator()
            light_path, dark_path = generator.generate_both_themes(
                definition, output_dir, "test"
            )

            assert light_path.exists()
            assert dark_path.exists()
            assert "light" in light_path.name
            assert "dark" in dark_path.name


class TestD2Engine:
    """Tests for D2 engine."""

    @pytest.fixture
    def d2_available(self):
        """Check if D2 CLI is available."""
        return shutil.which("d2") is not None

    def test_engine_registered(self):
        """Test D2 engine is registered."""
        engine_class = get_engine("d2")
        assert engine_class is not None

    def test_engine_capabilities(self):
        """Test D2 capabilities."""
        engine_class = get_engine("d2")
        info = engine_class.get_info()
        assert EngineCapability.SKETCH_MODE in info.capabilities
        assert EngineCapability.ANIMATION in info.capabilities
        assert EngineCapability.LAYERS in info.capabilities

    def test_engine_install_hint(self):
        """Test D2 provides install hint."""
        engine_class = get_engine("d2")
        hint = engine_class.get_install_hint()
        assert "brew install d2" in hint or "d2lang.com" in hint

    @pytest.mark.skipif(
        shutil.which("d2") is None,
        reason="D2 CLI not installed",
    )
    def test_generate_with_d2(self):
        """Test generating with D2 engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.svg"

            definition = DiagramDefinition(
                boxes=[
                    Box(id="api", label="API", x=0, y=0),
                    Box(id="db", label="Database", style="cylinder", x=2, y=0),
                ],
                arrows=[Arrow(from_id="api", to_id="db", label="queries")],
                config=DiagramConfig(engine=DiagramEngineType.D2, format="svg"),
            )

            generator = DiagramGenerator()
            result = generator.generate(definition, output_path, engine="d2")

            assert result.exists()


class TestExcalidrawEngine:
    """Tests for Excalidraw engine."""

    def test_engine_registered(self):
        """Test Excalidraw engine is registered."""
        engine_class = get_engine("excalidraw")
        assert engine_class is not None

    def test_engine_always_available(self):
        """Test Excalidraw is always available (uses Kroki.io)."""
        engine_class = get_engine("excalidraw")
        assert engine_class.is_available()

    def test_engine_capabilities(self):
        """Test Excalidraw capabilities."""
        engine_class = get_engine("excalidraw")
        info = engine_class.get_info()
        assert EngineCapability.SKETCH_MODE in info.capabilities
        assert "excalidraw" in info.formats

    def test_generate_excalidraw_json(self):
        """Test generating Excalidraw JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.excalidraw"

            definition = DiagramDefinition(
                boxes=[
                    Box(id="a", label="Box A", x=0, y=0),
                    Box(id="b", label="Box B", x=2, y=0),
                ],
                arrows=[Arrow(from_id="a", to_id="b")],
                config=DiagramConfig(engine=DiagramEngineType.EXCALIDRAW),
            )

            generator = DiagramGenerator()
            result = generator.generate(definition, output_path, engine="excalidraw")

            assert result.exists()
            assert result.suffix == ".excalidraw"


class TestBrandAdapter:
    """Tests for brand adapter color resolution."""

    def test_get_engine_colors_light(self):
        """Test getting engine colors in light mode."""
        colors = get_engine_colors(None, None, dark_mode=False)
        assert "background" in colors
        assert "text" in colors
        assert "primary" in colors
        assert colors["background"].startswith("#")

    def test_get_engine_colors_dark(self):
        """Test getting engine colors in dark mode."""
        colors = get_engine_colors(None, None, dark_mode=True)
        # Dark mode should have different background
        light_colors = get_engine_colors(None, None, dark_mode=False)
        assert colors["background"] != light_colors["background"]

    def test_resolve_hex_color(self):
        """Test resolving hex color."""
        color = resolve_color("#ff0000", None, None, dark_mode=False)
        assert color == "#ff0000"

    def test_resolve_brand_token_without_brand(self):
        """Test resolving brand token without brand context."""
        # Without brand context, token is returned as-is for flexibility
        color = resolve_color("brand.primary", None, None, dark_mode=False)
        # Should return the token as-is when no brand context available
        assert isinstance(color, str)
        # Or test with a semantic shorthand which does resolve
        color = resolve_color("primary", None, None, dark_mode=False)
        assert color.startswith("#")

    def test_get_font_family_without_brand(self):
        """Test getting font without brand context."""
        font = get_font_family(None, None, "heading")  # brand, theme, role
        assert isinstance(font, str)
        assert len(font) > 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_diagram_function(self):
        """Test generate_diagram convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"

            definition = DiagramDefinition(
                boxes=[Box(id="a", label="A", x=0, y=0)],
            )

            result = generate_diagram(definition, output_path)
            assert result.exists()

    def test_generate_diagram_from_dict(self):
        """Test generate_diagram from dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"

            data = {
                "boxes": [{"id": "a", "label": "A", "x": 0, "y": 0}],
            }

            result = generate_diagram(data, output_path)
            assert result.exists()


class TestDiagramYAMLParsing:
    """Tests for YAML parsing."""

    def test_parse_yaml_with_engine_options(self):
        """Test parsing YAML with engine options."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("""
title: Test Diagram
config:
  engine: d2
  format: svg
  engine_options:
    sketch: true
    layout: elk
boxes:
  - id: api
    label: API Gateway
    style: rounded
arrows:
  - from: api
    to: api
    label: recursive
""")
            f.flush()

            definition = DiagramDefinition.from_yaml(Path(f.name))
            assert definition.title == "Test Diagram"
            assert definition.config.engine == DiagramEngineType.D2
            assert definition.config.engine_options.get("sketch") is True
            assert definition.config.engine_options.get("layout") == "elk"

            Path(f.name).unlink()

    def test_parse_yaml_with_layers(self):
        """Test parsing YAML with layers."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("""
boxes:
  - id: api
    label: API
    layer: frontend
  - id: db
    label: Database
    layer: backend
layers:
  - id: frontend
    label: Frontend Layer
    color: "#e0f0ff"
  - id: backend
    label: Backend Layer
    color: "#fff0e0"
arrows:
  - from: api
    to: db
""")
            f.flush()

            definition = DiagramDefinition.from_yaml(Path(f.name))
            assert len(definition.layers) == 2
            assert definition.boxes[0].layer == "frontend"
            assert definition.layers[0].label == "Frontend Layer"

            Path(f.name).unlink()
