"""
Structured Error Handling for MCP Tools

Provides utilities for consistent, agent-parseable error responses
that work with the core exception hierarchy.

Usage:
    from .errors import mcp_error_handler, format_error

    @mcp.tool()
    @mcp_error_handler
    async def my_tool(path: str) -> str:
        # Raise MediaEngineError subclasses - they'll be formatted
        raise DocumentNotFoundError(path=path)

    # Or manually format errors
    return format_error(DocumentNotFoundError(path=path))
"""

import functools
import json
import traceback
from typing import Any, Callable, TypeVar

from ...core.exceptions import (
    MediaEngineError,
    DocumentLockedError,
    DocumentNotFoundError,
    SessionNotFoundError,
    ApprovalRequiredError,
    error_from_dict,
    is_recoverable,
    get_error_suggestions,
)


F = TypeVar("F", bound=Callable[..., Any])


def format_error(
    error: Exception,
    include_traceback: bool = False,
) -> str:
    """
    Format an exception into a structured JSON response.

    Args:
        error: The exception to format
        include_traceback: Whether to include stack trace (for debugging)

    Returns:
        JSON string with structured error information
    """
    if isinstance(error, MediaEngineError):
        # Use the structured to_dict() from our exception hierarchy
        result = error.to_dict()
    else:
        # Generic exception - wrap in standard format
        result = {
            "error": "UNEXPECTED_ERROR",
            "message": str(error),
            "recoverable": False,
            "suggestions": [
                "Check logs for more details",
                "Try the operation again",
                "Report this issue if it persists",
            ],
            "context": {},
            "type": error.__class__.__name__,
        }

    if include_traceback:
        result["traceback"] = traceback.format_exc()

    return json.dumps(result, indent=2)


def format_success(
    data: Any,
    message: str = None,
) -> str:
    """
    Format a successful result into a structured JSON response.

    Args:
        data: The result data
        message: Optional success message

    Returns:
        JSON string with success flag and data
    """
    result = {
        "success": True,
        "data": data,
    }
    if message:
        result["message"] = message
    return json.dumps(result, indent=2)


def mcp_error_handler(func: F) -> F:
    """
    Decorator that catches exceptions and formats them as structured responses.

    Use this on MCP tool functions to ensure consistent error handling:

        @mcp.tool()
        @mcp_error_handler
        async def my_tool(path: str) -> str:
            ...

    MediaEngineError subclasses are formatted with full context.
    Other exceptions are wrapped in a generic error format.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> str:
        try:
            return await func(*args, **kwargs)
        except MediaEngineError as e:
            return format_error(e)
        except json.JSONDecodeError as e:
            return format_error(
                MediaEngineError(
                    message=f"Invalid JSON: {e}",
                    error_code="INVALID_JSON",
                    recoverable=True,
                    suggestions=["Check JSON syntax", "Ensure proper escaping"],
                )
            )
        except FileNotFoundError as e:
            return format_error(
                DocumentNotFoundError(
                    path=str(e.filename) if e.filename else "unknown",
                    message=str(e),
                )
            )
        except PermissionError as e:
            return format_error(
                MediaEngineError(
                    message=f"Permission denied: {e}",
                    error_code="PERMISSION_DENIED",
                    recoverable=False,
                    suggestions=[
                        "Check file permissions",
                        "Ensure you have write access",
                    ],
                )
            )
        except Exception as e:
            return format_error(e)

    return wrapper  # type: ignore


def require_project(server_instance) -> str | None:
    """
    Check if a project is loaded, return error response if not.

    Usage:
        if error := require_project(server_instance):
            return error
    """
    if not server_instance.project:
        from ...core.exceptions import ProjectNotFoundError
        return format_error(
            ProjectNotFoundError(
                message="No project found. Run from a directory with project.yaml",
                search_path=".",
            )
        )
    return None


def require_language(server_instance, language: str) -> str | None:
    """
    Check if a language is configured, return error response if not.

    Usage:
        if error := require_language(server_instance, lang):
            return error
    """
    if language not in server_instance.project.languages:
        from ...core.exceptions import ConfigurationError
        return format_error(
            ConfigurationError(
                message=f"Language '{language}' not configured",
                config_key="languages",
                suggestions=[
                    f"Add '{language}' to project.yaml languages section",
                    f"Available languages: {', '.join(server_instance.project.languages)}",
                ],
            )
        )
    return None


def require_path_exists(path, description: str = "File") -> str | None:
    """
    Check if a path exists, return error response if not.

    Usage:
        if error := require_path_exists(validated_path, "Document"):
            return error
    """
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return format_error(
            DocumentNotFoundError(
                path=str(path),
                message=f"{description} not found: {path}",
            )
        )
    return None


def check_document_lock(
    server_instance,
    document_path: str,
    session_id: str = None,
) -> str | None:
    """
    Check if a document is locked by another session.

    Args:
        server_instance: MCP server instance
        document_path: Path to the document
        session_id: Current session ID (if known)

    Returns:
        Error response if locked by another session, None if available
    """
    from ...ai.locking import get_lock_manager

    if not server_instance.project:
        return None  # Let require_project handle this

    manager = get_lock_manager(server_instance.project.root)
    lock = manager.check_lock(document_path)

    if lock and (session_id is None or lock.session_id != session_id):
        return format_error(
            DocumentLockedError(
                message=f"Document is locked by session '{lock.session_id}'",
                path=document_path,
                locked_by=lock.session_id,
                lock_expires=lock.expires_at,
            )
        )
    return None


class MCPToolError(Exception):
    """
    Exception that can be raised in MCP tools to return a structured error.

    This is a convenience wrapper that holds both the exception and
    pre-formatted response.
    """

    def __init__(self, error: MediaEngineError | Exception):
        self.error = error
        self.response = format_error(error)
        super().__init__(str(error))
