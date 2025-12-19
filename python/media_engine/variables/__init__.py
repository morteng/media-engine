"""
Content Variables & Interpolation for Media Engine

Allows dynamic content insertion:
- Project variables: {{project.name}}, {{project.version}}
- Date variables: {{date.today}}, {{date.year}}
- Custom variables from variables.yaml
- Environment variables: {{env.API_URL}}

Prevents hardcoded values that become stale.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class VariableSet:
    """Collection of variables for interpolation."""

    # Built-in namespaces
    project: dict = field(default_factory=dict)
    date: dict = field(default_factory=dict)
    env: dict = field(default_factory=dict)

    # Custom namespaces from variables.yaml
    custom: dict = field(default_factory=dict)

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a variable by dot-notation path.

        Examples:
            get("project.name")
            get("pricing.starter")
            get("env.API_URL")
        """
        parts = path.split(".")

        if len(parts) == 0:
            return default

        namespace = parts[0]
        rest = ".".join(parts[1:]) if len(parts) > 1 else None

        # Check built-in namespaces
        if namespace == "project":
            return self._get_nested(self.project, rest, default)
        elif namespace == "date":
            return self._get_nested(self.date, rest, default)
        elif namespace == "env":
            return self._get_nested(self.env, rest, default)
        else:
            # Check custom namespace
            if namespace in self.custom:
                if rest:
                    return self._get_nested(self.custom[namespace], rest, default)
                return self.custom[namespace]
            # Try as top-level custom key
            return self._get_nested(self.custom, path, default)

    def _get_nested(self, data: dict, path: str, default: Any) -> Any:
        """Get nested value from dict using dot notation."""
        if not path:
            return data

        current = data
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def to_dict(self) -> dict:
        """Convert to flat dictionary for Jinja2."""
        result = {
            "project": self.project,
            "date": self.date,
            "env": self.env,
        }
        result.update(self.custom)
        return result


class VariableLoader:
    """Loads variables from project configuration."""

    def __init__(self, project):
        self.project = project
        self.variables_path = project.root / "variables.yaml"

    def load(self) -> VariableSet:
        """Load all variables for the project."""
        vs = VariableSet()

        # Project variables
        vs.project = {
            "name": self.project.config.name,
            "description": self.project.config.description,
            "root": str(self.project.root),
            "source_language": self.project.source_language,
            "languages": list(self.project.languages.keys()),
        }

        # Date variables
        now = datetime.now()
        vs.date = {
            "today": now.strftime("%Y-%m-%d"),
            "now": now.isoformat(),
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "month_name": now.strftime("%B"),
            "day": now.strftime("%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": int(now.timestamp()),
        }

        # Environment variables (filtered for safety)
        safe_env_prefixes = ["MEDIA_ENGINE_", "PROJECT_", "DOCS_", "API_"]
        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in safe_env_prefixes):
                vs.env[key] = value

        # Custom variables from variables.yaml
        if self.variables_path.exists():
            with open(self.variables_path) as f:
                custom = yaml.safe_load(f) or {}
                vs.custom = custom

        return vs


class ContentInterpolator:
    """
    Interpolates variables in content.

    Supports two syntaxes:
    - Mustache-style: {{variable.path}}
    - Jinja2-style: {{ variable.path }} (with spaces)
    """

    # Pattern for {{variable}} or {{ variable }}
    PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}")

    def __init__(self, variables: VariableSet):
        self.variables = variables

    def interpolate(self, content: str, strict: bool = False) -> tuple[str, list[str]]:
        """
        Replace variables in content.

        Args:
            content: Content with {{variable}} placeholders
            strict: If True, raise error on missing variables

        Returns:
            Tuple of (interpolated content, list of missing variables)
        """
        missing = []

        def replace(match):
            var_path = match.group(1)
            value = self.variables.get(var_path)

            if value is None:
                missing.append(var_path)
                if strict:
                    raise ValueError(f"Missing variable: {var_path}")
                return match.group(0)  # Keep original

            return str(value)

        result = self.PATTERN.sub(replace, content)
        return result, missing

    def find_variables(self, content: str) -> list[str]:
        """Find all variable references in content."""
        return [match.group(1) for match in self.PATTERN.finditer(content)]

    def validate(self, content: str) -> list[str]:
        """Find variables that don't resolve."""
        missing = []
        for var_path in self.find_variables(content):
            if self.variables.get(var_path) is None:
                missing.append(var_path)
        return missing


class ProjectInterpolator:
    """High-level interpolator for entire project."""

    def __init__(self, project):
        self.project = project
        self.loader = VariableLoader(project)
        self.variables = self.loader.load()
        self.interpolator = ContentInterpolator(self.variables)

    def process_document(self, doc_path: Path) -> tuple[str, list[str]]:
        """
        Process a document, replacing all variables.

        Returns:
            Tuple of (processed content, missing variables)
        """
        from ..cms.document import Document

        doc = Document.load(doc_path)
        return self.interpolator.interpolate(doc.content)

    def process_and_save(self, doc_path: Path, output_path: Path = None):
        """Process document and save result."""
        from ..cms.document import Document

        doc = Document.load(doc_path)
        content, missing = self.interpolator.interpolate(doc.content)

        if missing:
            raise ValueError(f"Missing variables in {doc_path}: {missing}")

        out = output_path or doc_path
        if out == doc_path:
            doc.content = content
            doc.save()
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            # Create new doc with processed content
            out.write_text(f"---\n{yaml.dump(doc.metadata)}---\n\n{content}")

    def validate_project(self) -> dict:
        """
        Validate all documents for missing variables.

        Returns:
            Report of missing variables by file
        """
        issues = {}

        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                content, missing = self.process_document(chapter)
                if missing:
                    issues[str(chapter)] = missing

        return {
            "total_files_with_issues": len(issues),
            "issues": issues,
            "all_missing": list(set(var for vars in issues.values() for var in vars)),
        }

    def get_available_variables(self) -> dict:
        """Get all available variables and their current values."""
        return self.variables.to_dict()


def interpolate_content(project, content: str) -> str:
    """Convenience function to interpolate content."""
    interpolator = ProjectInterpolator(project)
    result, _ = interpolator.interpolator.interpolate(content)
    return result


def validate_variables(project) -> dict:
    """Convenience function to validate project variables."""
    interpolator = ProjectInterpolator(project)
    return interpolator.validate_project()


__all__ = [
    "VariableSet",
    "VariableLoader",
    "ContentInterpolator",
    "ProjectInterpolator",
    "interpolate_content",
    "validate_variables",
]
