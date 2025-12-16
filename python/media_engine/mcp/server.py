"""
Media Engine MCP Server - Production-Ready Implementation

A comprehensive Model Context Protocol server that exposes all media-engine
functionality to AI agents in a secure, efficient manner.

Features:
- 20+ tools covering all media-engine operations
- Resources for project context and configuration
- Prompts for common workflows
- Security: path validation, input sanitization
- Caching for efficiency
- Full async support

Compatible with Claude Code, Claude Desktop, Cursor, VS Code, and any MCP client.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# MCP SDK import - graceful fallback
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        GetPromptResult,
        Prompt,
        PromptMessage,
        Resource,
        TextContent,
        Tool,
    )

    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    Server = object


class MediaEngineMCPServer:
    """
    Production-ready MCP Server for Media Engine.

    Provides comprehensive tooling for AI agents to interact with
    media-engine projects securely and efficiently.
    """

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize MCP server.

        Args:
            project_path: Path to project root. If None, searches from cwd.
        """
        self.project_path = Path(project_path).resolve() if project_path else None
        self._project = None
        self._cache = {}
        self._cache_ttl = 30  # seconds

        if HAS_MCP:
            self.server = Server("media-engine")
            self._register_all()
        else:
            self.server = None

    # === Project Access with Caching ===

    @property
    def project(self):
        """Lazy-load project with caching."""
        cache_key = "project"
        now = datetime.now().timestamp()

        if cache_key in self._cache:
            cached, ts = self._cache[cache_key]
            if now - ts < self._cache_ttl:
                return cached

        from ..core.project import Project, find_project

        if self.project_path:
            self._project = Project.load(self.project_path)
        else:
            self._project = find_project()

        if self._project:
            self._cache[cache_key] = (self._project, now)
        return self._project

    def _invalidate_cache(self):
        """Clear all cached data."""
        self._cache.clear()

    def _validate_path(self, path: str) -> Path:
        """
        Validate and sanitize a file path for security.

        Prevents path traversal attacks and ensures paths are within project.
        """
        if not self.project:
            raise ValueError("No project loaded")

        # Resolve and check if within project
        try:
            resolved = Path(path).resolve()
            project_root = self.project.root.resolve()

            # Allow paths within project root
            if project_root in resolved.parents or resolved == project_root:
                return resolved

            # Also allow content_dir, assets_dir, output_dir
            for allowed in [
                self.project.content_dir,
                self.project.assets_dir,
                self.project.output_dir,
                self.project.publish_dir,
            ]:
                allowed_resolved = allowed.resolve()
                if allowed_resolved in resolved.parents or resolved == allowed_resolved:
                    return resolved

            raise ValueError(f"Path outside project: {path}")
        except Exception as e:
            raise ValueError(f"Invalid path: {path} - {e}")

    # === Registration ===

    def _register_all(self):
        """Register all tools, resources, and prompts."""
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _register_tools(self):
        """Register all MCP tools."""
        if not HAS_MCP:
            return

        # === Project Tools ===

        @self.server.tool()
        async def project_status() -> str:
            """
            Get comprehensive project status.

            Returns project configuration, content counts per language,
            cache statistics, and overall health.
            """
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            status = self.project.get_status()
            status["health"] = self._get_health_summary()
            return json.dumps(status, indent=2)

        @self.server.tool()
        async def project_config() -> str:
            """
            Get project configuration details.

            Returns all settings from project.yaml including paths,
            localization, voiceover, and video settings.
            """
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            return json.dumps(
                {
                    "name": self.project.config.name,
                    "description": self.project.config.description,
                    "languages": {
                        code: {"name": lang.name, "locale": lang.locale, "voice_id": lang.voice_id}
                        for code, lang in self.project.languages.items()
                    },
                    "source_language": self.project.source_language,
                    "paths": {
                        "root": str(self.project.root),
                        "content": str(self.project.content_dir),
                        "assets": str(self.project.assets_dir),
                        "output": str(self.project.output_dir),
                        "publish": str(self.project.publish_dir),
                        "cache": str(self.project.cache_dir),
                    },
                    "voiceover": {
                        "provider": self.project.config.voiceover.provider,
                        "model": getattr(self.project.config.voiceover, "model", None),
                    },
                    "video": {
                        "width": self.project.config.video.width,
                        "height": self.project.config.video.height,
                        "fps": self.project.config.video.fps,
                    },
                },
                indent=2,
            )

        @self.server.tool()
        async def refresh_project() -> str:
            """
            Refresh project data by clearing caches.

            Use this after making changes to project files to ensure
            subsequent queries return fresh data.
            """
            self._invalidate_cache()
            return json.dumps(
                {
                    "status": "cache_cleared",
                    "message": "Project data will be refreshed on next query",
                }
            )

        # === Content Tools ===

        @self.server.tool()
        async def list_chapters(language: str = None) -> str:
            """
            List all chapters for a language.

            Args:
                language: Language code (default: source language)

            Returns list of chapters with titles and metadata.
            """
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            from ..cms.document import Document

            lang = language or self.project.source_language

            if lang not in self.project.languages:
                return json.dumps({"error": f"Language '{lang}' not configured"}, indent=2)

            chapters = self.project.list_chapters(lang)
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

        @self.server.tool()
        async def read_document(path: str) -> str:
            """
            Read a document's content and metadata.

            Args:
                path: Path to document file

            Returns document title, content, and all frontmatter metadata.
            """
            from ..cms.document import Document

            try:
                validated_path = self._validate_path(path)
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

        @self.server.tool()
        async def update_document_metadata(path: str, updates: str) -> str:
            """
            Update a document's frontmatter metadata.

            Args:
                path: Path to document file
                updates: JSON string of metadata updates

            Example: update_document_metadata("doc.md", '{"status": "reviewed"}')
            """
            from ..cms.document import Document

            try:
                validated_path = self._validate_path(path)
                updates_dict = json.loads(updates)
            except (ValueError, json.JSONDecodeError) as e:
                return json.dumps({"error": str(e)}, indent=2)

            if not validated_path.exists():
                return json.dumps({"error": f"Document not found: {path}"}, indent=2)

            doc = Document.load(validated_path)
            doc.metadata.update(updates_dict)
            doc.save()

            self._invalidate_cache()
            return json.dumps(
                {
                    "status": "updated",
                    "path": str(validated_path),
                    "updated_fields": list(updates_dict.keys()),
                },
                indent=2,
            )

        @self.server.tool()
        async def increment_document_version(path: str, bump: str = "patch") -> str:
            """
            Increment a document's version number.

            Args:
                path: Path to document file
                bump: Version bump type - "major", "minor", or "patch"
            """
            from ..cms.document import Document

            try:
                validated_path = self._validate_path(path)
            except ValueError as e:
                return json.dumps({"error": str(e)}, indent=2)

            if bump not in ("major", "minor", "patch"):
                return json.dumps({"error": "bump must be 'major', 'minor', or 'patch'"}, indent=2)

            doc = Document.load(validated_path)
            old_version = doc.metadata.get("version", "0.0.0")
            doc.increment_version(bump)
            doc.save()

            self._invalidate_cache()
            return json.dumps(
                {
                    "status": "version_incremented",
                    "path": str(validated_path),
                    "old_version": old_version,
                    "new_version": doc.metadata.get("version"),
                },
                indent=2,
            )

        # === Translation Tools ===

        @self.server.tool()
        async def translation_status(language: str = None) -> str:
            """
            Get translation sync status.

            Args:
                language: Filter to specific target language (optional)

            Returns list of all translations with sync status.
            """
            from ..cms.translation import TranslationTracker

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            tracker = TranslationTracker(self.project)
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

        @self.server.tool()
        async def outdated_translations() -> str:
            """
            Get list of translations that need updating.

            Returns only translations where the source has been modified
            since the translation was made.
            """
            from ..cms.translation import TranslationTracker

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            tracker = TranslationTracker(self.project)
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
                            "versions_behind": self._version_diff(
                                s.translated_version, s.source_version
                            ),
                        }
                        for s in outdated
                    ],
                },
                indent=2,
            )

        @self.server.tool()
        async def missing_translations(language: str) -> str:
            """
            Get source documents missing translations in a language.

            Args:
                language: Target language code
            """
            from ..cms.translation import TranslationTracker

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            if language not in self.project.languages:
                return json.dumps({"error": f"Language '{language}' not configured"}, indent=2)

            tracker = TranslationTracker(self.project)
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

        @self.server.tool()
        async def mark_translation_synced(translation_path: str) -> str:
            """
            Mark a translation as synced with current source version.

            Updates the translation's source_version to match the
            current source document version.

            Args:
                translation_path: Path to translation document
            """
            from ..cms.document import Document
            from ..cms.translation import TranslationTracker

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            try:
                validated_path = self._validate_path(translation_path)
            except ValueError as e:
                return json.dumps({"error": str(e)}, indent=2)

            tracker = TranslationTracker(self.project)
            trans_doc = Document.load(validated_path)

            old_version = trans_doc.metadata.get("source_version", "")
            tracker.mark_synced(trans_doc)

            self._invalidate_cache()
            return json.dumps(
                {
                    "status": "synced",
                    "translation": str(validated_path),
                    "old_source_version": old_version,
                    "new_source_version": trans_doc.metadata.get("source_version"),
                },
                indent=2,
            )

        # === Quality & Validation Tools ===

        @self.server.tool()
        async def quality_check() -> str:
            """
            Run quality checks on the project.

            Checks for placeholders, encoding issues, stale content,
            terminology consistency, and more.
            """
            from ..quality import run_quality_checks

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            report = run_quality_checks(self.project, console_output=False)

            return json.dumps(
                {
                    "summary": {
                        "total": report.total_count,
                        "errors": report.error_count,
                        "warnings": report.warning_count,
                        "info": report.info_count,
                        "passed": report.error_count == 0,
                    },
                    "issues": [
                        {
                            "severity": i.severity,
                            "category": i.category,
                            "message": i.message,
                            "file": str(i.file_path) if i.file_path else None,
                            "line": i.line,
                        }
                        for i in report.issues
                    ],
                },
                indent=2,
            )

        @self.server.tool()
        async def validate_project() -> str:
            """
            Validate project against schema.

            Checks frontmatter fields, references, and structure
            against schema.yaml rules.
            """
            from ..validation import validate_project as do_validate

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            schema_path = self.project.root / "schema.yaml"
            report = do_validate(
                self.project,
                schema_path if schema_path.exists() else None,
                console_output=False,
            )

            return json.dumps(
                {
                    "valid": report.error_count == 0,
                    "schema_used": str(schema_path) if schema_path.exists() else None,
                    "summary": {
                        "total": report.total_count,
                        "errors": report.error_count,
                        "warnings": report.warning_count,
                    },
                    "issues": [
                        {
                            "severity": i.severity,
                            "message": i.message,
                            "file": str(i.file_path) if i.file_path else None,
                        }
                        for i in report.issues
                    ],
                },
                indent=2,
            )

        # === Search Tools ===

        @self.server.tool()
        async def search_content(query: str, language: str = None, limit: int = 10) -> str:
            """
            Search project content with full-text search.

            Args:
                query: Search query (supports multiple words)
                language: Filter to specific language (optional)
                limit: Maximum results to return (default: 10)
            """
            from ..search import build_search_index

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            # Use cached index if available
            cache_key = f"search_index_{language or 'all'}"
            now = datetime.now().timestamp()

            if cache_key in self._cache:
                index, ts = self._cache[cache_key]
                if now - ts < 60:  # 1 minute cache for search index
                    pass
                else:
                    index = build_search_index(self.project, console_output=False)
                    self._cache[cache_key] = (index, now)
            else:
                index = build_search_index(self.project, console_output=False)
                self._cache[cache_key] = (index, now)

            results = index.search(query, limit=limit)

            if language:
                results = [r for r in results if r.entry.language == language]

            return json.dumps(
                {
                    "query": query,
                    "count": len(results),
                    "results": [
                        {
                            "title": r.entry.title,
                            "path": str(r.entry.path),
                            "language": r.entry.language,
                            "score": round(r.score, 3),
                            "snippet": r.snippet[:200] + "..."
                            if len(r.snippet) > 200
                            else r.snippet,
                        }
                        for r in results[:limit]
                    ],
                },
                indent=2,
            )

        # === Build Tools ===

        @self.server.tool()
        async def build_html(
            language: str = None, chapter: str = None, output_dir: str = None
        ) -> str:
            """
            Build HTML output from markdown chapters.

            Args:
                language: Language to build (default: source language)
                chapter: Specific chapter filename (optional, builds all if omitted)
                output_dir: Output directory (optional, uses default)
            """
            from ..builders.html import HTMLBuilder, HTMLConfig
            from ..cms.document import Document

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            lang = language or self.project.source_language
            builder = HTMLBuilder(theme=self.project.theme)

            if chapter:
                chapters = [self.project.get_chapters_dir(lang) / chapter]
            else:
                chapters = self.project.list_chapters(lang)

            if not chapters:
                return json.dumps({"error": f"No chapters found for '{lang}'"}, indent=2)

            output_path = Path(output_dir) if output_dir else self.project.output_dir / lang
            output_path.mkdir(parents=True, exist_ok=True)

            built = []
            for chapter_path in chapters:
                if not chapter_path.exists():
                    continue

                doc = Document.load(chapter_path)
                config = HTMLConfig(include_toc=True, lang=lang)
                html = builder.build(doc.content, doc.title, config)

                out_file = output_path / chapter_path.with_suffix(".html").name
                builder.save(html, out_file)
                built.append(str(out_file))

            self._invalidate_cache()
            return json.dumps(
                {
                    "status": "built",
                    "language": lang,
                    "files_built": len(built),
                    "output_files": built,
                },
                indent=2,
            )

        @self.server.tool()
        async def build_pptx(slides_path: str, output_path: str = None) -> str:
            """
            Build PowerPoint presentation from YAML definition.

            Args:
                slides_path: Path to slides YAML file
                output_path: Output path (optional)
            """
            try:
                from ..builders.pptx import PPTXBuilder
            except ImportError:
                return json.dumps({"error": "python-pptx not installed"}, indent=2)

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            try:
                validated_path = self._validate_path(slides_path)
            except ValueError as e:
                return json.dumps({"error": str(e)}, indent=2)

            if not validated_path.exists():
                return json.dumps({"error": f"Slides file not found: {slides_path}"}, indent=2)

            builder = PPTXBuilder(theme=self.project.theme)
            builder.build_from_yaml(validated_path)

            if output_path:
                out = Path(output_path)
            else:
                out = self.project.output_dir / validated_path.with_suffix(".pptx").name

            out.parent.mkdir(parents=True, exist_ok=True)
            saved = builder.save(out)

            return json.dumps(
                {
                    "status": "built",
                    "input": str(validated_path),
                    "output": str(saved),
                    "size_bytes": saved.stat().st_size,
                },
                indent=2,
            )

        @self.server.tool()
        async def build_xlsx(data_path: str, output_path: str = None) -> str:
            """
            Build Excel spreadsheet from YAML definition.

            Args:
                data_path: Path to data YAML file
                output_path: Output path (optional)
            """
            try:
                from ..builders.xlsx import XLSXBuilder
            except ImportError:
                return json.dumps({"error": "openpyxl not installed"}, indent=2)

            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            try:
                validated_path = self._validate_path(data_path)
            except ValueError as e:
                return json.dumps({"error": str(e)}, indent=2)

            if not validated_path.exists():
                return json.dumps({"error": f"Data file not found: {data_path}"}, indent=2)

            builder = XLSXBuilder(theme=self.project.theme)
            builder.build_from_yaml(validated_path)

            if output_path:
                out = Path(output_path)
            else:
                out = self.project.output_dir / validated_path.with_suffix(".xlsx").name

            out.parent.mkdir(parents=True, exist_ok=True)
            saved = builder.save(out)

            return json.dumps(
                {
                    "status": "built",
                    "input": str(validated_path),
                    "output": str(saved),
                    "size_bytes": saved.stat().st_size,
                },
                indent=2,
            )

        # === Cache Tools ===

        @self.server.tool()
        async def cache_status() -> str:
            """Get cache statistics and status."""
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            manifest = self.project._cache_manifest
            return json.dumps(
                {
                    "cache_dir": str(self.project.cache_dir),
                    "voiceover_cached": len(manifest.get("voiceover", {})),
                    "builds_tracked": len(manifest.get("builds", {})),
                    "content_hashes": len(manifest.get("content_hashes", {})),
                },
                indent=2,
            )

        @self.server.tool()
        async def clear_cache(cache_type: str = "all") -> str:
            """
            Clear cached data.

            Args:
                cache_type: Type to clear - "all", "voiceover", or "builds"
            """
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            if cache_type not in ("all", "voiceover", "builds"):
                return json.dumps(
                    {"error": "cache_type must be 'all', 'voiceover', or 'builds'"}, indent=2
                )

            count = self.project.clear_cache(cache_type)
            self._invalidate_cache()

            return json.dumps(
                {
                    "status": "cleared",
                    "type": cache_type,
                    "items_cleared": count,
                },
                indent=2,
            )

        # === Audit Tools ===

        @self.server.tool()
        async def log_action(action: str, details: str = None, user: str = None) -> str:
            """
            Log an action to the audit trail.

            Args:
                action: Action description (e.g., "document_updated")
                details: Additional details (optional)
                user: User identifier (optional)
            """
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            from ..audit import log_action as do_log

            do_log(self.project, action, details, user)

            return json.dumps(
                {
                    "status": "logged",
                    "action": action,
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )

        @self.server.tool()
        async def get_audit_log(limit: int = 50) -> str:
            """
            Get recent audit log entries.

            Args:
                limit: Maximum entries to return (default: 50)
            """
            if not self.project:
                return json.dumps({"error": "No project found"}, indent=2)

            from ..audit import get_recent_entries

            entries = get_recent_entries(self.project, limit)

            return json.dumps(
                {
                    "count": len(entries),
                    "entries": entries,
                },
                indent=2,
            )

    def _register_resources(self):
        """Register MCP resources for context."""
        if not HAS_MCP:
            return

        @self.server.resource("project://overview")
        async def project_overview() -> str:
            """Project overview and health status."""
            if not self.project:
                return "No project loaded"

            status = self.project.get_status()
            health = self._get_health_summary()

            return f"""# {self.project.config.name}

{self.project.config.description}

## Languages
- Source: {self.project.source_language}
- Configured: {", ".join(self.project.languages.keys())}

## Content
{json.dumps(status["content"], indent=2)}

## Health
- Translation sync: {health["translation_status"]}
- Quality: {health["quality_status"]}
"""

        @self.server.resource("project://languages")
        async def project_languages() -> str:
            """Configured languages and their settings."""
            if not self.project:
                return "No project loaded"

            return json.dumps(
                {
                    code: {"name": lang.name, "locale": lang.locale}
                    for code, lang in self.project.languages.items()
                },
                indent=2,
            )

    def _register_prompts(self):
        """Register prompts for common workflows."""
        if not HAS_MCP:
            return

        @self.server.prompt()
        async def review_translation(language: str) -> GetPromptResult:
            """Prompt for reviewing translations in a language."""
            return GetPromptResult(
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Review all translations for language '{language}':

1. First, get the translation status for {language}
2. For any outdated translations, read both source and translation
3. Summarize what changes are needed
4. Suggest whether minor updates or full re-translation is needed

Use the translation_status and read_document tools.""",
                        ),
                    )
                ]
            )

        @self.server.prompt()
        async def quality_review() -> GetPromptResult:
            """Prompt for comprehensive quality review."""
            return GetPromptResult(
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text="""Perform a comprehensive quality review:

1. Run quality_check to find all issues
2. Run validate_project to check schema compliance
3. Check translation_status for sync issues
4. Summarize findings by severity
5. Recommend priority fixes

Start with quality_check.""",
                        ),
                    )
                ]
            )

    # === Helper Methods ===

    def _get_health_summary(self) -> dict:
        """Get project health summary."""
        if not self.project:
            return {}

        # Check translations
        try:
            from ..cms.translation import TranslationTracker

            tracker = TranslationTracker(self.project)
            outdated = tracker.get_outdated_translations()
            trans_status = "all_synced" if not outdated else f"{len(outdated)}_outdated"
        except Exception:
            trans_status = "unknown"

        # Check quality
        try:
            from ..quality import run_quality_checks

            report = run_quality_checks(self.project, console_output=False)
            if report.error_count > 0:
                quality_status = f"{report.error_count}_errors"
            elif report.warning_count > 0:
                quality_status = f"{report.warning_count}_warnings"
            else:
                quality_status = "passed"
        except Exception:
            quality_status = "unknown"

        return {
            "translation_status": trans_status,
            "quality_status": quality_status,
        }

    def _version_diff(self, old: str, new: str) -> str:
        """Calculate version difference description."""
        try:
            old_parts = [int(x) for x in old.split(".")]
            new_parts = [int(x) for x in new.split(".")]

            # Pad to same length
            while len(old_parts) < 3:
                old_parts.append(0)
            while len(new_parts) < 3:
                new_parts.append(0)

            if new_parts[0] > old_parts[0]:
                return f"{new_parts[0] - old_parts[0]} major"
            elif new_parts[1] > old_parts[1]:
                return f"{new_parts[1] - old_parts[1]} minor"
            elif new_parts[2] > old_parts[2]:
                return f"{new_parts[2] - old_parts[2]} patch"
            return "same"
        except Exception:
            return "unknown"

    async def run(self):
        """Run the MCP server."""
        if not HAS_MCP:
            raise RuntimeError("MCP SDK not installed. Install with: pip install media-engine[mcp]")

        async with stdio_server() as (read, write):
            await self.server.run(read, write)


def main():
    """CLI entry point for MCP server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Media Engine MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  media-engine-mcp                    # Auto-detect project
  media-engine-mcp -p /path/to/proj   # Specify project path

Claude Desktop config (~/.claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "media-engine": {
        "command": "media-engine-mcp",
        "args": ["-p", "/path/to/project"]
      }
    }
  }
""",
    )
    parser.add_argument(
        "--project",
        "-p",
        type=Path,
        help="Path to project root (auto-detects if not specified)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="media-engine-mcp 1.0.0",
    )
    args = parser.parse_args()

    server = MediaEngineMCPServer(project_path=args.project)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
