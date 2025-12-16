"""
Media Engine Quality Module

Quality checks for content:
- Placeholder detection (TODO, TBD, FIXME)
- Terminology consistency
- Encoding validation (Norwegian characters)
- Reference validation
"""

from .checks import (
    QualityIssue,
    QualityReport,
    check_encoding,
    check_placeholders,
    check_terminology,
    run_quality_checks,
)

__all__ = [
    "check_placeholders",
    "check_terminology",
    "check_encoding",
    "run_quality_checks",
    "QualityIssue",
    "QualityReport",
]
