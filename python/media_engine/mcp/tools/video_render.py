"""Video Render MCP tools.

Render management tools for video production:
- Start/cancel render jobs
- Monitor render progress
- Manage render queue
- Export deliverables
"""

import json
import uuid
from datetime import datetime
from typing import Dict

# Global render state (shared with web routes when possible)
_render_jobs: Dict[str, Dict] = {}


def register_video_render_tools(mcp, server_instance):
    """Register video render MCP tools."""

    @mcp.tool()
    async def start_video_render(
        script_id: str,
        quality: str = "production",
        output_format: str = "mp4",
    ) -> str:
        """
        Queue a video render job.

        Args:
            script_id: Script identifier (e.g., "en/intro")
            quality: Render quality ("preview" for 720p fast, "production" for 1080p high quality)
            output_format: Output format (mp4, webm)

        Returns:
            JSON with job ID and status
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        # Parse script_id
        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format. Use 'language/script_name'"}, indent=2)

        lang, name = parts
        script_path = server_instance.project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            return json.dumps({"error": f"Script not found: {script_id}"}, indent=2)

        # Create job
        job_id = str(uuid.uuid4())[:8]
        job = {
            "id": job_id,
            "script_id": script_id,
            "script_path": str(script_path),
            "quality": quality,
            "output_format": output_format,
            "status": "queued",
            "progress": 0,
            "stage": "queued",
            "created": datetime.now().isoformat(),
            "started": None,
            "completed": None,
            "error": None,
            "output_path": None,
        }

        _render_jobs[job_id] = job

        return json.dumps({
            "status": "queued",
            "job_id": job_id,
            "script_id": script_id,
            "quality": quality,
            "message": f"Render job {job_id} queued. Use get_render_status to monitor progress.",
        }, indent=2)

    @mcp.tool()
    async def get_render_status(job_id: str) -> str:
        """
        Check the status of a render job.

        Args:
            job_id: The render job ID

        Returns:
            JSON with current job status and progress
        """
        if job_id not in _render_jobs:
            return json.dumps({"error": f"Job not found: {job_id}"}, indent=2)

        job = _render_jobs[job_id]

        return json.dumps({
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "stage": job["stage"],
            "script_id": job["script_id"],
            "quality": job["quality"],
            "created": job["created"],
            "started": job["started"],
            "completed": job["completed"],
            "output_path": job["output_path"],
            "error": job["error"],
        }, indent=2)

    @mcp.tool()
    async def cancel_render(job_id: str) -> str:
        """
        Cancel an active render job.

        Args:
            job_id: The render job ID to cancel

        Returns:
            JSON with cancellation status
        """
        if job_id not in _render_jobs:
            return json.dumps({"error": f"Job not found: {job_id}"}, indent=2)

        job = _render_jobs[job_id]

        if job["status"] in ["completed", "failed", "cancelled"]:
            return json.dumps({
                "error": f"Cannot cancel job in '{job['status']}' state",
                "job_id": job_id,
            }, indent=2)

        job["status"] = "cancelled"
        job["completed"] = datetime.now().isoformat()

        return json.dumps({
            "status": "cancelled",
            "job_id": job_id,
            "message": "Render job cancelled",
        }, indent=2)

    @mcp.tool()
    async def list_render_queue() -> str:
        """
        Get all render jobs and their statuses.

        Returns:
            JSON with list of all render jobs
        """
        jobs = list(_render_jobs.values())

        # Sort by created time, most recent first
        jobs.sort(key=lambda x: x.get("created", ""), reverse=True)

        # Calculate stats
        stats = {
            "total": len(jobs),
            "queued": sum(1 for j in jobs if j["status"] == "queued"),
            "rendering": sum(1 for j in jobs if j["status"] == "rendering"),
            "completed": sum(1 for j in jobs if j["status"] == "completed"),
            "failed": sum(1 for j in jobs if j["status"] == "failed"),
            "cancelled": sum(1 for j in jobs if j["status"] == "cancelled"),
        }

        return json.dumps({
            "jobs": jobs,
            "stats": stats,
        }, indent=2)

    @mcp.tool()
    async def clear_completed_jobs() -> str:
        """
        Remove completed and cancelled jobs from the queue.

        Returns:
            JSON with number of jobs cleared
        """
        global _render_jobs

        to_remove = [
            job_id for job_id, job in _render_jobs.items()
            if job["status"] in ["completed", "cancelled", "failed"]
        ]

        for job_id in to_remove:
            del _render_jobs[job_id]

        return json.dumps({
            "status": "cleared",
            "jobs_removed": len(to_remove),
            "remaining_jobs": len(_render_jobs),
        }, indent=2)

    @mcp.tool()
    async def export_video_assets(
        script_id: str,
        include_source: bool = False,
        include_audio: bool = True,
    ) -> str:
        """
        Package video deliverables for export.

        Args:
            script_id: Script identifier to export assets for
            include_source: Include source YAML script
            include_audio: Include generated voiceover audio

        Returns:
            JSON with list of export assets and their locations
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format"}, indent=2)

        lang, name = parts
        assets = []

        # Check for rendered video
        video_path = server_instance.project.output_dir / lang / "videos" / f"{name}.mp4"
        if video_path.exists():
            assets.append({
                "type": "video",
                "format": "mp4",
                "path": str(video_path),
                "size": video_path.stat().st_size,
                "modified": datetime.fromtimestamp(video_path.stat().st_mtime).isoformat(),
            })

        # Check for WebM version
        webm_path = video_path.with_suffix(".webm")
        if webm_path.exists():
            assets.append({
                "type": "video",
                "format": "webm",
                "path": str(webm_path),
                "size": webm_path.stat().st_size,
            })

        # Check for audio
        if include_audio:
            audio_path = server_instance.project.output_dir / lang / "videos" / f"{name}.mp3"
            if audio_path.exists():
                assets.append({
                    "type": "audio",
                    "format": "mp3",
                    "path": str(audio_path),
                    "size": audio_path.stat().st_size,
                })

        # Check for source script
        if include_source:
            script_path = server_instance.project.content_dir / lang / "scripts" / f"{name}.yaml"
            if script_path.exists():
                assets.append({
                    "type": "source",
                    "format": "yaml",
                    "path": str(script_path),
                    "size": script_path.stat().st_size,
                })

        if not assets:
            return json.dumps({
                "error": "No assets found for this script",
                "script_id": script_id,
            }, indent=2)

        total_size = sum(a["size"] for a in assets)

        return json.dumps({
            "script_id": script_id,
            "assets": assets,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "asset_count": len(assets),
        }, indent=2)

    @mcp.tool()
    async def get_render_settings(quality: str = "production") -> str:
        """
        Get render settings for a quality preset.

        Args:
            quality: Quality preset (preview, production, 4k)

        Returns:
            JSON with render settings
        """
        presets = {
            "preview": {
                "width": 1280,
                "height": 720,
                "fps": 30,
                "codec": "h264",
                "crf": 28,
                "description": "Fast preview, lower quality",
                "estimated_time_multiplier": 0.5,
            },
            "production": {
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "codec": "h264",
                "crf": 18,
                "description": "High quality for distribution",
                "estimated_time_multiplier": 1.0,
            },
            "4k": {
                "width": 3840,
                "height": 2160,
                "fps": 30,
                "codec": "h264",
                "crf": 15,
                "description": "Ultra high quality",
                "estimated_time_multiplier": 3.0,
            },
        }

        if quality not in presets:
            return json.dumps({
                "error": f"Unknown quality preset: {quality}",
                "available_presets": list(presets.keys()),
            }, indent=2)

        return json.dumps({
            "quality": quality,
            "settings": presets[quality],
            "available_presets": list(presets.keys()),
        }, indent=2)

    @mcp.tool()
    async def estimate_render_time(script_id: str, quality: str = "production") -> str:
        """
        Estimate render time for a video script.

        Args:
            script_id: Script identifier
            quality: Quality preset

        Returns:
            JSON with estimated render time
        """
        import yaml

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format"}, indent=2)

        lang, name = parts
        script_path = server_instance.project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            return json.dumps({"error": f"Script not found: {script_id}"}, indent=2)

        with open(script_path) as f:
            script = yaml.safe_load(f)

        scenes = script.get("scenes", [])
        total_duration = sum(s.get("duration", 5) for s in scenes)
        fps = script.get("settings", {}).get("fps", 30)
        total_frames = total_duration * fps

        # Quality multipliers
        quality_multipliers = {
            "preview": 0.5,
            "production": 1.0,
            "4k": 3.0,
        }
        multiplier = quality_multipliers.get(quality, 1.0)

        # Estimate based on frames (rough: 1 frame per 0.1 seconds for production)
        base_render_seconds = total_frames * 0.1
        estimated_seconds = base_render_seconds * multiplier

        # Add voiceover generation time (rough: 10 seconds per scene with voiceover)
        scenes_with_vo = sum(1 for s in scenes if s.get("voiceover"))
        vo_time = scenes_with_vo * 10

        total_estimated = estimated_seconds + vo_time

        return json.dumps({
            "script_id": script_id,
            "quality": quality,
            "video_duration": total_duration,
            "total_frames": total_frames,
            "scenes_with_voiceover": scenes_with_vo,
            "estimated_render_time": {
                "seconds": round(total_estimated),
                "minutes": round(total_estimated / 60, 1),
                "formatted": f"{int(total_estimated // 60)}m {int(total_estimated % 60)}s",
            },
            "breakdown": {
                "frame_rendering": round(estimated_seconds),
                "voiceover_generation": round(vo_time),
            },
            "note": "Estimates may vary based on scene complexity and system resources",
        }, indent=2)
