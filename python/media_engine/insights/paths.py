"""
Auto-Generated Reading Paths

Automatically generates optimal reading paths/learning journeys based on
document dependencies, complexity, and topic relationships.

Path types:
- Dependency-based: Follow prerequisite chain
- Complexity-based: Easier to harder
- Topic clusters: Related documents grouped
- Persona paths: Different paths for different audiences
"""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from ..core.project import Project


@dataclass
class PathNode:
    """A node in a reading path."""

    document: Path
    order: int
    title: str
    estimated_time: int  # minutes
    prerequisites: list[Path] = field(default_factory=list)
    word_count: int = 0
    difficulty: str = "medium"  # "easy", "medium", "hard"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document": str(self.document),
            "order": self.order,
            "title": self.title,
            "estimated_time": self.estimated_time,
            "prerequisites": [str(p) for p in self.prerequisites],
            "word_count": self.word_count,
            "difficulty": self.difficulty,
        }


@dataclass
class ReadingPath:
    """A recommended reading path."""

    name: str
    description: str
    path_type: str  # "dependency", "complexity", "topic", "persona"
    documents: list[PathNode] = field(default_factory=list)
    estimated_time: int = 0  # total minutes
    difficulty: str = "medium"
    language: str = "en"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "path_type": self.path_type,
            "documents": [d.to_dict() for d in self.documents],
            "estimated_time": self.estimated_time,
            "difficulty": self.difficulty,
            "language": self.language,
        }

    def format_markdown(self) -> str:
        """Format path as markdown checklist."""
        lines = [f"# {self.name}", "", self.description, ""]

        lines.append(f"**Estimated time:** {self.estimated_time} minutes")
        lines.append(f"**Difficulty:** {self.difficulty}")
        lines.append("")
        lines.append("## Reading Order")
        lines.append("")

        for node in self.documents:
            lines.append(f"- [ ] **{node.title}** ({node.estimated_time} min)")
            if node.prerequisites:
                prereqs = ", ".join(str(p) for p in node.prerequisites)
                lines.append(f"  - Prerequisites: {prereqs}")

        return "\n".join(lines)


# Words per minute for reading time estimation
WORDS_PER_MINUTE = 200


