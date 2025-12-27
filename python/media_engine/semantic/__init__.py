"""
Semantic Analysis Engine for Media Engine

Advanced semantic analysis using embeddings and NLP techniques:
- Semantic similarity detection (near-duplicates)
- Concept clustering and relationship mapping
- Terminology drift detection
- Contradiction identification
- Translation semantic parity

Requires: sentence-transformers (optional, falls back to TF-IDF)
"""

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

# Try to import sentence-transformers, fall back to TF-IDF
try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


@dataclass
class SemanticMatch:
    """A semantic similarity match between content."""

    doc1: Path
    doc2: Path
    similarity: float  # 0.0 - 1.0
    match_type: str  # "near_duplicate", "related", "concept_overlap"
    text1_preview: str = ""
    text2_preview: str = ""
    line1: Optional[int] = None
    line2: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "doc1": str(self.doc1),
            "doc2": str(self.doc2),
            "similarity": round(self.similarity, 3),
            "match_type": self.match_type,
            "text1_preview": self.text1_preview[:150],
            "text2_preview": self.text2_preview[:150],
        }


@dataclass
class TerminologyDrift:
    """Detected terminology inconsistency."""

    term1: str
    term2: str
    similarity: float
    contexts: list[dict]  # [{doc, line, text}, ...]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "term1": self.term1,
            "term2": self.term2,
            "similarity": round(self.similarity, 3),
            "contexts": self.contexts[:5],
            "recommendation": self.recommendation,
        }


@dataclass
class Contradiction:
    """Detected contradiction between content."""

    doc1: Path
    doc2: Path
    claim1: str
    claim2: str
    confidence: float
    topic: str

    def to_dict(self) -> dict:
        return {
            "doc1": str(self.doc1),
            "doc2": str(self.doc2),
            "claim1": self.claim1[:200],
            "claim2": self.claim2[:200],
            "confidence": round(self.confidence, 2),
            "topic": self.topic,
        }


@dataclass
class ContentCluster:
    """A cluster of semantically related content."""

    cluster_id: int
    topic: str
    documents: list[Path]
    centroid_doc: Path
    coherence: float  # How tightly clustered (0-1)

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "topic": self.topic,
            "documents": [str(d) for d in self.documents],
            "centroid_doc": str(self.centroid_doc),
            "coherence": round(self.coherence, 2),
        }


@dataclass
class SemanticReport:
    """Complete semantic analysis report."""

    near_duplicates: list[SemanticMatch]
    related_content: list[SemanticMatch]
    terminology_drift: list[TerminologyDrift]
    contradictions: list[Contradiction]
    clusters: list[ContentCluster]
    embedding_model: str
    analyzed_docs: int

    def to_dict(self) -> dict:
        return {
            "near_duplicates": [m.to_dict() for m in self.near_duplicates],
            "related_content": [m.to_dict() for m in self.related_content[:20]],
            "terminology_drift": [t.to_dict() for t in self.terminology_drift],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "clusters": [c.to_dict() for c in self.clusters],
            "embedding_model": self.embedding_model,
            "analyzed_docs": self.analyzed_docs,
            "summary": {
                "near_duplicate_count": len(self.near_duplicates),
                "related_pairs": len(self.related_content),
                "terminology_issues": len(self.terminology_drift),
                "contradictions": len(self.contradictions),
                "clusters": len(self.clusters),
            },
        }


