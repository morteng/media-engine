"""
Dependencies API routes.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_dependencies_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register dependency-related routes."""
    from pathlib import Path

    @router.get("/api/dependencies")
    async def get_dependencies():
        """Get all content dependencies."""
        project = get_project()

        try:
            from ...freshness import ContentRegistry, scan_project

            registry = ContentRegistry(project)
            registry.load()
            if not registry.items:
                scan_project(project, registry)
                registry.save()

            # Build dependency data
            items = []
            for path, item in registry.items.items():
                items.append({
                    "path": str(item.path),
                    "type": item.content_type.value,
                    "status": item.freshness_status.value,
                    "depends_on": [str(d) for d in item.depends_on],
                    "dependents": [],  # Will be populated below
                })

            # Build reverse dependency map (what depends on this item)
            path_to_idx = {item["path"]: i for i, item in enumerate(items)}
            for item in items:
                for dep in item["depends_on"]:
                    if dep in path_to_idx:
                        items[path_to_idx[dep]]["dependents"].append(item["path"])

            # Build tree structure
            tree = build_dependency_tree(items)

            return {
                "items": items,
                "tree": tree,
                "stats": {
                    "total": len(items),
                    "with_deps": len([i for i in items if i["depends_on"]]),
                    "roots": len([i for i in items if not i["depends_on"]]),
                },
            }

        except Exception as e:
            return {
                "items": [],
                "tree": [],
                "stats": {"total": 0, "with_deps": 0, "roots": 0},
                "error": str(e),
            }

    @router.get("/api/dependencies/impact/{path:path}")
    async def get_dependency_impact(path: str):
        """Get items affected if a file changes."""
        project = get_project()

        try:
            from ...freshness import ContentRegistry

            registry = ContentRegistry(project)
            registry.load()

            affected = registry.get_impact(Path(path))

            return {
                "source": path,
                "affected": [
                    {
                        "path": str(item.path),
                        "type": item.content_type.value,
                        "status": item.freshness_status.value,
                    }
                    for item in affected
                ],
                "count": len(affected),
            }

        except Exception as e:
            return {
                "source": path,
                "affected": [],
                "count": 0,
                "error": str(e),
            }

    @router.get("/api/dependencies/files")
    async def get_trackable_files():
        """Get list of files that can be selected for impact analysis."""
        project = get_project()

        files = []

        # Scan key directories
        scan_dirs = [
            ("content", project.content_dir),
            ("theme", project.root),
            ("deliverables", project.root / "docs" / "deliverables"),
        ]

        for category, base_dir in scan_dirs:
            if not base_dir.exists():
                continue

            for ext in ["*.md", "*.yaml", "*.yml", "*.css", "*.js", "*.html", "*.svg"]:
                for f in base_dir.rglob(ext):
                    if ".git" in str(f) or "node_modules" in str(f):
                        continue
                    files.append({
                        "path": str(f.relative_to(project.root)),
                        "name": f.name,
                        "category": category,
                    })

        # Sort by category and name
        files.sort(key=lambda x: (x["category"], x["name"]))

        return {"files": files[:500]}  # Limit to 500


def build_dependency_tree(items):
    """Build a tree structure from flat dependency list."""
    # Find root items (no dependencies)
    roots = [i for i in items if not i["depends_on"]]

    # Group items by type for better organization
    by_type = {}
    for item in items:
        item_type = item["type"]
        if item_type not in by_type:
            by_type[item_type] = []
        by_type[item_type].append(item)

    tree = []
    for type_name, type_items in sorted(by_type.items()):
        tree.append({
            "type": "group",
            "name": type_name.replace("_", " ").title(),
            "count": len(type_items),
            "children": [
                {
                    "type": "item",
                    "path": i["path"],
                    "item_type": i["type"],
                    "status": i["status"],
                    "deps_count": len(i["depends_on"]),
                    "dependents_count": len(i["dependents"]),
                }
                for i in sorted(type_items, key=lambda x: x["path"])
            ],
        })

    return tree
