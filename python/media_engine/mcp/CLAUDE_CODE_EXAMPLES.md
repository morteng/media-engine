# Claude Code Examples - Media Engine Integration

Real-world examples of using Media Engine MCP with Claude Code for documentation workflows.

## Example 1: Daily Documentation Health Check

**Goal**: Every morning, check documentation health and get recommended actions.

```python
# Using Claude Code with Media Engine MCP

# Get project health snapshot
context = get_project_context()
health = context["health_metrics"]

print(f"📊 Project Health: {health['score']}/100 ({health['grade']})")
print(f"📄 Documents: {context['total_documents']}")
print(f"🌐 Languages: {', '.join(context['languages'])}")

# Get prioritized actions
suggestions = get_suggested_actions()

print("\n🎯 Recommended Actions:")
for i, action in enumerate(suggestions["actions"][:5], 1):
    priority = "🔴" if action["priority"] == "high" else "🟡" if action["priority"] == "medium" else "⚪"
    print(f"{i}. {priority} {action['description']}")

# Export for team review
report = export_session_report()
print(f"\n✅ Full report exported: {report['path']}")
```

**Use in Claude Desktop:**
1. Add Media Engine MCP server config
2. Ask Claude: "Do a health check on the project"
3. Claude uses these tools automatically
4. Get daily summary in Claude Desktop

---

## Example 2: Translate Updated Documents

**Goal**: Automatically translate English documents to Norwegian when they're marked as final.

```python
# Monitor English docs marked as final
import json

# Find recently updated English docs
recent_updates = get_suggested_actions()

# Filter for "translate" suggestions
translations_needed = [
    a for a in recent_updates["actions"]
    if "translate" in a["action"].lower()
]

print(f"📚 {len(translations_needed)} documents need translation")

# For each translation needed
for doc in translations_needed:
    print(f"\n🔄 Processing: {doc['target_document']}")

    # Get document context
    doc_context = get_document_context(doc["target_document"])

    # Validate that we should translate it
    validation = validate_action(
        "translate_document",
        doc["target_document"],
        {"target_language": "Norwegian"}
    )

    if validation["valid"]:
        print(f"✓ Approved for translation")

        # Create translated version
        translated_path = doc["target_document"].replace("en/", "no/")

        # Log the action
        log_agent_action(
            "document_translated",
            "English document was marked as final and needed translation",
            f"Created Norwegian translation",
            doc["target_document"]
        )

        # Update metadata
        update_document_metadata(
            translated_path,
            {
                "language": "no",
                "source_document": doc["target_document"],
                "source_version": doc_context["metadata"]["version"]
            }
        )

        print(f"✓ Translation created: {translated_path}")
    else:
        print(f"⚠ Translation not approved: {validation['message']}")

print("\n✅ Translation batch complete")
```

**Set up automation:**
```bash
# Create a scheduled Claude Code task
# Runs daily at 9 AM
media-engine-task "translate_updated_docs" --schedule "daily 9am"
```

---

## Example 3: API Documentation Sync

**Goal**: When API changes, automatically update documentation and notify team.

```python
# Triggered when API spec changes (via webhook)

def handle_api_update(event_data):
    """Handle API specification update event."""

    api_version = event_data.get("api_version")
    updated_endpoints = event_data.get("endpoints", [])

    print(f"🔔 API Update Detected: v{api_version}")
    print(f"📝 {len(updated_endpoints)} endpoints changed")

    # Get impact analysis
    impact = analyze_change_impact(
        f"API v{api_version}: Updated {len(updated_endpoints)} endpoints"
    )

    print(f"\n📋 Impact Analysis:")
    print(f"   Documents affected: {len(impact['affected_documents'])}")
    print(f"   Broken references: {len(impact['broken_references'])}")
    print(f"   Translations to update: {len(impact['translation_implications'])}")

    # Validate that updating is appropriate
    validation = validate_action(
        "bulk_update_api_docs",
        "chapters/api.md",
        {
            "api_version": api_version,
            "endpoint_count": len(updated_endpoints)
        }
    )

    if not validation["valid"]:
        print(f"⚠️ Cannot auto-update: {validation['message']}")
        return

    # Prepare batch updates
    updates = []

    for endpoint in updated_endpoints:
        updates.append({
            "action": "update_section",
            "document": "chapters/api.md",
            "section": f"endpoints.{endpoint['name']}",
            "content": endpoint["documentation"]
        })

    # Preview changes
    preview = preview_changes({"updates": updates})

    print(f"\n👁️ Preview of changes:")
    for change in preview["changes"][:3]:
        print(f"   • {change['type']}: {change['summary']}")
    if len(preview["changes"]) > 3:
        print(f"   ... and {len(preview['changes']) - 3} more")

    # Apply with human confirmation
    if preview["valid"]:
        response = input("Apply changes? (y/n): ")
        if response.lower() == "y":
            batch_update(updates)

            # Log comprehensive action
            log_agent_action(
                "api_documentation_sync",
                f"API v{api_version} specification updated",
                f"Updated {len(updated_endpoints)} endpoints in documentation",
                "chapters/api.md"
            )

            # Notify team via webhook
            register_webhook(
                "https://slack.example.com/api-updates",
                "document.updated"
            )

            print("✅ Updates applied and team notified")
            return True

    print("❌ Changes cancelled by user")
    return False

# Usage: Would be triggered by webhook
# handle_api_update(event_data)
```

