"""
Translation routes: translation status and matrix.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_translation_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register translation-related routes."""
    from ...cms.document import Document
    from ...cms.translation import TranslationTracker

    @router.get("/api/translations")
    async def get_translations():
        """Get all translation statuses."""
        project = get_project()
        tracker = TranslationTracker(project)
        statuses = tracker.get_all_statuses()

        return {
            "total": len(statuses),
            "current": sum(1 for s in statuses if not s.is_outdated),
            "outdated": sum(1 for s in statuses if s.is_outdated),
            "translations": [
                {
                    "source_path": str(s.source_path),
                    "translation_path": str(s.translation_path),
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
        }

    @router.get("/api/translations/matrix")
    async def get_translation_matrix():
        """Get translation matrix (documents x languages)."""
        project = get_project()
        tracker = TranslationTracker(project)

        source_docs = project.list_chapters(project.source_language)
        languages = list(project.languages.keys())

        matrix = []
        for source_path in source_docs:
            source_doc = Document.load(source_path)
            row = {
                "source_path": str(source_path),
                "title": source_doc.title,
                "version": source_doc.metadata.get("version", ""),
                "translations": {},
            }

            for lang in languages:
                if lang == project.source_language:
                    row["translations"][lang] = {
                        "status": "source",
                        "path": str(source_path),
                    }
                else:
                    status = None
                    for s in tracker.get_all_statuses():
                        if str(s.source_path) == str(source_path) and s.target_language == lang:
                            status = s
                            break

                    if status:
                        row["translations"][lang] = {
                            "status": "outdated" if status.is_outdated else "current",
                            "path": str(status.translation_path),
                            "translated_version": status.translated_version,
                        }
                    else:
                        row["translations"][lang] = {
                            "status": "missing",
                            "path": None,
                        }

            matrix.append(row)

        return {
            "languages": languages,
            "source_language": project.source_language,
            "documents": matrix,
        }
