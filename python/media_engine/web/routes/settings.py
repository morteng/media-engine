"""
Settings API Routes

Provides unified settings management for the dashboard.
Supports reading defaults, project config, and environment variables.
Allows safe editing of project.yaml with validation and backup.
"""

import shutil
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict

import yaml

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


# Setting descriptions for UI display
SETTING_DESCRIPTIONS = {
    # Project
    "name": "Project display name",
    "description": "Project description",
    "source_language": "Primary content language",
    # Video
    "width": "Video width in pixels",
    "height": "Video height in pixels",
    "fps": "Frames per second",
    "codec": "Video codec (h264, h265)",
    "ffmpeg_preset": "Encoding speed vs quality tradeoff",
    "ffmpeg_crf": "Quality level (lower = better, 18 is visually lossless)",
    # Voiceover
    "provider": "Text-to-speech provider",
    "model": "TTS model to use",
    "stability": "Voice stability (0-1)",
    "similarity_boost": "Voice similarity boost (0-1)",
    # Quality
    "target_reading_level": "Target reading comprehension level (elementary, middle_school, high_school, college, graduate)",
    "target_lix_level": "Target Norwegian readability level (very_easy, easy, medium, difficult, very_difficult)",
    "freshness_default_days": "Days before content is considered stale",
    "freshness_warning_days": "Days before stale warning",
    "freshness_critical_days": "Days before critical staleness",
    "max_sentence_words": "Maximum words per sentence for readability",
    # Web
    "host": "Dashboard server host",
    "port": "Dashboard server port",
    "auto_open_browser": "Open browser automatically on launch",
}


def _get_setting_description(key: str) -> str:
    """Get description for a setting key."""
    return SETTING_DESCRIPTIONS.get(key, f"Configuration for {key}")


def _dataclass_to_dict_with_meta(obj: Any, category: str) -> Dict[str, Any]:
    """Convert a frozen dataclass to dict with metadata for each field."""
    result = {}
    for field in fields(obj):
        value = getattr(obj, field.name)
        # Convert frozenset to list for JSON serialization
        if isinstance(value, frozenset):
            value = list(value)
        elif isinstance(value, tuple):
            value = list(value)

        result[field.name] = {
            "value": value,
            "source": "default",
            "default": value,
            "editable": False,  # Defaults are not editable
            "description": _get_setting_description(field.name),
            "category": category,
            "type": field.type.__name__ if hasattr(field.type, "__name__") else str(field.type),
        }
    return result