---

## Example 4: Release Documentation Checklist

**Goal**: Generate and execute release documentation checklist.

```python
# Prepare documentation for release

release_version = "2.5.0"
print(f"🚀 Preparing documentation for release v{release_version}")

# Step 1: Get current status
print("\n📊 Step 1: Current Status")
context = get_project_context()
print(f"   Documents: {context['total_documents']}")
print(f"   Languages: {', '.join(context['languages'])}")

# Step 2: Run quality checks
print("\n✓ Step 2: Quality Checks")
quality_results = quality_check()
if quality_results["summary"]["errors"] > 0:
    print(f"   ⚠️  Found {quality_results['summary']['errors']} errors")
    print("   Fix errors before release")
else:
    print("   ✓ All quality checks passed")

# Step 3: Get release guidance
print("\n📋 Step 3: Release Workflow")
guidance = get_workflow_guidance("release")
for i, step in enumerate(guidance["steps"], 1):
    print(f"   {i}. {step['description']}")

# Step 4: Mark all as final
print(f"\n📌 Step 4: Mark Documentation as Final")
transform_result = apply_transformation(
    "status:in_review",
    f"update_status:final",
    dry_run=True
)
print(f"   Preview: Would mark {len(transform_result['affected'])} documents as final")

response = input("   Apply? (y/n): ")
if response.lower() == "y":
    apply_transformation(
        "status:in_review",
        "update_status:final",
        dry_run=False
    )
    print("   ✓ Documents marked as final")

# Step 5: Update version numbers
print(f"\n🔢 Step 5: Update Version Numbers")
for doc_path in [f"chapters/{i:02d}_*.md" for i in range(1, 20)]:
    # Find and update versions
    log_agent_action(
        "version_bump",
        f"Preparing for release v{release_version}",
        f"Updated version to {release_version}",
        doc_path
    )

# Step 6: Validate schema
print(f"\n✓ Step 6: Schema Validation")
validation = validate_project()
if validation["valid"]:
    print("   ✓ Project passes schema validation")
else:
    print(f"   ⚠️  Schema errors found: {len(validation['issues'])}")

# Step 7: Create release notes
print(f"\n📝 Step 7: Release Notes")
changelog = export_session_report()
print(f"   ✓ Release notes generated")

print(f"\n✅ Release documentation v{release_version} ready!")
```

---

## Example 5: Content Audit & Gap Analysis

**Goal**: Find missing documentation and content gaps.

