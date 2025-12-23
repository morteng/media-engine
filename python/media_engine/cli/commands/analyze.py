"""
Advanced Analysis CLI Commands

New analysis commands for semantic, LLM, knowledge graph, and other advanced features.
"""

import json
from pathlib import Path


def cmd_analyze(args):
    """Handle analyze subcommands."""
    from ...core import find_project

    subcmd = args.analyze_command

    if subcmd == "semantic":
        _cmd_semantic(args, find_project())
    elif subcmd == "llm":
        _cmd_llm(args, find_project())
    elif subcmd == "graph":
        _cmd_graph(args, find_project())
    elif subcmd == "norwegian":
        _cmd_norwegian(args, find_project())
    elif subcmd == "freshness":
        _cmd_freshness(args, find_project())
    elif subcmd == "codesync":
        _cmd_codesync(args, find_project())
    elif subcmd == "advanced":
        _cmd_advanced(args, find_project())
    else:
        print(
            "Unknown analyze command. Use: semantic, llm, graph, norwegian, freshness, codesync, advanced"
        )


def _cmd_semantic(args, project):
    """Run semantic analysis."""
    from ...semantic import HAS_SENTENCE_TRANSFORMERS, SemanticAnalyzer

    analyzer = SemanticAnalyzer(project)

    if not HAS_SENTENCE_TRANSFORMERS:
        print("Note: sentence-transformers not installed, using TF-IDF fallback")
        print("For better results: pip install sentence-transformers\n")

    results = {}
    threshold = getattr(args, "threshold", 0.85)

    # Determine what to run
    run_all = not any(
        [
            getattr(args, "duplicates", False),
            getattr(args, "related", False),
            getattr(args, "terminology", False),
            getattr(args, "contradictions", False),
            getattr(args, "clusters", False),
        ]
    )

    if getattr(args, "duplicates", False) or run_all:
        print("Finding near-duplicates...")
        dupes = analyzer.find_near_duplicates(threshold=threshold)
        results["near_duplicates"] = [d.to_dict() for d in dupes]

        if not getattr(args, "json", False):
            print(f"\nNear-duplicates found: {len(dupes)}")
            for d in dupes[:5]:
                print(f"  {d.similarity:.2f}: {d.doc1} <-> {d.doc2}")

    if getattr(args, "related", False) or run_all:
        print("Finding related content...")
        rel = analyzer.find_related_content(threshold=0.5)
        results["related_content"] = [r.to_dict() for r in rel]

        if not getattr(args, "json", False):
            print(f"\nRelated pairs found: {len(rel)}")
            for r in rel[:5]:
                print(f"  {r.similarity:.2f}: {r.doc1} <-> {r.doc2}")

    if getattr(args, "terminology", False) or run_all:
        print("Detecting terminology drift...")
        drift = analyzer.detect_terminology_drift()
        results["terminology_drift"] = [t.to_dict() for t in drift]

        if not getattr(args, "json", False):
            print(f"\nTerminology issues found: {len(drift)}")
            for t in drift[:5]:
                print(f"  '{t.term1}' vs '{t.term2}' (similarity: {t.similarity:.2f})")

    if getattr(args, "contradictions", False) or run_all:
        print("Finding contradictions...")
        contras = analyzer.find_contradictions()
        results["contradictions"] = [c.to_dict() for c in contras]

        if not getattr(args, "json", False):
            print(f"\nPotential contradictions: {len(contras)}")
            for c in contras[:3]:
                print(f"  Topic: {c.topic}")
                print(f"    {c.doc1}: {c.claim1[:80]}...")
                print(f"    {c.doc2}: {c.claim2[:80]}...")

    if getattr(args, "clusters", False) or run_all:
        print("Clustering content...")
        clust = analyzer.cluster_content()
        results["clusters"] = [c.to_dict() for c in clust]

        if not getattr(args, "json", False):
            print(f"\nClusters found: {len(clust)}")
            for c in clust[:5]:
                print(f"  {c.topic}: {len(c.documents)} documents")

    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))


