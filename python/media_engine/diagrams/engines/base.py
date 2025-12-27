"""
Diagram Engine Base Module

Abstract base class and types for diagram engines.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ...brand import BrandContext
    from ...core.theme import Theme
    from ..definition import DiagramDefinition


class EngineCapability(Enum):
    """Engine capabilities for feature detection."""

    DARK_MODE = "dark_mode"  # Supports dark mode rendering
    SKETCH_MODE = "sketch_mode"  # Hand-drawn appearance
    ANIMATION = "animation"  # Animated outputs
    INTERACTIVE = "interactive"  # Interactive HTML output
    LAYERS = "layers"  # Layer support
    GROUPS = "groups"  # Grouping elements
    CUSTOM_SHAPES = "custom_shapes"  # Beyond box/circle
    ICONS = "icons"  # Icon libraries
    CODE_BLOCKS = "code_blocks"  # Syntax-highlighted code
    MARKDOWN = "markdown"  # Markdown in labels
    BIDIRECTIONAL = "bidirectional"  # Two-way arrows
    PORTS = "ports"  # Connection port specification
    CUSTOM_FONTS = "custom_fonts"  # Custom font support


@dataclass
class EngineInfo:
    """Engine metadata and capabilities."""

    name: str
    version: str
    capabilities: list[EngineCapability] = field(default_factory=list)
    formats: list[str] = field(default_factory=list)  # Output formats: png, svg, pdf, html
    description: str = ""
    installed: bool = True

    def has_capability(self, capability: EngineCapability) -> bool:
        """Check if engine has a specific capability."""
        return capability in self.capabilities

    def supports_format(self, fmt: str) -> bool:
        """Check if engine supports an output format."""
        return fmt.lower() in [f.lower() for f in self.formats]


class DiagramEngine(ABC):
    """
    Abstract base class for diagram engines.

    All diagram engines must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(
        self,
        brand: Optional["BrandContext"] = None,
        theme: Optional["Theme"] = None,
    ):
        """
        Initialize engine with brand context.

        Args:
            brand: BrandContext for colors/fonts (recommended)
            theme: Legacy Theme fallback
        """
        self.brand = brand
        self.theme = theme
        self._colors_cache: dict[bool, dict[str, str]] = {}

    @classmethod
    @abstractmethod
    def get_info(cls) -> EngineInfo:
        """
        Get engine metadata and capabilities.

        Returns:
            EngineInfo with name, version, capabilities, and supported formats
        """
        pass

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """
        Check if engine dependencies are installed.

        Returns:
            True if engine can be used, False otherwise
        """
        pass

    @abstractmethod
    def generate(
        self,
        definition: "DiagramDefinition",
        output_path: Path,
        engine_options: Optional[dict[str, Any]] = None,
    ) -> Path:
        """
        Generate diagram from definition.

        Args:
            definition: Complete diagram definition
            output_path: Where to save output
            engine_options: Engine-specific options (overrides definition.config.engine_options)

        Returns:
            Path to generated file
        """
        pass

    def generate_both_themes(
        self,
        definition: "DiagramDefinition",
        output_dir: Path,
        base_name: str,
    ) -> tuple[Path, Path]:
        """
        Generate both light and dark theme versions.

        Args:
            definition: Diagram definition
            output_dir: Output directory
            base_name: Base filename (without extension)

        Returns:
            Tuple of (light_path, dark_path)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        fmt = definition.config.format

        # Generate light theme
        original_dark_mode = definition.config.dark_mode
        definition.config.dark_mode = False
        light_path = output_dir / f"{base_name}_light.{fmt}"
        self.generate(definition, light_path)

        # Generate dark theme
        definition.config.dark_mode = True
        dark_path = output_dir / f"{base_name}_dark.{fmt}"
        self.generate(definition, dark_path)

        # Restore original setting
        definition.config.dark_mode = original_dark_mode

        return light_path, dark_path

    def get_colors(self, dark_mode: bool = False) -> dict[str, str]:
        """
        Get color palette from brand context.

        Colors are cached per dark_mode setting.

        Args:
            dark_mode: Whether to get dark mode colors

        Returns:
            Dictionary of color names to hex values
        """
        if dark_mode not in self._colors_cache:
            from ..brand_adapter import get_engine_colors

            self._colors_cache[dark_mode] = get_engine_colors(
                self.brand, self.theme, dark_mode
            )
        return self._colors_cache[dark_mode]

    def resolve_color(
        self,
        color_value: Optional[str],
        dark_mode: bool = False,
        default_key: str = "primary",
    ) -> str:
        """
        Resolve a color value (hex or brand token).

        Args:
            color_value: Color specification
            dark_mode: Whether to use dark mode
            default_key: Default color key if value is None

        Returns:
            Resolved hex color
        """
        from ..brand_adapter import resolve_color

        return resolve_color(
            color_value, self.brand, self.theme, dark_mode, default_key
        )

    def get_font_family(self, role: str = "body") -> str:
        """
        Get font family for a role.

        Args:
            role: Font role - "heading", "body", or "code"

        Returns:
            Font family name
        """
        from ..brand_adapter import get_font_family

        return get_font_family(self.brand, self.theme, role)

    @classmethod
    def get_install_hint(cls) -> str:
        """
        Get installation instructions for this engine.

        Returns:
            Human-readable installation instructions
        """
        return f"Engine '{cls.get_info().name}' requires additional dependencies."

    def validate_definition(self, definition: "DiagramDefinition") -> list[str]:
        """
        Validate diagram definition for this engine.

        Returns list of warning messages for unsupported features.

        Args:
            definition: Diagram definition to validate

        Returns:
            List of warning messages (empty if all OK)
        """
        warnings = []
        info = self.get_info()

        # Check for unsupported features
        if definition.layers and not info.has_capability(EngineCapability.LAYERS):
            warnings.append(f"Engine '{info.name}' does not support layers")

        if definition.groups and not info.has_capability(EngineCapability.GROUPS):
            warnings.append(f"Engine '{info.name}' does not support groups")

        for arrow in definition.arrows:
            if arrow.animated and not info.has_capability(EngineCapability.ANIMATION):
                warnings.append(
                    f"Engine '{info.name}' does not support animated arrows"
                )
                break

        for arrow in definition.arrows:
            if arrow.bidirectional and not info.has_capability(
                EngineCapability.BIDIRECTIONAL
            ):
                warnings.append(
                    f"Engine '{info.name}' does not support bidirectional arrows"
                )
                break

        for box in definition.boxes:
            if box.icon and not info.has_capability(EngineCapability.ICONS):
                warnings.append(f"Engine '{info.name}' does not support icons")
                break

        # Check output format
        if not info.supports_format(definition.config.format):
            warnings.append(
                f"Engine '{info.name}' may not support format '{definition.config.format}'"
            )

        return warnings
