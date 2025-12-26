"""
Layout Presets

Tier 2: Preset-based customization for output generation.
Presets define layout, features, and styling options that sit between
zero-config (Tier 1) and full template control (Tier 3).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PresetFeatures:
    """Feature toggles for a preset."""
    
    # Navigation & Structure
    toc: bool = True
    navigation: bool = True
    breadcrumbs: bool = False
    search: bool = False
    
    # Content Features
    code_highlighting: bool = True
    callouts: bool = True
    footnotes: bool = True
    
    # Visual Features
    dark_mode: bool = True
    print_friendly: bool = True
    responsive: bool = True
    
    # Interactivity
    collapsible_sections: bool = False
    copy_code_buttons: bool = True
    anchor_links: bool = True
    
    # Layout Options
    sidebar: bool = False
    header: bool = True
    footer: bool = True
    cover_page: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "toc": self.toc,
            "navigation": self.navigation,
            "breadcrumbs": self.breadcrumbs,
            "search": self.search,
            "code_highlighting": self.code_highlighting,
            "callouts": self.callouts,
            "footnotes": self.footnotes,
            "dark_mode": self.dark_mode,
            "print_friendly": self.print_friendly,
            "responsive": self.responsive,
            "collapsible_sections": self.collapsible_sections,
            "copy_code_buttons": self.copy_code_buttons,
            "anchor_links": self.anchor_links,
            "sidebar": self.sidebar,
            "header": self.header,
            "footer": self.footer,
            "cover_page": self.cover_page,
        }


@dataclass
class LayoutPreset:
    """
    Layout preset configuration.
    
    Presets provide pre-configured layouts for different document types.
    """
    
    name: str
    description: str
    template: str  # Template name to use
    features: PresetFeatures = field(default_factory=PresetFeatures)
    
    # Styling overrides
    max_width: str = "800px"
    font_scale: float = 1.0
    line_height: float = 1.7
    
    # Format-specific settings
    formats: List[str] = field(default_factory=lambda: ["html", "pdf"])
    
    # CSS classes to add to body
    body_classes: List[str] = field(default_factory=list)
    
    # Additional CSS
    custom_css: str = ""
    
    def __post_init__(self):
        if isinstance(self.features, dict):
            self.features = PresetFeatures(**self.features)


# Built-in presets
PRESETS: Dict[str, LayoutPreset] = {
    "documentation": LayoutPreset(
        name="documentation",
        description="Technical documentation with sidebar navigation",
        template="documentation",
        features=PresetFeatures(
            toc=True,
            navigation=True,
            sidebar=True,
            search=True,
            code_highlighting=True,
            copy_code_buttons=True,
            breadcrumbs=True,
            collapsible_sections=True,
        ),
        max_width="1200px",
        body_classes=["docs-layout", "sidebar-visible"],
    ),
    
    "ebook": LayoutPreset(
        name="ebook",
        description="Book-style layout with chapters and pagination",
        template="ebook",
        features=PresetFeatures(
            toc=True,
            navigation=True,
            print_friendly=True,
            cover_page=True,
            footnotes=True,
            sidebar=False,
        ),
        max_width="700px",
        font_scale=1.1,
        line_height=1.8,
        body_classes=["ebook-layout"],
    ),
    
    "report": LayoutPreset(
        name="report",
        description="Professional report format",
        template="report",
        features=PresetFeatures(
            toc=True,
            cover_page=True,
            print_friendly=True,
            footnotes=True,
            header=True,
            footer=True,
        ),
        max_width="800px",
        body_classes=["report-layout"],
    ),
    
    "article": LayoutPreset(
        name="article",
        description="Single-page article layout",
        template="article",
        features=PresetFeatures(
            toc=False,
            navigation=False,
            header=True,
            footer=True,
            responsive=True,
        ),
        max_width="700px",
        line_height=1.8,
        body_classes=["article-layout"],
    ),
    
    "presentation": LayoutPreset(
        name="presentation",
        description="Web-based presentation slides",
        template="presentation",
        features=PresetFeatures(
            toc=False,
            navigation=True,
            dark_mode=True,
            responsive=False,  # Fixed aspect ratio
        ),
        max_width="100%",
        formats=["html"],
        body_classes=["presentation-layout"],
    ),
    
    "minimal": LayoutPreset(
        name="minimal",
        description="Clean, minimal layout with no extras",
        template="base",
        features=PresetFeatures(
            toc=False,
            navigation=False,
            sidebar=False,
            header=False,
            footer=False,
            dark_mode=False,
        ),
        max_width="800px",
        body_classes=["minimal-layout"],
    ),
}


def get_preset(name: str) -> Optional[LayoutPreset]:
    """
    Get a preset by name.
    
    Args:
        name: Preset name
        
    Returns:
        LayoutPreset or None if not found
    """
    return PRESETS.get(name)


def get_all_presets() -> List[LayoutPreset]:
    """Get all available presets."""
    return list(PRESETS.values())


def create_custom_preset(
    base: str = "minimal",
    name: str = "custom",
    **overrides,
) -> LayoutPreset:
    """
    Create a custom preset based on an existing one.
    
    Args:
        base: Base preset name to extend
        name: Name for the custom preset
        **overrides: Values to override
        
    Returns:
        New LayoutPreset with overrides applied
    """
    base_preset = get_preset(base)
    if not base_preset:
        base_preset = PRESETS["minimal"]
    
    # Create new preset with overrides
    preset_dict = {
        "name": name,
        "description": overrides.get("description", f"Custom preset based on {base}"),
        "template": overrides.get("template", base_preset.template),
        "max_width": overrides.get("max_width", base_preset.max_width),
        "font_scale": overrides.get("font_scale", base_preset.font_scale),
        "line_height": overrides.get("line_height", base_preset.line_height),
        "formats": overrides.get("formats", base_preset.formats.copy()),
        "body_classes": overrides.get("body_classes", base_preset.body_classes.copy()),
        "custom_css": overrides.get("custom_css", base_preset.custom_css),
    }
    
    # Handle features
    if "features" in overrides:
        preset_dict["features"] = overrides["features"]
    else:
        preset_dict["features"] = base_preset.features
    
    return LayoutPreset(**preset_dict)
