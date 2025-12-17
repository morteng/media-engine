"""Validate command - run validation checks."""

import json
import sys
from pathlib import Path

from rich.console import Console

from ...core import find_project

console = Console()


def cmd_validate(args):
    """Run validation checks on project."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...validation import validate_project, validate_references

    # Determine schema path
    schema_path = None
    if args.schema:
        schema_path = Path(args.schema)
        if not schema_path.exists():
            console.print(f"[red]Schema file not found: {schema_path}[/red]")
            sys.exit(1)

    if args.refs_only:
        # Only check references
        errors = validate_references(project, console_output=True)
        if errors and not args.json:
            sys.exit(1)
        return

    # Full validation
    report = validate_project(project, schema_path, console_output=not args.json)

    if args.json:
        output = {
            "passed": report.passed,
            "files_checked": report.files_checked,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "issues": [
                {
                    "type": i.type,
                    "severity": i.severity,
                    "file": str(i.file_path),
                    "line": i.line,
                    "message": i.message,
                    "field": i.field,
                }
                for i in report.issues
            ],
        }
        print(json.dumps(output, indent=2))

    if not report.passed:
        sys.exit(1)
