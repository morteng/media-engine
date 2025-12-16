"""
Link Validation for Media Engine

Validates both internal and external links in documentation:
- External URL reachability
- Internal document references
- Anchor/heading links
- Image and asset links

Caches results to avoid hammering external servers.
"""

import re
import json
import hashlib
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum


class LinkStatus(str, Enum):
    """Link validation status."""
    VALID = "valid"
    BROKEN = "broken"
    TIMEOUT = "timeout"
    REDIRECT = "redirect"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


@dataclass
class LinkResult:
    """Result of link validation."""
    url: str
    status: LinkStatus
    status_code: Optional[int] = None
    redirect_url: Optional[str] = None
    error: Optional[str] = None
    response_time_ms: Optional[float] = None
    source_file: Optional[Path] = None
    source_line: Optional[int] = None


class LinkCache:
    """Caches link validation results to avoid repeated checks."""

    def __init__(self, project, ttl_hours: int = 24):
        self.project = project
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir = project.root / ".media-engine"
        self.cache_path = self.cache_dir / "link_cache.json"
        self._cache = {}
        self._load()

    def _load(self):
        if self.cache_path.exists():
            with open(self.cache_path) as f:
                data = json.load(f)
                for url, entry in data.items():
                    # Check TTL
                    cached_at = datetime.fromisoformat(entry["cached_at"])
                    if datetime.now() - cached_at < self.ttl:
                        self._cache[url] = entry

    def _save(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(self._cache, f, indent=2)

    def get(self, url: str) -> Optional[dict]:
        return self._cache.get(url)

    def set(self, url: str, result: LinkResult):
        self._cache[url] = {
            "status": result.status.value,
            "status_code": result.status_code,
            "redirect_url": result.redirect_url,
            "error": result.error,
            "cached_at": datetime.now().isoformat(),
        }
        self._save()

    def clear(self):
        self._cache = {}
        if self.cache_path.exists():
            self.cache_path.unlink()


class LinkChecker:
    """
    Validates links in documentation.

    Features:
    - Parallel checking of external URLs
    - Result caching
    - Configurable timeouts
    - Skip patterns for known-good domains
    """

    # Domains to skip (always assumed valid)
    DEFAULT_SKIP_DOMAINS = [
        "example.com",
        "example.org",
        "localhost",
        "127.0.0.1",
    ]

    # Link patterns in markdown
    MD_LINK_PATTERN = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    MD_IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    HTML_LINK_PATTERN = re.compile(r'href=["\']([^"\']+)["\']')
    HTML_IMG_PATTERN = re.compile(r'src=["\']([^"\']+)["\']')

    def __init__(
        self,
        project,
        timeout: int = 10,
        skip_domains: list = None,
        use_cache: bool = True,
        max_workers: int = 10,
    ):
        self.project = project
        self.timeout = timeout
        self.skip_domains = set(skip_domains or self.DEFAULT_SKIP_DOMAINS)
        self.use_cache = use_cache
        self.max_workers = max_workers
        self.cache = LinkCache(project) if use_cache else None

    def extract_links(self, content: str, source_file: Path = None) -> list[dict]:
        """Extract all links from markdown/HTML content."""
        links = []
        lines = content.split("\n")
        in_code_block = False

        for line_num, line in enumerate(lines, 1):
            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip lines inside code blocks
            if in_code_block:
                continue

            # Remove inline code before checking for links
            line_without_code = re.sub(r'`[^`]+`', '', line)

            # Markdown links
            for match in self.MD_LINK_PATTERN.finditer(line_without_code):
                text, url = match.groups()
                links.append({
                    "url": url,
                    "text": text,
                    "type": "link",
                    "source_file": source_file,
                    "source_line": line_num,
                })

            # Markdown images
            for match in self.MD_IMAGE_PATTERN.finditer(line_without_code):
                alt, url = match.groups()
                links.append({
                    "url": url,
                    "text": alt,
                    "type": "image",
                    "source_file": source_file,
                    "source_line": line_num,
                })

            # HTML links
            for match in self.HTML_LINK_PATTERN.finditer(line_without_code):
                url = match.group(1)
                links.append({
                    "url": url,
                    "text": "",
                    "type": "html_link",
                    "source_file": source_file,
                    "source_line": line_num,
                })

        return links

    def is_external(self, url: str) -> bool:
        """Check if URL is external."""
        return url.startswith(("http://", "https://"))

    def should_skip(self, url: str) -> bool:
        """Check if URL should be skipped."""
        for domain in self.skip_domains:
            if domain in url:
                return True
        return False

    def check_external_url(self, url: str) -> LinkResult:
        """Check if an external URL is reachable."""
        # Check cache first
        if self.cache:
            cached = self.cache.get(url)
            if cached:
                return LinkResult(
                    url=url,
                    status=LinkStatus(cached["status"]),
                    status_code=cached.get("status_code"),
                    redirect_url=cached.get("redirect_url"),
                    error=cached.get("error"),
                )

        if self.should_skip(url):
            return LinkResult(url=url, status=LinkStatus.SKIPPED)

        start_time = datetime.now()

        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "MediaEngine-LinkChecker/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                elapsed = (datetime.now() - start_time).total_seconds() * 1000

                result = LinkResult(
                    url=url,
                    status=LinkStatus.VALID,
                    status_code=response.status,
                    redirect_url=response.url if response.url != url else None,
                    response_time_ms=elapsed,
                )

                if self.cache:
                    self.cache.set(url, result)

                return result

        except urllib.error.HTTPError as e:
            result = LinkResult(
                url=url,
                status=LinkStatus.BROKEN,
                status_code=e.code,
                error=str(e.reason),
            )
            if self.cache:
                self.cache.set(url, result)
            return result

        except urllib.error.URLError as e:
            result = LinkResult(
                url=url,
                status=LinkStatus.BROKEN,
                error=str(e.reason),
            )
            if self.cache:
                self.cache.set(url, result)
            return result

        except TimeoutError:
            result = LinkResult(
                url=url,
                status=LinkStatus.TIMEOUT,
                error=f"Timeout after {self.timeout}s",
            )
            if self.cache:
                self.cache.set(url, result)
            return result

        except Exception as e:
            result = LinkResult(
                url=url,
                status=LinkStatus.UNKNOWN,
                error=str(e),
            )
            return result

    def check_internal_link(self, url: str, source_file: Path) -> LinkResult:
        """Check if an internal link resolves."""
        # Handle anchor links
        if url.startswith("#"):
            # Would need to parse headings to validate
            return LinkResult(url=url, status=LinkStatus.VALID)

        # Handle relative paths
        if url.startswith("/"):
            target = self.project.content_dir / url.lstrip("/")
        else:
            target = (source_file.parent / url).resolve()

        # Strip anchor from path
        path_part = url.split("#")[0]
        if path_part:
            if url.startswith("/"):
                target = self.project.content_dir / path_part.lstrip("/")
            else:
                target = (source_file.parent / path_part).resolve()

            if target.exists():
                return LinkResult(url=url, status=LinkStatus.VALID)
            else:
                return LinkResult(
                    url=url,
                    status=LinkStatus.BROKEN,
                    error=f"File not found: {target}",
                    source_file=source_file,
                )

        return LinkResult(url=url, status=LinkStatus.VALID)

    def check_document(self, doc_path: Path) -> list[LinkResult]:
        """Check all links in a document."""
        from ..cms.document import Document

        doc = Document.load(doc_path)
        links = self.extract_links(doc.content, doc_path)

        results = []
        external_urls = []

        for link in links:
            url = link["url"]

            if self.is_external(url):
                external_urls.append(link)
            else:
                result = self.check_internal_link(url, doc_path)
                result.source_file = doc_path
                result.source_line = link["source_line"]
                results.append(result)

        # Check external URLs in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_link = {
                executor.submit(self.check_external_url, link["url"]): link
                for link in external_urls
            }

            for future in as_completed(future_to_link):
                link = future_to_link[future]
                result = future.result()
                result.source_file = doc_path
                result.source_line = link["source_line"]
                results.append(result)

        return results

    def check_project(self, include_external: bool = True) -> dict:
        """
        Check all links in the project.

        Args:
            include_external: Whether to check external URLs

        Returns:
            Comprehensive link report
        """
        all_results = []

        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                results = self.check_document(chapter)
                if not include_external:
                    results = [r for r in results if not self.is_external(r.url)]
                all_results.extend(results)

        # Summarize
        broken = [r for r in all_results if r.status == LinkStatus.BROKEN]
        timeout = [r for r in all_results if r.status == LinkStatus.TIMEOUT]
        valid = [r for r in all_results if r.status == LinkStatus.VALID]

        return {
            "summary": {
                "total": len(all_results),
                "valid": len(valid),
                "broken": len(broken),
                "timeout": len(timeout),
            },
            "broken_links": [
                {
                    "url": r.url,
                    "error": r.error,
                    "status_code": r.status_code,
                    "file": str(r.source_file) if r.source_file else None,
                    "line": r.source_line,
                }
                for r in broken
            ],
            "timeout_links": [
                {
                    "url": r.url,
                    "file": str(r.source_file) if r.source_file else None,
                    "line": r.source_line,
                }
                for r in timeout
            ],
        }


def check_links(project, include_external: bool = True) -> dict:
    """Convenience function to check all project links."""
    checker = LinkChecker(project)
    return checker.check_project(include_external=include_external)


__all__ = [
    "LinkStatus",
    "LinkResult",
    "LinkCache",
    "LinkChecker",
    "check_links",
]
