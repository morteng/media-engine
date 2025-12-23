"""
Freshness tracking API routes.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_freshness_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register freshness tracking routes."""
    from ...freshness import ContentRegistry, scan_project

    @router.get("/api/freshness")
    async def get_freshness(content_type: str = None, scan: bool = False):
        """Get freshness report for all tracked content."""
        project = get_project()

        # Initialize registry
        registry = ContentRegistry(project)
        registry.load()

        # Scan if requested or if registry is empty
        if scan or not registry.items:
            scan_project(project, registry)

        # Refresh freshness status
        report = registry.refresh()

        # Save updated registry
        registry.save()

        # Filter by content type if specified
        items = list(registry.items.values())
        stale_items = report.stale_items
        expired_items = report.expired_items
        claims_issue_items = report.claims_issue_items

        if content_type:
            from ...freshness import ContentType

            try:
                filter_type = ContentType(content_type)
                items = [i for i in items if i.content_type == filter_type]
                stale_items = [i for i in stale_items if i.content_type == filter_type]
                expired_items = [i for i in expired_items if i.content_type == filter_type]
                claims_issue_items = [
                    i for i in claims_issue_items if i.content_type == filter_type
                ]
            except ValueError:
                pass  # Invalid type, return all

        # Get ignore patterns for display
        ignore_patterns = registry.get_ignore_patterns()

        # Generate suggestions for untracked files
        def get_suggestion(path_str: str) -> str:
            if "/audio/" in path_str or path_str.endswith(".mp3"):
                return "ignore"
            elif ".cache" in path_str:
                return "ignore"
            elif "/slides/" in path_str:
                return "track"
            elif "/demos/" in path_str or "/demo/" in path_str:
                return "track"
            elif path_str.endswith(".md"):
                return "track"
            elif path_str.endswith(".yaml") or path_str.endswith(".yml"):
                return "track"
            return ""

        return {
            "total_items": report.total_items,
            "fresh_count": report.fresh_count,
            "stale_count": report.stale_count,
            "expired_count": report.expired_count,
            "missing_count": report.missing_count,
            "untracked_count": report.untracked_count,
            "ignored_count": report.ignored_count,
            "claims_issue_count": report.claims_issue_count,
            "ignore_patterns": ignore_patterns,
            "items": [
                {
                    "path": str(item.path),
                    "content_type": item.content_type.value,
                    "status": item.freshness_status.value,
                    "depends_on": [str(d) for d in item.depends_on],
                    "last_modified": item.last_modified.isoformat() if item.last_modified else None,
                    "content_hash": item.content_hash[:8] if item.content_hash else None,
                    "claims_unverified": item.metadata.get("claims_unverified"),
                    "claims_expired": item.metadata.get("claims_expired"),
                }
                for item in items
            ],
            "stale_items": [
                {
                    "path": str(item.path),
                    "content_type": item.content_type.value,
                    "depends_on": [str(d) for d in item.depends_on],
                }
                for item in stale_items
            ],
            "expired_items": [
                {
                    "path": str(item.path),
                    "content_type": item.content_type.value,
                    "freshness_days": item.freshness_days,
                    "last_modified": item.last_modified.isoformat() if item.last_modified else None,
                }
                for item in expired_items
            ],
            "claims_issue_items": [
                {
                    "path": str(item.path),
                    "content_type": item.content_type.value,
                    "claims_unverified": item.metadata.get("claims_unverified", 0),
                    "claims_expired": item.metadata.get("claims_expired", 0),
                }
                for item in claims_issue_items
            ],
            "untracked_files": [
                {"path": str(p), "suggestion": get_suggestion(str(p))}
                for p in report.untracked_files[:100]
            ],
            "ignored_files": [str(p) for p in report.ignored_files[:50]],
        }

    @router.post("/api/freshness/scan")
    async def scan_freshness():
        """Scan and re-register all project content."""
        project = get_project()

        # Initialize registry
        registry = ContentRegistry(project)
        registry.load()

        # Clear and rescan
        registry.items.clear()
        count = scan_project(project, registry)

        # Refresh and save
        report = registry.refresh()
        registry.save()

        return {
            "registered": count,
            "total_items": report.total_items,
            "stale_count": report.stale_count,
            "expired_count": report.expired_count,
            "untracked_count": report.untracked_count,
        }

    @router.get("/api/freshness/impact/{path:path}")
    async def get_freshness_impact(path: str):
        """Get items that would be affected if a file changes."""
        from pathlib import Path

        project = get_project()

        registry = ContentRegistry(project)
        registry.load()

        affected = registry.get_impact(Path(path))

        return {
            "source": path,
            "affected_items": [
                {
                    "path": str(item.path),
                    "content_type": item.content_type.value,
                }
                for item in affected
            ],
        }
