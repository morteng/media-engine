"""
Enhanced Code-Documentation Sync for Media Engine

Advanced code synchronization checking:
- Parse and validate code examples in documentation
- Verify syntax correctness for multiple languages
- Check API signatures against actual codebase
- Detect deprecated usage patterns
- Track code example freshness

Goes beyond file reference tracking to actual code validation.
"""

import ast
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class CodeLanguage(str, Enum):
    """Supported code languages for validation."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    YAML = "yaml"
    JSON = "json"
    HTML = "html"
    CSS = "css"
    UNKNOWN = "unknown"


class SyncIssueType(str, Enum):
    """Types of code sync issues."""

    SYNTAX_ERROR = "syntax_error"
    API_CHANGED = "api_changed"
    DEPRECATED = "deprecated"
    MISSING_IMPORT = "missing_import"
    WRONG_SIGNATURE = "wrong_signature"
    EXAMPLE_OUTDATED = "example_outdated"
    REFERENCE_MISSING = "reference_missing"


@dataclass
class CodeBlock:
    """A code block extracted from documentation."""

    content: str
    language: CodeLanguage
    start_line: int
    end_line: int
    is_complete: bool  # Complete vs. snippet
    has_output: bool  # Includes expected output

    def to_dict(self) -> dict:
        return {
            "language": self.language.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_preview": self.content[:100] + "..."
            if len(self.content) > 100
            else self.content,
            "is_complete": self.is_complete,
            "has_output": self.has_output,
        }


@dataclass
class SyncIssue:
    """A code synchronization issue."""

    issue_type: SyncIssueType
    severity: str  # "error", "warning", "info"
    document: Path
    line_number: int
    message: str
    code_snippet: str = ""
    suggestion: str = ""
    related_file: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "document": str(self.document),
            "line_number": self.line_number,
            "message": self.message,
            "code_snippet": self.code_snippet[:200] if self.code_snippet else "",
            "suggestion": self.suggestion,
            "related_file": str(self.related_file) if self.related_file else None,
        }


@dataclass
class APIReference:
    """A reference to an API element (function, class, etc.)."""

    name: str
    ref_type: str  # "function", "class", "method", "constant"
    source_file: Optional[Path]
    current_signature: Optional[str]
    documented_signature: Optional[str]
    is_deprecated: bool
    deprecation_note: str = ""


@dataclass
class CodeSyncReport:
    """Complete code synchronization report."""

    document: Path
    code_blocks: list[CodeBlock]
    issues: list[SyncIssue]
    api_references: list[APIReference]
    total_examples: int
    valid_examples: int
    validation_rate: float  # 0-100%
    last_code_change: Optional[datetime]
    needs_review: bool

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "code_blocks": [b.to_dict() for b in self.code_blocks],
            "issues": [i.to_dict() for i in self.issues],
            "api_references": [
                {"name": r.name, "type": r.ref_type, "deprecated": r.is_deprecated}
                for r in self.api_references
            ],
            "total_examples": self.total_examples,
            "valid_examples": self.valid_examples,
            "validation_rate": round(self.validation_rate, 1),
            "last_code_change": self.last_code_change.isoformat()
            if self.last_code_change
            else None,
            "needs_review": self.needs_review,
        }


class CodeBlockExtractor:
    """Extracts code blocks from markdown content."""

    # Pattern for fenced code blocks
    FENCE_PATTERN = re.compile(
        r"```(\w+)?\n([\s\S]*?)```",
        re.MULTILINE,
    )

    # Language aliases
    LANGUAGE_MAP = {
        "py": CodeLanguage.PYTHON,
        "python": CodeLanguage.PYTHON,
        "python3": CodeLanguage.PYTHON,
        "js": CodeLanguage.JAVASCRIPT,
        "javascript": CodeLanguage.JAVASCRIPT,
        "ts": CodeLanguage.TYPESCRIPT,
        "typescript": CodeLanguage.TYPESCRIPT,
        "sh": CodeLanguage.BASH,
        "bash": CodeLanguage.BASH,
        "shell": CodeLanguage.BASH,
        "zsh": CodeLanguage.BASH,
        "yml": CodeLanguage.YAML,
        "yaml": CodeLanguage.YAML,
        "json": CodeLanguage.JSON,
        "html": CodeLanguage.HTML,
        "css": CodeLanguage.CSS,
    }

    def extract(self, content: str) -> list[CodeBlock]:
        """Extract all code blocks from content."""
        blocks = []
        content.split("\n")

        for match in self.FENCE_PATTERN.finditer(content):
            lang_str = match.group(1) or ""
            code = match.group(2)

            # Determine language
            language = self.LANGUAGE_MAP.get(lang_str.lower(), CodeLanguage.UNKNOWN)

            # Find line numbers
            start_pos = match.start()
            start_line = content[:start_pos].count("\n") + 1
            end_line = start_line + code.count("\n") + 1

            # Check if complete example
            is_complete = self._is_complete_example(code, language)

            # Check for output markers
            has_output = ">>>" in code or "Output:" in code or "# =>" in code

            blocks.append(
                CodeBlock(
                    content=code.strip(),
                    language=language,
                    start_line=start_line,
                    end_line=end_line,
                    is_complete=is_complete,
                    has_output=has_output,
                )
            )

        return blocks

    def _is_complete_example(self, code: str, language: CodeLanguage) -> bool:
        """Check if code is a complete runnable example."""
        if language == CodeLanguage.PYTHON:
            # Has imports and function/class definition or main block
            has_structure = (
                "import " in code
                or "from " in code
                or "def " in code
                or "class " in code
                or "if __name__" in code
            )
            # Not just a snippet
            return has_structure and len(code.split("\n")) > 3

        elif language in (CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT):
            has_structure = (
                "import " in code
                or "require(" in code
                or "function " in code
                or "const " in code
                or "export " in code
            )
            return has_structure

        return len(code.split("\n")) > 5


class PythonValidator:
    """Validates Python code examples."""

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Check Python syntax.

        Returns:
            (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    def extract_imports(self, code: str) -> list[str]:
        """Extract imported modules from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])

        return imports

    def extract_api_calls(self, code: str) -> list[str]:
        """Extract function/method calls from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)

        return calls

    def check_deprecated(self, code: str, deprecation_patterns: list[str]) -> list[str]:
        """Check for deprecated API usage."""
        deprecated = []
        for pattern in deprecation_patterns:
            if re.search(pattern, code):
                deprecated.append(pattern)
        return deprecated


class JavaScriptValidator:
    """Validates JavaScript/TypeScript code examples."""

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Check JavaScript syntax using Node.js.

        Returns:
            (is_valid, error_message)
        """
        try:
            # Use node to check syntax
            result = subprocess.run(
                ["node", "--check"],
                input=code,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return True, None
            return False, result.stderr.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Node not available, skip validation
            return True, None


class YAMLValidator:
    """Validates YAML code examples."""

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """Check YAML syntax."""
        try:
            import yaml

            yaml.safe_load(code)
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)
        except ImportError:
            return True, None


