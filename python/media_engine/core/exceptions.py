"""
Media Engine Exception Hierarchy

Provides structured exceptions that agents can parse and recover from.
Each exception includes:
- error_code: Machine-readable identifier
- recoverable: Whether the agent can potentially fix this
- suggestions: List of actions the agent can take
- context: Additional data for debugging

Usage:
    from media_engine.core.exceptions import DocumentNotFoundError

    try:
        document = load_document(path)
    except DocumentNotFoundError as e:
        print(e.to_dict())  # Structured error for agent consumption
        if e.recoverable:
            # Try suggested actions
            for suggestion in e.suggestions:
                print(f"Try: {suggestion}")
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaEngineError(Exception):
    """
    Base exception for all Media Engine errors.

    Provides structured error information that agents can parse and act on.
    """

    message: str
    error_code: str = "MEDIA_ENGINE_ERROR"
    recoverable: bool = False
    suggestions: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, code={self.error_code!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": self.error_code,
            "message": self.message,
            "recoverable": self.recoverable,
            "suggestions": self.suggestions,
            "context": self.context,
            "type": self.__class__.__name__,
        }


# =============================================================================
# Configuration Errors
# =============================================================================


@dataclass
class ConfigurationError(MediaEngineError):
    """Base class for configuration-related errors."""

    error_code: str = "CONFIGURATION_ERROR"


@dataclass
class ProjectNotFoundError(ConfigurationError):
    """No project.yaml found in directory tree."""

    error_code: str = "PROJECT_NOT_FOUND"
    recoverable: bool = True
    search_path: str = ""

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                "Run 'media-engine init' to create a new project",
                "Navigate to a directory containing project.yaml",
                f"Check if project.yaml exists in {self.search_path or 'current directory'}",
            ]
        self.context["search_path"] = self.search_path


@dataclass
class InvalidConfigError(ConfigurationError):
    """Configuration file is invalid or malformed."""

    error_code: str = "INVALID_CONFIG"
    config_file: str = ""
    validation_errors: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                f"Check {self.config_file} for YAML syntax errors",
                "Validate against the schema with 'media-engine validate'",
                "See documentation for required fields",
            ]
        self.context["config_file"] = self.config_file
        self.context["validation_errors"] = self.validation_errors


@dataclass
class MissingDependencyError(ConfigurationError):
    """Optional dependency not installed."""

    error_code: str = "MISSING_DEPENDENCY"
    recoverable: bool = True
    package: str = ""
    feature: str = ""
    install_command: str = ""

    def __post_init__(self):
        if not self.suggestions and self.install_command:
            self.suggestions = [
                f"Install with: {self.install_command}",
                f"This is required for: {self.feature}",
            ]
        self.context["package"] = self.package
        self.context["feature"] = self.feature


# =============================================================================
# Document Errors
# =============================================================================


@dataclass
class DocumentError(MediaEngineError):
    """Base class for document-related errors."""

    error_code: str = "DOCUMENT_ERROR"
    path: str = ""

    def __post_init__(self):
        self.context["path"] = self.path


@dataclass
class DocumentNotFoundError(DocumentError):
    """Document does not exist at specified path."""

    error_code: str = "DOCUMENT_NOT_FOUND"
    recoverable: bool = True
    available_documents: list[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                "Verify the document path is correct",
                "Use list_documents() to see available documents",
                "Check if the document was moved or renamed",
            ]
            if self.available_documents:
                similar = [d for d in self.available_documents if self.path.split("/")[-1] in d]
                if similar:
                    self.suggestions.append(f"Did you mean: {similar[0]}?")
        self.context["available_documents"] = self.available_documents[:10]  # Limit size


@dataclass
class DocumentLockedError(DocumentError):
    """Document is locked by another session."""

    error_code: str = "DOCUMENT_LOCKED"
    recoverable: bool = True
    locked_by: str = ""
    lock_expires: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Wait for lock to expire (expires: {self.lock_expires})",
                f"Contact session owner: {self.locked_by}",
                "Use force_unlock() if you have permission",
                "Work on a different document instead",
            ]
        self.context["locked_by"] = self.locked_by
        self.context["lock_expires"] = self.lock_expires


@dataclass
class DocumentValidationError(DocumentError):
    """Document content failed validation."""

    error_code: str = "DOCUMENT_VALIDATION_ERROR"
    recoverable: bool = True
    validation_errors: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                "Review validation errors in context",
                "Fix frontmatter issues first",
                "Run 'media-engine validate' for detailed report",
            ]
        self.context["validation_errors"] = self.validation_errors


@dataclass
class DocumentParseError(DocumentError):
    """Document could not be parsed (invalid YAML, markdown, etc.)."""

    error_code: str = "DOCUMENT_PARSE_ERROR"
    line_number: int = 0
    parse_error: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Check line {self.line_number} for syntax errors" if self.line_number else "Check document syntax",
                "Validate YAML frontmatter",
                "Ensure proper markdown formatting",
            ]
        self.context["line_number"] = self.line_number
        self.context["parse_error"] = self.parse_error


# =============================================================================
# Build Errors
# =============================================================================


@dataclass
class BuildError(MediaEngineError):
    """Base class for build-related errors."""

    error_code: str = "BUILD_ERROR"
    output_format: str = ""
    publication: str = ""

    def __post_init__(self):
        self.context["output_format"] = self.output_format
        self.context["publication"] = self.publication


@dataclass
class BuildDependencyError(BuildError):
    """Build failed due to missing dependency."""

    error_code: str = "BUILD_DEPENDENCY_ERROR"
    recoverable: bool = True
    missing_asset: str = ""
    referenced_by: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Create or add missing asset: {self.missing_asset}",
                f"Update reference in: {self.referenced_by}",
                "Run 'media-engine links' to find all broken references",
            ]
        self.context["missing_asset"] = self.missing_asset
        self.context["referenced_by"] = self.referenced_by


@dataclass
class BuildOutputError(BuildError):
    """Failed to write build output."""

    error_code: str = "BUILD_OUTPUT_ERROR"
    output_path: str = ""
    reason: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Check write permissions for: {self.output_path}",
                "Ensure output directory exists",
                "Check available disk space",
            ]
        self.context["output_path"] = self.output_path
        self.context["reason"] = self.reason


# =============================================================================
# Session/Agent Errors
# =============================================================================


@dataclass
class SessionError(MediaEngineError):
    """Base class for AI session errors."""

    error_code: str = "SESSION_ERROR"
    session_id: str = ""

    def __post_init__(self):
        self.context["session_id"] = self.session_id


@dataclass
class SessionNotFoundError(SessionError):
    """Session does not exist."""

    error_code: str = "SESSION_NOT_FOUND"
    recoverable: bool = True
    active_sessions: list[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                "Start a new session with start_ai_session()",
                "List active sessions with get_agent_status()",
            ]
            if self.active_sessions:
                self.suggestions.append(f"Active sessions: {', '.join(self.active_sessions[:5])}")
        self.context["active_sessions"] = self.active_sessions


@dataclass
class SessionConflictError(SessionError):
    """Session conflict - concurrent modification detected."""

    error_code: str = "SESSION_CONFLICT"
    recoverable: bool = True
    conflicting_session: str = ""
    conflicting_document: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Wait for session {self.conflicting_session} to complete",
                f"Work on a different document than {self.conflicting_document}",
                "Use acquire_document_lock() before modifying",
            ]
        self.context["conflicting_session"] = self.conflicting_session
        self.context["conflicting_document"] = self.conflicting_document


@dataclass
class CheckpointError(SessionError):
    """Checkpoint operation failed."""

    error_code: str = "CHECKPOINT_ERROR"
    checkpoint_id: str = ""
    operation: str = ""  # create, rollback, delete

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                "List available checkpoints with list_checkpoints()",
                "Create a new checkpoint before risky operations",
            ]
        self.context["checkpoint_id"] = self.checkpoint_id
        self.context["operation"] = self.operation


# =============================================================================
# Translation Errors
# =============================================================================


@dataclass
class TranslationError(MediaEngineError):
    """Base class for translation-related errors."""

    error_code: str = "TRANSLATION_ERROR"
    source_language: str = ""
    target_language: str = ""

    def __post_init__(self):
        self.context["source_language"] = self.source_language
        self.context["target_language"] = self.target_language


@dataclass
class TranslationOutdatedError(TranslationError):
    """Translation is outdated relative to source."""

    error_code: str = "TRANSLATION_OUTDATED"
    recoverable: bool = True
    source_path: str = ""
    translation_path: str = ""
    source_hash: str = ""
    translation_hash: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Update translation: {self.translation_path}",
                "Run 'media-engine translation sync' to sync all",
                "Review source changes since last translation",
            ]
        self.context["source_path"] = self.source_path
        self.context["translation_path"] = self.translation_path


@dataclass
class TranslationMissingError(TranslationError):
    """Translation does not exist for source document."""

    error_code: str = "TRANSLATION_MISSING"
    recoverable: bool = True
    source_path: str = ""
    expected_path: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.suggestions:
            self.suggestions = [
                f"Create translation at: {self.expected_path}",
                f"Run 'media-engine translation sync --lang {self.target_language}'",
            ]
        self.context["source_path"] = self.source_path
        self.context["expected_path"] = self.expected_path


# =============================================================================
# Quality/Validation Errors
# =============================================================================


@dataclass
class QualityError(MediaEngineError):
    """Base class for quality check errors."""

    error_code: str = "QUALITY_ERROR"


@dataclass
class SecurityViolationError(QualityError):
    """Security issue detected (secrets, PII, etc.)."""

    error_code: str = "SECURITY_VIOLATION"
    recoverable: bool = True
    violation_type: str = ""  # secret, pii, api_key
    file_path: str = ""
    line_number: int = 0
    severity: str = "high"

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                f"Remove {self.violation_type} from {self.file_path}:{self.line_number}",
                "Use environment variables for secrets",
                "Run 'media-engine security' for full scan",
            ]
        self.context["violation_type"] = self.violation_type
        self.context["file_path"] = self.file_path
        self.context["line_number"] = self.line_number
        self.context["severity"] = self.severity


@dataclass
class LinkValidationError(QualityError):
    """Broken link detected."""

    error_code: str = "LINK_VALIDATION_ERROR"
    recoverable: bool = True
    link_url: str = ""
    source_file: str = ""
    link_type: str = ""  # internal, external, asset

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                f"Fix or remove broken link: {self.link_url}",
                f"Check if target exists for {self.link_type} link",
                "Run 'media-engine links' for all broken links",
            ]
        self.context["link_url"] = self.link_url
        self.context["source_file"] = self.source_file
        self.context["link_type"] = self.link_type


# =============================================================================
# Approval/Workflow Errors
# =============================================================================


@dataclass
class ApprovalError(MediaEngineError):
    """Base class for approval workflow errors."""

    error_code: str = "APPROVAL_ERROR"


@dataclass
class ApprovalRequiredError(ApprovalError):
    """Action requires human approval before proceeding."""

    error_code: str = "APPROVAL_REQUIRED"
    recoverable: bool = True
    action: str = ""
    approval_id: str = ""
    reason: str = ""

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                f"Request approval with request_approval(action='{self.action}')",
                f"Wait for human to approve request: {self.approval_id}",
                "Check pending approvals with get_pending_approvals()",
            ]
        self.context["action"] = self.action
        self.context["approval_id"] = self.approval_id
        self.context["reason"] = self.reason


@dataclass
class ApprovalRejectedError(ApprovalError):
    """Human rejected the requested action."""

    error_code: str = "APPROVAL_REJECTED"
    recoverable: bool = True
    action: str = ""
    rejection_reason: str = ""
    rejector: str = ""

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                f"Review rejection reason: {self.rejection_reason}",
                "Modify approach based on feedback",
                "Request approval with different parameters",
            ]
        self.context["action"] = self.action
        self.context["rejection_reason"] = self.rejection_reason
        self.context["rejector"] = self.rejector


@dataclass
class ApprovalTimeoutError(ApprovalError):
    """Approval request timed out."""

    error_code: str = "APPROVAL_TIMEOUT"
    recoverable: bool = True
    approval_id: str = ""
    timeout_minutes: int = 0

    def __post_init__(self):
        if not self.suggestions:
            self.suggestions = [
                "Resubmit approval request",
                "Try a longer timeout",
                "Check if approver is available",
            ]
        self.context["approval_id"] = self.approval_id
        self.context["timeout_minutes"] = self.timeout_minutes


# =============================================================================
# Utility Functions
# =============================================================================


def error_from_dict(data: dict[str, Any]) -> MediaEngineError:
    """
    Reconstruct an exception from its dictionary representation.

    Useful for deserializing errors from JSON responses.
    """
    error_classes = {
        "PROJECT_NOT_FOUND": ProjectNotFoundError,
        "INVALID_CONFIG": InvalidConfigError,
        "MISSING_DEPENDENCY": MissingDependencyError,
        "DOCUMENT_NOT_FOUND": DocumentNotFoundError,
        "DOCUMENT_LOCKED": DocumentLockedError,
        "DOCUMENT_VALIDATION_ERROR": DocumentValidationError,
        "DOCUMENT_PARSE_ERROR": DocumentParseError,
        "BUILD_DEPENDENCY_ERROR": BuildDependencyError,
        "BUILD_OUTPUT_ERROR": BuildOutputError,
        "SESSION_NOT_FOUND": SessionNotFoundError,
        "SESSION_CONFLICT": SessionConflictError,
        "CHECKPOINT_ERROR": CheckpointError,
        "TRANSLATION_OUTDATED": TranslationOutdatedError,
        "TRANSLATION_MISSING": TranslationMissingError,
        "SECURITY_VIOLATION": SecurityViolationError,
        "LINK_VALIDATION_ERROR": LinkValidationError,
        "APPROVAL_REQUIRED": ApprovalRequiredError,
        "APPROVAL_REJECTED": ApprovalRejectedError,
        "APPROVAL_TIMEOUT": ApprovalTimeoutError,
    }

    error_code = data.get("error", "MEDIA_ENGINE_ERROR")
    error_class = error_classes.get(error_code, MediaEngineError)

    return error_class(
        message=data.get("message", "Unknown error"),
        error_code=error_code,
        recoverable=data.get("recoverable", False),
        suggestions=data.get("suggestions", []),
        context=data.get("context", {}),
    )


def is_recoverable(error: Exception) -> bool:
    """Check if an error is potentially recoverable by an agent."""
    if isinstance(error, MediaEngineError):
        return error.recoverable
    return False


def get_error_suggestions(error: Exception) -> list[str]:
    """Get recovery suggestions for an error."""
    if isinstance(error, MediaEngineError):
        return error.suggestions
    return []
