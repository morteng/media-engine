---
name: media-delete
description: Safely delete or archive Media Engine documents
---

# Delete/Archive Media Engine Content

Safely remove documents with dependency checking and optional archival.

## Usage

```bash
/media-delete [path]              # Interactive mode with path
/media-delete                     # Full interactive mode
/media-delete --permanent [path]  # Skip archive (use with caution)
```

## What This Command Does

```
+------------------------------------------------------------------+
|                    DOCUMENT DELETION WORKFLOW                      |
|                                                                   |
|   1. Validate document exists                                     |
|   2. Analyze impact (dependencies, translations)                  |
|   3. Show impact to user                                          |
|   4. Confirm deletion                                             |
|   5. Archive or delete                                            |
|   6. Clean up references (optional)                               |
+------------------------------------------------------------------+
```

## Safety First Approach

By default, documents are **archived** (moved to `.archive/`), not permanently deleted.

### Archive Location
```
project/
├── content/
│   └── en/chapters/...
└── .archive/                    # Archived documents
    └── content/
        └── en/chapters/
            └── deleted_chapter.md  # Preserves structure
```

## Interactive Workflow

### Step 1: Identify Document
If path not provided, help user find the document:
```bash
# List documents
mcp: list_chapters language="en"
```

### Step 2: Analyze Impact
```bash
# Check what depends on this document
mcp: analyze_change_impact target="..." change_type="delete"

# Get full context
mcp: get_document_context path="..."
```

### Step 3: Show Impact Report

Display to user:
```markdown
## Deletion Impact Analysis

**Document**: content/en/chapters/05_old_chapter.md
**Title**: Old Chapter

### Dependencies Found
- 2 documents reference this chapter
  - chapters/03_overview.md (line 45)
  - chapters/10_advanced.md (line 12)

### Translations Found
- Norwegian: content/no/chapters/05_gammelt_kapittel.md

### Recommendation
Archive this document first. Update references before permanent deletion.
```

### Step 4: Confirm with User
Present options:
1. **Archive** (recommended) - Move to .archive/
2. **Delete permanently** - Cannot be undone
3. **Cancel** - Do nothing
4. **Update references first** - Fix deps then delete

### Step 5: Execute Deletion
```bash
# Archive (default, safe)
mcp: delete_document path="..." archive=true check_dependencies=true

# Or permanent (only if user confirms)
mcp: delete_document path="..." archive=false
```

### Step 6: Handle Related Content (Optional)
If user wants to clean up:
```bash
# Delete translations too
mcp: delete_document path="content/no/chapters/05_gammelt_kapittel.md" archive=true

# Or update references in other documents
# Use Claude Code's Edit tool to update referencing documents
```

## Examples

### Archive a Document
```bash
/media-delete content/en/chapters/deprecated_api.md
```

Output:
```markdown
## Document Archived

**Original**: content/en/chapters/deprecated_api.md
**Archived to**: .archive/content/en/chapters/deprecated_api.md

### Warnings
- 1 document references this chapter (chapters/02_setup.md)

### Next Steps
- Update references in chapters/02_setup.md
- Or restore from .archive/ if needed
```

### Permanent Deletion
```bash
/media-delete --permanent content/en/drafts/scratch.md
```

Output:
```markdown
## Document Permanently Deleted

**Path**: content/en/drafts/scratch.md

⚠️ This cannot be undone.
```

### Restore Archived Document
```bash
# Documents in .archive/ can be moved back
mv .archive/content/en/chapters/old.md content/en/chapters/old.md
```

## MCP Tools Used

| Step | Tool | Purpose |
|------|------|---------|
| 1 | `read_document` | Verify document exists |
| 2 | `analyze_change_impact` | Check dependencies |
| 3 | `get_document_context` | Full context including translations |
| 4 | `delete_document` | Execute archive/deletion |
| 5 | `validate_project` | Verify no broken references |

## Safety Checks

### Automatic Checks
- [x] Document exists
- [x] Path is within project
- [x] Dependencies analyzed
- [x] Translations identified

### User Confirmation Required
- Permanent deletion
- Deletion with dependencies
- Deletion of source with translations

## Output Format

```markdown
## Deletion Result

**Action**: [archived/deleted]
**Path**: [original path]
**Archive**: [archive path if archived]

### Dependencies
- [List any affected documents]

### Warnings
- [Any warnings about references]

### Recovery
[Instructions for restoring if archived]
```

## Error Handling

| Error | Solution |
|-------|----------|
| Document not found | Show similar paths, help locate |
| Has dependencies | Show deps, offer to update refs first |
| Permission denied | Check file permissions |
| Outside project | Refuse operation for safety |

## Related Commands

- `/media-create` - Create new documents
- `/quality-check` - Validate after deletion
- `/media-status` - Check project health
