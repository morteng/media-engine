"""
Professional HTML Document Template

Full-featured HTML document with:
- Sidebar navigation with TOC
- Theme toggle (light/dark with persistence)
- Reading progress bar
- Back to top button
- Cover page
- Print-optimized styles
- Self-contained fonts option
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from jinja2 import Template

if TYPE_CHECKING:
    from ..brand import BrandContext
    from ..core.theme import Theme


@dataclass
class CoverConfig:
    """Cover page configuration."""

    title: str = ""
    subtitle: str = ""
    version: str = ""
    date: str = ""
    author: str = ""
    logo_path: Optional[str] = None


@dataclass
class ChapterConfig:
    """Chapter metadata."""

    id: str
    title: str
    number: int = 0
    version: str = ""
    status: str = "draft"
    last_modified: str = ""


@dataclass
class DocumentConfig:
    """Document generation configuration."""

    include_toc: bool = True
    include_cover: bool = True
    include_progress: bool = True
    include_back_to_top: bool = True
    default_theme: str = "dark"  # "light" or "dark"
    lang: str = "en"
    embed_fonts: bool = False
    use_local_fonts: bool = True  # Link to local fonts.css instead of Google CDN
    fonts_css_path: str = "../shared/fonts.css"
    fonts_path: str = "../shared/fonts"
    assets_path: str = "../shared/assets"  # Path to static CSS/JS assets


# The professional HTML template
DOCUMENT_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang }}" data-theme="{{ default_theme }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {% if embed_fonts %}
    <style>{{ font_faces }}</style>
    {% elif use_local_fonts %}
    <link rel="stylesheet" href="{{ fonts_css_path }}">
    {% else %}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family={{ theme.typography.heading | urlencode }}:wght@300;400;600;700&family={{ theme.typography.body | urlencode }}:wght@300;400;500;600;700&family={{ theme.typography.code | urlencode }}:wght@400;500;600&display=swap" rel="stylesheet">
    {% endif %}
    <link rel="stylesheet" href="{{ assets_path }}/css/document.css">
    <style>
        /* CSS Variables - Theme System (dynamic values from theme) */
        :root {
            /* Typography */
            --font-heading: '{{ theme.typography.heading }}', Georgia, serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-code: '{{ theme.typography.code }}', 'SF Mono', Monaco, monospace;
            --base-size: {{ theme.typography.base_size }}px;
            --scale: {{ theme.typography.scale }};
        }

        /* Dark theme (default) */
        :root, [data-theme="dark"] {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: #242120;
            --bg-tertiary: #2e2a28;
            --text-primary: {{ theme.dark.text }};
            --text-secondary: #b8b2ac;
            --text-muted: {{ theme.dark.muted }};
            --border-color: {{ theme.dark.border }};
            --accent-color: {{ theme.dark.accent }};
            --accent-hover: #e8917a;
            --accent-light: rgba(212, 119, 90, 0.15);
        }

        [data-theme="light"] {
            --bg-primary: {{ theme.colors.background }};
            --bg-secondary: #f7f4f1;
            --bg-tertiary: #efe9e4;
            --text-primary: {{ theme.colors.text }};
            --text-secondary: {{ theme.colors.secondary }};
            --text-muted: {{ theme.colors.muted }};
            --border-color: {{ theme.colors.border }};
            --accent-color: {{ theme.colors.accent }};
            --accent-hover: #a84832;
            --accent-light: #fdf6f3;
        }
    </style>
</head>
<body>
    {% if include_progress %}
    <div class="progress-bar">
        <div class="progress-bar-fill" id="progress"></div>
    </div>
    {% endif %}

    <div class="layout">
        <nav class="sidebar" id="sidebar">
            <div class="sidebar-header">
                {% if logo_path %}
                <img src="{{ logo_path }}" alt="Logo" class="sidebar-logo">
                {% endif %}
                <div class="sidebar-title">{{ title }}</div>
                {% if version %}
                <div class="sidebar-version">Version {{ version }}</div>
                {% endif %}
            </div>
            <ul class="toc">
                {% for chapter in chapters %}
                <li class="toc-item" data-chapter="{{ chapter.id }}">
                    <a class="toc-link" href="#{{ chapter.id }}">{{ chapter.title }}</a>
                </li>
                {% endfor %}
            </ul>
        </nav>

        <div class="topbar">
            <button class="topbar-btn" id="theme-toggle">
                <span id="theme-icon">☀️</span>
                <span id="theme-text">Light</span>
            </button>
            <button class="topbar-btn" onclick="window.print()">
                🖨️ Print
            </button>
        </div>

        <main class="main">
            <div class="content">
                {% if include_cover and cover %}
                <div class="cover">
                    <h1>{{ cover.title }}</h1>
                    {% if cover.subtitle %}
                    <div class="cover-subtitle">{{ cover.subtitle }}</div>
                    {% endif %}
                    <div class="cover-meta">
                        {% if cover.version %}
                        <span>Version {{ cover.version }}</span>
                        {% endif %}
                        {% if cover.date %}
                        <span>{{ cover.date }}</span>
                        {% endif %}
                        {% if cover.author %}
                        <span>{{ cover.author }}</span>
                        {% endif %}
                    </div>
                </div>
                {% endif %}

                {{ content }}
            </div>
        </main>
    </div>

    {% if include_back_to_top %}
    <button class="back-to-top" id="back-to-top">↑</button>
    {% endif %}

    <script src="{{ assets_path }}/js/document.js"></script>
</body>
</html>"""


