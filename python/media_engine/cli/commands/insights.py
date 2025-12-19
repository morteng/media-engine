"""CLI commands for project insights."""

import json
import sys

from ...core.project import find_project


def cmd_health(args):
    """Show project health score."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import HealthScorer

    scorer = HealthScorer(project)

    if hasattr(args, "document") and args.document:
        # Score single document
        from pathlib import Path

        health = scorer.score_document(Path(args.document))
        if args.json:
            print(json.dumps(health.to_dict(), indent=2))
        else:
            print(f"\nDocument Health: {args.document}")
            print("=" * 50)
            print(f"Score: {health.overall}/100 (Grade: {health.grade})")
            print(f"Status: {health.status}")
            print("\nComponents:")
            for comp, score in health.components.items():
                bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                print(f"  {comp:<15} {bar} {score:.0f}")
            if health.issues:
                print(f"\nIssues ({len(health.issues)}):")
                for issue in health.issues[:5]:
                    print(f"  [{issue.severity}] {issue.message}")
            if health.recommendations:
                print("\nRecommendations:")
                for rec in health.recommendations[:3]:
                    print(f"  • {rec}")
    else:
        # Score entire project
        health = scorer.score_project()
        if args.json:
            print(json.dumps(health.to_dict(), indent=2))
        else:
            print("\n╔══════════════════════════════════════════════════╗")
            print(f"║  PROJECT HEALTH: {health.overall:.0f}/100 (Grade: {health.grade})".ljust(51) + "║")
            print(f"║  Status: {health.status}".ljust(51) + "║")
            print("╚══════════════════════════════════════════════════╝")
            print("\nComponent Breakdown:")
            for comp, score in health.components.items():
                bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                status = "✓" if score >= 80 else "⚠" if score >= 50 else "✗"
                print(f"  {comp:<15} {bar} {score:.0f} {status}")
            if health.critical_documents:
                print(f"\n⚠ Critical Documents ({len(health.critical_documents)}):")
                for doc in health.critical_documents[:5]:
                    print(f"  • {doc}")
            if health.recommendations:
                print("\nTop Recommendations:")
                for rec in health.recommendations[:3]:
                    print(f"  • {rec}")


def cmd_stats(args):
    """Show project statistics."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import StatisticsCollector

    collector = StatisticsCollector(project)
    stats = collector.collect()

    if args.json:
        print(json.dumps(stats.to_dict(), indent=2))
    else:
        print("\n╔══════════════════════════════════════════════════╗")
        print("║  PROJECT STATISTICS                               ║")
        print("╠══════════════════════════════════════════════════╣")

        # Content
        print(f"║  📄 Documents: {stats.content.total_documents}".ljust(51) + "║")
        print(f"║  📝 Words: {stats.content.total_words:,}".ljust(51) + "║")

        # By language
        if stats.content.documents_by_language:
            langs = ", ".join(f"{k}: {v}" for k, v in stats.content.documents_by_language.items())
            print(f"║  🌐 Languages: {langs}".ljust(51) + "║")

        print("╠══════════════════════════════════════════════════╣")

        # Status
        print("║  Status Breakdown:".ljust(51) + "║")
        for status, count in stats.status.by_status.items():
            print(f"║    {status}: {count}".ljust(51) + "║")

        print("╠══════════════════════════════════════════════════╣")

        # Activity
        print("║  Recent Activity:".ljust(51) + "║")
        print(f"║    Modified this week: {stats.activity.documents_modified_week}".ljust(51) + "║")
        print(f"║    Modified this month: {stats.activity.documents_modified_month}".ljust(51) + "║")
        if stats.activity.contributors:
            print(f"║    Contributors: {', '.join(stats.activity.contributors[:3])}".ljust(51) + "║")

        print("╚══════════════════════════════════════════════════╝")


def cmd_incomplete(args):
    """Find incomplete content (TODO/TBD/FIXME)."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import IncompleteTracker

    tracker = IncompleteTracker(project)

    if hasattr(args, "summary") and args.summary:
        summary = tracker.get_summary()
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("\nIncomplete Content Summary")
            print("=" * 40)
            print(f"Total items: {summary['total']}")
            print(f"Debt score: {summary['debt_score']:.1f}/100")
            print("\nBy priority:")
            for priority, count in summary["by_priority"].items():
                print(f"  {priority}: {count}")
            print("\nBy type:")
            for marker_type, count in summary["by_type"].items():
                print(f"  {marker_type}: {count}")
    else:
        items = tracker.scan_project()

        if hasattr(args, "high") and args.high:
            items = [i for i in items if i.priority == "high"]

        if args.json:
            print(json.dumps([i.to_dict() for i in items], indent=2))
        else:
            if not items:
                print("\n✓ No incomplete content found!")
            else:
                print(f"\nIncomplete Content ({len(items)} items)")
                print("=" * 60)

                current_doc = None
                for item in items:
                    if str(item.document) != current_doc:
                        current_doc = str(item.document)
                        print(f"\n{current_doc}")

                    priority_icon = "🔴" if item.priority == "high" else "🟡" if item.priority == "medium" else "⚪"
                    print(f"  {priority_icon} Line {item.line_number}: {item.content[:60]}")


def cmd_consistency(args):
    """Check status consistency."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import ConsistencyChecker

    checker = ConsistencyChecker(project)
    issues = checker.check_project()

    if args.json:
        print(json.dumps([i.to_dict() for i in issues], indent=2))
    else:
        if not issues:
            print("\n✓ No consistency issues found!")
        else:
            print(f"\nConsistency Issues ({len(issues)})")
            print("=" * 60)

            for issue in issues:
                print(f"\n📄 {issue.document}")
                print(f"   Type: {issue.issue_type}")
                print(f"   Declared: {issue.declared} → Detected: {issue.detected}")
                print(f"   Confidence: {issue.confidence:.0%}")
                print(f"   Recommendation: {issue.recommendation}")


