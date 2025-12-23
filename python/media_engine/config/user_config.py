"""
User Configuration Management

Handles user-level configuration stored in ~/.media-engine/
Tracks recent projects for easy switching in the dashboard.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class RecentProject:
    """A recently accessed project."""

    path: str
    name: str
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "last_accessed": self.last_accessed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecentProject":
        return cls(
            path=data["path"],
            name=data.get("name", Path(data["path"]).name),
            last_accessed=data.get("last_accessed", datetime.now().isoformat()),
        )


def get_user_config_dir() -> Path:
    """Get the user configuration directory (~/.media-engine/)."""
    config_dir = Path.home() / ".media-engine"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_config_path() -> Path:
    """Get path to the user config file."""
    return get_user_config_dir() / "config.yaml"


def _load_config() -> dict:
    """Load user configuration from file."""
    config_path = _get_config_path()
    if not config_path.exists():
        return {"recent_projects": [], "max_recent_projects": 10}

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
            if "recent_projects" not in config:
                config["recent_projects"] = []
            if "max_recent_projects" not in config:
                config["max_recent_projects"] = 10
            return config
    except Exception:
        return {"recent_projects": [], "max_recent_projects": 10}


def _save_config(config: dict) -> None:
    """Save user configuration to file."""
    config_path = _get_config_path()
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_recent_projects(*, include_temp: bool = False) -> List[RecentProject]:
    """
    Get list of recent projects, sorted by last accessed (most recent first).

    Args:
        include_temp: If True, include temp directory paths (for testing)

    Returns:
        List of RecentProject objects
    """
    config = _load_config()
    projects = []

    for proj_data in config.get("recent_projects", []):
        try:
            # Skip temp directory paths unless explicitly included
            path = proj_data.get("path", "")
            if not include_temp and _is_temp_path(path):
                continue
            projects.append(RecentProject.from_dict(proj_data))
        except (KeyError, TypeError):
            continue

    # Sort by last_accessed, most recent first
    projects.sort(key=lambda p: p.last_accessed, reverse=True)
    return projects


def add_recent_project(
    path: str, name: Optional[str] = None, *, allow_temp: bool = False
) -> Optional[RecentProject]:
    """
    Add or update a project in the recent projects list.

    Args:
        path: Absolute path to the project root
        name: Optional project name (defaults to directory name)
        allow_temp: If True, allow temp directory paths (for testing)

    Returns:
        The RecentProject that was added/updated, or None if skipped (temp path)
    """
    # Normalize path
    project_path = str(Path(path).resolve())

    # Skip temp directories (from tests, etc.) unless explicitly allowed
    if not allow_temp and _is_temp_path(project_path):
        return None

    config = _load_config()
    max_projects = config.get("max_recent_projects", 10)

    project_name = name or Path(path).name

    # Remove existing entry for this path (if any)
    config["recent_projects"] = [
        p for p in config["recent_projects"] if p.get("path") != project_path
    ]

    # Create new entry
    project = RecentProject(
        path=project_path,
        name=project_name,
        last_accessed=datetime.now().isoformat(),
    )

    # Add to front of list
    config["recent_projects"].insert(0, project.to_dict())

    # Trim to max
    config["recent_projects"] = config["recent_projects"][:max_projects]

    _save_config(config)
    return project


def remove_recent_project(path: str) -> bool:
    """
    Remove a project from the recent projects list.

    Args:
        path: Path to the project to remove

    Returns:
        True if project was found and removed, False otherwise
    """
    config = _load_config()
    project_path = str(Path(path).resolve())

    original_count = len(config["recent_projects"])
    config["recent_projects"] = [
        p for p in config["recent_projects"] if p.get("path") != project_path
    ]

    if len(config["recent_projects"]) < original_count:
        _save_config(config)
        return True
    return False


def project_exists(path: str) -> bool:
    """
    Check if a project path exists and contains a project.yaml.

    Args:
        path: Path to check

    Returns:
        True if valid project directory
    """
    project_path = Path(path)
    return project_path.exists() and (project_path / "project.yaml").exists()


def _is_temp_path(path: str) -> bool:
    """
    Check if a path is in a temporary directory.

    Args:
        path: Path to check

    Returns:
        True if path appears to be in a temp directory
    """
    import tempfile

    path_lower = path.lower()
    temp_indicators = [
        "/tmp/",
        "/temp/",
        "/var/folders/",
        "/private/var/folders/",
        tempfile.gettempdir().lower(),
    ]
    return any(indicator in path_lower for indicator in temp_indicators)


def cleanup_temp_projects() -> int:
    """
    Remove all temp directory paths from the recent projects list.

    Returns:
        Number of projects removed
    """
    config = _load_config()
    original_count = len(config.get("recent_projects", []))

    config["recent_projects"] = [
        p for p in config.get("recent_projects", []) if not _is_temp_path(p.get("path", ""))
    ]

    removed = original_count - len(config["recent_projects"])
    if removed > 0:
        _save_config(config)

    return removed
