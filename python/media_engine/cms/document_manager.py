"""Document Manager - A facade for document operations.

Provides a unified interface for listing and managing documents across
all languages and types in a media-engine project.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from .document import Document

if TYPE_CHECKING:
    from ..core.project import Project


class DocumentManager:
    """Facade for document operations across a project.

    Provides simplified access to documents without needing to know
    the underlying project structure.
    """

    def __init__(self, project: "Project"):
        """Initialize with a project instance.

        Args:
            project: The media-engine project to manage documents for.
        """
        self.project = project

    def list_documents(self, language: str = None) -> list[dict]:
        """List all documents with their metadata.

        Args:
            language: Optional language filter. If None, returns all languages.

        Returns:
            List of document dicts with path, title, language, status, etc.
        """
        documents = []

        # Determine which languages to include
        if language:
            languages = [language] if language in self.project.languages else []
        else:
            languages = list(self.project.languages.keys())

        for lang in languages:
            # Chapters
            try:
                for chapter in self.project.list_chapters(lang):
                    doc_info = self._doc_to_dict(chapter, lang, "chapter")
                    if doc_info:
                        documents.append(doc_info)
            except Exception:
                pass

            # Scripts
            try:
                for script in self.project.list_scripts(lang):
                    doc_info = self._doc_to_dict(script, lang, "script")
                    if doc_info:
                        documents.append(doc_info)
            except Exception:
                pass

            # Guides
            try:
                guides_dir = self.project.content_dir / lang / "guides"
                if guides_dir.exists():
                    for guide in guides_dir.glob("*.md"):
                        doc_info = self._doc_to_dict(guide, lang, "guide")
                        if doc_info:
                            documents.append(doc_info)
            except Exception:
                pass

            # Reference docs
            try:
                ref_dir = self.project.content_dir / lang / "reference"
                if ref_dir.exists():
                    for ref in ref_dir.glob("*.md"):
                        doc_info = self._doc_to_dict(ref, lang, "reference")
                        if doc_info:
                            documents.append(doc_info)
            except Exception:
                pass

            # Any other markdown files in language dir
            try:
                lang_dir = self.project.content_dir / lang
                if lang_dir.exists():
                    for md_file in lang_dir.glob("*.md"):
                        # Skip if already added via specific type
                        rel_path = md_file.relative_to(self.project.content_dir)
                        if not any(d["path"] == str(rel_path) for d in documents):
                            doc_info = self._doc_to_dict(md_file, lang, "document")
                            if doc_info:
                                documents.append(doc_info)
            except Exception:
                pass

        return documents

    def _doc_to_dict(self, path: Path, language: str, doc_type: str) -> dict | None:
        """Convert a document path to a dictionary with metadata.

        Args:
            path: Path to the document file.
            language: Language code.
            doc_type: Type of document (chapter, script, guide, etc.)

        Returns:
            Dict with document info, or None if loading fails.
        """
        try:
            doc = Document.load(path)
            rel_path = path.relative_to(self.project.content_dir)

            return {
                "path": str(rel_path),
                "absolute_path": str(path),
                "filename": path.name,
                "title": doc.title,
                "language": language,
                "type": doc_type,
                "status": doc.metadata.get("status", "unknown"),
                "version": doc.metadata.get("version", "1.0.0"),
                "tags": doc.metadata.get("tags", []),
                "source_document": doc.metadata.get("source_document"),
                "source_version": doc.metadata.get("source_version"),
            }
        except Exception:
            return None

    def get_document(self, path: str) -> dict | None:
        """Get a specific document by path.

        Args:
            path: Relative path to the document from content dir.

        Returns:
            Document info dict, or None if not found.
        """
        doc_path = self.project.content_dir / path
        if not doc_path.exists():
            # Try stripping leading slash
            doc_path = self.project.content_dir / path.lstrip("/")

        if not doc_path.exists():
            return None

        try:
            doc = Document.load(doc_path)
            rel_path = doc_path.relative_to(self.project.content_dir)

            # Determine language from path
            parts = rel_path.parts
            language = parts[0] if parts else "unknown"

            # Determine type from path
            if len(parts) > 1:
                if parts[1] == "chapters":
                    doc_type = "chapter"
                elif parts[1] == "scripts":
                    doc_type = "script"
                elif parts[1] == "guides":
                    doc_type = "guide"
                elif parts[1] == "reference":
                    doc_type = "reference"
                else:
                    doc_type = "document"
            else:
                doc_type = "document"

            return {
                "path": str(rel_path),
                "absolute_path": str(doc_path),
                "filename": doc_path.name,
                "title": doc.title,
                "language": language,
                "type": doc_type,
                "status": doc.metadata.get("status", "unknown"),
                "version": doc.metadata.get("version", "1.0.0"),
                "content": doc.content,
                "metadata": doc.metadata,
            }
        except Exception:
            return None

    def count_by_language(self) -> dict[str, int]:
        """Count documents by language.

        Returns:
            Dict mapping language code to document count.
        """
        counts = {}
        for lang in self.project.languages:
            docs = self.list_documents(language=lang)
            counts[lang] = len(docs)
        return counts

    def count_by_status(self) -> dict[str, int]:
        """Count documents by status.

        Returns:
            Dict mapping status to document count.
        """
        docs = self.list_documents()
        counts = {}
        for doc in docs:
            status = doc.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def count_by_type(self) -> dict[str, int]:
        """Count documents by type.

        Returns:
            Dict mapping type to document count.
        """
        docs = self.list_documents()
        counts = {}
        for doc in docs:
            doc_type = doc.get("type", "document")
            counts[doc_type] = counts.get(doc_type, 0) + 1
        return counts
