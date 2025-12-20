"""
AI Processing Types

Data structures for AI-assisted content operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AIOperation(str, Enum):
    """Available AI operations."""

    IMPROVE = "improve"
    TRANSLATE = "translate"
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    EXPAND = "expand"
    SIMPLIFY = "simplify"
    PROOFREAD = "proofread"


class AIBackend(str, Enum):
    """Available AI backends."""

    ANTHROPIC = "anthropic"
    CLAUDE_CODE = "claude_code"


@dataclass
class ContentSelection:
    """A piece of content selected for AI processing."""

    path: str
    content: str
    title: str
    content_type: str = "document"
    target_id: Optional[str] = None
    notes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIProcessRequest:
    """Request to process content through AI."""

    operation: AIOperation
    selections: List[ContentSelection]
    instructions: str = ""
    target_language: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentResult:
    """Result for a single content item."""

    path: str
    original: str
    processed: str
    changes_made: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


@dataclass
class AIProcessResult:
    """Result of AI processing."""

    request_id: str
    status: str
    results: List[ContentResult] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    duration_ms: int = 0
    error: Optional[str] = None
