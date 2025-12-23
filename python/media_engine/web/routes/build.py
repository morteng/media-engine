"""
Build API routes.
"""

import asyncio
from typing import TYPE_CHECKING, Callable, Dict

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_build_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register build-related routes."""
    from datetime import datetime

    from fastapi import BackgroundTasks

    # Track active builds
    build_state: Dict = {
        "active": False,
        "progress": 0,
        "logs": [],
        "last_build": None,
        "outputs": [],
    }

    @router.get("/api/build/status")
    async def get_build_status():
        """Get current build status."""
        project = get_project()

        # Check freshness for warnings
        try:
            from ...freshness import ContentRegistry, scan_project

            registry = ContentRegistry(project)
            registry.load()
            if not registry.items:
                scan_project(project, registry)
            report = registry.refresh()

            freshness_warning = None
            if report.stale_count > 0 or report.expired_count > 0:
                freshness_warning = {
                    "stale": report.stale_count,
                    "expired": report.expired_count,
                    "message": f"{report.stale_count + report.expired_count} items are stale and should be rebuilt",
                }
        except Exception:
            freshness_warning = None

        # Get output files
        outputs = []
        for lang in project.languages:
            output_dir = project.output_dir / lang
            if output_dir.exists():
                for f in output_dir.iterdir():
                    if f.is_file() and f.suffix in [".html", ".pdf", ".pptx", ".xlsx"]:
                        outputs.append(
                            {
                                "path": str(f.relative_to(project.root)),
                                "name": f.name,
                                "format": f.suffix[1:].upper(),
                                "language": lang,
                                "size": f.stat().st_size,
                                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                            }
                        )

        return {
            "active": build_state["active"],
            "progress": build_state["progress"],
            "logs": build_state["logs"][-50:],  # Last 50 entries
            "last_build": build_state["last_build"],
            "freshness_warning": freshness_warning,
            "outputs": sorted(outputs, key=lambda x: x["modified"], reverse=True)[:20],
        }

    @router.post("/api/build/start")
    async def start_build(
        background_tasks: BackgroundTasks,
        formats: str = "html",
        languages: str = None,
        force: bool = False,
    ):
        """Start a build process."""
        if build_state["active"]:
            return {"status": "error", "message": "Build already in progress"}

        project = get_project()
        format_list = [f.strip() for f in formats.split(",") if f.strip()]
        lang_list = (
            [lang.strip() for lang in languages.split(",")]
            if languages
            else list(project.languages.keys())
        )

        async def run_build():
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
                # Broadcast to connected clients
                asyncio.create_task(
                    manager.broadcast(
                        {
                            "type": "build_log",
                            "entry": entry,
                        }
                    )
                )

            log(f"Starting build: formats={format_list}, languages={lang_list}, force={force}")

            try:
                total_steps = len(format_list) * len(lang_list)
                current_step = 0

                for fmt in format_list:
                    for lang in lang_list:
                        current_step += 1
                        build_state["progress"] = int((current_step / total_steps) * 100)

                        log(f"Building {fmt.upper()} for {lang}...")

                        try:
                            if fmt == "html":
                                from ...builders.html import HTMLBuilder

                                builder = HTMLBuilder(project.theme)
                                # Build chapters
                                content_dir = project.content_dir / lang / "chapters"
                                if content_dir.exists():
                                    for md_file in sorted(content_dir.glob("*.md")):
                                        output_path = (
                                            project.output_dir / lang / f"{md_file.stem}.html"
                                        )
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        with open(md_file) as f:
                                            content = f.read()
                                        builder.build(content, output_path, title=md_file.stem)
                                        log(f"  Built {output_path.name}", "success")

                            elif fmt == "pptx":
                                from ...builders.pptx import PPTXBuilder

                                builder = PPTXBuilder(theme=project.theme)
                                slides_dir = project.content_dir / lang / "slides"
                                if slides_dir.exists():
                                    for yaml_file in sorted(slides_dir.glob("*.yaml")):
                                        output_path = (
                                            project.output_dir / lang / f"{yaml_file.stem}.pptx"
                                        )
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        builder.build_from_yaml(yaml_file, output_path)
                                        log(f"  Built {output_path.name}", "success")

                            elif fmt == "xlsx":
                                from ...builders.xlsx import XLSXBuilder

                                builder = XLSXBuilder()
                                data_dir = project.content_dir / lang / "data"
                                if data_dir.exists():
                                    for yaml_file in sorted(data_dir.glob("*.yaml")):
                                        output_path = (
                                            project.output_dir / lang / f"{yaml_file.stem}.xlsx"
                                        )
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        builder.build_from_yaml(yaml_file, output_path)
                                        log(f"  Built {output_path.name}", "success")

                            elif fmt == "pdf":
                                log("  PDF generation requires wkhtmltopdf", "warning")

                        except Exception as e:
                            log(f"  Error building {fmt} for {lang}: {e}", "error")

                log("Build completed!", "success")
                build_state["last_build"] = datetime.now().isoformat()

            except Exception as e:
                log(f"Build failed: {e}", "error")

            finally:
                build_state["active"] = False
                build_state["progress"] = 100

                # Notify completion
                await manager.broadcast(
                    {
                        "type": "build_complete",
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        background_tasks.add_task(asyncio.create_task, run_build())

        return {
            "status": "started",
            "formats": format_list,
            "languages": lang_list,
            "force": force,
        }

    @router.post("/api/build/cancel")
    async def cancel_build():
        """Cancel active build."""
        if not build_state["active"]:
            return {"status": "error", "message": "No active build"}

        build_state["active"] = False
        return {"status": "cancelled"}

    @router.get("/api/build/outputs")
    async def get_build_outputs():
        """Get list of built output files."""
        project = get_project()
        outputs = []

        for lang in project.languages:
            output_dir = project.output_dir / lang
            if output_dir.exists():
                for f in output_dir.rglob("*"):
                    if f.is_file() and f.suffix in [".html", ".pdf", ".pptx", ".xlsx"]:
                        outputs.append(
                            {
                                "path": str(f.relative_to(project.root)),
                                "name": f.name,
                                "format": f.suffix[1:].upper(),
                                "language": lang,
                                "size": f.stat().st_size,
                                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                            }
                        )

        return {
            "outputs": sorted(outputs, key=lambda x: x["modified"], reverse=True),
        }
