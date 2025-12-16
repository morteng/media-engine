"""
Tests for the security module - sensitive content detection.
"""

import pytest
from pathlib import Path
import tempfile

from media_engine.security import (
    SensitivityLevel,
    SensitiveMatch,
    SensitiveContentScanner,
    scan_for_secrets,
    PATTERNS,
)


class TestSensitivityLevel:
    """Tests for SensitivityLevel enum."""

    def test_levels_exist(self):
        """Test that all expected levels exist."""
        assert SensitivityLevel.CRITICAL == "critical"
        assert SensitivityLevel.HIGH == "high"
        assert SensitivityLevel.MEDIUM == "medium"
        assert SensitivityLevel.LOW == "low"

    def test_levels_are_strings(self):
        """Test that levels are string enums."""
        assert isinstance(SensitivityLevel.CRITICAL, str)
        assert SensitivityLevel.CRITICAL.value == "critical"


class TestSensitiveMatch:
    """Tests for SensitiveMatch dataclass."""

    def test_create_match(self):
        """Test creating a SensitiveMatch."""
        match = SensitiveMatch(
            pattern_name="test_pattern",
            matched_text="secret123",
            redacted_text="se*****23",
            line_number=10,
            column=5,
            level=SensitivityLevel.HIGH,
            file_path=Path("/test/file.md"),
            context="the secret123 is here",
        )
        assert match.pattern_name == "test_pattern"
        assert match.matched_text == "secret123"
        assert match.line_number == 10
        assert match.level == SensitivityLevel.HIGH

    def test_match_without_file_path(self):
        """Test creating a match without file path."""
        match = SensitiveMatch(
            pattern_name="test",
            matched_text="test",
            redacted_text="****",
            line_number=1,
            column=1,
            level=SensitivityLevel.LOW,
        )
        assert match.file_path is None
        assert match.context == ""


class TestPatterns:
    """Tests for the PATTERNS dictionary."""

    def test_patterns_exist(self):
        """Test that expected patterns exist."""
        expected = [
            "aws_access_key",
            "github_token",
            "openai_key",
            "anthropic_key",
            "email",
            "ssn",
            "ipv4_private",
        ]
        for pattern_name in expected:
            assert pattern_name in PATTERNS, f"Pattern {pattern_name} not found"

    def test_pattern_structure(self):
        """Test that patterns have required fields."""
        for name, config in PATTERNS.items():
            assert "pattern" in config, f"Pattern {name} missing 'pattern' field"
            assert "level" in config, f"Pattern {name} missing 'level' field"
            assert "description" in config, f"Pattern {name} missing 'description' field"
            assert isinstance(config["level"], SensitivityLevel)


