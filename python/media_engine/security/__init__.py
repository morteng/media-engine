"""
Security & Sensitive Content Detection for Media Engine

Scans documents for:
- API keys and tokens
- Passwords and secrets
- PII (emails, phone numbers, addresses)
- Internal URLs and IPs
- Confidential patterns

Prevents accidental leaks in published documentation.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class SensitivityLevel(str, Enum):
    """Severity levels for sensitive content."""

    CRITICAL = "critical"  # API keys, passwords - blocks publish
    HIGH = "high"  # PII, internal IPs - warns loudly
    MEDIUM = "medium"  # Suspicious patterns - warns
    LOW = "low"  # Potential issues - info


@dataclass
class SensitiveMatch:
    """A detected sensitive content match."""

    pattern_name: str
    matched_text: str
    redacted_text: str
    line_number: int
    column: int
    level: SensitivityLevel
    file_path: Optional[Path] = None
    context: str = ""


# === Detection Patterns ===

PATTERNS = {
    # API Keys and Tokens
    "aws_access_key": {
        "pattern": r"AKIA[0-9A-Z]{16}",
        "level": SensitivityLevel.CRITICAL,
        "description": "AWS Access Key ID",
    },
    "aws_secret_key": {
        "pattern": r"[A-Za-z0-9/+=]{40}",
        "level": SensitivityLevel.CRITICAL,
        "description": "Potential AWS Secret Key",
        "context_required": ["aws", "secret", "key"],
    },
    "github_token": {
        "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
        "level": SensitivityLevel.CRITICAL,
        "description": "GitHub Token",
    },
    "github_pat": {
        "pattern": r"github_pat_[A-Za-z0-9_]{22,}",
        "level": SensitivityLevel.CRITICAL,
        "description": "GitHub Personal Access Token",
    },
    "openai_key": {
        "pattern": r"sk-[A-Za-z0-9]{48,}",
        "level": SensitivityLevel.CRITICAL,
        "description": "OpenAI API Key",
    },
    "anthropic_key": {
        "pattern": r"sk-ant-[A-Za-z0-9-]{40,}",
        "level": SensitivityLevel.CRITICAL,
        "description": "Anthropic API Key",
    },
    "stripe_key": {
        "pattern": r"sk_live_[A-Za-z0-9]{24,}",
        "level": SensitivityLevel.CRITICAL,
        "description": "Stripe Live Secret Key",
    },
    "slack_token": {
        "pattern": r"xox[baprs]-[A-Za-z0-9-]{10,}",
        "level": SensitivityLevel.CRITICAL,
        "description": "Slack Token",
    },
    "generic_api_key": {
        "pattern": r"(?i)(api[_-]?key|apikey|api[_-]?secret)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_-]{20,})[\"']?",
        "level": SensitivityLevel.HIGH,
        "description": "Generic API Key Assignment",
    },
    "generic_secret": {
        "pattern": r"(?i)(secret|password|passwd|pwd|token)[\"']?\s*[:=]\s*[\"']?([^\s\"']{8,})[\"']?",
        "level": SensitivityLevel.HIGH,
        "description": "Generic Secret Assignment",
    },
    "bearer_token": {
        "pattern": r"Bearer\s+[A-Za-z0-9_-]{20,}",
        "level": SensitivityLevel.HIGH,
        "description": "Bearer Token",
    },
    "jwt_token": {
        "pattern": r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
        "level": SensitivityLevel.HIGH,
        "description": "JWT Token",
    },
    # PII - Personal Identifiable Information
    "email": {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "level": SensitivityLevel.MEDIUM,
        "description": "Email Address",
        "exceptions": ["example.com", "example.org", "test.com", "localhost"],
    },
    "phone_us": {
        "pattern": r"\b(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",
        "level": SensitivityLevel.MEDIUM,
        "description": "US Phone Number",
    },
    "phone_intl": {
        "pattern": r"\+[0-9]{1,3}[-.\s]?[0-9]{6,14}",
        "level": SensitivityLevel.MEDIUM,
        "description": "International Phone Number",
    },
    "ssn": {
        "pattern": r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
        "level": SensitivityLevel.CRITICAL,
        "description": "Social Security Number",
    },
    "credit_card": {
        "pattern": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
        "level": SensitivityLevel.CRITICAL,
        "description": "Credit Card Number",
    },
    # Network/Infrastructure
    "ipv4_private": {
        "pattern": r"\b(?:10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3})\b",
        "level": SensitivityLevel.MEDIUM,
        "description": "Private IP Address",
    },
    "internal_url": {
        "pattern": r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|internal\.|staging\.|dev\.)[^\s\"'<>]*",
        "level": SensitivityLevel.MEDIUM,
        "description": "Internal/Development URL",
    },
    # File paths that might be sensitive
    "windows_path": {
        "pattern": r"[A-Z]:\\(?:Users|Documents|Desktop)\\[^\s\"'<>]+",
        "level": SensitivityLevel.LOW,
        "description": "Windows User Path",
    },
    "unix_home": {
        "pattern": r"/(?:home|Users)/[a-zA-Z0-9_-]+/[^\s\"'<>]+",
        "level": SensitivityLevel.LOW,
        "description": "Unix Home Directory Path",
    },
}


class SensitiveContentScanner:
    """
    Scans content for sensitive information.

    Usage:
        scanner = SensitiveContentScanner()
        matches = scanner.scan_text(content)
        matches = scanner.scan_document(doc_path)
        report = scanner.scan_project(project)
    """

    def __init__(self, custom_patterns: dict = None, ignore_patterns: list = None):
        """
        Initialize scanner.

        Args:
            custom_patterns: Additional patterns to detect
            ignore_patterns: Pattern names to skip
        """
        self.patterns = PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
        self.ignore_patterns = set(ignore_patterns or [])

        # Compile patterns
        self._compiled = {}
        for name, config in self.patterns.items():
            if name not in self.ignore_patterns:
                self._compiled[name] = re.compile(config["pattern"])

    def scan_text(self, text: str, file_path: Path = None) -> list[SensitiveMatch]:
        """
        Scan text for sensitive content.

        Args:
            text: Text to scan
            file_path: Optional file path for context

        Returns:
            List of SensitiveMatch objects
        """
        matches = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            for name, regex in self._compiled.items():
                config = self.patterns[name]

                for match in regex.finditer(line):
                    matched_text = match.group()

                    # Check exceptions
                    exceptions = config.get("exceptions", [])
                    if any(exc in matched_text.lower() for exc in exceptions):
                        continue

                    # Check context requirements
                    context_required = config.get("context_required", [])
                    if context_required:
                        line_lower = line.lower()
                        if not any(ctx in line_lower for ctx in context_required):
                            continue

                    # Create redacted version
                    redacted = self._redact(matched_text, name)

                    # Get surrounding context
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 20)
                    context = line[start:end]

                    matches.append(
                        SensitiveMatch(
                            pattern_name=name,
                            matched_text=matched_text,
                            redacted_text=redacted,
                            line_number=line_num,
                            column=match.start() + 1,
                            level=config["level"],
                            file_path=file_path,
                            context=context,
                        )
                    )

        return matches

    def _redact(self, text: str, pattern_name: str) -> str:
        """Create redacted version of sensitive text."""
        if len(text) <= 8:
            return "*" * len(text)

        # Keep first and last 2 chars for identification
        return text[:2] + "*" * (len(text) - 4) + text[-2:]

    def scan_document(self, doc_path: Path) -> list[SensitiveMatch]:
        """Scan a document file for sensitive content."""
        from ..cms.document import Document

        doc = Document.load(doc_path)

        # Scan content
        matches = self.scan_text(doc.content, doc_path)

        # Also scan metadata values
        for key, value in doc.metadata.items():
            if isinstance(value, str):
                meta_matches = self.scan_text(value, doc_path)
                for m in meta_matches:
                    m.context = f"metadata.{key}: {m.context}"
                matches.extend(meta_matches)

        return matches

    def scan_project(self, project, include_assets: bool = False) -> dict:
        """
        Scan entire project for sensitive content.

        Args:
            project: Project instance
            include_assets: Whether to scan YAML/JSON assets too

        Returns:
            Comprehensive scan report
        """
        all_matches = []

        # Scan all documents
        for lang in project.languages:
            for chapter in project.list_chapters(lang):
                matches = self.scan_document(chapter)
                all_matches.extend(matches)

            # Scan scripts
            for script in project.list_scripts(lang):
                content = script.read_text()
                matches = self.scan_text(content, script)
                all_matches.extend(matches)

        # Optionally scan other content
        if include_assets:
            for yaml_file in project.content_dir.rglob("*.yaml"):
                content = yaml_file.read_text()
                matches = self.scan_text(content, yaml_file)
                all_matches.extend(matches)

        # Group by severity
        by_level = {level: [] for level in SensitivityLevel}
        for match in all_matches:
            by_level[match.level].append(match)

        return {
            "summary": {
                "total": len(all_matches),
                "critical": len(by_level[SensitivityLevel.CRITICAL]),
                "high": len(by_level[SensitivityLevel.HIGH]),
                "medium": len(by_level[SensitivityLevel.MEDIUM]),
                "low": len(by_level[SensitivityLevel.LOW]),
                "blocks_publish": len(by_level[SensitivityLevel.CRITICAL]) > 0,
            },
            "matches": [
                {
                    "file": str(m.file_path) if m.file_path else None,
                    "line": m.line_number,
                    "pattern": m.pattern_name,
                    "level": m.level.value,
                    "redacted": m.redacted_text,
                    "context": m.context,
                }
                for m in all_matches
            ],
            "by_file": self._group_by_file(all_matches),
        }

    def _group_by_file(self, matches: list[SensitiveMatch]) -> dict:
        """Group matches by file."""
        by_file = {}
        for match in matches:
            key = str(match.file_path) if match.file_path else "unknown"
            if key not in by_file:
                by_file[key] = []
            by_file[key].append(
                {
                    "line": match.line_number,
                    "pattern": match.pattern_name,
                    "level": match.level.value,
                }
            )
        return by_file


def scan_for_secrets(project, block_on_critical: bool = True) -> dict:
    """
    Convenience function to scan project for secrets.

    Args:
        project: Project instance
        block_on_critical: Whether to raise error on critical findings

    Returns:
        Scan report

    Raises:
        ValueError: If critical issues found and block_on_critical=True
    """
    scanner = SensitiveContentScanner()
    report = scanner.scan_project(project)

    if block_on_critical and report["summary"]["critical"] > 0:
        raise ValueError(
            f"Found {report['summary']['critical']} critical security issues. "
            "Cannot publish with exposed secrets."
        )

    return report


__all__ = [
    "SensitivityLevel",
    "SensitiveMatch",
    "SensitiveContentScanner",
    "scan_for_secrets",
    "PATTERNS",
]
