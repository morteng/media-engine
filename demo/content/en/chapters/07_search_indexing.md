---
title: "Search Indexing"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/02_content_management"
tags:
  - search
  - indexing
  - full-text
---

# Search Indexing

Media Engine provides full-text search for your project content with relevance scoring.

See [Content Management](02_content_management.md) for how documents are structured.

## Overview

The search system:

- Indexes all Markdown documents
- Supports full-text queries
- Ranks results by relevance
- Persists indexes for fast searches
- Integrates with the CLI

## Building a Search Index

Create and update search indexes using the CLI or Python API.

### CLI

```bash
# Build/update search index
media-engine index

# Search documents
media-engine search "authentication"

# Limit results
media-engine search "api" --limit 10

# Rebuild index before searching
media-engine search "query" --rebuild
```

### Python API

```python
from media_engine import build_search_index, find_project
from media_engine.search import SearchIndex

project = find_project()

# Build index
index = build_search_index(project)

# Save for later use
index.save(Path(".cache/search_index.json"))

# Load existing index
index = SearchIndex.load(Path(".cache/search_index.json"))
```

## Searching

```python
# Basic search
results = index.search("authentication", limit=10)

for result in results:
    print(f"{result.score:.0f} - {result.entry.title}")
    print(f"  {result.entry.excerpt}")
```

### Search Result Properties

| Property | Description |
|----------|-------------|
| `score` | Relevance score (higher = better) |
| `entry.id` | Document identifier |
| `entry.title` | Document title |
| `entry.path` | File path |
| `entry.type` | Document type (chapter, etc.) |
| `entry.excerpt` | Content preview |
| `entry.tags` | Document tags |

## Index Entries

Each indexed document has:

```python
@dataclass
class SearchEntry:
    id: str           # Unique identifier
    title: str        # Document title
    path: str         # File path
    type: str         # Document type
    content: str      # Full text content
    excerpt: str      # First ~200 chars
    tags: list[str]   # Document tags
    language: str     # Language code
```

## Relevance Scoring

The search algorithm considers:

1. **Title matches**: Highest weight
2. **Tag matches**: High weight
3. **Content matches**: Standard weight
4. **Term frequency**: More occurrences = higher score
5. **Document length**: Normalized for fair comparison

## CLI Output

```
$ media-engine search "video"

Search results for: video

Score  Title                          Type       Excerpt
────────────────────────────────────────────────────────
 85    Video Production               chapter    Media Engine integrates with...
 42    Introduction to Media Engine   chapter    ...generate videos, and other...
 28    Content Management             chapter    ...video scripts are defined...

Found 3 results
```

## JSON Output

```bash
media-engine search "video" --json
```

```json
{
  "query": "video",
  "results": [
    {
      "id": "en/chapters/03_video_production",
      "title": "Video Production",
      "path": "content/en/chapters/03_video_production.md",
      "score": 85,
      "excerpt": "Media Engine integrates with..."
    }
  ]
}
```

## Index Persistence

The system stores indexes as JSON for fast loading:

```python
# Save after building
index.save(project.cache_dir / "search_index.json")

# Load on subsequent runs
if index_path.exists():
    index = SearchIndex.load(index_path)
else:
    index = build_search_index(project)
    index.save(index_path)
```

## Multi-language Support

The search system indexes all languages:

```python
# Search across all languages
results = index.search("authentication")

# Filter by language in results
en_results = [r for r in results if r.entry.language == "en"]
```

## Best Practices

1. **Rebuild periodically**: Run `media-engine index` after major content changes
2. **Use tags**: Well-tagged documents are easier to find
3. **Write clear titles**: Titles heavily influence search results
4. **Check excerpts**: The first paragraph should summarize the document

## Integration Example

```python
from media_engine import find_project
from media_engine.search import build_search_index

def search_project(query: str, limit: int = 10):
    """Search project content."""
    project = find_project()
    if not project:
        return []

    # Load or build index
    index_path = project.cache_dir / "search_index.json"
    if index_path.exists():
        index = SearchIndex.load(index_path)
    else:
        index = build_search_index(project)
        index.save(index_path)

    # Search and return
    results = index.search(query, limit=limit)
    return [
        {
            "title": r.entry.title,
            "path": r.entry.path,
            "score": r.score,
        }
        for r in results
    ]
```
