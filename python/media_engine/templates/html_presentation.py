"""
HTML Presentation Templates

Generates beautiful, interactive HTML slide presentations with:
- Smooth animations and transitions
- Keyboard navigation (arrow keys, space, escape)
- Fullscreen mode (F key)
- Speaker notes view (S key)
- Progress indicator
- Touch/swipe support
- Print-friendly mode
- Full project branding
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from jinja2 import Template

if TYPE_CHECKING:
    from ..brand import BrandContext
    from ..core.theme import Theme


@dataclass
class Slide:
    """A single slide in the presentation."""

    type: str  # title, content, section, quote, image, two_column
    title: str = ""
    subtitle: str = ""
    bullets: List[str] = field(default_factory=list)
    left_title: str = ""
    left_bullets: List[str] = field(default_factory=list)
    right_title: str = ""
    right_bullets: List[str] = field(default_factory=list)
    quote: str = ""
    author: str = ""
    image: str = ""
    caption: str = ""
    notes: str = ""


# Modern HTML Presentation Template
PRESENTATION_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang }}" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {% if fonts_css_path %}
    <link rel="stylesheet" href="{{ fonts_css_path }}">
    {% endif %}
    <link rel="stylesheet" href="{{ assets_path }}/css/presentation.css">
    <style>
        /* CSS Variables from Theme (dynamic values) */
        :root {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: {{ theme.dark.surface }};
            --bg-tertiary: {{ theme.dark.border }};
            --text-primary: {{ theme.dark.text }};
            --text-muted: {{ theme.dark.muted }};
            --accent-color: {{ theme.dark.accent }};
            --accent-secondary: {{ theme.colors.secondary }};
            --border-color: {{ theme.dark.border }};
            --font-heading: '{{ theme.typography.heading }}', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: '{{ theme.typography.code }}', 'SF Mono', Monaco, monospace;
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
    <div class="presentation" id="presentation">
        <!-- Top Bar -->
        <div class="top-bar">
            {% if logo_path %}
            <div>
                <img src="{{ logo_path }}" alt="{{ title }}" class="logo logo-dark">
                <img src="{{ logo_path_light }}" alt="{{ title }}" class="logo logo-light">
            </div>
            {% else %}
            <div></div>
            {% endif %}
            <div class="toolbar">
                <button class="toolbar-btn" id="theme-toggle" title="Toggle theme (T)">Theme</button>
                <button class="toolbar-btn" id="fullscreen-btn" title="Fullscreen (F)">Fullscreen</button>
                <button class="toolbar-btn" id="help-btn" title="Help (?)">?</button>
            </div>
        </div>

        <!-- Slides -->
        <div class="slides">
            {% for slide in slides %}
            <div class="slide slide--{{ slide.type }}{% if loop.first %} active{% endif %}" data-index="{{ loop.index0 }}" data-notes="{{ slide.notes | e }}">
                <div class="slide-content">
                    {% if slide.type == "title" %}
                        {% if logo_path and loop.first %}
                        <img src="{{ logo_path }}" alt="" class="logo logo-dark">
                        <img src="{{ logo_path_light }}" alt="" class="logo logo-light">
                        {% endif %}
                        <h1 class="slide-title">{{ slide.title }}</h1>
                        <div class="accent-bar"></div>
                        {% if slide.subtitle %}
                        <p class="slide-subtitle">{{ slide.subtitle }}</p>
                        {% endif %}

                    {% elif slide.type == "content" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        <div class="accent-bar"></div>
                        {% if slide.bullets %}
                        <ul class="bullets">
                            {% for bullet in slide.bullets %}
                            <li>{{ bullet }}</li>
                            {% endfor %}
                        </ul>
                        {% endif %}

                    {% elif slide.type == "section" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        {% if slide.subtitle %}
                        <p class="slide-subtitle">{{ slide.subtitle }}</p>
                        {% endif %}

                    {% elif slide.type == "quote" %}
                        <div class="quote-text">{{ slide.quote }}</div>
                        {% if slide.author %}
                        <div class="quote-author">— {{ slide.author }}</div>
                        {% endif %}

                    {% elif slide.type == "two_column" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        <div class="accent-bar"></div>
                        <div class="two-columns">
                            <div class="column">
                                {% if slide.left_title %}
                                <h3 class="column-title">{{ slide.left_title }}</h3>
                                {% endif %}
                                <ul class="bullets">
                                    {% for bullet in slide.left_bullets %}
                                    <li>{{ bullet }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                            <div class="column">
                                {% if slide.right_title %}
                                <h3 class="column-title">{{ slide.right_title }}</h3>
                                {% endif %}
                                <ul class="bullets">
                                    {% for bullet in slide.right_bullets %}
                                    <li>{{ bullet }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>

                    {% elif slide.type == "image" %}
                        <h2 class="slide-title">{{ slide.title }}</h2>
                        <div class="accent-bar"></div>
                        {% if slide.image %}
                        <img src="{{ slide.image }}" alt="{{ slide.title }}" class="slide-image">
                        {% endif %}
                        {% if slide.caption %}
                        <p class="image-caption">{{ slide.caption }}</p>
                        {% endif %}
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Navigation -->
        <div class="nav-controls">
            <button class="nav-btn" id="prev-btn" title="Previous (←)">←</button>
            <button class="nav-btn" id="next-btn" title="Next (→)">→</button>
        </div>

        <!-- Progress Bar -->
        <div class="progress-bar" id="progress-bar"></div>

        <!-- Slide Counter -->
        <div class="slide-counter">
            <span id="current-slide">1</span> / <span id="total-slides">{{ slides|length }}</span>
        </div>

        <!-- Speaker Notes -->
        <div class="speaker-notes" id="speaker-notes">
            <h4>Speaker Notes</h4>
            <div id="notes-content"></div>
        </div>

        <!-- Help Overlay -->
        <div class="help-overlay" id="help-overlay">
            <div class="help-content">
                <h3>Keyboard Shortcuts</h3>
                <div class="shortcut"><span>Next slide</span><kbd>→</kbd> <kbd>Space</kbd> <kbd>N</kbd></div>
                <div class="shortcut"><span>Previous slide</span><kbd>←</kbd> <kbd>P</kbd></div>
                <div class="shortcut"><span>First slide</span><kbd>Home</kbd></div>
                <div class="shortcut"><span>Last slide</span><kbd>End</kbd></div>
                <div class="shortcut"><span>Fullscreen</span><kbd>F</kbd></div>
                <div class="shortcut"><span>Speaker notes</span><kbd>S</kbd></div>
                <div class="shortcut"><span>Toggle theme</span><kbd>T</kbd></div>
                <div class="shortcut"><span>This help</span><kbd>?</kbd></div>
                <div class="shortcut"><span>Close overlay</span><kbd>Esc</kbd></div>
            </div>
        </div>
    </div>

    <script src="{{ assets_path }}/js/presentation.js"></script>
</body>
</html>
"""


