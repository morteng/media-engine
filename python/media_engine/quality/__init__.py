"""
Media Engine Quality Module

Quality checks for content:
- Placeholder detection (TODO, TBD, FIXME)
- Terminology consistency
- Encoding validation (Norwegian characters)
- Reference validation
- Voice/tone consistency (brand guidelines)
"""

from .checks import (
    QualityIssue,
    QualityReport,
    check_encoding,
    check_placeholders,
    check_terminology,
    check_voice,
    run_quality_checks,
)

__all__ = [
    "check_placeholders",
    "check_terminology",
    "check_encoding",
    "check_voice",
    "run_quality_checks",
    "QualityIssue",
    "QualityReport",
]
