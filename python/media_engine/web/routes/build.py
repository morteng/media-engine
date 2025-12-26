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

    @router.get("/api/build/presets")
    async def get_build_presets():
        """Get available layout presets for output generation."""
        from ...templates import PRESETS, get_all_presets

        presets = []
        for preset in get_all_presets():
            presets.append({
                "name": preset.name,
                "description": preset.description,
                "template": preset.template,
                "formats": preset.formats,
                "features": preset.features.to_dict(),
                "maxWidth": preset.max_width,
                "fontScale": preset.font_scale,
                "lineHeight": preset.line_height,
            })

        return {
            "presets": presets,
            "default": "minimal",
        }

    @router.get("/api/build/publications")
    async def get_build_publications():
        """Get publications available for building with their formats and languages."""
        from datetime import datetime

        project = get_project()
        publications = []

        try:
            from ...cms.publication import PublicationRegistry

            registry = PublicationRegistry(project)

            # Get all publications grouped by base name (across languages)
            seen_bases = {}  # base_name -> publication info

            for lang in project.languages:
                for pub in registry.list_publications(lang):
                    # Extract base name (without language prefix)
                    base_name = pub.path.stem

                    # Get available formats from publication outputs config
                    formats = []
                    if hasattr(pub, "outputs") and pub.outputs:
                        for output in pub.outputs:
                            if hasattr(output, "format"):
                                formats.append(output.format)
                    if not formats:
                        # Default formats based on type
                        pub_type = getattr(pub, "pub_type", "book")
                        if pub_type == "deck":
                            formats = ["pptx"]
                        elif pub_type == "spreadsheet":
                            formats = ["xlsx"]
                        else:
                            formats = ["html"]

                    # Check if output exists and get last modified
                    last_built = None
                    is_stale = True
                    for fmt in formats:
                        if fmt == "html":
                            output_path = project.output_dir / lang / f"{base_name}.html"
                        elif fmt == "pptx":
                            output_path = project.output_dir / lang / f"{base_name}.pptx"
                        elif fmt == "xlsx":
                            output_path = project.output_dir / lang / f"{base_name}.xlsx"
                        else:
                            output_path = project.output_dir / lang / f"{base_name}.{fmt}"

                        if output_path.exists():
                            mtime = datetime.fromtimestamp(output_path.stat().st_mtime)
                            if last_built is None or mtime > datetime.fromisoformat(last_built):
                                last_built = mtime.isoformat()
                            is_stale = False

                    if base_name not in seen_bases:
                        seen_bases[base_name] = {
                            "key": base_name,
                            "title": pub.title,
                            "pub_type": getattr(pub, "pub_type", "book"),
                            "languages": [lang],
                            "formats": formats,
                            "lastBuilt": last_built,
                            "isStale": is_stale,
                            "chapterCount": len(pub.chapters) if hasattr(pub, "chapters") else 0,
                        }
                    else:
                        # Add language to existing publication
                        if lang not in seen_bases[base_name]["languages"]:
                            seen_bases[base_name]["languages"].append(lang)
                        # Update stale status - not stale if any language has output
                        if not is_stale:
                            seen_bases[base_name]["isStale"] = False
                        # Update last built if newer
                        if last_built:
                            existing = seen_bases[base_name]["lastBuilt"]
                            if existing is None or last_built > existing:
                                seen_bases[base_name]["lastBuilt"] = last_built

            publications = list(seen_bases.values())

        except Exception as e:
            # Fallback to simple format-based approach if no publications
            pass

        return {
            "publications": publications,
            "projectLanguages": list(project.languages.keys()),
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
                                from ...builders.html import HTMLBuilder, HTMLConfig
                                from ...cms.publication import PublicationRegistry

                                builder = HTMLBuilder(brand=project.brand_context)

                                # Build publication-based outputs
                                try:
                                    registry = PublicationRegistry(project)
                                    publications = list(registry.list_publications(lang))

                                    for pub in publications:
                                        # Get all chapter files for this publication
                                        md_files = []
                                        for ch in pub.chapters:
                                            ch_path = project.content_dir / lang / ch.path
                                            if ch_path.exists():
                                                md_files.append(ch_path)

                                        if md_files:
                                            # Use publication key as filename (sanitized)
                                            safe_name = pub.path.stem.replace(" ", "_").lower()
                                            output_path = project.output_dir / lang / f"{safe_name}.html"
                                            output_path.parent.mkdir(parents=True, exist_ok=True)

                                            config = HTMLConfig(lang=lang, include_toc=True)
                                            html = builder.build_combined(
                                                md_files,
                                                title=pub.title,
                                                config=config,
                                            )
                                            builder.save(html, output_path)
                                            log(f"  Built {output_path.name} ({len(md_files)} {pub.item_label})", "success")

                                except Exception as pub_error:
                                    log(f"  Publication registry error: {pub_error}, falling back to chapters", "warning")
                                    # Fallback to chapter-based build
                                    content_dir = project.content_dir / lang / "chapters"
                                    if content_dir.exists():
                                        md_files = sorted(content_dir.glob("*.md"))
                                        if md_files:
                                            combined_output = project.output_dir / lang / "documentation.html"
                                            combined_output.parent.mkdir(parents=True, exist_ok=True)
                                            config = HTMLConfig(lang=lang, include_toc=True)
                                            html = builder.build_combined(
                                                md_files,
                                                title=project.name or "Documentation",
                                                config=config,
                                            )
                                            builder.save(html, combined_output)
                                            log(f"  Built {combined_output.name} ({len(md_files)} chapters)", "success")

                            elif fmt == "pptx":
                                from ...builders.pptx import PPTXBuilder

                                slides_dir = project.content_dir / lang / "slides"
                                if slides_dir.exists():
                                    for yaml_file in sorted(slides_dir.glob("*.yaml")):
                                        output_path = (
                                            project.output_dir / lang / f"{yaml_file.stem}.pptx"
                                        )
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        # Create new builder for each file (PPTX can't be reused)
                                        pptx_builder = PPTXBuilder(brand=project.brand_context)
                                        pptx_builder.build_from_yaml(yaml_file)
                                        pptx_builder.save(output_path)
                                        log(f"  Built {output_path.name}", "success")

                            elif fmt == "xlsx":
                                from ...builders.xlsx import XLSXBuilder

                                data_dir = project.content_dir / lang / "data"
                                if data_dir.exists():
                                    for yaml_file in sorted(data_dir.glob("*.yaml")):
                                        output_path = (
                                            project.output_dir / lang / f"{yaml_file.stem}.xlsx"
                                        )
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        # Create new builder for each file
                                        xlsx_builder = XLSXBuilder(brand=project.brand_context)
                                        xlsx_builder.build_from_yaml(yaml_file)
                                        xlsx_builder.save(output_path)
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

        def run_build_sync():
            """Wrapper to run async build in thread pool."""
            asyncio.run(run_build())

        background_tasks.add_task(run_build_sync)

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

    @router.post("/api/build/unified")
    async def unified_build(
        background_tasks: BackgroundTasks,
        request: Dict = None,
    ):
        """
        Unified build endpoint supporting publication-based builds.

        Request body:
        {
            "publications": [
                {"key": "documentation", "formats": ["html"], "languages": ["en", "no"]},
                {"key": "pitch_deck", "formats": ["pptx"], "languages": ["en"]}
            ],
            "publish": true,
            "outputDir": "~/Desktop/Project/",
            "includeFonts": true,
            "includeDiagrams": true,
            "includeVideos": true
        }
        """
        from pathlib import Path

        if build_state["active"]:
            return {"status": "error", "message": "Build already in progress"}

        project = get_project()

        # Parse request
        if request is None:
            request = {}

        publications = request.get("publications", [])
        should_publish = request.get("publish", False)
        output_dir = request.get("outputDir")
        include_fonts = request.get("includeFonts", True)
        include_diagrams = request.get("includeDiagrams", True)
        include_videos = request.get("includeVideos", True)
        preset_name = request.get("preset")  # Layout preset for HTML output

        # Resolve publish path
        if output_dir:
            publish_path = Path(output_dir).expanduser()
        elif project.config.paths.publish:
            publish_path = Path(project.config.paths.publish).expanduser()
        else:
            publish_path = Path.home() / "Desktop" / project.config.name

        async def run_unified_build():
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
                    manager.broadcast({"type": "build_log", "entry": entry})
                )

            try:
                from ...builders.html import HTMLBuilder, HTMLConfig
                from ...builders.pptx import PPTXBuilder
                from ...builders.xlsx import XLSXBuilder
                from ...cms.publication import PublicationRegistry

                registry = PublicationRegistry(project)

                # Calculate total steps
                total_steps = sum(
                    len(p.get("formats", [])) * len(p.get("languages", []))
                    for p in publications
                )
                if should_publish:
                    total_steps += 1  # Publishing step
                current_step = 0

                log(f"Building {len(publications)} publications...")

                for pub_config in publications:
                    pub_key = pub_config.get("key")
                    formats = pub_config.get("formats", ["html"])
                    languages = pub_config.get("languages", list(project.languages.keys()))

                    for lang in languages:
                        # Find the publication
                        pub = None
                        for p in registry.list_publications(lang):
                            if p.path.stem == pub_key:
                                pub = p
                                break

                        if not pub:
                            log(f"  Publication '{pub_key}' not found for {lang}", "warning")
                            continue

                        for fmt in formats:
                            current_step += 1
                            build_state["progress"] = int((current_step / total_steps) * 100)

                            log(f"Building {pub.title} ({fmt.upper()}) for {lang}...")

                            try:
                                if fmt == "html":
                                    builder = HTMLBuilder(
                                        brand=project.brand_context,
                                        project=project,
                                    )
                                    md_files = []
                                    for ch in pub.chapters:
                                        ch_path = project.content_dir / lang / ch.path
                                        if ch_path.exists():
                                            md_files.append(ch_path)

                                    if md_files:
                                        safe_name = pub.path.stem.replace(" ", "_").lower()
                                        output_path = project.output_dir / lang / f"{safe_name}.html"
                                        output_path.parent.mkdir(parents=True, exist_ok=True)

                                        # Use preset if specified
                                        config = HTMLConfig(
                                            lang=lang,
                                            include_toc=True,
                                            preset=preset_name,
                                            project_name=project.name,
                                        )
                                        html = builder.build_combined(
                                            md_files,
                                            title=pub.title,
                                            config=config,
                                        )
                                        builder.save(html, output_path)
                                        preset_msg = f" (preset: {preset_name})" if preset_name else ""
                                        log(f"  Built {output_path.name}{preset_msg}", "success")

                                elif fmt == "pptx":
                                    # Look for slides YAML
                                    slides_dir = project.content_dir / lang / "slides"
                                    yaml_path = slides_dir / f"{pub_key}.yaml"
                                    if yaml_path.exists():
                                        output_path = project.output_dir / lang / f"{pub_key}.pptx"
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        pptx_builder = PPTXBuilder(brand=project.brand_context)
                                        pptx_builder.build_from_yaml(yaml_path)
                                        pptx_builder.save(output_path)
                                        log(f"  Built {output_path.name}", "success")
                                    else:
                                        log(f"  No slides YAML found for {pub_key}", "warning")

                                elif fmt == "xlsx":
                                    data_dir = project.content_dir / lang / "data"
                                    yaml_path = data_dir / f"{pub_key}.yaml"
                                    if yaml_path.exists():
                                        output_path = project.output_dir / lang / f"{pub_key}.xlsx"
                                        output_path.parent.mkdir(parents=True, exist_ok=True)
                                        xlsx_builder = XLSXBuilder(brand=project.brand_context)
                                        xlsx_builder.build_from_yaml(yaml_path)
                                        xlsx_builder.save(output_path)
                                        log(f"  Built {output_path.name}", "success")
                                    else:
                                        log(f"  No data YAML found for {pub_key}", "warning")

                                elif fmt == "pdf":
                                    log("  PDF generation requires wkhtmltopdf", "warning")

                            except Exception as e:
                                log(f"  Error building {pub_key} ({fmt}): {e}", "error")

                # Publish if requested
                if should_publish:
                    log(f"Publishing to {publish_path}...")
                    build_state["progress"] = 95

                    try:
                        from ...publish.packager import PublishConfig, publish_project

                        pub_config = PublishConfig(
                            output_dir=publish_path,
                            include_fonts=include_fonts,
                            include_diagrams=include_diagrams,
                            include_videos=include_videos,
                            console_output=False,
                        )
                        result = publish_project(project, pub_config)

                        log(f"Published {result.documents_copied} documents", "success")
                        log(f"Bundled {result.assets_bundled} assets", "success")
                        log(f"Output: {publish_path}", "success")

                    except Exception as e:
                        log(f"Publish failed: {e}", "error")
                        import traceback
                        log(traceback.format_exc(), "error")

                log("Build completed!", "success")
                build_state["last_build"] = datetime.now().isoformat()
                build_state["progress"] = 100

            except Exception as e:
                log(f"Build failed: {e}", "error")

            finally:
                build_state["active"] = False
                await manager.broadcast(
                    {
                        "type": "build_complete",
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        def run_unified_build_sync():
            asyncio.run(run_unified_build())

        background_tasks.add_task(run_unified_build_sync)

        return {
            "status": "started",
            "publications": [p.get("key") for p in publications],
            "publish": should_publish,
            "outputDir": str(publish_path) if should_publish else None,
        }

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

    @router.get("/api/build/publish-config")
    async def get_publish_config():
        """Get current publish configuration."""
        from pathlib import Path

        project = get_project()
        paths = project.config.paths

        # Determine publish path
        publish_path = str(paths.publish) if paths.publish else None

        # Check if desktop deliverables is enabled
        desktop_path = Path.home() / "Desktop" / project.config.name
        is_desktop_deliverables = (
            publish_path and Path(publish_path).resolve() == desktop_path.resolve()
        )

        # Default path if not configured
        default_path = str(project.root / "dist" / project.config.name)

        return {
            "publish_path": publish_path or default_path,
            "desktop_deliverables": is_desktop_deliverables,
            "default_path": default_path,
            "desktop_path": str(desktop_path),
            "project_name": project.config.name,
        }

    @router.post("/api/build/publish")
    async def publish_deliverables(
        background_tasks: BackgroundTasks,
        output_dir: str = None,
        include_fonts: bool = True,
        include_diagrams: bool = True,
        include_videos: bool = True,
    ):
        """Create deliverables package at specified directory."""
        from pathlib import Path

        project = get_project()

        # Determine output directory
        if output_dir:
            publish_path = Path(output_dir).expanduser()
        elif project.config.paths.publish:
            publish_path = Path(project.config.paths.publish).expanduser()
        else:
            publish_path = Path.home() / "Desktop" / project.config.name

        async def run_publish():
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
                    manager.broadcast({"type": "build_log", "entry": entry})
                )

            log(f"Publishing deliverables to: {publish_path}")

            try:
                from ...publish.packager import (
                    PublishConfig,
                    collect_deliverables,
                    publish_project,
                )

                build_state["progress"] = 10

                log("Collecting deliverables...")
                # Collect deliverables for each language
                total_items = 0
                for lang in project.languages:
                    categories = collect_deliverables(project, lang)
                    for cat in categories:
                        total_items += len(cat.items)
                        log(f"  {lang}/{cat.name}: {len(cat.items)} items")
                build_state["progress"] = 30

                log(f"Found {total_items} total deliverable items")

                log("Creating package...")
                build_state["progress"] = 50

                # Create publish config and run publish
                pub_config = PublishConfig(
                    output_dir=publish_path,
                    include_fonts=include_fonts,
                    include_diagrams=include_diagrams,
                    include_videos=include_videos,
                    console_output=False,
                )
                result = publish_project(project, pub_config)
                build_state["progress"] = 90

                log(f"Published {result.documents_copied} documents", "success")
                log(f"Bundled {result.assets_bundled} assets", "success")
                log(f"Output: {publish_path}", "success")

                build_state["last_build"] = datetime.now().isoformat()
                build_state["progress"] = 100

            except Exception as e:
                log(f"Publish failed: {e}", "error")
                import traceback
                log(traceback.format_exc(), "error")

            finally:
                build_state["active"] = False
                await manager.broadcast(
                    {
                        "type": "publish_complete",
                        "success": True,
                        "path": str(publish_path),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        def run_publish_sync():
            asyncio.run(run_publish())

        background_tasks.add_task(run_publish_sync)

        return {
            "status": "started",
            "output_dir": str(publish_path),
            "include_fonts": include_fonts,
            "include_diagrams": include_diagrams,
            "include_videos": include_videos,
        }
