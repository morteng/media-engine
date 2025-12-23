"""Translation management tools with automatic hash-based change detection."""

import json


def register_translation_tools(mcp, server_instance):
    """Register translation-related MCP tools."""

    @mcp.tool()
    async def translation_status(language: str = None) -> str:
        """
        Get translation sync status with automatic change detection.

        Uses content hash comparison - any source change is automatically detected.

        Args:
            language: Filter to specific target language (optional)

        Returns list of all translations with sync status and content hashes.
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
                        "is_outdated": s.is_outdated,
                        "status": s.status_label,
                        "source_content_hash": s.source_content_hash,
                        "translated_from_hash": s.translated_from_hash,
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

        Automatically detects when source content has changed via hash comparison.
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
                        "translation_title": s.translation_title,
                        "source": str(s.source_path),
                        "source_title": s.source_title,
                        "source_hash": s.source_content_hash,
                        "translated_from_hash": s.translated_from_hash,
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
        Mark a translation as synced with current source content.

        Updates the source_content_hash to match the current source,
        marking the translation as up-to-date.

        Args:
            translation_path: Path to translation document

        Returns:
            Sync result with old/new content hashes
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

        result = tracker.mark_synced(trans_doc)

        server_instance._invalidate_cache()
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def sync_all_translations(language: str = None, dry_run: bool = False) -> str:
        """
        Sync all current translations to record their content hashes.

        Use after updating translations to mark them as synced with source.
        Only syncs translations that are currently marked as 'current'.

        Args:
            language: Filter to specific target language (optional)
            dry_run: If True, show what would be synced without making changes

        Returns:
            Summary of synced translations
        """
        from ...cms.document import Document
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        statuses = tracker.get_all_statuses()

        if language:
            statuses = [s for s in statuses if s.target_language == language]

        # Only sync current translations (not outdated)
        to_sync = [s for s in statuses if not s.is_outdated]

        if dry_run:
            return json.dumps(
                {
                    "dry_run": True,
                    "would_sync": len(to_sync),
                    "translations": [
                        {"path": str(s.translation_path), "title": s.translation_title}
                        for s in to_sync
                    ],
                },
                indent=2,
            )

        synced = []
        errors = []

        for status in to_sync:
            try:
                trans_doc = Document.load(status.translation_path)
                result = tracker.mark_synced(trans_doc)
                if "error" in result:
                    errors.append({"path": str(status.translation_path), "error": result["error"]})
                else:
                    synced.append(result)
            except Exception as e:
                errors.append({"path": str(status.translation_path), "error": str(e)})

        server_instance._invalidate_cache()
        return json.dumps(
            {
                "synced_count": len(synced),
                "error_count": len(errors),
                "synced": synced,
                "errors": errors if errors else None,
            },
            indent=2,
        )
