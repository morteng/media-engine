"""
FastAPI Application for Media Engine Dashboard

Provides REST API and WebSocket endpoints for:
- Project status and configuration
- Translation tracking and management
- Quality checks and validation
- Real-time collaboration
- Build operations
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import webbrowser

# FastAPI imports - graceful fallback
try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None
    WebSocket = None
    WebSocketDisconnect = None

from ..core.project import Project, find_project


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.user_cursors: dict[str, dict] = {}  # user_id -> {file, line, col}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Notify others of new user
        await self.broadcast({
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        }, exclude=websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_cursors:
            del self.user_cursors[user_id]

    async def broadcast(self, message: dict, exclude: WebSocket = None):
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def update_cursor(self, user_id: str, file: str, line: int, col: int):
        self.user_cursors[user_id] = {"file": file, "line": line, "col": col}
        await self.broadcast({
            "type": "cursor_update",
            "user_id": user_id,
            "file": file,
            "line": line,
            "col": col,
        })


def create_app(project_path: Optional[Path] = None) -> "FastAPI":
    """
    Create FastAPI application for the dashboard.

    Args:
        project_path: Path to project root. If None, searches from cwd.

    Returns:
        FastAPI application instance
    """
    if not HAS_FASTAPI:
        raise RuntimeError(
            "FastAPI not installed. Install with: pip install media-engine[web]"
        )

    app = FastAPI(
        title="Media Engine Dashboard",
        description="Web interface for media-engine project management",
        version="1.0.0",
    )

    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # State
    manager = ConnectionManager()
    _project: Optional[Project] = None

    def get_project() -> Project:
        nonlocal _project
        if _project is None:
            if project_path:
                _project = Project.load(project_path)
            else:
                _project = find_project()
            if _project is None:
                raise HTTPException(404, "No project found")
        return _project

    # === Static Files ===
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # === API Routes ===

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the main dashboard page."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(generate_dashboard_html())

    @app.get("/api/project")
    async def get_project_info():
        """Get project configuration and status."""
        project = get_project()
        return {
            "name": project.config.name,
            "description": project.config.description,
            "root": str(project.root),
            "languages": {
                code: {"name": lang.name, "locale": lang.locale}
                for code, lang in project.languages.items()
            },
            "source_language": project.source_language,
            "paths": {
                "content": str(project.content_dir),
                "assets": str(project.assets_dir),
                "output": str(project.output_dir),
                "publish": str(project.publish_dir),
            },
        }

    @app.get("/api/status")
    async def get_status():
        """Get comprehensive project status."""
        project = get_project()
        return project.get_status()

    @app.get("/api/translations")
    async def get_translations():
        """Get all translation statuses."""
        from ..cms.translation import TranslationTracker
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

    @app.get("/api/translations/matrix")
    async def get_translation_matrix():
        """Get translation matrix (documents x languages)."""
        from ..cms.document import Document
        from ..cms.translation import TranslationTracker

        project = get_project()
        tracker = TranslationTracker(project)

        # Build matrix: rows are source docs, columns are languages
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
                    # Find translation
                    status = None
                    for s in tracker.get_all_statuses():
                        if (str(s.source_path) == str(source_path) and
                            s.target_language == lang):
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

    @app.get("/api/quality")
    async def get_quality():
        """Run quality checks and return report."""
        from ..quality import run_quality_checks
        project = get_project()
        report = run_quality_checks(project, console_output=False)

        return {
            "total": len(report.issues),
            "errors": report.error_count,
            "warnings": report.warning_count,
            "info": len(report.issues) - report.error_count - report.warning_count,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.type,
                    "message": i.message,
                    "file": str(i.file_path) if i.file_path else None,
                    "line": i.line,
                }
                for i in report.issues
            ],
        }

    @app.get("/api/validation")
    async def get_validation():
        """Validate project and return report."""
        from ..validation import validate_project
        project = get_project()
        schema_path = project.root / "schema.yaml"

        report = validate_project(
            project,
            schema_path if schema_path.exists() else None,
            console_output=False,
        )

        return {
            "valid": report.error_count == 0,
            "total": report.total_count,
            "errors": report.error_count,
            "warnings": report.warning_count,
            "issues": [
                {
                    "severity": i.severity,
                    "message": i.message,
                    "file": str(i.file_path) if i.file_path else None,
                }
                for i in report.issues
            ],
        }

    @app.get("/api/chapters/{language}")
    async def get_chapters(language: str):
        """Get chapters for a language."""
        from ..cms.document import Document
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

    @app.get("/api/document")
    async def get_document(path: str):
        """Get a document's content and metadata."""
        from ..cms.document import Document
        import markdown

        doc_path = Path(path)
        if not doc_path.exists():
            raise HTTPException(404, f"Document not found: {path}")

        doc = Document.load(doc_path)

        # Render markdown to HTML
        md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'toc',
            'meta',
            'codehilite',
        ])
        html_content = md.convert(doc.content)

        return {
            "path": str(doc_path),
            "title": doc.title,
            "content": doc.content,
            "html": html_content,
            "metadata": doc.metadata,
        }

    @app.get("/api/documents/{language}")
    async def list_documents(language: str):
        """List all documents for a language with metadata."""
        from ..cms.document import Document
        project = get_project()

        if language not in project.languages:
            raise HTTPException(404, f"Language '{language}' not found")

        documents = []

        # Chapters
        for chapter in project.list_chapters(language):
            doc = Document.load(chapter)
            documents.append({
                "path": str(chapter),
                "filename": chapter.name,
                "title": doc.title,
                "type": "chapter",
                "metadata": doc.metadata,
            })

        # Scripts
        for script in project.list_scripts(language):
            documents.append({
                "path": str(script),
                "filename": script.name,
                "title": script.stem.replace("_", " ").title(),
                "type": "script",
                "metadata": {},
            })

        # Diagrams
        diagrams_dir = project.content_dir / language / "diagrams"
        if diagrams_dir.exists():
            for diagram in diagrams_dir.glob("*.yaml"):
                documents.append({
                    "path": str(diagram),
                    "filename": diagram.name,
                    "title": diagram.stem.replace("_", " ").title(),
                    "type": "diagram",
                    "metadata": {},
                })

        # Slides
        slides_dir = project.content_dir / language / "slides"
        if slides_dir.exists():
            for slide in slides_dir.glob("*.yaml"):
                documents.append({
                    "path": str(slide),
                    "filename": slide.name,
                    "title": slide.stem.replace("_", " ").title(),
                    "type": "slides",
                    "metadata": {},
                })

        # Data
        data_dir = project.content_dir / language / "data"
        if data_dir.exists():
            for data_file in data_dir.glob("*.yaml"):
                documents.append({
                    "path": str(data_file),
                    "filename": data_file.name,
                    "title": data_file.stem.replace("_", " ").title(),
                    "type": "data",
                    "metadata": {},
                })

        # Demos
        demos_dir = project.content_dir / language / "demos"
        if demos_dir.exists():
            for demo in demos_dir.glob("*.yaml"):
                documents.append({
                    "path": str(demo),
                    "filename": demo.name,
                    "title": demo.stem.replace("_", " ").title(),
                    "type": "demo",
                    "metadata": {},
                })

        return {
            "language": language,
            "documents": documents,
        }

    @app.get("/api/file")
    async def get_file(path: str):
        """Get raw file content (for YAML files etc)."""
        import yaml

        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(404, f"File not found: {path}")

        content = file_path.read_text()

        # Parse YAML if applicable
        parsed = None
        if file_path.suffix in ('.yaml', '.yml'):
            try:
                parsed = yaml.safe_load(content)
            except:
                pass

        return {
            "path": str(file_path),
            "filename": file_path.name,
            "content": content,
            "parsed": parsed,
            "type": file_path.suffix.lstrip('.'),
        }

    @app.post("/api/document")
    async def save_document(path: str, content: str, metadata: dict = None):
        """Save a document (for collaborative editing)."""
        from ..cms.document import Document

        doc_path = Path(path)
        if not doc_path.exists():
            raise HTTPException(404, f"Document not found: {path}")

        doc = Document.load(doc_path)
        doc.content = content
        if metadata:
            doc.metadata.update(metadata)
        doc.save()

        # Broadcast change to collaborators
        await manager.broadcast({
            "type": "document_saved",
            "path": path,
            "timestamp": datetime.now().isoformat(),
        })

        return {"status": "saved", "path": path}

    @app.get("/api/audit-log")
    async def get_audit_log(limit: int = 100):
        """Get recent audit log entries."""
        project = get_project()
        log_path = project.root / ".media-engine" / "audit.log"

        if not log_path.exists():
            return {"entries": []}

        entries = []
        with open(log_path) as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return {"entries": entries[-limit:]}

    # === WebSocket for Real-time Collaboration ===

    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket for real-time collaboration."""
        await manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_json()

                if data.get("type") == "cursor":
                    await manager.update_cursor(
                        user_id,
                        data.get("file", ""),
                        data.get("line", 0),
                        data.get("col", 0),
                    )
                elif data.get("type") == "edit":
                    # Broadcast edit to other users
                    await manager.broadcast({
                        "type": "edit",
                        "user_id": user_id,
                        "file": data.get("file"),
                        "changes": data.get("changes"),
                        "timestamp": datetime.now().isoformat(),
                    }, exclude=websocket)

        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            await manager.broadcast({
                "type": "user_left",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            })

    return app


def generate_dashboard_html() -> str:
    """Generate embedded dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Engine Dashboard</title>
    <style>
        :root {
            --bg: #0f172a;
            --bg-card: #1e293b;
            --border: #334155;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }
        h1 { font-size: 1.5rem; font-weight: 600; }
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .status-ok { background: var(--success); color: #000; }
        .status-warn { background: var(--warning); color: #000; }
        .status-error { background: var(--error); color: #fff; }
        .grid { display: grid; gap: 1.5rem; }
        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        @media (max-width: 1024px) { .grid-3, .grid-4 { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 640px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1.5rem;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .card-title { font-size: 0.875rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
        .stat { font-size: 2.5rem; font-weight: 700; }
        .stat-label { font-size: 0.875rem; color: var(--text-muted); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
        th { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
        .matrix-cell {
            width: 2rem;
            height: 2rem;
            border-radius: 0.25rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
        }
        .cell-source { background: var(--primary); }
        .cell-current { background: var(--success); }
        .cell-outdated { background: var(--warning); }
        .cell-missing { background: var(--border); }
        .issue { padding: 0.5rem; border-radius: 0.25rem; margin-bottom: 0.5rem; font-size: 0.875rem; }
        .issue-error { background: rgba(239, 68, 68, 0.2); border-left: 3px solid var(--error); }
        .issue-warning { background: rgba(245, 158, 11, 0.2); border-left: 3px solid var(--warning); }
        .users-online { display: flex; gap: 0.5rem; }
        .user-avatar {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            background: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .loading { text-align: center; padding: 2rem; color: var(--text-muted); }
        .tabs { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        .tab {
            padding: 0.5rem 1rem;
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 0.25rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab:hover { border-color: var(--primary); color: var(--text); }
        .tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }
        /* Document browser styles */
        .doc-browser { display: grid; grid-template-columns: 300px 1fr; gap: 1.5rem; height: calc(100vh - 200px); }
        .doc-sidebar { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.5rem; overflow: hidden; display: flex; flex-direction: column; }
        .doc-sidebar-header { padding: 1rem; border-bottom: 1px solid var(--border); }
        .doc-list { flex: 1; overflow-y: auto; }
        .doc-item { padding: 0.75rem 1rem; cursor: pointer; border-bottom: 1px solid var(--border); transition: background 0.2s; }
        .doc-item:hover { background: rgba(59, 130, 246, 0.1); }
        .doc-item.active { background: rgba(59, 130, 246, 0.2); border-left: 3px solid var(--primary); }
        .doc-item-title { font-weight: 500; margin-bottom: 0.25rem; }
        .doc-item-meta { font-size: 0.75rem; color: var(--text-muted); }
        .doc-type-badge { font-size: 0.65rem; padding: 0.15rem 0.4rem; border-radius: 3px; background: var(--border); margin-left: 0.5rem; }
        .doc-preview { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.5rem; overflow: hidden; display: flex; flex-direction: column; }
        .doc-preview-header { padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .doc-preview-tabs { display: flex; gap: 0.5rem; }
        .preview-tab { padding: 0.25rem 0.75rem; background: transparent; border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-muted); cursor: pointer; font-size: 0.8rem; }
        .preview-tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }
        .doc-preview-content { flex: 1; overflow-y: auto; padding: 1.5rem; }
        .doc-preview-content.preview-mode { background: #fff; color: #1a1a1a; }
        .doc-preview-content.preview-mode h1, .doc-preview-content.preview-mode h2, .doc-preview-content.preview-mode h3 { color: #1a1a1a; margin-top: 1.5em; margin-bottom: 0.5em; }
        .doc-preview-content.preview-mode h1 { font-size: 2rem; border-bottom: 1px solid #e5e5e5; padding-bottom: 0.3em; }
        .doc-preview-content.preview-mode h2 { font-size: 1.5rem; }
        .doc-preview-content.preview-mode h3 { font-size: 1.25rem; }
        .doc-preview-content.preview-mode p { margin: 1em 0; line-height: 1.7; }
        .doc-preview-content.preview-mode code { background: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }
        .doc-preview-content.preview-mode pre { background: #f5f5f5; padding: 1em; border-radius: 5px; overflow-x: auto; }
        .doc-preview-content.preview-mode pre code { background: none; padding: 0; }
        .doc-preview-content.preview-mode blockquote { border-left: 4px solid var(--primary); margin: 1em 0; padding-left: 1em; color: #666; }
        .doc-preview-content.preview-mode table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        .doc-preview-content.preview-mode th, .doc-preview-content.preview-mode td { border: 1px solid #ddd; padding: 0.5em; text-align: left; }
        .doc-preview-content.preview-mode th { background: #f5f5f5; }
        .doc-preview-content.preview-mode ul, .doc-preview-content.preview-mode ol { margin: 1em 0; padding-left: 2em; }
        .doc-preview-content.preview-mode li { margin: 0.5em 0; }
        .doc-preview-content.preview-mode a { color: var(--primary); }
        .doc-preview-content.source-mode { font-family: 'Monaco', 'Menlo', monospace; font-size: 0.85rem; white-space: pre-wrap; }
        .doc-metadata { background: var(--bg); padding: 1rem; border-radius: 0.25rem; margin-bottom: 1rem; font-size: 0.85rem; }
        .doc-metadata dt { color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; margin-top: 0.5rem; }
        .doc-metadata dd { margin: 0; margin-bottom: 0.5rem; }
        .lang-select { padding: 0.5rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); width: 100%; }
        .yaml-viewer { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; overflow-x: auto; }
        .yaml-key { color: #9cdcfe; }
        .yaml-string { color: #ce9178; }
        .yaml-number { color: #b5cea8; }
        .empty-state { text-align: center; padding: 3rem; color: var(--text-muted); }
        .issue-clickable { cursor: pointer; transition: transform 0.1s, box-shadow 0.1s; }
        .issue-clickable:hover { transform: translateX(4px); box-shadow: -4px 0 0 var(--primary); }
        .issue-file { opacity: 0.8; }
        .issue-file:hover { text-decoration: underline; }
        .highlight-line { background: rgba(255, 235, 59, 0.3); animation: highlight-fade 2s ease-out; }
        @keyframes highlight-fade { from { background: rgba(255, 235, 59, 0.5); } to { background: transparent; } }
        .source-lines { font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-size: 0.85rem; }
        .source-line { display: flex; line-height: 1.5; padding: 0 0.5rem; }
        .source-line:hover { background: rgba(59, 130, 246, 0.1); }
        .line-number { color: var(--text-muted); min-width: 3rem; text-align: right; padding-right: 1rem; user-select: none; }
        .line-content { white-space: pre-wrap; word-break: break-all; flex: 1; }
        .theme-toggle { background: transparent; border: 1px solid var(--border); padding: 0.5rem; border-radius: 0.25rem; cursor: pointer; font-size: 1rem; }
        .theme-toggle:hover { background: var(--border); }

        /* Light mode styles */
        body.light-mode { --bg: #f8fafc; --bg-card: #ffffff; --border: #e2e8f0; --text: #1e293b; --text-muted: #64748b; }
        body.light-mode .doc-preview-content.source-mode { background: #f8f8f8; color: #333; }
        body.light-mode .yaml-viewer { background: #f5f5f5; color: #333; }
        body.light-mode .issue-warning { background: #fef3c7; border-left-color: #f59e0b; }
        body.light-mode .issue-error { background: #fee2e2; border-left-color: #ef4444; }
        body.light-mode .matrix-cell { color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1 id="project-name">Media Engine Dashboard</h1>
                <span class="stat-label" id="project-path"></span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div class="users-online" id="users-online"></div>
                <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle theme">☀️</button>
            </div>
        </header>

        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('documents')">Documents</button>
            <button class="tab" onclick="showTab('translations')">Translations</button>
            <button class="tab" onclick="showTab('quality')">Quality</button>
            <button class="tab" onclick="showTab('activity')">Activity</button>
        </div>

        <div id="tab-overview">
            <div class="grid grid-4" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Documents</div>
                    <div class="stat" id="stat-docs">-</div>
                    <div class="stat-label">total chapters</div>
                </div>
                <div class="card">
                    <div class="card-title">Languages</div>
                    <div class="stat" id="stat-langs">-</div>
                    <div class="stat-label">configured</div>
                </div>
                <div class="card">
                    <div class="card-title">Translations</div>
                    <div class="stat" id="stat-trans">-</div>
                    <div class="stat-label" id="stat-trans-detail">synced</div>
                </div>
                <div class="card">
                    <div class="card-title">Quality</div>
                    <div class="stat" id="stat-quality">-</div>
                    <div class="stat-label" id="stat-quality-detail">issues</div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Translation Matrix</div>
                    </div>
                    <div id="matrix-container"><div class="loading">Loading...</div></div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Recent Issues</div>
                    </div>
                    <div id="issues-container"><div class="loading">Loading...</div></div>
                </div>
            </div>
        </div>

        <div id="tab-documents" style="display: none;">
            <div class="doc-browser">
                <div class="doc-sidebar">
                    <div class="doc-sidebar-header">
                        <select id="lang-select" class="lang-select" onchange="loadDocuments()">
                        </select>
                    </div>
                    <div class="doc-list" id="doc-list">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
                <div class="doc-preview">
                    <div class="doc-preview-header">
                        <div>
                            <strong id="preview-title">Select a document</strong>
                            <span id="preview-path" class="stat-label"></span>
                        </div>
                        <div class="doc-preview-tabs">
                            <button class="preview-tab active" onclick="setPreviewMode('preview')">Preview</button>
                            <button class="preview-tab" onclick="setPreviewMode('source')">Source</button>
                            <button class="preview-tab" onclick="setPreviewMode('metadata')">Metadata</button>
                        </div>
                    </div>
                    <div class="doc-preview-content preview-mode" id="preview-content">
                        <div class="empty-state">Select a document from the list to preview</div>
                    </div>
                </div>
            </div>
        </div>

        <div id="tab-translations" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">All Translations</div>
                </div>
                <div id="translations-table"><div class="loading">Loading...</div></div>
            </div>
        </div>

        <div id="tab-quality" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Quality Report</div>
                </div>
                <div id="quality-report"><div class="loading">Loading...</div></div>
            </div>
        </div>

        <div id="tab-activity" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Audit Log</div>
                </div>
                <div id="audit-log"><div class="loading">Loading...</div></div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '';
        let ws = null;
        const userId = 'user-' + Math.random().toString(36).substr(2, 9);

        async function fetchAPI(endpoint) {
            const res = await fetch(API_BASE + endpoint);
            return res.json();
        }

        async function loadProject() {
            const data = await fetchAPI('/api/project');
            document.getElementById('project-name').textContent = data.name;
            document.getElementById('project-path').textContent = data.root;
            document.getElementById('stat-langs').textContent = Object.keys(data.languages).length;
        }

        async function loadStatus() {
            const data = await fetchAPI('/api/status');
            let totalDocs = 0;
            for (const lang in data.content) {
                totalDocs += data.content[lang].chapters || 0;
            }
            document.getElementById('stat-docs').textContent = totalDocs;
        }

        async function loadTranslations() {
            const data = await fetchAPI('/api/translations');
            document.getElementById('stat-trans').textContent = data.current + '/' + data.total;
            document.getElementById('stat-trans-detail').textContent =
                data.outdated > 0 ? data.outdated + ' outdated' : 'all synced';

            // Full table
            let html = '<table><thead><tr><th>Source</th><th>Translation</th><th>Status</th><th>Version</th></tr></thead><tbody>';
            for (const t of data.translations) {
                const statusClass = t.is_outdated ? 'status-warn' : 'status-ok';
                html += '<tr>';
                html += '<td>' + t.source_title + '</td>';
                html += '<td>' + t.translation_title + ' (' + t.target_language + ')</td>';
                html += '<td><span class="status-badge ' + statusClass + '">' + t.status + '</span></td>';
                html += '<td>' + t.translated_version + ' / ' + t.source_version + '</td>';
                html += '</tr>';
            }
            html += '</tbody></table>';
            document.getElementById('translations-table').innerHTML = html;
        }

        async function loadMatrix() {
            const data = await fetchAPI('/api/translations/matrix');
            let html = '<table><thead><tr><th>Document</th>';
            for (const lang of data.languages) {
                html += '<th style="text-align:center">' + lang.toUpperCase() + '</th>';
            }
            html += '</tr></thead><tbody>';

            for (const doc of data.documents) {
                html += '<tr><td title="' + doc.source_path + '">' + doc.title + '</td>';
                for (const lang of data.languages) {
                    const t = doc.translations[lang];
                    const cellClass = 'cell-' + t.status;
                    const icon = t.status === 'source' ? 'S' :
                                 t.status === 'current' ? '✓' :
                                 t.status === 'outdated' ? '!' : '?';
                    html += '<td style="text-align:center"><span class="matrix-cell ' + cellClass + '">' + icon + '</span></td>';
                }
                html += '</tr>';
            }
            html += '</tbody></table>';
            document.getElementById('matrix-container').innerHTML = html;
        }

        async function loadQuality() {
            const data = await fetchAPI('/api/quality');
            document.getElementById('stat-quality').textContent = data.total;
            document.getElementById('stat-quality-detail').textContent =
                data.errors > 0 ? data.errors + ' errors' :
                data.warnings > 0 ? data.warnings + ' warnings' : 'all good';

            // Issues list
            let html = '';
            const recentIssues = data.issues.slice(0, 5);
            if (recentIssues.length === 0) {
                html = '<div style="color: var(--success);">No issues found</div>';
            }
            for (const issue of recentIssues) {
                const issueClass = issue.severity === 'error' ? 'issue-error' : 'issue-warning';
                const clickable = issue.file ? ' issue-clickable' : '';
                const onclick = issue.file ? ' onclick="openIssueFile(\\'' + issue.file.replace(/'/g, "\\\\'") + '\\', ' + (issue.line || 0) + ')"' : '';
                html += '<div class="issue ' + issueClass + clickable + '"' + onclick + '>';
                html += '<strong>' + issue.category + '</strong>: ' + issue.message;
                if (issue.file) html += '<br><small class="issue-file">' + issue.file + '</small>';
                html += '</div>';
            }
            document.getElementById('issues-container').innerHTML = html;

            // Full report
            let reportHtml = '<div style="margin-bottom: 1rem;">Errors: ' + data.errors + ' | Warnings: ' + data.warnings + '</div>';
            for (const issue of data.issues) {
                const issueClass = issue.severity === 'error' ? 'issue-error' : 'issue-warning';
                const clickable = issue.file ? ' issue-clickable' : '';
                const onclick = issue.file ? ' onclick="openIssueFile(\\'' + issue.file.replace(/'/g, "\\\\'") + '\\', ' + (issue.line || 0) + ')"' : '';
                reportHtml += '<div class="issue ' + issueClass + clickable + '"' + onclick + '>';
                reportHtml += '<strong>' + issue.category + '</strong>: ' + issue.message;
                if (issue.file) reportHtml += '<br><small class="issue-file">' + issue.file + (issue.line ? ':' + issue.line : '') + '</small>';
                reportHtml += '</div>';
            }
            document.getElementById('quality-report').innerHTML = reportHtml || 'No issues';
        }

        async function loadAuditLog() {
            try {
                const data = await fetchAPI('/api/audit-log');
                let html = '<table><thead><tr><th>Time</th><th>Action</th><th>User</th><th>Details</th></tr></thead><tbody>';
                for (const entry of data.entries.reverse().slice(0, 50)) {
                    html += '<tr>';
                    html += '<td>' + new Date(entry.timestamp).toLocaleString() + '</td>';
                    html += '<td>' + entry.action + '</td>';
                    html += '<td>' + (entry.user || '-') + '</td>';
                    html += '<td>' + (entry.details || '-') + '</td>';
                    html += '</tr>';
                }
                html += '</tbody></table>';
                document.getElementById('audit-log').innerHTML = html || '<div>No audit entries</div>';
            } catch (e) {
                document.getElementById('audit-log').innerHTML = '<div>Audit log not available</div>';
            }
        }

        function showTab(name) {
            document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + name).style.display = 'block';
            event.target.classList.add('active');
            if (name === 'documents' && !documentsLoaded) {
                initDocumentBrowser();
            }
        }

        // Document browser state
        let documentsLoaded = false;
        let currentDoc = null;
        let currentDocData = null;
        let previewMode = 'preview';
        let projectLanguages = [];

        async function initDocumentBrowser() {
            const data = await fetchAPI('/api/project');
            projectLanguages = Object.keys(data.languages);

            const select = document.getElementById('lang-select');
            select.innerHTML = projectLanguages.map(lang =>
                '<option value="' + lang + '">' + lang.toUpperCase() + ' - ' + data.languages[lang].name + '</option>'
            ).join('');

            documentsLoaded = true;
            loadDocuments();
        }

        async function loadDocuments() {
            const lang = document.getElementById('lang-select').value;
            if (!lang) return;

            const docList = document.getElementById('doc-list');
            docList.innerHTML = '<div class="loading">Loading...</div>';

            try {
                const data = await fetchAPI('/api/documents/' + lang);

                // Group by type
                const grouped = {};
                for (const doc of data.documents) {
                    if (!grouped[doc.type]) grouped[doc.type] = [];
                    grouped[doc.type].push(doc);
                }

                let html = '';
                const typeLabels = {
                    chapter: 'Chapters',
                    script: 'Video Scripts',
                    diagram: 'Diagrams',
                    slides: 'Slides',
                    data: 'Data Files',
                    demo: 'Interactive Demos'
                };

                for (const [type, docs] of Object.entries(grouped)) {
                    html += '<div style="padding: 0.5rem 1rem; background: var(--bg); font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">' + (typeLabels[type] || type) + '</div>';
                    for (const doc of docs) {
                        const isActive = currentDoc === doc.path ? 'active' : '';
                        html += '<div class="doc-item ' + isActive + '" onclick="loadDocument(\\'' + doc.path.replace(/'/g, "\\\\'") + '\\', \\'' + doc.type + '\\')">';
                        html += '<div class="doc-item-title">' + doc.title + '</div>';
                        html += '<div class="doc-item-meta">' + doc.filename + '</div>';
                        html += '</div>';
                    }
                }

                docList.innerHTML = html || '<div class="empty-state">No documents found</div>';
            } catch (e) {
                docList.innerHTML = '<div class="empty-state">Error loading documents</div>';
            }
        }

        async function loadDocument(path, type) {
            currentDoc = path;

            // Update active state in list
            document.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
            event.target.closest('.doc-item').classList.add('active');

            const previewContent = document.getElementById('preview-content');
            previewContent.innerHTML = '<div class="loading">Loading...</div>';

            try {
                if (type === 'chapter') {
                    const data = await fetchAPI('/api/document?path=' + encodeURIComponent(path));
                    currentDocData = data;
                    document.getElementById('preview-title').textContent = data.title;
                    document.getElementById('preview-path').textContent = data.path;
                    renderDocPreview();
                } else {
                    const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                    currentDocData = {
                        title: data.filename,
                        content: data.content,
                        html: '<pre class="yaml-viewer">' + escapeHtml(data.content) + '</pre>',
                        metadata: data.parsed || {},
                        isYaml: true
                    };
                    document.getElementById('preview-title').textContent = data.filename;
                    document.getElementById('preview-path').textContent = data.path;
                    renderDocPreview();
                }
            } catch (e) {
                previewContent.innerHTML = '<div class="empty-state">Error loading document</div>';
            }
        }

        function renderDocPreview() {
            const previewContent = document.getElementById('preview-content');
            if (!currentDocData) return;

            if (previewMode === 'preview') {
                previewContent.className = 'doc-preview-content preview-mode';
                previewContent.innerHTML = currentDocData.html;
            } else if (previewMode === 'source') {
                previewContent.className = 'doc-preview-content source-mode';
                previewContent.textContent = currentDocData.content;
            } else if (previewMode === 'metadata') {
                previewContent.className = 'doc-preview-content';
                let html = '<div class="doc-metadata"><dl>';
                for (const [key, value] of Object.entries(currentDocData.metadata || {})) {
                    html += '<dt>' + escapeHtml(key) + '</dt>';
                    html += '<dd>' + escapeHtml(typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)) + '</dd>';
                }
                html += '</dl></div>';
                if (Object.keys(currentDocData.metadata || {}).length === 0) {
                    html = '<div class="empty-state">No metadata available</div>';
                }
                previewContent.innerHTML = html;
            }
        }

        function setPreviewMode(mode) {
            previewMode = mode;
            document.querySelectorAll('.preview-tab').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            renderDocPreview();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Open file from issue click
        let pendingLine = 0;
        async function openIssueFile(filePath, line) {
            pendingLine = line;

            // Detect language from path (e.g., /content/en/... or /content/no/...)
            const langMatch = filePath.match(/\\/content\\/([a-z]{2})\\//);
            const lang = langMatch ? langMatch[1] : projectLanguages[0];

            // Determine file type from path
            let fileType = 'chapter';
            if (filePath.includes('/scripts/')) fileType = 'script';
            else if (filePath.includes('/diagrams/')) fileType = 'diagram';
            else if (filePath.includes('/slides/')) fileType = 'slides';
            else if (filePath.includes('/data/')) fileType = 'data';
            else if (filePath.includes('/demos/')) fileType = 'demo';

            // Switch to documents tab
            document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-documents').style.display = 'block';
            document.querySelectorAll('.tab')[1].classList.add('active');

            // Init documents if needed
            if (!documentsLoaded) {
                await initDocumentBrowser();
            }

            // Select language
            const select = document.getElementById('lang-select');
            if (select.value !== lang) {
                select.value = lang;
                await loadDocuments();
            }

            // Load the document in source mode to show line
            previewMode = 'source';
            document.querySelectorAll('.preview-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.preview-tab')[1].classList.add('active');

            await loadDocumentDirect(filePath, fileType);
        }

        async function loadDocumentDirect(path, type) {
            currentDoc = path;

            const previewContent = document.getElementById('preview-content');
            previewContent.innerHTML = '<div class="loading">Loading...</div>';

            try {
                if (type === 'chapter') {
                    const data = await fetchAPI('/api/document?path=' + encodeURIComponent(path));
                    currentDocData = data;
                    document.getElementById('preview-title').textContent = data.title;
                    document.getElementById('preview-path').textContent = data.path;
                } else {
                    const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                    currentDocData = {
                        title: data.filename,
                        content: data.content,
                        html: '<pre class="yaml-viewer">' + escapeHtml(data.content) + '</pre>',
                        metadata: data.parsed || {},
                        isYaml: true
                    };
                    document.getElementById('preview-title').textContent = data.filename;
                    document.getElementById('preview-path').textContent = data.path;
                }

                renderDocPreviewWithHighlight(pendingLine);
                pendingLine = 0;

                // Update doc list selection
                document.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
            } catch (e) {
                previewContent.innerHTML = '<div class="empty-state">Error loading document</div>';
            }
        }

        function renderDocPreviewWithHighlight(line) {
            const previewContent = document.getElementById('preview-content');
            if (!currentDocData) return;

            previewContent.className = 'doc-preview-content source-mode';
            const lines = currentDocData.content.split('\\n');
            let html = '<div class="source-lines">';
            for (let i = 0; i < lines.length; i++) {
                const lineNum = i + 1;
                const highlight = lineNum === line ? ' highlight-line' : '';
                const lineId = lineNum === line ? ' id="target-line"' : '';
                html += '<div class="source-line' + highlight + '"' + lineId + '>';
                html += '<span class="line-number">' + lineNum + '</span>';
                html += '<span class="line-content">' + escapeHtml(lines[i]) + '</span>';
                html += '</div>';
            }
            html += '</div>';
            previewContent.innerHTML = html;

            // Scroll to target line
            if (line > 0) {
                setTimeout(() => {
                    const targetLine = document.getElementById('target-line');
                    if (targetLine) {
                        targetLine.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 100);
            }
        }

        // Dark/Light mode toggle
        let darkMode = true;
        function toggleTheme() {
            darkMode = !darkMode;
            document.body.classList.toggle('light-mode', !darkMode);
            localStorage.setItem('theme', darkMode ? 'dark' : 'light');
            document.getElementById('theme-toggle').textContent = darkMode ? '☀️' : '🌙';
        }

        // Load saved theme
        (function() {
            if (localStorage.getItem('theme') === 'light') {
                darkMode = false;
                document.body.classList.add('light-mode');
            }
            // Set initial icon after DOM ready
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('theme-toggle').textContent = darkMode ? '☀️' : '🌙';
            });
        })();

        function connectWebSocket() {
            ws = new WebSocket('ws://' + window.location.host + '/ws/' + userId);
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'user_joined' || data.type === 'user_left') {
                    updateOnlineUsers();
                } else if (data.type === 'document_saved') {
                    loadAll();
                }
            };
            ws.onclose = function() {
                setTimeout(connectWebSocket, 3000);
            };
        }

        function updateOnlineUsers() {
            // Placeholder - would show connected users
        }

        async function loadAll() {
            await Promise.all([
                loadProject(),
                loadStatus(),
                loadTranslations(),
                loadMatrix(),
                loadQuality(),
                loadAuditLog(),
            ]);
        }

        loadAll();
        connectWebSocket();
        setInterval(loadAll, 30000);
    </script>
</body>
</html>"""


def run_dashboard(
    project_path: Optional[Path] = None,
    host: str = "127.0.0.1",
    port: int = 8080,
    open_browser: bool = True,
):
    """
    Run the dashboard server.

    Args:
        project_path: Path to project root
        host: Host to bind to
        port: Port to bind to
        open_browser: Whether to open browser automatically
    """
    if not HAS_FASTAPI:
        raise RuntimeError(
            "FastAPI not installed. Install with: pip install media-engine[web]"
        )

    app = create_app(project_path)

    if open_browser:
        import threading
        def open_browser_delayed():
            import time
            time.sleep(1)
            webbrowser.open(f"http://{host}:{port}")
        threading.Thread(target=open_browser_delayed, daemon=True).start()

    uvicorn.run(app, host=host, port=port)