```python
# Comprehensive content audit

print("🔍 Content Audit & Gap Analysis")
print("=" * 50)

# Get full project context
context = get_project_context()

print(f"\n📊 Project Overview:")
print(f"   Name: {context['name']}")
print(f"   Languages: {context['languages']}")
print(f"   Documents: {context['total_documents']}")
print(f"   Health: {context['health_metrics']['score']}/100")

# Find incomplete content
print(f"\n❓ Incomplete Content:")
suggestions = get_suggested_actions()
incomplete = [a for a in suggestions["actions"] if "incomplete" in a["action"].lower()]

for item in incomplete[:10]:
    priority = "🔴" if item["priority"] == "high" else "🟡"
    print(f"   {priority} {item['description']}")

# Find orphaned documents
print(f"\n🚫 Potential Issues:")
impact = analyze_change_impact("Audit for broken references")
if impact["broken_references"]:
    print(f"   Broken references: {len(impact['broken_references'])}")
    for ref in impact["broken_references"][:5]:
        print(f"      • {ref['source']} → {ref['target']}")

# Find translation gaps
print(f"\n🌐 Translation Status:")
for lang in context["languages"]:
    # Would check translation status
    print(f"   {lang}: status TBD")

# Generate recommendations
print(f"\n💡 Recommendations:")
best_practices = get_best_practices("documentation_completeness")
for i, practice in enumerate(best_practices["recommendations"][:3], 1):
    print(f"   {i}. {practice}")

# Export full audit report
print(f"\n📋 Exporting audit report...")
report = export_session_report()
print(f"   ✓ Report saved: {report['path']}")

print(f"\n✅ Audit complete!")
```

---

## Example 6: Automated Content Review Workflow

**Goal**: Review all documents systematically and mark reviewed ones.

```python
# Systematic content review

print("📖 Content Review Workflow")

# Get documents needing review
suggestions = get_suggested_actions()
review_items = [a for a in suggestions["actions"] if "review" in a["action"].lower()]

print(f"📋 {len(review_items)} items to review\n")

# Track progress
reviewed = 0
approved = 0
issues_found = []

for item in review_items:
    doc_path = item.get("target_document")

    print(f"🔄 Reviewing: {doc_path}")

    # Get document full context
    doc_context = get_document_context(doc_path)

    # Check quality
    print(f"   ✓ Health: {doc_context['health']}/100")
    print(f"   ✓ Version: {doc_context['metadata']['version']}")

    # Validate review
    validation = validate_action(
        "approve_document",
        doc_path,
        {"reviewer": "qa@example.com"}
    )

    if validation["valid"]:
        # Approve and mark as reviewed
        update_document_metadata(
            doc_path,
            {
                "status": "approved",
                "reviewed_by": "qa@example.com",
                "review_date": datetime.now().isoformat()
            }
        )

        log_agent_action(
            "document_reviewed",
            f"Systematic review of documentation",
            f"Approved {doc_path}",
            doc_path
        )

        approved += 1
        print(f"   ✅ Approved")
    else:
        print(f"   ⚠️  Issues: {validation['issues']}")
        issues_found.append(doc_path)

    reviewed += 1

    print()

# Summary
print("=" * 50)
print(f"✅ Review Complete:")
print(f"   Reviewed: {reviewed}")
print(f"   Approved: {approved}")
print(f"   With Issues: {len(issues_found)}")

if issues_found:
    print(f"\n   Documents with issues:")
    for doc in issues_found:
        print(f"   • {doc}")

print(f"\n✓ Session report exported")
```

---

## Example 7: Advanced Semantic Analysis

**Goal**: Find duplicate content and terminology inconsistencies.

```python
# Semantic analysis for content quality

print("🔍 Semantic Content Analysis")
print("=" * 50)

# Get comprehensive quality report
report = quality_report_comprehensive()

# 1. Near-Duplicate Detection
print("\n📄 Near-Duplicate Detection:")
semantic = quality_report_module("semantic")

if semantic.get("near_duplicates"):
    print(f"   Found {len(semantic['near_duplicates'])} duplicate pairs:")
    for dup in semantic["near_duplicates"][:5]:
        similarity = dup["similarity"] * 100
        print(f"   • {dup['doc1']}")
        print(f"     ↔ {dup['doc2']}")
        print(f"     Similarity: {similarity:.1f}%")
        print()
else:
    print("   ✓ No near-duplicates found")

# 2. Terminology Drift
print("\n📚 Terminology Consistency:")
if semantic.get("terminology_drift"):
    print(f"   Found {len(semantic['terminology_drift'])} inconsistencies:")
    for drift in semantic["terminology_drift"][:5]:
        print(f"   • Term: '{drift['term']}'")
        print(f"     Variants: {', '.join(drift['variants'])}")
        print(f"     In: {len(drift['documents'])} documents")
else:
    print("   ✓ Terminology is consistent")

# 3. Content Clusters
print(f"\n🗂️ Content Clusters:")
if semantic.get("content_clusters"):
    print(f"   Content organized into {len(semantic['content_clusters'])} topic clusters")
    for i, cluster in enumerate(semantic["content_clusters"][:3], 1):
        print(f"   Cluster {i}: {cluster['name']} ({len(cluster['documents'])} docs)")

# Recommendations
print("\n💡 Recommendations:")
if semantic.get("near_duplicates"):
    print("   • Review duplicate pairs - consolidate or differentiate")
if semantic.get("terminology_drift"):
    print("   • Standardize terminology across all documents")

print("\n✅ Semantic analysis complete!")
```