def cmd_parity(args):
    """Show translation parity matrix."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import ParityAnalyzer

    primary = args.primary if hasattr(args, "primary") and args.primary else "en"
    analyzer = ParityAnalyzer(project, primary_language=primary)
    report = analyzer.analyze()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("\nTranslation Parity Matrix")
        print("=" * 60)
        print(report.format_table())

        if hasattr(args, "lang") and args.lang:
            missing = analyzer.get_missing_for_language(args.lang)
            if missing:
                print(f"\nMissing translations for '{args.lang}' ({len(missing)}):")
                for path in missing[:10]:
                    print(f"  • {path}")
                if len(missing) > 10:
                    print(f"  ... and {len(missing) - 10} more")


def cmd_terms(args):
    """Check terminology consistency."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import TerminologyChecker

    checker = TerminologyChecker(project)
    issues = checker.find_inconsistencies()

    if args.json:
        print(json.dumps([i.to_dict() for i in issues], indent=2))
    else:
        if not issues:
            print("\n✓ No terminology inconsistencies found!")
        else:
            print(f"\nTerminology Issues ({len(issues)})")
            print("=" * 60)

            for issue in issues:
                terms = ", ".join(issue.term_group)
                print(f"\n[{issue.severity}] {issue.issue_type}: {terms}")
                print(f"  Recommended: {issue.recommended}")
                print(f"  Occurrences: {issue.total_occurrences}")


def cmd_duplicates(args):
    """Find duplicate content."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import DuplicateDetector

    detector = DuplicateDetector(project)

    if hasattr(args, "exact") and args.exact:
        matches = detector.find_exact_duplicates()
    else:
        report = detector.generate_report()
        matches = report.exact_duplicates + report.similar_content

    if args.json:
        print(json.dumps([m.to_dict() for m in matches], indent=2))
    else:
        if not matches:
            print("\n✓ No duplicate content found!")
        else:
            print(f"\nDuplicate Content ({len(matches)} matches)")
            print("=" * 60)

            for match in matches:
                print(f"\n[{match.match_type}] Similarity: {match.similarity:.0%}")
                for loc in match.locations:
                    print(f"  • {loc.document}:{loc.start_line}-{loc.end_line}")
                print(f"  Preview: {match.content_preview[:80]}...")


def cmd_velocity(args):
    """Show content velocity metrics."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import VelocityTracker

    days = args.days if hasattr(args, "days") and args.days else 30
    tracker = VelocityTracker(project)
    metrics = tracker.get_metrics(days)

    if args.json:
        print(json.dumps(metrics.to_dict(), indent=2))
    else:
        print(f"\nContent Velocity (Last {days} Days)")
        print("=" * 50)
        print(f"Commits: {metrics.commits}")
        print(f"Lines added: {metrics.lines_added}")
        print(f"Lines removed: {metrics.lines_removed}")
        print(f"Documents modified: {metrics.documents_modified}")

        if metrics.top_contributors:
            print("\nTop Contributors:")
            for contrib in metrics.top_contributors[:5]:
                print(f"  • {contrib.name}: {contrib.commits} commits")

        if metrics.area_breakdown:
            print("\nArea Breakdown:")
            for area, area_metrics in list(metrics.area_breakdown.items())[:5]:
                trend_icon = "↑" if area_metrics.trend == "up" else "↓" if area_metrics.trend == "down" else "→"
                print(f"  {area}: {area_metrics.commits} changes {trend_icon}")


def cmd_graph(args):
    """Generate knowledge graph."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import KnowledgeGraph

    graph = KnowledgeGraph(project)
    nodes, edges = graph.build_graph()

    if hasattr(args, "format") and args.format == "dot":
        print(graph.export_dot())
    elif hasattr(args, "format") and args.format == "cytoscape":
        print(json.dumps(graph.export_cytoscape(), indent=2))
    elif args.json:
        print(json.dumps(graph.export_json(), indent=2))
    else:
        print("\nKnowledge Graph")
        print("=" * 50)
        print(f"Nodes: {len(nodes)}")
        print(f"Edges: {len(edges)}")

        hubs = graph.find_hubs()
        if hubs:
            print(f"\nHub Documents ({len(hubs)}):")
            for hub in hubs[:5]:
                print(f"  • {hub.title} ({hub.connections} connections)")

        orphans = graph.find_orphans()
        if orphans:
            print(f"\nOrphan Documents ({len(orphans)}):")
            for orphan in orphans[:5]:
                print(f"  • {orphan.title}")


def cmd_path(args):
    """Generate reading paths."""
    try:
        project = find_project()
    except FileNotFoundError:
        print("Error: No project found. Run from a project directory.")
        sys.exit(1)

    from ...insights import PathGenerator

    lang = args.lang if hasattr(args, "lang") and args.lang else "en"
    generator = PathGenerator(project, language=lang)

    if hasattr(args, "persona") and args.persona:
        path = generator.generate_persona_path(args.persona)
    elif hasattr(args, "complexity") and args.complexity:
        path = generator.generate_complexity_path()
    else:
        path = generator.generate_dependency_path()

    if hasattr(args, "export") and args.export == "md":
        print(path.format_markdown())
    elif args.json:
        print(json.dumps(path.to_dict(), indent=2))
    else:
        print(f"\n{path.name}")
        print("=" * 50)
        print(path.description)
        print(f"\nEstimated time: {path.estimated_time} minutes")
        print("\nReading Order:")
        for node in path.documents:
            print(f"  {node.order}. {node.title} ({node.estimated_time} min)")
