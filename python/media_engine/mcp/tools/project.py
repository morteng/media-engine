"""Project management tools."""

import json


def register_project_tools(mcp, server_instance):
    """Register project-related MCP tools."""

    @mcp.tool()
    async def project_status() -> str:
        """
        Get comprehensive project status.

        Returns project configuration, content counts per language,
        cache statistics, and overall health.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        status = server_instance.project.get_status()
        status["health"] = server_instance._get_health_summary()
        return json.dumps(status, indent=2)

    @mcp.tool()
    async def project_config() -> str:
        """
        Get project configuration details.

        Returns all settings from project.yaml including paths,
        localization, voiceover, and video settings.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        return json.dumps(
            {
                "name": server_instance.project.config.name,
                "description": server_instance.project.config.description,
                "languages": {
                    code: {"name": lang.name, "locale": lang.locale, "voice_id": lang.voice_id}
                    for code, lang in server_instance.project.languages.items()
                },
                "source_language": server_instance.project.source_language,
                "paths": {
                    "root": str(server_instance.project.root),
                    "content": str(server_instance.project.content_dir),
                    "assets": str(server_instance.project.assets_dir),
                    "output": str(server_instance.project.output_dir),
                    "publish": str(server_instance.project.publish_dir),
                    "cache": str(server_instance.project.cache_dir),
                },
                "voiceover": {
                    "provider": server_instance.project.config.voiceover.provider,
                    "model": getattr(server_instance.project.config.voiceover, "model", None),
                },
                "video": {
                    "width": server_instance.project.config.video.width,
                    "height": server_instance.project.config.video.height,
                    "fps": server_instance.project.config.video.fps,
                },
            },
            indent=2,
        )

    @mcp.tool()
    async def refresh_project() -> str:
        """
        Refresh project data by clearing caches.

        Use this after making changes to project files to ensure
        subsequent queries return fresh data.
        """
        server_instance._invalidate_cache()
        return json.dumps(
            {
                "status": "cache_cleared",
                "message": "Project data will be refreshed on next query",
            }
        )
