"""
GUI Launcher for Media Engine

Provides easy ways to start the web dashboard:
- Auto-detect project in current directory
- Browse for project directory
- Command-line launcher
- Desktop integration (optional)

Usage:
    media-engine-gui              # Auto-detect or browse
    media-engine-gui /path/to    # Start with specific project
    media-engine dashboard       # CLI equivalent
"""

import os
import sys
import webbrowser
from pathlib import Path
from typing import Optional


def find_project_in_directory(directory: Path) -> Optional[Path]:
    """Find project.yaml in directory or its parents."""
    current = directory.resolve()

    while current != current.parent:
        project_file = current / "project.yaml"
        if project_file.exists():
            return current
        current = current.parent

    return None


def browse_for_directory() -> Optional[Path]:
    """
    Open a directory browser dialog.

    Uses tkinter if available, falls back to command-line prompt.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # Hide main window

        directory = filedialog.askdirectory(title="Select Media Engine Project Directory")

        root.destroy()

        if directory:
            return Path(directory)
        return None

    except ImportError:
        # No tkinter, use command-line
        print("\nNo project found in current directory.")
        path = input("Enter project path (or press Enter to cancel): ").strip()
        if path:
            return Path(path)
        return None


def check_dependencies() -> tuple[bool, list[str]]:
    """Check if required dependencies are installed."""
    missing = []

    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")

    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")

    try:
        import websockets
    except ImportError:
        missing.append("websockets")

    return len(missing) == 0, missing


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎬 Media Engine Dashboard                                 ║
║                                                              ║
║   Content Management & Media Production System               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_project_info(project_path: Path):
    """Print project information."""
    import yaml

    project_file = project_path / "project.yaml"
    if project_file.exists():
        with open(project_file) as f:
            config = yaml.safe_load(f)

        name = config.get("name", "Unknown")
        desc = config.get("description", "")

        print(f"  Project: {name}")
        if desc:
            print(f"  Description: {desc[:60]}{'...' if len(desc) > 60 else ''}")
        print(f"  Location: {project_path}")
        print()


def launch_dashboard(
    project_path: Path,
    host: str = "127.0.0.1",
    port: int = 8080,
    open_browser: bool = True,
):
    """Launch the web dashboard."""
    # Verify it's a valid project
    if not (project_path / "project.yaml").exists():
        print(f"Error: No project.yaml found in {project_path}")
        sys.exit(1)

    # Import and run
    try:
        from ..web import run_dashboard
    except ImportError as e:
        print(f"Error importing web module: {e}")
        print("\nInstall web dependencies with:")
        print("  pip install media-engine[web]")
        sys.exit(1)

    url = f"http://{host}:{port}"
    print(f"  Starting dashboard at: {url}")
    print()
    print("  Press Ctrl+C to stop")
    print("─" * 50)

    run_dashboard(
        project_path=project_path,
        host=host,
        port=port,
        open_browser=open_browser,
    )


def main():
    """Main GUI launcher entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="media-engine-gui",
        description="Launch Media Engine Dashboard",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        help="Path to project directory (auto-detects if not specified)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser",
    )
    parser.add_argument(
        "--browse",
        action="store_true",
        help="Open directory browser instead of auto-detect",
    )

    args = parser.parse_args()

    print_banner()

    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with:")
        print("  pip install media-engine[web]")
        sys.exit(1)

    # Determine project path
    project_path = None

    if args.project_path:
        # Explicit path provided
        project_path = Path(args.project_path).resolve()
        if not project_path.exists():
            print(f"Error: Directory does not exist: {project_path}")
            sys.exit(1)
    elif args.browse:
        # Open directory browser
        project_path = browse_for_directory()
        if not project_path:
            print("No directory selected. Exiting.")
            sys.exit(0)
    else:
        # Auto-detect in current directory
        project_path = find_project_in_directory(Path.cwd())

        if not project_path:
            # Try to browse
            print("No project found in current directory.")
            project_path = browse_for_directory()
            if not project_path:
                print("\nUsage: media-engine-gui /path/to/project")
                print("Or run from a directory containing project.yaml")
                sys.exit(1)

    # Validate project
    if not (project_path / "project.yaml").exists():
        # Check if path is a parent directory containing projects
        sub_projects = list(project_path.glob("**/project.yaml"))
        if sub_projects:
            print(f"Found {len(sub_projects)} project(s):")
            for i, p in enumerate(sub_projects[:5]):
                print(f"  {i + 1}. {p.parent}")
            print("\nSpecify the exact project directory.")
            sys.exit(1)
        else:
            print(f"Error: No project.yaml found in {project_path}")
            sys.exit(1)

    # Print project info
    print_project_info(project_path)

    # Launch dashboard
    launch_dashboard(
        project_path=project_path,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )


# Quick launcher for import
def quick_launch(project_path: str = None, port: int = 8080):
    """
    Quick launch function for programmatic use.

    Usage:
        from media_engine.gui import quick_launch
        quick_launch()  # Auto-detect project
        quick_launch("/path/to/project")  # Specific project
    """
    if project_path:
        path = Path(project_path).resolve()
    else:
        path = find_project_in_directory(Path.cwd())
        if not path:
            raise ValueError("No project found in current directory")

    launch_dashboard(path, port=port)


__all__ = [
    "main",
    "quick_launch",
    "launch_dashboard",
    "find_project_in_directory",
]
