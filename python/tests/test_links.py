"""
Tests for the links module - link validation.
"""

import json
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from media_engine.links import (
    LinkCache,
    LinkChecker,
    LinkResult,
    LinkStatus,
    check_links,
)


class TestLinkStatus:
    """Tests for LinkStatus enum."""

    def test_status_values(self):
        """Test that all expected status values exist."""
        assert LinkStatus.VALID.value == "valid"
        assert LinkStatus.BROKEN.value == "broken"
        assert LinkStatus.TIMEOUT.value == "timeout"
        assert LinkStatus.REDIRECT.value == "redirect"
        assert LinkStatus.SKIPPED.value == "skipped"
        assert LinkStatus.UNKNOWN.value == "unknown"

    def test_status_is_string_enum(self):
        """Test that status is a string enum."""
        assert isinstance(LinkStatus.VALID, str)
        assert LinkStatus.VALID == "valid"


class TestLinkResult:
    """Tests for LinkResult dataclass."""

    def test_basic_result(self):
        """Test creating a basic result."""
        result = LinkResult(url="https://example.com", status=LinkStatus.VALID)
        assert result.url == "https://example.com"
        assert result.status == LinkStatus.VALID
        assert result.status_code is None
        assert result.error is None

    def test_result_with_all_fields(self):
        """Test result with all fields populated."""
        result = LinkResult(
            url="https://example.com",
            status=LinkStatus.REDIRECT,
            status_code=301,
            redirect_url="https://www.example.com",
            error=None,
            response_time_ms=150.5,
            source_file=Path("/test/file.md"),
            source_line=42,
        )
        assert result.status_code == 301
        assert result.redirect_url == "https://www.example.com"
        assert result.response_time_ms == 150.5
        assert result.source_line == 42

    def test_broken_result(self):
        """Test broken link result."""
        result = LinkResult(
            url="https://broken.example.com",
            status=LinkStatus.BROKEN,
            status_code=404,
            error="Not Found",
        )
        assert result.status == LinkStatus.BROKEN
        assert result.status_code == 404
        assert result.error == "Not Found"


class TestLinkCache:
    """Tests for LinkCache class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project with temp directory."""
        project = Mock()
        project.root = tmp_path
        return project

    def test_cache_init(self, mock_project):
        """Test cache initialization."""
        cache = LinkCache(mock_project)
        assert cache.project == mock_project
        assert cache.cache_dir == mock_project.root / ".media-engine"

    def test_cache_set_and_get(self, mock_project):
        """Test setting and getting cached results."""
        cache = LinkCache(mock_project)
        result = LinkResult(
            url="https://test.com",
            status=LinkStatus.VALID,
            status_code=200,
        )
        cache.set("https://test.com", result)

        cached = cache.get("https://test.com")
        assert cached is not None
        assert cached["status"] == "valid"
        assert cached["status_code"] == 200

    def test_cache_miss(self, mock_project):
        """Test cache miss returns None."""
        cache = LinkCache(mock_project)
        assert cache.get("https://nonexistent.com") is None

    def test_cache_clear(self, mock_project):
        """Test clearing the cache."""
        cache = LinkCache(mock_project)
        result = LinkResult(url="https://test.com", status=LinkStatus.VALID)
        cache.set("https://test.com", result)

        cache.clear()
        assert cache.get("https://test.com") is None

    def test_cache_persistence(self, mock_project):
        """Test cache persists to disk."""
        cache1 = LinkCache(mock_project)
        result = LinkResult(
            url="https://persist.com",
            status=LinkStatus.VALID,
            status_code=200,
        )
        cache1.set("https://persist.com", result)

        # Create new cache instance - should load from disk
        cache2 = LinkCache(mock_project)
        cached = cache2.get("https://persist.com")
        assert cached is not None
        assert cached["status"] == "valid"

    def test_cache_ttl_expiry(self, mock_project, tmp_path):
        """Test cache entries expire after TTL."""
        # Create cache file with old entry
        cache_dir = tmp_path / ".media-engine"
        cache_dir.mkdir()
        cache_file = cache_dir / "link_cache.json"

        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        cache_data = {
            "https://old.com": {
                "status": "valid",
                "status_code": 200,
                "cached_at": old_time,
            }
        }
        cache_file.write_text(json.dumps(cache_data))

        # Load cache - old entry should be expired
        cache = LinkCache(mock_project, ttl_hours=24)
        assert cache.get("https://old.com") is None


