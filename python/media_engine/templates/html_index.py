"""
HTML Index Templates

Generates navigation pages:
- Project index (root index.html)
- Language index (en/index.html, no/index.html)

Links all deliverables in an organized, branded way.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING
from datetime import datetime

from jinja2 import Template

if TYPE_CHECKING:
    from ..core.theme import Theme


@dataclass
class DeliverableItem:
    """A deliverable item for the index."""
    name: str
    path: str
    description: str = ""
    icon: str = ""
    file_type: str = ""  # html, pdf, pptx, xlsx, mp4


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
PROJECT_INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} - Deliverables</title>
    <style>
        :root {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: #242120;
            --text-primary: {{ theme.dark.text }};
            --text-secondary: #b8b2ac;
            --text-muted: {{ theme.dark.muted }};
            --accent-color: {{ theme.dark.accent }};
            --border-color: {{ theme.dark.border }};
            --font-heading: '{{ theme.typography.heading }}', Georgia, serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, sans-serif;
        }

        [data-theme="light"] {
            --bg-primary: {{ theme.colors.background }};
            --bg-secondary: #f7f4f1;
            --text-primary: {{ theme.colors.text }};
            --text-secondary: {{ theme.colors.secondary }};
            --text-muted: {{ theme.colors.muted }};
            --accent-color: {{ theme.colors.accent }};
            --border-color: {{ theme.colors.border }};
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: var(--font-body);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 60px 20px;
        }

        .container {
            max-width: 800px;
            width: 100%;
        }

        header {
            text-align: center;
            margin-bottom: 60px;
        }

        .logo {
            max-width: 150px;
            height: auto;
            margin-bottom: 24px;
        }

        h1 {
            font-family: var(--font-heading);
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 12px;
            letter-spacing: -0.02em;
        }

        .tagline {
            color: var(--text-muted);
            font-size: 1.1rem;
        }

        .languages {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }

        .language-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 32px;
            text-decoration: none;
            transition: all 0.2s ease;
        }

        .language-card:hover {
            border-color: var(--accent-color);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        }

        .language-flag {
            font-size: 2rem;
            margin-bottom: 16px;
        }

        .language-name {
            font-family: var(--font-heading);
            font-size: 1.5rem;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .language-desc {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 16px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 14px;
        }

        .theme-toggle:hover {
            background: var(--bg-primary);
            color: var(--text-primary);
        }

        footer {
            margin-top: auto;
            padding-top: 40px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <button class="theme-toggle" id="theme-toggle">☀️ Light Mode</button>

    <div class="container">
        <header>
            {% if logo_path %}
            <img src="{{ logo_path }}" alt="{{ project_name }}" class="logo">
            {% endif %}
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

    <script>
        const toggle = document.getElementById('theme-toggle');
        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            toggle.textContent = theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode';
        }
        const saved = localStorage.getItem('theme') || 'dark';
        setTheme(saved);
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'light' ? 'dark' : 'light');
        });
    </script>
</body>
</html>'''


# Language Index Template (en/index.html)
LANGUAGE_INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="{{ lang_code }}" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ lang_name }} - {{ project_name }}</title>
    <style>
        :root {
            --bg-primary: {{ theme.dark.background }};
            --bg-secondary: #242120;
            --bg-tertiary: #2e2a28;
            --text-primary: {{ theme.dark.text }};
            --text-secondary: #b8b2ac;
            --text-muted: {{ theme.dark.muted }};
            --accent-color: {{ theme.dark.accent }};
            --border-color: {{ theme.dark.border }};
            --font-heading: '{{ theme.typography.heading }}', Georgia, serif;
            --font-body: '{{ theme.typography.body }}', -apple-system, sans-serif;
        }

        [data-theme="light"] {
            --bg-primary: {{ theme.colors.background }};
            --bg-secondary: #f7f4f1;
            --bg-tertiary: #efe9e4;
            --text-primary: {{ theme.colors.text }};
            --text-secondary: {{ theme.colors.secondary }};
            --text-muted: {{ theme.colors.muted }};
            --accent-color: {{ theme.colors.accent }};
            --border-color: {{ theme.colors.border }};
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: var(--font-body);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 40px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 48px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .back-link {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 14px;
        }

        .back-link:hover {
            color: var(--accent-color);
        }

        .logo {
            max-width: 100px;
            height: auto;
        }

        h1 {
            font-family: var(--font-heading);
            font-size: 1.75rem;
            font-weight: 600;
        }

        .theme-toggle {
            padding: 8px 14px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 13px;
        }

        .category {
            margin-bottom: 48px;
        }

        .category-title {
            font-family: var(--font-heading);
            font-size: 1.25rem;
            color: var(--text-primary);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .category-icon {
            font-size: 1.25rem;
        }

        .items {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }

        .item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            text-decoration: none;
            transition: all 0.15s ease;
        }

        .item:hover {
            border-color: var(--accent-color);
            background: var(--bg-tertiary);
        }

        .item-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
        }

        .item-info {
            flex: 1;
            min-width: 0;
        }

        .item-name {
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .item-desc {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .item-type {
            font-size: 0.7rem;
            padding: 3px 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        footer {
            margin-top: 60px;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-left">
                <a href="../index.html" class="back-link">← All Languages</a>
                {% if logo_path %}
                <img src="{{ logo_path }}" alt="{{ project_name }}" class="logo">
                {% endif %}
                <h1>{{ lang_name }} Deliverables</h1>
            </div>
            <button class="theme-toggle" id="theme-toggle">☀️ Light</button>
        </header>

        {% for category in categories %}
        <section class="category">
            <h2 class="category-title">
                <span class="category-icon">{{ category.icon }}</span>
                {{ category.name }}
            </h2>
            <div class="items">
                {% for item in category.items %}
                <a href="{{ item.path }}" class="item">
                    <span class="item-icon">{{ item.icon }}</span>
                    <div class="item-info">
                        <div class="item-name">{{ item.name }}</div>
                        {% if item.description %}
                        <div class="item-desc">{{ item.description }}</div>
                        {% endif %}
                    </div>
                    <span class="item-type">{{ item.file_type }}</span>
                </a>
                {% endfor %}
            </div>
        </section>
        {% endfor %}
    </div>

    <footer>
        <p>Generated {{ date }} by Media Engine</p>
    </footer>

    <script>
        const toggle = document.getElementById('theme-toggle');
        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            toggle.textContent = theme === 'light' ? '🌙 Dark' : '☀️ Light';
        }
        const saved = localStorage.getItem('theme') || 'dark';
        setTheme(saved);
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'light' ? 'dark' : 'light');
        });
    </script>
</body>
</html>'''


class IndexTemplate:
    """Navigation index template renderer."""

    def __init__(self, theme: "Theme" = None):
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
    ) -> str:
        """Render the root project index."""
        return self.project_template.render(
            project_name=project_name,
            languages=languages,
            tagline=tagline,
            logo_path=logo_path,
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
    ) -> str:
        """Render a language-specific index."""
        return self.language_template.render(
            project_name=project_name,
            lang_code=lang_code,
            lang_name=lang_name,
            categories=categories,
            logo_path=logo_path,
            theme=self.theme,
            date=datetime.now().strftime("%Y-%m-%d"),
        )


def render_project_index(
    project_name: str,
    languages: List[LanguageInfo],
    theme: "Theme" = None,
    tagline: str = "",
    logo_path: Optional[str] = None,
) -> str:
    """Convenience function to render project index."""
    template = IndexTemplate(theme=theme)
    return template.render_project_index(project_name, languages, tagline, logo_path)


def render_language_index(
    project_name: str,
    lang_code: str,
    lang_name: str,
    categories: List[DeliverableCategory],
    theme: "Theme" = None,
    logo_path: Optional[str] = None,
) -> str:
    """Convenience function to render language index."""
    template = IndexTemplate(theme=theme)
    return template.render_language_index(
        project_name, lang_code, lang_name, categories, logo_path
    )