def register_settings_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register settings-related routes."""
    from fastapi import Body, HTTPException

    from ...settings import (
        CACHE,
        CLI,
        NETWORK,
        QUALITY,
        VIDEO,
        VOICEOVER,
        WEB,
    )
    from ...settings.env import get_env_summary

    @router.get("/api/settings")
    async def get_all_settings() -> Dict[str, Any]:
        """
        Get all settings with source annotations.

        Returns settings from all sources (defaults, project.yaml, env)
        with metadata indicating where each value comes from.
        """
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        # Build unified settings response
        settings = {
            "project": _get_project_settings(project),
            "video": _get_video_settings(project),
            "voiceover": _get_voiceover_settings(project),
            "quality": _get_quality_settings(project),
            "paths": _get_paths_settings(project),
            "environment": _get_env_settings(),
        }

        return settings

    @router.get("/api/settings/defaults")
    async def get_defaults() -> Dict[str, Any]:
        """Get all frozen default values."""
        return {
            "video": _dataclass_to_dict_with_meta(VIDEO, "video"),
            "voiceover": _dataclass_to_dict_with_meta(VOICEOVER, "voiceover"),
            "quality": _dataclass_to_dict_with_meta(QUALITY, "quality"),
            "web": _dataclass_to_dict_with_meta(WEB, "web"),
            "network": _dataclass_to_dict_with_meta(NETWORK, "network"),
            "cache": _dataclass_to_dict_with_meta(CACHE, "cache"),
            "cli": _dataclass_to_dict_with_meta(CLI, "cli"),
        }

    @router.get("/api/settings/project")
    async def get_project_settings_only() -> Dict[str, Any]:
        """Get only project.yaml settings."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        project_yaml = project.root / "project.yaml"
        if not project_yaml.exists():
            return {"error": "project.yaml not found"}

        with open(project_yaml) as f:
            raw_config = yaml.safe_load(f) or {}

        return {
            "path": str(project_yaml),
            "config": raw_config,
            "last_modified": datetime.fromtimestamp(
                project_yaml.stat().st_mtime
            ).isoformat(),
        }

    @router.get("/api/settings/env")
    async def get_env_settings_only() -> Dict[str, Any]:
        """Get environment variables status (values redacted for sensitive vars)."""
        return get_env_summary(include_sensitive=False)

    @router.put("/api/settings/project")
    async def update_project_settings(
        section: str = Body(..., embed=True),
        updates: Dict[str, Any] = Body(..., embed=True),
    ) -> Dict[str, Any]:
        """
        Update a section of project.yaml.

        Creates a backup before modifying and validates the changes.
        """
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        project_yaml = project.root / "project.yaml"
        if not project_yaml.exists():
            raise HTTPException(status_code=404, detail="project.yaml not found")

        # Validate section
        valid_sections = ["project", "video", "voiceover", "quality", "paths", "localization"]
        if section not in valid_sections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section '{section}'. Must be one of: {valid_sections}",
            )

        try:
            # Load current config
            with open(project_yaml) as f:
                config = yaml.safe_load(f) or {}

            # Create backup
            backup_path = project.root / ".project.yaml.bak"
            shutil.copy2(project_yaml, backup_path)

            # Update section
            if section not in config:
                config[section] = {}

            # Special handling for paths section with desktop_deliverables
            if section == "paths" and "desktop_deliverables" in updates:
                desktop_enabled = updates.pop("desktop_deliverables")
                if desktop_enabled:
                    # Set publish path to Desktop folder
                    project_name = config.get("project", {}).get("name", "media-engine")
                    desktop_path = str(Path.home() / "Desktop" / project_name)
                    config["paths"]["publish"] = desktop_path
                else:
                    # Remove publish path to use default
                    config["paths"].pop("publish", None)

            # Merge updates into section
            for key, value in updates.items():
                config[section][key] = value

            # Write updated config
            with open(project_yaml, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

            # Reload project config to pick up changes
            project.reload_config()

            # Broadcast change
            await manager.broadcast({
                "type": "settings_changed",
                "section": section,
                "changes": updates,
                "timestamp": datetime.now().isoformat(),
                "refresh": ["settings", "project"],
            })

            return {
                "status": "success",
                "section": section,
                "updated_fields": list(updates.keys()),
                "backup_path": str(backup_path),
                "requires_reload": section in ["localization", "paths"],
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update settings: {e}")

    @router.post("/api/settings/validate")
    async def validate_settings(
        section: str = Body(..., embed=True),
        updates: Dict[str, Any] = Body(..., embed=True),
    ) -> Dict[str, Any]:
        """Validate proposed settings changes without applying them."""
        errors = {}

        # Type validation
        if section == "video":
            if "width" in updates and not isinstance(updates["width"], int):
                errors["width"] = "Must be an integer"
            if "height" in updates and not isinstance(updates["height"], int):
                errors["height"] = "Must be an integer"
            if "fps" in updates:
                if not isinstance(updates["fps"], int) or updates["fps"] not in [24, 30, 60]:
                    errors["fps"] = "Must be 24, 30, or 60"

        if section == "voiceover":
            if "stability" in updates:
                val = updates["stability"]
                if not isinstance(val, (int, float)) or not 0 <= val <= 1:
                    errors["stability"] = "Must be a number between 0 and 1"
            if "similarity_boost" in updates:
                val = updates["similarity_boost"]
                if not isinstance(val, (int, float)) or not 0 <= val <= 1:
                    errors["similarity_boost"] = "Must be a number between 0 and 1"

        if section == "quality":
            valid_reading_levels = ["elementary", "middle_school", "high_school", "college", "graduate"]
            valid_lix_levels = ["very_easy", "easy", "medium", "difficult", "very_difficult"]

            if "target_reading_level" in updates:
                val = updates["target_reading_level"]
                if not isinstance(val, str) or val not in valid_reading_levels:
                    errors["target_reading_level"] = f"Must be one of: {', '.join(valid_reading_levels)}"

            if "target_lix_level" in updates:
                val = updates["target_lix_level"]
                if not isinstance(val, str) or val not in valid_lix_levels:
                    errors["target_lix_level"] = f"Must be one of: {', '.join(valid_lix_levels)}"

            if "max_sentence_words" in updates:
                val = updates["max_sentence_words"]
                if not isinstance(val, int) or val < 5 or val > 100:
                    errors["max_sentence_words"] = "Must be between 5 and 100 words"

            if "freshness_default_days" in updates:
                val = updates["freshness_default_days"]
                if not isinstance(val, int) or val < 1 or val > 365:
                    errors["freshness_default_days"] = "Must be between 1 and 365 days"

        if section == "project":
            if "name" in updates:
                val = updates["name"]
                if not isinstance(val, str) or len(val) < 1 or len(val) > 100:
                    errors["name"] = "Must be 1-100 characters"

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def _get_project_settings(project: "Project") -> Dict[str, Any]:
        """Get project-level settings with source tracking."""
        return {
            "name": {
                "value": project.config.name,
                "source": "project",
                "default": "Untitled Project",
                "editable": True,
                "description": "Project display name",
                "category": "project",
            },
            "description": {
                "value": project.config.description or "",
                "source": "project" if project.config.description else "default",
                "default": "",
                "editable": True,
                "description": "Project description",
                "category": "project",
            },
            "source_language": {
                "value": project.source_language,
                "source": "project",
                "default": "en",
                "editable": False,  # Changing this is complex
                "description": "Primary content language",
                "category": "project",
            },
            "languages": {
                "value": list(project.languages.keys()),
                "source": "project",
                "default": ["en"],
                "editable": False,
                "description": "Configured languages",
                "category": "project",
            },
        }

    def _get_video_settings(project: "Project") -> Dict[str, Any]:
        """Get video settings with source tracking."""
        config = project.config.video
        return {
            "width": {
                "value": config.width,
                "source": "project" if config.width != VIDEO.width else "default",
                "default": VIDEO.width,
                "editable": True,
                "description": "Video width in pixels",
                "category": "video",
            },
            "height": {
                "value": config.height,
                "source": "project" if config.height != VIDEO.height else "default",
                "default": VIDEO.height,
                "editable": True,
                "description": "Video height in pixels",
                "category": "video",
            },
            "fps": {
                "value": config.fps,
                "source": "project" if config.fps != VIDEO.fps else "default",
                "default": VIDEO.fps,
                "editable": True,
                "description": "Frames per second",
                "category": "video",
            },
        }

    def _get_voiceover_settings(project: "Project") -> Dict[str, Any]:
        """Get voiceover settings with source tracking."""
        config = project.config.voiceover
        return {
            "provider": {
                "value": config.provider,
                "source": "project" if config.provider != VOICEOVER.provider else "default",
                "default": VOICEOVER.provider,
                "editable": True,
                "description": "Text-to-speech provider",
                "category": "voiceover",
            },
            "stability": {
                "value": config.stability,
                "source": "project" if config.stability != VOICEOVER.stability else "default",
                "default": VOICEOVER.stability,
                "editable": True,
                "description": "Voice stability (0-1)",
                "category": "voiceover",
            },
            "similarity_boost": {
                "value": config.similarity_boost,
                "source": "project" if config.similarity_boost != VOICEOVER.similarity_boost else "default",
                "default": VOICEOVER.similarity_boost,
                "editable": True,
                "description": "Voice similarity boost (0-1)",
                "category": "voiceover",
            },
        }

    def _get_quality_settings(project: "Project") -> Dict[str, Any]:
        """Get quality settings with source tracking."""
        # Quality settings come from project.yaml quality and freshness sections
        freshness_config = project.config.freshness
        quality_config = project.config.quality
        return {
            "target_reading_level": {
                "value": quality_config.target_reading_level,
                "source": "project" if quality_config.target_reading_level != QUALITY.target_reading_level else "default",
                "default": QUALITY.target_reading_level,
                "editable": True,
                "description": "Target reading comprehension level (elementary, middle_school, high_school, college, graduate)",
                "category": "quality",
            },
            "target_lix_level": {
                "value": quality_config.target_lix_level,
                "source": "project" if quality_config.target_lix_level != QUALITY.target_lix_level else "default",
                "default": QUALITY.target_lix_level,
                "editable": True,
                "description": "Target Norwegian readability level (very_easy, easy, medium, difficult, very_difficult)",
                "category": "quality",
            },
            "max_sentence_words": {
                "value": quality_config.max_sentence_words,
                "source": "project" if quality_config.max_sentence_words != QUALITY.max_sentence_words else "default",
                "default": QUALITY.max_sentence_words,
                "editable": True,
                "description": "Maximum words per sentence for readability",
                "category": "quality",
            },
            "freshness_default_days": {
                "value": freshness_config.default_freshness_days if freshness_config else QUALITY.freshness_default_days,
                "source": "project" if freshness_config and freshness_config.default_freshness_days != QUALITY.freshness_default_days else "default",
                "default": QUALITY.freshness_default_days,
                "editable": True,
                "description": "Days before content is considered stale",
                "category": "quality",
            },
        }

    def _get_paths_settings(project: "Project") -> Dict[str, Any]:
        """Get path settings with source tracking."""
        paths = project.config.paths

        # Check if desktop deliverables is enabled
        desktop_path = Path.home() / "Desktop" / project.config.name
        publish_path = str(paths.publish) if paths.publish else None
        is_desktop_deliverables = publish_path and Path(publish_path).resolve() == desktop_path.resolve()

        return {
            "content": {
                "value": str(paths.content) if paths.content else "content",
                "source": "project",
                "default": "content",
                "editable": False,  # Changing paths is risky
                "description": "Content directory",
                "category": "paths",
            },
            "assets": {
                "value": str(paths.assets) if paths.assets else "assets",
                "source": "project",
                "default": "assets",
                "editable": False,
                "description": "Assets directory",
                "category": "paths",
            },
            "output": {
                "value": str(paths.output) if paths.output else "output",
                "source": "project",
                "default": "output",
                "editable": False,
                "description": "Build output directory",
                "category": "paths",
            },
            "publish": {
                "value": publish_path or f"dist/{project.config.name}",
                "source": "project" if paths.publish else "default",
                "default": f"dist/{project.config.name}",
                "editable": True,
                "description": "Final deliverables publish directory",
                "category": "paths",
            },
            "desktop_deliverables": {
                "value": is_desktop_deliverables,
                "source": "project" if is_desktop_deliverables else "default",
                "default": False,
                "editable": True,
                "description": f"Publish deliverables to Desktop folder (~/Desktop/{project.config.name})",
                "category": "paths",
                "type": "boolean",
            },
        }

    def _get_env_settings() -> Dict[str, Any]:
        """Get environment variable settings."""
        env_summary = get_env_summary(include_sensitive=False)
        result = {}
        for key, info in env_summary.items():
            result[key] = {
                "value": "[SET]" if info["is_set"] else "[NOT SET]",
                "source": "env",
                "default": None,
                "editable": False,
                "description": info["description"],
                "category": "environment",
                "is_set": info["is_set"],
                "sensitive": info["sensitive"],
            }
        return result
