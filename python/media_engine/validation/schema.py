"""
Schema Validation Module

Validates YAML frontmatter against JSON schemas.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import yaml

try:
    from jsonschema import ValidationError as JsonSchemaError
    from jsonschema import validate

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from rich.console import Console

if TYPE_CHECKING:
    pass

console = Console()


@dataclass
class SchemaError:
    """A schema validation error."""

    file_path: Path
    field: str
    message: str
    value: Any = None
    schema_path: str = ""


@dataclass
class SchemaValidator:
    """Validates frontmatter against schemas."""

    schemas: Dict[str, dict] = field(default_factory=dict)

    def load_schema(self, name: str, schema: dict):
        """Load a schema by name."""
        self.schemas[name] = schema

    def load_schema_file(self, path: Path) -> Optional[str]:
        """Load schema from YAML file."""
        if not path.exists():
            return None

        with open(path) as f:
            data = yaml.safe_load(f)

        name = path.stem
        self.schemas[name] = data
        return name

    def validate(
        self,
        frontmatter: dict,
        schema_name: str,
        file_path: Optional[Path] = None,
    ) -> List[SchemaError]:
        """
        Validate frontmatter against a schema.

        Args:
            frontmatter: Frontmatter dictionary to validate
            schema_name: Name of schema to validate against
            file_path: Optional file path for error reporting

        Returns:
            List of SchemaError
        """
        errors = []
        file_path = file_path or Path("unknown")

        if schema_name not in self.schemas:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field="",
                    message=f"Schema '{schema_name}' not found",
                )
            )
            return errors

        schema = self.schemas[schema_name]

        if HAS_JSONSCHEMA:
            # Use jsonschema for validation
            try:
                validate(instance=frontmatter, schema=schema)
            except JsonSchemaError as e:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field=".".join(str(p) for p in e.absolute_path),
                        message=e.message,
                        value=e.instance,
                        schema_path=".".join(str(p) for p in e.schema_path),
                    )
                )
        else:
            # Basic validation without jsonschema
            errors.extend(self._basic_validate(frontmatter, schema, file_path))

        return errors

    def _basic_validate(
        self,
        data: dict,
        schema: dict,
        file_path: Path,
        path: str = "",
    ) -> List[SchemaError]:
        """Basic validation without jsonschema library."""
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field_name in required:
            if field_name not in data:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field=f"{path}.{field_name}" if path else field_name,
                        message=f"Required field '{field_name}' is missing",
                    )
                )

        # Check field types
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name not in data:
                continue

            value = data[field_name]
            expected_type = field_schema.get("type")

            if expected_type:
                if not self._check_type(value, expected_type):
                    errors.append(
                        SchemaError(
                            file_path=file_path,
                            field=f"{path}.{field_name}" if path else field_name,
                            message=f"Expected type '{expected_type}', got '{type(value).__name__}'",
                            value=value,
                        )
                    )

            # Check enum values
            if "enum" in field_schema:
                if value not in field_schema["enum"]:
                    errors.append(
                        SchemaError(
                            file_path=file_path,
                            field=f"{path}.{field_name}" if path else field_name,
                            message=f"Value '{value}' not in allowed values: {field_schema['enum']}",
                            value=value,
                        )
                    )

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        if expected_type not in type_map:
            return True  # Unknown type, don't validate

        return isinstance(value, type_map[expected_type])


# Default document schema
DEFAULT_DOCUMENT_SCHEMA = {
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string"},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "status": {
            "type": "string",
            "enum": ["draft", "review", "final", "archived"],
        },
        "last_modified": {"type": "string"},
        "freshness_days": {"type": "integer", "minimum": 1},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "references": {
            "type": "array",
            "items": {"type": "string"},
        },
        "depends_on": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


def load_schema(path: Path) -> dict:
    """Load a schema from a YAML or JSON file."""
    with open(path) as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        else:
            return json.load(f)


def validate_frontmatter(
    frontmatter: dict,
    schema: Optional[dict] = None,
    file_path: Optional[Path] = None,
) -> List[SchemaError]:
    """
    Validate frontmatter against a schema.

    Args:
        frontmatter: Frontmatter dictionary
        schema: Schema dictionary (uses default if not provided)
        file_path: File path for error reporting

    Returns:
        List of SchemaError
    """
    validator = SchemaValidator()
    schema = schema or DEFAULT_DOCUMENT_SCHEMA
    validator.load_schema("document", schema)
    return validator.validate(frontmatter, "document", file_path)
