"""
Template Components

Reusable template components for building output documents.
Components can be overridden by placing custom versions in project templates/components/.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader, ChoiceLoader

if TYPE_CHECKING:
    from ..core.project import Project
    from ..brand import BrandContext


class ComponentRegistry:
    """
    Registry for template components.
    
    Components are small, reusable template fragments like:
    - header: Page header with logo and navigation
    - footer: Page footer with copyright and links
    - toc: Table of contents
    - nav: Navigation sidebar
    - callout: Alert/info boxes
    - code_block: Styled code blocks
    """
    
    BUILTIN_COMPONENTS = [
        "header",
        "footer",
        "toc",
        "nav",
        "callout",
        "code_block",
        "breadcrumbs",
        "search",
        "pagination",
    ]
    
    def __init__(self, project: "Project" = None, brand: "BrandContext" = None):
        """
        Initialize component registry.
        
        Args:
            project: Project for finding custom components
            brand: BrandContext for styling
        """
        self.project = project
        self.brand = brand
        
        # Build loader chain
        loaders = []
        
        # Custom components (highest priority)
        if project:
            custom_path = project.root / "templates" / "components"
            if custom_path.exists():
                loaders.append(FileSystemLoader(str(custom_path)))
        
        # Built-in components
        builtin_path = Path(__file__).parent / "html" / "components"
        if builtin_path.exists():
            loaders.append(FileSystemLoader(str(builtin_path)))
        
        self.env = Environment(
            loader=ChoiceLoader(loaders) if loaders else None,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def render(self, name: str, **context) -> str:
        """
        Render a component.
        
        Args:
            name: Component name
            **context: Template context
            
        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.get_template(f"{name}.html.j2")
            return template.render(**context)
        except Exception:
            # Return empty string if component not found
            return ""
    
    def has_component(self, name: str) -> bool:
        """Check if a component exists."""
        try:
            self.env.get_template(f"{name}.html.j2")
            return True
        except Exception:
            return False
    
    def list_components(self) -> list:
        """List all available components."""
        components = []
        
        # Check for custom components
        if self.project:
            custom_path = self.project.root / "templates" / "components"
            if custom_path.exists():
                for f in custom_path.glob("*.html.j2"):
                    components.append({
                        "name": f.stem.replace(".html", ""),
                        "source": "custom",
                        "path": f,
                    })
        
        # Add built-in components
        for name in self.BUILTIN_COMPONENTS:
            if name not in [c["name"] for c in components]:
                components.append({
                    "name": name,
                    "source": "builtin",
                })
        
        return components


def render_component(
    name: str,
    project: "Project" = None,
    brand: "BrandContext" = None,
    **context,
) -> str:
    """
    Convenience function to render a component.
    
    Args:
        name: Component name
        project: Optional project for custom components
        brand: Optional brand for styling
        **context: Template context
        
    Returns:
        Rendered HTML string
    """
    registry = ComponentRegistry(project, brand)
    return registry.render(name, **context)


# Pre-built component renderers for common use cases
def render_header(
    title: str,
    logo: Optional[str] = None,
    nav_items: list = None,
    brand: "BrandContext" = None,
) -> str:
    """Render a page header component."""
    return render_component(
        "header",
        title=title,
        logo=logo,
        nav_items=nav_items or [],
        brand=brand,
    )


def render_footer(
    copyright_text: str = "",
    links: list = None,
    brand: "BrandContext" = None,
) -> str:
    """Render a page footer component."""
    return render_component(
        "footer",
        copyright_text=copyright_text,
        links=links or [],
        brand=brand,
    )


def render_toc(
    headings: list,
    max_depth: int = 3,
    include_numbers: bool = False,
) -> str:
    """Render a table of contents component."""
    return render_component(
        "toc",
        headings=headings,
        max_depth=max_depth,
        include_numbers=include_numbers,
    )


def render_callout(
    type: str,  # info, warning, success, error
    title: str = "",
    content: str = "",
) -> str:
    """Render a callout/alert component."""
    return render_component(
        "callout",
        type=type,
        title=title,
        content=content,
    )
