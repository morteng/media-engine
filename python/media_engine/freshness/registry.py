"""
Content Registry

Central registry for tracking all project content with dependency chains.
Provides freshness computation and untracked content detection.

Uses centralized settings from media_engine.settings for defaults.
"""

import fnmatch
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from .types import ContentType, FreshnessReport, FreshnessStatus, TrackedItem
from ..settings import DEFAULT_IGNORE_PATTERNS, DIRS, FILES

if TYPE_CHECKING:
    from ..core.project import Project


# File extensions tracked by content type
TRACKED_EXTENSIONS: Dict[ContentType, Set[str]] = {
    ContentType.SOURCE_DOCUMENT: {".md", ".yaml", ".yml"},
    ContentType.TRANSLATED_DOCUMENT: {".md"},
    ContentType.VIDEO_SCRIPT: {".yaml", ".yml"},
    ContentType.VIDEO_RENDER: {".mp4", ".webm"},
    ContentType.VOICEOVER_AUDIO: {".mp3", ".wav"},
    ContentType.DEMO_HTML: {".html"},
    ContentType.DEMO_ASSET: {".css", ".js", ".svg", ".png", ".jpg"},
    ContentType.DEMO_CAPTURE: {".mp4", ".webm"},
    ContentType.DIAGRAM_SOURCE: {".yaml", ".yml"},
    ContentType.DIAGRAM_RENDER: {".svg", ".png"},
    ContentType.DELIVERABLE: {".html", ".pdf", ".pptx"},
    ContentType.THEME: {".yaml", ".yml"},
    ContentType.CONFIG: {".yaml", ".yml"},
}

# All tracked extensions
ALL_TRACKED_EXTENSIONS: Set[str] = set()
for exts in TRACKED_EXTENSIONS.values():
    ALL_TRACKED_EXTENSIONS.update(exts)

# Registry file location (from centralized settings)
REGISTRY_FILE = f"{DIRS.media_engine}/{FILES.content_registry}"


