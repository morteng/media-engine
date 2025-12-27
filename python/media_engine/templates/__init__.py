"""
Media Engine Templates Module

Three-tier template system for output generation:

Tier 1: Zero-Config (Brand-Driven)
    - Automatic styling from brand.yaml
    - No template configuration needed
    - Works out of the box

Tier 2: Preset-Based Customization
    - Layout presets: documentation, ebook, report, presentation
    - Feature toggles: toc, navigation, print_friendly
    - Configure in publication.yaml

Tier 3: Full Template Control
    - Custom Jinja2 templates in project templates/ directory
    - Component overrides
    - Full control over output structure

Usage:
    from media_engine.templates import TemplateRegistry, get_preset

    # Get preset configuration
    preset = get_preset("documentation")

    # Load template
    registry = TemplateRegistry(project)
    template = registry.get_template("html", preset.template)
"""

from .components import (
    ComponentRegistry,
    render_component,
)
from .presets import (
    PRESETS,
    LayoutPreset,
    PresetFeatures,
    get_all_presets,
    get_preset,
)
from .registry import (
    TemplateInfo,
    TemplateRegistry,
    get_builtin_templates,
    get_template_path,
)

__all__ = [
    # Registry
    "TemplateRegistry",
    "TemplateInfo",
    "get_builtin_templates",
    "get_template_path",
    # Presets
    "LayoutPreset",
    "PresetFeatures",
    "get_preset",
    "get_all_presets",
    "PRESETS",
    # Components
    "ComponentRegistry",
    "render_component",
]
