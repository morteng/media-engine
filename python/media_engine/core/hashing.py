"""
Unified content hashing utilities.

All modules should use these functions for consistent hash computation
across the entire Media Engine codebase.

Hash format: SHA256, truncated to 16 characters (64 bits)
This provides sufficient collision resistance for content identification
while keeping hashes compact for display and storage.
"""

import hashlib
from pathlib import Path
from typing import Union

# Standard hash length for all content hashes
HASH_LENGTH = 16


def compute_content_hash(content: str) -> str:
    """
    Compute a content hash from a string.

    Normalizes whitespace before hashing for consistency.

    Args:
        content: String content to hash

    Returns:
        16-character hex hash
    """
    # Normalize whitespace
    normalized = " ".join(content.split()).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:HASH_LENGTH]


def compute_raw_hash(data: Union[str, bytes]) -> str:
    """
    Compute a hash from raw data without normalization.

    Use this for binary content or when whitespace matters.

    Args:
        data: String or bytes to hash

    Returns:
        16-character hex hash
    """
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()[:HASH_LENGTH]


def compute_file_hash(file_path: Path) -> str:
    """
    Compute a hash from a file's binary content.

    Reads file in chunks for memory efficiency with large files.

    Args:
        file_path: Path to file

    Returns:
        16-character hex hash
    """
    if not file_path.exists():
        return ""

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:HASH_LENGTH]


def compute_document_hash(doc_path: Path) -> str:
    """
    Compute a content hash for a document file.

    For markdown files, excludes frontmatter from the hash
    so that metadata changes don't affect the content hash.

    Args:
        doc_path: Path to document file

    Returns:
        16-character hex hash
    """
    if not doc_path.exists():
        return ""

    content = doc_path.read_text(encoding="utf-8")

    # Strip frontmatter for markdown files
    if doc_path.suffix == ".md" and content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]

    return compute_content_hash(content)


def compute_short_hash(content: str, length: int = 8) -> str:
    """
    Compute a short hash for identifiers.

    Use this for IDs where 8 characters is sufficient
    (e.g., claim IDs, note IDs).

    Args:
        content: String to hash
        length: Number of hex characters (default 8)

    Returns:
        Truncated hex hash
    """
    return hashlib.sha256(content.encode()).hexdigest()[:length]


def verify_hash(content: str, expected_hash: str) -> bool:
    """
    Verify content matches an expected hash.

    Args:
        content: Content to verify
        expected_hash: Expected hash value

    Returns:
        True if hash matches
    """
    actual = compute_content_hash(content)
    return actual == expected_hash


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """
    Verify a file matches an expected hash.

    Args:
        file_path: Path to file
        expected_hash: Expected hash value

    Returns:
        True if hash matches
    """
    actual = compute_file_hash(file_path)
    return actual == expected_hash
