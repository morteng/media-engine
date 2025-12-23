"""
Environment variable handling for Media Engine.

Provides a clean interface for reading and validating environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar

from .paths import ENV

T = TypeVar("T")


@dataclass
class EnvVar:
    """Represents an environment variable with metadata."""

    name: str
    description: str
    default: Optional[str] = None
    required: bool = False
    sensitive: bool = False  # Don't log the value

    def get(self) -> Optional[str]:
        """Get the environment variable value."""
        return os.environ.get(self.name, self.default)

    def get_or_raise(self) -> str:
        """Get the value or raise if not set and required."""
        value = self.get()
        if value is None and self.required:
            raise EnvironmentError(f"Required environment variable {self.name} is not set")
        if value is None:
            raise ValueError(f"Environment variable {self.name} is not set and has no default")
        return value

    def is_set(self) -> bool:
        """Check if the environment variable is set."""
        return self.name in os.environ

    def as_path(self) -> Optional[Path]:
        """Get the value as a Path."""
        value = self.get()
        return Path(value) if value else None

    def as_int(self, default: int = 0) -> int:
        """Get the value as an integer."""
        value = self.get()
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def as_bool(self, default: bool = False) -> bool:
        """Get the value as a boolean."""
        value = self.get()
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")


# =============================================================================
# DEFINED ENVIRONMENT VARIABLES
# =============================================================================

# Path overrides
PUBLISH_DIR = EnvVar(
    name=ENV.publish_dir,
    description="Override the publish directory for built outputs",
    required=False,
)

PROJECT_DIR = EnvVar(
    name=ENV.project_dir,
    description="Override the project directory",
    required=False,
)

# API Keys
ELEVENLABS_API_KEY = EnvVar(
    name=ENV.elevenlabs_key,
    description="ElevenLabs API key for voiceover generation",
    required=False,
    sensitive=True,
)

ELEVENLABS_API_KEY_ALT = EnvVar(
    name=ENV.elevenlabs_key_alt,
    description="Alternative ElevenLabs API key environment variable",
    required=False,
    sensitive=True,
)

# Debug settings
DEBUG = EnvVar(
    name=ENV.debug,
    description="Enable debug mode",
    default="false",
    required=False,
)

LOG_LEVEL = EnvVar(
    name=ENV.log_level,
    description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    default="INFO",
    required=False,
)

# User info
USER = EnvVar(
    name=ENV.user,
    description="Current user (Unix)",
    required=False,
)

USERNAME = EnvVar(
    name=ENV.username,
    description="Current user (Windows)",
    required=False,
)


# =============================================================================
# ALL ENVIRONMENT VARIABLES
# =============================================================================

ALL_ENV_VARS: dict[str, EnvVar] = {
    "publish_dir": PUBLISH_DIR,
    "project_dir": PROJECT_DIR,
    "elevenlabs_api_key": ELEVENLABS_API_KEY,
    "elevenlabs_api_key_alt": ELEVENLABS_API_KEY_ALT,
    "debug": DEBUG,
    "log_level": LOG_LEVEL,
    "user": USER,
    "username": USERNAME,
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_elevenlabs_api_key() -> Optional[str]:
    """Get ElevenLabs API key from either environment variable."""
    return ELEVENLABS_API_KEY.get() or ELEVENLABS_API_KEY_ALT.get()


def get_current_user() -> str:
    """Get current username from environment."""
    return USER.get() or USERNAME.get() or "unknown"


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return DEBUG.as_bool()


def get_log_level() -> str:
    """Get configured log level."""
    return LOG_LEVEL.get() or "INFO"


def validate_required_env_vars() -> list[str]:
    """
    Validate all required environment variables are set.

    Returns:
        List of missing required variable names
    """
    missing = []
    for var in ALL_ENV_VARS.values():
        if var.required and not var.is_set():
            missing.append(var.name)
    return missing


def get_env_summary(include_sensitive: bool = False) -> dict[str, dict[str, Any]]:
    """
    Get a summary of all environment variables.

    Args:
        include_sensitive: Whether to include actual values of sensitive vars

    Returns:
        Dictionary of variable info
    """
    summary = {}
    for key, var in ALL_ENV_VARS.items():
        value = var.get()
        summary[key] = {
            "name": var.name,
            "description": var.description,
            "is_set": var.is_set(),
            "required": var.required,
            "sensitive": var.sensitive,
            "value": ("[REDACTED]" if var.sensitive and not include_sensitive else value),
        }
    return summary


def generate_env_example() -> str:
    """
    Generate content for a .env.example file.

    Returns:
        String content for .env.example
    """
    lines = [
        "# Media Engine Environment Variables",
        "# Copy this file to .env and fill in the values",
        "",
    ]

    for var in ALL_ENV_VARS.values():
        lines.append(f"# {var.description}")
        if var.required:
            lines.append("# REQUIRED")
        if var.sensitive:
            lines.append("# SENSITIVE - do not commit to version control")

        if var.default:
            lines.append(f"{var.name}={var.default}")
        else:
            lines.append(f"# {var.name}=")
        lines.append("")

    return "\n".join(lines)