class PresentationTemplate:
    """HTML presentation template renderer."""

    def __init__(self, theme: "Theme" = None, brand: "BrandContext" = None):
        """
        Initialize presentation template.

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
        self.template = Template(PRESENTATION_TEMPLATE)

    def render(
        self,
        title: str,
        slides: List[Slide],
        logo_path: Optional[str] = None,
        logo_path_light: Optional[str] = None,
        fonts_css_path: Optional[str] = None,
        assets_path: str = "../shared/assets",
        lang: str = "en",
    ) -> str:
        """Render the presentation to HTML."""
        return self.template.render(
            title=title,
            slides=slides,
            theme=self.theme,
            logo_path=logo_path,
            logo_path_light=logo_path_light
            or (logo_path.replace("logo.", "logo-light.") if logo_path else None),
            fonts_css_path=fonts_css_path,
            assets_path=assets_path,
            lang=lang,
            date=datetime.now().strftime("%Y-%m-%d"),
        )


def render_presentation(
    title: str,
    slides: List[Slide],
    theme: "Theme" = None,
    logo_path: Optional[str] = None,
    fonts_css_path: Optional[str] = None,
    assets_path: str = "../shared/assets",
    lang: str = "en",
    brand: "BrandContext" = None,
) -> str:
    """Convenience function to render a presentation."""
    template = PresentationTemplate(theme=theme, brand=brand)
    return template.render(
        title=title,
        slides=slides,
        logo_path=logo_path,
        fonts_css_path=fonts_css_path,
        assets_path=assets_path,
        lang=lang,
    )


def build_presentation_from_yaml(yaml_path: Path, theme: "Theme" = None) -> tuple[str, List[Slide]]:
    """
    Parse a YAML slide definition and return title and slides.

    Args:
        yaml_path: Path to YAML file
        theme: Optional theme

    Returns:
        Tuple of (title, slides)
    """
    import yaml

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    title = data.get("title", "Presentation")
    subtitle = data.get("subtitle", "")
    slides = []

    # Add title slide if defined at top level
    if title:
        slides.append(
            Slide(
                type="title",
                title=title,
                subtitle=subtitle,
            )
        )

    # Process slides
    for slide_data in data.get("slides", []):
        slide_type = slide_data.get("type", "content")

        slide = Slide(
            type=slide_type,
            title=slide_data.get("title", ""),
            subtitle=slide_data.get("subtitle", ""),
            bullets=slide_data.get("bullets", []),
            left_title=slide_data.get("left_title", ""),
            left_bullets=slide_data.get("left_bullets", []),
            right_title=slide_data.get("right_title", ""),
            right_bullets=slide_data.get("right_bullets", []),
            quote=slide_data.get("quote", ""),
            author=slide_data.get("author", ""),
            image=slide_data.get("image", ""),
            caption=slide_data.get("caption", ""),
            notes=slide_data.get("notes", ""),
        )
        slides.append(slide)

    return title, slides
