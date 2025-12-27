"""Diagram tools for MCP."""

import json
from pathlib import Path


def register_diagram_tools(mcp, server_instance):
    """Register diagram-related MCP tools."""

    @mcp.tool()
    async def build_diagram(
        path: str,
        engine: str = None,
        dark_mode: bool = False,
        output_path: str = None,
    ) -> str:
        """
        Build a single diagram from YAML definition.

        Args:
            path: Path to diagram YAML file (relative to project or absolute)
            engine: Engine to use (matplotlib, d2, excalidraw) - defaults to YAML config
            dark_mode: Generate dark mode version
            output_path: Custom output path (optional)

        Returns:
            JSON with build result including output file path.
        """
        from ...diagrams import DiagramDefinition, DiagramGenerator

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Diagram file not found: {path}"}, indent=2)

        try:
            definition = DiagramDefinition.from_yaml(validated_path)
        except Exception as e:
            return json.dumps({"error": f"Failed to parse diagram: {e}"}, indent=2)

        # Set dark mode
        definition.config.dark_mode = dark_mode

        # Determine output path
        if output_path:
            out = Path(output_path)
        else:
            out_dir = server_instance.project.output_dir / "diagrams"
            suffix = "_dark" if dark_mode else ""
            out = out_dir / f"{validated_path.stem}{suffix}.{definition.config.format}"

        out.parent.mkdir(parents=True, exist_ok=True)

        # Get brand context if available
        brand = getattr(server_instance.project, "brand_context", None)
        theme = getattr(server_instance.project, "theme", None)

        generator = DiagramGenerator(brand=brand, theme=theme)

        try:
            result = generator.generate(definition, out, engine=engine)
            return json.dumps(
                {
                    "status": "built",
                    "input": str(validated_path),
                    "output": str(result),
                    "engine": engine or definition.config.engine.value,
                    "dark_mode": dark_mode,
                    "size_bytes": result.stat().st_size,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"Build failed: {e}"}, indent=2)

    @mcp.tool()
    async def build_all_diagrams(
        language: str = None,
        engine: str = None,
        dark_mode: bool = False,
        output_dir: str = None,
    ) -> str:
        """
        Build all diagrams in the project for a language.

        Args:
            language: Language to build (default: source language)
            engine: Override engine for all diagrams
            dark_mode: Generate dark mode only (else generates both themes)
            output_dir: Custom output directory

        Returns:
            JSON with list of built files and any errors.
        """
        from ...diagrams import build_diagrams

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        lang = language or server_instance.project.source_language

        try:
            paths = build_diagrams(
                server_instance.project,
                language=lang,
                engine_override=engine,
                dark_mode=dark_mode,
                output_dir=Path(output_dir) if output_dir else None,
            )

            return json.dumps(
                {
                    "status": "built",
                    "language": lang,
                    "engine": engine or "auto",
                    "dark_mode": dark_mode,
                    "files_built": len(paths),
                    "output_files": [str(p) for p in paths],
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"Build failed: {e}"}, indent=2)

    @mcp.tool()
    async def list_diagram_engines() -> str:
        """
        List available diagram engines with their capabilities.

        Returns:
            JSON with list of engines, installation status, and capabilities.
        """
        from ...diagrams import get_available_engines

        engines = get_available_engines()

        return json.dumps(
            {
                "engines": [
                    {
                        "name": e.name,
                        "version": e.version,
                        "installed": e.installed,
                        "formats": e.formats,
                        "capabilities": [c.value for c in e.capabilities],
                        "description": e.description,
                    }
                    for e in engines
                ],
                "installed_count": sum(1 for e in engines if e.installed),
                "total_count": len(engines),
            },
            indent=2,
        )

    @mcp.tool()
    async def list_diagrams(language: str = None) -> str:
        """
        List all diagrams in the project.

        Args:
            language: Filter by language (default: all languages)

        Returns:
            JSON with list of diagram files and their metadata.
        """
        from ...diagrams import DiagramDefinition

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        languages = (
            [language] if language else list(server_instance.project.languages.keys())
        )

        diagrams = []
        for lang in languages:
            diagrams_dir = server_instance.project.get_content_path(lang, "diagrams")
            if diagrams_dir.exists():
                for path in sorted(diagrams_dir.glob("*.yaml")):
                    try:
                        definition = DiagramDefinition.from_yaml(path)
                        diagrams.append(
                            {
                                "path": str(
                                    path.relative_to(server_instance.project.root)
                                ),
                                "language": lang,
                                "title": definition.title or path.stem,
                                "engine": definition.config.engine.value,
                                "format": definition.config.format,
                                "boxes": len(definition.boxes),
                                "arrows": len(definition.arrows),
                                "layers": len(definition.layers),
                                "groups": len(definition.groups),
                                "suggested_engine": definition.get_suggested_engine().value,
                            }
                        )
                    except Exception as e:
                        diagrams.append(
                            {
                                "path": str(
                                    path.relative_to(server_instance.project.root)
                                ),
                                "language": lang,
                                "error": str(e),
                            }
                        )

        return json.dumps(
            {
                "diagrams": diagrams,
                "total": len(diagrams),
                "by_language": {
                    lang: sum(1 for d in diagrams if d.get("language") == lang)
                    for lang in languages
                },
            },
            indent=2,
        )

    @mcp.tool()
    async def preview_diagram(path: str) -> str:
        """
        Get detailed information about a diagram definition.

        Args:
            path: Path to diagram YAML file

        Returns:
            JSON with complete diagram structure and suggested engine.
        """
        from ...diagrams import DiagramDefinition

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Diagram file not found: {path}"}, indent=2)

        try:
            definition = DiagramDefinition.from_yaml(validated_path)
        except Exception as e:
            return json.dumps({"error": f"Failed to parse diagram: {e}"}, indent=2)

        return json.dumps(
            {
                "path": str(validated_path),
                "title": definition.title,
                "config": {
                    "engine": definition.config.engine.value,
                    "format": definition.config.format,
                    "width": definition.config.width,
                    "height": definition.config.height,
                    "dpi": definition.config.dpi,
                    "dark_mode": definition.config.dark_mode,
                    "font_scale": definition.config.font_scale,
                    "engine_options": definition.config.engine_options,
                },
                "boxes": [
                    {
                        "id": b.id,
                        "label": b.label,
                        "style": b.style,
                        "x": b.x,
                        "y": b.y,
                        "width": b.width,
                        "height": b.height,
                        "color": b.color,
                        "layer": b.layer,
                        "group": b.group,
                    }
                    for b in definition.boxes
                ],
                "arrows": [
                    {
                        "from": a.from_id,
                        "to": a.to_id,
                        "label": a.label,
                        "style": a.style,
                        "curved": a.curved,
                        "bidirectional": a.bidirectional,
                        "animated": a.animated,
                    }
                    for a in definition.arrows
                ],
                "layers": [
                    {"id": l.id, "label": l.label, "color": l.color}
                    for l in definition.layers
                ],
                "groups": [
                    {"id": g.id, "label": g.label}
                    for g in definition.groups
                ],
                "suggested_engine": definition.get_suggested_engine().value,
                "element_count": {
                    "boxes": len(definition.boxes),
                    "arrows": len(definition.arrows),
                    "layers": len(definition.layers),
                    "groups": len(definition.groups),
                },
            },
            indent=2,
        )
