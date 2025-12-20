"""
AI-Assisted Content Processing Module

Provides AI-powered content operations like improvement, translation, and analysis.
"""

from .config import AIConfig, get_ai_config, is_ai_configured, save_ai_config
from .queue import AITask, TaskPriority, TaskQueue, TaskStatus
from .types import (
    AIBackend,
    AIOperation,
    AIProcessRequest,
    AIProcessResult,
    ContentSelection,
)

__all__ = [
    # Types
    "AIOperation",
    "AIBackend",
    "ContentSelection",
    "AIProcessRequest",
    "AIProcessResult",
    # Config
    "AIConfig",
    "get_ai_config",
    "save_ai_config",
    "is_ai_configured",
    # Queue
    "TaskQueue",
    "AITask",
    "TaskStatus",
    "TaskPriority",
]
