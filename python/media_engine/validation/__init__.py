"""
Media Engine Validation Module

Document validation:
- Schema validation for YAML frontmatter
- Reference and citation validation
- Cross-document link checking
"""

from .schema import (
    SchemaValidator,
    SchemaError,
    validate_frontmatter,
    load_schema,
)
from .references import (
    ReferenceValidator,
    ReferenceError,
    validate_references,
    validate_links,
)
from .validator import (
    ValidationReport,
    ValidationIssue,
    validate_project,
)

__all__ = [
    # Schema
    "SchemaValidator",
    "SchemaError",
    "validate_frontmatter",
    "load_schema",
    # References
    "ReferenceValidator",
    "ReferenceError",
    "validate_references",
    "validate_links",
    # Combined
    "ValidationReport",
    "ValidationIssue",
    "validate_project",
]