def _cmd_llm(args, project):
    """Run LLM analysis."""
    from ...llm_quality import LLMQualityEvaluator

    provider = getattr(args, "provider", "anthropic")
    model = getattr(args, "model", None)
    document = getattr(args, "document", None)

    try:
        evaluator = LLMQualityEvaluator(project, provider=provider, model=model)
    except Exception as e:
        print(f"Error initializing LLM client: {e}")
        print("Ensure API key is set (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        return

    if document:
        doc_path = Path(document)
        print(f"Analyzing {doc_path}...")

        run_all = not any(
            [
                getattr(args, "completeness", False),
                getattr(args, "prerequisites", False),
                getattr(args, "examples", False),
                getattr(args, "outdated", False),
                getattr(args, "agents", False),
            ]
        )

        results = {}

        if getattr(args, "completeness", False) or run_all:
            print("Checking completeness...")
            comp = evaluator.evaluate_completeness(doc_path)
            results["completeness"] = comp.to_dict()

            if not getattr(args, "json", False):
                print(f"  Coverage: {comp.coverage_score}%")

        if getattr(args, "prerequisites", False) or run_all:
            print("Checking prerequisites...")
            prereq = evaluator.check_prerequisites(doc_path)
            results["prerequisites"] = prereq.to_dict()

            if not getattr(args, "json", False):
                if prereq.missing_prerequisites:
                    print(f"  Missing: {', '.join(prereq.missing_prerequisites[:3])}")
                else:
                    print("  All prerequisites covered")

        if getattr(args, "examples", False) or run_all:
            print("Assessing examples...")
            ex = evaluator.assess_examples(doc_path)
            results["examples"] = ex.to_dict()

            if not getattr(args, "json", False):
                print(f"  Examples: {ex.total_examples}, Quality: {ex.quality_score}%")

        if getattr(args, "outdated", False) or run_all:
            print("Detecting outdated claims...")
            out = evaluator.detect_outdated_claims(doc_path)
            results["outdated"] = out.to_dict()

            if not getattr(args, "json", False):
                print(f"  Outdated claims: {len(out.outdated_claims)}")

        if getattr(args, "agents", False):
            print("Running multi-agent review...")
            reviews = evaluator.multi_agent_review(doc_path)
            results["agent_reviews"] = [r.to_dict() for r in reviews]

            if not getattr(args, "json", False):
                for r in reviews:
                    print(f"  {r.perspective.value}: {r.overall_score}/100")

        if getattr(args, "json", False):
            print(json.dumps(results, indent=2))
    else:
        print("Analyzing project (limited to 10 documents)...")
        report = evaluator.evaluate_project(max_documents=10)

        if getattr(args, "json", False):
            print(json.dumps(report, indent=2))
        else:
            print(f"Documents evaluated: {report['summary']['documents_evaluated']}")
            print(f"Average score: {report['summary']['average_score']}")
            print(f"Total findings: {report['summary']['total_findings']}")


def _cmd_graph(args, project):
    """Run knowledge graph analysis."""
    from ...knowledge import HAS_NETWORKX, KnowledgeGraph

    if not HAS_NETWORKX:
        print("Error: networkx required: pip install networkx")
        return

    graph = KnowledgeGraph(project)

    print("Building knowledge graph...")
    graph.build()

    results = {}
    run_all = not any(
        [
            getattr(args, "orphans", False),
            getattr(args, "prerequisites", False),
            getattr(args, "paths", False),
            getattr(args, "metrics", False),
        ]
    )

    if getattr(args, "metrics", False) or run_all:
        m = graph.compute_metrics()
        results["metrics"] = m.to_dict()

        if not getattr(args, "json", False):
            print("\nGraph Metrics:")
            print(f"  Nodes: {m.total_nodes} ({m.document_count} docs, {m.concept_count} concepts)")
            print(f"  Edges: {m.total_edges}")
            print(f"  Avg connections/doc: {m.avg_connections_per_doc:.1f}")

    if getattr(args, "orphans", False) or run_all:
        orph = graph.find_orphan_concepts()
        results["orphan_concepts"] = [o.to_dict() for o in orph]

        if not getattr(args, "json", False):
            print(f"\nOrphan Concepts: {len(orph)}")
            for o in orph[:5]:
                print(f"  {o.concept}: {len(o.mentions)} mentions")

    if getattr(args, "prerequisites", False) or run_all:
        issues = graph.validate_prerequisites()
        results["prerequisite_issues"] = [i.to_dict() for i in issues]

        if not getattr(args, "json", False):
            print(f"\nPrerequisite Issues: {len(issues)}")
            for i in issues[:5]:
                print(f"  {i.document}: missing '{i.missing_prereq}'")

    if getattr(args, "paths", False) or run_all:
        reading_paths = graph.generate_reading_paths()
        results["reading_paths"] = [p.to_dict() for p in reading_paths]

        if not getattr(args, "json", False):
            print(f"\nReading Paths: {len(reading_paths)}")
            for p in reading_paths[:3]:
                print(f"  {p.title}: {len(p.documents)} docs, ~{p.estimated_time_minutes:.0f} min")

    export_path = getattr(args, "export", None)
    if export_path:
        graph.export_graphml(Path(export_path))
        print(f"\nExported to {export_path}")

    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))