class DocumentTemplate:
    """Professional HTML document template renderer."""

    def __init__(self, theme: "Theme" = None, brand: "BrandContext" = None):
        """
        Initialize document template.

        Args:
            theme: Legacy Theme for styling (deprecated, use brand instead)
            brand: BrandContext for unified brand access (recommended)
        """
        if brand:
            # Convert BrandContext to Theme for template compatibility
            self.theme = brand.to_legacy_theme()
        else:
            from ..core.theme import COPPER_AND_CREAM

            self.theme = theme or COPPER_AND_CREAM
        self.template = Template(DOCUMENT_TEMPLATE)

    def render(
        self,
        content: str,
        title: str,
        chapters: List[ChapterConfig] = None,
        cover: CoverConfig = None,
        config: DocumentConfig = None,
    ) -> str:
        """
        Render the document template.

        Args:
            content: HTML content
            title: Document title
            chapters: List of chapter configs for TOC
            cover: Cover page configuration
            config: Document configuration

        Returns:
            Complete HTML document
        """
        config = config or DocumentConfig()
        chapters = chapters or []

        return self.template.render(
            title=title,
            theme=self.theme,
            content=content,
            chapters=chapters,
            cover=cover,
            include_cover=config.include_cover and cover is not None,
            include_toc=config.include_toc,
            include_progress=config.include_progress,
            include_back_to_top=config.include_back_to_top,
            default_theme=config.default_theme,
            lang=config.lang,
            embed_fonts=config.embed_fonts,
            use_local_fonts=config.use_local_fonts,
            fonts_css_path=config.fonts_css_path,
            fonts_path=config.fonts_path,
            assets_path=config.assets_path,
            version=cover.version if cover else "",
            logo_path=cover.logo_path if cover else None,
            font_faces="",  # TODO: Add embedded font faces
        )


def render_document(
    content: str,
    title: str,
    theme: "Theme" = None,
    chapters: List[ChapterConfig] = None,
    cover: CoverConfig = None,
    config: DocumentConfig = None,
    brand: "BrandContext" = None,
) -> str:
    """Convenience function to render a document."""
    template = DocumentTemplate(theme=theme, brand=brand)
    return template.render(content, title, chapters, cover, config)
