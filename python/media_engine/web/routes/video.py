"""
Video Production API routes.

Provides endpoints for video script management, rendering, and asset browsing.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

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

    class VoiceoverRequest(BaseModel):
        """Request to generate voiceover for a script."""

        mode: str = "mock"  # "mock", "macos", or "elevenlabs"
        voice_id: Optional[str] = None
        force: bool = False  # Regenerate even if cached

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

    @router.post("/api/video/scripts/{script_id:path}/voiceover")
    async def generate_script_voiceover(script_id: str, request: VoiceoverRequest, background_tasks: BackgroundTasks):
        """Generate voiceover audio for a video script."""
        project = get_project()

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        script_path = project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")

        # Output path for voiceover
        output_dir = project.output_dir / lang / "videos"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"{name}.mp3"

        # Check if already exists and not forcing regeneration
        if audio_path.exists() and not request.force:
            return {
                "status": "exists",
                "audio_path": str(audio_path.relative_to(project.root)),
                "message": "Voiceover already exists. Use force=true to regenerate.",
            }

        # Generate voiceover in background
        job_id = str(uuid.uuid4())[:8]
        background_tasks.add_task(
            _run_voiceover_generation,
            job_id,
            project,
            script_path,
            audio_path,
            request.mode,
            manager,
        )

        await manager.broadcast({
            "type": "voiceover_started",
            "job_id": job_id,
            "script_id": script_id,
        })

        return {
            "status": "generating",
            "job_id": job_id,
            "audio_path": str(audio_path.relative_to(project.root)),
        }

    @router.get("/api/video/scripts/{script_id:path}/voiceover/status")
    async def get_voiceover_status(script_id: str):
        """Check if voiceover exists for a script."""
        project = get_project()

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid script ID format")

        lang, name = parts
        audio_path = project.output_dir / lang / "videos" / f"{name}.mp3"
        props_path = project.output_dir / lang / "videos" / f"{name}.props.json"

        return {
            "has_voiceover": audio_path.exists(),
            "has_props": props_path.exists(),
            "audio_path": str(audio_path.relative_to(project.root)) if audio_path.exists() else None,
            "audio_size": audio_path.stat().st_size if audio_path.exists() else None,
            "audio_modified": datetime.fromtimestamp(audio_path.stat().st_mtime).isoformat() if audio_path.exists() else None,
        }

    @router.get("/api/video/preview/config")
    async def get_preview_config():
        """Get Remotion preview configuration."""
        project = get_project()
        remotion_dir = find_remotion_dir(project)

        return {
            "enabled": remotion_dir is not None,
            "studio_url": "http://localhost:3001",  # Remotion Studio port (3000 often taken by other services)
            "studio_port": 3001,
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
            result = sock.connect_ex(('localhost', 3001))
            sock.close()

            if result == 0:
                return {"status": "already_running", "url": "http://localhost:3001"}

            # Start in background
            background_tasks.add_task(
                _start_remotion_studio,
                remotion_dir,
            )

            return {"status": "starting", "url": "http://localhost:3001"}
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

    @router.get("/api/video/asset")
    async def serve_video_asset(path: str):
        """Serve a video asset (demo clip, audio, etc.) for preview.

        Path can be:
        - demos/xyz.mp4 (remotion/public/demos)
        - output/lang/videos/xyz.mp4 (project output)
        """
        from fastapi.responses import FileResponse

        project = get_project()

        # Handle demo clips from remotion/public
        if path.startswith("demos/"):
            remotion_dir = find_remotion_dir(project)
            if not remotion_dir:
                raise HTTPException(status_code=404, detail="Remotion project not found")
            full_path = remotion_dir / "public" / path
        else:
            # Handle output files
            full_path = project.root / path

        # Security: ensure the path is within allowed directories
        try:
            resolved = full_path.resolve()
            remotion_dir = find_remotion_dir(project)

            allowed_roots = [project.root.resolve()]
            if remotion_dir:
                allowed_roots.append(remotion_dir.resolve())

            if not any(str(resolved).startswith(str(root)) for root in allowed_roots):
                raise HTTPException(status_code=403, detail="Access denied")
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Determine media type
        suffix = full_path.suffix.lower()
        media_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
        }
        media_type = media_types.get(suffix, "application/octet-stream")

        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type=media_type,
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
            {
                "id": "CameraCanvas",
                "name": "Camera Canvas",
                "category": "camera",
                "description": "Animated camera pan/zoom over high-res screenshots",
                "props": ["imagePath", "captureWidth", "captureHeight", "keyframes", "background", "shadow"],
            },
            {
                "id": "AnimatedDemoScene",
                "name": "Animated Demo Scene",
                "category": "camera",
                "description": "Demo scene with camera animation and voiceover captions",
                "props": ["demo", "state", "cameraData", "text", "showCaptions", "showFocusHighlight"],
            },
            {
                "id": "FocusHighlight",
                "name": "Focus Highlight",
                "category": "camera",
                "description": "Highlight overlay for target elements (glow, outline, dim-others)",
                "props": ["bounds", "style", "color", "cameraState"],
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

    @router.get("/api/video/camera/presets")
    async def list_camera_presets():
        """List available camera animation presets."""
        from ...video.camera_presets import CAMERA_PRESETS

        presets = []
        for preset_id, preset in CAMERA_PRESETS.items():
            presets.append({
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
                "pattern": preset.pattern,
                "default_zoom": preset.default_zoom,
                "default_duration": preset.default_duration,
                "default_hold": preset.default_hold,
                "default_easing": preset.default_easing,
                "start_zoom": preset.start_zoom,
                "end_zoom": preset.end_zoom,
            })

        return {
            "presets": presets,
            "count": len(presets),
        }

    @router.get("/api/video/camera/easings")
    async def list_camera_easings():
        """List available camera easing functions."""
        from ...video.camera_path import EASING_FUNCTIONS

        easings = []
        for name in EASING_FUNCTIONS.keys():
            easings.append({
                "name": name,
                "recommended": name in ["easeInOutCubic", "easeOutCubic", "easeOutQuart"],
            })

        return {
            "easings": easings,
            "count": len(easings),
            "recommended": "easeInOutCubic",
        }

    @router.get("/api/video/effects/presets")
    async def list_effect_presets():
        """List available visual effects presets."""
        from ...video.camera_effects import EFFECT_PRESETS

        presets = []
        for preset_id, preset in EFFECT_PRESETS.items():
            presets.append({
                "id": preset_id,
                "name": preset_id.replace("_", " ").title(),
                "description": _get_effect_preset_description(preset_id),
                "vignette_enabled": preset.vignette.enabled,
                "shake_enabled": preset.camera_shake.enabled,
                "perspective_enabled": preset.perspective_tilt.enabled,
                "depth_of_field_enabled": preset.depth_of_field.enabled,
                "motion_blur_enabled": preset.motion_blur.enabled,
            })

        return {
            "presets": presets,
            "count": len(presets),
        }

    # =========================================================================
    # Demo Recording Routes
    # =========================================================================

    @router.get("/api/video/demos")
    async def list_demo_recordings():
        """List all demo recording definitions."""
        from ...video.demo_capture import load_demo_definition

        project = get_project()
        demos = []

        # Search for demo definition files in content/*/demos/
        for lang in project.languages:
            demos_dir = project.content_dir / lang / "demos"
            if demos_dir.exists():
                for demo_file in sorted(demos_dir.glob("*.yaml")):
                    try:
                        definition = load_demo_definition(demo_file)
                        demos.append({
                            "id": demo_file.stem,
                            "name": definition.name,
                            "path": str(demo_file.relative_to(project.root)),
                            "language": lang,
                            "url": definition.url,
                            "viewport": {
                                "width": definition.viewport_width,
                                "height": definition.viewport_height,
                            },
                            "states_count": len(definition.states),
                            "sequences_count": len(definition.sequences),
                        })
                    except Exception as e:
                        demos.append({
                            "id": demo_file.stem,
                            "name": demo_file.stem,
                            "path": str(demo_file.relative_to(project.root)),
                            "language": lang,
                            "error": str(e),
                        })

        return {"demos": demos, "count": len(demos)}

    @router.get("/api/video/demos/{demo_id}")
    async def get_demo_recording(demo_id: str, language: str = "en"):
        """Get a single demo recording definition with full details."""
        import yaml
        from ...video.demo_capture import load_demo_definition

        project = get_project()

        # Find the demo file
        demo_file = project.content_dir / language / "demos" / f"{demo_id}.yaml"
        if not demo_file.exists():
            # Try other languages
            for lang in project.languages:
                demo_file = project.content_dir / lang / "demos" / f"{demo_id}.yaml"
                if demo_file.exists():
                    break
            else:
                raise HTTPException(status_code=404, detail=f"Demo '{demo_id}' not found")

        try:
            definition = load_demo_definition(demo_file)

            # Parse camera configurations from states
            states = []
            with open(demo_file, "r") as f:
                raw_data = yaml.safe_load(f)

            for state_id, state in definition.states.items():
                state_data = {
                    "id": state_id,
                    "description": state.description,
                    "duration": state.duration,
                    "wait_for": state.wait_for,
                    "has_setup": bool(state.setup),
                    "has_actions": bool(state.actions),
                }

                raw_state = raw_data.get("states", {}).get(state_id, {})
                if "camera" in raw_state:
                    state_data["camera"] = raw_state["camera"]

                states.append(state_data)

            sequences = []
            for seq_id, seq in definition.sequences.items():
                sequences.append({
                    "id": seq_id,
                    "description": seq.description,
                    "states": seq.states,
                    "transition_delay": seq.transition_delay,
                })

            return {
                "id": demo_id,
                "name": definition.name,
                "path": str(demo_file.relative_to(project.root)),
                "url": definition.url,
                "viewport": {
                    "width": definition.viewport_width,
                    "height": definition.viewport_height,
                },
                "states": states,
                "sequences": sequences,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/video/demos/{demo_id}/content")
    async def get_demo_recording_content(demo_id: str, language: str = "en"):
        """Get raw YAML content for a demo recording."""
        project = get_project()

        demo_file = project.content_dir / language / "demos" / f"{demo_id}.yaml"
        if not demo_file.exists():
            for lang in project.languages:
                demo_file = project.content_dir / lang / "demos" / f"{demo_id}.yaml"
                if demo_file.exists():
                    break
            else:
                raise HTTPException(status_code=404, detail=f"Demo '{demo_id}' not found")

        return {
            "id": demo_id,
            "content": demo_file.read_text(),
            "path": str(demo_file.relative_to(project.root)),
        }

    @router.get("/demos/{demo_id}/states/{state_id}.png")
    async def get_demo_state_screenshot(demo_id: str, state_id: str, language: str = "en"):
        """Serve a demo state screenshot.

        Screenshots are stored in:
        - output/{language}/demos/{demo_id}/states/{state_id}.png
        """
        from fastapi.responses import FileResponse

        project = get_project()

        # Look for screenshot in output directory
        screenshot_path = project.output_dir / language / "demos" / demo_id / "states" / f"{state_id}.png"
        if screenshot_path.exists():
            return FileResponse(screenshot_path, media_type="image/png")

        # Try other languages
        for lang in project.languages:
            screenshot_path = project.output_dir / lang / "demos" / demo_id / "states" / f"{state_id}.png"
            if screenshot_path.exists():
                return FileResponse(screenshot_path, media_type="image/png")

        raise HTTPException(status_code=404, detail=f"Screenshot not found: {demo_id}/{state_id}")

    @router.post("/api/video/demos/{demo_id}/capture-screenshots")
    async def capture_demo_screenshots(demo_id: str, language: str = "en", states: Optional[List[str]] = None):
        """Capture screenshots for demo states with camera data.

        Captures high-resolution screenshots of demo states using Playwright.
        Also extracts element bounds for CSS selectors in focus_sequence and
        generates pre-computed keyframes for camera animation.

        If states is not provided, captures all states in the demo.

        Returns the paths to captured screenshots and camera data.
        """
        import json
        import yaml
        from ...video.demo_capture import load_demo_definition, capture_screenshot
        from ...video.camera_capture import CameraConfig, CameraCaptureEngine
        from ...video.camera_path import CameraPathGenerator

        project = get_project()

        # Find the demo definition
        demo_file = project.content_dir / language / "demos" / f"{demo_id}.yaml"
        if not demo_file.exists():
            for lang in project.languages:
                demo_file = project.content_dir / lang / "demos" / f"{demo_id}.yaml"
                if demo_file.exists():
                    language = lang
                    break
            else:
                raise HTTPException(status_code=404, detail=f"Demo '{demo_id}' not found")

        try:
            definition = load_demo_definition(demo_file)
            # Load raw YAML for camera configs
            with open(demo_file, "r") as f:
                raw_data = yaml.safe_load(f)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load demo: {e}")

        # Determine which states to capture
        states_to_capture = states or list(definition.states.keys())
        captured = []
        errors = []

        # Output directory
        output_dir = project.output_dir / language / "demos" / demo_id / "states"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Camera data output directory
        camera_dir = project.output_dir / language / "demos" / demo_id / "camera"
        camera_dir.mkdir(parents=True, exist_ok=True)

        FPS = 30

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={
                        "width": definition.viewport_width,
                        "height": definition.viewport_height,
                    },
                )
                page = await context.new_page()

                # Navigate to the demo URL
                await page.goto(definition.url, wait_until="networkidle")

                # Create camera capture engine
                camera_engine = CameraCaptureEngine(
                    page=page,
                    viewport_width=definition.viewport_width,
                    viewport_height=definition.viewport_height,
                )

                for state_id in states_to_capture:
                    if state_id not in definition.states:
                        errors.append({"state_id": state_id, "error": "State not found"})
                        continue

                    state = definition.states[state_id]
                    output_path = output_dir / f"{state_id}.png"

                    try:
                        # Capture screenshot
                        await capture_screenshot(page, state, output_path)

                        # Get camera config from raw YAML
                        raw_state = raw_data.get("states", {}).get(state_id, {})
                        raw_camera = raw_state.get("camera", {})

                        # Generate camera data if focus_sequence is defined
                        camera_data = None
                        if raw_camera.get("focus_sequence"):
                            camera_config = CameraConfig.from_dict(raw_camera)

                            # Extract element bounds for CSS selectors
                            selectors = camera_config.get_all_selectors()
                            element_bounds = {}
                            if selectors:
                                element_bounds = await camera_engine.get_multiple_element_bounds(selectors)

                            # Generate keyframes
                            duration = state.duration or 2
                            total_frames = int(duration * FPS)

                            path_generator = CameraPathGenerator(
                                viewport_width=definition.viewport_width,
                                viewport_height=definition.viewport_height,
                                capture_scale=camera_config.capture_scale,
                            )

                            camera_data = path_generator.generate_camera_data(
                                camera_config=camera_config,
                                element_bounds=element_bounds,
                                total_frames=total_frames,
                                fps=FPS,
                            )

                            # Save camera data to JSON
                            camera_file = camera_dir / f"{state_id}.json"
                            with open(camera_file, "w") as f:
                                json.dump(camera_data, f, indent=2)

                        captured.append({
                            "state_id": state_id,
                            "path": str(output_path.relative_to(project.root)),
                            "url": f"/demos/{demo_id}/states/{state_id}.png",
                            "has_camera_data": camera_data is not None,
                            "keyframes": len(camera_data.get("keyframes", [])) if camera_data else 0,
                        })
                    except Exception as e:
                        errors.append({"state_id": state_id, "error": str(e)})

                await browser.close()

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {
            "demo_id": demo_id,
            "captured": captured,
            "errors": errors,
            "total_captured": len(captured),
        }

    @router.get("/api/video/demos/{demo_id}/states/{state_id}/camera")
    async def get_demo_state_camera_data(demo_id: str, state_id: str, language: str = "en"):
        """Get pre-computed camera data for a demo state.

        Returns keyframes with resolved pixel coordinates for camera animation.
        """
        import json

        project = get_project()

        # Look for camera data
        camera_file = project.output_dir / language / "demos" / demo_id / "camera" / f"{state_id}.json"
        if not camera_file.exists():
            # Try other languages
            for lang in project.languages:
                camera_file = project.output_dir / lang / "demos" / demo_id / "camera" / f"{state_id}.json"
                if camera_file.exists():
                    break
            else:
                # Return default static camera if no data
                return {
                    "state_id": state_id,
                    "mode": "static",
                    "keyframes": [],
                    "has_data": False,
                }

        try:
            with open(camera_file, "r") as f:
                camera_data = json.load(f)
            return {
                "state_id": state_id,
                "has_data": True,
                **camera_data,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # =========================================================================
    # Video Project Management
    # =========================================================================

    class VideoProjectCreateRequest(BaseModel):
        """Request to create a video project."""
        name: str
        language: str = "en"
        source_documents: list[str] = []

    class VideoProjectUpdateRequest(BaseModel):
        """Request to update a video project."""
        name: Optional[str] = None
        status: Optional[str] = None
        metadata: Optional[Dict] = None

    class VideoCommentCreateRequest(BaseModel):
        """Request to add a review comment."""
        component_id: str
        text: str
        author: str = "user"
        timestamp: Optional[float] = None
        frame: Optional[int] = None
        priority: str = "normal"

    class VideoCommentResolveRequest(BaseModel):
        """Request to resolve a review comment."""
        resolution: str
        resolved_by: str = "user"

    @router.get("/api/video/projects")
    async def list_video_projects(status: Optional[str] = None):
        """List all video projects."""
        from ...video.project import VideoProjectRegistry, ProjectStatus

        project = get_project()
        registry = VideoProjectRegistry(project)

        status_filter = None
        if status:
            try:
                status_filter = ProjectStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        projects = registry.list(status=status_filter)

        return {
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "language": p.language,
                    "status": p.status.value,
                    "components_count": len(p.components),
                    "progress": p.progress,
                    "created_at": p.created_at.isoformat(),
                    "modified_at": p.modified_at.isoformat(),
                }
                for p in projects
            ],
            "count": len(projects),
        }

    @router.post("/api/video/projects")
    async def create_video_project(request: VideoProjectCreateRequest):
        """Create a new video project."""
        from ...video.project import VideoProjectRegistry

        project = get_project()
        registry = VideoProjectRegistry(project)

        # Convert source document paths
        source_docs = [Path(p) for p in request.source_documents]

        video_project = registry.create(
            name=request.name,
            language=request.language,
            source_documents=source_docs,
        )

        await manager.broadcast({
            "type": "video_project_created",
            "project_id": video_project.id,
            "name": video_project.name,
        })

        return {
            "id": video_project.id,
            "name": video_project.name,
            "status": video_project.status.value,
            "created_at": video_project.created_at.isoformat(),
        }

    @router.get("/api/video/projects/{project_id}")
    async def get_video_project(project_id: str):
        """Get a video project by ID."""
        from ...video.project import VideoProjectRegistry

        project = get_project()
        registry = VideoProjectRegistry(project)

        video_project = registry.get(project_id)
        if not video_project:
            raise HTTPException(status_code=404, detail="Video project not found")

        return {
            "id": video_project.id,
            "name": video_project.name,
            "language": video_project.language,
            "status": video_project.status.value,
            "script_path": str(video_project.script_path) if video_project.script_path else None,
            "demo_definition_path": str(video_project.demo_definition_path) if video_project.demo_definition_path else None,
            "source_documents": [str(p) for p in video_project.source_documents],
            "components": {
                k: {
                    "id": v.id,
                    "type": v.type.value,
                    "path": str(v.path),
                    "status": v.status.value,
                    "scene_id": v.scene_id,
                    "depends_on": v.depends_on,
                    "generated_at": v.generated_at.isoformat() if v.generated_at else None,
                    "generated_by": v.generated_by,
                    "error_message": v.error_message,
                }
                for k, v in video_project.components.items()
            },
            "progress": video_project.progress,
            "is_complete": video_project.is_complete,
            "created_at": video_project.created_at.isoformat(),
            "modified_at": video_project.modified_at.isoformat(),
            "metadata": video_project.metadata,
        }

    @router.put("/api/video/projects/{project_id}")
    async def update_video_project(project_id: str, request: VideoProjectUpdateRequest):
        """Update a video project."""
        from ...video.project import VideoProjectRegistry, ProjectStatus

        project = get_project()
        registry = VideoProjectRegistry(project)

        video_project = registry.get(project_id)
        if not video_project:
            raise HTTPException(status_code=404, detail="Video project not found")

        if request.name is not None:
            video_project.name = request.name
        if request.status is not None:
            try:
                video_project.status = ProjectStatus(request.status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        if request.metadata is not None:
            video_project.metadata.update(request.metadata)

        registry.update(video_project)

        await manager.broadcast({
            "type": "video_project_updated",
            "project_id": video_project.id,
        })

        return {"status": "ok", "message": "Project updated"}

    @router.delete("/api/video/projects/{project_id}")
    async def delete_video_project(project_id: str):
        """Delete a video project."""
        from ...video.project import VideoProjectRegistry

        project = get_project()
        registry = VideoProjectRegistry(project)

        if not registry.delete(project_id):
            raise HTTPException(status_code=404, detail="Video project not found")

        await manager.broadcast({
            "type": "video_project_deleted",
            "project_id": project_id,
        })

        return {"status": "ok", "message": "Project deleted"}

    @router.get("/api/video/projects/{project_id}/components")
    async def get_video_project_components(project_id: str):
        """Get all components for a video project."""
        from ...video.project import VideoProjectRegistry

        project = get_project()
        registry = VideoProjectRegistry(project)

        video_project = registry.get(project_id)
        if not video_project:
            raise HTTPException(status_code=404, detail="Video project not found")

        # Group components by type
        by_type = {}
        for comp in video_project.components.values():
            type_key = comp.type.value
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append({
                "id": comp.id,
                "path": str(comp.path),
                "status": comp.status.value,
                "scene_id": comp.scene_id,
                "depends_on": comp.depends_on,
                "generated_at": comp.generated_at.isoformat() if comp.generated_at else None,
                "generated_by": comp.generated_by,
                "error_message": comp.error_message,
            })

        return {
            "project_id": project_id,
            "by_type": by_type,
            "total": len(video_project.components),
            "ready": len(video_project.get_ready_components()),
            "stale": len(video_project.get_stale_components()),
            "pending": len(video_project.get_pending_components()),
        }

    @router.get("/api/video/projects/{project_id}/dependencies")
    async def get_video_project_dependencies(project_id: str):
        """Get the dependency graph for a video project."""
        from ...video.project import VideoProjectRegistry, COMPONENT_DEPENDENCIES

        project = get_project()
        registry = VideoProjectRegistry(project)

        video_project = registry.get(project_id)
        if not video_project:
            raise HTTPException(status_code=404, detail="Video project not found")

        # Build nodes and edges
        nodes = []
        edges = []

        for comp in video_project.components.values():
            nodes.append({
                "id": comp.id,
                "type": comp.type.value,
                "status": comp.status.value,
                "scene_id": comp.scene_id,
            })
            for dep_id in comp.depends_on:
                edges.append({
                    "from": dep_id,
                    "to": comp.id,
                })

        return {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "type_dependencies": {
                k.value: [v.value for v in deps]
                for k, deps in COMPONENT_DEPENDENCIES.items()
            },
        }

    @router.post("/api/video/projects/{project_id}/components/{component_id}/regenerate")
    async def regenerate_video_component(project_id: str, component_id: str, cascade: bool = True):
        """Mark a component for regeneration (and optionally cascade to dependents)."""
        from ...video.project import VideoProjectRegistry

        project = get_project()
        registry = VideoProjectRegistry(project)

        video_project = registry.get(project_id)
        if not video_project:
            raise HTTPException(status_code=404, detail="Video project not found")

        if component_id not in video_project.components:
            raise HTTPException(status_code=404, detail="Component not found")

        if cascade:
            affected = video_project.mark_component_stale(component_id)
        else:
            video_project.components[component_id].mark_stale()
            affected = [component_id]

        registry.update(video_project)

        await manager.broadcast({
            "type": "video_components_stale",
            "project_id": project_id,
            "affected": affected,
        })

        return {
            "status": "ok",
            "affected_components": affected,
        }

    # =========================================================================
    # Video Review Comments
    # =========================================================================

    @router.get("/api/video/projects/{project_id}/comments")
    async def list_video_comments(
        project_id: str,
        status: Optional[str] = None,
        include_resolved: bool = False,
    ):
        """List review comments for a video project."""
        from ...video.review import VideoReviewStore, CommentStatus

        project = get_project()
        store = VideoReviewStore(project)

        status_filter = None
        if status:
            try:
                status_filter = CommentStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        comments = store.get_comments_for_project(
            project_id,
            status=status_filter,
            include_resolved=include_resolved,
        )

        return {
            "comments": [c.to_dict() for c in comments],
            "count": len(comments),
            "stats": store.get_stats(project_id),
        }

    @router.post("/api/video/projects/{project_id}/comments")
    async def add_video_comment(project_id: str, request: VideoCommentCreateRequest):
        """Add a review comment to a video project component."""
        from ...video.review import VideoReviewStore, CommentPriority
        from ...video.project import VideoProjectRegistry

        project = get_project()

        # Verify project exists
        registry = VideoProjectRegistry(project)
        video_project = registry.get(project_id)
        if not video_project:
            raise HTTPException(status_code=404, detail="Video project not found")

        # Verify component exists
        if request.component_id not in video_project.components:
            raise HTTPException(status_code=404, detail="Component not found")

        # Parse priority
        try:
            priority = CommentPriority(request.priority)
        except ValueError:
            priority = CommentPriority.NORMAL

        store = VideoReviewStore(project)
        comment = store.add_comment(
            project_id=project_id,
            component_id=request.component_id,
            text=request.text,
            author=request.author,
            timestamp=request.timestamp,
            frame=request.frame,
            priority=priority,
        )

        await manager.broadcast({
            "type": "video_comment_added",
            "project_id": project_id,
            "comment_id": comment.id,
            "component_id": request.component_id,
        })

        return {
            "id": comment.id,
            "status": comment.status.value,
            "created_at": comment.created_at.isoformat(),
        }

    @router.get("/api/video/projects/{project_id}/comments/{comment_id}")
    async def get_video_comment(project_id: str, comment_id: str):
        """Get a specific review comment."""
        from ...video.review import VideoReviewStore

        project = get_project()
        store = VideoReviewStore(project)

        comment = store.get_comment(comment_id)
        if not comment or comment.project_id != project_id:
            raise HTTPException(status_code=404, detail="Comment not found")

        return comment.to_dict()

    @router.delete("/api/video/projects/{project_id}/comments/{comment_id}")
    async def delete_video_comment(project_id: str, comment_id: str):
        """Delete a review comment."""
        from ...video.review import VideoReviewStore

        project = get_project()
        store = VideoReviewStore(project)

        comment = store.get_comment(comment_id)
        if not comment or comment.project_id != project_id:
            raise HTTPException(status_code=404, detail="Comment not found")

        if not store.delete_comment(comment_id):
            raise HTTPException(status_code=500, detail="Failed to delete comment")

        await manager.broadcast({
            "type": "video_comment_deleted",
            "project_id": project_id,
            "comment_id": comment_id,
        })

        return {"status": "ok", "message": "Comment deleted"}

    @router.post("/api/video/projects/{project_id}/comments/{comment_id}/queue")
    async def queue_video_comment_for_ai(project_id: str, comment_id: str):
        """Queue a review comment for AI processing."""
        from ...video.review import VideoReviewStore

        project = get_project()
        store = VideoReviewStore(project)

        comment = store.get_comment(comment_id)
        if not comment or comment.project_id != project_id:
            raise HTTPException(status_code=404, detail="Comment not found")

        if not comment.is_actionable:
            raise HTTPException(status_code=400, detail="Comment is not actionable")

        task_id = store.queue_for_ai(comment_id)
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to queue comment")

        await manager.broadcast({
            "type": "video_comment_queued",
            "project_id": project_id,
            "comment_id": comment_id,
            "task_id": task_id,
        })

        return {
            "status": "queued",
            "task_id": task_id,
        }

    @router.post("/api/video/projects/{project_id}/comments/{comment_id}/resolve")
    async def resolve_video_comment(
        project_id: str,
        comment_id: str,
        request: VideoCommentResolveRequest,
    ):
        """Resolve a review comment."""
        from ...video.review import VideoReviewStore

        project = get_project()
        store = VideoReviewStore(project)

        comment = store.get_comment(comment_id)
        if not comment or comment.project_id != project_id:
            raise HTTPException(status_code=404, detail="Comment not found")

        resolved_comment = store.resolve_comment(
            comment_id=comment_id,
            resolution=request.resolution,
            resolved_by=request.resolved_by,
        )

        if not resolved_comment:
            raise HTTPException(status_code=500, detail="Failed to resolve comment")

        await manager.broadcast({
            "type": "video_comment_resolved",
            "project_id": project_id,
            "comment_id": comment_id,
            "resolution": request.resolution,
        })

        return {
            "status": "resolved",
            "resolved_at": resolved_comment.resolved_at.isoformat() if resolved_comment.resolved_at else None,
        }

    @router.get("/api/video/comments/pending")
    async def list_pending_video_comments():
        """List all pending comments across all projects."""
        from ...video.review import VideoReviewStore

        project = get_project()
        store = VideoReviewStore(project)

        comments = store.get_pending_comments()

        return {
            "comments": [c.to_dict() for c in comments],
            "count": len(comments),
        }


def _get_effect_preset_description(preset_id: str) -> str:
    """Get description for an effects preset."""
    descriptions = {
        "cinematic": "Vignette + Dynamic Tilt for feature showcases",
        "documentary": "Light Shake + Subtle Vignette for authentic feel",
        "professional": "Light Vignette only for clean corporate content",
        "dramatic": "Tilt + Strong Vignette + DoF for impactful reveals",
        "tech_demo": "Vignette + Light DoF for software demonstrations",
        "minimal": "No effects for raw footage and tutorials",
        "immersive": "All effects (subtle) for immersive experiences",
    }
    return descriptions.get(preset_id, "Custom effects configuration")


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

        # Generate voiceover and build video
        from ...video.builder import VideoBuilder, VideoConfig
        from ...video.quality import VideoQuality

        # Convert quality string to enum
        quality_enum = VideoQuality.PRODUCTION
        if request.quality == "preview":
            quality_enum = VideoQuality.PREVIEW

        # Create config and builder
        config = VideoConfig.from_quality(quality_enum)
        builder = VideoBuilder(project, config=config)

        # Update progress through stages
        job["progress"] = 10
        await manager.broadcast({"type": "render_progress", "job_id": job_id, "progress": 10, "stage": "voiceover"})

        # Build video
        job["stage"] = "rendering_video"
        job["progress"] = 30
        await manager.broadcast(
            {"type": "render_progress", "job_id": job_id, "progress": 30, "stage": "rendering_video"}
        )

        # Find remotion project directory
        remotion_dir = project.root / "remotion"
        if not remotion_dir.exists():
            remotion_dir = project.root.parent / "remotion"

        # Call the builder's build method
        # TODO: Add UI toggle for mock_voiceover - using mock for now to avoid API costs
        result = await builder.build(
            script_path=script_path,
            render=True,
            remotion_project=remotion_dir if remotion_dir.exists() else None,
            mock_voiceover=True,  # Use silent audio with estimated timing
        )

        if not result.success:
            raise Exception(result.error or "Video build failed")

        output_path = result.video_path

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


async def _run_voiceover_generation(
    job_id: str,
    project: "Project",
    script_path: Path,
    audio_path: Path,
    mode: str,
    manager: "ConnectionManager",
):
    """Run voiceover generation in background."""
    import yaml

    try:
        await manager.broadcast({
            "type": "voiceover_progress",
            "job_id": job_id,
            "progress": 10,
            "stage": "parsing_script",
        })

        # Parse script to get voiceover texts
        with open(script_path, "r") as f:
            script = yaml.safe_load(f)

        # Extract text segments from scenes
        texts = []
        for scene in script.get("scenes", []):
            scene_id = scene.get("id", f"scene_{len(texts)}")
            text = scene.get("voiceover") or scene.get("content", {}).get("text")
            if text:
                texts.append((scene_id, text))

        if not texts:
            raise Exception("No voiceover text found in script scenes")

        await manager.broadcast({
            "type": "voiceover_progress",
            "job_id": job_id,
            "progress": 20,
            "stage": "generating_audio",
            "total_scenes": len(texts),
        })

        # Generate based on mode
        from ...video.voiceover import (
            generate_voiceover,
            generate_voiceover_mock,
            generate_voiceover_macos,
        )

        if mode == "mock":
            result = await generate_voiceover_mock(texts, audio_path)
        elif mode == "macos":
            result = await generate_voiceover_macos(texts, audio_path)
        else:
            # ElevenLabs - get voice_id from config
            lang_config = project.languages.get(project.source_language)
            voice_id = lang_config.voice_id if lang_config else project.config.voiceover.voice_id
            if not voice_id:
                raise Exception("No voice_id configured for ElevenLabs")

            result = await generate_voiceover(
                texts=texts,
                output_path=audio_path,
                voice_id=voice_id,
                cache_dir=project.cache_dir / "voiceover",
                language=project.source_language,
            )

        await manager.broadcast({
            "type": "voiceover_progress",
            "job_id": job_id,
            "progress": 80,
            "stage": "generating_props",
        })

        # Generate props.json
        from ...video.builder import VideoBuilder

        builder = VideoBuilder(project)
        props = builder.generate_props(script_path)

        # Save props
        props_path = audio_path.with_suffix(".props.json")
        import json
        with open(props_path, "w") as f:
            json.dump(props, f, indent=2)

        await manager.broadcast({
            "type": "voiceover_complete",
            "job_id": job_id,
            "audio_path": str(audio_path.relative_to(project.root)),
            "props_path": str(props_path.relative_to(project.root)),
            "duration": result.total_duration,
            "scenes": len(result.segments),
        })

    except Exception as e:
        await manager.broadcast({
            "type": "voiceover_failed",
            "job_id": job_id,
            "error": str(e),
        })


def _start_remotion_studio(remotion_dir: Path, port: int = 3001):
    """Start Remotion Studio server in background."""
    import subprocess
    import os

    try:
        subprocess.Popen(
            ["npx", "remotion", "studio", "--port", str(port)],
            cwd=str(remotion_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "BROWSER": "none"},  # Don't auto-open browser
        )
    except Exception as e:
        print(f"Failed to start Remotion Studio: {e}")
