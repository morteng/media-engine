"""
Reference Validation Module

Validates citations, cross-references, and links in documents.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional, TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


@dataclass
class ReferenceError:
    """A reference validation error."""
    file_path: Path
    line: int
    reference: str
    error_type: str  # broken_link, missing_citation, undefined_reference
    message: str
    context: str = ""


@dataclass
class ReferenceValidator:
    """Validates references and links in documents."""
    known_references: Set[str] = field(default_factory=set)
    known_files: Set[Path] = field(default_factory=set)

    def add_reference(self, ref_id: str):
        """Register a known reference ID."""
        self.known_references.add(ref_id)

    def add_file(self, path: Path):
        """Register a known file path."""
        self.known_files.add(path.resolve())

    def validate_document(
        self,
        content: str,
        file_path: Path,
        base_dir: Optional[Path] = None,
    ) -> List[ReferenceError]:
        """
        Validate all references in a document.

        Args:
            content: Document content
            file_path: Path to document
            base_dir: Base directory for relative links

        Returns:
            List of ReferenceError
        """
        errors = []
        base_dir = base_dir or file_path.parent

        # Validate markdown links
        errors.extend(self._validate_links(content, file_path, base_dir))

        # Validate citations [^1] or [@citation]
        errors.extend(self._validate_citations(content, file_path))

        # Validate reference IDs (e.g., TR001, MR002)
        errors.extend(self._validate_ref_ids(content, file_path))

        return errors

    def _validate_links(
        self,
        content: str,
        file_path: Path,
        base_dir: Path,
    ) -> List[ReferenceError]:
        """Validate markdown links."""
        errors = []
        lines = content.split('\n')

        # Match [text](url) links
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        for line_num, line in enumerate(lines, 1):
            for match in link_pattern.finditer(line):
                link_text = match.group(1)
                link_url = match.group(2)

                # Skip external URLs
                if link_url.startswith(('http://', 'https://', 'mailto:')):
                    continue

                # Skip anchors
                if link_url.startswith('#'):
                    continue

                # Check relative file links
                target_path = (base_dir / link_url).resolve()

                # Remove anchor from path if present
                if '#' in str(target_path):
                    target_path = Path(str(target_path).split('#')[0])

                if not target_path.exists() and target_path not in self.known_files:
                    errors.append(ReferenceError(
                        file_path=file_path,
                        line=line_num,
                        reference=link_url,
                        error_type="broken_link",
                        message=f"Link target not found: {link_url}",
                        context=line.strip()[:80],
                    ))

        return errors

    def _validate_citations(
        self,
        content: str,
        file_path: Path,
    ) -> List[ReferenceError]:
        """Validate footnote-style citations."""
        errors = []
        lines = content.split('\n')

        # Find all citation references [^id]
        cite_refs = set()
        cite_defs = set()

        cite_ref_pattern = re.compile(r'\[\^([^\]]+)\](?!\:)')
        cite_def_pattern = re.compile(r'^\[\^([^\]]+)\]\:')

        for line_num, line in enumerate(lines, 1):
            # Find references
            for match in cite_ref_pattern.finditer(line):
                cite_refs.add((match.group(1), line_num, line.strip()[:80]))

            # Find definitions
            for match in cite_def_pattern.finditer(line):
                cite_defs.add(match.group(1))

        # Check for undefined citations
        for cite_id, line_num, context in cite_refs:
            if cite_id not in cite_defs:
                errors.append(ReferenceError(
                    file_path=file_path,
                    line=line_num,
                    reference=f"[^{cite_id}]",
                    error_type="missing_citation",
                    message=f"Citation [^{cite_id}] is referenced but not defined",
                    context=context,
                ))

        return errors

    def _validate_ref_ids(
        self,
        content: str,
        file_path: Path,
    ) -> List[ReferenceError]:
        """Validate document reference IDs (TR001, MR002, etc.)."""
        errors = []
        lines = content.split('\n')

        # Pattern for reference IDs
        ref_pattern = re.compile(r'\b(TR|MR|CA|REG|UR|ADR)\d{3}\b')

        for line_num, line in enumerate(lines, 1):
            for match in ref_pattern.finditer(line):
                ref_id = match.group(0)

                if ref_id not in self.known_references:
                    errors.append(ReferenceError(
                        file_path=file_path,
                        line=line_num,
                        reference=ref_id,
                        error_type="undefined_reference",
                        message=f"Reference {ref_id} is not defined in any document",
                        context=line.strip()[:80],
                    ))

        return errors


def collect_references(project: "Project") -> Set[str]:
    """
    Collect all defined reference IDs from a project.

    Args:
        project: Project to scan

    Returns:
        Set of reference IDs
    """
    from ..cms import Document

    references = set()
    ref_pattern = re.compile(r'^(TR|MR|CA|REG|UR|ADR)\d{3}')

    for language in project.languages:
        # Check research documents
        research_dir = project.get_content_path(language, "research")
        if research_dir.exists():
            for path in research_dir.glob("*.md"):
                # Extract ref ID from filename
                match = ref_pattern.match(path.stem)
                if match:
                    references.add(path.stem.split('_')[0])

                # Also check frontmatter
                try:
                    doc = Document.load(path)
                    if 'reference_id' in doc.frontmatter:
                        references.add(doc.frontmatter['reference_id'])
                except Exception:
                    pass

    return references


def collect_files(project: "Project") -> Set[Path]:
    """
    Collect all document file paths from a project.

    Args:
        project: Project to scan

    Returns:
        Set of resolved file paths
    """
    files = set()

    for language in project.languages:
        for chapter_path in project.list_chapters(language):
            files.add(chapter_path.resolve())

        research_dir = project.get_content_path(language, "research")
        if research_dir.exists():
            for path in research_dir.glob("*.md"):
                files.add(path.resolve())

    # Add deliverables
    deliverables_dir = project.root / "docs" / "deliverables"
    if deliverables_dir.exists():
        for path in deliverables_dir.rglob("*.md"):
            files.add(path.resolve())

    return files


def validate_references(
    project: "Project",
    console_output: bool = True,
) -> List[ReferenceError]:
    """
    Validate all references in a project.

    Args:
        project: Project to validate
        console_output: Whether to print progress

    Returns:
        List of ReferenceError
    """
    from ..cms import Document

    if console_output:
        console.print("[bold]Validating references...[/bold]")

    # Build validator with known references and files
    validator = ReferenceValidator()

    known_refs = collect_references(project)
    for ref in known_refs:
        validator.add_reference(ref)

    known_files = collect_files(project)
    for path in known_files:
        validator.add_file(path)

    if console_output:
        console.print(f"  [dim]Found {len(known_refs)} reference IDs[/dim]")
        console.print(f"  [dim]Found {len(known_files)} document files[/dim]")

    # Validate all documents
    all_errors = []

    for language in project.languages:
        for chapter_path in project.list_chapters(language):
            try:
                doc = Document.load(chapter_path)
                errors = validator.validate_document(
                    doc.content,
                    chapter_path,
                    chapter_path.parent,
                )
                all_errors.extend(errors)
            except Exception as e:
                if console_output:
                    console.print(f"  [yellow]Warning: {chapter_path.name}: {e}[/yellow]")

    if console_output:
        if all_errors:
            console.print(f"[yellow]Found {len(all_errors)} reference issues[/yellow]")
        else:
            console.print("[green]✓ All references valid[/green]")

    return all_errors


def validate_links(
    project: "Project",
    console_output: bool = True,
) -> List[ReferenceError]:
    """
    Validate only links (not citations or ref IDs) in a project.

    Args:
        project: Project to validate
        console_output: Whether to print progress

    Returns:
        List of ReferenceError (only broken_link type)
    """
    all_errors = validate_references(project, console_output=False)
    link_errors = [e for e in all_errors if e.error_type == "broken_link"]

    if console_output:
        if link_errors:
            console.print(f"[yellow]Found {len(link_errors)} broken links[/yellow]")
        else:
            console.print("[green]✓ All links valid[/green]")

    return link_errors
