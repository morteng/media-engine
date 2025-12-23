# Media Engine MCP - Agent Developer Guide

**Version:** 1.0 | **Status:** Production-Ready

This guide explains how to use Media Engine's MCP (Model Context Protocol) server to build AI agents and automated workflows for documentation management.

## Quick Start

### Installation

```bash
pip install media-engine[mcp]
```

### Launch MCP Server

```bash
media-engine-mcp --project /path/to/project
```

### Configure in Claude Desktop

Create or edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "media-engine": {
      "command": "media-engine-mcp",
      "args": ["-p", "/path/to/project"]
    }
  }
}
```

Restart Claude Desktop to load the tools.

---

## Tool Categories

### 1. Context & Discovery Tools

Get project context and find relevant documents.

#### `get_project_context()`
Returns comprehensive project information:
- Project overview (name, description, purpose)
- Content structure (languages, documents, organization)
- Key terminology and concepts
- Current health metrics
- Recent activity

**Use Case:** When starting work on a project, get full context before making changes.

```
Agent: "What's the current state of this documentation project?"
→ get_project_context()
→ Agent understands project structure, health, and language setup
```

#### `find_relevant_documents(query: str, context: str = "")`
Semantic search for documents related to a query.

**Parameters:**
- `query`: What you're looking for ("API authentication", "installation steps")
- `context`: Optional context about what you're doing

**Returns:**
- List of matching documents with relevance scores
- Document paths and metadata
- Brief descriptions

**Use Case:** Find all docs related to a topic before making changes.

```
Agent: "Find all documents about authentication"
→ find_relevant_documents("authentication")
→ Returns API docs, guide chapters, examples
```

#### `analyze_change_impact(change_description: str)`
Predict what else might be affected by a change.

**Parameters:**
- `change_description`: Description of the change you want to make

**Returns:**
- List of affected documents
- Potential broken references
- Translation implications
- Suggested updates

**Use Case:** Before making a big change, understand the ripple effects.

```
Agent: "I want to rename 'API Key' to 'Secret Key' everywhere"
→ analyze_change_impact("Rename 'API Key' to 'Secret Key'")
→ Returns all affected docs, translations, code references
```

#### `get_document_context(document_path: str)`
Get detailed context about a specific document.

**Returns:**
- Full content preview
- Frontmatter (metadata)
- Links to related documents
- Quality issues
- Translation status

---

### 2. Suggestion & Guidance Tools

Get AI-powered recommendations about what to do next.

#### `get_suggested_actions()`
Get a ranked list of recommended next actions.

**Returns:**
- High-priority items (critical issues, stale content)
- Medium-priority items (incomplete content, inconsistencies)
- Low-priority items (optimizations, improvements)
- Reasoning for each suggestion

**Use Case:** At start of session, get actionable priorities.

```
Agent session starts
→ get_suggested_actions()
→ "Fix 3 high-priority quality issues"
→ "Update 2 stale translations"
→ "Complete 5 TODO items in API docs"
```

#### `validate_action(action: str, target: str, params: dict = {})`
Check if an action is safe before executing.

**Parameters:**
- `action`: What you want to do ("update_document", "delete_section")
- `target`: What you're doing it to (document path, etc.)
- `params`: Additional parameters

**Returns:**
- Whether action is valid
- Any warnings or concerns
- Estimated impact
- Alternative approaches if problematic

**Use Case:** Before making changes, verify the action makes sense.

```
Agent: "I want to delete the 'Deprecated' chapter"
→ validate_action("delete_document", "chapters/08_deprecated.md")
→ "Action valid but be aware: 5 documents link to this"
→ "Alternatives: Move to archive, mark as deprecated instead"
```

#### `get_workflow_guidance(workflow: str)`
Get step-by-step guidance for common workflows.

**Parameters:**
- `workflow`: Type of workflow ("translation", "new_feature", "release", etc.)

**Returns:**
- Step-by-step instructions
- Tools to use at each step
- Checkpoints and validation steps
- Common pitfalls

**Use Case:** Learn the recommended way to do something.

```
Agent: "How do I add a new chapter?"
→ get_workflow_guidance("new_chapter")
→ Step 1: Create file in content/en/chapters/
→ Step 2: Add frontmatter with metadata
→ Step 3: Write content
→ Step 4: Check health score
→ Step 5: Create translations
```

#### `get_best_practices(topic: str = "general")`
Get best practices for a specific topic.

**Parameters:**
- `topic`: "general", "api_docs", "translations", "video_content", etc.

**Returns:**
- Recommended patterns and approaches
- Common mistakes to avoid
- Quality standards
- Examples of good vs. poor implementations

---

### 3. Document Management Tools

Create, read, update, and delete documents.

#### `read_document(document_path: str)`
Read a document's content and metadata.

**Returns:**
- Full content
- Frontmatter fields
- Associated metadata
- Links and references

#### `update_document_metadata(document_path: str, updates: dict)`
Update document frontmatter (title, status, version, etc.)

**Parameters:**
- `document_path`: Path to document
- `updates`: Dictionary of fields to update

**Returns:**
- Updated metadata
- Any validation warnings

**Use Case:** Bump version, update status, change metadata.

```
Agent: "Mark this document as final"
→ update_document_metadata(
    "chapters/01_intro.md",
    {"status": "final", "reviewed_by": "qa@example.com"}
  )