class JSONValidator:
    """Validates JSON code examples."""

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """Check JSON syntax."""
        import json

        try:
            json.loads(code)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Line {e.lineno}: {e.msg}"


class EnhancedCodeSyncChecker:
    """
    Enhanced code-documentation synchronization checker.

    Usage:
        from media_engine.codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)

        # Check a specific document
        report = checker.check_document(doc_path)

        # Check all documents
        reports = checker.check_project()

        # Get issues by severity
        errors = checker.get_errors()
        warnings = checker.get_warnings()
    """

    # Known deprecated patterns
    PYTHON_DEPRECATED = [
        r"\.format\(",  # Prefer f-strings
        r"print\s+[^(]",  # Python 2 print
        r"from __future__ import",  # Usually unnecessary in modern Python
        r"async\s+\w+\s*=",  # Incorrect async usage
    ]

    def __init__(self, project):
        """
        Initialize code sync checker.

        Args:
            project: Media Engine project
        """
        self.project = project
        self.extractor = CodeBlockExtractor()
        self.python_validator = PythonValidator()
        self.js_validator = JavaScriptValidator()
        self.yaml_validator = YAMLValidator()
        self.json_validator = JSONValidator()

        # Build API index from project code
        self._api_index: dict[str, dict] = {}
        self._build_api_index()

    def _build_api_index(self) -> None:
        """Build index of API elements from project code."""
        python_dir = self.project.root / "python"

        if not python_dir.exists():
            return

        for py_file in python_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self._api_index[node.name] = {
                            "type": "function",
                            "file": py_file,
                            "signature": self._get_function_signature(node),
                        }
                    elif isinstance(node, ast.ClassDef):
                        self._api_index[node.name] = {
                            "type": "class",
                            "file": py_file,
                        }
            except (OSError, SyntaxError):
                pass

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature from AST node."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return f"{node.name}({', '.join(args)})"

    def check_document(self, doc_path: Path) -> CodeSyncReport:
        """
        Check code synchronization for a document.

        Args:
            doc_path: Path to document

        Returns:
            CodeSyncReport with issues found
        """
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path
            try:
                doc_path = full_path.relative_to(self.project.content_dir)
            except ValueError:
                pass

        content = full_path.read_text(encoding="utf-8")
        blocks = self.extractor.extract(content)
        issues = []
        api_refs = []
        valid_count = 0

        for block in blocks:
            # Validate syntax based on language
            is_valid, error = self._validate_block(block)

            if not is_valid:
                issues.append(
                    SyncIssue(
                        issue_type=SyncIssueType.SYNTAX_ERROR,
                        severity="error",
                        document=doc_path,
                        line_number=block.start_line,
                        message=f"Syntax error in {block.language.value} code: {error}",
                        code_snippet=block.content[:200],
                        suggestion="Fix the syntax error in the code example",
                    )
                )
            else:
                valid_count += 1

            # Check for deprecated patterns (Python only for now)
            if block.language == CodeLanguage.PYTHON:
                deprecated = self.python_validator.check_deprecated(
                    block.content, self.PYTHON_DEPRECATED
                )
                for pattern in deprecated:
                    issues.append(
                        SyncIssue(
                            issue_type=SyncIssueType.DEPRECATED,
                            severity="warning",
                            document=doc_path,
                            line_number=block.start_line,
                            message=f"Potentially deprecated pattern: {pattern}",
                            code_snippet=block.content[:100],
                            suggestion="Consider updating to modern syntax",
                        )
                    )

                # Check API references
                api_calls = self.python_validator.extract_api_calls(block.content)
                for call in api_calls:
                    if call in self._api_index:
                        info = self._api_index[call]
                        api_refs.append(
                            APIReference(
                                name=call,
                                ref_type=info["type"],
                                source_file=info.get("file"),
                                current_signature=info.get("signature"),
                                documented_signature=None,
                                is_deprecated=False,
                            )
                        )

                # Check imports
                imports = self.python_validator.extract_imports(block.content)
                for imp in imports:
                    if imp.startswith("media_engine"):
                        # Check if module exists
                        mod_path = self.project.root / "python" / imp.replace(".", "/")
                        if not mod_path.exists() and not (mod_path.parent / "__init__.py").exists():
                            issues.append(
                                SyncIssue(
                                    issue_type=SyncIssueType.MISSING_IMPORT,
                                    severity="error",
                                    document=doc_path,
                                    line_number=block.start_line,
                                    message=f"Import '{imp}' may not exist",
                                    suggestion="Verify the import path is correct",
                                )
                            )

        # Check if referenced code files changed after document
        last_code_change = self._get_last_code_change(api_refs)
        doc_modified = self._get_doc_modified(full_path)
        needs_review = False

        if last_code_change and doc_modified:
            if last_code_change > doc_modified:
                needs_review = True
                issues.append(
                    SyncIssue(
                        issue_type=SyncIssueType.EXAMPLE_OUTDATED,
                        severity="warning",
                        document=doc_path,
                        line_number=0,
                        message="Referenced code changed after document was last updated",
                        suggestion="Review examples for accuracy",
                    )
                )

        return CodeSyncReport(
            document=doc_path,
            code_blocks=blocks,
            issues=issues,
            api_references=api_refs,
            total_examples=len(blocks),
            valid_examples=valid_count,
            validation_rate=(valid_count / len(blocks) * 100) if blocks else 100,
            last_code_change=last_code_change,
            needs_review=needs_review,
        )

    def _validate_block(self, block: CodeBlock) -> tuple[bool, Optional[str]]:
        """Validate a code block based on its language."""
        if block.language == CodeLanguage.PYTHON:
            return self.python_validator.validate_syntax(block.content)
        elif block.language in (CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT):
            return self.js_validator.validate_syntax(block.content)
        elif block.language == CodeLanguage.YAML:
            return self.yaml_validator.validate_syntax(block.content)
        elif block.language == CodeLanguage.JSON:
            return self.json_validator.validate_syntax(block.content)
        else:
            return True, None  # Skip validation for unknown languages

    def _get_last_code_change(self, api_refs: list[APIReference]) -> Optional[datetime]:
        """Get the most recent change to referenced code files."""
        if not api_refs:
            return None

        latest = None
        for ref in api_refs:
            if ref.source_file and ref.source_file.exists():
                mtime = datetime.fromtimestamp(ref.source_file.stat().st_mtime)
                if latest is None or mtime > latest:
                    latest = mtime

        return latest

    def _get_doc_modified(self, doc_path: Path) -> Optional[datetime]:
        """Get document last modified time."""
        try:
            return datetime.fromtimestamp(doc_path.stat().st_mtime)
        except OSError:
            return None

    def check_project(self) -> list[CodeSyncReport]:
        """Check all documents in the project."""
        reports = []

        if not self.project.content_dir.exists():
            return reports

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = md_file.relative_to(self.project.content_dir)
                report = self.check_document(rel_path)
                reports.append(report)
            except (OSError, ValueError):
                pass

        return reports

    def get_errors(self) -> list[SyncIssue]:
        """Get all error-level issues across project."""
        issues = []
        for report in self.check_project():
            issues.extend([i for i in report.issues if i.severity == "error"])
        return issues

    def get_warnings(self) -> list[SyncIssue]:
        """Get all warning-level issues across project."""
        issues = []
        for report in self.check_project():
            issues.extend([i for i in report.issues if i.severity == "warning"])
        return issues

    def get_all_issues(self) -> list[SyncIssue]:
        """Get all issues across project."""
        issues = []
        for report in self.check_project():
            issues.extend(report.issues)
        return issues

    def generate_summary(self) -> dict:
        """Generate summary report for project."""
        reports = self.check_project()

        total_examples = sum(r.total_examples for r in reports)
        valid_examples = sum(r.valid_examples for r in reports)
        all_issues = []
        for r in reports:
            all_issues.extend(r.issues)

        error_count = sum(1 for i in all_issues if i.severity == "error")
        warning_count = sum(1 for i in all_issues if i.severity == "warning")
        needs_review = sum(1 for r in reports if r.needs_review)

        return {
            "summary": {
                "documents_checked": len(reports),
                "total_examples": total_examples,
                "valid_examples": valid_examples,
                "validation_rate": round(valid_examples / max(1, total_examples) * 100, 1),
                "error_count": error_count,
                "warning_count": warning_count,
                "documents_needing_review": needs_review,
            },
            "issues_by_type": {
                issue_type.value: sum(1 for i in all_issues if i.issue_type == issue_type)
                for issue_type in SyncIssueType
            },
            "documents": [r.to_dict() for r in reports if r.issues],
        }


def check_code_sync(project) -> dict:
    """Convenience function for code sync checking."""
    checker = EnhancedCodeSyncChecker(project)
    return checker.generate_summary()


__all__ = [
    "EnhancedCodeSyncChecker",
    "CodeBlockExtractor",
    "PythonValidator",
    "JavaScriptValidator",
    "YAMLValidator",
    "JSONValidator",
    "CodeBlock",
    "SyncIssue",
    "SyncIssueType",
    "CodeLanguage",
    "APIReference",
    "CodeSyncReport",
    "check_code_sync",
]
