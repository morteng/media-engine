"""
HTML Index Templates

Generates navigation pages:
- Project index (root index.html)
- Language index (en/index.html, no/index.html)

Links all deliverables in an organized, branded way.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from jinja2 import Template

if TYPE_CHECKING:
    from ..brand import BrandContext
    from ..core.theme import Theme


@dataclass
class FormatLink:
    """A single format link (HTML, PDF, PPTX, etc.)."""

    file_type: str  # html, pdf, pptx, xlsx, mp4
    path: str
    label: str = ""  # Optional custom label


@dataclass
class DeliverableItem:
    """A deliverable item for the index."""

    name: str
    path: str
    description: str = ""
    icon: str = ""
    file_type: str = ""  # html, pdf, pptx, xlsx, mp4
    formats: List[FormatLink] = field(default_factory=list)  # Multiple format links


@dataclass
class DeliverableCategory:
    """Category of deliverables."""

    name: str
    icon: str = ""
    items: List[DeliverableItem] = field(default_factory=list)


@dataclass
class LanguageInfo:
    """Language information for project index."""

    code: str
    name: str
    path: str


# Project Index Template (root index.html)
PROJECT_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark" class="project-index">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} - Deliverables</title>
    <link rel="stylesheet" href="shared/fonts.css">
    <link rel="stylesheet" href="{{ assets_path }}/css/index.css">
    <style>
        /* CSS Variables - Theme System (dynamic values from theme) */
        :root {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: {{ theme.dark.surface }};
            --bg-tertiary: {{ theme.dark.border }};
            --text-primary: {{ theme.dark.text }};
            --text-muted: {{ theme.dark.muted }};
            --accent-color: {{ theme.dark.accent }};
            --border-color: {{ theme.dark.border }};
            --font-heading: '{{ theme.typography.heading }}', -apple-system, sans-serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, sans-serif;
        }

        [data-theme="light"] {
            --bg-primary: {{ theme.colors.background }};
            --bg-secondary: {{ theme.colors.surface }};
            --bg-tertiary: {{ theme.colors.border }};
            --text-primary: {{ theme.colors.text }};
            --text-muted: {{ theme.colors.muted }};
            --accent-color: {{ theme.colors.accent }};
            --border-color: {{ theme.colors.border }};
        }
    </style>
</head>
<body>
    <div class="top-bar">
        {% if logo_path %}
        <div>
            <img src="{{ logo_path }}" alt="{{ project_name }}" class="logo logo-dark">
            <img src="{{ logo_path.replace('logo.', 'logo-light.') }}" alt="{{ project_name }}" class="logo logo-light">
        </div>
        {% else %}
        <span></span>
        {% endif %}
        <button class="theme-toggle" id="theme-toggle">☀️ Light Mode</button>
    </div>

    <div class="container">
        <header>
            <h1>{{ project_name }}</h1>
            {% if tagline %}
            <p class="tagline">{{ tagline }}</p>
            {% endif %}
        </header>

        <div class="languages">
            {% for lang in languages %}
            <a href="{{ lang.path }}" class="language-card">
                <div class="language-flag">{{ lang.code | upper }}</div>
                <div class="language-name">{{ lang.name }}</div>
                <div class="language-desc">View {{ lang.name }} deliverables</div>
            </a>
            {% endfor %}
        </div>
    </div>

    <footer>
        <p>Generated {{ date }} by Media Engine</p>
    </footer>

    <script src="{{ assets_path }}/js/index.js"></script>
</body>
</html>"""