```

#### `increment_document_version(document_path: str, part: str = "minor")`
Increment document version number.

**Parameters:**
- `document_path`: Path to document
- `part`: "major", "minor", or "patch"

**Returns:**
- New version number
- Updated metadata

---

### 4. Batch Operations

Execute multiple changes atomically.

#### `batch_update(operations: list)`
Execute multiple document updates in one transaction.

**Parameters:**
- `operations`: List of operations to perform

**Returns:**
- Summary of changes
- Success/failure status
- Rollback info if anything fails

**Use Case:** Apply the same change to multiple documents.

```
Agent: "Update all API docs to use new authentication method"
→ batch_update([
    {"action": "replace", "document": "chapters/auth.md", "find": "API Key", "replace": "Secret Key"},
    {"action": "replace", "document": "guides/auth.md", "find": "API Key", "replace": "Secret Key"},
    {"action": "update_metadata", "document": "chapters/auth.md", "version": "2.1.0"}
  ])
```

#### `apply_transformation(selector: str, transformation: str, dry_run: bool = True)`
Apply transformation to multiple documents matching a selector.

**Parameters:**
- `selector`: Document filter ("status:draft", "lang:en", "type:chapter")
- `transformation`: Transformation to apply ("update_status:final", "add_tag:reviewed")
- `dry_run`: Preview changes without applying

**Returns:**
- List of affected documents
- Changes that would be made
- Validation results

**Use Case:** Bulk update documents matching criteria.

```
Agent: "Mark all draft documents as in_review"
→ apply_transformation(
    "status:draft",
    "update_status:in_review",
    dry_run=true
  )
→ Shows 12 documents would be affected
→ apply_transformation(..., dry_run=false)  # Apply for real
```

#### `preview_changes(changes: dict)`
Preview proposed changes without applying them.

**Parameters:**
- `changes`: Changes to preview

**Returns:**
- Before/after diff
- Impact analysis
- Any warnings

---

### 5. Session & Memory Tools

Maintain context across multiple tool calls.

#### `set_session_context(key: str, value: str)`
Store information for use later in session.

**Use Case:** Remember decisions and state across multiple calls.

```
Agent: "Remember the API version we're documenting"
→ set_session_context("api_version", "2.5.0")
→ Later, get_session_context("api_version") returns "2.5.0"
```

#### `log_agent_action(action: str, reasoning: str, result: str, target: str = "")`
Log what the agent did (for audit trail and learning).

**Returns:**
- Confirmation of logged action
- Action ID for reference

**Use Case:** Create audit trail of all changes.

```
Agent: "Log that I updated the API documentation"
→ log_agent_action(
    "document_update",
    "API docs were out of date with v2.5 features",
    "Updated 5 documents with new endpoints",
    "chapters/api.md"
  )
