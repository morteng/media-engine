"""
Diagram API routes.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Optional

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_diagram_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register diagram-related routes."""
    from fastapi import BackgroundTasks, HTTPException
    from pydantic import BaseModel

    # Track active diagram builds
    build_state: Dict = {
        "active": False,
        "progress": 0,
        "logs": [],
        "last_build": None,
    }

    class DiagramBuildRequest(BaseModel):
        """Request body for diagram build."""
        language: Optional[str] = None
        engine: Optional[str] = None
        dark_mode: bool = False

    class SingleDiagramBuildRequest(BaseModel):
        """Request body for single diagram build."""
        path: str
        engine: Optional[str] = None
        dark_mode: bool = False
        output_path: Optional[str] = None

    @router.get("/api/diagrams")
    async def list_diagrams(language: str = None):
        """List all diagrams in the project."""
        from ...diagrams import DiagramDefinition

        project = get_project()

        languages = [language] if language else list(project.languages.keys())

        diagrams = []
        for lang in languages:
            diagrams_dir = project.get_content_path(lang, "diagrams")
            if diagrams_dir.exists():
                for path in sorted(diagrams_dir.glob("*.yaml")):
                    try:
                        definition = DiagramDefinition.from_yaml(path)
                        diagrams.append({
                            "path": str(path.relative_to(project.root)),
                            "language": lang,
                            "title": definition.title or path.stem,
                            "engine": definition.config.engine.value,
                            "format": definition.config.format,
                            "boxes": len(definition.boxes),
                            "arrows": len(definition.arrows),
                            "layers": len(definition.layers),
                            "groups": len(definition.groups),
                            "suggested_engine": definition.get_suggested_engine().value,
                        })
                    except Exception as e:
                        diagrams.append({
                            "path": str(path.relative_to(project.root)),
                            "language": lang,
                            "error": str(e),
                        })

        return {
            "diagrams": diagrams,
            "total": len(diagrams),
            "by_language": {
                lang: sum(1 for d in diagrams if d.get("language") == lang)
                for lang in languages
            },
        }

    @router.get("/api/diagrams/engines")
    async def list_engines():
        """List available diagram engines."""
        from ...diagrams import get_available_engines, get_engine

        engines = get_available_engines()

        result = []
        for e in engines:
            engine_data = {
                "name": e.name,
                "version": e.version,
                "installed": e.installed,
                "formats": e.formats,
                "capabilities": [c.value for c in e.capabilities],
                "description": e.description,
            }

            # Get install hint if not installed
            if not e.installed:
                engine_class = get_engine(e.name)
                if engine_class:
                    engine_data["install_hint"] = engine_class.get_install_hint()

            result.append(engine_data)

        return {
            "engines": result,
            "installed_count": sum(1 for e in engines if e.installed),
            "total_count": len(engines),
        }

    @router.get("/api/diagrams/{path:path}")
    async def get_diagram(path: str):
        """Get details of a specific diagram."""
        from ...diagrams import DiagramDefinition

        project = get_project()

        diagram_path = project.root / path
        if not diagram_path.exists():
            raise HTTPException(status_code=404, detail=f"Diagram not found: {path}")

        try:
            definition = DiagramDefinition.from_yaml(diagram_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse diagram: {e}")

        return {
            "path": path,
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
        }

    @router.post("/api/diagrams/build")
    async def build_single_diagram(request: SingleDiagramBuildRequest):
        """Build a single diagram."""
        from ...diagrams import DiagramDefinition, DiagramGenerator

        project = get_project()

        diagram_path = project.root / request.path
        if not diagram_path.exists():
            raise HTTPException(status_code=404, detail=f"Diagram not found: {request.path}")

        try:
            definition = DiagramDefinition.from_yaml(diagram_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse diagram: {e}")

        # Set dark mode
        definition.config.dark_mode = request.dark_mode

        # Determine output path
        if request.output_path:
            output = Path(request.output_path)
        else:
            out_dir = project.output_dir / "diagrams"
            suffix = "_dark" if request.dark_mode else ""
            output = out_dir / f"{diagram_path.stem}{suffix}.{definition.config.format}"

        output.parent.mkdir(parents=True, exist_ok=True)

        # Get brand context
        brand = getattr(project, "brand_context", None)
        theme = getattr(project, "theme", None)

        generator = DiagramGenerator(brand=brand, theme=theme)

        try:
            result = generator.generate(definition, output, engine=request.engine)
            return {
                "status": "built",
                "input": str(diagram_path.relative_to(project.root)),
                "output": str(result.relative_to(project.root)),
                "engine": request.engine or definition.config.engine.value,
                "dark_mode": request.dark_mode,
                "size_bytes": result.stat().st_size,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Build failed: {e}")

    @router.post("/api/diagrams/build-all")
    async def build_all_diagrams(
        background_tasks: BackgroundTasks,
        request: DiagramBuildRequest,
    ):
        """Build all diagrams in the project."""
        if build_state["active"]:
            return {"status": "error", "message": "Build already in progress"}

        project = get_project()
        language = request.language or project.source_language

        async def run_build():
            from ...diagrams import build_diagrams

            build_state["active"] = True
            build_state["progress"] = 0
            build_state["logs"] = []

            def log(msg: str, level: str = "info"):
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "message": msg,
                    "level": level,
                }
                build_state["logs"].append(entry)
                asyncio.create_task(
                    manager.broadcast({
                        "type": "diagram_build_log",
                        "entry": entry,
                    })
                )

            log(f"Starting diagram build: language={language}, engine={request.engine}, dark_mode={request.dark_mode}")

            try:
                paths = build_diagrams(
                    project,
                    language=language,
                    engine_override=request.engine,
                    dark_mode=request.dark_mode,
                )

                for path in paths:
                    log(f"Built {path.name}", "success")

                log(f"Completed: {len(paths)} diagrams built", "success")
                build_state["last_build"] = datetime.now().isoformat()

            except Exception as e:
                log(f"Build failed: {e}", "error")

            finally:
                build_state["active"] = False
                build_state["progress"] = 100

                await manager.broadcast({
                    "type": "diagram_build_complete",
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                })

        def run_build_sync():
            asyncio.run(run_build())

        background_tasks.add_task(run_build_sync)

        return {
            "status": "started",
            "language": language,
            "engine": request.engine,
            "dark_mode": request.dark_mode,
        }

    @router.get("/api/diagrams/build/status")
    async def get_build_status():
        """Get diagram build status."""
        project = get_project()

        # Get output files
        outputs = []
        output_dir = project.output_dir / "diagrams"
        if output_dir.exists():
            for f in output_dir.rglob("*"):
                if f.is_file() and f.suffix in [".png", ".svg", ".pdf", ".excalidraw"]:
                    outputs.append({
                        "path": str(f.relative_to(project.root)),
                        "name": f.name,
                        "format": f.suffix[1:].upper(),
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    })

        return {
            "active": build_state["active"],
            "progress": build_state["progress"],
            "logs": build_state["logs"][-50:],
            "last_build": build_state["last_build"],
            "outputs": sorted(outputs, key=lambda x: x["modified"], reverse=True)[:20],
        }

    @router.post("/api/diagrams/build/cancel")
    async def cancel_build():
        """Cancel active diagram build."""
        if not build_state["active"]:
            return {"status": "error", "message": "No active build"}

        build_state["active"] = False
        return {"status": "cancelled"}
