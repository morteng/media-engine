"""
Publication builder - renders publications to output formats.

Coordinates the build process for publications, delegating to
format-specific builders (HTMLBuilder, PDFBuilder, PPTXBuilder).
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..core import compute_file_hash
from .models import (
    BuildStatus,
    OutputFormat,
    Publication,
    PublicationBuild,
)

if TYPE_CHECKING:
    from ..core.project import Project
    from .registry import PublicationRegistry

logger = logging.getLogger(__name__)


class PublicationBuilder:
    """
    Builds publications to their output formats.

    Handles the coordination of building a publication, including:
    - Collecting and ordering components
    - Rendering to the target format
    - Recording build status
    """

    def __init__(self, project: "Project", registry: "PublicationRegistry"):
        self.project = project
        self.registry = registry
        self.output_dir = project.root / "dist"

    def build(
        self,
        publication: Publication,
        format: OutputFormat,
        language: str = "en",
        output_dir: Optional[Path] = None,
    ) -> PublicationBuild:
        """
        Build a publication to a specific format.

        Args:
            publication: The publication to build
            format: Output format (pdf, html, pptx, etc.)
            language: Language to build
            output_dir: Optional output directory

        Returns:
            PublicationBuild record
        """
        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        build = PublicationBuild(
            publication_id=publication.id,
            format=format,
            language=language,
            status=BuildStatus.BUILDING,
            started_at=datetime.now(),
            component_hashes={},
        )

        try:
            # Collect component hashes
            for comp in publication.get_all_components():
                source_path = self.project.root / comp.source
                if source_path.exists():
                    build.component_hashes[str(comp.source)] = compute_file_hash(
                        source_path
                    )

            # Build based on format
            if format == OutputFormat.HTML:
                output_path = self._build_html(publication, language, output_dir)
            elif format == OutputFormat.PDF:
                output_path = self._build_pdf(publication, language, output_dir)
            elif format == OutputFormat.PPTX:
                output_path = self._build_pptx(publication, language, output_dir)
            elif format == OutputFormat.DOCX:
                output_path = self._build_docx(publication, language, output_dir)
            else:
                raise ValueError(f"Unsupported format: {format}")

            build.output_path = output_path
            build.status = BuildStatus.COMPLETE
            build.completed_at = datetime.now()

        except Exception as e:
            logger.error(f"Build failed: {e}")
            build.status = BuildStatus.FAILED
            build.error = str(e)
            build.completed_at = datetime.now()

        # Record the build
        self.registry.record_build(build)

        return build

    def _build_html(
        self, publication: Publication, language: str, output_dir: Path
    ) -> Path:
        """Build HTML output."""
        from ..builders import HTMLBuilder

        output_path = output_dir / f"{publication.id}_{language}.html"

        # Collect content from components
        content_parts = []
        for comp in publication.get_all_components():
            source_path = self.project.root / comp.source
            # Adjust path for language
            if language != "en":
                lang_path = self.project.root / "content" / language
                if (lang_path / comp.source.name).exists():
                    source_path = lang_path / comp.source.name

            if source_path.exists() and source_path.suffix == ".md":
                content_parts.append(source_path.read_text())

        # Build HTML
        builder = HTMLBuilder(
            theme=self.project.theme,
            brand=getattr(self.project, "brand_context", None),
        )

        combined_content = "\n\n---\n\n".join(content_parts)
        builder.build_from_markdown(
            content=combined_content,
            title=publication.title,
            output_path=output_path,
        )

        return output_path

    def _build_pdf(
        self, publication: Publication, language: str, output_dir: Path
    ) -> Path:
        """Build PDF output."""
        try:
            from ..builders.pdf import PDFBuilder
        except ImportError:
            # Fallback: build HTML first, then note PDF requires weasyprint
            html_path = self._build_html(publication, language, output_dir)
            logger.warning("PDF generation requires weasyprint. Built HTML instead.")
            return html_path

        output_path = output_dir / f"{publication.id}_{language}.pdf"

        # Collect content
        content_parts = []
        for comp in publication.get_all_components():
            source_path = self.project.root / comp.source
            if source_path.exists() and source_path.suffix == ".md":
                content_parts.append(source_path.read_text())

        builder = PDFBuilder(theme=self.project.theme)
        combined_content = "\n\n---\n\n".join(content_parts)
        builder.build_from_markdown(
            content=combined_content,
            title=publication.title,
            output_path=output_path,
        )

        return output_path

    def _build_pptx(
        self, publication: Publication, language: str, output_dir: Path
    ) -> Path:
        """Build PowerPoint output."""
        from ..builders import PPTXBuilder

        output_path = output_dir / f"{publication.id}_{language}.pptx"

        # For presentations, each component becomes a slide or slide group
        slides_data = []
        for comp in publication.get_all_components():
            source_path = self.project.root / comp.source
            if source_path.exists() and source_path.suffix == ".md":
                content = source_path.read_text()
                # Parse markdown into slide data
                slides_data.append({
                    "title": comp.title or source_path.stem,
                    "content": content,
                })

        builder = PPTXBuilder(
            theme=self.project.theme,
            brand=getattr(self.project, "brand_context", None),
        )
        builder.build_presentation(
            slides=slides_data,
            title=publication.title,
            output_path=output_path,
        )

        return output_path

    def _build_docx(
        self, publication: Publication, language: str, output_dir: Path
    ) -> Path:
        """Build Word document output."""
        # For now, build HTML and note that DOCX requires pandoc
        html_path = self._build_html(publication, language, output_dir)
        output_path = output_dir / f"{publication.id}_{language}.docx"

        # Try to convert HTML to DOCX using pandoc
        import subprocess

        try:
            subprocess.run(
                ["pandoc", str(html_path), "-o", str(output_path)],
                check=True,
                capture_output=True,
            )
            return output_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("DOCX generation requires pandoc. Built HTML instead.")
            return html_path

    def build_all(
        self,
        publication: Publication,
        output_dir: Optional[Path] = None,
    ) -> list[PublicationBuild]:
        """Build all formats and languages for a publication."""
        builds = []
        for fmt in publication.formats:
            for lang in publication.languages:
                build = self.build(publication, fmt, lang, output_dir)
                builds.append(build)
        return builds