```

#### `get_agent_actions(limit: int = 20)`
Get history of actions taken by agent in session.

**Returns:**
- Recent actions with timestamps
- Reasoning and results
- Target documents

#### `export_session_report()`
Export complete session activity report.

**Returns:**
- Summary of all actions taken
- Documents modified
- Issues found and fixed
- Recommendations for next steps

---

### 6. Quality & Validation Tools

Check quality and validate content with comprehensive analysis.

#### `quality_check()`
Run comprehensive quality checks.

**Returns:**
- Summary of issues by severity
- Detailed findings
- Quality score changes

#### `validate_project()`
Validate entire project against schema.

**Returns:**
- Validation results
- Schema violations
- Reference integrity

#### `quality_report_comprehensive()`
Run ALL analysis modules and get unified quality report.

**Returns:**
- Project health summary
- Basic quality (readability, links, schema)
- Semantic analysis (duplicates, terminology)
- Knowledge graph (concepts, prerequisites)
- Freshness predictions (staleness risk)
- Code-doc synchronization issues
- Advanced analysis (audience, style)
- Unified recommendations

**Use Case:** Get complete quality picture before major releases or reviews.

```
Agent: "Give me a complete quality report"
→ quality_report_comprehensive()
→ Returns unified report across all 7+ analysis modules
→ Prioritized recommendations for improvement
```

#### `quality_report_document(document_path: str)`
Get detailed quality analysis for a specific document.

**Parameters:**
- `document_path`: Path to the document to analyze

**Returns:**
- Document-specific health score
- Similar documents (semantic analysis)
- Concepts and prerequisites (knowledge graph)
- Readability metrics (LIX for Norwegian, Flesch for English)
- Staleness risk prediction
- Code-doc sync status

**Use Case:** Deep-dive into a specific document's quality.

```
Agent: "Analyze the API authentication chapter"
→ quality_report_document("chapters/08_api_auth.md")
→ Returns comprehensive analysis for that document
```

#### `quality_report_module(module: str)`
Get analysis from a specific module.

**Parameters:**
- `module`: One of "semantic", "knowledge", "freshness", "codesync", "readability", "advanced"

**Returns:**
- Module-specific analysis results
- Issues and recommendations

**Use Case:** Focus on a specific type of analysis.

```
Agent: "Show me semantic duplicates"
→ quality_report_module("semantic")
→ Returns near-duplicates, terminology drift, content clusters
```

#### `quality_report_issues(priority: str = "all")`
Get prioritized list of all quality issues.

**Parameters:**
- `priority`: "high", "medium", "low", or "all"

**Returns:**
- Issues sorted by priority
- Source module for each issue
- Specific recommendations

---

### 7. Advanced Analysis Tools

Deep analysis capabilities for content quality and maintenance.

#### Semantic Analysis

Detect content similarity and terminology consistency.

**Available through `quality_report_module("semantic")`:**
- **Near-Duplicates**: Documents with >85% content similarity
- **Terminology Drift**: Inconsistent term usage across documents
- **Content Clusters**: Automatic topic grouping

**Use Case:** Find redundant content and maintain consistent vocabulary.

```
Agent: "Are there any duplicate documents?"
→ natural_language_query("duplicate documents")
→ Returns semantic similarity analysis
```

#### Knowledge Graph

Map concepts and relationships across documentation.

**Available through `quality_report_module("knowledge")`:**
- **Concept Extraction**: Key concepts in each document
- **Prerequisite Mapping**: What readers should know before each document
- **Orphan Concepts**: Concepts mentioned but never explained
- **Coverage Score**: How well concepts are interconnected

**Use Case:** Ensure documentation has proper learning flow.

```
Agent: "Which concepts are mentioned but never explained?"
→ natural_language_query("orphan concepts")
→ Returns list of concepts needing definition
```

#### Predictive Freshness

Predict which documents will become stale.

**Available through `quality_report_module("freshness")`:**
- **Staleness Risk Score**: 0-1 probability of becoming stale
- **Days Until Stale**: Predicted time before review needed
- **Risk Factors**: Why document is at risk (references volatile content, etc.)

**Use Case:** Proactive content maintenance planning.

```
Agent: "What content is at risk of becoming outdated?"
→ natural_language_query("staleness risk")
→ Returns high-risk documents with predicted timeframes
```

#### Code-Doc Sync

Detect mismatches between code references and documentation.

**Available through `quality_report_module("codesync")`:**
- **Syntax Errors**: Invalid code examples
- **API Mismatches**: Deprecated or changed API references
- **Version Drift**: Documentation doesn't match code version

**Use Case:** Keep code examples accurate.

```
Agent: "Are the code examples up to date?"
→ natural_language_query("code sync")
→ Returns list of outdated code references
```

#### Norwegian Readability (LIX)

Specific readability analysis for Norwegian content.

**Available through `quality_report_module("readability")`:**
- **LIX Score**: Standard Norwegian readability metric
- **Difficulty Level**: "easy", "medium", "difficult", "very_difficult"
- **Recommendations**: How to simplify complex content

**Use Case:** Ensure Norwegian content is accessible.

```
Agent: "How readable is our Norwegian content?"
→ natural_language_query("norwegian readability")
→ Returns LIX scores and difficulty assessments
```

---

### 8. Webhook & Event Tools

Subscribe to and receive notifications about project changes.

#### `register_webhook(url: str, event_types: str)`
Register to receive notifications about events.

**Parameters:**
- `url`: Webhook URL to call (must accept POST)
- `event_types`: Comma-separated event types
  - `document.*` - Any document change
  - `document.updated`, `document.created`, `document.deleted`
  - `build.*` - Any build event
  - `build.started`, `build.completed`, `build.failed`
  - `quality.*` - Any quality issue
  - `quality.issue`, `quality.check_completed`

**Returns:**
- Webhook ID
- Confirmation of registration

**Use Case:** Get notified when important events happen.

```
Agent: "Notify me when quality checks complete"
→ register_webhook(
    "https://agent.example.com/webhook",
    "quality.check_completed,build.completed"
  )
