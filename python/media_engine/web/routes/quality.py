"""
Quality and validation routes.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def _get_cached_or_compute(key: str, compute_fn, max_age: float = 300):
    """Helper to get cached data or compute it, then cache the result."""
    import time

    from ..preprocessor import get_preprocessor

    preprocessor = get_preprocessor()
    if preprocessor:
        cached = preprocessor.get_cached(key, max_age_seconds=max_age)
        if cached is not None:
            return cached

    # Compute the result
    start = time.time()
    result = compute_fn()
    elapsed_ms = (time.time() - start) * 1000

    # Store in cache for next time
    if preprocessor:
        preprocessor.cache.set(key, result, computation_time_ms=elapsed_ms)

    return result


def register_quality_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register quality and validation routes."""
    from ...quality import run_quality_checks
    from ...validation import validate_project

    @router.get("/api/quality")
    async def get_quality():
        """Run quality checks and return report."""
        project = get_project()

        def compute_quality():
            report = run_quality_checks(project, console_output=False)
            return {
                "total": len(report.issues),
                "errors": report.error_count,
                "warnings": report.warning_count,
                "info": len(report.issues) - report.error_count - report.warning_count,
                "issues": [
                    {
                        "severity": i.severity,
                        "category": i.type,
                        "message": i.message,
                        "file": str(i.file_path) if i.file_path else None,
                        "line": i.line,
                    }
                    for i in report.issues
                ],
            }

        return _get_cached_or_compute("quality", compute_quality, max_age=300)

    @router.get("/api/validation")
    async def get_validation():
        """Validate project and return report."""
        project = get_project()
        schema_path = project.root / "schema.yaml"

        report = validate_project(
            project,
            schema_path if schema_path.exists() else None,
            console_output=False,
        )

        return {
            "valid": report.error_count == 0,
            "total": len(report.issues),
            "errors": report.error_count,
            "warnings": report.warning_count,
            "issues": [
                {
                    "severity": i.severity,
                    "message": i.message,
                    "file": str(i.file_path) if i.file_path else None,
                }
                for i in report.issues
            ],
        }