# Language Index Template (en/index.html)
LANGUAGE_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang_code }}" data-theme="dark" class="language-index">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ lang_name }} - {{ project_name }}</title>
    <link rel="stylesheet" href="../shared/fonts.css">
    <link rel="stylesheet" href="{{ assets_path }}/css/index.css">
    <style>
        /* CSS Variables - Theme System (dynamic values from theme) */
        :root {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: {{ theme.dark.surface }};
            --bg-tertiary: {{ theme.dark.border }};
            --text-primary: {{ theme.dark.text }};
            --text-muted: {{ theme.dark.muted }};
            --accent-color: {{ theme.dark.accent }};
            --border-color: {{ theme.dark.border }};
            --font-heading: '{{ theme.typography.heading }}', -apple-system, sans-serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, sans-serif;
        }

        [data-theme="light"] {
            --bg-primary: {{ theme.colors.background }};
            --bg-secondary: {{ theme.colors.surface }};
            --bg-tertiary: {{ theme.colors.border }};
            --text-primary: {{ theme.colors.text }};
            --text-muted: {{ theme.colors.muted }};
            --accent-color: {{ theme.colors.accent }};
            --border-color: {{ theme.colors.border }};
        }
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="top-bar-left">
            {% if logo_path %}
            <div>
                <img src="{{ logo_path }}" alt="{{ project_name }}" class="logo logo-dark">
                <img src="{{ logo_path.replace('logo.', 'logo-light.') }}" alt="{{ project_name }}" class="logo logo-light">
            </div>
            {% endif %}
            <a href="../index.html" class="back-link">← All Languages</a>
        </div>
        <button class="theme-toggle" id="theme-toggle">☀️ Light</button>
    </div>

    <div class="container">
        <h1 class="page-title">{{ lang_name }} Deliverables</h1>

        {% for category in categories %}
        <section class="category">
            <h2 class="category-title">
                <span class="category-icon">{{ category.icon }}</span>
                {{ category.name }}
            </h2>
            <div class="items">
                {% for item in category.items %}
                {% if item.formats %}
                {# Grouped item with multiple formats #}
                <div class="item-card">
                    <span class="item-icon">{{ item.icon }}</span>
                    <div class="item-info">
                        <div class="item-name">{{ item.name }}</div>
                        {% if item.description %}
                        <div class="item-desc">{{ item.description }}</div>
                        {% endif %}
                    </div>
                    <div class="format-links">
                        {% for fmt in item.formats %}
                        <a href="{{ fmt.path }}" class="format-badge{% if loop.first %} primary{% endif %}" {% if fmt.file_type in ['pdf', 'pptx', 'xlsx'] %}target="_blank"{% endif %}>{{ fmt.label or fmt.file_type }}</a>
                        {% endfor %}
                    </div>
                </div>
                {% elif item.file_type == 'mp4' %}
                <button class="item" data-video="{{ item.path }}" data-title="{{ item.name }}">
                    <span class="item-icon">{{ item.icon }}</span>
                    <div class="item-info">
                        <div class="item-name">{{ item.name }}</div>
                        {% if item.description %}
                        <div class="item-desc">{{ item.description }}</div>
                        {% endif %}
                    </div>
                    <span class="item-type">▶ play</span>
                </button>
                {% else %}
                <a href="{{ item.path }}" class="item" {% if item.file_type in ['pdf', 'pptx', 'xlsx'] %}target="_blank"{% endif %}>
                    <span class="item-icon">{{ item.icon }}</span>
                    <div class="item-info">
                        <div class="item-name">{{ item.name }}</div>
                        {% if item.description %}
                        <div class="item-desc">{{ item.description }}</div>
                        {% endif %}
                    </div>
                    <span class="item-type">{{ item.file_type }}</span>
                </a>
                {% endif %}
                {% endfor %}
            </div>
        </section>
        {% endfor %}
    </div>

    <!-- Video Player Modal -->
    <div class="video-modal" id="video-modal">
        <div class="video-modal-content">
            <button class="video-modal-close" id="video-close">✕</button>
            <video id="video-player" controls>
                <source src="" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div class="video-modal-title" id="video-title"></div>
            <a class="video-modal-download" id="video-download" href="" download>⬇ Download video</a>
        </div>
    </div>

    <footer>
        <p>Generated {{ date }} by Media Engine</p>
    </footer>

    <script src="{{ assets_path }}/js/index.js"></script>
</body>
</html>"""


class IndexTemplate:
    """Navigation index template renderer."""

    def __init__(self, theme: "Theme" = None, brand: "BrandContext" = None):
        """
        Initialize index template.

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
        self.project_template = Template(PROJECT_INDEX_TEMPLATE)
        self.language_template = Template(LANGUAGE_INDEX_TEMPLATE)

    def render_project_index(
        self,
        project_name: str,
        languages: List[LanguageInfo],
        tagline: str = "",
        logo_path: Optional[str] = None,
        assets_path: str = "shared/assets",
    ) -> str:
        """Render the root project index."""
        return self.project_template.render(
            project_name=project_name,
            languages=languages,
            tagline=tagline,
            logo_path=logo_path,
            assets_path=assets_path,
            theme=self.theme,
            date=datetime.now().strftime("%Y-%m-%d"),
        )

    def render_language_index(
        self,
        project_name: str,
        lang_code: str,
        lang_name: str,
        categories: List[DeliverableCategory],
        logo_path: Optional[str] = None,
        assets_path: str = "../shared/assets",
    ) -> str:
        """Render a language-specific index."""
        return self.language_template.render(
            project_name=project_name,
            lang_code=lang_code,
            lang_name=lang_name,
            categories=categories,
            logo_path=logo_path,
            assets_path=assets_path,
            theme=self.theme,
            date=datetime.now().strftime("%Y-%m-%d"),
        )


def render_project_index(
    project_name: str,
    languages: List[LanguageInfo],
    theme: "Theme" = None,
    tagline: str = "",
    logo_path: Optional[str] = None,
    brand: "BrandContext" = None,
    assets_path: str = "shared/assets",
) -> str:
    """Convenience function to render project index."""
    template = IndexTemplate(theme=theme, brand=brand)
    return template.render_project_index(project_name, languages, tagline, logo_path, assets_path)


def render_language_index(
    project_name: str,
    lang_code: str,
    lang_name: str,
    categories: List[DeliverableCategory],
    theme: "Theme" = None,
    logo_path: Optional[str] = None,
    brand: "BrandContext" = None,
    assets_path: str = "../shared/assets",
) -> str:
    """Convenience function to render language index."""
    template = IndexTemplate(theme=theme, brand=brand)
    return template.render_language_index(
        project_name, lang_code, lang_name, categories, logo_path, assets_path
    )