def _cmd_norwegian(args, project):
    """Run Norwegian readability analysis."""
    from ...readability.norwegian import NorwegianReadabilityChecker, NorwegianReadabilityLevel

    target = getattr(args, "target", "medium")
    language = getattr(args, "language", "no")

    level_map = {
        "very_easy": NorwegianReadabilityLevel.VERY_EASY,
        "easy": NorwegianReadabilityLevel.EASY,
        "medium": NorwegianReadabilityLevel.MEDIUM,
        "difficult": NorwegianReadabilityLevel.DIFFICULT,
    }

    checker = NorwegianReadabilityChecker(
        target_level=level_map.get(target, NorwegianReadabilityLevel.MEDIUM)
    )
    report = checker.check_project(project, language=language)

    if "error" in report:
        print(f"Error: {report['error']}")
        return

    if getattr(args, "json", False):
        print(json.dumps(report, indent=2))
    else:
        summary = report["summary"]
        print(f"Norwegian Readability Analysis ({language})")
        print(f"  Target: {target} (LIX < {checker.target_lix})")
        print(f"  Documents: {summary['total_documents']}")
        print(f"  Pass rate: {summary['pass_rate']}%")
        print(f"  Average LIX: {summary['average_lix']}")
        print(f"  Total words: {summary['total_word_count']}")

        failing = [d for d in report["documents"] if not d["passes_target"]]
        if failing:
            print(f"\nDocuments exceeding target ({len(failing)}):")
            for d in failing[:5]:
                print(f"  {d['file']}: LIX {d['lix']:.1f} ({d['lix_level']})")


def _cmd_freshness(args, project):
    """Run predictive freshness analysis."""
    from ...freshness.predictive import FreshnessPredictor

    predictor = FreshnessPredictor(project)

    print("Learning from history...")
    predictor.train()

    results = {}
    run_all = not any(
        [
            getattr(args, "predict", False),
            getattr(args, "priority", False),
            getattr(args, "patterns", False),
        ]
    )

    if getattr(args, "patterns", False) or run_all:
        results["patterns"] = [p.to_dict() for p in predictor._patterns.values()]

        if not getattr(args, "json", False):
            print("\nLearned Patterns:")
            for p in predictor._patterns.values():
                print(f"  {p.document_type}: avg update every {p.update_frequency_days:.0f} days")

    if getattr(args, "priority", False) or run_all:
        queue = predictor.get_review_priority(10)
        results["review_priority"] = queue

        if not getattr(args, "json", False):
            print("\nReview Priority Queue:")
            for item in queue[:10]:
                risk = item["risk"]
                level = item["risk_level"]
                print(f"  [{level.upper():8}] {item['path']} (risk: {risk:.2f})")

    if getattr(args, "predict", False) or run_all:
        report = predictor.generate_report()
        results["high_risk_count"] = report.high_risk_count

        if not getattr(args, "json", False):
            print("\nPredictions Summary:")
            print(f"  Documents analyzed: {len(report.predictions)}")
            print(f"  High risk: {report.high_risk_count}")

    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))


