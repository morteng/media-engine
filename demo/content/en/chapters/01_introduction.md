---
title: "Introduction to Media Engine"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
tags:
  - introduction
  - overview

# Hierarchy metadata
doc_type: "architecture"
lifecycle: "living"
sequence_order: 1
owner: "morteng@example.com"
approvers:
  - "reviewer@example.com"

# Key facts defined here
anchors:
  project_name:
    value: "Media Engine"
    type: string
  min_python_version:
    value: "3.11"
    type: string
---

# Introduction to Media Engine

Media Engine is a powerful, agent-operated media production framework designed to transform structured content into professional outputs. Whether you need documents, presentations, videos, or data exports, Media Engine provides a unified workflow that AI assistants like Claude Code can operate autonomously—turning your Markdown source files into polished deliverables with minimal manual intervention.

## Key Features

- **Content Management**: Markdown documents with YAML frontmatter for metadata tracking
- **Multi-format Output**: Generate HTML, PDF, PPTX, XLSX, and video from the same source
- **Smart Caching**: Only rebuild what's changed
- **Multi-language Support**: Content in multiple languages with translation tracking
- **Agent-Friendly**: CLI designed for AI assistants to operate

## How It Works

```
Content (Markdown) → Media Engine → Outputs (PDF, Video, etc.)
                          ↑
                    project.yaml
                    (configuration)
```

![Media Engine Architecture](../assets/images/architecture.svg)

The media engine reads your content, applies your theme, and generates outputs. It tracks what's been built and only regenerates when source content changes.

![Content Workflow](../assets/images/workflow.svg)

## Getting Started

1. Create a project with `media-engine init`
2. Add content to `content/{language}/chapters/`
3. Build with `media-engine build`
4. Publish to Desktop with `media-engine publish`

## Feature Overview

| Category | Capabilities |
|----------|-------------|
| **Content** | Markdown with frontmatter, multi-language support, translation tracking |
| **Outputs** | HTML, PDF, PPTX, XLSX, video generation |
| **Quality** | Readability scoring, link validation, security scanning |
| **Workflow** | Smart caching, dependency tracking, approval workflows |
| **Integration** | CLI for automation, MCP server for AI agents, web dashboard |
