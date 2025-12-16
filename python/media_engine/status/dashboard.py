"""
Project Dashboard Module

Provides comprehensive project status views.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn
from rich import box

if TYPE_CHECKING:
    from ..core.project import Project

console = Console()


@dataclass
class DocumentStatus:
    """Status of a document."""
    path: Path
    title: str
    status: str  # draft, review, final
    version: str
    last_modified: Optional[datetime] = None
    word_count: int = 0
    freshness_status: str = "fresh"  # fresh, stale, expired
    days_old: int = 0


@dataclass
class ContentStatus:
    """Status of all content for a language."""
    language: str
    chapters: List[DocumentStatus] = field(default_factory=list)
    research: List[DocumentStatus] = field(default_factory=list)
    total_words: int = 0
    completion_percent: float = 0.0
    stale_count: int = 0


@dataclass
class VideoStatus:
    """Status of video production."""
    script_name: str
    language: str
    has_script: bool = False
    has_voiceover: bool = False
    has_captions: bool = False
    has_video: bool = False
    duration_seconds: float = 0.0
    status: str = "not_started"  # not_started, in_progress, complete


@dataclass
class DeliverableStatus:
    """Status of a deliverable output."""
    name: str
    type: str  # html, pdf, pptx, xlsx, video
    language: str
    exists: bool = False
    path: Optional[Path] = None
    last_built: Optional[datetime] = None
    is_stale: bool = False


@dataclass
class ProjectDashboard:
    """Complete project status dashboard."""
    project_name: str
    project_root: Path
    languages: List[str] = field(default_factory=list)
    source_language: str = "en"
    content_status: Dict[str, ContentStatus] = field(default_factory=dict)
    video_status: List[VideoStatus] = field(default_factory=list)
    deliverables: List[DeliverableStatus] = field(default_factory=list)
    quality_issues: int = 0
    cache_size_mb: float = 0.0
    last_build: Optional[datetime] = None

    @property
    def total_chapters(self) -> int:
        return sum(len(c.chapters) for c in self.content_status.values())

    @property
    def total_words(self) -> int:
        return sum(c.total_words for c in self.content_status.values())

    @property
    def completion_percent(self) -> float:
        if not self.content_status:
            return 0.0
        return sum(c.completion_percent for c in self.content_status.values()) / len(self.content_status)

    @property
    def video_completion(self) -> float:
        if not self.video_status:
            return 0.0
        complete = sum(1 for v in self.video_status if v.status == "complete")
        return (complete / len(self.video_status)) * 100

    @property
    def deliverable_count(self) -> int:
        return sum(1 for d in self.deliverables if d.exists)


def get_content_status(project: "Project", language: str) -> ContentStatus:
    """Get content status for a specific language."""
    from ..cms import Document

    status = ContentStatus(language=language)

    # Get chapters
    for chapter_path in project.list_chapters(language):
        try:
            doc = Document.load(chapter_path)
            doc_status = DocumentStatus(
                path=chapter_path,
                title=doc.title,
                status=doc.metadata.get("status", "draft"),
                version=doc.metadata.get("version", "0.0.0"),
                last_modified=doc.last_modified,
                word_count=len(doc.content.split()),
                freshness_status=doc.freshness_status,
                days_old=doc.days_since_modified,
            )
            status.chapters.append(doc_status)
            status.total_words += doc_status.word_count

            if doc_status.freshness_status in ("stale", "expired"):
                status.stale_count += 1
        except Exception:
            pass

    # Calculate completion based on status
    if status.chapters:
        final_count = sum(1 for c in status.chapters if c.status == "final")
        status.completion_percent = (final_count / len(status.chapters)) * 100

    return status


def get_video_status(project: "Project", language: str) -> List[VideoStatus]:
    """Get video production status for a language."""
    videos = []

    scripts_dir = project.get_content_path(language, "scripts")
    if not scripts_dir.exists():
        return videos

    output_dir = project.output_dir / language / "videos"
    audio_dir = project.cache_dir / "voiceover" / language

    for script_file in scripts_dir.glob("*.yaml"):
        name = script_file.stem
        status = VideoStatus(
            script_name=name,
            language=language,
            has_script=True,
        )

        # Check for voiceover audio
        if audio_dir.exists():
            audio_file = audio_dir / f"{name}.mp3"
            if audio_file.exists():
                status.has_voiceover = True

        # Check for captions
        if output_dir.exists():
            caption_file = output_dir / f"{name}.vtt"
            if caption_file.exists():
                status.has_captions = True

        # Check for final video
        if output_dir.exists():
            video_file = output_dir / f"{name}.mp4"
            if video_file.exists():
                status.has_video = True

        # Determine overall status
        if status.has_video:
            status.status = "complete"
        elif status.has_voiceover or status.has_captions:
            status.status = "in_progress"
        else:
            status.status = "not_started"

        videos.append(status)

    return videos


def get_deliverable_status(project: "Project") -> List[DeliverableStatus]:
    """Get status of all deliverables."""
    deliverables = []

    for language in project.languages:
        output_dir = project.output_dir / language

        # HTML proposal
        html_path = output_dir / "proposal.html"
        deliverables.append(DeliverableStatus(
            name="Proposal",
            type="html",
            language=language,
            exists=html_path.exists(),
            path=html_path if html_path.exists() else None,
            last_built=datetime.fromtimestamp(html_path.stat().st_mtime) if html_path.exists() else None,
        ))

        # PDF proposal
        pdf_path = output_dir / "proposal.pdf"
        deliverables.append(DeliverableStatus(
            name="Proposal",
            type="pdf",
            language=language,
            exists=pdf_path.exists(),
            path=pdf_path if pdf_path.exists() else None,
            last_built=datetime.fromtimestamp(pdf_path.stat().st_mtime) if pdf_path.exists() else None,
        ))

        # Presentations
        presentations_dir = output_dir / "presentations"
        if presentations_dir.exists():
            for pres in presentations_dir.glob("*.pptx"):
                deliverables.append(DeliverableStatus(
                    name=pres.stem.replace("_", " ").title(),
                    type="pptx",
                    language=language,
                    exists=True,
                    path=pres,
                    last_built=datetime.fromtimestamp(pres.stat().st_mtime),
                ))

        # Videos
        videos_dir = output_dir / "videos"
        if videos_dir.exists():
            for video in videos_dir.glob("*.mp4"):
                deliverables.append(DeliverableStatus(
                    name=video.stem.replace("-", " ").replace("_", " ").title(),
                    type="video",
                    language=language,
                    exists=True,
                    path=video,
                    last_built=datetime.fromtimestamp(video.stat().st_mtime),
                ))

    return deliverables


def get_project_dashboard(project: "Project") -> ProjectDashboard:
    """Generate complete project dashboard."""
    dashboard = ProjectDashboard(
        project_name=project.name,
        project_root=project.root,
        languages=list(project.languages.keys()),
        source_language=project.source_language,
    )

    # Content status for each language
    for language in project.languages:
        dashboard.content_status[language] = get_content_status(project, language)

    # Video status for each language
    for language in project.languages:
        dashboard.video_status.extend(get_video_status(project, language))

    # Deliverables
    dashboard.deliverables = get_deliverable_status(project)

    # Cache size
    if project.cache_dir.exists():
        total_size = sum(f.stat().st_size for f in project.cache_dir.rglob("*") if f.is_file())
        dashboard.cache_size_mb = total_size / 1024 / 1024

    return dashboard


def print_dashboard(dashboard: ProjectDashboard):
    """Print comprehensive dashboard to console."""
    # Header
    console.print()
    console.print(Panel(
        f"[bold]{dashboard.project_name}[/bold]\n"
        f"[dim]{dashboard.project_root}[/dim]",
        title="Media Engine Dashboard",
        border_style="blue"
    ))

    # Overview stats
    console.print()
    console.print("[bold]Overview[/bold]")
    console.print(f"  Languages: {', '.join(dashboard.languages)} (source: {dashboard.source_language})")
    console.print(f"  Chapters: {dashboard.total_chapters}")
    console.print(f"  Words: {dashboard.total_words:,}")
    console.print(f"  Completion: {dashboard.completion_percent:.0f}%")
    console.print(f"  Cache: {dashboard.cache_size_mb:.1f} MB")

    # Content status table
    console.print()
    content_table = Table(title="Content Status", box=box.ROUNDED)
    content_table.add_column("Language", style="cyan")
    content_table.add_column("Chapters", justify="right")
    content_table.add_column("Words", justify="right")
    content_table.add_column("Complete", justify="right")
    content_table.add_column("Stale", justify="right")

    for lang, status in dashboard.content_status.items():
        is_source = lang == dashboard.source_language
        lang_display = f"[bold]{lang}[/bold]" if is_source else lang
        stale_display = f"[yellow]{status.stale_count}[/yellow]" if status.stale_count > 0 else "[dim]0[/dim]"

        content_table.add_row(
            lang_display,
            str(len(status.chapters)),
            f"{status.total_words:,}",
            f"{status.completion_percent:.0f}%",
            stale_display,
        )

    console.print(content_table)

    # Video status table
    if dashboard.video_status:
        console.print()
        video_table = Table(title="Video Production", box=box.ROUNDED)
        video_table.add_column("Script", style="cyan")
        video_table.add_column("Lang", justify="center")
        video_table.add_column("Script", justify="center")
        video_table.add_column("Audio", justify="center")
        video_table.add_column("Captions", justify="center")
        video_table.add_column("Video", justify="center")
        video_table.add_column("Status", justify="center")

        for video in dashboard.video_status:
            status_color = {
                "complete": "green",
                "in_progress": "yellow",
                "not_started": "dim",
            }.get(video.status, "white")

            video_table.add_row(
                video.script_name,
                video.language,
                "[green]✓[/green]" if video.has_script else "[dim]–[/dim]",
                "[green]✓[/green]" if video.has_voiceover else "[dim]–[/dim]",
                "[green]✓[/green]" if video.has_captions else "[dim]–[/dim]",
                "[green]✓[/green]" if video.has_video else "[dim]–[/dim]",
                f"[{status_color}]{video.status}[/{status_color}]",
            )

        console.print(video_table)

    # Deliverables table
    existing_deliverables = [d for d in dashboard.deliverables if d.exists]
    if existing_deliverables:
        console.print()
        del_table = Table(title="Deliverables", box=box.ROUNDED)
        del_table.add_column("Name", style="cyan")
        del_table.add_column("Type", justify="center")
        del_table.add_column("Lang", justify="center")
        del_table.add_column("Built", justify="right")

        for d in existing_deliverables:
            built_str = d.last_built.strftime("%Y-%m-%d %H:%M") if d.last_built else "–"
            del_table.add_row(
                d.name,
                d.type.upper(),
                d.language,
                built_str,
            )

        console.print(del_table)

    # Summary
    console.print()
    total_videos = len(dashboard.video_status)
    complete_videos = sum(1 for v in dashboard.video_status if v.status == "complete")
    console.print(f"[dim]Videos: {complete_videos}/{total_videos} complete | Deliverables: {dashboard.deliverable_count} built[/dim]")