def _cmd_codesync(args, project):
    """Run code sync analysis."""
    from ...codesync import EnhancedCodeSyncChecker

    checker = EnhancedCodeSyncChecker(project)
    document = getattr(args, "document", None)

    if document:
        doc_path = Path(document)
        report = checker.check_document(doc_path)

        if getattr(args, "json", False):
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"Code Sync Check: {doc_path}")
            print(f"  Examples: {report.total_examples}")
            print(f"  Valid: {report.valid_examples} ({report.validation_rate:.1f}%)")
            print(f"  Needs review: {'Yes' if report.needs_review else 'No'}")

            if report.issues:
                print(f"\nIssues ({len(report.issues)}):")
                for issue in report.issues:
                    if getattr(args, "errors_only", False) and issue.severity != "error":
                        continue
                    print(f"  [{issue.severity.upper()}] Line {issue.line_number}: {issue.message}")
    else:
        summary = checker.generate_summary()

        if getattr(args, "json", False):
            print(json.dumps(summary, indent=2))
        else:
            s = summary["summary"]
            print("Code Sync Summary:")
            print(f"  Documents: {s['documents_checked']}")
            print(f"  Examples: {s['total_examples']}")
            print(f"  Valid: {s['valid_examples']} ({s['validation_rate']}%)")
            print(f"  Errors: {s['error_count']}")
            print(f"  Warnings: {s['warning_count']}")


def _cmd_advanced(args, project):
    """Run advanced analysis."""
    from ...advanced import AdvancedAnalyzer

    analyzer = AdvancedAnalyzer(project)

    print("Running advanced analysis...")
    report = analyzer.analyze_project()

    run_all = not any(
        [
            getattr(args, "drift", False),
            getattr(args, "questions", False),
            getattr(args, "crossref", False),
            getattr(args, "structure", False),
            getattr(args, "style", False),
        ]
    )

    results = {}

    if getattr(args, "drift", False) or run_all:
        results["audience_drift"] = [a.to_dict() for a in report.audience_drift]

        if not getattr(args, "json", False):
            print(f"\nAudience Drift: {len(report.audience_drift)} documents with drift")
            for d in report.audience_drift[:3]:
                print(f"  {d.document}: {d.drift_direction} ({d.drift_magnitude:.1f} grades)")

    if getattr(args, "questions", False) or run_all:
        results["question_coverage"] = [q.to_dict() for q in report.question_coverage]

        if not getattr(args, "json", False):
            faq_needed = [q for q in report.question_coverage if q.faq_potential]
            print(f"\nQuestion Coverage: {len(faq_needed)} docs could use FAQ section")

    if getattr(args, "crossref", False) or run_all:
        results["cross_references"] = [c.to_dict() for c in report.cross_reference_metrics]

        if not getattr(args, "json", False):
            orphans = [c for c in report.cross_reference_metrics if c.orphan_score > 0.7]
            print(f"\nCross-References: {len(orphans)} isolated documents")

    if getattr(args, "structure", False) or run_all:
        results["structure"] = [s.to_dict() for s in report.structure_analyses]

        if not getattr(args, "json", False):
            issues = [s for s in report.structure_analyses if s.issues]
            print(f"\nStructure Issues: {len(issues)} documents with issues")

    if getattr(args, "style", False) or run_all:
        results["style"] = [s.to_dict() for s in report.style_consistency]

        if not getattr(args, "json", False):
            mixed = [s for s in report.style_consistency if s.formality_level == "mixed"]
            print(f"\nStyle Consistency: {len(mixed)} documents with mixed formality")

    results["overall_quality_score"] = report.overall_quality_score

    if not getattr(args, "json", False):
        print(f"\nOverall Quality Score: {report.overall_quality_score:.1f}/100")

    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))
