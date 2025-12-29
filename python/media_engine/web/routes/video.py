"""
Video Production API routes.

Provides endpoints for video script management, rendering, and asset browsing.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_video_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register video production routes."""
    from fastapi import BackgroundTasks, HTTPException
    from pydantic import BaseModel

    # Track render jobs
    render_state: Dict[str, Dict] = {}

    def find_remotion_dir(project: "Project") -> Optional[Path]:
        """Find remotion directory in project root or parent directories."""
        # Check project root first
        candidate = project.root / "remotion"
        if candidate.exists() and (candidate / "package.json").exists():
            return candidate

        # Check parent directories (for monorepo structure like demo/)
        for parent in project.root.parents:
            candidate = parent / "remotion"
            if candidate.exists() and (candidate / "package.json").exists():
                return candidate
            # Stop at filesystem root
            if parent == parent.parent:
                break

        return None

    class RenderRequest(BaseModel):
        """Request to start a video render."""

        script_id: str
        quality: str = "production"  # "preview" or "production"
        output_format: str = "mp4"

    class ScriptUpdateRequest(BaseModel):
        """Request to update a video script."""

        content: str

    class ScriptCreateRequest(BaseModel):
        """Request to create a new video script."""

        name: str
        content: str
        language: str = "en"

    class ScriptDuplicateRequest(BaseModel):
        """Request to duplicate a video script."""

        name: str

    # =========================================================================
    # Script Management
    # =========================================================================

    @router.get("/api/video/scripts")
    async def list_video_scripts():
        """List all video scripts in the project."""
        project = get_project()
        scripts = []

        # Find all YAML files in scripts/ directories
        for lang in project.languages:
            scripts_dir = project.content_dir / lang / "scripts"
            if scripts_dir.exists():
                for script_path in scripts_dir.glob("*.yaml"):
                    try:
                        import yaml

                        with open(script_path, "r") as f:
                            data = yaml.safe_load(f)

                        # Get output info if exists
                        output_path = project.output_dir / lang / "videos" / f"{script_path.stem}.mp4"
                        has_output = output_path.exists()
                        output_size = output_path.stat().st_size if has_output else None
                        output_modified = (
                            datetime.fromtimestamp(output_path.stat().st_mtime).isoformat()
                            if has_output
                            else None
                        )

                        scripts.append(
                            {
                                "id": f"{lang}/{script_path.stem}",
                                "name": data.get("title", script_path.stem),
                                "path": str(script_path.relative_to(project.root)),
                                "language": lang,
                                "description": data.get("description", ""),
                                "version": data.get("metadata", {}).get("version", "1.0.0"),
                                "status": data.get("metadata", {}).get("status", "draft"),
                                "scenes": len(data.get("scenes", [])),
                                "duration": _estimate_duration(data),
                                "has_output": has_output,
                                "output_size": output_size,
                                "output_modified": output_modified,
                            }
                        )
                    except Exception as e:
                        scripts.append(
                            {
                                "id": f"{lang}/{script_path.stem}",
                                "name": script_path.stem,
                                "path": str(script_path.relative_to(project.root)),
                                "language": lang,
                                "error": str(e),
                            }
                        )

        return {"scripts": scripts, "count": len(scripts)}

    @router.get("/api/video/scripts/{script_id:path}")
    async def get_video_script(script_id: str):
        """Get a video script's content and metadata."""
        project = get_project()

        # Parse script_id (format: lang/name)
        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        script_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")

        try:
            import yaml

            with open(script_path, "r") as f:
                content = f.read()
                data = yaml.safe_load(content)

            return {
                "id": script_id,
                "path": str(script_path.relative_to(project.root)),
                "content": content,
                "parsed": data,
                "modified": datetime.fromtimestamp(script_path.stat().st_mtime).isoformat(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read script: {e}")

    @router.put("/api/video/scripts/{script_id:path}")
    async def update_video_script(script_id: str, request: ScriptUpdateRequest):
        """Update a video script's content."""
        project = get_project()

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        script_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")

        try:
            # Validate YAML
            import yaml

            yaml.safe_load(request.content)

            # Write content
            with open(script_path, "w") as f:
                f.write(request.content)

            # Broadcast update
            await manager.broadcast(
                {"type": "script_updated", "script_id": script_id, "timestamp": datetime.now().isoformat()}
            )

            return {"status": "ok", "message": "Script updated"}
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update script: {e}")

    @router.post("/api/video/scripts")
    async def create_video_script(request: ScriptCreateRequest):
        """Create a new video script."""
        project = get_project()
        import yaml
        import re

        # Sanitize the name to create a valid filename
        safe_name = re.sub(r'[^\w\-]', '_', request.name.lower().strip())
        if not safe_name:
            safe_name = "untitled"

        # Ensure scripts directory exists
        scripts_dir = project.content_dir / request.language / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename if exists
        script_path = scripts_dir / f"{safe_name}.yaml"
        counter = 1
        while script_path.exists():
            script_path = scripts_dir / f"{safe_name}_{counter}.yaml"
            counter += 1

        try:
            # Validate YAML
            yaml.safe_load(request.content)

            # Write content
            with open(script_path, "w") as f:
                f.write(request.content)

            script_id = f"{request.language}/{script_path.stem}"

            # Broadcast creation
            await manager.broadcast(
                {"type": "script_created", "script_id": script_id, "timestamp": datetime.now().isoformat()}
            )

            return {"status": "ok", "script_id": script_id, "path": str(script_path.relative_to(project.root))}
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create script: {e}")

    @router.delete("/api/video/scripts/{script_id:path}")
    async def delete_video_script(script_id: str):
        """Delete a video script."""
        project = get_project()

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        script_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")

        try:
            script_path.unlink()

            # Broadcast deletion
            await manager.broadcast(
                {"type": "script_deleted", "script_id": script_id, "timestamp": datetime.now().isoformat()}
            )

            return {"status": "ok", "message": "Script deleted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete script: {e}")

    @router.post("/api/video/scripts/{script_id:path}/duplicate")
    async def duplicate_video_script(script_id: str, request: ScriptDuplicateRequest):
        """Duplicate a video script."""
        project = get_project()
        import yaml
        import re

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        source_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source script not found")

        try:
            # Read source content
            with open(source_path, "r") as f:
                content = f.read()
                data = yaml.safe_load(content)

            # Update title in content
            data["title"] = request.name

            # Generate safe filename
            safe_name = re.sub(r'[^\w\-]', '_', request.name.lower().strip())
            if not safe_name:
                safe_name = f"{name}_copy"

            scripts_dir = project.content_dir / lang / "scripts"
            new_path = scripts_dir / f"{safe_name}.yaml"
            counter = 1
            while new_path.exists():
                new_path = scripts_dir / f"{safe_name}_{counter}.yaml"
                counter += 1

            # Write new script
            with open(new_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            new_script_id = f"{lang}/{new_path.stem}"

            # Broadcast creation
            await manager.broadcast(
                {"type": "script_created", "script_id": new_script_id, "timestamp": datetime.now().isoformat()}
            )

            return {"status": "ok", "script_id": new_script_id, "path": str(new_path.relative_to(project.root))}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to duplicate script: {e}")

    @router.get("/api/video/scripts/{script_id:path}/props")
    async def get_script_props(script_id: str):
        """Generate Remotion props for a video script."""
        project = get_project()

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        script_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")

        try:
            from ...video.builder import VideoBuilder

            builder = VideoBuilder(project)
            props = builder.generate_props(script_path)

            return {"props": props}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate props: {e}")

    @router.get("/api/video/preview/config")
    async def get_preview_config():
        """Get Remotion preview configuration."""
        project = get_project()
        remotion_dir = find_remotion_dir(project)

        return {
            "enabled": remotion_dir is not None,
            "studio_url": "http://localhost:3000",  # Default Remotion Studio port
            "studio_port": 3000,
            "compositions": ["Main", "ProfessionalHook", "OutputShowcase"],
            "default_composition": "Main",
            "remotion_path": str(remotion_dir) if remotion_dir else None,
        }

    @router.post("/api/video/preview/start")
    async def start_preview_server(background_tasks: BackgroundTasks):
        """Start the Remotion Studio preview server."""
        project = get_project()
        remotion_dir = find_remotion_dir(project)

        if not remotion_dir:
            raise HTTPException(status_code=404, detail="Remotion project not found")

        try:
            import subprocess
            import os

            # Check if already running
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 3000))
            sock.close()

            if result == 0:
                return {"status": "already_running", "url": "http://localhost:3000"}

            # Start in background
            background_tasks.add_task(
                _start_remotion_studio,
                remotion_dir,
            )

            return {"status": "starting", "url": "http://localhost:3000"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start preview: {e}")

    # =========================================================================
    # Render Management
    # =========================================================================

    @router.post("/api/video/render")
    async def start_render(request: RenderRequest, background_tasks: BackgroundTasks):
        """Start a video render job."""
        project = get_project()

        parts = request.script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        script_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")

        # Create job
        job_id = str(uuid.uuid4())[:8]
        render_state[job_id] = {
            "id": job_id,
            "script_id": request.script_id,
            "quality": request.quality,
            "status": "queued",
            "progress": 0,
            "stage": "initializing",
            "started": datetime.now().isoformat(),
            "completed": None,
            "error": None,
            "output_path": None,
        }

        # Start background render
        background_tasks.add_task(_run_render, job_id, project, script_path, request, manager, render_state)

        await manager.broadcast({"type": "render_started", "job_id": job_id, "script_id": request.script_id})

        return {"job_id": job_id, "status": "queued"}

    @router.get("/api/video/render/{job_id}")
    async def get_render_status(job_id: str):
        """Get the status of a render job."""
        if job_id not in render_state:
            raise HTTPException(status_code=404, detail="Render job not found")

        return render_state[job_id]

    @router.delete("/api/video/render/{job_id}")
    async def cancel_render(job_id: str):
        """Cancel an active render job."""
        if job_id not in render_state:
            raise HTTPException(status_code=404, detail="Render job not found")

        job = render_state[job_id]
        if job["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Job already finished")

        job["status"] = "cancelled"
        job["completed"] = datetime.now().isoformat()

        await manager.broadcast({"type": "render_cancelled", "job_id": job_id})

        return {"status": "cancelled"}

    @router.get("/api/video/render/{job_id}/download")
    async def download_render(job_id: str):
        """Get download URL for a completed render."""
        from fastapi.responses import FileResponse

        if job_id not in render_state:
            raise HTTPException(status_code=404, detail="Render job not found")

        job = render_state[job_id]
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Render not completed")

        output_path = job.get("output_path")
        if not output_path:
            raise HTTPException(status_code=404, detail="Output file not found")

        output_file = Path(output_path)
        if not output_file.exists():
            raise HTTPException(status_code=404, detail="Output file not found on disk")

        # Return a URL that can be used to download the file
        # The actual file serving would be handled by a static files route
        project = get_project()
        relative_path = output_file.relative_to(project.root)

        return {
            "download_url": f"/api/video/file/{relative_path}",
            "filename": output_file.name,
            "size": output_file.stat().st_size,
        }

    @router.get("/api/video/file/{file_path:path}")
    async def serve_video_file(file_path: str):
        """Serve a video file for download."""
        from fastapi.responses import FileResponse

        project = get_project()
        full_path = project.root / file_path

        # Security: ensure the path is within the project
        try:
            full_path.resolve().relative_to(project.root.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type="video/mp4",
        )

    @router.get("/api/video/queue")
    async def get_render_queue():
        """Get all render jobs."""
        jobs = list(render_state.values())
        # Sort by started time, most recent first
        jobs.sort(key=lambda x: x.get("started", ""), reverse=True)

        return {
            "jobs": jobs,
            "active": sum(1 for j in jobs if j["status"] in ["queued", "rendering"]),
            "completed": sum(1 for j in jobs if j["status"] == "completed"),
            "failed": sum(1 for j in jobs if j["status"] == "failed"),
        }

    # =========================================================================
    # Assets Management
    # =========================================================================

    @router.get("/api/video/assets")
    async def list_video_assets():
        """List video production assets (demo clips, audio, graphics)."""
        project = get_project()
        assets = {"demos": [], "audio": [], "graphics": [], "outputs": []}

        # Demo clips
        demos_dir = project.root / "remotion" / "public" / "demos"
        if demos_dir.exists():
            for clip in demos_dir.glob("*.mp4"):
                assets["demos"].append(
                    {
                        "name": clip.stem,
                        "path": f"demos/{clip.name}",
                        "size": clip.stat().st_size,
                        "modified": datetime.fromtimestamp(clip.stat().st_mtime).isoformat(),
                    }
                )

        # Audio files (voiceovers)
        for lang in project.languages:
            audio_dir = project.output_dir / lang / "videos"
            if audio_dir.exists():
                for audio in audio_dir.glob("*.mp3"):
                    assets["audio"].append(
                        {
                            "name": audio.stem,
                            "path": str(audio.relative_to(project.root)),
                            "language": lang,
                            "size": audio.stat().st_size,
                            "modified": datetime.fromtimestamp(audio.stat().st_mtime).isoformat(),
                        }
                    )

        # Output videos
        for lang in project.languages:
            videos_dir = project.output_dir / lang / "videos"
            if videos_dir.exists():
                for video in videos_dir.glob("*.mp4"):
                    assets["outputs"].append(
                        {
                            "name": video.stem,
                            "path": str(video.relative_to(project.root)),
                            "language": lang,
                            "size": video.stat().st_size,
                            "modified": datetime.fromtimestamp(video.stat().st_mtime).isoformat(),
                        }
                    )

        return assets

    @router.get("/api/video/components")
    async def list_motion_components():
        """List available Remotion motion graphics components."""
        # Component catalog - could be loaded from JSON file
        components = [
            {
                "id": "TitleCard",
                "name": "Title Card",
                "category": "title",
                "description": "Animated title sequence with gradient text and glow effects",
                "props": ["title", "tagline", "variant"],
            },
            {
                "id": "TextReveal",
                "name": "Text Reveal",
                "category": "text",
                "description": "Kinetic typography with multiple animation styles",
                "props": ["text", "effect", "delay", "size"],
            },
            {
                "id": "FeatureCard",
                "name": "Feature Card",
                "category": "layout",
                "description": "Animated feature showcase with icon and bullets",
                "props": ["title", "icon", "bullets", "highlight"],
            },
            {
                "id": "StatCounter",
                "name": "Stat Counter",
                "category": "data",
                "description": "Animated number counter with label",
                "props": ["value", "label", "prefix", "suffix"],
            },
            {
                "id": "Background",
                "name": "Background",
                "category": "background",
                "description": "Animated backgrounds (aurora, grid, particles, cyber, waves)",
                "props": ["variant", "intensity"],
            },
            {
                "id": "Transition",
                "name": "Transition",
                "category": "transition",
                "description": "Scene transitions (glitch, aurora-sweep, slice, zoom-burst)",
                "props": ["type", "direction", "duration"],
            },
            {
                "id": "SplitScreenDemo",
                "name": "Split Screen Demo",
                "category": "layout",
                "description": "Diagonal split between demo video and motion graphics",
                "props": ["demoClipPath", "title", "bullets", "splitAngle"],
            },
        ]

        backgrounds = ["dark", "aurora", "grid", "particles", "pulse", "cyber", "waves"]
        transitions = [
            "fade",
            "wipe",
            "glitch",
            "aurora-sweep",
            "slice",
            "zoom-burst",
            "diagonal-split",
            "liquid",
            "pixel-dissolve",
            "rotate-wipe",
            "flash",
            "grid-reveal",
            "radial",
        ]
        text_effects = ["fade-up", "bounce", "elastic", "wave", "split", "scale-pop", "rotate", "glitch"]

        return {
            "components": components,
            "backgrounds": backgrounds,
            "transitions": transitions,
            "text_effects": text_effects,
        }

    @router.get("/api/video/voices")
    async def list_available_voices():
        """List available TTS voices for voiceover generation."""
        project = get_project()

        voices = []
        for lang_code, lang_config in project.languages.items():
            if hasattr(lang_config, "voice_id") and lang_config.voice_id:
                voices.append(
                    {
                        "language": lang_code,
                        "voice_id": lang_config.voice_id,
                        "name": getattr(lang_config, "voice_name", lang_code),
                    }
                )

        # Default voice from config
        if hasattr(project.config, "voiceover"):
            voices.append(
                {
                    "language": "default",
                    "voice_id": project.config.voiceover.voice_id,
                    "name": "Default",
                }
            )

        return {"voices": voices}


# =============================================================================
# Helper Functions
# =============================================================================


def _estimate_duration(script_data: Dict) -> Optional[float]:
    """Estimate total video duration from script."""
    total = 0
    for scene in script_data.get("scenes", []):
        duration = scene.get("duration", 5)
        total += duration
    return total if total > 0 else None


async def _run_render(
    job_id: str,
    project: "Project",
    script_path: Path,
    request: Any,
    manager: "ConnectionManager",
    render_state: Dict,
):
    """Run video render in background."""
    job = render_state[job_id]

    try:
        job["status"] = "rendering"
        job["stage"] = "generating_voiceover"
        await manager.broadcast({"type": "render_progress", "job_id": job_id, "progress": 5, "stage": "voiceover"})

        # Generate voiceover
        from ...video.builder import VideoBuilder

        builder = VideoBuilder(project)

        # Update progress through stages
        job["progress"] = 10
        await manager.broadcast({"type": "render_progress", "job_id": job_id, "progress": 10, "stage": "voiceover"})

        # Build video
        job["stage"] = "rendering_video"
        job["progress"] = 30
        await manager.broadcast(
            {"type": "render_progress", "job_id": job_id, "progress": 30, "stage": "rendering_video"}
        )

        # Call the builder
        lang = request.script_id.split("/")[0]
        output_path = await builder.build_video_async(
            script_path,
            quality=request.quality,
            language=lang,
            progress_callback=lambda p, s: _update_render_progress(job_id, p, s, manager, render_state),
        )

        # Complete
        job["status"] = "completed"
        job["progress"] = 100
        job["stage"] = "done"
        job["completed"] = datetime.now().isoformat()
        job["output_path"] = str(output_path) if output_path else None

        await manager.broadcast(
            {
                "type": "render_complete",
                "job_id": job_id,
                "output_path": job["output_path"],
            }
        )

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed"] = datetime.now().isoformat()

        await manager.broadcast(
            {
                "type": "render_failed",
                "job_id": job_id,
                "error": str(e),
            }
        )


async def _update_render_progress(job_id: str, progress: int, stage: str, manager: "ConnectionManager", render_state: Dict):
    """Update render progress and broadcast."""
    if job_id in render_state:
        render_state[job_id]["progress"] = progress
        render_state[job_id]["stage"] = stage
        await manager.broadcast({"type": "render_progress", "job_id": job_id, "progress": progress, "stage": stage})


def _start_remotion_studio(remotion_dir: Path):
    """Start Remotion Studio server in background."""
    import subprocess
    import os

    try:
        subprocess.Popen(
            ["npm", "run", "start"],
            cwd=str(remotion_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "BROWSER": "none"},  # Don't auto-open browser
        )
    except Exception as e:
        print(f"Failed to start Remotion Studio: {e}")
