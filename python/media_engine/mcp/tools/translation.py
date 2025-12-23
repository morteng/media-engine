"""Translation management tools with hash-based change detection."""

import json


def register_translation_tools(mcp, server_instance):
    """Register translation-related MCP tools."""

    @mcp.tool()
    async def translation_status(language: str = None) -> str:
        """
        Get translation sync status with hash-based change detection.

        Supports two tracking modes:
        - **hash**: Automatic detection via content hash (preferred)
        - **version**: Manual version comparison (fallback)

        Args:
            language: Filter to specific target language (optional)

        Returns list of all translations with sync status, tracking mode,
        and content change detection.
        """
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        statuses = tracker.get_all_statuses()

        if language:
            statuses = [s for s in statuses if s.target_language == language]

        # Calculate stats by tracking mode
        hash_tracked = sum(1 for s in statuses if s.tracking_mode == "hash")
        version_tracked = sum(1 for s in statuses if s.tracking_mode == "version")

        return json.dumps(
            {
                "total": len(statuses),
                "current": sum(1 for s in statuses if not s.is_outdated),
                "outdated": sum(1 for s in statuses if s.is_outdated),
                "tracking_stats": {
                    "hash_tracked": hash_tracked,
                    "version_tracked": version_tracked,
                    "recommendation": "Run 'mark_translation_synced' on all translations to enable hash-based tracking"
                    if version_tracked > 0
                    else "All translations using hash-based tracking",
                },
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
                        "tracking_mode": s.tracking_mode,
                        "content_changed": s.content_changed,
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

        Detects outdated translations using:
        - **Hash comparison** (automatic): Content hash differs from when translation was made
        - **Version comparison** (fallback): Source version is newer than translated version

        Returns detailed info about what changed and why translation is outdated.
        """
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        outdated = tracker.get_outdated_translations()

        return json.dumps(
            {
                "count": len(outdated),
                "summary": {
                    "content_changes": sum(1 for s in outdated if s.content_changed),
                    "version_changes": sum(1 for s in outdated if not s.content_changed),
                },
                "outdated": [
                    {
                        "translation": str(s.translation_path),
                        "translation_title": s.translation_title,
                        "source": str(s.source_path),
                        "source_title": s.source_title,
                        "source_version": s.source_version,
                        "translated_from_version": s.translated_version,
                        "tracking_mode": s.tracking_mode,
                        "content_changed": s.content_changed,
                        "reason": "content changed (detected via hash)"
                        if s.content_changed
                        else f"version bump ({s.translated_version} → {s.source_version})",
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
    async def mark_translation_synced(translation_path: str, use_hash: bool = True) -> str:
        """
        Mark a translation as synced with current source version.

        Updates both source_version AND source_content_hash for comprehensive
        change tracking. Hash-based tracking enables automatic detection of
        future source changes without requiring manual version bumps.

        Args:
            translation_path: Path to translation document
            use_hash: Enable hash-based tracking (default: True, recommended)

        Returns:
            Sync result with old/new versions and content hashes
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

        result = tracker.mark_synced(trans_doc, use_hash=use_hash)

        server_instance._invalidate_cache()
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def sync_all_translations(language: str = None, dry_run: bool = False) -> str:
        """
        Sync all translations to enable hash-based tracking.

        Iterates through all translations and updates their source_content_hash
        to enable automatic change detection. Only syncs translations that are
        currently marked as 'current' (not outdated).

        Args:
            language: Filter to specific target language (optional)
            dry_run: If True, show what would be synced without making changes

        Returns:
            Summary of synced translations with tracking mode enabled
        """
        from ...cms.document import Document
        from ...cms.translation import TranslationTracker

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        tracker = TranslationTracker(server_instance.project)
        statuses = tracker.get_all_statuses()

        if language:
            statuses = [s for s in statuses if s.target_language == language]

        # Only sync current translations (not already outdated)
        to_sync = [s for s in statuses if not s.is_outdated and s.tracking_mode == "version"]

        if dry_run:
            return json.dumps(
                {
                    "dry_run": True,
                    "would_sync": len(to_sync),
                    "translations": [
                        {
                            "path": str(s.translation_path),
                            "title": s.translation_title,
                            "current_mode": s.tracking_mode,
                            "new_mode": "hash",
                        }
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
                result = tracker.mark_synced(trans_doc, use_hash=True)
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
                "message": f"Enabled hash-based tracking for {len(synced)} translations",
            },
            indent=2,
        )
