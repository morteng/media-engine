"""Document management tools.

Provides tools for managing documents including:
- Listing and reading documents
- Creating new documents with proper structure
- Updating metadata and content
- Deleting/archiving documents
- Scaffolding documents from templates
"""

import json
import shutil
from datetime import date
from pathlib import Path


def register_document_tools(mcp, server_instance):
    """Register document-related MCP tools."""

    @mcp.tool()
    async def list_chapters(language: str = None) -> str:
        """
        List all chapters for a language.

        Args:
            language: Language code (default: source language)

        Returns list of chapters with titles and metadata.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...cms.document import Document

        lang = language or server_instance.project.source_language

        if lang not in server_instance.project.languages:
            return json.dumps({"error": f"Language '{lang}' not configured"}, indent=2)

        chapters = server_instance.project.list_chapters(lang)
        return json.dumps(
            [
                {
                    "path": str(c),
                    "filename": c.name,
                    "title": Document.load(c).title,
                    "version": Document.load(c).metadata.get("version", ""),
                    "status": Document.load(c).metadata.get("status", ""),
                }
                for c in chapters
            ],
            indent=2,
        )

    @mcp.tool()
    async def read_document(path: str) -> str:
        """
        Read a document's content and metadata.

        Args:
            path: Path to document file

        Returns document title, content, and all frontmatter metadata.
        """
        from ...cms.document import Document

        try:
            validated_path = server_instance._validate_path(path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Document not found: {path}"}, indent=2)

        doc = Document.load(validated_path)
        return json.dumps(
            {
                "path": str(validated_path),
                "title": doc.title,
                "content": doc.content,
                "metadata": doc.metadata,
                "word_count": len(doc.content.split()),
            },
            indent=2,
        )

    @mcp.tool()
    async def update_document_metadata(path: str, updates: str) -> str:
        """
        Update a document's frontmatter metadata.

        Args:
            path: Path to document file
            updates: JSON string of metadata updates

        Example: update_document_metadata("doc.md", '{"status": "reviewed"}')
        """
        from ...cms.document import Document

        try:
            validated_path = server_instance._validate_path(path)
            updates_dict = json.loads(updates)
        except (ValueError, json.JSONDecodeError) as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Document not found: {path}"}, indent=2)

        doc = Document.load(validated_path)
        doc.metadata.update(updates_dict)
        doc.save()

        server_instance._invalidate_cache()
        return json.dumps(
            {
                "status": "updated",
                "path": str(validated_path),
                "updated_fields": list(updates_dict.keys()),
            },
            indent=2,
        )

    @mcp.tool()
    async def increment_document_version(path: str, bump: str = "patch") -> str:
        """
        Increment a document's version number.

        Args:
            path: Path to document file
            bump: Version bump type - "major", "minor", or "patch"
        """
        from ...cms.document import Document

        try:
            validated_path = server_instance._validate_path(path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if bump not in ("major", "minor", "patch"):
            return json.dumps({"error": "bump must be 'major', 'minor', or 'patch'"}, indent=2)

        doc = Document.load(validated_path)
        old_version = doc.metadata.get("version", "0.0.0")
        doc.increment_version(bump)
        doc.save()

        server_instance._invalidate_cache()
        return json.dumps(
            {
                "status": "version_incremented",
                "path": str(validated_path),
                "old_version": old_version,
                "new_version": doc.metadata.get("version"),
            },
            indent=2,
        )

    @mcp.tool()
    async def create_document(
        path: str,
        title: str,
        doc_type: str = "chapter",
        content: str = "",
        language: str = None,
        source_document: str = None,
        source_version: str = None,
        status: str = "draft",
        tags: str = None,
    ) -> str:
        """
        Create a new document with proper frontmatter structure.

        Args:
            path: Relative path for the new document (e.g., "content/en/chapters/17_new_chapter.md")
            title: Document title
            doc_type: Type of document - chapter, script, slide, diagram, data, translation
            content: Initial markdown content (optional)
            language: Language code (auto-detected from path if not provided)
            source_document: For translations, path to source document
            source_version: For translations, version of source being translated
            status: Initial status - draft, in_review, approved, final (default: draft)
            tags: Comma-separated list of tags (optional)

        Returns:
            Created document info including full path.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project

        # Build full path
        if path.startswith("/"):
            full_path = Path(path)
        else:
            full_path = project.root / path

        # Validate path is within project
        try:
            resolved = full_path.resolve()
            if not str(resolved).startswith(str(project.root.resolve())):
                return json.dumps({"error": "Path must be within project root"}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Invalid path: {e}"}, indent=2)

        # Check if file already exists
        if full_path.exists():
            return json.dumps({"error": f"Document already exists: {path}"}, indent=2)

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Auto-detect language from path
        if not language:
            path_parts = full_path.parts
            for lang in project.languages:
                if lang in path_parts:
                    language = lang
                    break

        # Build metadata
        metadata = {
            "title": title,
            "version": "1.0.0",
            "status": status,
            "last_modified": date.today().isoformat(),
        }

        # Add language for non-source documents
        if language and language != project.source_language:
            metadata["language"] = language

        # Add translation metadata
        if source_document:
            metadata["source_document"] = source_document
            metadata["source_version"] = source_version or "1.0.0"

        # Add type-specific metadata
        if doc_type in ["chapter", "translation"]:
            metadata["freshness_days"] = 60

        # Add tags
        if tags:
            metadata["tags"] = [t.strip() for t in tags.split(",")]

        # Build frontmatter
        import frontmatter

        post = frontmatter.Post(content or f"# {title}\n\n", **metadata)

        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "created",
                "path": str(full_path),
                "relative_path": str(full_path.relative_to(project.root)),
                "title": title,
                "doc_type": doc_type,
                "language": language,
                "metadata": metadata,
            },
            indent=2,
        )

    @mcp.tool()
    async def update_document_content(
        path: str,
        content: str,
        update_modified: bool = True,
        increment_version: str = None,
    ) -> str:
        """
        Update a document's content (body text).

        Args:
            path: Path to document file
            content: New markdown content (replaces existing body)
            update_modified: Whether to update last_modified date (default: True)
            increment_version: Version bump type - "major", "minor", "patch", or None

        Returns:
            Updated document info.
        """
        from ...cms.document import Document

        try:
            validated_path = server_instance._validate_path(path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Document not found: {path}"}, indent=2)

        doc = Document.load(validated_path)
        old_word_count = doc.word_count()

        # Update content
        doc.content = content
        new_word_count = doc.word_count()

        # Update metadata
        if update_modified:
            doc.metadata["last_modified"] = date.today().isoformat()

        if increment_version and increment_version in ("major", "minor", "patch"):
            doc.increment_version(increment_version)

        doc.save()
        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "content_updated",
                "path": str(validated_path),
                "old_word_count": old_word_count,
                "new_word_count": new_word_count,
                "version": doc.metadata.get("version"),
                "last_modified": doc.metadata.get("last_modified"),
            },
            indent=2,
        )

    @mcp.tool()
    async def delete_document(
        path: str,
        archive: bool = True,
        check_dependencies: bool = True,
    ) -> str:
        """
        Delete or archive a document.

        By default, documents are moved to .archive/ instead of permanently deleted.
        Use archive=False for permanent deletion (use with caution).

        Args:
            path: Path to document file
            archive: If True, move to .archive/ instead of deleting (default: True)
            check_dependencies: If True, check for dependent documents first (default: True)

        Returns:
            Deletion status and any dependency warnings.
        """

        try:
            validated_path = server_instance._validate_path(path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Document not found: {path}"}, indent=2)

        project = server_instance.project
        warnings = []

        # Check for dependencies
        if check_dependencies:
            try:
                from ...relationships import get_registry_manager, init_registry_manager

                registry_manager = get_registry_manager(project)
                if registry_manager is None:
                    registry_manager = init_registry_manager(project)

                # Find documents that depend on this one
                dependents = registry_manager.registry.get_impact(validated_path)

                if dependents:
                    warnings.append(
                        f"Found {len(dependents)} documents depending on this: {[str(d) for d in list(dependents)[:5]]}"
                    )
            except Exception:
                pass  # Dependency checking is optional

            # Check for translations of this document
            try:
                from ...translation.tracker import TranslationTracker

                tracker = TranslationTracker(project)
                pairs = tracker.get_translation_pairs()

                translations = []
                for pair in pairs:
                    if str(validated_path) in str(pair.get("source", "")):
                        translations.append(pair.get("translation"))

                if translations:
                    warnings.append(f"Found {len(translations)} translations of this document")
            except Exception:
                pass

        # Perform deletion/archival
        if archive:
            # Create archive directory
            archive_dir = project.root / ".archive"
            archive_dir.mkdir(exist_ok=True)

            # Preserve relative path structure in archive
            rel_path = validated_path.relative_to(project.root)
            archive_path = archive_dir / rel_path
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            # Move to archive
            shutil.move(str(validated_path), str(archive_path))

            server_instance._invalidate_cache()
            return json.dumps(
                {
                    "status": "archived",
                    "original_path": str(validated_path),
                    "archive_path": str(archive_path),
                    "warnings": warnings,
                    "note": "Document moved to .archive/. "
                    "Use archive=False for permanent deletion.",
                },
                indent=2,
            )
        else:
            # Permanent deletion
            validated_path.unlink()

            server_instance._invalidate_cache()
            return json.dumps(
                {
                    "status": "deleted",
                    "path": str(validated_path),
                    "warnings": warnings,
                    "note": "Document permanently deleted. This cannot be undone.",
                },
                indent=2,
            )

    @mcp.tool()
    async def scaffold_document(
        doc_type: str,
        language: str = None,
        title: str = None,
        source_path: str = None,
    ) -> str:
        """
        Generate document content/structure ready to write.

        Unlike create_document which writes directly, this returns the content
        for review before writing. Useful for AI-assisted document creation.

        Args:
            doc_type: Type of document to scaffold:
                - "chapter": Standard documentation chapter
                - "translation": Translation of existing document (requires source_path)
                - "script": Video script YAML
                - "slide": Presentation slides YAML
                - "diagram": Diagram definition YAML
                - "data": Data spreadsheet YAML
            language: Target language code
            title: Document title (auto-generated if not provided)
            source_path: For translations, path to source document to translate

        Returns:
            Scaffolded content with suggested path and metadata.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        language = language or project.source_language

        result = {
            "doc_type": doc_type,
            "language": language,
            "suggested_path": None,
            "content": None,
            "metadata": None,
        }

        if doc_type == "chapter":
            # Find next chapter number
            chapters = project.list_chapters(language)
            next_num = len(chapters) + 1

            slug = _slugify(title) if title else "new_chapter"
            filename = f"{next_num:02d}_{slug}.md"

            result["suggested_path"] = f"content/{language}/chapters/{filename}"
            result["metadata"] = {
                "title": title or "New Chapter",
                "version": "1.0.0",
                "status": "draft",
                "last_modified": date.today().isoformat(),
                "freshness_days": 60,
                "tags": [],
            }
            result["content"] = f"""# {title or "New Chapter"}

## Overview

[Provide an overview of this chapter's content]

## Section 1

[First main section]

## Section 2

[Second main section]

## Summary

[Summarize the key points]
"""

        elif doc_type == "translation":
            if not source_path:
                return json.dumps(
                    {"error": "source_path required for translation scaffold"},
                    indent=2,
                )

            # Load source document
            from ...cms.document import Document

            try:
                source_full = server_instance._validate_path(source_path)
                source_doc = Document.load(source_full)
            except Exception as e:
                return json.dumps({"error": f"Cannot load source: {e}"}, indent=2)

            # Generate translated filename
            source_name = source_full.stem
            slug = _slugify(title) if title else source_name

            result["suggested_path"] = f"content/{language}/chapters/{slug}.md"
            result["metadata"] = {
                "title": title or f"[Translate: {source_doc.title}]",
                "version": "1.0.0",
                "status": "draft",
                "last_modified": date.today().isoformat(),
                "language": language,
                "source_document": source_path,
                "source_version": source_doc.version,
                "freshness_days": 60,
            }
            result["content"] = f"""# {title or f"[Translate: {source_doc.title}]"}

<!-- Source document: {source_path} -->
<!-- Translate the content below -->

{source_doc.content}
"""
            result["source_info"] = {
                "title": source_doc.title,
                "version": source_doc.version,
                "word_count": source_doc.word_count(),
            }

        elif doc_type == "script":
            slug = _slugify(title) if title else "new_script"
            result["suggested_path"] = f"content/{language}/scripts/{slug}.yaml"
            result["content"] = f"""# Video Script: {title or "New Script"}
title: "{title or "New Script"}"
description: "[Script description]"
duration_estimate: "3:00"
voice_id: null  # ElevenLabs voice ID

scenes:
  - id: intro
    type: intro
    duration: 5
    voiceover: |
      Welcome to this video about [topic].
    visual:
      show_logo: true
      animation: "fade-in"

  - id: main_content
    type: content
    duration: 120
    voiceover: |
      [Main content voiceover text]
    visual:
      background: "gradient"
      elements:
        - type: text_reveal
          text: "Key Point"

  - id: closing
    type: outro
    duration: 10
    voiceover: |
      Thank you for watching.
    visual:
      show_logo: true
      call_to_action: "Subscribe for more"
"""

        elif doc_type == "slide":
            slug = _slugify(title) if title else "new_slides"
            result["suggested_path"] = f"content/{language}/slides/{slug}.yaml"
            result["content"] = f"""# Presentation: {title or "New Presentation"}
title: "{title or "New Presentation"}"
description: "[Presentation description]"
author: "[Author name]"

slides:
  - type: title
    title: "{title or "New Presentation"}"
    subtitle: "[Subtitle]"

  - type: content
    title: "Overview"
    bullets:
      - "First key point"
      - "Second key point"
      - "Third key point"

  - type: section
    title: "Section 1"

  - type: content
    title: "Details"
    bullets:
      - "Detail 1"
      - "Detail 2"

  - type: closing
    title: "Thank You"
    contact: "[Contact info]"
"""

        elif doc_type == "diagram":
            slug = _slugify(title) if title else "new_diagram"
            result["suggested_path"] = f"content/{language}/diagrams/{slug}.yaml"
            result["content"] = f"""# Diagram: {title or "New Diagram"}
title: "{title or "New Diagram"}"
type: "flowchart"  # flowchart, architecture, timeline, comparison

nodes:
  - id: start
    label: "Start"
    type: "start"

  - id: process1
    label: "Process 1"
    type: "process"

  - id: decision
    label: "Decision?"
    type: "decision"

  - id: end
    label: "End"
    type: "end"

edges:
  - from: start
    to: process1

  - from: process1
    to: decision

  - from: decision
    to: end
    label: "Yes"
"""

        elif doc_type == "data":
            slug = _slugify(title) if title else "new_data"
            result["suggested_path"] = f"content/{language}/data/{slug}.yaml"
            result["content"] = f"""# Data: {title or "New Data"}
title: "{title or "New Data"}"
description: "[Data description]"

sheets:
  - name: "Sheet 1"
    columns:
      - name: "Column A"
        type: "string"
      - name: "Column B"
        type: "number"
      - name: "Column C"
        type: "string"
    rows:
      - ["Value 1", 100, "Description 1"]
      - ["Value 2", 200, "Description 2"]
      - ["Value 3", 300, "Description 3"]
"""

        else:
            return json.dumps(
                {
                    "error": f"Unknown doc_type: {doc_type}. "
                    "Use: chapter, translation, script, slide, diagram, data"
                },
                indent=2,
            )

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def move_document(
        source_path: str,
        dest_path: str,
        update_references: bool = True,
    ) -> str:
        """
        Move/rename a document and optionally update references.

        Args:
            source_path: Current path to document
            dest_path: New path for document
            update_references: Whether to update references in other documents (default: True)

        Returns:
            Move status and any reference updates made.
        """
        try:
            source_validated = server_instance._validate_path(source_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not source_validated.exists():
            return json.dumps({"error": f"Source document not found: {source_path}"}, indent=2)

        project = server_instance.project

        # Build destination path
        if dest_path.startswith("/"):
            dest_full = Path(dest_path)
        else:
            dest_full = project.root / dest_path

        # Validate destination
        try:
            dest_resolved = dest_full.resolve()
            if not str(dest_resolved).startswith(str(project.root.resolve())):
                return json.dumps({"error": "Destination must be within project root"}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Invalid destination: {e}"}, indent=2)

        if dest_full.exists():
            return json.dumps({"error": f"Destination already exists: {dest_path}"}, indent=2)

        # Create destination directory if needed
        dest_full.parent.mkdir(parents=True, exist_ok=True)

        # Move the file
        shutil.move(str(source_validated), str(dest_full))

        references_updated = []

        # Update references in other documents
        if update_references:
            try:
                from ...cms.document import Document

                # Get relative paths for matching
                old_rel = str(source_validated.relative_to(project.root))
                new_rel = str(dest_full.relative_to(project.root))
                old_stem = source_validated.stem
                new_stem = dest_full.stem

                # Scan all documents for references
                for lang in project.languages:
                    for chapter in project.list_chapters(lang):
                        try:
                            doc = Document.load(chapter)
                            original_content = doc.content

                            # Replace references
                            updated_content = doc.content.replace(old_rel, new_rel)
                            updated_content = updated_content.replace(old_stem, new_stem)

                            if updated_content != original_content:
                                doc.content = updated_content
                                doc.save()
                                references_updated.append(str(chapter))
                        except Exception:
                            pass
            except Exception:
                pass

        server_instance._invalidate_cache()

        return json.dumps(
            {
                "status": "moved",
                "source": str(source_validated),
                "destination": str(dest_full),
                "references_updated": references_updated,
            },
            indent=2,
        )


def _slugify(text: str) -> str:
    """Convert text to slug format."""
    import re

    if not text:
        return "untitled"
    # Lowercase and replace spaces/special chars with underscores
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug.strip("_")
