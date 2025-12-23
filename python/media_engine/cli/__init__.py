"""
Media Engine CLI

Agent-friendly command line interface for media production.

Usage:
    media-engine status [--json]
    media-engine build [--only FORMAT] [--force] [--lang LANG]
    media-engine publish [--formats LIST]
    media-engine stale [--json]
    media-engine cache status
    media-engine cache clear [--voiceover] [--builds]
    media-engine analyze semantic [--duplicates] [--drift] [--clusters]
    media-engine analyze llm [--completeness] [--review]
    media-engine analyze graph [--build] [--orphans] [--metrics]
    media-engine analyze norwegian [--target LEVEL]
    media-engine analyze freshness [--train] [--predict] [--queue]
    media-engine analyze codesync [--syntax] [--deprecated]
    media-engine analyze advanced [--full]
"""

import argparse
import sys

from .commands import (
    cmd_analyze,
    cmd_brand,
    cmd_build,
    cmd_cache,
    cmd_changelog,
    cmd_consistency,
    cmd_dashboard,
    cmd_demos,
    cmd_duplicates,
    cmd_freshness,
    cmd_gaps,
    cmd_graph,
    cmd_health,
    cmd_hierarchy,
    cmd_incomplete,
    cmd_index,
    cmd_init,
    cmd_integrity,
    cmd_links,
    cmd_notes,
    cmd_pack,
    cmd_parity,
    cmd_path,
    cmd_provenance,
    cmd_publish,
    cmd_quality,
    cmd_readability,
    cmd_release,
    cmd_search,
    cmd_security,
    cmd_stale,
    cmd_stats,
    cmd_status,
    cmd_terms,
    cmd_translation,
    cmd_validate,
    cmd_velocity,
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="media-engine",
        description="Agent-based media production framework",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument(
        "view",
        nargs="?",
        choices=["docs", "videos", "quality", "deliverables", "tree", "cache"],
        help="Specific view: docs, videos, quality, deliverables, tree, cache",
    )
    status_parser.add_argument("--lang", help="Filter by language")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # brand
    brand_parser = subparsers.add_parser("brand", help="Brand/design system management")
    brand_subparsers = brand_parser.add_subparsers(dest="brand_command")

    brand_subparsers.add_parser("status", help="Show brand status")
    brand_migrate = brand_subparsers.add_parser("migrate", help="Migrate theme.yaml to brand.yaml")
    brand_migrate.add_argument("--dry-run", action="store_true", help="Show what would be created")
    brand_subparsers.add_parser("validate", help="Validate brand.yaml")
    brand_subparsers.add_parser("init", help="Initialize brand.yaml from template")
    brand_export = brand_subparsers.add_parser("export-css", help="Export CSS variables")
    brand_export.add_argument("--output", "-o", help="Output file path")
    brand_export.add_argument("--dark", action="store_true", help="Generate dark mode CSS")

    # Voice commands
    brand_voice = brand_subparsers.add_parser("voice", help="Show brand voice profile")
    brand_voice.add_argument("--doc-type", help="Show profile for document type")
    brand_voice.add_argument("--audience", help="Show profile for audience")
    brand_voice.add_argument("--json", action="store_true", help="Output as JSON")

    brand_voice_check = brand_subparsers.add_parser(
        "voice-check", help="Check documents against voice guidelines"
    )
    brand_voice_check.add_argument("document", nargs="?", help="Document to check")
    brand_voice_check.add_argument("--all", action="store_true", help="Check all documents")
    brand_voice_check.add_argument("--json", action="store_true", help="Output as JSON")

    brand_context = brand_subparsers.add_parser(
        "context", help="Show effective brand context for document"
    )
    brand_context.add_argument("document", help="Document path")
    brand_context.add_argument("--json", action="store_true", help="Output as JSON")

    brand_terminology = brand_subparsers.add_parser(
        "terminology", help="Check terminology consistency"
    )
    brand_terminology.add_argument("--json", action="store_true", help="Output as JSON")

    # build
    build_parser = subparsers.add_parser("build", help="Build media outputs")
    build_parser.add_argument("--only", help="Only build specific formats (comma-separated)")
    build_parser.add_argument("--force", action="store_true", help="Force rebuild all")
    build_parser.add_argument("--lang", help="Only build specific languages (comma-separated)")
    build_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    build_parser.add_argument(
        "--quality",
        "-q",
        choices=["preview", "production"],
        default="production",
        help="Video quality: preview (720p/24fps) or production (1080p/60fps, default)",
    )

    # publish
    publish_parser = subparsers.add_parser("publish", help="Publish complete deliverable package")
    publish_parser.add_argument(
        "--output", "-o", help="Output directory (default: project publish_dir)"
    )
    publish_parser.add_argument("--no-fonts", action="store_true", help="Skip font bundling")
    publish_parser.add_argument("--no-diagrams", action="store_true", help="Skip diagram bundling")
    publish_parser.add_argument("--no-videos", action="store_true", help="Skip video bundling")
    publish_parser.add_argument(
        "--no-index", action="store_true", help="Skip navigation index generation"
    )
    publish_parser.add_argument("--zip", action="store_true", help="Create ZIP archive")

    # release
    release_parser = subparsers.add_parser(
        "release", help="Copy production videos to deliverables folder"
    )
    release_parser.add_argument("--dry-run", action="store_true", help="Show what would be copied")
    release_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing files"
    )
    release_parser.add_argument("--lang", "-l", help="Only release specific language")

    # quality
    quality_parser = subparsers.add_parser("quality", help="Run quality checks")
    quality_parser.add_argument("--json", action="store_true", help="Output as JSON")
    quality_parser.add_argument(
        "--type", "-t", help="Filter by issue type (e.g., hierarchy, placeholder, encoding)"
    )
    quality_parser.add_argument(
        "--no-hierarchy", action="store_true", help="Skip hierarchy structure checks"
    )

    # stale
    stale_parser = subparsers.add_parser("stale", help="List stale content")
    stale_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # cache
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command")

    cache_subparsers.add_parser("status", help="Show cache status")
    cache_clear = cache_subparsers.add_parser("clear", help="Clear cache")
    cache_clear.add_argument("--voiceover", action="store_true", help="Clear voiceover cache only")
    cache_clear.add_argument("--builds", action="store_true", help="Clear builds cache only")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("directory", nargs="?", help="Project directory")
    init_parser.add_argument("--name", help="Project name")

    # search
    search_parser = subparsers.add_parser("search", help="Search project documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    search_parser.add_argument("--rebuild", action="store_true", help="Rebuild index")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate project content")
    validate_parser.add_argument("--schema", help="Path to custom schema file")
    validate_parser.add_argument("--refs-only", action="store_true", help="Only check references")
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # pack
    pack_parser = subparsers.add_parser("pack", help="Generate curated packs")
    pack_parser.add_argument("type", choices=["investor", "pilot"], help="Pack type")
    pack_parser.add_argument("--output", "-o", help="Output directory")
    pack_parser.add_argument("--no-zip", action="store_true", help="Don't create ZIP archive")

    # index
    index_parser = subparsers.add_parser("index", help="Build search index")
    index_parser.add_argument("--output", "-o", help="Output path for index file")

    # translation
    trans_parser = subparsers.add_parser("translation", help="Translation tracking")
    trans_subparsers = trans_parser.add_subparsers(dest="translation_command")

    trans_status = trans_subparsers.add_parser("status", help="Show translation status")
    trans_status.add_argument("--json", action="store_true", help="Output as JSON")

    trans_outdated = trans_subparsers.add_parser("outdated", help="Show outdated translations")
    trans_outdated.add_argument("--json", action="store_true", help="Output as JSON")

    trans_missing = trans_subparsers.add_parser("missing", help="Show missing translations")
    trans_missing.add_argument("--lang", help="Target language (default: no)")
    trans_missing.add_argument("--json", action="store_true", help="Output as JSON")

    # dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Launch web dashboard")
    dash_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dash_parser.add_argument("--port", "-p", type=int, default=8080, help="Port to bind to")
    dash_parser.add_argument("--no-browser", action="store_true", help="Don't open browser")

    # provenance
    prov_parser = subparsers.add_parser("provenance", help="Provenance and approval tracking")
    prov_subparsers = prov_parser.add_subparsers(dest="provenance_command")

    prov_report = prov_subparsers.add_parser("report", help="Generate provenance report")
    prov_report.add_argument("--json", action="store_true", help="Output as JSON")

    prov_claims = prov_subparsers.add_parser("claims", help="List claims needing verification")
    prov_claims.add_argument("--json", action="store_true", help="Output as JSON")

    prov_queue = prov_subparsers.add_parser("queue", help="Show review queue")
    prov_queue.add_argument("--json", action="store_true", help="Output as JSON")

    prov_scan = prov_subparsers.add_parser("scan", help="Scan documents for potential claims")
    prov_scan.add_argument("--json", action="store_true", help="Output as JSON")

    prov_validate = prov_subparsers.add_parser(
        "validate-urls", help="Validate external URLs in claims"
    )
    prov_validate.add_argument("--json", action="store_true", help="Output as JSON")

    prov_add = prov_subparsers.add_parser("add", help="Add a new claim")
    prov_add.add_argument("--document", "-d", required=True, help="Document path")
    prov_add.add_argument("--claim", "-c", required=True, help="Claim text")
    prov_add.add_argument("--source", "-s", required=True, help="Source attribution")
    prov_add.add_argument("--url", "-u", help="Source URL (optional)")
    prov_add.add_argument(
        "--type", "-t", default="internal", help="Source type: internal, external, research, data"
    )

    prov_verify = prov_subparsers.add_parser("verify", help="Verify a claim")
    prov_verify.add_argument("--document", "-d", required=True, help="Document path")
    prov_verify.add_argument("--claim-id", "-c", required=True, help="Claim ID to verify")
    prov_verify.add_argument("--verifier", "-v", required=True, help="Verifier name")
    prov_verify.add_argument("--expiry-days", "-e", type=int, default=365, help="Days until expiry")

    # integrity
    integ_parser = subparsers.add_parser("integrity", help="Asset and terminology integrity")
    integ_subparsers = integ_parser.add_subparsers(dest="integrity_command")

    integ_verify = integ_subparsers.add_parser("verify", help="Verify asset checksums")
    integ_verify.add_argument("--json", action="store_true", help="Output as JSON")

    integ_subparsers.add_parser("record", help="Record asset checksums")

    integ_terms = integ_subparsers.add_parser("terms", help="Check terminology consistency")
    integ_terms.add_argument("--json", action="store_true", help="Output as JSON")

    # notes
    notes_parser = subparsers.add_parser("notes", help="General notes management")
    notes_subparsers = notes_parser.add_subparsers(dest="notes_command")

    notes_list = notes_subparsers.add_parser("list", help="List notes")
    notes_list.add_argument(
        "--status", choices=["pending", "completed", "archived"], help="Filter by status"
    )
    notes_list.add_argument(
        "--type",
        choices=[
            "scene",
            "document",
            "asset",
            "project",
            "chapter",
            "translation",
            "script",
            "diagram",
        ],
        help="Filter by type",
    )
    notes_list.add_argument(
        "--priority", choices=["low", "medium", "high", "critical"], help="Filter by priority"
    )
    notes_list.add_argument("--pending", action="store_true", help="Show only pending notes")
    notes_list.add_argument("--json", action="store_true", help="Output as JSON")

    notes_add = notes_subparsers.add_parser("add", help="Add a new note")
    notes_add.add_argument("--type", "-t", required=True, help="Note type")
    notes_add.add_argument("--target", "-T", required=True, help="Target content path")
    notes_add.add_argument("--text", "-m", required=True, help="Note text")
    notes_add.add_argument("--target-id", help="Sub-target ID (e.g., scene_id)")
    notes_add.add_argument("--priority", "-p", default="medium", help="Priority level")
    notes_add.add_argument("--tags", help="Comma-separated tags")

    notes_complete = notes_subparsers.add_parser("complete", help="Mark note as completed")
    notes_complete.add_argument("note_id", help="Note ID to complete")

    notes_archive = notes_subparsers.add_parser("archive", help="Archive a note")
    notes_archive.add_argument("note_id", help="Note ID to archive")

    notes_reopen = notes_subparsers.add_parser("reopen", help="Reopen a note")
    notes_reopen.add_argument("note_id", help="Note ID to reopen")

    notes_delete = notes_subparsers.add_parser("delete", help="Delete a note")
    notes_delete.add_argument("note_id", help="Note ID to delete")

    notes_report = notes_subparsers.add_parser("report", help="Generate notes report")
    notes_report.add_argument("--json", action="store_true", help="Output as JSON")

    notes_subparsers.add_parser("export", help="Export notes for agents")

    notes_migrate = notes_subparsers.add_parser("migrate", help="Migrate legacy scene notes")
    notes_migrate.add_argument("--json", action="store_true", help="Output as JSON")

    # readability
    read_parser = subparsers.add_parser("readability", help="Readability analysis")
    read_parser.add_argument(
        "--target",
        choices=["elementary", "middle_school", "high_school", "college", "graduate", "technical"],
        help="Target reading level",
    )
    read_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # gaps
    gaps_parser = subparsers.add_parser("gaps", help="Content gap analysis")
    gaps_parser.add_argument("--topics", help="Expected topics (comma-separated)")
    gaps_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # links
    links_parser = subparsers.add_parser("links", help="Link validation")
    links_parser.add_argument(
        "--internal-only", action="store_true", help="Only check internal links"
    )
    links_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # security
    sec_parser = subparsers.add_parser("security", help="Security scan for sensitive content")
    sec_parser.add_argument(
        "--include-assets", action="store_true", help="Also scan YAML/JSON assets"
    )
    sec_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # changelog
    change_parser = subparsers.add_parser("changelog", help="Generate changelog")
    change_parser.add_argument("--since", help="Start date (ISO format)")
    change_parser.add_argument("--days", type=int, help="Include last N days")
    change_parser.add_argument("--output", "-o", help="Output file")
    change_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # demos
    demos_parser = subparsers.add_parser("demos", help="Interactive HTML demos")
    demos_subparsers = demos_parser.add_subparsers(dest="demos_command")

    demos_list = demos_subparsers.add_parser("list", help="List available demos")
    demos_list.add_argument("--json", action="store_true", help="Output as JSON")

    demos_build = demos_subparsers.add_parser("build", help="Build demos to HTML")
    demos_build.add_argument("--output", "-o", help="Output directory")
    demos_build.add_argument("--json", action="store_true", help="Output as JSON")

    # freshness
    fresh_parser = subparsers.add_parser("freshness", help="Content freshness tracking")
    fresh_parser.add_argument("--scan", action="store_true", help="Scan and register all content")
    fresh_parser.add_argument("--stale", action="store_true", help="Show only stale items")
    fresh_parser.add_argument("--untracked", action="store_true", help="Show only untracked files")
    fresh_parser.add_argument("--ignored", action="store_true", help="Show ignored files")
    fresh_parser.add_argument(
        "--show-ignored", action="store_true", help="Show active ignore patterns"
    )
    fresh_parser.add_argument(
        "--type",
        help="Filter by content type (e.g., video_render, source_document)",
    )
    fresh_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # hierarchy
    hier_parser = subparsers.add_parser("hierarchy", help="Document hierarchy management")
    hier_subparsers = hier_parser.add_subparsers(dest="hierarchy_command")

    hier_status = hier_subparsers.add_parser("status", help="Show hierarchy status")
    hier_status.add_argument("--json", action="store_true", help="Output as JSON")

    hier_tree = hier_subparsers.add_parser("tree", help="Show hierarchy as tree")
    hier_tree.add_argument("--root", help="Root document path")
    hier_tree.add_argument("--dot", action="store_true", help="Output DOT format for Graphviz")

    hier_stale = hier_subparsers.add_parser("stale", help="Show stale documents")
    hier_stale.add_argument("--json", action="store_true", help="Output as JSON")

    hier_validate = hier_subparsers.add_parser("validate", help="Validate hierarchy structure")
    hier_validate.add_argument("--json", action="store_true", help="Output as JSON")

    hier_subparsers.add_parser("refresh", help="Refresh hierarchy from documents")

    hier_nav = hier_subparsers.add_parser("nav", help="Show navigation context for a document")
    hier_nav.add_argument("--document", "-d", required=True, help="Document path")
    hier_nav.add_argument("--json", action="store_true", help="Output as JSON")

    hier_anchors = hier_subparsers.add_parser("anchors", help="Show consistency anchors")
    hier_anchors.add_argument("--json", action="store_true", help="Output as JSON")
    hier_anchors.add_argument("--validate", action="store_true", help="Validate anchor references")

    hier_impact = hier_subparsers.add_parser("impact", help="Analyze impact of document changes")
    hier_impact.add_argument("--document", "-d", required=True, help="Document path")
    hier_impact.add_argument(
        "--change-type", "-t",
        choices=["content", "metadata", "delete", "anchor"],
        default="content",
        help="Type of change",
    )
    hier_impact.add_argument("--description", help="Description of the change")
    hier_impact.add_argument("--json", action="store_true", help="Output as JSON")

    hier_coverage = hier_subparsers.add_parser("coverage", help="Analyze documentation coverage")
    hier_coverage.add_argument("--json", action="store_true", help="Output as JSON")
    hier_coverage.add_argument("--suggest", action="store_true", help="Show gap suggestions")

    # ============== INSIGHTS COMMANDS ==============

    # health
    health_parser = subparsers.add_parser("health", help="Show project health score")
    health_parser.add_argument("document", nargs="?", help="Specific document to check")
    health_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show project statistics")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # incomplete
    incomplete_parser = subparsers.add_parser(
        "incomplete", help="Find incomplete content (TODO/TBD)"
    )
    incomplete_parser.add_argument("--high", action="store_true", help="Only high priority items")
    incomplete_parser.add_argument("--summary", action="store_true", help="Show summary only")
    incomplete_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # consistency
    consistency_parser = subparsers.add_parser("consistency", help="Check status consistency")
    consistency_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # parity
    parity_parser = subparsers.add_parser("parity", help="Translation parity matrix")
    parity_parser.add_argument("--primary", default="en", help="Primary language")
    parity_parser.add_argument("--lang", help="Show missing for specific language")
    parity_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # terms
    terms_parser = subparsers.add_parser("terms", help="Check terminology consistency")
    terms_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # duplicates
    dup_parser = subparsers.add_parser("duplicates", help="Find duplicate content")
    dup_parser.add_argument("--exact", action="store_true", help="Only exact duplicates")
    dup_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # velocity
    velocity_parser = subparsers.add_parser("velocity", help="Content velocity metrics")
    velocity_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    velocity_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # graph
    graph_parser = subparsers.add_parser("graph", help="Knowledge graph")
    graph_parser.add_argument(
        "--format", choices=["json", "dot", "cytoscape"], help="Export format"
    )
    graph_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # path
    path_parser = subparsers.add_parser("path", help="Reading paths")
    path_parser.add_argument("--persona", help="Generate persona-specific path")
    path_parser.add_argument("--complexity", action="store_true", help="Order by complexity")
    path_parser.add_argument("--lang", default="en", help="Language")
    path_parser.add_argument("--export", choices=["md"], help="Export format")
    path_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # ============== ADVANCED ANALYSIS COMMANDS ==============

    # analyze (parent command with subcommands)
    analyze_parser = subparsers.add_parser(
        "analyze", help="Advanced content analysis (semantic, LLM, knowledge graph)"
    )
    analyze_subparsers = analyze_parser.add_subparsers(dest="analyze_command")

    # analyze semantic
    sem_parser = analyze_subparsers.add_parser("semantic", help="Semantic similarity analysis")
    sem_parser.add_argument("--duplicates", action="store_true", help="Find near-duplicates")
    sem_parser.add_argument("--related", help="Find content related to document path")
    sem_parser.add_argument("--drift", action="store_true", help="Detect terminology drift")
    sem_parser.add_argument("--clusters", action="store_true", help="Cluster similar content")
    sem_parser.add_argument(
        "--contradictions", action="store_true", help="Find potential contradictions"
    )
    sem_parser.add_argument(
        "--translation-parity", action="store_true", help="Check translation semantic parity"
    )
    sem_parser.add_argument(
        "--threshold", type=float, default=0.85, help="Similarity threshold (0-1)"
    )
    sem_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze llm
    llm_parser = analyze_subparsers.add_parser("llm", help="LLM-powered quality evaluation")
    llm_parser.add_argument("document", nargs="?", help="Specific document to analyze")
    llm_parser.add_argument(
        "--completeness", action="store_true", help="Check content completeness"
    )
    llm_parser.add_argument("--prerequisites", action="store_true", help="Validate prerequisites")
    llm_parser.add_argument("--examples", action="store_true", help="Assess code examples")
    llm_parser.add_argument("--outdated", action="store_true", help="Detect outdated claims")
    llm_parser.add_argument("--review", action="store_true", help="Multi-agent review")
    llm_parser.add_argument(
        "--perspectives",
        help="Review perspectives (comma-separated: technical,user,editor,security,accessibility)",
    )
    llm_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze graph
    kg_parser = analyze_subparsers.add_parser("graph", help="Knowledge graph analysis")
    kg_parser.add_argument("--build", action="store_true", help="Build/refresh knowledge graph")
    kg_parser.add_argument("--orphans", action="store_true", help="Find orphan concepts")
    kg_parser.add_argument(
        "--prerequisites", action="store_true", help="Validate prerequisite chains"
    )
    kg_parser.add_argument("--path", help="Generate reading path from concept")
    kg_parser.add_argument("--metrics", action="store_true", help="Show graph metrics")
    kg_parser.add_argument("--export", choices=["json", "graphml", "gexf"], help="Export format")
    kg_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze norwegian (LIX readability)
    nor_parser = analyze_subparsers.add_parser(
        "norwegian", help="Norwegian LIX readability analysis"
    )
    nor_parser.add_argument("document", nargs="?", help="Specific document to analyze")
    nor_parser.add_argument(
        "--target",
        choices=["very_easy", "easy", "medium", "difficult", "very_difficult"],
        help="Target difficulty level",
    )
    nor_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze freshness (predictive)
    pred_parser = analyze_subparsers.add_parser("freshness", help="Predictive staleness detection")
    pred_parser.add_argument("--train", action="store_true", help="Train from git history")
    pred_parser.add_argument("--predict", action="store_true", help="Predict staleness risk")
    pred_parser.add_argument("--queue", action="store_true", help="Show prioritized review queue")
    pred_parser.add_argument("--days", type=int, default=90, help="History days to analyze")
    pred_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze codesync
    code_parser = analyze_subparsers.add_parser("codesync", help="Enhanced code-documentation sync")
    code_parser.add_argument("document", nargs="?", help="Specific document to check")
    code_parser.add_argument("--syntax", action="store_true", help="Validate code syntax")
    code_parser.add_argument("--deprecated", action="store_true", help="Find deprecated patterns")
    code_parser.add_argument("--api-refs", action="store_true", help="Check API references")
    code_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze advanced
    adv_parser = analyze_subparsers.add_parser(
        "advanced", help="Advanced analysis (audience drift, questions, style)"
    )
    adv_parser.add_argument("document", nargs="?", help="Specific document to analyze")
    adv_parser.add_argument("--audience-drift", action="store_true", help="Detect audience drift")
    adv_parser.add_argument("--questions", action="store_true", help="Question coverage analysis")
    adv_parser.add_argument("--crossrefs", action="store_true", help="Cross-reference density")
    adv_parser.add_argument("--structure", action="store_true", help="Document structure analysis")
    adv_parser.add_argument("--style", action="store_true", help="Style consistency check")
    adv_parser.add_argument("--full", action="store_true", help="Run all advanced analyses")
    adv_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "status": cmd_status,
        "brand": cmd_brand,
        "build": cmd_build,
        "publish": cmd_publish,
        "release": cmd_release,
        "quality": cmd_quality,
        "stale": cmd_stale,
        "cache": cmd_cache,
        "init": cmd_init,
        "search": cmd_search,
        "validate": cmd_validate,
        "pack": cmd_pack,
        "index": cmd_index,
        "translation": cmd_translation,
        "dashboard": cmd_dashboard,
        "provenance": cmd_provenance,
        "integrity": cmd_integrity,
        "notes": cmd_notes,
        "readability": cmd_readability,
        "gaps": cmd_gaps,
        "links": cmd_links,
        "security": cmd_security,
        "changelog": cmd_changelog,
        "demos": cmd_demos,
        "freshness": cmd_freshness,
        "hierarchy": cmd_hierarchy,
        # Insights commands
        "health": cmd_health,
        "stats": cmd_stats,
        "incomplete": cmd_incomplete,
        "consistency": cmd_consistency,
        "parity": cmd_parity,
        "terms": cmd_terms,
        "duplicates": cmd_duplicates,
        "velocity": cmd_velocity,
        "graph": cmd_graph,
        "path": cmd_path,
        # Advanced analysis
        "analyze": cmd_analyze,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


__all__ = ["main"]
