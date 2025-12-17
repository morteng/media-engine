"""Translation management tools."""

import json


def register_translation_tools(mcp, server_instance):
    """Register translation-related MCP tools."""

    @mcp.tool()
    async def translation_status(language: str = None) -> str:
        """
        Get translation sync status.

        Args:
            language: Filter to specific target language (optional)

        Returns list of all translations with sync status.
        """
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        statuses = tracker.get_all_statuses()

        if language:
            statuses = [s for s in statuses if s.target_language == language]

        return json.dumps(
            {
                "total": len(statuses),
                "current": sum(1 for s in statuses if not s.is_outdated),
                "outdated": sum(1 for s in statuses if s.is_outdated),
                "translations": [
                    {
                        "source": str(s.source_path),
                        "translation": str(s.translation_path),
                        "source_title": s.source_title,
                        "translation_title": s.translation_title,
                        "source_language": s.source_language,
                        "target_language": s.target_language,
                        "source_version": s.source_version,
                        "translated_version": s.translated_version,
                        "is_outdated": s.is_outdated,
                        "status": s.status_label,
                    }
                    for s in statuses
                ],
            },
            indent=2,
        )

    @mcp.tool()
    async def outdated_translations() -> str:
        """
        Get list of translations that need updating.

        Returns only translations where the source has been modified
        since the translation was made.
        """
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        outdated = tracker.get_outdated_translations()

        return json.dumps(
            {
                "count": len(outdated),
                "outdated": [
                    {
                        "translation": str(s.translation_path),
                        "source": str(s.source_path),
                        "source_version": s.source_version,
                        "translated_from_version": s.translated_version,
                        "versions_behind": server_instance._version_diff(
                            s.translated_version, s.source_version
                        ),
                    }
                    for s in outdated
                ],
            },
            indent=2,
        )

    @mcp.tool()
    async def missing_translations(language: str) -> str:
        """
        Get source documents missing translations in a language.

        Args:
            language: Target language code
        """
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        if language not in server_instance.project.languages:
            return json.dumps({"error": f"Language '{language}' not configured"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        missing = tracker.get_missing_translations(language)

        return json.dumps(
            {
                "target_language": language,
                "count": len(missing),
                "missing": [
                    {
                        "source_path": str(doc.path),
                        "title": doc.title,
                        "version": doc.metadata.get("version", ""),
                    }
                    for doc in missing
                ],
            },
            indent=2,
        )

    @mcp.tool()
    async def mark_translation_synced(translation_path: str) -> str:
        """
        Mark a translation as synced with current source version.

        Updates the translation's source_version to match the
        current source document version.

        Args:
            translation_path: Path to translation document
        """
        from ...cms.document import Document
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(translation_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        trans_doc = Document.load(validated_path)

        old_version = trans_doc.metadata.get("source_version", "")
        tracker.mark_synced(trans_doc)

        server_instance._invalidate_cache()
        return json.dumps(
            {
                "status": "synced",
                "translation": str(validated_path),
                "old_source_version": old_version,
                "new_source_version": trans_doc.metadata.get("source_version"),
            },
            indent=2,
        )
