---
title: "Security Scanning"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/04_quality_checks"
tags:
  - security
  - secrets
  - pii
---

# Security Scanning

Media Engine includes comprehensive security scanning to detect sensitive content before publishing.

See [Quality Checks](04_quality_checks.md) for the broader quality system.

## Overview

The security scanner detects:

- **API Keys**: AWS, GitHub, OpenAI, Anthropic, Stripe, and more
- **PII**: Email addresses, phone numbers, SSNs
- **Internal URLs**: Private network addresses and localhost references
- **Credentials**: Passwords, tokens, and authentication secrets

## Running Security Scans

Use the CLI to scan your project for sensitive content.

### CLI

```bash
# Scan all documents
media-engine security

# Include asset files (YAML, JSON)
media-engine security --include-assets

# Output as JSON
media-engine security --json
```

### Python API

```python
from media_engine.security import scan_for_secrets, SensitiveContentScanner

# Quick scan
report = scan_for_secrets(project)

print(f"Files scanned: {report['files_scanned']}")
print(f"Findings: {report['total_findings']}")

# Detailed scanner
scanner = SensitiveContentScanner()
matches = scanner.scan_text(content)

for match in matches:
    print(f"{match.level}: {match.pattern_name}")
    print(f"  Found: {match.matched_text[:20]}...")
```

## Detected Patterns

The scanner recognizes common secret patterns.

### API Keys

| Pattern | Example | Severity |
|---------|---------|----------|
| AWS Access Key | `AKIA...` | Critical |
| GitHub Token | `ghp_...` | Critical |
| OpenAI API Key | `sk-...` | Critical |
| Anthropic Key | `sk-ant-...` | Critical |
| Stripe Live Key | `sk_live_...` | Critical |

### Personal Information

| Pattern | Example | Severity |
|---------|---------|----------|
| Email Address | `user@example.com` | High |
| Phone Number | `+1-555-X​XX-X​XXX` | High |
| SSN | `X​XX-X​X-X​XXX` | Critical |

### Internal References

| Pattern | Example | Severity |
|---------|---------|----------|
| Private IP | `10.x​.x​.x` | Medium |
| Localhost | `localhost:PORT` | Low |
| Internal URL | `internal.example/` | Medium |

## Sensitivity Levels

The scanner categorizes findings by severity:

- **Critical**: Remove before publishing (API keys, SSNs)
- **High**: Review carefully (emails, phone numbers)
- **Medium**: May be intentional (internal URLs)
- **Low**: Informational (localhost references)

## CI/CD Integration

Block publishing when critical issues are found:

```bash
# Fail on any critical findings
media-engine security || exit 1
```

```python
from media_engine.security import scan_for_secrets

report = scan_for_secrets(project, block_on_critical=True)
# Raises ValueError if critical findings exist
```

## Excluding False Positives

Some patterns may be intentional (e.g., example API keys in documentation). Configure exclusions in your project:

```yaml
# project.yaml
security:
  exclude_patterns:
    - "sk_test_*"  # Test mode keys
    - "*@example.com"  # Example emails
  exclude_files:
    - "content/examples/**"
```

## Best Practices

1. **Scan before committing**: Add security scan to pre-commit hooks
2. **Use environment variables**: Never hardcode real credentials
3. **Review findings**: Not all matches are actual secrets
4. **Document exceptions**: Explain why certain patterns are excluded
