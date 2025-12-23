"""
Translation tracking for multilingual document management.

Tracks source documents and their translations, detecting when translations
become outdated due to source document updates.

Supports two tracking modes:
1. **Hash-based** (preferred): Uses content hash for automatic change detection
2. **Version-based** (fallback): Uses semantic version comparison

Hash-based tracking is automatic - any content change is detected.
Version-based requires manual version bumps in source documents.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .document import Document


def compute_content_hash(content: str) -> str:
    """
    Compute a stable hash of document content for change detection.

    Normalizes whitespace and ignores frontmatter to focus on actual content changes.
    """
    # Normalize: strip, collapse whitespace, lowercase for stability
    normalized = " ".join(content.split()).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


@dataclass
class TranslationStatus:
    """Status of a translation relative to its source document."""

    source_path: Path
    translation_path: Path
    source_version: str
    translated_version: str  # version of source when translation was made
    is_outdated: bool
    source_language: str
    target_language: str
    source_title: str
    translation_title: str

    # Hash-based tracking fields
    source_content_hash: str = ""  # Current hash of source content
    translated_from_hash: str = ""  # Hash of source when translation was made
    tracking_mode: str = "version"  # "hash" or "version"
    content_changed: bool = False  # True if content hash differs

    # Additional context
    source_last_modified: str = ""
    translation_last_modified: str = ""

    @property
    def status_label(self) -> str:
        """Human-readable status label."""
        if self.is_outdated:
            if self.tracking_mode == "hash" and self.content_changed:
                return "outdated (content changed)"
            return "outdated"
        return "current"

    @property
    def needs_review(self) -> bool:
        """Whether this translation needs human review."""
        return self.is_outdated or self.content_changed


class TranslationTracker:
    """
    Tracks translations and their sync status with source documents.

    Uses frontmatter fields:
    - source_document: relative path to source (e.g., "en/chapters/01_intro.md")
    - source_version: version of source when translation was made
    - language: target language code
    """

    def __init__(self, project):
        """
        Initialize tracker with a project.

        Args:
            project: Project instance to track translations for
        """
        self.project = project
        self._translations: dict[Path, Document] = {}
        self._sources: dict[Path, Document] = {}
        self._loaded = False

    def _load_documents(self) -> None:
        """Load all documents from project."""
        if self._loaded:
            return

        self._translations.clear()
        self._sources.clear()

        for lang_code in self.project.languages:
            for chapter_path in self.project.list_chapters(lang_code):
                try:
                    doc = Document.load(chapter_path)
                    source_doc = doc.metadata.get("source_document")

                    if source_doc:
                        # This is a translation
                        self._translations[chapter_path] = doc
                    else:
                        # This is a source document
                        self._sources[chapter_path] = doc
                except Exception:
                    pass

        self._loaded = True

    def _resolve_source_path(self, source_ref: str) -> Optional[Path]:
        """Resolve a source_document reference to an absolute path."""
        # source_ref is relative to content dir, e.g., "en/chapters/01_intro.md"
        content_dir = self.project.content_dir
        source_path = content_dir / source_ref

        if source_path.exists():
            return source_path

        return None

    def get_translation_pairs(self) -> list[tuple[Document, Document]]:
        """
        Get all source-translation document pairs.

        Returns:
            List of (source_doc, translation_doc) tuples
        """
        self._load_documents()
        pairs = []

        for trans_path, trans_doc in self._translations.items():
            source_ref = trans_doc.metadata.get("source_document")
            if not source_ref:
                continue

            source_path = self._resolve_source_path(source_ref)
            if source_path and source_path in self._sources:
                pairs.append((self._sources[source_path], trans_doc))

        return pairs

    def get_status(self, translation: Document) -> Optional[TranslationStatus]:
        """
        Get the translation status for a single document.

        Uses hash-based tracking if source_content_hash is present in frontmatter,
        otherwise falls back to version-based comparison.

        Args:
            translation: Document to check

        Returns:
            TranslationStatus or None if not a translation
        """
        source_ref = translation.metadata.get("source_document")
        if not source_ref:
            return None

        source_path = self._resolve_source_path(source_ref)
        if not source_path or not source_path.exists():
            return None

        try:
            source_doc = Document.load(source_path)
        except Exception:
            return None

        source_version = source_doc.version
        translated_version = translation.metadata.get("source_version", "0.0.0")

        # Compute current source content hash
        current_source_hash = compute_content_hash(source_doc.content)

        # Check for hash-based tracking
        translated_from_hash = translation.metadata.get("source_content_hash", "")
        tracking_mode = "hash" if translated_from_hash else "version"

        # Determine if outdated
        if tracking_mode == "hash":
            # Hash-based: compare content hashes
            content_changed = translated_from_hash != current_source_hash
            is_outdated = content_changed
        else:
            # Version-based: compare semantic versions
            content_changed = False
            is_outdated = self._compare_versions(source_version, translated_version) > 0

        # Extract language codes
        source_lang = self._extract_language(source_path)
        target_lang = translation.metadata.get("language") or self._extract_language(
            translation.path
        )

        # Get last modified dates
        source_last_mod = source_doc.metadata.get("last_modified", "")
        trans_last_mod = translation.metadata.get("last_modified", "")

        return TranslationStatus(
            source_path=source_path,
            translation_path=translation.path,
            source_version=source_version,
            translated_version=translated_version,
            is_outdated=is_outdated,
            source_language=source_lang,
            target_language=target_lang,
            source_title=source_doc.title,
            translation_title=translation.title,
            source_content_hash=current_source_hash,
            translated_from_hash=translated_from_hash,
            tracking_mode=tracking_mode,
            content_changed=content_changed,
            source_last_modified=source_last_mod,
            translation_last_modified=trans_last_mod,
        )

    def _extract_language(self, path: Path) -> str:
        """Extract language code from path."""
        content_dir = self.project.content_dir
        try:
            rel_path = path.relative_to(content_dir)
            # First part of path is language code
            return rel_path.parts[0]
        except (ValueError, IndexError):
            return "unknown"

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns:
            > 0 if v1 > v2, < 0 if v1 < v2, 0 if equal
        """

        def parse_version(v: str) -> tuple[int, int, int]:
            parts = v.split(".")
            try:
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                return (major, minor, patch)
            except ValueError:
                return (0, 0, 0)

        p1 = parse_version(v1)
        p2 = parse_version(v2)

        if p1 > p2:
            return 1
        elif p1 < p2:
            return -1
        return 0

    def get_outdated_translations(self) -> list[TranslationStatus]:
        """
        Get all translations that are outdated.

        Returns:
            List of TranslationStatus for outdated translations
        """
        self._load_documents()
        outdated = []

        for trans_doc in self._translations.values():
            status = self.get_status(trans_doc)
            if status and status.is_outdated:
                outdated.append(status)

        return outdated

    def get_sync_status(self) -> dict[str, list[TranslationStatus]]:
        """
        Get sync status grouped by target language.

        Returns:
            Dict mapping language codes to list of TranslationStatus
        """
        self._load_documents()
        by_language: dict[str, list[TranslationStatus]] = {}

        for trans_doc in self._translations.values():
            status = self.get_status(trans_doc)
            if status:
                lang = status.target_language
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(status)

        return by_language

    def get_missing_translations(self, target_language: str) -> list[Document]:
        """
        Get source documents that don't have a translation in target language.

        Args:
            target_language: Language code to check for translations

        Returns:
            List of source documents missing translations
        """
        self._load_documents()
        missing = []

        # Get all source documents
        source_paths = set(self._sources.keys())

        # Get translated source paths for target language
        translated_sources = set()
        for trans_doc in self._translations.values():
            trans_lang = trans_doc.metadata.get("language") or self._extract_language(
                trans_doc.path
            )
            if trans_lang == target_language:
                source_ref = trans_doc.metadata.get("source_document")
                if source_ref:
                    source_path = self._resolve_source_path(source_ref)
                    if source_path:
                        translated_sources.add(source_path)

        # Find missing
        for source_path in source_paths:
            source_lang = self._extract_language(source_path)
            # Only check source language documents
            if source_lang == self.project.source_language:
                if source_path not in translated_sources:
                    missing.append(self._sources[source_path])

        return missing

    def mark_synced(self, translation: Document, use_hash: bool = True) -> dict:
        """
        Mark a translation as synced with current source version.

        Updates both source_version and source_content_hash in the
        translation's frontmatter for comprehensive tracking.

        Args:
            translation: Translation document to update
            use_hash: Whether to also record content hash (default: True)

        Returns:
            Dict with sync details including old/new versions and hashes
        """
        source_ref = translation.metadata.get("source_document")
        if not source_ref:
            return {"error": "No source_document reference"}

        source_path = self._resolve_source_path(source_ref)
        if not source_path or not source_path.exists():
            return {"error": f"Source not found: {source_ref}"}

        try:
            source_doc = Document.load(source_path)

            # Capture old values
            old_version = translation.metadata.get("source_version", "")
            old_hash = translation.metadata.get("source_content_hash", "")

            # Update version
            translation.metadata["source_version"] = source_doc.version

            # Update content hash for automatic tracking
            if use_hash:
                content_hash = compute_content_hash(source_doc.content)
                translation.metadata["source_content_hash"] = content_hash
            else:
                content_hash = ""

            translation.save()

            return {
                "status": "synced",
                "source": str(source_path),
                "translation": str(translation.path),
                "old_version": old_version,
                "new_version": source_doc.version,
                "old_hash": old_hash,
                "new_hash": content_hash,
                "tracking_mode": "hash" if use_hash else "version",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_all_statuses(self) -> list[TranslationStatus]:
        """
        Get status for all translations.

        Returns:
            List of all TranslationStatus objects
        """
        self._load_documents()
        statuses = []

        for trans_doc in self._translations.values():
            status = self.get_status(trans_doc)
            if status:
                statuses.append(status)

        return statuses

    def refresh(self) -> None:
        """Force refresh of cached document data."""
        self._loaded = False
        self._load_documents()