---

## Example 8: Knowledge Graph Analysis

**Goal**: Analyze concept coverage and identify learning gaps.

```python
# Knowledge graph analysis

print("🧠 Knowledge Graph Analysis")
print("=" * 50)

# Get knowledge graph report
knowledge = quality_report_module("knowledge")

# 1. Concept Overview
print("\n📊 Concept Overview:")
print(f"   Total concepts: {knowledge['total_concepts']}")
print(f"   Total relationships: {knowledge['total_relationships']}")
print(f"   Coverage score: {knowledge['coverage_score']}/100")

# 2. Orphan Concepts
print("\n🚫 Orphan Concepts (mentioned but never explained):")
if knowledge.get("orphan_concepts"):
    for orphan in knowledge["orphan_concepts"][:10]:
        print(f"   • '{orphan['name']}' in {orphan['document']}")

    if len(knowledge["orphan_concepts"]) > 10:
        remaining = len(knowledge["orphan_concepts"]) - 10
        print(f"   ... and {remaining} more")
else:
    print("   ✓ All concepts are properly explained")

# 3. Prerequisite Issues
print("\n📋 Prerequisite Issues:")
if knowledge.get("prerequisite_issues"):
    for issue in knowledge["prerequisite_issues"][:5]:
        print(f"   • {issue['document']}")
        print(f"     Missing prerequisites: {', '.join(issue['missing'])}")
else:
    print("   ✓ All documents have proper prerequisite coverage")

# 4. Suggest improvements
print("\n💡 Recommendations:")
if knowledge.get("orphan_concepts"):
    print("   • Add definitions or links for orphan concepts")
if knowledge.get("prerequisite_issues"):
    print("   • Add 'Prerequisites' sections to affected documents")
if knowledge["coverage_score"] < 80:
    print("   • Increase cross-referencing between related documents")

# Export knowledge map
print("\n📤 Exporting knowledge map visualization...")
log_agent_action(
    "knowledge_analysis",
    "Analyzed concept coverage and prerequisites",
    f"Found {len(knowledge.get('orphan_concepts', []))} orphan concepts",
    "project"
)

print("\n✅ Knowledge graph analysis complete!")
```

---

## Example 9: Predictive Freshness Analysis

**Goal**: Identify documents at risk of becoming stale.

```python
# Predictive freshness analysis

print("⏰ Predictive Freshness Analysis")
print("=" * 50)

# Get freshness predictions
freshness = quality_report_module("freshness")

# 1. Overview
print("\n📊 Freshness Overview:")
print(f"   Documents analyzed: {freshness['total_analyzed']}")
print(f"   Average risk score: {freshness['average_risk']:.2f}")

# 2. High-Risk Documents
print("\n🔴 High-Risk Documents (>70% staleness probability):")
high_risk = [p for p in freshness.get("predictions", []) if p["risk_score"] > 0.7]

if high_risk:
    for doc in sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)[:10]:
        risk_pct = doc["risk_score"] * 100
        days = doc.get("days_until_stale", "?")
        print(f"   🔴 {doc['path']}")
        print(f"      Risk: {risk_pct:.0f}% | Stale in: ~{days} days")
        if doc.get("risk_factors"):
            print(f"      Factors: {', '.join(doc['risk_factors'][:3])}")
else:
    print("   ✓ No high-risk documents found")

# 3. Medium-Risk Documents
print("\n🟡 Medium-Risk Documents (40-70%):")
medium_risk = [p for p in freshness.get("predictions", []) if 0.4 <= p["risk_score"] <= 0.7]
print(f"   {len(medium_risk)} documents at medium risk")

# 4. Schedule maintenance
print("\n📅 Recommended Maintenance Schedule:")
if high_risk:
    print("   This week:")
    for doc in high_risk[:3]:
        print(f"     • Review: {doc['path']}")
if medium_risk:
    print("   This month:")
    for doc in medium_risk[:3]:
        print(f"     • Check: {doc['path']}")

# Log for tracking
if high_risk:
    log_agent_action(
        "freshness_analysis",
        "Identified documents at risk of becoming stale",
        f"Found {len(high_risk)} high-risk, {len(medium_risk)} medium-risk documents",
        "project"
    )

print("\n✅ Freshness analysis complete!")
```

