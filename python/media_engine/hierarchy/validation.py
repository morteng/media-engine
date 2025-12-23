"""
Hierarchy Validation for Media Engine

Validates document hierarchy structure for integrity:
- Cycle detection
- Orphan detection
- Sequence order conflicts
- Level consistency
- Derivation integrity
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .types import DocumentType, HierarchyValidationError

if TYPE_CHECKING:
    from .graph import HierarchyGraph

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of hierarchy validation."""

    is_valid: bool
    errors: list[HierarchyValidationError] = field(default_factory=list)
    warnings: list[HierarchyValidationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }


class HierarchyValidator:
    """
    Validates document hierarchy structure.

    Checks for:
    - Circular parent references (cycles)
    - Orphan documents (missing parents)
    - Duplicate sequence orders among siblings
    - Level consistency (hierarchy_level matches depth)
    - Derivation integrity (sources exist)
    - Document type hierarchy rules
    """

    # Errors that should block publishing
    CRITICAL_ERROR_TYPES = {
        "circular_reference",
        "missing_parent",
        "invalid_derivation",
    }

    def __init__(self, graph: "HierarchyGraph"):
        self.graph = graph
        self.registry = graph.registry

    def validate_all(self) -> ValidationResult:
        """Run all validation checks."""
        errors = []
        warnings = []

        # Collect all issues
        errors.extend(self.detect_cycles())
        errors.extend(self.find_orphans())
        errors.extend(self.check_derivation_integrity())

        warnings.extend(self.check_sequence_order())
        warnings.extend(self.check_level_consistency())
        warnings.extend(self.check_type_rules())

        # Determine overall validity (no critical errors)
        is_valid = not any(
            e.error_type in self.CRITICAL_ERROR_TYPES for e in errors
        )

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )

    def detect_cycles(self) -> list[HierarchyValidationError]:
        """
        Find circular parent references.

        Uses DFS with path tracking to detect cycles.
        """
        errors = []
        visited = set()
        path_stack = set()

        def dfs(path_str: str, current_path: list[str]) -> Optional[list[str]]:
            """DFS to detect cycle, returns cycle path if found."""
            if path_str in path_stack:
                # Found a cycle - return the cycle path
                cycle_start = current_path.index(path_str)
                return current_path[cycle_start:] + [path_str]

            if path_str in visited:
                return None

            visited.add(path_str)
            path_stack.add(path_str)
            current_path.append(path_str)

            node = self.registry.get_node(Path(path_str))
            if node and node.parent:
                parent_str = str(node.parent)
                cycle = dfs(parent_str, current_path)
                if cycle:
                    return cycle

            current_path.pop()
            path_stack.remove(path_str)
            return None

        # Check each node
        for node in self.registry.get_all_nodes():
            path_str = str(node.path)
            if path_str not in visited:
                cycle = dfs(path_str, [])
                if cycle:
                    errors.append(
                        HierarchyValidationError(
                            error_type="circular_reference",
                            severity="error",
                            document=Path(cycle[0]),
                            message=f"Circular parent chain detected: {' → '.join(cycle)}",
                            related_documents=[Path(p) for p in cycle[1:]],
                        )
                    )

        return errors

    def find_orphans(self) -> list[HierarchyValidationError]:
        """
        Find documents with invalid parent references.

        An orphan is a document whose parent_document points to
        a file that doesn't exist in the registry.
        """
        errors = []

        for node in self.registry.get_all_nodes():
            if node.parent:
                parent_node = self.registry.get_node(node.parent)
                if parent_node is None:
                    errors.append(
                        HierarchyValidationError(
                            error_type="missing_parent",
                            severity="error",
                            document=node.path,
                            message=f"Parent document not found: {node.parent}",
                            related_documents=[node.parent],
                        )
                    )

        return errors

    def check_sequence_order(self) -> list[HierarchyValidationError]:
        """
        Find duplicate sequence orders among siblings.

        Siblings should have unique sequence_order values.
        """
        warnings = []

        # Group nodes by parent
        by_parent: dict[Optional[str], list] = {}
        for node in self.registry.get_all_nodes():
            parent_key = str(node.parent) if node.parent else None
            if parent_key not in by_parent:
                by_parent[parent_key] = []
            by_parent[parent_key].append(node)

        # Check each group for duplicates
        for parent_key, siblings in by_parent.items():
            order_map: dict[int, list] = {}
            for node in siblings:
                order = node.sequence_order
                if order not in order_map:
                    order_map[order] = []
                order_map[order].append(node)

            # Report duplicates
            for order, nodes in order_map.items():
                if len(nodes) > 1:
                    first = nodes[0]
                    others = nodes[1:]
                    msg = f"Duplicate sequence_order={order} ({len(others)} others)"
                    warnings.append(
                        HierarchyValidationError(
                            error_type="duplicate_order",
                            severity="warning",
                            document=first.path,
                            message=msg,
                            related_documents=[n.path for n in others],
                        )
                    )

        return warnings

    def check_level_consistency(self) -> list[HierarchyValidationError]:
        """
        Verify hierarchy_level matches computed depth.

        The level field should match the actual depth in the tree.
        """
        warnings = []

        for node in self.registry.get_all_nodes():
            computed_level = self.graph.get_level(node.path)
            if node.level != computed_level:
                msg = f"hierarchy_level={node.level} but computed is {computed_level}"
                warnings.append(
                    HierarchyValidationError(
                        error_type="level_mismatch",
                        severity="warning",
                        document=node.path,
                        message=msg,
                    )
                )

        return warnings

    def check_derivation_integrity(self) -> list[HierarchyValidationError]:
        """
        Verify derived_from references are valid.

        Each source in derived_from should exist in the registry.
        """
        errors = []

        for node in self.registry.get_all_nodes():
            for source in node.derived_from:
                source_node = self.registry.get_node(source.path)
                if source_node is None:
                    errors.append(
                        HierarchyValidationError(
                            error_type="invalid_derivation",
                            severity="error",
                            document=node.path,
                            message=f"Derivation source not found: {source.path}",
                            related_documents=[source.path],
                        )
                    )

        return errors

    def check_type_rules(self) -> list[HierarchyValidationError]:
        """
        Validate document type hierarchy rules.

        Rules:
        - Source documents shouldn't derive from derived documents
        - Operations should derive from architecture/implementation
        """
        warnings = []

        source_types = DocumentType.source_types()
        derived_types = DocumentType.derived_types()

        for node in self.registry.get_all_nodes():
            # Source docs shouldn't derive from derived docs
            if node.doc_type in source_types:
                for source in node.derived_from:
                    source_node = self.registry.get_node(source.path)
                    if source_node and source_node.doc_type in derived_types:
                        msg = f"Source derives from derived: {source.path}"
                        warnings.append(
                            HierarchyValidationError(
                                error_type="type_rule_violation",
                                severity="warning",
                                document=node.path,
                                message=msg,
                                related_documents=[source.path],
                            )
                        )

            # Operations should derive from architecture or implementation
            if node.doc_type == DocumentType.OPERATIONS:
                has_valid_source = False
                for source in node.derived_from:
                    source_node = self.registry.get_node(source.path)
                    if source_node and source_node.doc_type in {
                        DocumentType.ARCHITECTURE,
                        DocumentType.IMPLEMENTATION,
                    }:
                        has_valid_source = True
                        break

                if node.derived_from and not has_valid_source:
                    msg = "Operations should derive from architecture/implementation"
                    warnings.append(
                        HierarchyValidationError(
                            error_type="type_rule_violation",
                            severity="warning",
                            document=node.path,
                            message=msg,
                        )
                    )

        return warnings

    def validate_single(self, path: Path) -> ValidationResult:
        """Validate a single document's hierarchy relationships."""
        errors = []
        warnings = []

        node = self.registry.get_node(path)
        if not node:
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
            )

        # Check parent
        if node.parent:
            parent_node = self.registry.get_node(node.parent)
            if parent_node is None:
                errors.append(
                    HierarchyValidationError(
                        error_type="missing_parent",
                        severity="error",
                        document=path,
                        message=f"Parent document not found: {node.parent}",
                        related_documents=[node.parent],
                    )
                )

        # Check derivation sources
        for source in node.derived_from:
            source_node = self.registry.get_node(source.path)
            if source_node is None:
                errors.append(
                    HierarchyValidationError(
                        error_type="invalid_derivation",
                        severity="error",
                        document=path,
                        message=f"Derivation source not found: {source.path}",
                        related_documents=[source.path],
                    )
                )

        # Check level
        computed_level = self.graph.get_level(path)
        if node.level != computed_level:
            warnings.append(
                HierarchyValidationError(
                    error_type="level_mismatch",
                    severity="warning",
                    document=path,
                    message=f"hierarchy_level={node.level} but computed depth is {computed_level}",
                )
            )

        is_valid = not any(e.error_type in self.CRITICAL_ERROR_TYPES for e in errors)

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )


__all__ = ["HierarchyValidator", "ValidationResult"]
