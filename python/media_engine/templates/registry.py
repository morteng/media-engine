"""
Template Registry

Manages template loading with a three-tier priority system:
1. Project templates/ directory (user customizations)
2. Publication-specific templates
3. Built-in templates (package defaults)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape, ChoiceLoader

if TYPE_CHECKING:
    from ..core.project import Project


@dataclass
class TemplateInfo:
    """Information about a template."""
    
    name: str
    path: Path
    format: str  # html, pdf, pptx
    source: str  # builtin, project, publication
    description: str = ""
    extends: Optional[str] = None  # Parent template
    features: List[str] = field(default_factory=list)


def get_builtin_path() -> Path:
    """Get path to built-in templates directory."""
    return Path(__file__).parent / "html"


def get_builtin_templates() -> List[TemplateInfo]:
    """List all built-in templates."""
    templates = []
    builtin_path = get_builtin_path()
    
    if not builtin_path.exists():
        return templates
    
    for template_file in builtin_path.glob("*.html.j2"):
        name = template_file.stem.replace(".html", "")
        templates.append(TemplateInfo(
            name=name,
            path=template_file,
            format="html",
            source="builtin",
            description=_get_template_description(name),
        ))
    
    return templates


def _get_template_description(name: str) -> str:
    """Get description for built-in template."""
    descriptions = {
        "base": "Base HTML template with minimal styling",
        "documentation": "Technical documentation with sidebar navigation",
        "ebook": "Book-style layout with chapters and pagination",
        "report": "Professional report format",
        "presentation": "Web-based presentation slides",
        "article": "Single-page article layout",
    }
    return descriptions.get(name, "")


def get_template_path(format: str, name: str) -> Optional[Path]:
    """Get path to a built-in template by format and name."""
    builtin_path = get_builtin_path()
    
    if format == "html":
        template_path = builtin_path / f"{name}.html.j2"
        if template_path.exists():
            return template_path
    
    return None


class TemplateRegistry:
    """
    Registry for managing templates across tiers.
    
    Priority order:
    1. Project templates/ directory
    2. Publication-specific templates
    3. Built-in package templates
    """
    
    def __init__(self, project: "Project" = None, publication_path: Path = None):
        """
        Initialize template registry.
        
        Args:
            project: Project instance for project-level templates
            publication_path: Path to publication for publication-level templates
        """
        self.project = project
        self.publication_path = publication_path
        
        # Build template search paths (priority order)
        loaders = []
        
        # Tier 3: Project templates (highest priority)
        if project:
            project_templates = project.root / "templates"
            if project_templates.exists():
                loaders.append(FileSystemLoader(str(project_templates)))
        
        # Tier 3: Publication templates
        if publication_path:
            pub_templates = publication_path / "templates"
            if pub_templates.exists():
                loaders.append(FileSystemLoader(str(pub_templates)))
        
        # Tier 1-2: Built-in templates (lowest priority)
        builtin_path = get_builtin_path()
        if builtin_path.exists():
            loaders.append(FileSystemLoader(str(builtin_path)))
        
        # Create Jinja2 environment with combined loader
        self.env = Environment(
            loader=ChoiceLoader(loaders) if loaders else None,
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filters
        self._add_filters()
    
    def _add_filters(self):
        """Add custom Jinja2 filters."""
        
        def slugify(text: str) -> str:
            """Convert text to URL-friendly slug."""
            import re
            text = text.lower()
            text = re.sub(r"[^\w\s-]", "", text)
            text = re.sub(r"[-\s]+", "-", text)
            return text.strip("-")
        
        def format_date(date, format: str = "%B %d, %Y") -> str:
            """Format a date."""
            if hasattr(date, "strftime"):
                return date.strftime(format)
            return str(date)
        
        self.env.filters["slugify"] = slugify
        self.env.filters["format_date"] = format_date
    
    def get_template(self, format: str, name: str):
        """
        Get a template by format and name.
        
        Args:
            format: Template format (html, pdf, pptx)
            name: Template name
            
        Returns:
            Jinja2 Template object
        """
        if format == "html":
            template_name = f"{name}.html.j2"
        elif format == "pdf":
            template_name = f"pdf/{name}.html.j2"
        else:
            template_name = f"{name}.j2"
        
        return self.env.get_template(template_name)
    
    def has_template(self, format: str, name: str) -> bool:
        """Check if a template exists."""
        try:
            self.get_template(format, name)
            return True
        except Exception:
            return False
    
    def list_templates(self, format: str = None) -> List[TemplateInfo]:
        """
        List all available templates.
        
        Args:
            format: Optional format filter
            
        Returns:
            List of TemplateInfo objects
        """
        templates = []
        
        # Add built-in templates
        for info in get_builtin_templates():
            if format is None or info.format == format:
                templates.append(info)
        
        # Add project templates
        if self.project:
            project_templates = self.project.root / "templates"
            if project_templates.exists():
                for f in project_templates.glob("**/*.j2"):
                    template_format = self._guess_format(f)
                    if format is None or template_format == format:
                        templates.append(TemplateInfo(
                            name=f.stem.replace(".html", ""),
                            path=f,
                            format=template_format,
                            source="project",
                        ))
        
        return templates
    
    def _guess_format(self, path: Path) -> str:
        """Guess format from template path."""
        if ".html" in path.name:
            return "html"
        elif "pdf" in str(path):
            return "pdf"
        elif "pptx" in str(path):
            return "pptx"
        return "html"
    
    def render(
        self,
        format: str,
        name: str,
        **context,
    ) -> str:
        """
        Render a template with context.
        
        Args:
            format: Template format
            name: Template name
            **context: Template context variables
            
        Returns:
            Rendered template string
        """
        template = self.get_template(format, name)
        return template.render(**context)
    
    def get_component(self, name: str):
        """
        Get a component template.
        
        Components are reusable template fragments in the components/ directory.
        """
        return self.env.get_template(f"components/{name}.html.j2")
    
    def render_component(self, name: str, **context) -> str:
        """Render a component with context."""
        template = self.get_component(name)
        return template.render(**context)
