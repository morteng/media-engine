"""
Code-Documentation Sync Detection

Detects when source code referenced in documentation has changed,
flagging docs that may be stale even if recently edited.

Reference types:
- File paths: `src/core/config.py`
- Function names: `find_project()`
- Class names: `HTMLBuilder`
- CLI commands: `media-engine build`
- Import statements in code blocks
"""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.project import Project


@dataclass
class CodeReference:
    """A reference to code in documentation."""

    doc_path: Path
    ref_type: str  # "file", "function", "class", "cli", "import"
    ref_target: str
    line_number: int
    context: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "doc_path": str(self.doc_path),
            "ref_type": self.ref_type,
            "ref_target": self.ref_target,
            "line_number": self.line_number,
            "context": self.context,
        }


@dataclass
class SyncStatus:
    """Sync status for a document."""

    document: Path
    references: list[CodeReference]
    stale_refs: list[CodeReference]
    last_doc_modified: Optional[datetime]
    last_code_change: Optional[datetime]
    needs_review: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "reference_count": len(self.references),
            "stale_count": len(self.stale_refs),
            "stale_refs": [r.to_dict() for r in self.stale_refs],
            "last_doc_modified": self.last_doc_modified.isoformat() if self.last_doc_modified else None,
            "last_code_change": self.last_code_change.isoformat() if self.last_code_change else None,
            "needs_review": self.needs_review,
        }


# Reference patterns
REFERENCE_PATTERNS = {
    "file": re.compile(r"`([a-zA-Z_][a-zA-Z0-9_/.-]*\.(py|js|ts|go|rs|java|rb|sh))`"),
    "function": re.compile(r"`(\w+)\(\)`"),
    "class": re.compile(r"`([A-Z][a-zA-Z0-9]+)`"),
    "cli": re.compile(r"media-engine\s+(\w+(?:\s+\w+)?)"),
    "import": re.compile(r"from\s+(\S+)\s+import|import\s+(\S+)"),
}