class TestSensitiveContentScanner:
    """Tests for SensitiveContentScanner class."""

    @pytest.fixture
    def scanner(self):
        """Create a scanner instance."""
        return SensitiveContentScanner()

    # === API Key Detection ===

    def test_detect_aws_access_key(self, scanner):
        """Test AWS access key detection."""
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        aws_match = next((m for m in matches if m.pattern_name == "aws_access_key"), None)
        assert aws_match is not None
        assert aws_match.level == SensitivityLevel.CRITICAL

    def test_detect_github_token(self, scanner):
        """Test GitHub token detection."""
        text = "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        gh_match = next((m for m in matches if m.pattern_name == "github_token"), None)
        assert gh_match is not None
        assert gh_match.level == SensitivityLevel.CRITICAL

    def test_detect_github_pat(self, scanner):
        """Test GitHub PAT detection."""
        text = "token: github_pat_ABCDEFGHIJKLMNOPQRSTUVa"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        pat_match = next((m for m in matches if m.pattern_name == "github_pat"), None)
        assert pat_match is not None

    def test_detect_openai_key(self, scanner):
        """Test OpenAI API key detection."""
        text = "OPENAI_API_KEY=sk-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        openai_match = next((m for m in matches if m.pattern_name == "openai_key"), None)
        assert openai_match is not None
        assert openai_match.level == SensitivityLevel.CRITICAL

    def test_detect_anthropic_key(self, scanner):
        """Test Anthropic API key detection."""
        text = "key = sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        ant_match = next((m for m in matches if m.pattern_name == "anthropic_key"), None)
        assert ant_match is not None
        assert ant_match.level == SensitivityLevel.CRITICAL

    # Stripe key test removed - live key patterns trigger GitHub push protection

    def test_detect_slack_token(self, scanner):
        """Test Slack token detection."""
        text = "SLACK_TOKEN=xoxb-123456789012-1234567890123"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        slack_match = next((m for m in matches if m.pattern_name == "slack_token"), None)
        assert slack_match is not None

    def test_detect_generic_api_key(self, scanner):
        """Test generic API key detection."""
        text = "api_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZa'"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        generic_match = next((m for m in matches if m.pattern_name == "generic_api_key"), None)
        assert generic_match is not None

    def test_detect_bearer_token(self, scanner):
        """Test Bearer token detection."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        bearer_match = next((m for m in matches if m.pattern_name == "bearer_token"), None)
        assert bearer_match is not None

    def test_detect_jwt_token(self, scanner):
        """Test JWT token detection."""
        text = "token = eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        jwt_match = next((m for m in matches if m.pattern_name == "jwt_token"), None)
        assert jwt_match is not None

    # === PII Detection ===

    def test_detect_email(self, scanner):
        """Test email detection."""
        text = "Contact: john.doe@company.com for more info"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        email_match = next((m for m in matches if m.pattern_name == "email"), None)
        assert email_match is not None
        assert email_match.level == SensitivityLevel.MEDIUM

    def test_email_exceptions(self, scanner):
        """Test that example emails are not flagged."""
        text = "Use test@example.com for testing"
        matches = scanner.scan_text(text)
        email_matches = [m for m in matches if m.pattern_name == "email"]
        assert len(email_matches) == 0

    def test_detect_phone_us(self, scanner):
        """Test US phone number detection."""
        text = "Call us at (555) 123-4567"
        matches = scanner.scan_text(text)
        phone_match = next((m for m in matches if m.pattern_name == "phone_us"), None)
        assert phone_match is not None
        assert phone_match.level == SensitivityLevel.MEDIUM

    def test_detect_phone_intl(self, scanner):
        """Test international phone detection."""
        text = "Contact: +47 12345678"
        matches = scanner.scan_text(text)
        phone_match = next((m for m in matches if m.pattern_name == "phone_intl"), None)
        assert phone_match is not None

    def test_detect_ssn(self, scanner):
        """Test SSN detection."""
        text = "SSN: 123-45-6789"
        matches = scanner.scan_text(text)
        ssn_match = next((m for m in matches if m.pattern_name == "ssn"), None)
        assert ssn_match is not None
        assert ssn_match.level == SensitivityLevel.CRITICAL

    def test_detect_credit_card(self, scanner):
        """Test credit card detection."""
        # Visa test number
        text = "Card: 4111111111111111"
        matches = scanner.scan_text(text)
        cc_match = next((m for m in matches if m.pattern_name == "credit_card"), None)
        assert cc_match is not None
        assert cc_match.level == SensitivityLevel.CRITICAL

    # === Network Detection ===

    def test_detect_private_ip(self, scanner):
        """Test private IP detection."""
        text = "Server at 192.168.1.100"
        matches = scanner.scan_text(text)
        ip_match = next((m for m in matches if m.pattern_name == "ipv4_private"), None)
        assert ip_match is not None
        assert ip_match.level == SensitivityLevel.MEDIUM

    def test_detect_private_ip_10_range(self, scanner):
        """Test 10.x.x.x range detection."""
        text = "Internal: 10.0.0.1"
        matches = scanner.scan_text(text)
        ip_match = next((m for m in matches if m.pattern_name == "ipv4_private"), None)
        assert ip_match is not None

    def test_detect_internal_url(self, scanner):
        """Test internal URL detection."""
        text = "API: http://localhost:8080/api"
        matches = scanner.scan_text(text)
        url_match = next((m for m in matches if m.pattern_name == "internal_url"), None)
        assert url_match is not None
        assert url_match.level == SensitivityLevel.MEDIUM

    # === File Path Detection ===

    def test_detect_unix_home_path(self, scanner):
        """Test Unix home path detection."""
        text = "Config at /home/username/config.yaml"
        matches = scanner.scan_text(text)
        path_match = next((m for m in matches if m.pattern_name == "unix_home"), None)
        assert path_match is not None
        assert path_match.level == SensitivityLevel.LOW

    def test_detect_windows_path(self, scanner):
        """Test Windows path detection."""
        text = "File: C:\\Users\\John\\Documents\\secrets.txt"
        matches = scanner.scan_text(text)
        path_match = next((m for m in matches if m.pattern_name == "windows_path"), None)
        assert path_match is not None

    # === Redaction ===

    def test_redaction_short_text(self, scanner):
        """Test redaction of short text."""
        redacted = scanner._redact("pass", "test")
        assert redacted == "****"

    def test_redaction_long_text(self, scanner):
        """Test redaction of longer text."""
        redacted = scanner._redact("mysecretpassword", "test")
        assert redacted.startswith("my")
        assert redacted.endswith("rd")
        assert "*" in redacted

    # === Multi-line Scanning ===

    def test_multiline_scan(self, scanner):
        """Test scanning multiple lines."""
        text = """
        Line 1: nothing here
        Line 2: email is test@company.com
        Line 3: more text
        Line 4: SSN is 123-45-6789
        """
        matches = scanner.scan_text(text)
        assert len(matches) >= 2

        email_match = next((m for m in matches if m.pattern_name == "email"), None)
        assert email_match is not None
        assert email_match.line_number == 3

        ssn_match = next((m for m in matches if m.pattern_name == "ssn"), None)
        assert ssn_match is not None
        assert ssn_match.line_number == 5

    # === Context ===

    def test_match_includes_context(self, scanner):
        """Test that matches include surrounding context."""
        text = "The password = 'secretpass123' in this line"
        matches = scanner.scan_text(text)
        assert len(matches) >= 1
        assert any("password" in m.context.lower() for m in matches)

    # === Custom Patterns ===

    def test_custom_patterns(self):
        """Test adding custom patterns."""
        custom = {
            "custom_key": {
                "pattern": r"CUSTOM-[A-Z]{10}",
                "level": SensitivityLevel.HIGH,
                "description": "Custom Key",
            }
        }
        scanner = SensitiveContentScanner(custom_patterns=custom)
        text = "Key: CUSTOM-ABCDEFGHIJ"
        matches = scanner.scan_text(text)
        custom_match = next((m for m in matches if m.pattern_name == "custom_key"), None)
        assert custom_match is not None

    def test_ignore_patterns(self):
        """Test ignoring specific patterns."""
        scanner = SensitiveContentScanner(ignore_patterns=["email"])
        text = "Contact: test@company.com"
        matches = scanner.scan_text(text)
        email_matches = [m for m in matches if m.pattern_name == "email"]
        assert len(email_matches) == 0

    # === File Path Parameter ===

    def test_scan_with_file_path(self, scanner):
        """Test that file path is included in matches."""
        text = "SSN: 123-45-6789"
        test_path = Path("/test/document.md")
        matches = scanner.scan_text(text, file_path=test_path)
        assert len(matches) >= 1
        assert matches[0].file_path == test_path


class TestScanDocument:
    """Tests for scanning document files."""

    @pytest.fixture
    def scanner(self):
        return SensitiveContentScanner()

    @pytest.fixture
    def temp_md_file(self, tmp_path):
        """Create a temporary markdown file."""
        content = """---
