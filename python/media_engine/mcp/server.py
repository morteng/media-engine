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
from datetime import datetime
from pathlib import Path
from typing import Optional

# MCP SDK import - graceful fallback
try:
    from mcp.server import FastMCP

    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    FastMCP = object


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
            self.mcp = FastMCP("media-engine")
            self._register_all()
        else:
            self.mcp = None

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
        Relative paths are resolved from project root.
        """
        if not self.project:
            raise ValueError("No project loaded")

        # Resolve and check if within project
        try:
            project_root = self.project.root.resolve()

            # Handle relative paths by prepending project root
            path_obj = Path(path)
            if not path_obj.is_absolute():
                path_obj = project_root / path_obj

            resolved = path_obj.resolve()

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

        # Import tool registration functions
        from .tools import (
            ai,
            ai_context,
            audit,
            batch,
            brand,
            build,
            cache,
            claude,
            context,
            dependencies,
            diagrams,
            documents,
            hierarchy,
            motion_design,
            notes,
            project,
            provenance,
            publications,
            quality,
            relationships,
            reports,
            search,
            session,
            suggestions,
            translation,
            video_producer,
            video_render,
            webhooks,
        )

        # Register all tool categories
        project.register_project_tools(self.mcp, self)
        documents.register_document_tools(self.mcp, self)
        translation.register_translation_tools(self.mcp, self)
        quality.register_quality_tools(self.mcp, self)
        brand.register_brand_tools(self.mcp, self)
        reports.register_report_tools(self.mcp, self)  # Comprehensive quality reports
        search.register_search_tools(self.mcp, self)
        build.register_build_tools(self.mcp, self)
        diagrams.register_diagram_tools(self.mcp, self)
        cache.register_cache_tools(self.mcp, self)
        audit.register_audit_tools(self.mcp, self)
        provenance.register_provenance_tools(self.mcp, self)
        notes.register_notes_tools(self.mcp, self)
        hierarchy.register_hierarchy_tools(self.mcp, self)  # Document hierarchy & info flow
        dependencies.register_dependency_tools(self.mcp, self)  # Hash-based dependency tracking
        relationships.register_relationship_tools(self.mcp, self)  # Unified relationship registry
        publications.register_publication_tools(self.mcp, self)  # Composite document publications

        # Enhanced AI agent tools
        context.register_context_tools(self.mcp, self)
        suggestions.register_suggestion_tools(self.mcp, self)
        batch.register_batch_tools(self.mcp, self)
        session.register_session_tools(self.mcp, self)
        claude.register_claude_tools(self.mcp, self)
        ai.register_ai_tools(self.mcp, self)
        ai_context.register_ai_context_tools(self.mcp, self)  # AI context & session management
        webhooks.register_webhook_tools(self.mcp, self)

        # Video production tools (autonomous video producer agent)
        video_producer.register_video_producer_tools(self.mcp, self)
        motion_design.register_motion_design_tools(self.mcp, self)
        video_render.register_video_render_tools(self.mcp, self)

    def _register_resources(self):
        """Register MCP resources for context."""
        from . import helpers, resources

        resources.register_resources(self.mcp, self, helpers.get_health_summary)

    def _register_prompts(self):
        """Register prompts for common workflows."""
        from . import resources

        resources.register_prompts(self.mcp)

    # === Helper Methods ===

    def _get_health_summary(self) -> dict:
        """Get project health summary."""
        from . import helpers

        return helpers.get_health_summary(self.project)

    def _version_diff(self, old: str, new: str) -> str:
        """Calculate version difference description."""
        from . import helpers

        return helpers.version_diff(old, new)

    async def run(self):
        """Run the MCP server."""
        if not HAS_MCP:
            raise RuntimeError("MCP SDK not installed. Install with: pip install media-engine[mcp]")

        await self.mcp.run_stdio_async()


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
