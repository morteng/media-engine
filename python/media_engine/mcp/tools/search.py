"""Search tools."""

import json
from datetime import datetime


def register_search_tools(mcp, server_instance):
    """Register search-related MCP tools."""

    @mcp.tool()
    async def search_content(query: str, language: str = None, limit: int = 10) -> str:
        """
        Search project content with full-text search.

        Args:
            query: Search query (supports multiple words)
            language: Filter to specific language (optional)
            limit: Maximum results to return (default: 10)
        """
        from ...search import build_search_index

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        # Use cached index if available
        cache_key = f"search_index_{language or 'all'}"
        now = datetime.now().timestamp()

        if cache_key in server_instance._cache:
            index, ts = server_instance._cache[cache_key]
            if now - ts < 60:  # 1 minute cache for search index
                pass
            else:
                index = build_search_index(server_instance.project, console_output=False)
                server_instance._cache[cache_key] = (index, now)
        else:
            index = build_search_index(server_instance.project, console_output=False)
            server_instance._cache[cache_key] = (index, now)

        results = index.search(query, limit=limit)

        if language:
            results = [r for r in results if r.entry.language == language]

        return json.dumps(
            {
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "title": r.entry.title,
                        "path": str(r.entry.path),
                        "language": r.entry.language,
                        "score": round(r.score, 3),
                        "snippet": r.snippet[:200] + "..." if len(r.snippet) > 200 else r.snippet,
                    }
                    for r in results[:limit]
                ],
            },
            indent=2,
        )