@dataclass
class PathGenerator:
    """
    Generates reading paths for documentation.

    Usage:
        generator = PathGenerator(project)
        path = generator.generate_dependency_path()
        print(path.format_markdown())

        # Get next document suggestion
        next_doc = generator.suggest_next_document(current_doc)
    """

    project: Project
    words_per_minute: int = WORDS_PER_MINUTE
    language: str = "en"

    def generate_dependency_path(self, language: Optional[str] = None) -> ReadingPath:
        """
        Generate a reading path based on document dependencies.

        Args:
            language: Language to filter by (default: self.language)

        Returns:
            ReadingPath ordered by prerequisites
        """
        language = language or self.language
        documents = self._get_documents(language)

        # Build dependency graph
        dependencies: dict[str, list[str]] = {}
        doc_info: dict[str, dict] = {}

        for doc_path in documents:
            try:
                content = doc_path.read_text(encoding="utf-8")
                fm, body = self._parse_frontmatter(content)

                rel_path = str(doc_path.relative_to(self.project.content_dir))
                doc_info[rel_path] = {
                    "title": fm.get("title", doc_path.stem),
                    "word_count": len(body.split()),
                    "path": doc_path,
                }

                deps = fm.get("depends_on", [])
                if isinstance(deps, str):
                    deps = [deps]
                dependencies[rel_path] = deps

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Topological sort
        ordered = self._topological_sort(dependencies)

        # Build path nodes
        nodes: list[PathNode] = []
        for i, doc_id in enumerate(ordered):
            if doc_id in doc_info:
                info = doc_info[doc_id]
                word_count = info["word_count"]
                est_time = max(1, word_count // self.words_per_minute)

                nodes.append(
                    PathNode(
                        document=Path(doc_id),
                        order=i + 1,
                        title=info["title"],
                        estimated_time=est_time,
                        prerequisites=[Path(d) for d in dependencies.get(doc_id, [])],
                        word_count=word_count,
                    )
                )

        total_time = sum(n.estimated_time for n in nodes)

        return ReadingPath(
            name="Dependency-Based Reading Path",
            description="Read documents in order of prerequisites, ensuring you have the necessary background.",
            path_type="dependency",
            documents=nodes,
            estimated_time=total_time,
            language=language,
        )

    def generate_complexity_path(self, language: Optional[str] = None) -> ReadingPath:
        """
        Generate a reading path ordered by complexity (easier first).

        Args:
            language: Language to filter by

        Returns:
            ReadingPath ordered by readability score
        """
        language = language or self.language
        documents = self._get_documents(language)

        # Score documents by complexity
        scored: list[tuple[Path, dict, float]] = []

        for doc_path in documents:
            try:
                content = doc_path.read_text(encoding="utf-8")
                fm, body = self._parse_frontmatter(content)

                # Simple complexity score based on word/sentence length
                score = self._calculate_complexity(body)

                scored.append((doc_path, {
                    "title": fm.get("title", doc_path.stem),
                    "word_count": len(body.split()),
                }, score))

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Sort by complexity (lower = easier)
        scored.sort(key=lambda x: x[2])

        # Build path nodes
        nodes: list[PathNode] = []
        for i, (doc_path, info, score) in enumerate(scored):
            word_count = info["word_count"]
            est_time = max(1, word_count // self.words_per_minute)

            difficulty = "easy" if score < 0.3 else "hard" if score > 0.7 else "medium"

            nodes.append(
                PathNode(
                    document=doc_path.relative_to(self.project.content_dir),
                    order=i + 1,
                    title=info["title"],
                    estimated_time=est_time,
                    word_count=word_count,
                    difficulty=difficulty,
                )
            )

        total_time = sum(n.estimated_time for n in nodes)
        avg_difficulty = sum(1 if n.difficulty == "easy" else 3 if n.difficulty == "hard" else 2 for n in nodes)
        overall_difficulty = "easy" if avg_difficulty / len(nodes) < 1.5 else "hard" if avg_difficulty / len(nodes) > 2.5 else "medium" if nodes else "medium"

        return ReadingPath(
            name="Complexity-Based Reading Path",
            description="Start with easier content and progress to more complex topics.",
            path_type="complexity",
            documents=nodes,
            estimated_time=total_time,
            difficulty=overall_difficulty,
            language=language,
        )

    def generate_topic_clusters(self, language: Optional[str] = None) -> list[ReadingPath]:
        """
        Generate reading paths grouped by topic.

        Args:
            language: Language to filter by

        Returns:
            List of ReadingPath, one per topic cluster
        """
        language = language or self.language
        documents = self._get_documents(language)

        # Group by directory (proxy for topic)
        clusters: dict[str, list[tuple[Path, dict]]] = defaultdict(list)

        for doc_path in documents:
            try:
                rel_path = doc_path.relative_to(self.project.content_dir)
                parts = rel_path.parts

                # Use second directory level as topic
                if len(parts) >= 2:
                    topic = parts[1]
                else:
                    topic = "general"

                content = doc_path.read_text(encoding="utf-8")
                fm, body = self._parse_frontmatter(content)

                clusters[topic].append((rel_path, {
                    "title": fm.get("title", doc_path.stem),
                    "word_count": len(body.split()),
                }))

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Build paths for each cluster
        paths: list[ReadingPath] = []

        for topic, docs in sorted(clusters.items()):
            nodes: list[PathNode] = []

            for i, (doc_path, info) in enumerate(docs):
                word_count = info["word_count"]
                est_time = max(1, word_count // self.words_per_minute)

                nodes.append(
                    PathNode(
                        document=doc_path,
                        order=i + 1,
                        title=info["title"],
                        estimated_time=est_time,
                        word_count=word_count,
                    )
                )

            total_time = sum(n.estimated_time for n in nodes)

            paths.append(
                ReadingPath(
                    name=f"{topic.title()} Guide",
                    description=f"All documents related to {topic}.",
                    path_type="topic",
                    documents=nodes,
                    estimated_time=total_time,
                    language=language,
                )
            )

        return paths

    def generate_persona_path(self, persona: str, language: Optional[str] = None) -> ReadingPath:
        """
        Generate a reading path for a specific persona.

        Args:
            persona: Persona type (developer, manager, translator)
            language: Language to filter by

        Returns:
            ReadingPath tailored for the persona
        """
        language = language or self.language

        # Define persona preferences
        persona_topics = {
            "developer": ["cli", "api", "integration", "code", "development"],
            "manager": ["overview", "introduction", "publishing", "reports"],
            "translator": ["translation", "localization", "content"],
            "writer": ["content", "writing", "quality", "style"],
        }

        preferred_topics = persona_topics.get(persona.lower(), [])

        documents = self._get_documents(language)
        scored: list[tuple[Path, dict, float]] = []

        for doc_path in documents:
            try:
                rel_path = doc_path.relative_to(self.project.content_dir)
                content = doc_path.read_text(encoding="utf-8")
                fm, body = self._parse_frontmatter(content)

                # Score based on topic relevance
                title_lower = fm.get("title", doc_path.stem).lower()
                path_lower = str(rel_path).lower()
                body_lower = body.lower()

                score = 0.0
                for topic in preferred_topics:
                    if topic in title_lower:
                        score += 2.0
                    if topic in path_lower:
                        score += 1.0
                    if topic in body_lower[:500]:
                        score += 0.5

                scored.append((rel_path, {
                    "title": fm.get("title", doc_path.stem),
                    "word_count": len(body.split()),
                }, score))

            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Sort by relevance (higher = more relevant)
        scored.sort(key=lambda x: -x[2])

        # Take top documents
        top_docs = scored[:10] if len(scored) > 10 else scored

        nodes: list[PathNode] = []
        for i, (doc_path, info, score) in enumerate(top_docs):
            if score > 0:  # Only include relevant docs
                word_count = info["word_count"]
                est_time = max(1, word_count // self.words_per_minute)

                nodes.append(
                    PathNode(
                        document=doc_path,
                        order=i + 1,
                        title=info["title"],
                        estimated_time=est_time,
                        word_count=word_count,
                    )
                )

        total_time = sum(n.estimated_time for n in nodes)

        return ReadingPath(
            name=f"{persona.title()} Reading Path",
            description=f"Recommended reading for {persona.lower()}s, focusing on relevant topics.",
            path_type="persona",
            documents=nodes,
            estimated_time=total_time,
            language=language,
        )

    def suggest_next_document(self, current_doc: Path) -> Optional[Path]:
        """
        Suggest the next document to read after the current one.

        Args:
            current_doc: Path to the current document

        Returns:
            Path to suggested next document, or None
        """
        path = self.generate_dependency_path()

        # Find current document in path
        current_order = None
        for node in path.documents:
            if str(node.document) == str(current_doc) or node.document == current_doc:
                current_order = node.order
                break

        if current_order is not None:
            # Find next document
            for node in path.documents:
                if node.order == current_order + 1:
                    return node.document

        return None

    def get_document_prerequisites(self, doc_path: Path) -> list[Path]:
        """
        Get prerequisites for a specific document.

        Args:
            doc_path: Path to the document

        Returns:
            List of prerequisite document paths
        """
        if not doc_path.is_absolute():
            full_path = self.project.content_dir / doc_path
        else:
            full_path = doc_path

        try:
            content = full_path.read_text(encoding="utf-8")
            fm, _ = self._parse_frontmatter(content)

            deps = fm.get("depends_on", [])
            if isinstance(deps, str):
                deps = [deps]

            return [Path(d) for d in deps]

        except (OSError, UnicodeDecodeError):
            return []

    def _get_documents(self, language: str) -> list[Path]:
        """Get all documents for a language."""
        lang_dir = self.project.content_dir / language
        if not lang_dir.exists():
            return []

        return list(lang_dir.rglob("*.md"))

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}, content

        try:
            end_idx = content.index("---", 3)
            frontmatter = yaml.safe_load(content[3:end_idx]) or {}
            body = content[end_idx + 3:].strip()
            return frontmatter, body
        except (ValueError, yaml.YAMLError):
            return {}, content

    def _topological_sort(self, dependencies: dict[str, list[str]]) -> list[str]:
        """Topological sort of documents based on dependencies."""
        # Build in-degree count
        in_degree: dict[str, int] = defaultdict(int)
        for node in dependencies:
            in_degree.setdefault(node, 0)
            for dep in dependencies[node]:
                in_degree[node] += 1

        # Start with nodes that have no dependencies
        queue = [node for node in dependencies if in_degree[node] == 0]
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for dependents
            for other in dependencies:
                if node in dependencies[other]:
                    # This is backwards - we want nodes that depend on current
                    pass

            # Find nodes that can now be processed
            for other, deps in dependencies.items():
                if other not in result and node in deps:
                    # Check if all deps are satisfied
                    if all(d in result for d in deps):
                        if other not in queue:
                            queue.append(other)

        # Add remaining nodes (cycles or unconnected)
        for node in dependencies:
            if node not in result:
                result.append(node)

        return result

    def _calculate_complexity(self, text: str) -> float:
        """Calculate complexity score (0-1) based on text analysis."""
        words = text.split()
        if not words:
            return 0.5

        # Average word length (normalized)
        avg_word_len = sum(len(w) for w in words) / len(words)
        word_score = min(1.0, avg_word_len / 10)

        # Sentence length
        sentences = text.count(".") + text.count("!") + text.count("?")
        if sentences > 0:
            avg_sentence_len = len(words) / sentences
            sentence_score = min(1.0, avg_sentence_len / 30)
        else:
            sentence_score = 0.5

        return (word_score + sentence_score) / 2


def generate_reading_path(project: Project, language: str = "en") -> ReadingPath:
    """Convenience function to generate a dependency-based reading path."""
    generator = PathGenerator(project, language=language)
    return generator.generate_dependency_path()