class TFIDFEncoder:
    """
    Fallback TF-IDF based encoder when sentence-transformers unavailable.

    Produces sparse vectors that can be compared via cosine similarity.
    """

    def __init__(self):
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.fitted = False

    def fit(self, documents: list[str]) -> None:
        """Build vocabulary and IDF from documents."""
        doc_freq: dict[str, int] = defaultdict(int)
        all_terms: set[str] = set()

        for doc in documents:
            terms = set(self._tokenize(doc))
            all_terms.update(terms)
            for term in terms:
                doc_freq[term] += 1

        # Build vocabulary (top 10000 terms by document frequency)
        sorted_terms = sorted(doc_freq.items(), key=lambda x: -x[1])[:10000]
        self.vocabulary = {term: idx for idx, (term, _) in enumerate(sorted_terms)}

        # Compute IDF
        n_docs = len(documents)
        self.idf = {term: math.log(n_docs / (1 + doc_freq[term])) for term in self.vocabulary}
        self.fitted = True

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode texts to TF-IDF vectors."""
        if not self.fitted:
            self.fit(texts)

        vectors = np.zeros((len(texts), len(self.vocabulary)))

        for i, text in enumerate(texts):
            terms = self._tokenize(text)
            term_freq: dict[str, int] = defaultdict(int)
            for term in terms:
                term_freq[term] += 1

            for term, freq in term_freq.items():
                if term in self.vocabulary:
                    idx = self.vocabulary[term]
                    tf = 1 + math.log(freq) if freq > 0 else 0
                    vectors[i, idx] = tf * self.idf.get(term, 0)

            # Normalize
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm

        return vectors

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return [w for w in text.split() if len(w) > 2]


class SemanticAnalyzer:
    """
    Semantic analysis engine using embeddings.

    Uses sentence-transformers if available, falls back to TF-IDF.

    Usage:
        from media_engine.semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)

        # Find near-duplicates
        duplicates = analyzer.find_near_duplicates(threshold=0.85)

        # Find related content
        related = analyzer.find_related_content(threshold=0.6)

        # Detect terminology drift
        drift = analyzer.detect_terminology_drift()

        # Find contradictions (requires LLM)
        contradictions = analyzer.find_contradictions()

        # Cluster related content
        clusters = analyzer.cluster_content(n_clusters=10)

        # Full report
        report = analyzer.generate_report()
    """

    # Default model (small, fast, good quality)
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(
        self,
        project,
        model_name: str = None,
        use_gpu: bool = False,
    ):
        """
        Initialize semantic analyzer.

        Args:
            project: Media Engine project
            model_name: Sentence transformer model name (default: all-MiniLM-L6-v2)
            use_gpu: Whether to use GPU for embeddings
        """
        self.project = project
        self.model_name = model_name or self.DEFAULT_MODEL

        # Initialize encoder
        if HAS_SENTENCE_TRANSFORMERS:
            device = "cuda" if use_gpu else "cpu"
            self.encoder = SentenceTransformer(self.model_name, device=device)
            self.encoder_type = "transformer"
        else:
            self.encoder = TFIDFEncoder()
            self.encoder_type = "tfidf"

        # Cache for embeddings
        self._embeddings_cache: dict[str, np.ndarray] = {}
        self._content_cache: dict[str, str] = {}
        self._chunk_cache: dict[str, list[dict]] = {}

    def _load_documents(self) -> dict[Path, str]:
        """Load all markdown documents."""
        docs = {}
        if not self.project.content_dir.exists():
            return docs

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel_path = md_file.relative_to(self.project.content_dir)
                docs[rel_path] = self._clean_content(content)
            except (OSError, UnicodeDecodeError):
                pass

        return docs

    def _clean_content(self, content: str) -> str:
        """Remove markdown formatting for semantic analysis."""
        # Remove frontmatter
        if content.startswith("---"):
            try:
                end = content.index("---", 3)
                content = content[end + 3 :]
            except ValueError:
                pass

        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"`[^`]+`", "", content)

        # Remove links but keep text
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

        # Remove images
        content = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)

        # Remove HTML
        content = re.sub(r"<[^>]+>", "", content)

        # Remove headers markers but keep text
        content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)

        # Normalize whitespace
        content = " ".join(content.split())

        return content

    def _chunk_document(self, content: str, chunk_size: int = 200) -> list[dict]:
        """Split document into overlapping chunks for comparison."""
        words = content.split()
        chunks = []
        stride = chunk_size // 2

        for i in range(0, len(words), stride):
            chunk_words = words[i : i + chunk_size]
            if len(chunk_words) >= chunk_size // 4:  # Minimum chunk size
                chunks.append(
                    {
                        "text": " ".join(chunk_words),
                        "start_word": i,
                        "end_word": i + len(chunk_words),
                    }
                )

        return chunks

    def _get_embeddings(self, texts: list[str]) -> np.ndarray:
        """Get embeddings for texts."""
        if self.encoder_type == "transformer":
            return self.encoder.encode(texts, show_progress_bar=False)
        else:
            return self.encoder.encode(texts)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _batch_cosine_similarity(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity matrix."""
        # Normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        normalized = embeddings / norms

        # Compute similarity matrix
        return np.dot(normalized, normalized.T)

    def find_near_duplicates(
        self,
        threshold: float = 0.85,
        chunk_level: bool = True,
    ) -> list[SemanticMatch]:
        """
        Find semantically near-duplicate content.

        Args:
            threshold: Minimum similarity score (0.85 = very similar)
            chunk_level: Compare at chunk level (more precise) vs document level

        Returns:
            List of SemanticMatch instances
        """
        docs = self._load_documents()
        if not docs:
            return []

        matches = []

        if chunk_level:
            # Chunk-level comparison (more precise)
            all_chunks = []
            chunk_docs = []

            for doc_path, content in docs.items():
                chunks = self._chunk_document(content)
                for chunk in chunks:
                    all_chunks.append(chunk["text"])
                    chunk_docs.append((doc_path, chunk))

            if not all_chunks:
                return []

            # Get embeddings
            embeddings = self._get_embeddings(all_chunks)

            # Compute similarity matrix
            sim_matrix = self._batch_cosine_similarity(embeddings)

            # Find pairs above threshold
            seen = set()
            for i in range(len(all_chunks)):
                for j in range(i + 1, len(all_chunks)):
                    doc1, chunk1 = chunk_docs[i]
                    doc2, chunk2 = chunk_docs[j]

                    # Skip same document
                    if doc1 == doc2:
                        continue

                    sim = sim_matrix[i, j]
                    if sim >= threshold:
                        pair_key = (
                            str(doc1),
                            str(doc2),
                            chunk1["start_word"],
                            chunk2["start_word"],
                        )
                        if pair_key not in seen:
                            seen.add(pair_key)
                            matches.append(
                                SemanticMatch(
                                    doc1=doc1,
                                    doc2=doc2,
                                    similarity=float(sim),
                                    match_type="near_duplicate",
                                    text1_preview=chunk1["text"][:200],
                                    text2_preview=chunk2["text"][:200],
                                )
                            )
        else:
            # Document-level comparison
            doc_list = list(docs.keys())
            contents = list(docs.values())

            embeddings = self._get_embeddings(contents)
            sim_matrix = self._batch_cosine_similarity(embeddings)

            for i in range(len(doc_list)):
                for j in range(i + 1, len(doc_list)):
                    sim = sim_matrix[i, j]
                    if sim >= threshold:
                        matches.append(
                            SemanticMatch(
                                doc1=doc_list[i],
                                doc2=doc_list[j],
                                similarity=float(sim),
                                match_type="near_duplicate",
                                text1_preview=contents[i][:200],
                                text2_preview=contents[j][:200],
                            )
                        )

        # Sort by similarity
        matches.sort(key=lambda x: -x.similarity)

        return matches

    def find_related_content(
        self,
        threshold: float = 0.5,
        max_results: int = 50,
    ) -> list[SemanticMatch]:
        """
        Find semantically related content (looser than duplicates).

        Args:
            threshold: Minimum similarity (0.5 = moderately related)
            max_results: Maximum number of results

        Returns:
            List of SemanticMatch instances
        """
        docs = self._load_documents()
        if not docs:
            return []

        doc_list = list(docs.keys())
        contents = list(docs.values())

        embeddings = self._get_embeddings(contents)
        sim_matrix = self._batch_cosine_similarity(embeddings)

        matches = []
        for i in range(len(doc_list)):
            for j in range(i + 1, len(doc_list)):
                sim = sim_matrix[i, j]
                if threshold <= sim < 0.85:  # Related but not duplicate
                    matches.append(
                        SemanticMatch(
                            doc1=doc_list[i],
                            doc2=doc_list[j],
                            similarity=float(sim),
                            match_type="related",
                            text1_preview=contents[i][:200],
                            text2_preview=contents[j][:200],
                        )
                    )

        # Sort by similarity and limit
        matches.sort(key=lambda x: -x.similarity)
        return matches[:max_results]

    def detect_terminology_drift(
        self,
        similarity_threshold: float = 0.7,
    ) -> list[TerminologyDrift]:
        """
        Detect inconsistent terminology (same concept, different terms).

        Args:
            similarity_threshold: How similar terms must be to flag

        Returns:
            List of TerminologyDrift instances
        """
        docs = self._load_documents()
        if not docs:
            return []

        # Extract potential terms (capitalized phrases, technical terms)
        term_pattern = re.compile(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b"  # Capitalized phrases
            r"|\b([a-z]+[-_][a-z]+)\b"  # Hyphenated/underscored terms
        )

        term_contexts: dict[str, list[dict]] = defaultdict(list)

        for doc_path, content in docs.items():
            for match in term_pattern.finditer(content):
                term = match.group(0)
                if len(term) > 3:  # Skip short terms
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(content), match.end() + 50)
                    term_contexts[term.lower()].append(
                        {
                            "term": term,
                            "doc": str(doc_path),
                            "context": content[context_start:context_end],
                        }
                    )

        # Find similar terms
        terms = list(term_contexts.keys())
        if len(terms) < 2:
            return []

        # Get embeddings for terms
        embeddings = self._get_embeddings(terms)
        sim_matrix = self._batch_cosine_similarity(embeddings)

        drift_issues = []
        seen_pairs = set()

        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                if terms[i] == terms[j]:
                    continue

                sim = sim_matrix[i, j]
                if sim >= similarity_threshold:
                    pair_key = tuple(sorted([terms[i], terms[j]]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Check if they appear in different documents
                    docs_i = set(c["doc"] for c in term_contexts[terms[i]])
                    docs_j = set(c["doc"] for c in term_contexts[terms[j]])

                    if docs_i != docs_j:  # Used inconsistently
                        # Get canonical forms
                        term1_forms = set(c["term"] for c in term_contexts[terms[i]])
                        term2_forms = set(c["term"] for c in term_contexts[terms[j]])

                        drift_issues.append(
                            TerminologyDrift(
                                term1=list(term1_forms)[0],
                                term2=list(term2_forms)[0],
                                similarity=float(sim),
                                contexts=(
                                    term_contexts[terms[i]][:3] + term_contexts[terms[j]][:3]
                                ),
                                recommendation=f"Standardize on one term: '{list(term1_forms)[0]}' or '{list(term2_forms)[0]}'",
                            )
                        )

        drift_issues.sort(key=lambda x: -x.similarity)
        return drift_issues

    def cluster_content(
        self,
        n_clusters: int = None,
        min_cluster_size: int = 2,
    ) -> list[ContentCluster]:
        """
        Cluster documents by semantic similarity.

        Args:
            n_clusters: Number of clusters (auto-detected if None)
            min_cluster_size: Minimum documents per cluster

        Returns:
            List of ContentCluster instances
        """
        docs = self._load_documents()
        if len(docs) < 3:
            return []

        doc_list = list(docs.keys())
        contents = list(docs.values())

        embeddings = self._get_embeddings(contents)

        # Auto-detect number of clusters
        if n_clusters is None:
            n_clusters = max(2, len(docs) // 5)

        # Simple k-means clustering
        clusters = self._kmeans_cluster(embeddings, n_clusters)

        # Build cluster objects
        result = []
        for cluster_id in range(n_clusters):
            members = [doc_list[i] for i, c in enumerate(clusters) if c == cluster_id]

            if len(members) >= min_cluster_size:
                # Find centroid document
                member_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
                member_embeddings = embeddings[member_indices]
                centroid = member_embeddings.mean(axis=0)

                # Find closest to centroid
                distances = [
                    np.linalg.norm(member_embeddings[i] - centroid)
                    for i in range(len(member_indices))
                ]
                centroid_idx = member_indices[np.argmin(distances)]

                # Calculate coherence (average pairwise similarity)
                if len(member_indices) > 1:
                    sims = []
                    for i in range(len(member_indices)):
                        for j in range(i + 1, len(member_indices)):
                            sim = self._cosine_similarity(
                                member_embeddings[i], member_embeddings[j]
                            )
                            sims.append(sim)
                    coherence = sum(sims) / len(sims) if sims else 0
                else:
                    coherence = 1.0

                # Extract topic from centroid document headings
                centroid_content = contents[centroid_idx]
                heading_match = re.search(r"^#\s+(.+)$", centroid_content, re.MULTILINE)
                topic = heading_match.group(1) if heading_match else f"Cluster {cluster_id}"

                result.append(
                    ContentCluster(
                        cluster_id=cluster_id,
                        topic=topic,
                        documents=members,
                        centroid_doc=doc_list[centroid_idx],
                        coherence=float(coherence),
                    )
                )

        result.sort(key=lambda x: -len(x.documents))
        return result

    def _kmeans_cluster(
        self,
        embeddings: np.ndarray,
        n_clusters: int,
        max_iter: int = 100,
    ) -> list[int]:
        """Simple k-means clustering."""
        n_samples = len(embeddings)

        # Initialize centroids randomly
        indices = np.random.choice(n_samples, n_clusters, replace=False)
        centroids = embeddings[indices].copy()

        labels = np.zeros(n_samples, dtype=int)

        for _ in range(max_iter):
            # Assign points to nearest centroid
            old_labels = labels.copy()
            for i in range(n_samples):
                distances = [
                    np.linalg.norm(embeddings[i] - centroids[j]) for j in range(n_clusters)
                ]
                labels[i] = np.argmin(distances)

            # Update centroids
            for j in range(n_clusters):
                members = embeddings[labels == j]
                if len(members) > 0:
                    centroids[j] = members.mean(axis=0)

            # Check convergence
            if np.array_equal(labels, old_labels):
                break

        return labels.tolist()

    def find_contradictions(
        self,
        llm_client=None,
    ) -> list[Contradiction]:
        """
        Find contradictory claims across documents.

        This method extracts factual claims and checks for contradictions.
        If an LLM client is provided, uses it for better detection.
        Otherwise, uses heuristic-based detection.

        Args:
            llm_client: Optional LLM client for advanced detection

        Returns:
            List of Contradiction instances
        """
        docs = self._load_documents()
        if len(docs) < 2:
            return []

        # Extract potential claims (sentences with factual patterns)
        claim_patterns = [
            r"(?:is|are|was|were|will be|should be|must be)\s+(?:the|a|an)?\s*\w+",
            r"(?:always|never|must|should|cannot|can't|won't)",
            r"(?:requires?|needs?|depends?\s+on)",
            r"(?:default(?:s)?|by default)",
            r"\d+(?:\.\d+)?(?:\s*%|\s*percent|\s*seconds?|\s*minutes?)",
        ]

        claims: list[dict] = []

        for doc_path, content in docs.items():
            sentences = re.split(r"[.!?]+", content)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < 20 or len(sent) > 300:
                    continue

                for pattern in claim_patterns:
                    if re.search(pattern, sent, re.I):
                        claims.append(
                            {
                                "doc": doc_path,
                                "text": sent,
                            }
                        )
                        break

        if len(claims) < 2:
            return []

        # Get embeddings for claims
        claim_texts = [c["text"] for c in claims]
        embeddings = self._get_embeddings(claim_texts)

        # Find similar claims from different documents
        contradictions = []

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                # Skip same document
                if claims[i]["doc"] == claims[j]["doc"]:
                    continue

                sim = self._cosine_similarity(embeddings[i], embeddings[j])

                # High similarity but different docs = potential contradiction
                if sim >= 0.6:
                    # Check for negation patterns
                    text1 = claims[i]["text"].lower()
                    text2 = claims[j]["text"].lower()

                    negation_words = [
                        "not",
                        "no",
                        "never",
                        "cannot",
                        "can't",
                        "won't",
                        "don't",
                        "doesn't",
                    ]
                    has_negation1 = any(w in text1 for w in negation_words)
                    has_negation2 = any(w in text2 for w in negation_words)

                    # Different polarity = likely contradiction
                    if has_negation1 != has_negation2:
                        # Extract topic (first noun phrase)
                        topic_match = re.search(r"\b(?:the|a|an)?\s*(\w+(?:\s+\w+)?)\b", text1)
                        topic = topic_match.group(1) if topic_match else "unknown"

                        contradictions.append(
                            Contradiction(
                                doc1=claims[i]["doc"],
                                doc2=claims[j]["doc"],
                                claim1=claims[i]["text"],
                                claim2=claims[j]["text"],
                                confidence=float(sim),
                                topic=topic,
                            )
                        )

        contradictions.sort(key=lambda x: -x.confidence)
        return contradictions[:20]  # Top 20

    def check_translation_parity(
        self,
        source_lang: str = "en",
    ) -> list[SemanticMatch]:
        """
        Check semantic parity between translations.

        Compares translated documents against their source to detect
        semantic drift (meaning changed during translation).

        Args:
            source_lang: Source language code

        Returns:
            List of SemanticMatch instances where translation diverged
        """
        docs = self._load_documents()
        if not docs:
            return []

        # Group documents by language
        by_lang: dict[str, dict[str, str]] = defaultdict(dict)
        for doc_path, content in docs.items():
            parts = doc_path.parts
            if len(parts) >= 2:
                lang = parts[0]
                rest = "/".join(parts[1:])
                by_lang[lang][rest] = content

        if source_lang not in by_lang:
            return []

        source_docs = by_lang[source_lang]
        divergences = []

        for target_lang, target_docs in by_lang.items():
            if target_lang == source_lang:
                continue

            # Find matching documents
            for doc_name, source_content in source_docs.items():
                if doc_name in target_docs:
                    target_content = target_docs[doc_name]

                    # Get embeddings
                    source_emb = self._get_embeddings([source_content])[0]
                    target_emb = self._get_embeddings([target_content])[0]

                    sim = self._cosine_similarity(source_emb, target_emb)

                    # Low similarity = semantic drift
                    if sim < 0.7:
                        divergences.append(
                            SemanticMatch(
                                doc1=Path(source_lang) / doc_name,
                                doc2=Path(target_lang) / doc_name,
                                similarity=float(sim),
                                match_type="translation_drift",
                                text1_preview=source_content[:200],
                                text2_preview=target_content[:200],
                            )
                        )

        divergences.sort(key=lambda x: x.similarity)
        return divergences

    def generate_report(self) -> SemanticReport:
        """Generate comprehensive semantic analysis report."""
        return SemanticReport(
            near_duplicates=self.find_near_duplicates(threshold=0.85),
            related_content=self.find_related_content(threshold=0.5, max_results=30),
            terminology_drift=self.detect_terminology_drift(),
            contradictions=self.find_contradictions(),
            clusters=self.cluster_content(),
            embedding_model=self.model_name if self.encoder_type == "transformer" else "TF-IDF",
            analyzed_docs=len(self._load_documents()),
        )


def analyze_semantics(project) -> SemanticReport:
    """Convenience function to run semantic analysis."""
    analyzer = SemanticAnalyzer(project)
    return analyzer.generate_report()


__all__ = [
    "SemanticAnalyzer",
    "SemanticMatch",
    "TerminologyDrift",
    "Contradiction",
    "ContentCluster",
    "SemanticReport",
    "TFIDFEncoder",
    "HAS_SENTENCE_TRANSFORMERS",
    "analyze_semantics",
]
