"""
User Configuration Module

Manages user-level settings stored in ~/.media-engine/
"""

from .user_config import (
    add_recent_project,
    get_recent_projects,
    get_user_config_dir,
    remove_recent_project,
)

__all__ = [
    "get_user_config_dir",
    "get_recent_projects",
    "add_recent_project",
    "remove_recent_project",
]
