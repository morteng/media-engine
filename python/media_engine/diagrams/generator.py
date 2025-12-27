"""
Diagram Generator Module

High-level API for diagram generation with backward compatibility.
Delegates to pluggable engines for actual rendering.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from .definition import (
    DiagramDefinition,
    DiagramEngineType,
)
from .engines import get_engine
from .engines.matplotlib_engine import MatplotlibEngine

if TYPE_CHECKING:
    from ..brand import BrandContext
    from ..core.project import Project
    from ..core.theme import Theme


class DiagramGenerator:
    """
    Generate diagrams from definitions.

    This class provides a high-level interface for diagram generation
    with support for multiple engines. It maintains backward compatibility
    with the original API while delegating to engine implementations.

    Args:
        theme: Legacy Theme object for colors (optional)
        brand: BrandContext for colors/fonts (preferred, optional)
        engine: Default engine to use (optional, defaults to matplotlib)

    Example:
        >>> from media_engine.diagrams import DiagramGenerator, DiagramDefinition
        >>> generator = DiagramGenerator()
        >>> definition = DiagramDefinition.from_yaml("diagram.yaml")
        >>> generator.generate(definition, "output.png")
    """

    def __init__(
        self,
        theme: Optional["Theme"] = None,
        brand: Optional["BrandContext"] = None,
        engine: Optional[str] = None,
    ):
        """Initialize the generator with theme/brand and default engine."""
        self.theme = theme
        self.brand = brand
        self._default_engine = engine or "matplotlib"

        # For backward compatibility, also store raw theme
        if theme is None and brand is None:
            try:
                from ..core.theme import COPPER_AND_CREAM

                self.theme = COPPER_AND_CREAM
            except ImportError:
                pass

    def generate(
        self,
        definition: DiagramDefinition,
        output_path: Path,
        engine: Optional[str] = None,
    ) -> Path:
        """
        Generate diagram and save to file.

        Args:
            definition: Diagram definition
            output_path: Output file path
            engine: Engine to use (overrides default and config)

        Returns:
            Path to generated file
        """
        output_path = Path(output_path)

        # Determine engine to use
        engine_name = engine or definition.config.engine.value
        if engine_name == "auto":
            engine_name = definition.get_suggested_engine().value

        # Get engine class
        engine_class = get_engine(engine_name)
        if engine_class is None:
            # Fallback to matplotlib
            engine_class = MatplotlibEngine

        # Check availability
        if not engine_class.is_available():
            # Warn and fallback to matplotlib
            import warnings

            warnings.warn(
                f"Engine '{engine_name}' is not available, falling back to matplotlib. "
                f"Hint: {engine_class.get_install_hint()}"
            )
            engine_class = MatplotlibEngine

        # Create engine instance
        engine_instance = engine_class(brand=self.brand, theme=self.theme)

        # Generate
        return engine_instance.generate(definition, output_path)

    def generate_both_themes(
        self,
        definition: DiagramDefinition,
        output_dir: Path,
        base_name: str,
        engine: Optional[str] = None,
    ) -> tuple[Path, Path]:
        """
        Generate both light and dark theme versions.

        Args:
            definition: Diagram definition
            output_dir: Output directory
            base_name: Base filename (without extension)
            engine: Engine to use (optional)

        Returns:
            Tuple of (light_path, dark_path)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine engine
        engine_name = engine or definition.config.engine.value
        if engine_name == "auto":
            engine_name = definition.get_suggested_engine().value

        engine_class = get_engine(engine_name)
        if engine_class is None or not engine_class.is_available():
            engine_class = MatplotlibEngine

        # Create engine instance
        engine_instance = engine_class(brand=self.brand, theme=self.theme)

        # Generate both themes
        return engine_instance.generate_both_themes(definition, output_dir, base_name)


# Convenience functions for backward compatibility


def generate_diagram(
    definition: Union[DiagramDefinition, dict, Path],
    output_path: Path,
    theme: Optional["Theme"] = None,
    brand: Optional["BrandContext"] = None,
    engine: Optional[str] = None,
) -> Path:
    """
    Convenience function to generate a diagram.

    Args:
        definition: Diagram definition (object, dict, or YAML path)
        output_path: Output file path
        theme: Legacy Theme for colors (optional)
        brand: BrandContext for colors/fonts (optional)
        engine: Engine to use (optional)

    Returns:
        Path to generated file
    """
    generator = DiagramGenerator(theme=theme, brand=brand)

    if isinstance(definition, Path):
        definition = DiagramDefinition.from_yaml(definition)
    elif isinstance(definition, dict):
        definition = DiagramDefinition.from_dict(definition)

    return generator.generate(definition, output_path, engine=engine)


def generate_diagram_set(
    definition: Union[DiagramDefinition, dict, Path],
    output_dir: Path,
    base_name: str,
    theme: Optional["Theme"] = None,
    brand: Optional["BrandContext"] = None,
    engine: Optional[str] = None,
) -> tuple[Path, Path]:
    """
    Generate both light and dark theme versions.

    Args:
        definition: Diagram definition (object, dict, or YAML path)
        output_dir: Output directory
        base_name: Base filename (without extension)
        theme: Legacy Theme for colors (optional)
        brand: BrandContext for colors/fonts (optional)
        engine: Engine to use (optional)

    Returns:
        Tuple of (light_path, dark_path)
    """
    generator = DiagramGenerator(theme=theme, brand=brand)

    if isinstance(definition, Path):
        definition = DiagramDefinition.from_yaml(definition)
    elif isinstance(definition, dict):
        definition = DiagramDefinition.from_dict(definition)

    return generator.generate_both_themes(definition, output_dir, base_name, engine=engine)


def build_diagrams(
    project: "Project",
    language: Optional[str] = None,
    engine_override: Optional[str] = None,
    dark_mode: bool = False,
    output_dir: Optional[Path] = None,
) -> list[Path]:
    """
    Build all diagrams in a project.

    Args:
        project: Project instance
        language: Language to build (default: source language)
        engine_override: Override engine for all diagrams
        dark_mode: Generate dark mode only (else generates both)
        output_dir: Custom output directory (optional)

    Returns:
        List of generated file paths
    """

    lang = language or project.source_language
    diagrams_dir = project.get_content_path(lang, "diagrams")

    if not diagrams_dir.exists():
        return []

    # Output directory
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = project.output_dir / lang / "diagrams"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Get brand context if available
    brand = getattr(project, "brand_context", None)
    theme = getattr(project, "theme", None)

    generator = DiagramGenerator(brand=brand, theme=theme)

    generated = []
    for diagram_file in sorted(diagrams_dir.glob("*.yaml")):
        definition = DiagramDefinition.from_yaml(diagram_file)
        base_name = diagram_file.stem

        # Override engine if specified
        if engine_override:
            definition.config.engine = DiagramEngineType(engine_override)

        if dark_mode:
            # Generate dark mode only
            definition.config.dark_mode = True
            output = out_dir / f"{base_name}_dark.{definition.config.format}"
            result = generator.generate(definition, output)
            generated.append(result)
        else:
            # Generate both themes
            light_path, dark_path = generator.generate_both_themes(
                definition, out_dir, base_name
            )
            generated.extend([light_path, dark_path])

    return generated
