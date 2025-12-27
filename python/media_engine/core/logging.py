"""
Structured Logging for Media Engine

Provides consistent, machine-parseable logging for AI agents and human operators.
Supports both human-readable console output and structured JSON for machine parsing.

Features:
- Structured log entries with context
- Operation tracking with timing
- Event correlation via request_id
- Multiple output formats (console, JSON, file)
- Log level filtering per component

Usage:
    from media_engine.core.logging import get_logger, LogContext

    logger = get_logger("documents")

    # Simple logging
    logger.info("Document loaded", path="content/en/chapters/01.md")

    # With context manager for operation tracking
    with logger.operation("build_document", document_id="doc-123"):
        # ... do work ...
        logger.debug("Processing section", section="intro")
    # Automatically logs operation completion with duration

    # Structured context
    with LogContext(session_id="abc-123", agent="video-producer"):
        logger.info("Starting video render")
"""

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from threading import local
from typing import Any, Callable, Dict, List, Optional, TypeVar

# Thread-local storage for context
_context = local()


def get_context() -> Dict[str, Any]:
    """Get current logging context."""
    if not hasattr(_context, "data"):
        _context.data = {}
    return _context.data


def set_context(**kwargs) -> None:
    """Set context values for current thread."""
    ctx = get_context()
    ctx.update(kwargs)


def clear_context() -> None:
    """Clear all context values."""
    _context.data = {}


@contextmanager
def LogContext(**kwargs):
    """
    Context manager for adding temporary context to all log messages.

    Usage:
        with LogContext(session_id="abc", agent="video-producer"):
            logger.info("Processing")  # Includes session_id and agent
    """
    ctx = get_context()
    old_values = {k: ctx.get(k) for k in kwargs}
    ctx.update(kwargs)
    try:
        yield
    finally:
        for k, v in old_values.items():
            if v is None:
                ctx.pop(k, None)
            else:
                ctx[k] = v


@dataclass
class LogEntry:
    """A structured log entry."""
    timestamp: str
    level: str
    logger: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
        }
        if self.context:
            result["context"] = self.context
        if self.operation:
            result["operation"] = self.operation
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.request_id:
            result["request_id"] = self.request_id
        if self.error:
            result["error"] = self.error
        return result

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            context=getattr(record, "context", {}),
            operation=getattr(record, "operation", None),
            duration_ms=getattr(record, "duration_ms", None),
            request_id=getattr(record, "request_id", None),
            error=getattr(record, "error", None),
        )
        return entry.to_json()


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with color support."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        if self.use_color:
            color = self.COLORS.get(level, "")
            level_str = f"{color}{level:8}{self.RESET}"
        else:
            level_str = f"{level:8}"

        # Base message
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        msg = f"{timestamp} {level_str} [{record.name}] {record.getMessage()}"

        # Add context if present
        context = getattr(record, "context", {})
        if context:
            ctx_str = " ".join(f"{k}={v}" for k, v in context.items())
            msg += f" | {ctx_str}"

        # Add duration if present
        duration = getattr(record, "duration_ms", None)
        if duration is not None:
            msg += f" ({duration:.1f}ms)"

        # Add error info if present
        error = getattr(record, "error", None)
        if error:
            msg += f"\n  Error: {error.get('type', 'Unknown')}: {error.get('message', '')}"

        return msg


class StructuredLogger:
    """
    Logger wrapper that provides structured logging capabilities.

    This wraps the standard Python logger but adds:
    - Automatic context injection
    - Operation tracking with timing
    - Structured error formatting
    """

    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self._logger = logger

    def _log(
        self,
        level: int,
        message: str,
        error: Optional[Exception] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs,
    ) -> None:
        """Internal log method that adds structure."""
        # Merge thread context with kwargs
        context = {**get_context(), **kwargs}

        # Create log record with extra attributes
        extra = {
            "context": context,
            "operation": operation,
            "duration_ms": duration_ms,
            "request_id": context.get("request_id"),
            "error": None,
        }

        if error:
            extra["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
            # Include structured error info if available
            if hasattr(error, "to_dict"):
                extra["error"].update(error.to_dict())

        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception."""
        self._log(logging.ERROR, message, error=error, **kwargs)

    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message with optional exception."""
        self._log(logging.CRITICAL, message, error=error, **kwargs)

    @contextmanager
    def operation(self, name: str, **kwargs):
        """
        Context manager for tracking operations with timing.

        Usage:
            with logger.operation("build_document", path="doc.md"):
                # ... do work ...
            # Automatically logs completion with duration
        """
        start_time = time.perf_counter()
        self._log(logging.DEBUG, f"Starting {name}", operation=name, **kwargs)

        try:
            yield
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log(
                logging.DEBUG,
                f"Completed {name}",
                operation=name,
                duration_ms=duration_ms,
                **kwargs,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log(
                logging.ERROR,
                f"Failed {name}",
                error=e,
                operation=name,
                duration_ms=duration_ms,
                **kwargs,
            )
            raise


# Global configuration
_loggers: Dict[str, StructuredLogger] = {}
_root_logger: Optional[logging.Logger] = None
_log_level = logging.INFO
_output_format = "console"  # "console" or "json"
_log_file: Optional[Path] = None


def configure_logging(
    level: str = "INFO",
    output_format: str = "console",
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure the logging system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        output_format: Output format ("console" for human-readable, "json" for structured)
        log_file: Optional file path for logging output
    """
    global _log_level, _output_format, _log_file, _root_logger

    _log_level = getattr(logging, level.upper(), logging.INFO)
    _output_format = output_format
    _log_file = log_file

    # Configure root logger for media_engine
    _root_logger = logging.getLogger("media_engine")
    _root_logger.setLevel(_log_level)

    # Remove existing handlers
    _root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(_log_level)

    if output_format == "json":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())

    _root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(_log_level)
        file_handler.setFormatter(StructuredFormatter())  # Always JSON for files
        _root_logger.addHandler(file_handler)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger for a component.

    Args:
        name: Logger name (e.g., "documents", "build", "mcp.tools")

    Returns:
        StructuredLogger instance
    """
    global _root_logger

    if name in _loggers:
        return _loggers[name]

    # Ensure root logger is configured
    if _root_logger is None:
        configure_logging()

    # Create underlying logger
    full_name = f"media_engine.{name}" if not name.startswith("media_engine") else name
    logger = logging.getLogger(full_name)

    # Wrap in StructuredLogger
    structured = StructuredLogger(name, logger)
    _loggers[name] = structured

    return structured


# Decorator for logging function calls
F = TypeVar("F", bound=Callable[..., Any])


def log_operation(logger_name: str, operation_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator that logs function entry, exit, and timing.

    Usage:
        @log_operation("documents")
        def load_document(path: str) -> Document:
            ...

        @log_operation("build", "render_video")
        def render(script: Script) -> Video:
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            op_name = operation_name or func.__name__

            with logger.operation(op_name):
                return func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator


def log_async_operation(logger_name: str, operation_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator for async functions that logs entry, exit, and timing.

    Usage:
        @log_async_operation("mcp.tools")
        async def handle_request(request: Request) -> Response:
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            op_name = operation_name or func.__name__

            start_time = time.perf_counter()
            logger.debug(f"Starting {op_name}")

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.debug(f"Completed {op_name}", duration_ms=duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(f"Failed {op_name}", error=e, duration_ms=duration_ms)
                raise

        return wrapper  # type: ignore
    return decorator
