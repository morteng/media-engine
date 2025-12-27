"""
AI-Native Content Processing Module

Provides comprehensive AI integration for Media Engine:
- Work queue for task management
- Session tracking for continuity across conversations
- Research store for persistent knowledge
- Notes system for AI-human collaboration
- Context provider for comprehensive AI awareness
- Approval gates for human-in-the-loop workflows
- Document locking for concurrent safety
"""

from .approval import ApprovalManager, ApprovalRequest, ApprovalResponse, ApprovalStatus
from .config import AIConfig, get_ai_config, is_ai_configured, save_ai_config
from .context import AIContext
from .locking import DocumentLock, LockManager, get_lock_manager
from .notes import Note, NotePriority, NotesManager, NoteStatus, NoteType
from .queue import AITask, TaskPriority, TaskQueue, TaskStatus
from .research import ResearchItem, ResearchSource, ResearchStatus, ResearchStore
from .sessions import (
    Session,
    SessionChange,
    SessionCheckpoint,
    SessionDecision,
    SessionManager,
    SessionStatus,
    SessionStep,
)
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
    # Sessions
    "SessionManager",
    "Session",
    "SessionStatus",
    "SessionStep",
    "SessionChange",
    "SessionCheckpoint",
    "SessionDecision",
    # Research
    "ResearchStore",
    "ResearchItem",
    "ResearchSource",
    "ResearchStatus",
    # Notes
    "NotesManager",
    "Note",
    "NoteType",
    "NoteStatus",
    "NotePriority",
    # Locking
    "LockManager",
    "DocumentLock",
    "get_lock_manager",
    # Approval
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalResponse",
    "ApprovalStatus",
    # Context
    "AIContext",
]