@dataclass
class CodeSyncChecker:
    """
    Checks synchronization between documentation and code.

    Usage:
        checker = CodeSyncChecker(project)
        status = checker.check_sync(Path("chapters/05.md"))
        if status.needs_review:
            print(f"Doc needs review: {status.stale_refs}")

        # Find what docs are affected by a code change
        affected = checker.get_impact(Path("python/media_engine/core/config.py"))
    """

    project: Project
    code_dirs: list[str] = field(default_factory=lambda: ["python", "src", "lib"])

    def extract_references(self, doc_path: Path) -> list[CodeReference]:
        """
        Extract all code references from a document.

        Args:
            doc_path: Path to the document

        Returns:
            List of CodeReference instances
        """
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path
            try:
                doc_path = full_path.relative_to(self.project.content_dir)
            except ValueError:
                doc_path = full_path.relative_to(self.project.root)

        if not full_path.exists():
            return []

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        references: list[CodeReference] = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Extract references using patterns
            for ref_type, pattern in REFERENCE_PATTERNS.items():
                for match in pattern.finditer(line):
                    target = match.group(1) or match.group(2) if len(match.groups()) > 1 else match.group(1)
                    if target:
                        references.append(
                            CodeReference(
                                doc_path=doc_path,
                                ref_type=ref_type,
                                ref_target=target,
                                line_number=line_num,
                                context=line.strip()[:100],
                            )
                        )

        return references

    def check_sync(self, doc_path: Path) -> SyncStatus:
        """
        Check if a document's code references are up to date.

        Args:
            doc_path: Path to the document

        Returns:
            SyncStatus indicating if review is needed
        """
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path
            try:
                doc_path = full_path.relative_to(self.project.content_dir)
            except ValueError:
                doc_path = full_path.relative_to(self.project.root)

        references = self.extract_references(full_path)
        stale_refs: list[CodeReference] = []
        last_code_change: Optional[datetime] = None

        # Get document modification time
        try:
            last_doc_modified = datetime.fromtimestamp(full_path.stat().st_mtime)
        except OSError:
            last_doc_modified = None

        # Check each reference
        for ref in references:
            if ref.ref_type == "file":
                # Check if the file exists and when it was modified
                code_path = self._find_code_file(ref.ref_target)
                if code_path and code_path.exists():
                    try:
                        code_mtime = datetime.fromtimestamp(code_path.stat().st_mtime)
                        if last_code_change is None or code_mtime > last_code_change:
                            last_code_change = code_mtime

                        if last_doc_modified and code_mtime > last_doc_modified:
                            stale_refs.append(ref)
                    except OSError:
                        pass

            elif ref.ref_type in ("function", "class"):
                # Search for function/class in code
                code_locations = self._find_definition(ref.ref_target, ref.ref_type)
                for code_path in code_locations:
                    try:
                        code_mtime = datetime.fromtimestamp(code_path.stat().st_mtime)
                        if last_code_change is None or code_mtime > last_code_change:
                            last_code_change = code_mtime

                        if last_doc_modified and code_mtime > last_doc_modified:
                            stale_refs.append(ref)
                            break
                    except OSError:
                        pass

        needs_review = len(stale_refs) > 0

        return SyncStatus(
            document=doc_path,
            references=references,
            stale_refs=stale_refs,
            last_doc_modified=last_doc_modified,
            last_code_change=last_code_change,
            needs_review=needs_review,
        )

    def check_project(self) -> list[SyncStatus]:
        """
        Check all documents in the project for stale references.

        Returns:
            List of SyncStatus for documents with issues
        """
        results: list[SyncStatus] = []

        if not self.project.content_dir.exists():
            return results

        for md_file in self.project.content_dir.rglob("*.md"):
            status = self.check_sync(md_file)
            if status.needs_review or status.references:
                results.append(status)

        # Sort by stale count (most stale first)
        results.sort(key=lambda s: -len(s.stale_refs))

        return results

    def get_impact(self, code_path: Path) -> list[Path]:
        """
        Find documents affected by changes to a code file.

        Args:
            code_path: Path to the changed code file

        Returns:
            List of document paths that reference this code
        """
        affected: list[Path] = []

        if not code_path.is_absolute():
            code_path = self.project.root / code_path

        # Get relative path for matching
        try:
            rel_path = code_path.relative_to(self.project.root)
        except ValueError:
            rel_path = code_path

        if not self.project.content_dir.exists():
            return affected

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")

                # Check if the file is referenced
                if str(rel_path) in content or code_path.name in content:
                    try:
                        affected.append(md_file.relative_to(self.project.content_dir))
                    except ValueError:
                        affected.append(md_file.relative_to(self.project.root))

            except (OSError, UnicodeDecodeError):
                pass

        return affected

    def get_stale_references(self) -> list[CodeReference]:
        """Get all stale code references across the project."""
        stale: list[CodeReference] = []

        for status in self.check_project():
            stale.extend(status.stale_refs)

        return stale

    def _find_code_file(self, ref_target: str) -> Optional[Path]:
        """Find a code file matching the reference."""
        # Check each code directory
        for code_dir in self.code_dirs:
            code_path = self.project.root / code_dir / ref_target
            if code_path.exists():
                return code_path

        # Also check the reference as an absolute path from project root
        direct_path = self.project.root / ref_target
        if direct_path.exists():
            return direct_path

        return None

    def _find_definition(self, name: str, def_type: str) -> list[Path]:
        """Find files containing a function or class definition."""
        matching_files: list[Path] = []

        if def_type == "function":
            pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
        elif def_type == "class":
            pattern = rf"^\s*class\s+{re.escape(name)}\s*[:\(]"
        else:
            return matching_files

        pattern_re = re.compile(pattern, re.MULTILINE)

        for code_dir in self.code_dirs:
            code_path = self.project.root / code_dir
            if not code_path.exists():
                continue

            for py_file in code_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if pattern_re.search(content):
                        matching_files.append(py_file)
                except (OSError, UnicodeDecodeError):
                    pass

        return matching_files


def check_code_sync(project: Project) -> list[SyncStatus]:
    """Convenience function to check code-documentation sync."""
    checker = CodeSyncChecker(project)
    return checker.check_project()
