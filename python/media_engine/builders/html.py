"""
HTML Builder

Generates styled HTML documents from Markdown.
Applies theme styling and supports code highlighting.

Features:
- Themed HTML output
- Table of contents generation
- Code syntax highlighting
- Responsive design
- Dark mode support
- PDF-ready styling
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List

import markdown
from jinja2 import Template

if TYPE_CHECKING:
    from ..core.theme import Theme


# Professional HTML template with theme support
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        /* CSS Variables from Theme */
        :root {
            --color-primary: {{ theme.colors.primary }};
            --color-secondary: {{ theme.colors.secondary }};
            --color-accent: {{ theme.colors.accent }};
            --color-background: {{ theme.colors.background }};
            --color-text: {{ theme.colors.text }};
            --color-muted: {{ theme.colors.muted }};
            --color-border: {{ theme.colors.border }};
            --font-heading: {{ theme.typography.heading }}, Georgia, serif;
            --font-body: {{ theme.typography.body }}, -apple-system, BlinkMacSystemFont, sans-serif;
            --font-code: {{ theme.typography.code }}, 'SF Mono', Monaco, monospace;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --color-background: {{ theme.dark.background }};
                --color-text: {{ theme.dark.text }};
                --color-accent: {{ theme.dark.accent }};
                --color-muted: {{ theme.dark.muted }};
                --color-border: {{ theme.dark.border }};
            }
        }

        /* Reset and Base */
        *, *::before, *::after {
            box-sizing: border-box;
        }

        html {
            font-size: 16px;
            scroll-behavior: smooth;
        }

        body {
            font-family: var(--font-body);
            line-height: 1.7;
            color: var(--color-text);
            background: var(--color-background);
            margin: 0;
            padding: 0;
        }

        /* Main Container */
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }

        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-heading);
            color: var(--color-primary);
            line-height: 1.3;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }

        h1 {
            font-size: 2.5rem;
            margin-top: 0;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid var(--color-accent);
        }

        h2 {
            font-size: 1.8rem;
            color: var(--color-secondary);
        }

        h3 {
            font-size: 1.4rem;
        }

        h4, h5, h6 {
            font-size: 1.1rem;
        }

        p {
            margin: 1rem 0;
        }

        /* Links */
        a {
            color: var(--color-accent);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s ease;
        }

        a:hover {
            border-bottom-color: var(--color-accent);
        }

        /* Lists */
        ul, ol {
            margin: 1rem 0;
            padding-left: 1.5rem;
        }

        li {
            margin: 0.5rem 0;
        }

        li > ul, li > ol {
            margin: 0.25rem 0;
        }

        /* Code */
        code {
            font-family: var(--font-code);
            font-size: 0.9em;
            background: rgba(0, 0, 0, 0.05);
            padding: 0.2em 0.4em;
            border-radius: 4px;
        }

        pre {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 1.5rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5rem 0;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        pre code {
            background: none;
            padding: 0;
            color: inherit;
            font-size: inherit;
        }

        /* Blockquotes */
        blockquote {
            border-left: 4px solid var(--color-accent);
            margin: 1.5rem 0;
            padding: 0.5rem 0 0.5rem 1.5rem;
            color: var(--color-muted);
            font-style: italic;
        }

        blockquote p {
            margin: 0.5rem 0;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            font-size: 0.95rem;
        }

        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--color-border);
        }

        th {
            font-family: var(--font-heading);
            font-weight: 600;
            color: var(--color-primary);
            background: rgba(0, 0, 0, 0.02);
        }

        tr:hover {
            background: rgba(0, 0, 0, 0.02);
        }

        /* Images */
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1.5rem 0;
        }

        /* Horizontal Rule */
        hr {
            border: none;
            border-top: 2px solid var(--color-border);
            margin: 3rem 0;
        }

        /* Table of Contents */
        .toc {
            background: rgba(0, 0, 0, 0.02);
            padding: 1.5rem 2rem;
            border-radius: 8px;
            margin: 2rem 0;
        }

        .toc h2 {
            margin-top: 0;
            font-size: 1.2rem;
        }

        .toc ul {
            list-style: none;
            padding-left: 0;
        }

        .toc li {
            margin: 0.3rem 0;
        }

        .toc a {
            color: var(--color-muted);
        }

        .toc a:hover {
            color: var(--color-accent);
        }

        /* Print Styles */
        @media print {
            body {
                background: white;
                color: black;
                font-size: 11pt;
            }

            .container {
                max-width: none;
                padding: 0;
            }

            h1, h2, h3 {
                page-break-after: avoid;
            }

            pre, blockquote, table {
                page-break-inside: avoid;
            }

            a {
                color: inherit;
                text-decoration: underline;
            }
        }

        /* Custom: Callouts */
        .callout {
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
        }

        .callout.info {
            background: rgba(49, 130, 206, 0.1);
            border-left: 4px solid #3182ce;
        }

        .callout.warning {
            background: rgba(221, 107, 32, 0.1);
            border-left: 4px solid #dd6b20;
        }

        .callout.success {
            background: rgba(56, 161, 105, 0.1);
            border-left: 4px solid #38a169;
        }

        /* Footer */
        .footer {
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--color-border);
            color: var(--color-muted);
            font-size: 0.9rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        {% if toc %}
        <nav class="toc">
            <h2>Contents</h2>
            {{ toc }}
        </nav>
        {% endif %}

        {{ content }}

        {% if footer %}
        <footer class="footer">
            {{ footer }}
        </footer>
        {% endif %}
    </div>
</body>
</html>"""