class TestLinkChecker:
    """Tests for LinkChecker class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        project.languages = ["en"]
        project.list_chapters = Mock(return_value=[])
        return project

    @pytest.fixture
    def checker(self, mock_project):
        """Create a checker instance with caching disabled."""
        return LinkChecker(mock_project, use_cache=False)

    def test_checker_init(self, mock_project):
        """Test checker initialization."""
        checker = LinkChecker(mock_project, timeout=15, max_workers=5)
        assert checker.timeout == 15
        assert checker.max_workers == 5
        assert "example.com" in checker.skip_domains

    def test_checker_custom_skip_domains(self, mock_project):
        """Test custom skip domains."""
        checker = LinkChecker(mock_project, skip_domains=["test.local"])
        assert "test.local" in checker.skip_domains

    # Link extraction tests
    def test_extract_markdown_links(self, checker):
        """Test extracting markdown links."""
        content = """
        Check out [Google](https://google.com) for more info.
        Also see [docs](/docs/guide.md) for details.
        """
        links = checker.extract_links(content)

        assert len(links) == 2
        assert any(l["url"] == "https://google.com" for l in links)
        assert any(l["url"] == "/docs/guide.md" for l in links)

    def test_extract_markdown_images(self, checker):
        """Test extracting markdown images."""
        content = """
        Here is an image: ![Alt text](https://example.com/image.png)
        Local image: ![Logo](/assets/logo.svg)
        """
        links = checker.extract_links(content)

        images = [l for l in links if l["type"] == "image"]
        assert len(images) == 2

    def test_extract_html_links(self, checker):
        """Test extracting HTML links."""
        content = """
        <a href="https://example.com">Link</a>
        <a href='/local/path'>Another</a>
        """
        links = checker.extract_links(content)

        html_links = [l for l in links if l["type"] == "html_link"]
        assert len(html_links) == 2

    def test_extract_links_with_source_info(self, checker):
        """Test that links include source file and line."""
        content = "Line 1\n[Link](https://test.com)\nLine 3"
        source = Path("/test/doc.md")

        links = checker.extract_links(content, source)
        assert links[0]["source_file"] == source
        assert links[0]["source_line"] == 2

    # URL classification tests
    def test_is_external(self, checker):
        """Test external URL detection."""
        assert checker.is_external("https://google.com")
        assert checker.is_external("http://example.com")
        assert not checker.is_external("/local/path")
        assert not checker.is_external("relative/path")
        assert not checker.is_external("#anchor")

    def test_should_skip(self, checker):
        """Test URL skip detection."""
        assert checker.should_skip("https://example.com/test")
        assert checker.should_skip("http://localhost:8080")
        assert checker.should_skip("http://127.0.0.1/api")
        assert not checker.should_skip("https://google.com")

    # External URL checking tests
    @patch("urllib.request.urlopen")
    def test_check_external_url_success(self, mock_urlopen, checker):
        """Test checking a successful external URL."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.url = "https://google.com"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = checker.check_external_url("https://google.com")
        assert result.status == LinkStatus.VALID
        assert result.status_code == 200

    def test_check_external_url_skipped(self, checker):
        """Test that skipped URLs return SKIPPED status."""
        result = checker.check_external_url("https://example.com/test")
        assert result.status == LinkStatus.SKIPPED

    @patch("urllib.request.urlopen")
    def test_check_external_url_404(self, mock_urlopen, checker):
        """Test checking a 404 URL."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://broken.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        result = checker.check_external_url("https://broken.com")
        assert result.status == LinkStatus.BROKEN
        assert result.status_code == 404

    @patch("urllib.request.urlopen")
    def test_check_external_url_network_error(self, mock_urlopen, checker):
        """Test checking URL with network error."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = checker.check_external_url("https://unreachable.com")
        assert result.status == LinkStatus.BROKEN
        assert "Connection refused" in result.error

    @patch("urllib.request.urlopen")
    def test_check_external_url_timeout(self, mock_urlopen, checker):
        """Test checking URL with timeout."""
        mock_urlopen.side_effect = TimeoutError()

        result = checker.check_external_url("https://slow.com")
        assert result.status == LinkStatus.TIMEOUT

    @patch("urllib.request.urlopen")
    def test_check_external_url_unknown_error(self, mock_urlopen, checker):
        """Test checking URL with unknown error."""
        mock_urlopen.side_effect = Exception("Unknown error")

        result = checker.check_external_url("https://weird.com")
        assert result.status == LinkStatus.UNKNOWN

    # Internal link checking tests
    def test_check_internal_link_anchor(self, checker, mock_project):
        """Test anchor links are always valid."""
        result = checker.check_internal_link("#section", Path("/test/doc.md"))
        assert result.status == LinkStatus.VALID

    def test_check_internal_link_exists(self, checker, mock_project):
        """Test internal link to existing file."""
        # Create target file
        target = mock_project.content_dir / "guide.md"
        target.write_text("# Guide")

        source = mock_project.content_dir / "index.md"
        result = checker.check_internal_link("guide.md", source)
        assert result.status == LinkStatus.VALID

    def test_check_internal_link_broken(self, checker, mock_project):
        """Test internal link to non-existent file."""
        source = mock_project.content_dir / "index.md"
        result = checker.check_internal_link("nonexistent.md", source)
        assert result.status == LinkStatus.BROKEN
        assert "not found" in result.error.lower()

    def test_check_internal_link_absolute(self, checker, mock_project):
        """Test absolute internal link."""
        target = mock_project.content_dir / "docs" / "api.md"
        target.parent.mkdir(parents=True)
        target.write_text("# API")

        source = mock_project.content_dir / "index.md"
        result = checker.check_internal_link("/docs/api.md", source)
        assert result.status == LinkStatus.VALID

    def test_check_internal_link_with_anchor(self, checker, mock_project):
        """Test internal link with anchor."""
        target = mock_project.content_dir / "guide.md"
        target.write_text("# Guide")

        source = mock_project.content_dir / "index.md"
        result = checker.check_internal_link("guide.md#section", source)
        assert result.status == LinkStatus.VALID


class TestLinkCheckerDocument:
    """Tests for checking entire documents."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        return project

    @pytest.fixture
    def checker(self, mock_project):
        """Create a checker instance."""
        return LinkChecker(mock_project, use_cache=False)

    def test_check_document(self, checker, mock_project, tmp_path):
        """Test checking a document with real Document class."""
        # Create a test document with proper frontmatter
        doc_path = tmp_path / "content" / "test.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_content = """---
title: Test
---

Check [local](other.md) link.
Check [anchor](#section) link.
"""
        doc_path.write_text(doc_content)

        # Create target file for internal link
        (tmp_path / "content" / "other.md").write_text("---\ntitle: Other\n---\n# Other")

        results = checker.check_document(doc_path)

        # Should find 2 links: local and anchor
        assert len(results) == 2
        # Anchor links are always valid, local file exists
        assert all(r.status == LinkStatus.VALID for r in results)


class TestLinkCheckerProject:
    """Tests for checking entire projects."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_check_project_internal_only(self, demo_project):
        """Test checking project internal links only."""
        checker = LinkChecker(demo_project, use_cache=False)
        result = checker.check_project(include_external=False)

        assert "summary" in result
        assert "total" in result["summary"]
        assert "broken_links" in result

    def test_check_project_summary_structure(self, demo_project):
        """Test project check summary structure."""
        checker = LinkChecker(demo_project, use_cache=False)
        result = checker.check_project(include_external=False)

        summary = result["summary"]
        assert "total" in summary
        assert "valid" in summary
        assert "broken" in summary
        assert "timeout" in summary


class TestCheckLinksFunction:
    """Tests for the convenience function."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_check_links_function(self, demo_project):
        """Test the check_links convenience function."""
        result = check_links(demo_project, include_external=False)
        assert "summary" in result
        assert "broken_links" in result


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project."""
        project = Mock()
        project.root = tmp_path
        project.content_dir = tmp_path / "content"
        project.content_dir.mkdir()
        return project

    @pytest.fixture
    def checker(self, mock_project):
        """Create a checker instance."""
        return LinkChecker(mock_project, use_cache=False)

    def test_empty_content(self, checker):
        """Test extracting links from empty content."""
        links = checker.extract_links("")
        assert links == []

    def test_no_links_in_content(self, checker):
        """Test content with no links."""
        content = "Just some plain text without any links."
        links = checker.extract_links(content)
        assert links == []

    def test_malformed_markdown_link(self, checker):
        """Test malformed markdown link is not extracted."""
        content = "[broken link(https://example.com)"
        links = checker.extract_links(content)
        assert len(links) == 0

    def test_link_in_code_block(self, checker):
        """Test links in code blocks are still extracted."""
        content = """
        ```python
        url = "https://example.com"
        ```
        """
        # Note: The current implementation doesn't skip code blocks
        # This test documents current behavior
        checker.extract_links(content)
        # HTML patterns might match quotes
        # Just verify no crash

    def test_multiple_links_same_line(self, checker):
        """Test multiple links on same line."""
        content = "[A](https://a.com) and [B](https://b.com)"
        links = checker.extract_links(content)
        assert len(links) == 2

    def test_nested_brackets(self, checker):
        """Test handling of nested brackets."""
        content = "[[not a link]](https://test.com)"
        checker.extract_links(content)
        # Regex may or may not match this - just verify no crash

    def test_special_characters_in_url(self, checker):
        """Test URLs with special characters."""
        content = "[Link](https://example.com/path?q=1&x=2#anchor)"
        links = checker.extract_links(content)
        assert len(links) == 1
        assert "?q=1&x=2#anchor" in links[0]["url"]

    def test_unicode_in_link_text(self, checker):
        """Test unicode in link text."""
        content = "[Les mer her](https://example.com)"
        links = checker.extract_links(content)
        assert len(links) == 1
        assert "Les mer her" in links[0]["text"]

    def test_data_uri_scheme(self, checker):
        """Test data URI is not external."""
        assert not checker.is_external("data:image/png;base64,...")

    def test_mailto_link(self, checker):
        """Test mailto link is not external."""
        assert not checker.is_external("mailto:test@example.com")

    def test_javascript_link(self, checker):
        """Test javascript link is not external."""
        assert not checker.is_external("javascript:void(0)")

    def test_cache_with_redirect(self, mock_project):
        """Test caching redirect results."""
        cache = LinkCache(mock_project)
        result = LinkResult(
            url="https://old.com",
            status=LinkStatus.REDIRECT,
            status_code=301,
            redirect_url="https://new.com",
        )
        cache.set("https://old.com", result)

        cached = cache.get("https://old.com")
        assert cached["redirect_url"] == "https://new.com"
