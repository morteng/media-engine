---
name: process-ai-queue
description: Process pending AI tasks from the dashboard queue with Claude Code tools
---

# Process AI Queue

Process pending AI tasks from the dashboard queue with full tool access.

## Usage

```bash
/process-ai-queue              # Process all pending tasks
/process-ai-queue --limit 5    # Process up to 5 tasks
```

## What This Command Does

```
+------------------------------------------------------------------+
|                    AI QUEUE PROCESSING WORKFLOW                    |
|                                                                   |
|   1. List pending tasks (ai_list_tasks)                           |
|   2. For each task:                                               |
|      a. Claim the task (ai_claim_task)                            |
|      b. Read and understand the content                           |
|      c. Process according to operation type:                      |
|         - improve: Edit files to improve clarity                  |
|         - translate: Create/update translations                   |
|         - analyze: Provide feedback (no file changes)             |
|         - summarize: Generate summary                             |
|         - expand: Elaborate on content                            |
|         - simplify: Simplify language                             |
|         - proofread: Fix grammar/spelling                         |
|      d. Run quality checks if appropriate                         |
|      e. Complete the task (ai_complete_task)                      |
|   3. Report summary of completed tasks                            |
+------------------------------------------------------------------+
```

## Processing Workflow

### Step 1: Check Queue
```bash
# Get pending tasks using MCP
mcp: ai_list_tasks status="pending"
```

If no pending tasks, report "No pending tasks" and exit.

### Step 2: Process Each Task

For each pending task:

#### 2a. Claim the Task
```bash
mcp: ai_claim_task task_id="<task_id>"
```

#### 2b. Understand the Request
Read the task details:
- **operation**: What to do (improve, translate, etc.)
- **instructions**: User's specific instructions
- **selections**: Documents/scenes to process
- **notes**: User notes attached to each selection
- **target_language**: For translation operations

#### 2c. Process Content

**For "improve" operations:**
1. Read the document(s)
2. Analyze content and notes
3. Edit the file directly to improve clarity, flow, etc.
4. Follow user instructions

**For "translate" operations:**
1. Read the source document
2. Create or update translation file using /media-create if needed
3. Translate content maintaining formatting
4. Update translation metadata

**For "analyze" operations:**
1. Read the document(s)
2. Provide detailed feedback
3. Do NOT modify files
4. Include feedback in completion summary

**For other operations (summarize, expand, simplify, proofread):**
1. Read the document(s)
2. Apply the requested transformation
3. Edit files directly

#### 2d. Quality Check (Optional)
For operations that modify files:
```bash
# Run quality check on modified files
/quality-check
```

#### 2e. Complete the Task
```bash
mcp: ai_complete_task task_id="<task_id>" summary="<what was done>" files_modified="<list of files>"
```

### Step 3: Report Summary

After processing all tasks, provide a summary:
```markdown
## AI Queue Processing Complete

**Tasks Processed**: 3
**Files Modified**: 5

### Task 1: improve (abc123)
- Improved clarity in chapter 1
- Added 2 examples
- Files: content/en/chapters/01_intro.md

### Task 2: translate (def456)
- Translated chapter 2 to Norwegian
- Files: content/no/chapters/02_setup.md

### Task 3: analyze (ghi789)
- Provided feedback on chapter 3
- Suggested improvements for code examples
- No files modified
```

## Examples

### Basic Usage
```
User: /process-ai-queue
Claude: Let me check the AI task queue...

[Uses ai_list_tasks to find 2 pending tasks]

Processing task abc123 (improve)...
[Claims task, reads document, edits file, completes task]

Processing task def456 (translate)...
[Claims task, reads source, creates translation, completes task]

## AI Queue Processing Complete
...
```

### With Limit
```
User: /process-ai-queue --limit 1
Claude: Processing only 1 task from the queue...
```

## MCP Tools Used

| Step | Tool | Purpose |
|------|------|------------|
| 1 | `ai_list_tasks` | Get pending tasks |
| 2a | `ai_claim_task` | Claim task for processing |
| 2b | `ai_get_task` | Get full task details |
| 2c | `read_document`, Edit | Process content |
| 2d | `quality_check` | Verify quality |
| 2e | `ai_complete_task` | Mark task done |
| 2e | `ai_fail_task` | Mark task failed (on error) |

## Error Handling

If an error occurs during processing:
1. Mark the task as failed using `ai_fail_task`
2. Continue with next task
3. Include error in final summary

## Integration with Skills

This command can leverage other skills:
- `/media-create` - For creating new translation files
- `/quality-check` - For validating changes
- `/test` - For running tests after code-related changes

## Notes for Claude Code

When processing tasks:
- **Honor user instructions**: Follow the instructions field carefully
- **Consider notes**: Each selection may have user notes attached
- **Be thorough**: Make meaningful improvements, not just cosmetic changes
- **Edit files directly**: Don't just suggest changes - make them
- **Provide clear summaries**: Users see the summary in the dashboard