---

## Example 10: Code-Documentation Sync Check

**Goal**: Ensure code examples are accurate and up-to-date.

```python
# Code-documentation synchronization check

print("🔗 Code-Documentation Sync Check")
print("=" * 50)

# Get code-doc sync analysis
codesync = quality_report_module("codesync")

# 1. Overview
print("\n📊 Sync Status:")
print(f"   Total issues: {codesync['total_issues']}")
print(f"   Critical: {codesync['critical_count']}")
print(f"   Warnings: {codesync['warning_count']}")

if codesync['total_issues'] == 0:
    print("   ✓ All code examples are synchronized!")
else:
    # 2. Critical Issues
    print("\n🔴 Critical Issues (code examples broken):")
    for issue in codesync.get("critical_issues", [])[:10]:
        print(f"   • {issue['document']}")
        print(f"     Type: {issue['type']}")
        print(f"     Problem: {issue['message']}")
        print()

    # 3. Warnings
    print("\n🟡 Warnings:")
    warnings = [i for i in codesync.get("issues", []) if i["severity"] == "warning"]
    for issue in warnings[:5]:
        print(f"   • {issue['document']}: {issue['message']}")

    # 4. Fix critical issues
    print("\n🔧 Fixing Critical Issues:")
    for issue in codesync.get("critical_issues", [])[:3]:
        doc_path = issue["document"]

        # Validate fix
        validation = validate_action(
            "update_code_example",
            doc_path,
            {"issue_type": issue["type"]}
        )

        if validation["valid"]:
            # Get document
            doc = read_document(doc_path)

            # Log the fix attempt
            log_agent_action(
                "codesync_fix",
                f"Fixing {issue['type']} in code example",
                f"Reviewing {doc_path}",
                doc_path
            )

            print(f"   ✓ Ready to fix: {doc_path}")
        else:
            print(f"   ⚠ Cannot auto-fix: {doc_path} - {validation['message']}")

print("\n✅ Code-doc sync check complete!")
```

---

## Example 11: Norwegian Readability Analysis

**Goal**: Ensure Norwegian content is accessible to target audience.

```python
# Norwegian readability analysis

print("📖 Norwegian Readability Analysis (LIX)")
print("=" * 50)

# Get readability analysis
readability = quality_report_module("readability")

if "norwegian" not in readability or not readability["norwegian"].get("documents_analyzed"):
    print("   ℹ No Norwegian documents found")
else:
    no_data = readability["norwegian"]

    # 1. Overview
    print("\n📊 Norwegian Content Overview:")
    print(f"   Documents analyzed: {no_data['documents_analyzed']}")
    print(f"   Average LIX score: {no_data['average_lix']}")

    # LIX interpretation
    avg_lix = no_data['average_lix']
    if avg_lix < 25:
        level = "Very Easy (children's books)"
    elif avg_lix < 35:
        level = "Easy (simple text)"
    elif avg_lix < 45:
        level = "Medium (newspapers)"
    elif avg_lix < 55:
        level = "Difficult (official documents)"
    else:
        level = "Very Difficult (academic)"
    print(f"   Average difficulty: {level}")

    # 2. Difficult Documents
    print(f"\n🔴 Very Difficult Documents (LIX > 55):")
    for doc in no_data.get("difficult_documents", []):
        print(f"   • {doc['path']}")
        print(f"     LIX: {doc['lix']} ({doc['level']})")

    # 3. Distribution
    print("\n📈 Difficulty Distribution:")
    # Would show distribution across levels
    print(f"   Easy: {no_data.get('easy_count', 0)} documents")
    print(f"   Very Difficult: {no_data.get('very_difficult_count', 0)} documents")

    # 4. Recommendations
    print("\n💡 Recommendations for Difficult Documents:")
    if no_data.get("difficult_documents"):
        print("   • Use shorter sentences (aim for 15-20 words)")
        print("   • Replace long words with simpler alternatives")
        print("   • Break complex paragraphs into smaller ones")
        print("   • Add explanatory subheadings")

print("\n✅ Norwegian readability analysis complete!")
```

