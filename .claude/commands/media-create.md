---
name: media-create
description: Create new Media Engine content with proper structure
---

# Create Media Engine Content

Create new documents, translations, scripts, slides, or other content with proper structure and metadata.

## Usage

```bash
/media-create                           # Interactive mode
/media-create chapter "Title" [lang]    # New chapter
/media-create translation [lang] [path] # Translate existing doc
/media-create script "Title" [lang]     # Video script
/media-create slide "Title" [lang]      # Presentation
/media-create diagram "Title" [lang]    # Diagram definition
/media-create data "Title" [lang]       # Data spreadsheet
```

## What This Command Does

```
+------------------------------------------------------------------+
|                    DOCUMENT CREATION WORKFLOW                      |
|                                                                   |
|   1. Analyze project structure (get_project_context)              |
|   2. Generate scaffold (scaffold_document)                        |
|   3. Review with user                                             |
|   4. Create document (create_document)                            |
|   5. Verify creation                                              |
+------------------------------------------------------------------+
```

## Interactive Workflow

When run without arguments, guide the user through:

### Step 1: Document Type Selection
Ask the user what type of document to create:
- **chapter**: Standard documentation chapter
- **translation**: Translation of existing document
- **script**: Video script (YAML)
- **slide**: Presentation slides (YAML)
- **diagram**: Diagram definition (YAML)
- **data**: Data spreadsheet (YAML)

### Step 2: Title and Language
- Ask for document title
- Determine target language (default: source language)
- For translations: select source document

### Step 3: Generate and Review Scaffold
```bash
# Use MCP to generate scaffold
mcp: scaffold_document doc_type="..." title="..." language="..."
```

Show the user:
- Suggested file path
- Generated metadata
- Template content

### Step 4: Customize (Optional)
Ask if user wants to modify:
- File path
- Metadata fields
- Initial content

### Step 5: Create Document
```bash
# Use MCP to create
mcp: create_document path="..." title="..." doc_type="..."
```

### Step 6: Verify and Report
```bash
# Verify creation
mcp: read_document path="..."

# Report to user
"Document created: content/en/chapters/17_new_chapter.md"
```

## Examples

### Create a New Chapter
```bash
/media-create chapter "API Authentication" en
```

Workflow:
1. Generate scaffold for chapter
2. Suggest path: `content/en/chapters/17_api_authentication.md`
3. Create with proper frontmatter
4. Report success

### Create a Translation
```bash
/media-create translation no content/en/chapters/01_introduction.md
```

Workflow:
1. Read source document
2. Generate translation scaffold with source content
3. Suggest Norwegian filename
4. Create with translation metadata (source_document, source_version)
5. Remind user to translate content

### Create a Video Script
```bash
/media-create script "Product Demo" en
```

Workflow:
1. Generate script YAML scaffold
2. Suggest path: `content/en/scripts/product_demo.yaml`
3. Create with scene template structure
4. Report success

## MCP Tools Used

| Step | Tool | Purpose |
|------|------|---------|
| 1 | `get_project_context` | Understand project structure |
| 2 | `scaffold_document` | Generate template |
| 3 | `create_document` | Write the file |
| 4 | `read_document` | Verify creation |

## Output Format

After creation, provide:

```markdown
## Document Created

**Path**: content/en/chapters/17_api_authentication.md
**Type**: chapter
**Language**: English (en)
**Status**: draft

### Metadata
- Title: API Authentication
- Version: 1.0.0
- Freshness: 60 days

### Next Steps
1. Edit the document to add content
2. Run `/quality-check` when ready
3. Create translations if needed
```

## Error Handling

| Error | Solution |
|-------|----------|
| Document already exists | Suggest different path or offer to view existing |
| Invalid document type | Show available types |
| Source not found (translation) | List available source documents |

## Related Commands

- `/media-delete` - Delete/archive documents
- `/quality-check` - Validate content after creation
- `/media-translate` - Full translation workflow
