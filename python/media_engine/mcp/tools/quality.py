"""Quality and validation tools."""

import json


def register_quality_tools(mcp, server_instance):
    """Register quality-related MCP tools."""

    @mcp.tool()
    async def quality_check() -> str:
        """
        Run quality checks on the project.

        Checks for placeholders, encoding issues, stale content,
        terminology consistency, and more.
        """
        from ...quality import run_quality_checks

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        report = run_quality_checks(server_instance.project, console_output=False)

        return json.dumps(
            {
                "summary": {
                    "total": report.total_count,
                    "errors": report.error_count,
                    "warnings": report.warning_count,
                    "info": report.info_count,
                    "passed": report.error_count == 0,
                },
                "issues": [
                    {
                        "severity": i.severity,
                        "category": i.category,
                        "message": i.message,
                        "file": str(i.file_path) if i.file_path else None,
                        "line": i.line,
                    }
                    for i in report.issues
                ],
            },
            indent=2,
        )

    @mcp.tool()
    async def validate_project() -> str:
        """
        Validate project against schema.

        Checks frontmatter fields, references, and structure
        against schema.yaml rules.
        """
        from ...validation import validate_project as do_validate

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        schema_path = server_instance.project.root / "schema.yaml"
        report = do_validate(
            server_instance.project,
            schema_path if schema_path.exists() else None,
            console_output=False,
        )

        return json.dumps(
            {
                "valid": report.error_count == 0,
                "schema_used": str(schema_path) if schema_path.exists() else None,
                "summary": {
                    "total": report.total_count,
                    "errors": report.error_count,
                    "warnings": report.warning_count,
                },
                "issues": [
                    {
                        "severity": i.severity,
                        "message": i.message,
                        "file": str(i.file_path) if i.file_path else None,
                    }
                    for i in report.issues
                ],
            },
            indent=2,
        )
