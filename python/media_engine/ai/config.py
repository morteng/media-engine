"""
AI Configuration Management

Handles AI backend configuration with priority:
1. Environment variables
2. User config file (~/.media-engine/ai_config.yaml)
3. Project config
4. Defaults
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from .types import AIBackend

if TYPE_CHECKING:
    from ..core.project import Project


CONFIG_DIR = Path.home() / ".media-engine"
CONFIG_FILE = CONFIG_DIR / "ai_config.yaml"


@dataclass
class AIConfig:
    """AI processing configuration."""

    api_key: Optional[str] = None
    backend: AIBackend = AIBackend.CLAUDE_CODE
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7


def get_ai_config(project: Optional["Project"] = None) -> AIConfig:
    """
    Get AI configuration with priority:
    1. Environment variables
    2. User config file
    3. Defaults
    """
    config = AIConfig()

    # Load from user config file if exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
            if data.get("api_key"):
                config.api_key = data["api_key"]
            if data.get("backend"):
                try:
                    config.backend = AIBackend(data["backend"])
                except ValueError:
                    pass
            if data.get("model"):
                config.model = data["model"]
            if data.get("max_tokens"):
                config.max_tokens = int(data["max_tokens"])
            if data.get("temperature"):
                config.temperature = float(data["temperature"])
        except Exception:
            pass

    # Override with environment variables
    if os.environ.get("ANTHROPIC_API_KEY"):
        config.api_key = os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("MEDIA_ENGINE_AI_BACKEND"):
        try:
            config.backend = AIBackend(os.environ["MEDIA_ENGINE_AI_BACKEND"])
        except ValueError:
            pass
    if os.environ.get("MEDIA_ENGINE_AI_MODEL"):
        config.model = os.environ["MEDIA_ENGINE_AI_MODEL"]

    return config


def save_ai_config(
    api_key: Optional[str] = None,
    backend: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> None:
    """Save AI configuration to user config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing config
    data = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Update with provided values
    if api_key is not None:
        data["api_key"] = api_key
    if backend is not None:
        data["backend"] = backend
    if model is not None:
        data["model"] = model
    if max_tokens is not None:
        data["max_tokens"] = max_tokens
    if temperature is not None:
        data["temperature"] = temperature

    # Save
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def is_ai_configured() -> bool:
    """Check if AI is configured (has API key or uses Claude Code backend)."""
    config = get_ai_config()

    # Claude Code doesn't need API key
    if config.backend == AIBackend.CLAUDE_CODE:
        return True

    # Anthropic API needs key
    return config.api_key is not None
