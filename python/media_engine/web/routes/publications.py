"""
Publications API routes.

Endpoints for managing composite publications (books, guides, presentations)
that combine multiple chapters into a single output.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_publications_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register publications-related API routes."""

    @router.get("/api/publications")
    async def list_publications(language: str = None):
        """List all publications, optionally filtered by language."""
        project = get_project()

        from ...cms.publication import PublicationRegistry

        registry = PublicationRegistry(project)
        publications = registry.list_publications(language)

        return {
            "publications": [
                {
                    "key": f"{pub.language}/{pub.path.stem}",
                    "title": pub.title,
                    "subtitle": pub.subtitle,
                    "language": pub.language,
                    "pub_type": pub.pub_type,
                    "status": pub.metadata.status,
                    "version": pub.metadata.version,
                    "item_count": pub.item_count,
                    "item_label": pub.item_label,
                    "chapter_count": len(pub.chapters),
                    "slide_count": len(pub.slides),
                    "data_source_count": len(pub.data_sources),
                    "output_formats": [o.format for o in pub.outputs],
                    "is_translation": pub.is_translation,
                    "source_document": pub.source_document,
                }
                for pub in publications
            ],
            "total": len(publications),
        }

    @router.get("/api/publications/{language}/{name}")
    async def get_publication(language: str, name: str):
        """Get detailed information about a publication."""
        project = get_project()

        from ...cms.publication import PublicationRegistry

        key = f"{language}/{name}"
        registry = PublicationRegistry(project)
        pub = registry.get_publication(key)

        if not pub:
            return {"error": f"Publication not found: {key}"}

        status = registry.get_status(pub)

        return {
            "key": key,
            "title": pub.title,
            "subtitle": pub.subtitle,
            "description": pub.description,
            "language": pub.language,
            "metadata": {
                "version": pub.metadata.version,
                "status": pub.metadata.status,
                "author": pub.metadata.author,
                "copyright": pub.metadata.copyright,
                "license": pub.metadata.license,
                "isbn": pub.metadata.isbn,
                "edition": pub.metadata.edition,
                "publication_date": pub.metadata.publication_date,
                "target_audience": pub.metadata.target_audience,
                "reading_time": pub.metadata.reading_time,
            },
            "chapters": [
                {
                    "path": ch.path,
                    "required": ch.required,
                    "sections": ch.sections,
                }
                for ch in pub.chapters
            ],
            "outputs": [
                {
                    "format": o.format,
                    "template": o.template,
                    "filename": o.filename,
                    "single_file": o.single_file,
                    "toc": o.toc,
                }
                for o in pub.outputs
            ],
            "is_translation": pub.is_translation,
            "source_document": pub.source_document,
            "source_hash": pub.source_hash,
            "validation": {
                "is_valid": status.is_valid,
                "issues": status.issues,
                "chapter_count": status.chapter_count,
                "missing_chapters": status.missing_chapters,
                "translation_current": status.translation_current,
                "source_changed": status.source_changed,
            },
            "assets": pub.assets,
            "related": pub.related,
        }

    @router.get("/api/publications/status")
    async def publication_status(language: str = None):
        """Get status of all publications."""
        project = get_project()

        from ...cms.publication import PublicationRegistry

        registry = PublicationRegistry(project)
        publications = registry.list_publications(language)

        statuses = []
        total_valid = 0
        total_current = 0
        total_issues = 0

        for pub in publications:
            status = registry.get_status(pub)

            if status.is_valid:
                total_valid += 1
            if status.translation_current:
                total_current += 1
            total_issues += len(status.issues)

            statuses.append({
                "key": f"{pub.language}/{pub.path.stem}",
                "title": pub.title,
                "language": pub.language,
                "pub_type": pub.pub_type,
                "status": pub.metadata.status,
                "is_valid": status.is_valid,
                "issues_count": len(status.issues),
                "item_count": pub.item_count,
                "item_label": pub.item_label,
                "chapter_count": status.chapter_count,
                "slide_count": len(pub.slides),
                "data_source_count": len(pub.data_sources),
                "missing_chapters": status.missing_chapters,
                "is_translation": pub.is_translation,
                "translation_current": status.translation_current,
                "source_changed": status.source_changed,
            })

        return {
            "publications": statuses,
            "summary": {
                "total": len(statuses),
                "valid": total_valid,
                "invalid": len(statuses) - total_valid,
                "translations_current": total_current,
                "translations_outdated": len([s for s in statuses if s["is_translation"] and not s["translation_current"]]),
                "total_issues": total_issues,
            },
        }

    @router.get("/api/publications/translations")
    async def publication_translations():
        """Get translation pairs for publications."""
        project = get_project()

        from ...cms.publication import PublicationRegistry

        registry = PublicationRegistry(project)
        pairs = registry.get_translation_pairs()

        result = []
        for source, translation in pairs:
            trans_status = registry.get_status(translation)

            result.append({
                "source": {
                    "key": f"{source.language}/{source.path.stem}",
                    "title": source.title,
                    "language": source.language,
                    "content_hash": source.content_hash,
                },
                "translation": {
                    "key": f"{translation.language}/{translation.path.stem}",
                    "title": translation.title,
                    "language": translation.language,
                    "source_hash": translation.source_hash,
                },
                "sync_status": {
                    "is_current": trans_status.translation_current,
                    "source_changed": trans_status.source_changed,
                    "needs_update": not trans_status.translation_current,
                },
            })

        return {
            "pairs": result,
            "total": len(result),
            "outdated": len([p for p in result if p["sync_status"]["needs_update"]]),
        }

    @router.get("/api/publications/{language}/{name}/validate")
    async def validate_publication(language: str, name: str):
        """Validate a publication's structure."""
        project = get_project()

        from ...cms.publication import PublicationRegistry

        key = f"{language}/{name}"
        registry = PublicationRegistry(project)
        pub = registry.get_publication(key)

        if not pub:
            return {"error": f"Publication not found: {key}"}

        issues = pub.validate(project.content_dir)
        status = registry.get_status(pub)

        # Categorize issues
        critical = [i for i in issues if "Required" in i]
        warnings = [i for i in issues if "Optional" in i or "missing" in i.lower()]
        info = [i for i in issues if i not in critical and i not in warnings]

        return {
            "key": key,
            "is_valid": status.is_valid,
            "issues": {
                "critical": critical,
                "warnings": warnings,
                "info": info,
            },
            "summary": {
                "total_issues": len(issues),
                "critical_count": len(critical),
                "warning_count": len(warnings),
                "chapters_found": status.chapter_count - status.missing_chapters,
                "chapters_missing": status.missing_chapters,
                "translation_status": "current" if status.translation_current else "outdated" if status.source_changed else "n/a",
            },
        }
