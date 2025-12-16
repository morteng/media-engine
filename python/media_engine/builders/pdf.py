"""
PDF Builder for Media Engine

Generates PDF documents from markdown content.
Uses WeasyPrint for high-quality PDF generation.

Features:
- Custom styling from theme
- Table of contents
- Page numbers
- Headers/footers
- Cover pages
"""

from pathlib import Path

import markdown

# WeasyPrint import - graceful fallback
try:
    from weasyprint import CSS, HTML
    from weasyprint.text.fonts import FontConfiguration

    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


class PDFBuilder:
    """
    Builds PDF documents from markdown.

    Usage:
        builder = PDFBuilder(theme=project.theme)
        builder.build_from_markdown(content, title, output_path)
        builder.build_from_document(doc, output_path)
    """

    def __init__(self, theme=None):
        """
        Initialize PDF builder.

        Args:
            theme: Theme instance for styling
        """
        if not HAS_WEASYPRINT:
            raise RuntimeError("WeasyPrint not installed. Install with: pip install weasyprint")

        self.theme = theme
        self.font_config = FontConfiguration()

    def _get_css(self) -> str:
        """Generate CSS from theme."""
        if self.theme:
            primary = self.theme.colors.get("primary", "#2c2522")
            accent = self.theme.colors.get("accent", "#0066cc")
            bg = self.theme.colors.get("background", "#ffffff")
            text = self.theme.colors.get("text", "#2c2522")
            heading_font = self.theme.typography.get("heading", "Georgia")
            body_font = self.theme.typography.get("body", "Helvetica")
        else:
            primary = "#2c2522"
            accent = "#0066cc"
            bg = "#ffffff"
            text = "#2c2522"
            heading_font = "Georgia"
            body_font = "Helvetica"

        return f"""
        @page {{
            size: A4;
            margin: 2.5cm 2cm;

            @top-center {{
                content: string(chapter);
                font-size: 10pt;
                color: {primary};
            }}

            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
            }}
        }}

        @page :first {{
            @top-center {{ content: none; }}
        }}

        body {{
            font-family: {body_font}, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: {text};
            background: {bg};
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: {heading_font}, serif;
            color: {primary};
            page-break-after: avoid;
        }}

        h1 {{
            font-size: 24pt;
            margin-top: 0;
            string-set: chapter content();
        }}

        h2 {{
            font-size: 18pt;
            margin-top: 1.5em;
            border-bottom: 1px solid {accent};
            padding-bottom: 0.3em;
        }}

        h3 {{
            font-size: 14pt;
            margin-top: 1.2em;
        }}

        p {{
            margin: 0.8em 0;
            text-align: justify;
        }}

        a {{
            color: {accent};
            text-decoration: none;
        }}

        code {{
            font-family: 'Courier New', monospace;
            background: #f5f5f5;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 0.9em;
        }}

        pre {{
            background: #f5f5f5;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 0.85em;
            page-break-inside: avoid;
        }}

        pre code {{
            background: none;
            padding: 0;
        }}

        blockquote {{
            border-left: 4px solid {accent};
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
            font-style: italic;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            page-break-inside: avoid;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 0.5em;
            text-align: left;
        }}

        th {{
            background: {primary};
            color: white;
        }}

        tr:nth-child(even) {{
            background: #f9f9f9;
        }}

        img {{
            max-width: 100%;
            height: auto;
        }}

        .cover-page {{
            page-break-after: always;
            text-align: center;
            padding-top: 30%;
        }}

        .cover-page h1 {{
            font-size: 36pt;
            margin-bottom: 0.5em;
        }}

        .cover-page .subtitle {{
            font-size: 18pt;
            color: #666;
        }}

        .toc {{
            page-break-after: always;
        }}

        .toc h2 {{
            border-bottom: none;
        }}

        .toc ul {{
            list-style: none;
            padding: 0;
        }}

        .toc li {{
            margin: 0.5em 0;
        }}

        .toc a {{
            text-decoration: none;
        }}

        .toc a::after {{
            content: leader('.') target-counter(attr(href), page);
        }}
        """

    def build_from_markdown(
        self,
        content: str,
        title: str,
        output_path: Path,
        include_toc: bool = True,
        include_cover: bool = True,
        subtitle: str = None,
    ) -> Path:
        """
        Build PDF from markdown content.

        Args:
            content: Markdown content
            title: Document title
            output_path: Output PDF path
            include_toc: Whether to include table of contents
            include_cover: Whether to include cover page
            subtitle: Optional subtitle for cover

        Returns:
            Path to generated PDF
        """
        # Convert markdown to HTML
        md = markdown.Markdown(
            extensions=[
                "tables",
                "fenced_code",
                "toc",
                "meta",
            ]
        )
        html_content = md.convert(content)

        # Build full HTML document
        parts = []

        # Cover page
        if include_cover:
            parts.append(f"""
            <div class="cover-page">
                <h1>{title}</h1>
                {f'<p class="subtitle">{subtitle}</p>' if subtitle else ""}
            </div>
            """)

        # Table of contents
        if include_toc and hasattr(md, "toc"):
            parts.append(f"""
            <div class="toc">
                <h2>Contents</h2>
                {md.toc}
            </div>
            """)

        # Main content
        parts.append(html_content)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            {"".join(parts)}
        </body>
        </html>
        """

        # Generate PDF
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = HTML(string=html)
        css = CSS(string=self._get_css(), font_config=self.font_config)
        doc.write_pdf(output_path, stylesheets=[css], font_config=self.font_config)

        return output_path

    def build_from_document(
        self,
        doc,
        output_path: Path,
        include_toc: bool = True,
        include_cover: bool = True,
    ) -> Path:
        """
        Build PDF from a Document instance.

        Args:
            doc: Document instance
            output_path: Output PDF path
            include_toc: Whether to include table of contents
            include_cover: Whether to include cover page

        Returns:
            Path to generated PDF
        """
        return self.build_from_markdown(
            doc.content,
            doc.title,
            output_path,
            include_toc=include_toc,
            include_cover=include_cover,
            subtitle=doc.metadata.get("subtitle"),
        )

    def build_combined(
        self,
        documents: list,
        title: str,
        output_path: Path,
        include_toc: bool = True,
    ) -> Path:
        """
        Build single PDF from multiple documents.

        Args:
            documents: List of Document instances
            title: Combined document title
            output_path: Output PDF path
            include_toc: Whether to include table of contents

        Returns:
            Path to generated PDF
        """
        combined_content = []

        for doc in documents:
            combined_content.append(f"# {doc.title}\n\n{doc.content}")

        return self.build_from_markdown(
            "\n\n---\n\n".join(combined_content),
            title,
            output_path,
            include_toc=include_toc,
            include_cover=True,
        )


def build_pdf(project, language: str = None, output_dir: Path = None) -> list[Path]:
    """
    Convenience function to build PDFs for a project.

    Args:
        project: Project instance
        language: Specific language (default: all)
        output_dir: Output directory (default: project output_dir)

    Returns:
        List of generated PDF paths
    """
    from ..cms.document import Document

    builder = PDFBuilder(theme=project.theme)
    output_dir = output_dir or project.output_dir
    generated = []

    languages = [language] if language else list(project.languages.keys())

    for lang in languages:
        lang_output = output_dir / lang
        lang_output.mkdir(parents=True, exist_ok=True)

        for chapter_path in project.list_chapters(lang):
            doc = Document.load(chapter_path)
            pdf_path = lang_output / chapter_path.with_suffix(".pdf").name
            builder.build_from_document(doc, pdf_path)
            generated.append(pdf_path)

    return generated


__all__ = ["PDFBuilder", "build_pdf"]