→ Returns webhook_id: "abc123"
→ Agent later receives POST with event details
```

#### `list_webhooks()`
List all registered webhooks.

#### `unregister_webhook(webhook_id: str)`
Remove a webhook subscription.

#### `emit_event(event_type: str, data: dict)`
Emit a test event (for testing workflows).

#### `on_event_notification(event_json: str)`
Receive and handle an event notification.

---

### 9. Claude Code Specific Tools

Integration with Claude Code (CLI tool).

#### `generate_claude_context()`
Generate optimal context for Claude Code.

**Returns:**
- Content for `.claude/claude_context.md`
- Current project state summary
- Key commands and workflows
- Important conventions
- Current issues and priorities

**Use Case:** Update Claude Code context with latest project state.

```
Agent: "Update Claude Code context with current project state"
→ generate_claude_context()
→ Content that describes:
  - 12 chapters, 2 languages, 3 pending translations
  - 5 high-priority issues
  - Current health score
  - Recommended next tasks
```

#### `natural_language_query(query: str)`
Ask natural language questions about the project.

**Returns:**
- Answer to the question
- Supporting context
- Recommended next steps

**Use Case:** Ask natural questions without knowing exact tool names.

```
Agent: "Which chapters are still incomplete?"
→ natural_language_query("which chapters are still incomplete")
→ Returns: "5 chapters have TODO items..."
```

---

## Example Workflows

### Workflow 1: Documentation Review & Update

```python
# 1. Get project state
context = get_project_context()

