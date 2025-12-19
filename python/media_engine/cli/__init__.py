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
"""

import argparse
import sys

from .commands import (
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
    cmd_incomplete,
    cmd_index,
    cmd_init,
    cmd_integrity,
    cmd_links,
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
    release_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be copied"
    )
    release_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing files"
    )
    release_parser.add_argument("--lang", "-l", help="Only release specific language")

    # quality
    quality_parser = subparsers.add_parser("quality", help="Run quality checks")
    quality_parser.add_argument("--json", action="store_true", help="Output as JSON")

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "status": cmd_status,
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
        "readability": cmd_readability,
        "gaps": cmd_gaps,
        "links": cmd_links,
        "security": cmd_security,
        "changelog": cmd_changelog,
        "demos": cmd_demos,
        "freshness": cmd_freshness,
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
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


__all__ = ["main"]