@dataclass
class HTMLConfig:
    """Configuration for HTML generation."""

    include_toc: bool = False
    footer: str = ""
    lang: str = "en"


class HTMLBuilder:
    """Builds HTML documents with theme styling."""

    def __init__(self, theme: "Theme" = None):
        """
        Initialize HTML builder.

        Args:
            theme: Theme for styling (uses defaults if not provided)
        """
        from ..core.theme import COPPER_AND_CREAM

        self.theme = theme or COPPER_AND_CREAM
        self.template = Template(HTML_TEMPLATE)

        # Markdown processor with extensions
        self.md = markdown.Markdown(
            extensions=[
                "tables",
                "fenced_code",
                "codehilite",
                "toc",
                "meta",
                "attr_list",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "guess_lang": False,
                },
                "toc": {
                    "permalink": True,
                    "permalink_class": "anchor",
                    "toc_depth": 1,  # Only H1 (chapters) in TOC
                },
            },
        )

    def build(
        self,
        content: str,
        title: str = "Document",
        config: HTMLConfig = None,
    ) -> str:
        """
        Build HTML from Markdown content.

        Args:
            content: Markdown content
            title: Document title
            config: Optional configuration

        Returns:
            HTML string
        """
        config = config or HTMLConfig()

        # Reset markdown processor
        self.md.reset()

        # Convert markdown to HTML
        html_content = self.md.convert(content)

        # Get TOC if enabled
        toc_html = ""
        if config.include_toc and hasattr(self.md, "toc"):
            toc_html = self.md.toc

        # Render template
        html = self.template.render(
            title=title,
            theme=self.theme,
            content=html_content,
            toc=toc_html if config.include_toc else None,
            footer=config.footer,
            lang=config.lang,
        )

        return html

    def build_from_file(
        self,
        source_path: Path,
        title: str = None,
        config: HTMLConfig = None,
    ) -> str:
        """
        Build HTML from Markdown file.

        Args:
            source_path: Path to .md file
            title: Optional title (defaults to filename)
            config: Optional configuration

        Returns:
            HTML string
        """
        content = source_path.read_text()

        # Extract title from first H1 if not provided
        if not title:
            import re

            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                title = match.group(1)
            else:
                title = source_path.stem.replace("_", " ").title()

        return self.build(content, title, config)

    def build_combined(
        self,
        source_paths: List[Path],
        title: str = "Combined Document",
        config: HTMLConfig = None,
    ) -> str:
        """
        Build HTML from multiple Markdown files.

        Args:
            source_paths: List of .md file paths
            title: Document title
            config: Optional configuration

        Returns:
            HTML string
        """
        combined_content = []

        for path in source_paths:
            if path.exists():
                content = path.read_text()
                combined_content.append(content)

        return self.build(
            "\n\n---\n\n".join(combined_content),
            title,
            config,
        )

    def save(
        self,
        html: str,
        output_path: Path,
    ) -> Path:
        """
        Save HTML to file.

        Args:
            html: HTML content
            output_path: Where to save

        Returns:
            Path to saved file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        return output_path


def build_html(
    source_path: Path,
    output_path: Path,
    theme: "Theme" = None,
    include_toc: bool = False,
) -> Path:
    """
    Build HTML from Markdown source.

    Args:
        source_path: Path to .md file
        output_path: Where to save .html
        theme: Optional theme for styling
        include_toc: Whether to include table of contents

    Returns:
        Path to generated HTML
    """
    builder = HTMLBuilder(theme=theme)
    config = HTMLConfig(include_toc=include_toc)

    html = builder.build_from_file(source_path, config=config)
    return builder.save(html, output_path)


def build_html_combined(
    source_paths: List[Path],
    output_path: Path,
    title: str = "Document",
    theme: "Theme" = None,
    include_toc: bool = True,
) -> Path:
    """
    Build HTML from multiple Markdown sources.

    Args:
        source_paths: List of .md files
        output_path: Where to save .html
        title: Document title
        theme: Optional theme for styling
        include_toc: Whether to include table of contents

    Returns:
        Path to generated HTML
    """
    builder = HTMLBuilder(theme=theme)
    config = HTMLConfig(include_toc=include_toc)

    html = builder.build_combined(source_paths, title, config)
    return builder.save(html, output_path)