# 2. Find quality issues
suggestions = get_suggested_actions()
# "Fix 3 critical quality issues in API docs"

# 3. Get guidance on how to fix
guidance = get_workflow_guidance("quality_improvement")

# 4. For each issue, validate fix before applying
for issue in high_priority_issues:
    validation = validate_action(
        "fix_quality_issue",
        issue["document"],
        {"issue_type": issue["type"]}
    )

    if validation["valid"]:
        # Apply fix
        update_document_metadata(issue["document"], {"status": "in_review"})
        log_agent_action(
            "quality_fix",
            f"Fixed {issue['type']}",
            "Document updated",
            issue["document"]
        )

# 5. Get next steps
next_actions = get_suggested_actions()
log_agent_action(
    "session_complete",
    "Documentation review",
    f"Fixed {fixed_count} issues",
    "project"
)
```

### Workflow 2: Translation Coordination

```python
# 1. Get project context
context = get_project_context()

# 2. Find documents needing translation
suggested = get_suggested_actions()
# "Translate 8 updated English documents to Norwegian"

# 3. Plan translation workflow
guidance = get_workflow_guidance("translation")

# 4. Apply bulk update to mark for translation
apply_transformation(
    "lang:en AND status:final AND tag:needs_translation",
    "add_tag:pending_translation",
    dry_run=True  # Preview first
)

# Show preview to human or approve automatically
apply_transformation(
    "lang:en AND status:final AND tag:needs_translation",
    "add_tag:pending_translation",
    dry_run=False  # Actually apply
)

# 5. Subscribe to completion notifications
register_webhook(
    "https://slack.example.com/translations",
    "quality.check_completed,build.completed"
)

# 6. Log session
export_session_report()
```

### Workflow 3: New Feature Documentation

```python
# 1. Get context about current state
context = get_project_context()

# 2. Get guidance for new feature docs
guidance = get_workflow_guidance("new_feature")
# Step-by-step instructions for documenting a new feature

# 3. Check if related docs exist
related = find_relevant_documents("new_feature_name")

# 4. Analyze impact of adding docs
impact = analyze_change_impact("Adding chapter about new feature")

# 5. Validate that structure makes sense
validation = validate_action(
    "create_document",
    "chapters/XX_new_feature.md",
    {"section": "features"}
)

# 6. Create in batch if creating multiple
batch_update([
    {"action": "create", "path": "chapters/XX_new_feature.md", "content": "..."},
    {"action": "update_metadata", "path": "index.md", "update": {"version": "3.1.0"}},
    {"action": "create", "path": "content/no/chapters/XX_new_feature.md", "content": "..."} # Translated version
])

# 7. Log
log_agent_action(
    "new_documentation",
    "New feature needed documentation",
    "Created chapter and Norwegian translation",
    "chapters/XX_new_feature.md"
)
```

### Workflow 4: Advanced Quality Analysis & Maintenance

```python
# 1. Get comprehensive quality report
report = quality_report_comprehensive()
# Returns unified analysis from all modules

# 2. Review high-priority issues
issues = quality_report_issues(priority="high")
# "3 near-duplicate documents found"
# "5 documents at high staleness risk"
# "2 critical code-doc sync issues"

# 3. Deep-dive into semantic duplicates
semantic = quality_report_module("semantic")
for dup in semantic["near_duplicates"]:
    # Analyze each duplicate pair
    doc1_context = get_document_context(dup["doc1"])
    doc2_context = get_document_context(dup["doc2"])
    # Decide: consolidate, differentiate, or leave as-is

# 4. Check freshness predictions
freshness = quality_report_module("freshness")
high_risk = [p for p in freshness["predictions"] if p["risk_score"] > 0.7]
# Schedule reviews for high-risk documents

# 5. Fix code-doc sync issues
codesync = quality_report_module("codesync")
for issue in codesync["critical_issues"]:
    # Update code examples to match current API
    doc = read_document(issue["document"])
    # Fix the issue
    update_document_content(issue["document"], fixed_content)
    log_agent_action(
        "codesync_fix",
        f"Fixed {issue['type']} in {issue['document']}",
        "Updated code example to match API v2.5",
        issue["document"]
    )

