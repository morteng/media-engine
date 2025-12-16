"""
Schema validation and design system management.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .document import Document


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str
    severity: str = "error"  # error, warning, info

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    """Result of schema validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str) -> None:
        self.errors.append(ValidationError(field, message, "error"))
        self.valid = False

    def add_warning(self, field: str, message: str) -> None:
        self.warnings.append(ValidationError(field, message, "warning"))

    def __bool__(self) -> bool:
        return self.valid


class SchemaValidator:
    """Validates document frontmatter against schemas."""

    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.schemas: dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all schema files."""
        if not self.schema_dir.exists():
            return

        for schema_file in self.schema_dir.glob("*.yaml"):
            if schema_file.name.startswith("design"):
                continue  # Skip design system
            try:
                with open(schema_file) as f:
                    schema = yaml.safe_load(f)
                    # Extract schema name from filename
                    name = schema_file.stem
                    self.schemas[name] = schema
            except Exception as e:
                print(f"Warning: Failed to load schema {schema_file}: {e}")

    def validate(self, doc: Document) -> ValidationResult:
        """Validate a document against its schema."""
        result = ValidationResult(valid=True)

        # Determine which schema to use
        schema_name = doc.doc_type
        if schema_name not in self.schemas:
            result.add_warning("schema", f"No schema found for type '{schema_name}'")
            return result

        schema = self.schemas[schema_name]
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for field_name in required:
            if field_name not in doc.metadata:
                result.add_error(field_name, "Required field is missing")

        # Validate each field
        for field_name, field_schema in properties.items():
            if field_name not in doc.metadata:
                continue

            value = doc.metadata[field_name]
            self._validate_field(field_name, value, field_schema, result)

        # Additional validations
        self._validate_version_format(doc, result)
        self._validate_dates(doc, result)
        self._validate_references(doc, result)

        return result

    def _validate_field(
        self, field_name: str, value: Any, schema: dict, result: ValidationResult
    ) -> None:
        """Validate a single field against its schema."""
        field_type = schema.get("type")

        # Type checking
        if field_type == "string":
            if not isinstance(value, str):
                result.add_error(field_name, f"Expected string, got {type(value).__name__}")
                return

            # Pattern matching
            pattern = schema.get("pattern")
            if pattern and not re.match(pattern, value):
                result.add_error(field_name, f"Value '{value}' doesn't match pattern '{pattern}'")

            # Enum values
            enum = schema.get("enum")
            if enum and value not in enum:
                result.add_error(field_name, f"Value '{value}' not in allowed values: {enum}")

            # Length constraints
            min_len = schema.get("minLength")
            max_len = schema.get("maxLength")
            if min_len and len(value) < min_len:
                result.add_error(field_name, f"Value too short (min {min_len} chars)")
            if max_len and len(value) > max_len:
                result.add_error(field_name, f"Value too long (max {max_len} chars)")

        elif field_type == "integer":
            if not isinstance(value, int):
                result.add_error(field_name, f"Expected integer, got {type(value).__name__}")
                return

            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if minimum is not None and value < minimum:
                result.add_error(field_name, f"Value {value} below minimum {minimum}")
            if maximum is not None and value > maximum:
                result.add_error(field_name, f"Value {value} above maximum {maximum}")

        elif field_type == "array":
            if not isinstance(value, list):
                result.add_error(field_name, f"Expected array, got {type(value).__name__}")
                return

            # Validate items
            items_schema = schema.get("items", {})
            for i, item in enumerate(value):
                if items_schema.get("type") == "string":
                    if not isinstance(item, str):
                        result.add_error(field_name, f"Item {i} should be string")
                    pattern = items_schema.get("pattern")
                    if pattern and isinstance(item, str) and not re.match(pattern, item):
                        result.add_warning(field_name, f"Item '{item}' doesn't match pattern")

    def _validate_version_format(self, doc: Document, result: ValidationResult) -> None:
        """Validate semantic version format."""
        version = doc.version
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            result.add_error("version", f"Invalid version format '{version}' (expected X.Y.Z)")

    def _validate_dates(self, doc: Document, result: ValidationResult) -> None:
        """Validate date fields."""
        today = date.today()

        if doc.last_modified:
            if doc.last_modified > today:
                result.add_warning("last_modified", "Date is in the future")
        else:
            result.add_warning("last_modified", "Missing or invalid date")

        if doc.last_reviewed and doc.last_modified:
            if doc.last_reviewed > doc.last_modified:
                result.add_warning("last_reviewed", "Review date after modification date")

    def _validate_references(self, doc: Document, result: ValidationResult) -> None:
        """Validate references array structure."""
        for i, ref in enumerate(doc.references):
            if "id" not in ref:
                result.add_error("references", f"Reference {i} missing 'id' field")
            if "title" not in ref:
                result.add_error("references", f"Reference {i} missing 'title' field")

        # Check for duplicate IDs
        ids = [r.get("id") for r in doc.references if "id" in r]
        if len(ids) != len(set(ids)):
            result.add_error("references", "Duplicate reference IDs found")


class DesignSystem:
    """Manages the design system configuration."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: dict = {}
        self._loaded = False

    def load(self) -> None:
        """Load the design system configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Design system not found: {self.config_path}")

        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)
        self._loaded = True

    def ensure_loaded(self) -> None:
        """Ensure design system is loaded."""
        if not self._loaded:
            self.load()

    # Color accessors
    def get_color(self, name: str) -> str:
        """Get a color by name (supports dot notation like 'layers.client')."""
        self.ensure_loaded()
        parts = name.split(".")
        value = self.config.get("colors", {})
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return "#000000"
        return value if isinstance(value, str) else "#000000"

    @property
    def colors(self) -> dict:
        """Get all colors."""
        self.ensure_loaded()
        return self.config.get("colors", {})

    @property
    def primary_color(self) -> str:
        return self.get_color("primary")

    @property
    def secondary_color(self) -> str:
        return self.get_color("secondary")

    @property
    def accent_color(self) -> str:
        return self.get_color("accent")

    @property
    def layer_colors(self) -> dict[str, str]:
        """Get diagram layer colors."""
        self.ensure_loaded()
        return self.config.get("colors", {}).get("layers", {})

    # Typography accessors
    @property
    def fonts(self) -> dict:
        """Get font configuration."""
        self.ensure_loaded()
        return self.config.get("typography", {}).get("fonts", {})

    @property
    def heading_font(self) -> str:
        return self.fonts.get("heading", "Inter")

    @property
    def body_font(self) -> str:
        return self.fonts.get("body", "Inter")

    @property
    def mono_font(self) -> str:
        return self.fonts.get("mono", "JetBrains Mono")

    # Diagram settings
    @property
    def diagram_defaults(self) -> dict:
        """Get default diagram settings."""
        self.ensure_loaded()
        return self.config.get("diagrams", {}).get("defaults", {})

    @property
    def diagram_fonts(self) -> dict:
        """Get diagram font settings."""
        self.ensure_loaded()
        return self.config.get("diagrams", {}).get("fonts", {})

    # Status colors
    def get_status_color(self, status: str) -> str:
        """Get color for a document status."""
        self.ensure_loaded()
        colors = self.config.get("status_colors", {})
        return colors.get(status, self.get_color("muted"))

    # CSS generation
    def generate_css_variables(self) -> str:
        """Generate CSS custom properties from design system."""
        self.ensure_loaded()
        lines = [":root {"]

        # Colors
        for name, value in self.colors.items():
            if isinstance(value, str):
                lines.append(f"    --color-{name}: {value};")
            elif isinstance(value, dict):
                for sub_name, sub_value in value.items():
                    lines.append(f"    --color-{name}-{sub_name}: {sub_value};")

        # Typography
        fonts = self.fonts
        lines.append(f"    --font-heading: '{fonts.get('heading', 'Inter')}', sans-serif;")
        lines.append(f"    --font-body: '{fonts.get('body', 'Inter')}', sans-serif;")
        lines.append(f"    --font-mono: '{fonts.get('mono', 'monospace')}', monospace;")

        # Sizes
        sizes = self.config.get("typography", {}).get("sizes", {})
        for name, value in sizes.items():
            lines.append(f"    --size-{name}: {value};")

        # Spacing
        spacing = self.config.get("spacing", {})
        for name, value in spacing.items():
            css_name = name.replace("_", "-")
            lines.append(f"    --spacing-{css_name}: {value};")

        lines.append("}")
        return "\n".join(lines)

    def to_matplotlib_style(self) -> dict:
        """Convert design system to matplotlib rcParams style."""
        self.ensure_loaded()

        diagram_fonts = self.diagram_fonts
        diagram_defaults = self.diagram_defaults

        return {
            # Figure
            "figure.figsize": (
                diagram_defaults.get("width", 12),
                diagram_defaults.get("height", 8),
            ),
            "figure.dpi": diagram_defaults.get("dpi", 150),
            "figure.facecolor": "white",
            "figure.edgecolor": "white",
            # Fonts
            "font.family": "sans-serif",
            "font.sans-serif": [self.heading_font, "DejaVu Sans"],
            "font.size": diagram_fonts.get("size_label", 10),
            # Axes
            "axes.facecolor": "white",
            "axes.edgecolor": self.get_color("border"),
            "axes.labelcolor": self.primary_color,
            "axes.titlesize": diagram_fonts.get("size_title", 14),
            "axes.titleweight": "bold",
            # Text
            "text.color": self.primary_color,
            # Lines
            "lines.linewidth": self.config.get("diagrams", {}).get("lines", {}).get("width", 1.5),
        }
