"""Cache management tools."""

import json


def register_cache_tools(mcp, server_instance):
    """Register cache-related MCP tools."""

    @mcp.tool()
    async def cache_status() -> str:
        """Get cache statistics and status."""
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        manifest = server_instance.project._cache_manifest
        return json.dumps(
            {
                "cache_dir": str(server_instance.project.cache_dir),
                "voiceover_cached": len(manifest.get("voiceover", {})),
                "builds_tracked": len(manifest.get("builds", {})),
                "content_hashes": len(manifest.get("content_hashes", {})),
            },
            indent=2,
        )

    @mcp.tool()
    async def clear_cache(cache_type: str = "all") -> str:
        """
        Clear cached data.

        Args:
            cache_type: Type to clear - "all", "voiceover", or "builds"
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        if cache_type not in ("all", "voiceover", "builds"):
            return json.dumps(
                {"error": "cache_type must be 'all', 'voiceover', or 'builds'"}, indent=2
            )

        count = server_instance.project.clear_cache(cache_type)
        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "cleared",
                "type": cache_type,
                "items_cleared": count,
            },
            indent=2,
        )
