"""Build tools."""

import json
from pathlib import Path


def register_build_tools(mcp, server_instance):
    """Register build-related MCP tools."""

    @mcp.tool()
    async def build_html(language: str = None, chapter: str = None, output_dir: str = None) -> str:
        """
        Build HTML output from markdown chapters.

        Args:
            language: Language to build (default: source language)
            chapter: Specific chapter filename (optional, builds all if omitted)
            output_dir: Output directory (optional, uses default)
        """
        from ...builders.html import HTMLBuilder, HTMLConfig
        from ...cms.document import Document

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        lang = language or server_instance.project.source_language
        builder = HTMLBuilder(theme=server_instance.project.theme)

        if chapter:
            chapters = [server_instance.project.get_chapters_dir(lang) / chapter]
        else:
            chapters = server_instance.project.list_chapters(lang)

        if not chapters:
            return json.dumps({"error": f"No chapters found for '{lang}'"}, indent=2)

        output_path = Path(output_dir) if output_dir else server_instance.project.output_dir / lang
        output_path.mkdir(parents=True, exist_ok=True)

        built = []
        for chapter_path in chapters:
            if not chapter_path.exists():
                continue

            doc = Document.load(chapter_path)
            config = HTMLConfig(include_toc=True, lang=lang)
            html = builder.build(doc.content, doc.title, config)

            out_file = output_path / chapter_path.with_suffix(".html").name
            builder.save(html, out_file)
            built.append(str(out_file))

        server_instance._invalidate_cache()
        return json.dumps(
            {
                "status": "built",
                "language": lang,
                "files_built": len(built),
                "output_files": built,
            },
            indent=2,
        )

    @mcp.tool()
    async def build_pptx(slides_path: str, output_path: str = None) -> str:
        """
        Build PowerPoint presentation from YAML definition.

        Args:
            slides_path: Path to slides YAML file
            output_path: Output path (optional)
        """
        try:
            from ...builders.pptx import PPTXBuilder
        except ImportError:
            return json.dumps({"error": "python-pptx not installed"}, indent=2)

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(slides_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Slides file not found: {slides_path}"}, indent=2)

        builder = PPTXBuilder(theme=server_instance.project.theme)
        builder.build_from_yaml(validated_path)

        if output_path:
            out = Path(output_path)
        else:
            out = server_instance.project.output_dir / validated_path.with_suffix(".pptx").name

        out.parent.mkdir(parents=True, exist_ok=True)
        saved = builder.save(out)

        return json.dumps(
            {
                "status": "built",
                "input": str(validated_path),
                "output": str(saved),
                "size_bytes": saved.stat().st_size,
            },
            indent=2,
        )

    @mcp.tool()
    async def build_xlsx(data_path: str, output_path: str = None) -> str:
        """
        Build Excel spreadsheet from YAML definition.

        Args:
            data_path: Path to data YAML file
            output_path: Output path (optional)
        """
        try:
            from ...builders.xlsx import XLSXBuilder
        except ImportError:
            return json.dumps({"error": "openpyxl not installed"}, indent=2)

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(data_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Data file not found: {data_path}"}, indent=2)

        builder = XLSXBuilder(theme=server_instance.project.theme)
        builder.build_from_yaml(validated_path)

        if output_path:
            out = Path(output_path)
        else:
            out = server_instance.project.output_dir / validated_path.with_suffix(".xlsx").name

        out.parent.mkdir(parents=True, exist_ok=True)
        saved = builder.save(out)

        return json.dumps(
            {
                "status": "built",
                "input": str(validated_path),
                "output": str(saved),
                "size_bytes": saved.stat().st_size,
            },
            indent=2,
        )