# 6. Check Norwegian readability
readability = quality_report_module("readability")
difficult = [r for r in readability["norwegian"] if r["level"] == "very_difficult"]
# Flag documents needing simplification

# 7. Export session report
report = export_session_report()
# Summary of all quality improvements made
```

### Workflow 5: Pre-Release Quality Gate

```python
# 1. Run comprehensive quality check
report = quality_report_comprehensive()

# 2. Check if project passes quality gates
gates = {
    "health_score": report["health"]["score"] >= 80,
    "no_critical_issues": len(report["issues"]["critical"]) == 0,
    "translations_current": len(report["translation"]["outdated"]) == 0,
    "no_high_risk_staleness": len([p for p in report["freshness"]["predictions"]
                                   if p["risk_score"] > 0.8]) == 0,
    "code_examples_valid": len(report["codesync"]["critical"]) == 0,
}

# 3. Report gate status
all_passed = all(gates.values())
if all_passed:
    log_agent_action(
        "quality_gate_passed",
        "Pre-release quality check",
        "All quality gates passed",
        "project"
    )
else:
    failed_gates = [g for g, passed in gates.items() if not passed]
    log_agent_action(
        "quality_gate_failed",
        "Pre-release quality check",
        f"Failed gates: {', '.join(failed_gates)}",
        "project"
    )
    # Get specific issues for each failed gate
    for gate in failed_gates:
        issues = quality_report_issues(priority="high")
        # Help fix each issue
```

---

## Best Practices for Agents

### 1. **Start with Context**
Always begin by getting project context:
```python
context = get_project_context()
# Understand structure, health, status
```

### 2. **Get Guidance**
Use workflow guidance before making changes:
```python
guidance = get_workflow_guidance("what_you_want_to_do")
# Follow recommended steps
```

### 3. **Validate Before Changing**
Always validate actions:
```python
validation = validate_action(action, target)
if not validation["valid"]:
    # Adjust approach or ask for clarification
```

### 4. **Preview Batch Changes**
Always use `dry_run=true` first:
```python
# Preview
apply_transformation(selector, transformation, dry_run=True)
# Then apply
apply_transformation(selector, transformation, dry_run=False)
```

### 5. **Log Everything**
Create audit trail:
```python
log_agent_action(action, reasoning, result, target)
```

### 6. **Handle Errors Gracefully**
Document what failed and why:
```python
try:
    # Do something
except Exception as e:
    log_agent_action(
        "action_failed",
        "Reason for attempt",
        f"Failed: {str(e)}",
        target
    )
```

### 7. **Get Feedback**
Ask for next steps:
```python
suggestions = get_suggested_actions()
# Follow top recommendations
```

---

## Security Considerations

1. **Path Validation**: All paths are validated against project boundaries
2. **No Shell Access**: MCP tools don't execute arbitrary commands
3. **Read-Only Resources**: Some operations require explicit approval
4. **Audit Logging**: All changes are logged with reasoning
5. **Webhook Verification**: In production, verify webhook signatures

---

## Troubleshooting

**"No project found"**
- Ensure MCP server was started with `--project` flag pointing to valid project
- Or start server in project root directory

**"Path outside project"**
- Can only access files within project boundaries
- Check file path is relative to project root

**Tool not available?**
- Make sure `pip install media-engine[mcp]` installed the MCP extra
- Restart Claude Desktop if recently updated

**Webhooks not firing?**
- Check webhook URL is publicly accessible
- Verify event types match your subscriptions
- Check server logs for delivery errors

---

## More Information

- **MCP Spec**: https://spec.modelcontextprotocol.io/
- **Media Engine Docs**: See project documentation
- **Examples**: See example workflows in this guide

---

**Last Updated:** December 2025 | **Version:** 1.0
