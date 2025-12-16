"""
Media Engine Validation Module

Document validation:
- Schema validation for YAML frontmatter
- Reference and citation validation
- Cross-document link checking
"""

from .references import (
    ReferenceError,
    ReferenceValidator,
    validate_links,
    validate_references,
)
from .schema import (
    SchemaError,
    SchemaValidator,
    load_schema,
    validate_frontmatter,
)
from .validator import (
    ValidationIssue,
    ValidationReport,
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
