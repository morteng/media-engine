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
    <style>
        /* ========================================
           CSS Variables - Theme System
           ======================================== */
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

        /* ========================================
           Reset & Base
           ======================================== */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html {
            font-size: var(--base-size);
            scroll-behavior: smooth;
            scroll-padding-top: 80px;
        }

        body {
            font-family: var(--font-body);
            line-height: 1.7;
            color: var(--text-primary);
            background: var(--bg-primary);
        }

        /* ========================================
           Layout - Sidebar & Main
           ======================================== */
        .layout {
            min-height: 100vh;
        }

        .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            width: 280px;
            height: 100vh;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            padding: 24px 0;
            z-index: 100;
        }

        .sidebar-header {
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 16px;
        }

        .sidebar-logo {
            max-width: 120px;
            height: auto;
            margin-bottom: 12px;
        }

        .sidebar-title {
            font-family: var(--font-heading);
            font-size: 15px;
            font-weight: 500;
            color: var(--text-primary);
        }

        .sidebar-version {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* TOC Navigation */
        .toc {
            list-style: none;
        }

        .toc-item {
            border-left: 2px solid transparent;
        }

        .toc-item.active {
            border-left-color: var(--accent-color);
            background: var(--accent-light);
        }

        .toc-link {
            display: block;
            padding: 8px 20px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            transition: all 0.15s ease;
        }

        .toc-link:hover {
            color: var(--accent-color);
            background: var(--bg-tertiary);
        }

        .toc-item.active .toc-link {
            color: var(--accent-color);
            font-weight: 500;
        }

        /* Main content area */
        .main {
            margin-left: 280px;
            padding: 40px 60px;
        }

        /* Topbar with controls */
        .topbar {
            position: fixed;
            top: 0;
            left: 280px;
            right: 0;
            height: 60px;
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 0 40px;
            z-index: 50;
            gap: 16px;
        }

        .topbar-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-primary);
            color: var(--text-secondary);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .topbar-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .content {
            padding-top: 80px;
        }

        /* ========================================
           Typography
           ======================================== */
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-heading);
            color: var(--text-primary);
            line-height: 1.3;
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }

        h2 {
            font-size: 1.75rem;
            font-weight: 500;
            margin: 48px 0 20px;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
        }

        h3 {
            font-size: 1.25rem;
            font-weight: 500;
            margin: 32px 0 12px;
        }

        h4 {
            font-size: 1rem;
            font-weight: 500;
            margin: 24px 0 8px;
            color: var(--text-secondary);
        }

        p {
            margin-bottom: 16px;
            color: var(--text-secondary);
        }

        strong {
            color: var(--text-primary);
            font-weight: 600;
        }

        a {
            color: var(--accent-color);
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        /* Lists */
        ul, ol {
            margin: 0 0 16px 24px;
            color: var(--text-secondary);
        }

        li {
            margin-bottom: 6px;
        }

        /* Code */
        code {
            font-family: var(--font-code);
            font-size: 0.875em;
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 4px;
        }

        pre {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 16px 0;
        }

        pre code {
            background: none;
            padding: 0;
            font-size: 13px;
            line-height: 1.6;
        }

        /* Tables */
        .table-wrapper {
            overflow-x: auto;
            margin: 24px 0;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 14px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        th {
            background: linear-gradient(to bottom, var(--bg-secondary), var(--bg-tertiary));
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            border-bottom: 2px solid var(--border-color);
        }

        td {
            color: var(--text-secondary);
        }

        tr:nth-child(even) td {
            background: var(--bg-secondary);
        }

        tr:hover td {
            background: var(--accent-light);
        }

        /* Blockquotes */
        blockquote {
            border-left: 3px solid var(--accent-color);
            padding: 12px 20px;
            margin: 16px 0;
            background: var(--bg-secondary);
            border-radius: 0 8px 8px 0;
        }

        blockquote p:last-child {
            margin-bottom: 0;
        }

        /* Images */
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 24px auto;
        }

        figure {
            margin: 32px 0;
            text-align: center;
        }

        figcaption {
            font-size: 0.875rem;
            color: var(--text-muted);
            font-style: italic;
            margin-top: 12px;
        }

        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 32px 0;
        }

        /* ========================================
           Cover Page
           ======================================== */
        .cover {
            text-align: center;
            padding: 60px 0;
            margin-bottom: 40px;
            border-bottom: 1px solid var(--border-color);
        }

        .cover h1 {
            font-size: 3rem;
            margin-bottom: 8px;
        }

        .cover-subtitle {
            font-size: 1.25rem;
            color: var(--text-muted);
            margin-bottom: 24px;
            font-weight: 300;
        }

        .cover-meta {
            display: flex;
            justify-content: center;
            gap: 32px;
            font-size: 14px;
            color: var(--text-secondary);
        }

        /* ========================================
           Chapter Sections
           ======================================== */
        .chapter {
            margin-bottom: 60px;
        }

        .chapter-meta {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 24px;
            font-size: 13px;
        }

        .chapter-meta-row {
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }

        .chapter-meta-item {
            color: var(--text-muted);
        }

        .chapter-meta-item strong {
            color: var(--text-secondary);
        }

        /* ========================================
           Progress Bar
           ======================================== */
        .progress-bar {
            position: fixed;
            top: 0;
            left: 280px;
            right: 0;
            height: 3px;
            background: var(--bg-tertiary);
            z-index: 200;
        }

        .progress-bar-fill {
            height: 100%;
            background: var(--accent-color);
            width: 0%;
            transition: width 0.1s ease;
        }

        /* ========================================
           Back to Top
           ======================================== */
        .back-to-top {
            position: fixed;
            bottom: 32px;
            right: 32px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--accent-color);
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
            font-size: 20px;
        }

        .back-to-top.visible {
            opacity: 1;
            visibility: visible;
        }

        .back-to-top:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
        }

        /* ========================================
           Print Styles
           ======================================== */
        @media print {
            .sidebar, .topbar, .progress-bar, .back-to-top, .chapter-meta {
                display: none !important;
            }

            .layout {
                display: block;
            }

            .main {
                margin-left: 0;
                padding: 0;
                max-width: 100%;
            }

            .content {
                padding-top: 0;
            }

            body {
                font-size: 11pt;
                line-height: 1.5;
                color: #000 !important;
                background: #fff !important;
            }

            h1, h2, h3, h4, h5, h6 {
                color: #000 !important;
                page-break-after: avoid;
            }

            p, li, td, th {
                color: #333 !important;
            }

            a {
                color: #000 !important;
                text-decoration: underline;
            }

            table, figure, pre, blockquote {
                page-break-inside: avoid;
            }

            .cover {
                page-break-after: always;
            }

            .chapter {
                page-break-before: always;
            }
        }

        /* ========================================
           Responsive
           ======================================== */
        @media (max-width: 1024px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }

            .sidebar.open {
                transform: translateX(0);
            }

            .main {
                margin-left: 0;
                padding: 20px;
            }

            .topbar {
                left: 0;
            }

            .progress-bar {
                left: 0;
            }
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

    <script>
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            if (theme === 'light') {
                themeIcon.textContent = '🌙';
                themeText.textContent = 'Dark';
            } else {
                themeIcon.textContent = '☀️';
                themeText.textContent = 'Light';
            }
        }

        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || '{{ default_theme }}';
        setTheme(savedTheme);

        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'light' ? 'dark' : 'light');
        });

        {% if include_progress %}
        // Reading progress
        const progressBar = document.getElementById('progress');
        window.addEventListener('scroll', () => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = (scrollTop / docHeight) * 100;
            progressBar.style.width = progress + '%';
        });
        {% endif %}

        {% if include_back_to_top %}
        // Back to top
        const backToTop = document.getElementById('back-to-top');
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        {% endif %}

        // Active TOC highlighting
        const tocItems = document.querySelectorAll('.toc-item');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    tocItems.forEach(item => item.classList.remove('active'));
                    const id = entry.target.id;
                    const tocItem = document.querySelector(`.toc-item[data-chapter="${id}"]`);
                    if (tocItem) tocItem.classList.add('active');
                }
            });
        }, { rootMargin: '-80px 0px -70% 0px' });

        document.querySelectorAll('.chapter, h2[id]').forEach(section => {
            observer.observe(section);
        });
    </script>
</body>
</html>"""


class DocumentTemplate:
    """Professional HTML document template renderer."""

    def __init__(self, theme: "Theme" = None):
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
) -> str:
    """Convenience function to render a document."""
    template = DocumentTemplate(theme=theme)
    return template.render(content, title, chapters, cover, config)