title: Test Document
author: test@company.com
---

# Test

API Key: sk-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv
"""
        file_path = tmp_path / "test.md"
        file_path.write_text(content)
        return file_path

    def test_scan_document(self, scanner, temp_md_file):
        """Test scanning a markdown document."""
        matches = scanner.scan_document(temp_md_file)
        assert len(matches) >= 1
        # Should find the OpenAI key in content
        openai_match = next((m for m in matches if m.pattern_name == "openai_key"), None)
        assert openai_match is not None

    def test_scan_document_metadata(self, scanner, temp_md_file):
        """Test that metadata is also scanned."""
        matches = scanner.scan_document(temp_md_file)
        # Should find the email in metadata
        email_match = next((m for m in matches if m.pattern_name == "email"), None)
        assert email_match is not None


class TestScanForSecrets:
    """Tests for the scan_for_secrets convenience function."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        from media_engine.core import find_project
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project
        return Project.load(demo_path)

    def test_scan_project_returns_report(self, demo_project):
        """Test that scan_for_secrets returns a report."""
        report = scan_for_secrets(demo_project, block_on_critical=False)
        assert "summary" in report
        assert "matches" in report
        assert "by_file" in report

    def test_report_summary_structure(self, demo_project):
        """Test report summary structure."""
        report = scan_for_secrets(demo_project, block_on_critical=False)
        summary = report["summary"]
        assert "total" in summary
        assert "critical" in summary
        assert "high" in summary
        assert "medium" in summary
        assert "low" in summary
        assert "blocks_publish" in summary

    def test_block_on_critical(self, tmp_path):
        """Test that critical findings can block."""
        # Create a project with a secret
        content_dir = tmp_path / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)

        # Create project files
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text("""
name: Test Project
source_language: en
languages:
  en:
    name: English
paths:
  content: content
""")

        # Create a document with a critical secret
        doc = content_dir / "01_test.md"
        doc.write_text("""---
title: Test
---

# Test

SSN: 123-45-6789
""")

        from media_engine.core.project import Project
        project = Project.load(tmp_path)

        with pytest.raises(ValueError, match="critical security issues"):
            scan_for_secrets(project, block_on_critical=True)

    def test_no_block_when_clean(self, demo_project):
        """Test that clean projects don't block."""
        # Demo project should be clean
        report = scan_for_secrets(demo_project, block_on_critical=True)
        assert report["summary"]["critical"] == 0


class TestCleanContent:
    """Tests to verify clean content is not flagged."""

    @pytest.fixture
    def scanner(self):
        return SensitiveContentScanner()

    def test_clean_markdown_not_flagged(self, scanner):
        """Test that normal markdown content is not flagged."""
        text = """
        # Introduction

        This is a normal document about APIs.
        We discuss authentication but don't include real keys.

        ## Configuration

        Set your API key in environment variables:
        ```
        export API_KEY=your-api-key-here
        ```
        """
        matches = scanner.scan_text(text)
        # Should have no critical matches
        critical = [m for m in matches if m.level == SensitivityLevel.CRITICAL]
        assert len(critical) == 0

    def test_placeholder_values_not_critical(self, scanner):
        """Test that placeholder values are handled correctly."""
        text = "api_key = 'your-api-key-here'"
        matches = scanner.scan_text(text)
        critical = [m for m in matches if m.level == SensitivityLevel.CRITICAL]
        assert len(critical) == 0
