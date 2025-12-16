"""
Combined Validation Module

Runs all validation checks and produces a unified report.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich import box

from .schema import SchemaValidator, SchemaError, validate_frontmatter
from .references import ReferenceValidator, ReferenceError, validate_references

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


@dataclass
class ValidationIssue:
    """A unified validation issue."""
    type: str  # schema, reference, link, citation
    severity: str  # error, warning
    file_path: Path
    line: Optional[int]
    message: str
    field: str = ""
    context: str = ""


@dataclass
class ValidationReport:
    """Complete validation report."""
    issues: List[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def schema_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.type == "schema"]

    @property
    def reference_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.type in ("reference", "link", "citation")]

    def add_schema_error(self, error: SchemaError, severity: str = "error"):
        """Add a schema validation error."""
        self.issues.append(ValidationIssue(
            type="schema",
            severity=severity,
            file_path=error.file_path,
            line=None,
            message=error.message,
            field=error.field,
        ))
        if severity == "error":
            self.passed = False

    def add_reference_error(self, error: ReferenceError, severity: str = "warning"):
        """Add a reference validation error."""
        self.issues.append(ValidationIssue(
            type=error.error_type,
            severity=severity,
            file_path=error.file_path,
            line=error.line,
            message=error.message,
            context=error.context,
        ))
        if severity == "error":
            self.passed = False


def validate_project(
    project: "Project",
    schema_path: Optional[Path] = None,
    console_output: bool = True,
) -> ValidationReport:
    """
    Run all validation checks on a project.

    Args:
        project: Project to validate
        schema_path: Path to custom schema file
        console_output: Whether to print progress

    Returns:
        ValidationReport with all issues
    """
    from ..cms import Document

    report = ValidationReport()

    if console_output:
        console.print("\n[bold]Running validation checks...[/bold]\n")

    # Load schema if provided
    schema = None
    if schema_path and schema_path.exists():
        import yaml
        with open(schema_path) as f:
            schema = yaml.safe_load(f)

    # Validate all documents
    for language in project.languages:
        for chapter_path in project.list_chapters(language):
            report.files_checked += 1

            try:
                doc = Document.load(chapter_path)

                # Schema validation
                schema_errors = validate_frontmatter(
                    doc.frontmatter,
                    schema,
                    chapter_path,
                )
                for error in schema_errors:
                    report.add_schema_error(error)

            except Exception as e:
                report.issues.append(ValidationIssue(
                    type="parse",
                    severity="error",
                    file_path=chapter_path,
                    line=None,
                    message=f"Failed to parse document: {e}",
                ))
                report.passed = False

    # Reference validation
    ref_errors = validate_references(project, console_output=False)
    for error in ref_errors:
        # Broken links are warnings, missing citations are errors
        severity = "error" if error.error_type == "missing_citation" else "warning"
        report.add_reference_error(error, severity)

    if console_output:
        print_validation_report(report)

    return report


def print_validation_report(report: ValidationReport):
    """Print validation report to console."""
    console.print(f"[bold]Validation Report[/bold]")
    console.print(f"Files checked: {report.files_checked}")
    console.print(f"Issues found: {len(report.issues)} ({report.error_count} errors, {report.warning_count} warnings)")
    console.print()

    if not report.issues:
        console.print("[green]✓ All validations passed[/green]")
        return

    # Group issues by type
    schema_issues = report.schema_issues
    ref_issues = report.reference_issues

    if schema_issues:
        console.print("[bold]Schema Issues[/bold]")
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("File", style="cyan", width=30)
        table.add_column("Field", width=20)
        table.add_column("Message")

        for issue in schema_issues:
            severity_color = "red" if issue.severity == "error" else "yellow"
            table.add_row(
                issue.file_path.name,
                issue.field or "–",
                f"[{severity_color}]{issue.message}[/{severity_color}]",
            )

        console.print(table)
        console.print()

    if ref_issues:
        console.print("[bold]Reference Issues[/bold]")
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("File", style="cyan", width=25)
        table.add_column("Line", justify="right", width=6)
        table.add_column("Type", width=15)
        table.add_column("Message")

        for issue in ref_issues:
            severity_color = "red" if issue.severity == "error" else "yellow"
            table.add_row(
                issue.file_path.name,
                str(issue.line) if issue.line else "–",
                issue.type,
                f"[{severity_color}]{issue.message}[/{severity_color}]",
            )

        console.print(table)
        console.print()

    if report.passed:
        console.print("[green]✓ Validation passed (warnings only)[/green]")
    else:
        console.print(f"[red]✗ Validation failed ({report.error_count} errors)[/red]")
