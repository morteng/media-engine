"""
Quality and validation routes.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


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
