"""
Changelog Generation for Media Engine

Auto-generates changelogs from:
- Git commit history
- Document version changes
- Translation updates
- Build artifacts

Supports multiple output formats.
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ChangeType(str, Enum):
    """Types of changes for categorization."""

    ADDED = "added"
    CHANGED = "changed"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    FIXED = "fixed"
    SECURITY = "security"
    TRANSLATION = "translation"
    DOCUMENTATION = "documentation"


@dataclass
class ChangeEntry:
    """A single changelog entry."""

    type: ChangeType
    description: str
    date: datetime
    author: Optional[str] = None
    commit: Optional[str] = None
    files: list[str] = field(default_factory=list)
    breaking: bool = False


@dataclass
class ChangelogVersion:
    """A version section in the changelog."""

    version: str
    date: datetime
    entries: list[ChangeEntry] = field(default_factory=list)
    summary: Optional[str] = None


class GitHistoryParser:
    """Parses git history for changelog entries."""

    # Patterns for conventional commits
    COMMIT_PATTERNS = {
        "feat": ChangeType.ADDED,
        "add": ChangeType.ADDED,
        "fix": ChangeType.FIXED,
        "docs": ChangeType.DOCUMENTATION,
        "refactor": ChangeType.CHANGED,
        "update": ChangeType.CHANGED,
        "change": ChangeType.CHANGED,
        "remove": ChangeType.REMOVED,
        "delete": ChangeType.REMOVED,
        "deprecate": ChangeType.DEPRECATED,
        "security": ChangeType.SECURITY,
        "translate": ChangeType.TRANSLATION,
        "i18n": ChangeType.TRANSLATION,
        "l10n": ChangeType.TRANSLATION,
    }

    def __init__(self, project):
        self.project = project
        self.root = project.root

    def get_commits(
        self,
        since: datetime = None,
        until: datetime = None,
        path_filter: str = None,
    ) -> list[dict]:
        """Get git commits within date range."""
        cmd = [
            "git",
            "log",
            "--format=%H|%an|%aI|%s",
            "--date=iso",
        ]

        if since:
            cmd.append(f"--since={since.isoformat()}")
        if until:
            cmd.append(f"--until={until.isoformat()}")
        if path_filter:
            cmd.extend(["--", path_filter])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    {
                        "hash": parts[0],
                        "author": parts[1],
                        "date": datetime.fromisoformat(parts[2].replace("Z", "+00:00")),
                        "message": parts[3],
                    }
                )

        return commits

    def get_changed_files(self, commit_hash: str) -> list[str]:
        """Get files changed in a commit."""
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            return [f for f in result.stdout.strip().split("\n") if f]
        except subprocess.CalledProcessError:
            return []

    def parse_commit_type(self, message: str) -> tuple[ChangeType, str, bool]:
        """
        Parse commit message to extract type and clean description.

        Returns:
            Tuple of (change_type, description, is_breaking)
        """
        message = message.strip()
        breaking = False

        # Check for breaking change indicator
        if message.startswith("!") or "BREAKING" in message.upper():
            breaking = True
            message = message.lstrip("! ")

        # Check conventional commit format: type(scope): description
        # or type: description
        lower_msg = message.lower()

        for prefix, change_type in self.COMMIT_PATTERNS.items():
            if lower_msg.startswith(f"{prefix}:") or lower_msg.startswith(f"{prefix}("):
                # Extract description after the prefix
                if ":" in message:
                    description = message.split(":", 1)[1].strip()
                else:
                    description = message
                return change_type, description, breaking

        # Default to CHANGED for unrecognized patterns
        return ChangeType.CHANGED, message, breaking

    def to_entries(self, commits: list[dict]) -> list[ChangeEntry]:
        """Convert git commits to changelog entries."""
        entries = []

        for commit in commits:
            change_type, description, breaking = self.parse_commit_type(commit["message"])
            files = self.get_changed_files(commit["hash"])

            # Filter to content files for documentation changelog
            content_files = [f for f in files if f.startswith("content/") or f.endswith(".md")]

            entries.append(
                ChangeEntry(
                    type=change_type,
                    description=description,
                    date=commit["date"],
                    author=commit["author"],
                    commit=commit["hash"][:7],
                    files=content_files if content_files else files[:5],  # Limit file list
                    breaking=breaking,
                )
            )

        return entries


class DocumentVersionTracker:
    """Tracks document version changes for changelog."""

    def __init__(self, project):
        self.project = project

    def get_version_changes(self, since: datetime = None) -> list[ChangeEntry]:
        """Get document version changes."""
        from ..cms.document import Document

        entries = []

        for lang in self.project.languages:
            for chapter_path in self.project.list_chapters(lang):
                doc = Document.load(chapter_path)

                # Check if document was modified recently
                mtime = datetime.fromtimestamp(chapter_path.stat().st_mtime)
                if since and mtime < since:
                    continue

                status = doc.metadata.get("status", "draft")

                # Create entry based on status
                if status == "published":
                    entries.append(
                        ChangeEntry(
                            type=ChangeType.DOCUMENTATION,
                            description=f"Published: {doc.title}",
                            date=mtime,
                            files=[str(chapter_path.relative_to(self.project.root))],
                        )
                    )
                elif "translated" in doc.metadata.get("tags", []):
                    entries.append(
                        ChangeEntry(
                            type=ChangeType.TRANSLATION,
                            description=f"Translated: {doc.title} ({lang})",
                            date=mtime,
                            files=[str(chapter_path.relative_to(self.project.root))],
                        )
                    )

        return entries


class ChangelogGenerator:
    """
    Generates changelogs from various sources.

    Usage:
        generator = ChangelogGenerator(project)
        changelog = generator.generate()
        markdown = generator.to_markdown(changelog)
    """

    def __init__(self, project):
        self.project = project
        self.git_parser = GitHistoryParser(project)
        self.doc_tracker = DocumentVersionTracker(project)

    def generate(
        self,
        since: datetime = None,
        include_git: bool = True,
        include_docs: bool = True,
        group_by_version: bool = False,
    ) -> list[ChangeEntry]:
        """
        Generate changelog entries.

        Args:
            since: Only include changes since this date
            include_git: Include git commit history
            include_docs: Include document version changes
            group_by_version: Group entries by version tag

        Returns:
            List of ChangeEntry objects
        """
        entries = []

        if include_git:
            commits = self.git_parser.get_commits(
                since=since,
                path_filter="content/" if include_docs else None,
            )
            entries.extend(self.git_parser.to_entries(commits))

        if include_docs:
            entries.extend(self.doc_tracker.get_version_changes(since=since))

        # Sort by date descending
        entries.sort(key=lambda e: e.date, reverse=True)

        # Remove duplicates (same description on same day)
        seen = set()
        unique = []
        for entry in entries:
            key = (entry.description.lower()[:50], entry.date.date())
            if key not in seen:
                seen.add(key)
                unique.append(entry)

        return unique

    def to_markdown(
        self,
        entries: list[ChangeEntry],
        title: str = "Changelog",
        group_by_type: bool = True,
    ) -> str:
        """Convert entries to markdown format."""
        lines = [f"# {title}\n"]

        if not entries:
            lines.append("No changes recorded.\n")
            return "\n".join(lines)

        if group_by_type:
            # Group by change type
            by_type = {}
            for entry in entries:
                if entry.type not in by_type:
                    by_type[entry.type] = []
                by_type[entry.type].append(entry)

            # Order of sections
            type_order = [
                ChangeType.ADDED,
                ChangeType.CHANGED,
                ChangeType.FIXED,
                ChangeType.SECURITY,
                ChangeType.TRANSLATION,
                ChangeType.DOCUMENTATION,
                ChangeType.DEPRECATED,
                ChangeType.REMOVED,
            ]

            for change_type in type_order:
                if change_type in by_type:
                    lines.append(f"\n## {change_type.value.title()}\n")
                    for entry in by_type[change_type]:
                        breaking = " **BREAKING**" if entry.breaking else ""
                        date_str = entry.date.strftime("%Y-%m-%d")
                        lines.append(f"- {entry.description}{breaking} ({date_str})")
        else:
            # Chronological list
            current_date = None
            for entry in entries:
                entry_date = entry.date.date()
                if entry_date != current_date:
                    current_date = entry_date
                    lines.append(f"\n## {entry_date.isoformat()}\n")

                breaking = " **BREAKING**" if entry.breaking else ""
                type_badge = f"[{entry.type.value}]"
                lines.append(f"- {type_badge} {entry.description}{breaking}")

        return "\n".join(lines)

    def to_json(self, entries: list[ChangeEntry]) -> list[dict]:
        """Convert entries to JSON-serializable format."""
        return [
            {
                "type": entry.type.value,
                "description": entry.description,
                "date": entry.date.isoformat(),
                "author": entry.author,
                "commit": entry.commit,
                "files": entry.files,
                "breaking": entry.breaking,
            }
            for entry in entries
        ]


def generate_changelog(
    project,
    since: datetime = None,
    format: str = "markdown",
) -> str:
    """
    Convenience function to generate changelog.

    Args:
        project: Project instance
        since: Only include changes since this date
        format: Output format ("markdown" or "json")

    Returns:
        Formatted changelog string
    """
    import json

    generator = ChangelogGenerator(project)
    entries = generator.generate(since=since)

    if format == "json":
        return json.dumps(generator.to_json(entries), indent=2)
    return generator.to_markdown(entries)


__all__ = [
    "ChangeType",
    "ChangeEntry",
    "ChangelogVersion",
    "ChangelogGenerator",
    "generate_changelog",
]
