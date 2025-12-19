"""
Search API routes.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_search_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register search-related routes."""
    import re
    from pathlib import Path

    @router.get("/api/search")
    async def search_content(
        q: str,
        lang: str = None,
        type: str = None,
        limit: int = 50,
    ):
        """Search across all project content."""
        project = get_project()

        if not q or len(q) < 2:
            return {"results": [], "total": 0, "query": q}

        results = []
        query_lower = q.lower()
        query_pattern = re.compile(re.escape(q), re.IGNORECASE)

        # Determine which languages to search
        languages = [lang] if lang and lang in project.languages else list(project.languages.keys())

        for search_lang in languages:
            # Search directories based on type filter
            search_dirs = []
            if not type or type == "chapter":
                search_dirs.append((project.content_dir / search_lang / "chapters", "chapter"))
            if not type or type == "script":
                search_dirs.append((project.content_dir / search_lang / "scripts", "script"))
            if not type or type == "data":
                search_dirs.append((project.content_dir / search_lang / "data", "data"))

            for search_dir, doc_type in search_dirs:
                if not search_dir.exists():
                    continue

                for file_path in search_dir.rglob("*"):
                    if not file_path.is_file():
                        continue

                    # Skip non-text files
                    if file_path.suffix.lower() not in [".md", ".yaml", ".yml", ".json", ".txt"]:
                        continue

                    try:
                        content = file_path.read_text(encoding="utf-8")
                    except Exception:
                        continue

                    # Check if query matches
                    matches = list(query_pattern.finditer(content))
                    if not matches and query_lower not in file_path.name.lower():
                        continue

                    # Extract title from content
                    title = file_path.stem.replace("_", " ").replace("-", " ").title()
                    if file_path.suffix == ".md":
                        # Try to get title from frontmatter or first heading
                        lines = content.split("\n")
                        for line in lines:
                            if line.startswith("# "):
                                title = line[2:].strip()
                                break
                            if line.startswith("title:"):
                                title = line[6:].strip().strip('"\'')
                                break

                    # Generate snippet with context
                    snippet = ""
                    if matches:
                        match = matches[0]
                        start = max(0, match.start() - 100)
                        end = min(len(content), match.end() + 100)
                        snippet = content[start:end]

                        # Clean up snippet
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."

                        # Highlight matches in snippet
                        snippet = query_pattern.sub(
                            lambda m: f"<mark>{m.group()}</mark>",
                            snippet
                        )

                    results.append({
                        "path": str(file_path.relative_to(project.root)),
                        "title": title,
                        "type": doc_type,
                        "language": search_lang,
                        "snippet": snippet,
                        "match_count": len(matches),
                        "score": len(matches) + (10 if query_lower in file_path.name.lower() else 0),
                    })

        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "results": results[:limit],
            "total": len(results),
            "query": q,
        }

    @router.post("/api/search/index/rebuild")
    async def rebuild_search_index():
        """Rebuild the search index."""
        project = get_project()

        try:
            from ...search import SearchIndex

            index = SearchIndex(project)
            index.build()
            index.save()

            return {
                "status": "rebuilt",
                "documents": len(index.documents) if hasattr(index, "documents") else 0,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }
