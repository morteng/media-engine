"""
Translation routes: translation status and matrix.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def _get_cached_or_compute(key: str, compute_fn, max_age: float = 300):
    """Helper to get cached data or compute it, then cache the result."""
    import time

    from ..preprocessor import get_preprocessor

    preprocessor = get_preprocessor()
    if preprocessor:
        cached = preprocessor.get_cached(key, max_age_seconds=max_age)
        if cached is not None:
            return cached

    # Compute the result
    start = time.time()
    result = compute_fn()
    elapsed_ms = (time.time() - start) * 1000

    # Store in cache for next time
    if preprocessor:
        preprocessor.cache.set(key, result, computation_time_ms=elapsed_ms)

    return result


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

        def compute_translations():
            tracker = TranslationTracker(project)
            statuses = tracker.get_all_statuses()
            return {
                "total": len(statuses),
                "current": sum(1 for s in statuses if not s.is_outdated),
                "outdated": sum(1 for s in statuses if s.is_outdated),
                "translations": [s.to_dict() for s in statuses],
            }

        return _get_cached_or_compute("translations", compute_translations, max_age=300)

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
                            "translated_from_hash": status.translated_from_hash,
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
