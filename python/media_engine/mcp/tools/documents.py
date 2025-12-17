"""Document management tools."""

import json


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
