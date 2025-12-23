"""
Duplicate & Similar Content Detection

Detects duplicated or highly similar content across documents, helping reduce
maintenance burden and improve content consistency.

Detection methods:
- Exact duplicate detection (identical text blocks)
- Near-duplicate detection (>80% similarity)
- Concept repetition (same topic explained multiple times)
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.hashing import compute_content_hash
from ..core.project import Project


@dataclass
class ContentLocation:
    """Location of a content block."""

    document: Path
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
        }


@dataclass
class DuplicateMatch:
    """A detected duplicate content match."""

    match_type: str  # "exact", "similar", "concept"
    similarity: float  # 0.0 - 1.0
    locations: list[ContentLocation]
    content_preview: str
    recommendation: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "match_type": self.match_type,
            "similarity": self.similarity,
            "locations": [loc.to_dict() for loc in self.locations],
            "content_preview": self.content_preview,
            "recommendation": self.recommendation,
        }


@dataclass
class DuplicateReport:
    """Complete duplicate detection report."""

    exact_duplicates: list[DuplicateMatch]
    similar_content: list[DuplicateMatch]
    concept_repetition: list[DuplicateMatch]
    total_issues: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "exact_duplicates": [d.to_dict() for d in self.exact_duplicates],
            "similar_content": [d.to_dict() for d in self.similar_content],
            "concept_repetition": [d.to_dict() for d in self.concept_repetition],
            "total_issues": self.total_issues,
        }


@dataclass
class DuplicateDetector:
    """
    Detects duplicate and similar content across documents.

    Usage:
        detector = DuplicateDetector(project)
        duplicates = detector.find_exact_duplicates()
        similar = detector.find_similar_content(threshold=0.8)
    """

    project: Project
    min_words: int = 50  # Minimum words for duplicate detection
    similarity_threshold: float = 0.8  # Default similarity threshold

    def find_exact_duplicates(self, min_words: Optional[int] = None) -> list[DuplicateMatch]:
        """
        Find exact duplicate text blocks.

        Args:
            min_words: Minimum words for a block to be considered

        Returns:
            List of DuplicateMatch instances
        """
        min_words = min_words or self.min_words
        duplicates: list[DuplicateMatch] = []

        # Hash -> list of locations
        content_hashes: dict[str, list[ContentLocation]] = defaultdict(list)

        if not self.project.content_dir.exists():
            return duplicates

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel_path = md_file.relative_to(self.project.content_dir)

                # Extract paragraphs
                paragraphs = self._extract_paragraphs(content)

                for para in paragraphs:
                    if len(para["text"].split()) >= min_words:
                        # Normalize and hash
                        normalized = self._normalize_text(para["text"])
                        hash_key = compute_content_hash(normalized)

                        content_hashes[hash_key].append(
                            ContentLocation(
                                document=rel_path,
                                start_line=para["start_line"],
                                end_line=para["end_line"],
                                text=para["text"],
                            )
                        )

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Find hashes with multiple locations
        for hash_key, locations in content_hashes.items():
            if len(locations) > 1:
                duplicates.append(
                    DuplicateMatch(
                        match_type="exact",
                        similarity=1.0,
                        locations=locations,
                        content_preview=locations[0].text[:200],
                        recommendation="Consider extracting to shared include or cross-referencing",
                    )
                )

        return duplicates

    def find_similar_content(self, threshold: Optional[float] = None) -> list[DuplicateMatch]:
        """
        Find semantically similar paragraphs.

        Args:
            threshold: Minimum similarity score (0.0 - 1.0)

        Returns:
            List of DuplicateMatch instances
        """
        threshold = threshold or self.similarity_threshold
        similar: list[DuplicateMatch] = []

        # Collect all paragraphs with their locations
        paragraphs: list[tuple[ContentLocation, set[str]]] = []

        if not self.project.content_dir.exists():
            return similar

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel_path = md_file.relative_to(self.project.content_dir)

                for para in self._extract_paragraphs(content):
                    if len(para["text"].split()) >= self.min_words:
                        # Create word set for Jaccard similarity
                        words = set(self._normalize_text(para["text"]).split())
                        location = ContentLocation(
                            document=rel_path,
                            start_line=para["start_line"],
                            end_line=para["end_line"],
                            text=para["text"],
                        )
                        paragraphs.append((location, words))

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Compare all pairs (optimize for large projects)
        seen_pairs: set[frozenset] = set()

        for i, (loc1, words1) in enumerate(paragraphs):
            for j, (loc2, words2) in enumerate(paragraphs[i + 1 :], i + 1):
                # Skip if same document
                if loc1.document == loc2.document:
                    continue

                # Skip if already compared
                pair_key = frozenset(
                    [f"{loc1.document}:{loc1.start_line}", f"{loc2.document}:{loc2.start_line}"]
                )
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Calculate Jaccard similarity
                similarity = self._jaccard_similarity(words1, words2)

                if similarity >= threshold and similarity < 1.0:  # Exclude exact matches
                    similar.append(
                        DuplicateMatch(
                            match_type="similar",
                            similarity=round(similarity, 2),
                            locations=[loc1, loc2],
                            content_preview=f"Doc 1: {loc1.text[:100]}...\nDoc 2: {loc2.text[:100]}...",
                            recommendation="Consolidate or cross-reference similar content",
                        )
                    )

        # Sort by similarity (highest first)
        similar.sort(key=lambda x: -x.similarity)

        return similar

    def find_concept_repetition(self, concepts: Optional[list[str]] = None) -> list[DuplicateMatch]:
        """
        Find the same concept explained multiple times.

        Args:
            concepts: List of concept keywords to check

        Returns:
            List of DuplicateMatch instances
        """
        repetitions: list[DuplicateMatch] = []

        # Default concepts to look for
        if concepts is None:
            concepts = self._detect_key_concepts()

        if not self.project.content_dir.exists():
            return repetitions

        for concept in concepts:
            locations: list[ContentLocation] = []
            concept_pattern = re.compile(rf"\b{re.escape(concept)}\b", re.IGNORECASE)

            for md_file in self.project.content_dir.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    rel_path = md_file.relative_to(self.project.content_dir)

                    # Find sections that explain this concept
                    for section in self._extract_sections(content):
                        title = section["title"].lower()
                        section["body"].lower()

                        # Check if section is about this concept
                        if concept.lower() in title or (
                            concept_pattern.search(section["body"])
                            and len(section["body"].split()) > 100
                        ):
                            locations.append(
                                ContentLocation(
                                    document=rel_path,
                                    start_line=section["start_line"],
                                    end_line=section["end_line"],
                                    text=section["body"][:300],
                                )
                            )

                except (OSError, UnicodeDecodeError, ValueError):
                    pass

            if len(locations) > 1:
                repetitions.append(
                    DuplicateMatch(
                        match_type="concept",
                        similarity=0.0,  # N/A for concept repetition
                        locations=locations,
                        content_preview=f'Concept "{concept}" explained in {len(locations)} locations',
                        recommendation=f"Reference canonical explanation of '{concept}'",
                    )
                )

        return repetitions

    def generate_report(self) -> DuplicateReport:
        """Generate a complete duplicate detection report."""
        exact = self.find_exact_duplicates()
        similar = self.find_similar_content()
        concepts = self.find_concept_repetition()

        return DuplicateReport(
            exact_duplicates=exact,
            similar_content=similar,
            concept_repetition=concepts,
            total_issues=len(exact) + len(similar) + len(concepts),
        )

    def check_similarity(self, doc1: Path, doc2: Path) -> float:
        """
        Calculate similarity between two documents.

        Args:
            doc1: First document path
            doc2: Second document path

        Returns:
            Similarity score (0.0 - 1.0)
        """
        if not doc1.is_absolute():
            doc1 = self.project.content_dir / doc1
        if not doc2.is_absolute():
            doc2 = self.project.content_dir / doc2

        try:
            content1 = doc1.read_text(encoding="utf-8")
            content2 = doc2.read_text(encoding="utf-8")

            words1 = set(self._normalize_text(content1).split())
            words2 = set(self._normalize_text(content2).split())

            return self._jaccard_similarity(words1, words2)
        except (OSError, UnicodeDecodeError):
            return 0.0

    def _extract_paragraphs(self, content: str) -> list[dict]:
        """Extract paragraphs from markdown content."""
        paragraphs: list[dict] = []
        lines = content.split("\n")
        current_para: list[str] = []
        start_line = 1

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if not stripped:
                if current_para:
                    paragraphs.append(
                        {
                            "text": " ".join(current_para),
                            "start_line": start_line,
                            "end_line": i - 1,
                        }
                    )
                    current_para = []
                start_line = i + 1
            elif stripped.startswith("#"):
                # Heading - start new paragraph
                if current_para:
                    paragraphs.append(
                        {
                            "text": " ".join(current_para),
                            "start_line": start_line,
                            "end_line": i - 1,
                        }
                    )
                    current_para = []
                start_line = i + 1
            elif stripped.startswith("```"):
                # Code block - skip
                if current_para:
                    paragraphs.append(
                        {
                            "text": " ".join(current_para),
                            "start_line": start_line,
                            "end_line": i - 1,
                        }
                    )
                    current_para = []
                start_line = i + 1
            else:
                current_para.append(stripped)

        # Handle last paragraph
        if current_para:
            paragraphs.append(
                {
                    "text": " ".join(current_para),
                    "start_line": start_line,
                    "end_line": len(lines),
                }
            )

        return paragraphs

    def _extract_sections(self, content: str) -> list[dict]:
        """Extract sections (heading + content) from markdown."""
        sections: list[dict] = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headings = list(heading_pattern.finditer(content))

        for i, match in enumerate(headings):
            start = match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)

            start_line = content[: match.start()].count("\n") + 1
            end_line = content[:end].count("\n") + 1

            sections.append(
                {
                    "title": match.group(2).strip(),
                    "level": len(match.group(1)),
                    "body": content[start:end].strip(),
                    "start_line": start_line,
                    "end_line": end_line,
                }
            )

        return sections

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def _jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _detect_key_concepts(self) -> list[str]:
        """Detect key concepts from document headings."""
        concepts: dict[str, int] = defaultdict(int)

        if not self.project.content_dir.exists():
            return []

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")

                for section in self._extract_sections(content):
                    # Extract key terms from headings
                    title = section["title"].lower()
                    # Skip common words
                    for word in title.split():
                        if len(word) > 4 and word not in ("about", "using", "guide", "chapter"):
                            concepts[word] += 1

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Return concepts that appear in multiple documents
        return [c for c, count in concepts.items() if count >= 2]


def find_duplicates(project: Project) -> list[DuplicateMatch]:
    """Convenience function to find all duplicates."""
    detector = DuplicateDetector(project)
    return detector.find_exact_duplicates() + detector.find_similar_content()
