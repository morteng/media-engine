"""
Document routes: chapters, viewing, saving, listing.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_document_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register document-related routes."""
    import markdown
    from fastapi import HTTPException

    from ...cms.document import Document

    @router.get("/api/chapters/{language}")
    async def get_chapters(language: str):
        """Get chapters for a language."""
        project = get_project()

        if language not in project.languages:
            raise HTTPException(404, f"Language '{language}' not found")

        chapters = project.list_chapters(language)
        return [
            {
                "path": str(c),
                "filename": c.name,
                "title": Document.load(c).title,
                "metadata": Document.load(c).metadata,
            }
            for c in chapters
        ]

    @router.get("/api/document")
    async def get_document(path: str):
        """Get a document's content and metadata."""
        doc_path = Path(path)
        if not doc_path.exists():
            raise HTTPException(404, f"Document not found: {path}")

        doc = Document.load(doc_path)

        md = markdown.Markdown(
            extensions=[
                "tables",
                "fenced_code",
                "toc",
                "meta",
                "codehilite",
            ]
        )
        html_content = md.convert(doc.content)

        return {
            "path": str(doc_path),
            "title": doc.title,
            "content": doc.content,
            "html": html_content,
            "metadata": doc.metadata,
        }

    @router.get("/api/documents/{language}")
    async def list_documents(language: str):
        """List all documents for a language with metadata."""
        project = get_project()

        if language not in project.languages:
            raise HTTPException(404, f"Language '{language}' not found")

        # Build publication membership map
        from ...cms.publication import PublicationRegistry

        publication_map = {}  # chapter_path -> publication_info
        publications = []

        try:
            registry = PublicationRegistry(project)
            for pub in registry.list_publications(language):
                pub_info = {
                    "key": f"{pub.language}/{pub.path.stem}",
                    "title": pub.title,
                    "pub_type": pub.pub_type,
                    "item_count": pub.item_count,
                    "item_label": pub.item_label,
                }
                publications.append(pub_info)

                # Map chapters to their publication
                for ch in pub.chapters:
                    chapter_path = project.content_dir / language / ch.path
                    publication_map[str(chapter_path)] = pub_info
        except Exception:
            pass  # Publication registry may not be available

        documents = []

        # Chapters
        for chapter in project.list_chapters(language):
            doc = Document.load(chapter)
            chapter_path = str(chapter)
            pub_info = publication_map.get(chapter_path)

            documents.append(
                {
                    "path": chapter_path,
                    "filename": chapter.name,
                    "title": doc.title,
                    "type": "chapter",
                    "metadata": doc.metadata,
                    "publication": pub_info,  # None if orphan chapter
                }
            )

        # Scripts
        for script in project.list_scripts(language):
            documents.append(
                {
                    "path": str(script),
                    "filename": script.name,
                    "title": script.stem.replace("_", " ").title(),
                    "type": "script",
                    "metadata": {},
                }
            )

        # Diagrams
        diagrams_dir = project.content_dir / language / "diagrams"
        if diagrams_dir.exists():
            for diagram in diagrams_dir.glob("*.yaml"):
                documents.append(
                    {
                        "path": str(diagram),
                        "filename": diagram.name,
                        "title": diagram.stem.replace("_", " ").title(),
                        "type": "diagram",
                        "metadata": {},
                    }
                )

        # Slides
        slides_dir = project.content_dir / language / "slides"
        if slides_dir.exists():
            for slide in slides_dir.glob("*.yaml"):
                documents.append(
                    {
                        "path": str(slide),
                        "filename": slide.name,
                        "title": slide.stem.replace("_", " ").title(),
                        "type": "slides",
                        "metadata": {},
                    }
                )

        # Data
        data_dir = project.content_dir / language / "data"
        if data_dir.exists():
            for data_file in data_dir.glob("*.yaml"):
                documents.append(
                    {
                        "path": str(data_file),
                        "filename": data_file.name,
                        "title": data_file.stem.replace("_", " ").title(),
                        "type": "data",
                        "metadata": {},
                    }
                )

        # Demos
        demos_dir = project.content_dir / language / "demos"
        if demos_dir.exists():
            for demo in demos_dir.glob("*.yaml"):
                documents.append(
                    {
                        "path": str(demo),
                        "filename": demo.name,
                        "title": demo.stem.replace("_", " ").title(),
                        "type": "demo",
                        "metadata": {},
                    }
                )

        # Deliverables
        deliverable_categories = [
            ("investor", "Investor"),
            ("pilot", "Pilot"),
            ("legal", "Legal"),
            ("press", "Press"),
            ("sales", "Sales"),
            ("playbooks", "Playbooks"),
        ]
        for folder, category in deliverable_categories:
            folder_dir = project.content_dir / language / folder
            if folder_dir.exists():
                for md_file in folder_dir.glob("*.md"):
                    doc = Document.load(md_file)
                    documents.append(
                        {
                            "path": str(md_file),
                            "filename": md_file.name,
                            "title": doc.title or md_file.stem.replace("_", " ").title(),
                            "type": "deliverable",
                            "category": category,
                            "metadata": doc.metadata,
                        }
                    )

        return {
            "language": language,
            "documents": documents,
            "publications": publications,
        }

    @router.post("/api/document")
    async def save_document(path: str, content: str, metadata: dict = None):
        """Save a document (for collaborative editing)."""
        doc_path = Path(path)
        if not doc_path.exists():
            raise HTTPException(404, f"Document not found: {path}")

        doc = Document.load(doc_path)
        doc.content = content
        if metadata:
            doc.metadata.update(metadata)
        doc.save()

        await manager.broadcast(
            {
                "type": "document_saved",
                "path": path,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {"status": "saved", "path": path}

    @router.get("/api/file")
    async def get_file(path: str):
        """Get raw file content (for YAML files etc)."""
        import yaml

        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(404, f"File not found: {path}")

        content = file_path.read_text()

        parsed = None
        if file_path.suffix in (".yaml", ".yml"):
            try:
                parsed = yaml.safe_load(content)
            except Exception:
                pass

        result = {
            "path": str(file_path),
            "filename": file_path.name,
            "content": content,
            "parsed": parsed,
            "type": file_path.suffix.lstrip("."),
        }

        # Check for video assets if this is a script file
        if "scripts" in file_path.parts and file_path.suffix in (".yaml", ".yml"):
            project = get_project()
            script_name = file_path.stem

            # Determine language from path
            lang = None
            for part in file_path.parts:
                if part in project.languages:
                    lang = part
                    break

            if lang:
                video_dir = project.output_dir / lang / "videos"
                video_path = video_dir / f"{script_name}.mp4"
                props_path = video_dir / f"{script_name}.props.json"
                audio_path = video_dir / f"{script_name}.mp3"
                captions_path = video_dir / f"{script_name}.vtt"

                video_info = {
                    "hasVideo": video_path.exists(),
                    "hasAudio": audio_path.exists(),
                    "hasCaptions": captions_path.exists(),
                    "hasProps": props_path.exists(),
                }

                if video_path.exists():
                    rel_video = video_path.relative_to(project.output_dir)
                    video_info["videoUrl"] = f"/media/{rel_video}"

                if audio_path.exists():
                    rel_audio = audio_path.relative_to(project.output_dir)
                    video_info["audioUrl"] = f"/media/{rel_audio}"

                if captions_path.exists():
                    rel_captions = captions_path.relative_to(project.output_dir)
                    video_info["captionsUrl"] = f"/media/{rel_captions}"

                if props_path.exists():
                    try:
                        props = json.loads(props_path.read_text())
                        video_info["duration"] = props.get("duration", 0)
                        video_info["fps"] = props.get("fps", 30)
                        # Include scene timing data for sync
                        video_info["sceneTiming"] = [
                            {
                                "id": s.get("id"),
                                "startTime": s.get("startFrame", 0) / props.get("fps", 30),
                                "endTime": s.get("endFrame", 0) / props.get("fps", 30),
                            }
                            for s in props.get("scenes", [])
                        ]
                    except Exception:
                        pass

                result["video"] = video_info

        return result
