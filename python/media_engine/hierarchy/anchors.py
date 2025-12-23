"""Consistency anchors for cross-document fact tracking.

Anchors are named facts defined in documents that other documents can reference.
When an anchor changes, all referencing documents can be flagged for review.

Example in frontmatter:
```yaml
anchors:
  max_chapters: 50
  supported_formats: ["html", "pdf", "pptx"]
  api_version: "2.0"
```

References in other documents:
```yaml
anchor_refs:
  - source: "chapters/01_introduction.md"
    anchor: "max_chapters"
  - source: "chapters/02_api.md"
    anchor: "api_version"
```
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .registry import HierarchyRegistry


class AnchorChangeType(Enum):
    """Type of anchor change."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    TYPE_CHANGED = "type_changed"


@dataclass
class Anchor:
    """A named fact defined in a document."""

    name: str
    value: Any
    document_path: Path
    description: Optional[str] = None
    last_modified: Optional[datetime] = None

    def __hash__(self) -> int:
        return hash((self.name, str(self.document_path)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Anchor):
            return False
        return self.name == other.name and self.document_path == other.document_path


@dataclass
class AnchorReference:
    """A reference to an anchor from another document."""

    source_document: Path
    anchor_name: str
    referencing_document: Path
    expected_value: Optional[Any] = None  # Optional snapshot of expected value


@dataclass
class AnchorChange:
    """Represents a change to an anchor."""

    anchor_name: str
    document_path: Path
    change_type: AnchorChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    affected_documents: list[Path] = field(default_factory=list)


@dataclass
class AnchorValidationResult:
    """Result of validating anchor references."""

    valid: bool
    # Tuples: (ref_doc, anchor, source_doc)
    missing_anchors: list[tuple[Path, str, Path]] = field(default_factory=list)
    # Tuples: (ref_doc, anchor, expected, actual)
    value_mismatches: list[tuple[Path, str, Any, Any]] = field(default_factory=list)
    # Tuples: (ref_doc, anchor) - source doc not found
    orphan_references: list[tuple[Path, str]] = field(default_factory=list)


class AnchorRegistry:
    """Registry of all anchors and their references across documents."""

    def __init__(self, registry: "HierarchyRegistry"):
        self.hierarchy_registry = registry
        # doc_path -> anchor_name -> Anchor
        self._anchors: dict[str, dict[str, Anchor]] = {}
        # doc_path -> list of refs from this doc
        self._references: dict[str, list[AnchorReference]] = {}
        # source_doc -> anchor -> list of referencing docs
        self._reverse_refs: dict[str, dict[str, list[Path]]] = {}
        self._built = False

    def build(self) -> None:
        """Build the anchor registry from all documents."""
        self._anchors.clear()
        self._references.clear()
        self._reverse_refs.clear()

        for path_str, entry in self.hierarchy_registry._nodes.items():
            path = Path(path_str)
            doc_path_str = path_str

            # Extract anchors defined in this document
            if entry.anchors:
                self._anchors[doc_path_str] = {}
                for name, value in entry.anchors.items():
                    if isinstance(value, dict) and "value" in value:
                        # Extended format: {value: x, description: "..."}
                        anchor = Anchor(
                            name=name,
                            value=value["value"],
                            document_path=path,
                            description=value.get("description"),
                        )
                    else:
                        # Simple format: just the value
                        anchor = Anchor(
                            name=name,
                            value=value,
                            document_path=path,
                        )
                    self._anchors[doc_path_str][name] = anchor

            # Extract anchor references from this document
            anchor_refs = entry.raw_metadata.get("anchor_refs", [])
            if anchor_refs:
                self._references[doc_path_str] = []
                for ref in anchor_refs:
                    if isinstance(ref, dict) and "source" in ref and "anchor" in ref:
                        # Resolve relative source path to absolute
                        source_rel = ref["source"]
                        source_path = self._resolve_source_path(path, source_rel)

                        anchor_ref = AnchorReference(
                            source_document=source_path,
                            anchor_name=ref["anchor"],
                            referencing_document=path,
                            expected_value=ref.get("expected_value"),
                        )
                        self._references[doc_path_str].append(anchor_ref)

                        # Build reverse reference index
                        source_str = str(source_path)
                        if source_str not in self._reverse_refs:
                            self._reverse_refs[source_str] = {}
                        if ref["anchor"] not in self._reverse_refs[source_str]:
                            self._reverse_refs[source_str][ref["anchor"]] = []
                        self._reverse_refs[source_str][ref["anchor"]].append(path)

        self._built = True

    def _resolve_source_path(self, referencing_doc: Path, source_rel: str) -> Path:
        """
        Resolve a relative source path to an absolute path.

        Source paths in anchor_refs can be:
        - Relative to content dir: "chapters/01_introduction.md"
        - Language-prefixed: "en/chapters/01_introduction.md"

        We try to find the document in the same language directory as the referencing doc.
        """
        # Try to find the source in the same language directory
        # e.g., if referencing_doc is /project/content/en/chapters/04.md
        # and source_rel is "chapters/01_introduction.md"
        # then look for /project/content/en/chapters/01_introduction.md

        # Find language directory (parent of chapters/)
        lang_dir = referencing_doc.parent
        while lang_dir.name not in ("en", "no", "content") and lang_dir != lang_dir.parent:
            lang_dir = lang_dir.parent

        if lang_dir.name == "content":
            # Couldn't find language dir, try relative to content
            content_dir = lang_dir
            resolved = content_dir / source_rel
            if resolved.exists():
                return resolved
        elif lang_dir.name in ("en", "no"):
            # Found language dir
            resolved = lang_dir / source_rel
            if resolved.exists():
                return resolved
            # Also try parent (content dir) with language prefix
            content_dir = lang_dir.parent
            resolved = content_dir / source_rel
            if resolved.exists():
                return resolved

        # Fallback: try resolving from the registry nodes
        for node_path in self.hierarchy_registry._nodes:
            if node_path.endswith(source_rel.split("/")[-1]):
                # Check if the path matches
                if source_rel in node_path:
                    return Path(node_path)

        # Final fallback: return as-is (will fail validation)
        return Path(source_rel)

    def get_anchor(self, document_path: Path, anchor_name: str) -> Optional[Anchor]:
        """Get a specific anchor from a document."""
        doc_str = str(document_path)
        if doc_str in self._anchors:
            return self._anchors[doc_str].get(anchor_name)
        return None

    def get_document_anchors(self, document_path: Path) -> dict[str, Anchor]:
        """Get all anchors defined in a document."""
        return self._anchors.get(str(document_path), {})

    def get_document_references(self, document_path: Path) -> list[AnchorReference]:
        """Get all anchor references from a document."""
        return self._references.get(str(document_path), [])

    def get_referencing_documents(self, document_path: Path, anchor_name: str) -> list[Path]:
        """Get all documents that reference a specific anchor."""
        doc_str = str(document_path)
        if doc_str in self._reverse_refs:
            return self._reverse_refs[doc_str].get(anchor_name, [])
        return []

    def get_all_anchors(self) -> list[Anchor]:
        """Get all anchors across all documents."""
        anchors = []
        for doc_anchors in self._anchors.values():
            anchors.extend(doc_anchors.values())
        return anchors

    def validate_references(self) -> AnchorValidationResult:
        """Validate all anchor references."""
        missing = []
        mismatches = []
        orphans = []

        for doc_path_str, refs in self._references.items():
            ref_doc = Path(doc_path_str)
            for ref in refs:
                source_str = str(ref.source_document)

                # Check if source document exists in registry
                if source_str not in self._anchors:
                    # Source document might not have any anchors defined
                    source_in_registry = source_str in self.hierarchy_registry._nodes
                    if not source_in_registry:
                        orphans.append((ref_doc, ref.anchor_name))
                        continue
                    else:
                        # Source exists but anchor doesn't
                        missing.append((ref_doc, ref.anchor_name, ref.source_document))
                        continue

                # Check if anchor exists in source
                anchor = self._anchors[source_str].get(ref.anchor_name)
                if not anchor:
                    missing.append((ref_doc, ref.anchor_name, ref.source_document))
                    continue

                # Check value match if expected value is specified
                if ref.expected_value is not None:
                    if anchor.value != ref.expected_value:
                        mismatch = (ref_doc, ref.anchor_name, ref.expected_value, anchor.value)
                        mismatches.append(mismatch)

        valid = len(missing) == 0 and len(orphans) == 0
        return AnchorValidationResult(
            valid=valid,
            missing_anchors=missing,
            value_mismatches=mismatches,
            orphan_references=orphans,
        )

    def detect_changes(
        self, document_path: Path, new_anchors: dict[str, Any]
    ) -> list[AnchorChange]:
        """Detect changes between current and new anchors for a document."""
        changes = []
        doc_str = str(document_path)
        current_anchors = self._anchors.get(doc_str, {})

        # Check for modified or removed anchors
        for name, anchor in current_anchors.items():
            if name not in new_anchors:
                # Anchor removed
                affected = self.get_referencing_documents(document_path, name)
                changes.append(AnchorChange(
                    anchor_name=name,
                    document_path=document_path,
                    change_type=AnchorChangeType.REMOVED,
                    old_value=anchor.value,
                    new_value=None,
                    affected_documents=affected,
                ))
            else:
                new_value = new_anchors[name]
                if isinstance(new_value, dict) and "value" in new_value:
                    new_value = new_value["value"]

                if type(anchor.value) is not type(new_value):
                    # Type changed
                    affected = self.get_referencing_documents(document_path, name)
                    changes.append(AnchorChange(
                        anchor_name=name,
                        document_path=document_path,
                        change_type=AnchorChangeType.TYPE_CHANGED,
                        old_value=anchor.value,
                        new_value=new_value,
                        affected_documents=affected,
                    ))
                elif anchor.value != new_value:
                    # Value modified
                    affected = self.get_referencing_documents(document_path, name)
                    changes.append(AnchorChange(
                        anchor_name=name,
                        document_path=document_path,
                        change_type=AnchorChangeType.MODIFIED,
                        old_value=anchor.value,
                        new_value=new_value,
                        affected_documents=affected,
                    ))

        # Check for new anchors
        for name, value in new_anchors.items():
            if name not in current_anchors:
                if isinstance(value, dict) and "value" in value:
                    value = value["value"]
                changes.append(AnchorChange(
                    anchor_name=name,
                    document_path=document_path,
                    change_type=AnchorChangeType.ADDED,
                    old_value=None,
                    new_value=value,
                    affected_documents=[],  # New anchors don't have refs yet
                ))

        return changes

    def get_impact_summary(self) -> dict[str, Any]:
        """Get a summary of anchor usage and impact."""
        total_anchors = sum(len(anchors) for anchors in self._anchors.values())
        total_refs = sum(len(refs) for refs in self._references.values())

        # Find most referenced anchors
        anchor_ref_counts: dict[str, int] = {}
        for source_doc, anchor_refs in self._reverse_refs.items():
            for anchor_name, ref_docs in anchor_refs.items():
                key = f"{source_doc}:{anchor_name}"
                anchor_ref_counts[key] = len(ref_docs)

        most_referenced = sorted(anchor_ref_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Find documents with most anchors
        docs_by_anchor_count = sorted(
            [(doc, len(anchors)) for doc, anchors in self._anchors.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "total_anchors": total_anchors,
            "total_references": total_refs,
            "documents_with_anchors": len(self._anchors),
            "documents_with_refs": len(self._references),
            "most_referenced": most_referenced,
            "documents_by_anchor_count": docs_by_anchor_count,
        }