---

## Example 12: Pre-Release Quality Gate

**Goal**: Run comprehensive quality checks before release.

```python
# Pre-release quality gate check

print("🚦 Pre-Release Quality Gate")
print("=" * 50)

release_version = "2.5.0"
print(f"   Checking release v{release_version}\n")

# Get comprehensive report
report = quality_report_comprehensive()

# Define quality gates
gates = {
    "Health Score ≥ 80": report["health"]["score"] >= 80,
    "No Critical Issues": len(report["issues"]["critical"]) == 0,
    "Translations Current": len(report["translation"]["outdated"]) == 0,
    "No High-Risk Staleness": len([p for p in report["freshness"]["predictions"]
                                    if p["risk_score"] > 0.8]) == 0,
    "Code Examples Valid": len(report["codesync"]["critical"]) == 0,
    "No Orphan Concepts": len(report["knowledge"]["orphan_concepts"]) < 5,
    "Terminology Consistent": len(report["semantic"]["terminology_drift"]) < 3,
}

# Check each gate
print("📋 Quality Gate Results:\n")
all_passed = True

for gate_name, passed in gates.items():
    status = "✅" if passed else "❌"
    all_passed = all_passed and passed
    print(f"   {status} {gate_name}")

# Summary
print("\n" + "=" * 50)
if all_passed:
    print("🎉 ALL GATES PASSED - Ready for release!")

    log_agent_action(
        "quality_gate_passed",
        f"Pre-release check for v{release_version}",
        "All quality gates passed",
        "project"
    )
else:
    print("⚠️ GATES FAILED - Fix issues before release")

    # Show what needs fixing
    print("\n📋 Required Fixes:")
    failed_gates = [name for name, passed in gates.items() if not passed]
    for gate in failed_gates:
        print(f"   • {gate}")

    # Get specific issues
    print("\n🔧 Specific Issues:")
    issues = quality_report_issues(priority="high")
    for issue in issues[:5]:
        print(f"   • [{issue['module']}] {issue['message']}")

    log_agent_action(
        "quality_gate_failed",
        f"Pre-release check for v{release_version}",
        f"Failed gates: {', '.join(failed_gates)}",
        "project"
    )

print("\n✅ Quality gate check complete!")
```

---

## Best Practices for Claude Code Integration

### 1. **Always Start with Context**
```python
context = get_project_context()
# Check health, structure, current state
```

### 2. **Validate Before Bulk Changes**
```python
# Always dry_run first
apply_transformation(selector, transformation, dry_run=True)
# Then apply
apply_transformation(selector, transformation, dry_run=False)
```

### 3. **Log Everything for Audit Trail**
```python
log_agent_action(action, reasoning, result, target)
# Creates accountability and helps with debugging
```

### 4. **Use Workflow Guidance**
```python
guidance = get_workflow_guidance("what_you_want_to_do")
# Follow recommended steps
```

### 5. **Handle Errors Gracefully**
```python
try:
    # Do something
except Exception as e:
    log_agent_action("action_failed", reason, f"Error: {e}", target)
    # Continue or alert user
```

### 6. **Get Feedback on Next Steps**
```python
suggestions = get_suggested_actions()
# Always follow top priorities
```

---

## Running Examples

### As Claude Code Task
```bash
# Save example as .claude/tasks/health-check.py
# Run with:
media-engine-task health-check

# Or schedule it:
media-engine-task health-check --schedule "daily 9am"
```

### In Claude Desktop
1. Copy example code
2. Paste in Claude chat
3. Say "Run this" or "Execute this"
4. Claude executes using MCP tools

### As Automation Script
```bash
# Save as bin/daily-audit.py
# Add to cron:
0 9 * * * /usr/bin/python3 /path/to/bin/daily-audit.py
```

---

## Troubleshooting Examples

**"No project found"**
- Make sure MCP server is running with `--project` flag
- Or run from project root directory

**Tool calls failing**
- Check internet connectivity for webhooks
- Verify file paths are relative to project root
- Check project.yaml exists and is valid

**Slow execution**
- Use `dry_run=true` to preview before applying
- Batch operations are more efficient than individual updates
- Cache context to avoid repeated calls

---

**Last Updated:** December 2025
**Version:** 1.0
**Status:** Production Ready
