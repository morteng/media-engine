"""Status command - show project status."""

import json
import sys

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_status(args):
    """Show project status."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found in current directory or parents[/red]")
        sys.exit(1)

    # Check for specific view
    view = getattr(args, "view", None)

    if args.json:
        status = project.get_status()
        print(json.dumps(status, indent=2, default=str))
        return

    # Import status module
    from ...status import (
        get_project_dashboard,
        print_dashboard,
        print_deliverable_status,
        print_document_status,
        print_quality_status,
        print_video_status,
    )
    from ...status.views import print_build_tree, print_cache_status

    if view == "docs":
        print_document_status(project, getattr(args, "lang", None))
    elif view == "videos":
        print_video_status(project, getattr(args, "lang", None))
    elif view == "quality":
        print_quality_status(project, getattr(args, "lang", None))
    elif view == "deliverables":
        print_deliverable_status(project)
    elif view == "tree":
        print_build_tree(project)
    elif view == "cache":
        print_cache_status(project)
    else:
        # Default: comprehensive dashboard
        dashboard = get_project_dashboard(project)
        print_dashboard(dashboard)