class ContentRegistry:
    """Central registry for tracking content freshness and dependencies."""

    def __init__(self, project: "Project"):
        self.project = project
        self.items: Dict[str, TrackedItem] = {}  # path -> TrackedItem
        self._registry_path = project.root / REGISTRY_FILE
        self._loaded = False
        self._provenance_cache: Optional[Dict[str, tuple]] = None
        self._ignore_patterns: Optional[List[str]] = None

    def _load_mediaignore(self) -> List[str]:
        """Load patterns from .mediaignore file."""
        mediaignore_path = self.project.root / ".mediaignore"
        patterns = []

        if mediaignore_path.exists():
            try:
                with open(mediaignore_path) as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except (OSError, IOError):
                pass

        return patterns

    def get_ignore_patterns(self) -> List[str]:
        """Get all ignore patterns from defaults, .mediaignore, and project.yaml."""
        if self._ignore_patterns is not None:
            return self._ignore_patterns

        patterns = list(DEFAULT_IGNORE_PATTERNS)

        # Add patterns from .mediaignore
        patterns.extend(self._load_mediaignore())

        # Add patterns from project.yaml freshness config
        if hasattr(self.project.config, "freshness"):
            patterns.extend(self.project.config.freshness.ignore_patterns)

        self._ignore_patterns = patterns
        return patterns

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on patterns."""
        patterns = self.get_ignore_patterns()
        path_str = str(path)

        for pattern in patterns:
            # Handle glob-style patterns with **
            if "**" in pattern:
                # Convert ** pattern to work with fnmatch
                # Replace ** with a marker, then handle it
                if pattern.startswith("**/"):
                    # Match anywhere in path
                    check_pattern = pattern[3:]  # Remove **/
                    if fnmatch.fnmatch(path_str, f"*{check_pattern}"):
                        return True
                    if fnmatch.fnmatch(path_str, check_pattern):
                        return True
                    # Also check each path component
                    for part in path.parts:
                        if fnmatch.fnmatch(part, check_pattern.split("/")[0]):
                            return True
                elif pattern.endswith("/**"):
                    # Match directory prefix
                    prefix = pattern[:-3]
                    if path_str.startswith(prefix) or f"/{prefix}" in f"/{path_str}":
                        return True
                else:
                    # General ** pattern - try direct match
                    if fnmatch.fnmatch(path_str, pattern.replace("**", "*")):
                        return True
            else:
                # Simple pattern
                if fnmatch.fnmatch(path_str, pattern):
                    return True
                if fnmatch.fnmatch(path.name, pattern):
                    return True

        return False

    def clear_ignore_cache(self) -> None:
        """Clear cached ignore patterns (call after config changes)."""
        self._ignore_patterns = None

    def load(self) -> None:
        """Load registry from disk."""
        if self._registry_path.exists():
            try:
                with open(self._registry_path) as f:
                    data = json.load(f)

                for item_data in data.get("items", {}).values():
                    item = TrackedItem.from_dict(item_data)
                    self.items[str(item.path)] = item

                self._loaded = True
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to load registry: {e}")
                self.items = {}
        else:
            self.items = {}

    def save(self) -> None:
        """Save registry to disk."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0.0",
            "project": self.project.name,
            "last_scan": datetime.now().isoformat(),
            "items": {k: v.to_dict() for k, v in self.items.items()},
        }

        with open(self._registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(
        self,
        path: Path,
        content_type: ContentType,
        depends_on: Optional[List[Path]] = None,
        freshness_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrackedItem:
        """Register a content item for tracking."""
        # Make path relative to project root
        if path.is_absolute():
            try:
                path = path.relative_to(self.project.root)
            except ValueError:
                pass  # Keep absolute if not under project root

        abs_path = self.project.root / path

        # Compute content hash and mtime
        content_hash = ""
        last_modified = None

        if abs_path.exists():
            content_hash = self._compute_hash(abs_path)
            last_modified = datetime.fromtimestamp(abs_path.stat().st_mtime)

        item = TrackedItem(
            path=path,
            content_type=content_type,
            depends_on=depends_on or [],
            last_modified=last_modified,
            last_checked=datetime.now(),
            content_hash=content_hash,
            freshness_days=freshness_days,
            metadata=metadata or {},
        )

        # Compute initial freshness
        item.freshness_status = self._compute_freshness(item)

        self.items[str(path)] = item
        return item

    def unregister(self, path: Path) -> bool:
        """Remove an item from the registry."""
        key = str(path)
        if key in self.items:
            del self.items[key]
            return True
        return False

    def get(self, path: Path) -> Optional[TrackedItem]:
        """Get a tracked item by path."""
        return self.items.get(str(path))

    def get_by_type(self, content_type: ContentType) -> List[TrackedItem]:
        """Get all items of a specific type."""
        return [item for item in self.items.values() if item.content_type == content_type]

    def get_stale(self) -> List[TrackedItem]:
        """Get all stale items."""
        return [
            item
            for item in self.items.values()
            if item.freshness_status == FreshnessStatus.STALE
        ]

    def get_expired(self) -> List[TrackedItem]:
        """Get all expired items."""
        return [
            item
            for item in self.items.values()
            if item.freshness_status == FreshnessStatus.EXPIRED
        ]

    def get_missing(self) -> List[TrackedItem]:
        """Get all missing items (registered but file gone)."""
        return [
            item
            for item in self.items.values()
            if item.freshness_status == FreshnessStatus.MISSING
        ]

    def find_untracked(
        self, scan_dirs: Optional[List[Path]] = None, include_ignored: bool = False
    ) -> Tuple[List[Path], List[Path]]:
        """Find files that exist but aren't tracked.

        Args:
            scan_dirs: Directories to scan. If None, uses default project dirs.
            include_ignored: If True, also returns ignored files separately.

        Returns:
            Tuple of (untracked_files, ignored_files).
            If include_ignored is False, ignored_files will be empty.
        """
        if scan_dirs is None:
            scan_dirs = [
                self.project.content_dir,
                self.project.root / "docs" / "deliverables",
                self.project.output_dir,
            ]

            # Add any additional scan dirs from config
            if hasattr(self.project.config, "freshness"):
                for extra_dir in self.project.config.freshness.scan_dirs:
                    extra_path = self.project.root / extra_dir
                    if extra_path not in scan_dirs:
                        scan_dirs.append(extra_path)

        known_paths = set(self.items.keys())
        untracked = []
        ignored = []

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue

            for file_path in scan_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                # Skip hidden files and common non-content files
                if file_path.name.startswith("."):
                    continue
                if file_path.suffix not in ALL_TRACKED_EXTENSIONS:
                    continue

                try:
                    rel_path = file_path.relative_to(self.project.root)
                except ValueError:
                    continue

                # Check if already tracked
                if str(rel_path) in known_paths:
                    continue

                # Check ignore patterns
                if self._should_ignore(rel_path):
                    if include_ignored:
                        ignored.append(rel_path)
                    continue

                untracked.append(rel_path)

        return untracked, ignored

    def refresh(self, check_provenance: bool = True) -> FreshnessReport:
        """Refresh all items and compute freshness report.

        Args:
            check_provenance: Whether to check provenance issues for documents.
        """
        now = datetime.now()

        # Clear provenance cache for fresh data
        if check_provenance:
            self.clear_provenance_cache()

        # Update all items
        for item in self.items.values():
            abs_path = self.project.root / item.path

            if abs_path.exists():
                item.last_modified = datetime.fromtimestamp(abs_path.stat().st_mtime)
                item.content_hash = self._compute_hash(abs_path)
            else:
                item.freshness_status = FreshnessStatus.MISSING

            item.last_checked = now
            item.freshness_status = self._compute_freshness(item)

            # Check provenance issues for documents
            if check_provenance and item.content_type in (
                ContentType.SOURCE_DOCUMENT,
                ContentType.TRANSLATED_DOCUMENT,
            ):
                if item.freshness_status == FreshnessStatus.FRESH:
                    if self.has_provenance_issues(item.path):
                        item.freshness_status = FreshnessStatus.CLAIMS_ISSUE
                        # Store issue details in metadata
                        unverified, expired, expiring = self.get_provenance_issue_counts(item.path)
                        item.metadata["claims_unverified"] = unverified
                        item.metadata["claims_expired"] = expired
                        item.metadata["claims_expiring"] = expiring

        # Find untracked and ignored files
        untracked, ignored = self.find_untracked(include_ignored=True)

        # Build report
        report = FreshnessReport(
            project_name=self.project.name,
            scan_time=now,
            total_items=len(self.items),
            untracked_files=untracked,
            untracked_count=len(untracked),
            ignored_files=ignored,
            ignored_count=len(ignored),
        )

        for item in self.items.values():
            if item.freshness_status == FreshnessStatus.FRESH:
                report.fresh_count += 1
            elif item.freshness_status == FreshnessStatus.STALE:
                report.stale_count += 1
                report.stale_items.append(item)
            elif item.freshness_status == FreshnessStatus.EXPIRED:
                report.expired_count += 1
                report.expired_items.append(item)
            elif item.freshness_status == FreshnessStatus.MISSING:
                report.missing_count += 1
                report.missing_items.append(item)
            elif item.freshness_status == FreshnessStatus.CLAIMS_ISSUE:
                report.claims_issue_count += 1
                report.claims_issue_items.append(item)

        return report

    def get_dependents(self, path: Path) -> List[TrackedItem]:
        """Get all items that depend on a given path."""
        path_str = str(path)
        dependents = []

        for item in self.items.values():
            if path_str in [str(d) for d in item.depends_on]:
                dependents.append(item)

        return dependents

    def get_impact(self, changed_path: Path) -> List[TrackedItem]:
        """Get all items affected by a change to a file (transitive)."""
        affected = set()
        to_check = [changed_path]

        while to_check:
            current = to_check.pop()
            dependents = self.get_dependents(current)

            for dep in dependents:
                if str(dep.path) not in affected:
                    affected.add(str(dep.path))
                    to_check.append(dep.path)

        return [self.items[p] for p in affected]

    def _compute_freshness(self, item: TrackedItem) -> FreshnessStatus:
        """Compute freshness status for an item."""
        abs_path = self.project.root / item.path

        # Check if file exists
        if not abs_path.exists():
            return FreshnessStatus.MISSING

        # Check if any dependency is newer
        if item.depends_on:
            item_mtime = item.last_modified or datetime.min

            for dep_path in item.depends_on:
                dep_abs = self.project.root / dep_path
                if dep_abs.exists():
                    dep_mtime = datetime.fromtimestamp(dep_abs.stat().st_mtime)
                    if dep_mtime > item_mtime:
                        return FreshnessStatus.STALE

        # Check freshness_days expiration
        if item.freshness_days and item.last_modified:
            age_days = (datetime.now() - item.last_modified).days
            if age_days > item.freshness_days:
                return FreshnessStatus.EXPIRED

        return FreshnessStatus.FRESH

    def _compute_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file content (first 16 chars)."""
        hasher = hashlib.sha256()

        with open(path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        return hasher.hexdigest()[:16]

    def all_paths(self) -> Set[str]:
        """Get all tracked paths."""
        return set(self.items.keys())

    def _load_provenance_issues(self) -> Dict[str, Tuple[int, int, int]]:
        """Load provenance issues for all documents.

        Returns a dict mapping document paths to (unverified, expired, expiring) counts.
        """
        if self._provenance_cache is not None:
            return self._provenance_cache

        try:
            from ..provenance import ProvenanceTracker

            tracker = ProvenanceTracker(self.project)
            issues = tracker.get_documents_with_claim_issues()

            # Aggregate by document path
            doc_issues: Dict[str, Dict[str, int]] = {}
            for path, issue_type, count in issues:
                path_str = str(path)
                if path_str not in doc_issues:
                    doc_issues[path_str] = {"unverified": 0, "expired": 0, "expiring": 0}

                if issue_type == "unverified_claims":
                    doc_issues[path_str]["unverified"] = count
                elif issue_type == "expired_claims":
                    doc_issues[path_str]["expired"] = count
                elif issue_type == "expiring_claims":
                    doc_issues[path_str]["expiring"] = count

            # Convert to tuple format
            self._provenance_cache = {
                path: (data["unverified"], data["expired"], data["expiring"])
                for path, data in doc_issues.items()
            }
            return self._provenance_cache

        except Exception:
            # Provenance module not available or failed
            self._provenance_cache = {}
            return {}

    def has_provenance_issues(self, path: Path) -> bool:
        """Check if a document has provenance issues."""
        issues = self._load_provenance_issues()
        path_str = str(path)

        if path_str not in issues:
            return False

        unverified, expired, _ = issues[path_str]
        # Only count unverified and expired as blocking issues
        return unverified > 0 or expired > 0

    def get_provenance_issue_counts(self, path: Path) -> Tuple[int, int, int]:
        """Get provenance issue counts for a document.

        Returns: (unverified_claims, expired_claims, expiring_soon_claims)
        """
        issues = self._load_provenance_issues()
        return issues.get(str(path), (0, 0, 0))

    def clear_provenance_cache(self) -> None:
        """Clear the cached provenance issues."""
        self._provenance_cache = None
