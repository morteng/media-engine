"""
Advanced Content Analysis for Media Engine

Additional advanced analysis capabilities:
- Audience drift detection (complexity trending over time)
- Question coverage analysis
- Cross-reference density metrics
- Content structure analysis
- Writing style consistency

These are higher-order analyses that provide deeper insights.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AudienceDrift:
    """Detected drift in content audience level over time."""

    document: Path
    initial_grade_level: float
    current_grade_level: float
    drift_direction: str  # "more_complex", "simpler", "stable"
    drift_magnitude: float  # Grade levels changed
    measurements: list[dict]  # [{date, grade_level}, ...]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "initial_grade_level": round(self.initial_grade_level, 1),
            "current_grade_level": round(self.current_grade_level, 1),
            "drift_direction": self.drift_direction,
            "drift_magnitude": round(self.drift_magnitude, 1),
            "measurements": self.measurements[-10:],  # Last 10
            "recommendation": self.recommendation,
        }


@dataclass
class QuestionCoverage:
    """Analysis of questions covered by documentation."""

    document: Path
    explicit_questions: list[str]  # Questions in content (headers, text)
    implicit_questions: list[str]  # Questions the content answers
    uncovered_questions: list[str]  # Common questions not addressed
    question_density: float  # Questions per 1000 words
    faq_potential: bool  # Should have FAQ section

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "explicit_questions": self.explicit_questions[:10],
            "implicit_questions": self.implicit_questions[:10],
            "uncovered_questions": self.uncovered_questions[:5],
            "question_density": round(self.question_density, 2),
            "faq_potential": self.faq_potential,
        }


@dataclass
class CrossReferenceMetrics:
    """Cross-reference density and quality metrics."""

    document: Path
    outgoing_links: int
    incoming_links: int
    link_density: float  # Links per 1000 words
    orphan_score: float  # 0-1, higher = more isolated
    hub_score: float  # 0-1, higher = more central
    missing_cross_refs: list[str]  # Concepts that should be linked

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "outgoing_links": self.outgoing_links,
            "incoming_links": self.incoming_links,
            "link_density": round(self.link_density, 2),
            "orphan_score": round(self.orphan_score, 2),
            "hub_score": round(self.hub_score, 2),
            "missing_cross_refs": self.missing_cross_refs[:5],
        }


@dataclass
class StructureAnalysis:
    """Content structure analysis."""

    document: Path
    heading_depth: int  # Maximum heading level
    section_count: int
    avg_section_length: float  # Words per section
    structure_balance: float  # 0-1, higher = more balanced
    issues: list[str]

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "heading_depth": self.heading_depth,
            "section_count": self.section_count,
            "avg_section_length": round(self.avg_section_length, 1),
            "structure_balance": round(self.structure_balance, 2),
            "issues": self.issues,
        }


@dataclass
class StyleConsistency:
    """Writing style consistency analysis."""

    document: Path
    voice_consistency: float  # 0-100, consistent use of active/passive
    tense_consistency: float  # 0-100, consistent verb tenses
    formality_level: str  # "formal", "informal", "mixed"
    person_usage: dict  # {"first": %, "second": %, "third": %}
    issues: list[str]

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "voice_consistency": round(self.voice_consistency, 1),
            "tense_consistency": round(self.tense_consistency, 1),
            "formality_level": self.formality_level,
            "person_usage": {k: round(v, 1) for k, v in self.person_usage.items()},
            "issues": self.issues,
        }


@dataclass
class AdvancedAnalysisReport:
    """Complete advanced analysis report."""

    audience_drift: list[AudienceDrift]
    question_coverage: list[QuestionCoverage]
    cross_reference_metrics: list[CrossReferenceMetrics]
    structure_analyses: list[StructureAnalysis]
    style_consistency: list[StyleConsistency]
    overall_quality_score: float

    def to_dict(self) -> dict:
        return {
            "audience_drift": [a.to_dict() for a in self.audience_drift],
            "question_coverage": [q.to_dict() for q in self.question_coverage],
            "cross_reference_metrics": [c.to_dict() for c in self.cross_reference_metrics],
            "structure_analyses": [s.to_dict() for s in self.structure_analyses],
            "style_consistency": [s.to_dict() for s in self.style_consistency],
            "overall_quality_score": round(self.overall_quality_score, 1),
        }


class AudienceDriftAnalyzer:
    """
    Analyzes audience drift over time.

    Tracks how content complexity changes with each edit.
    """

    def __init__(self, project):
        self.project = project

    def analyze(self, doc_path: Path) -> Optional[AudienceDrift]:
        """Analyze audience drift for a document."""
        import subprocess

        full_path = self.project.content_dir / doc_path

        if not full_path.exists():
            return None

        try:
            # Get historical versions via git
            result = subprocess.run(
                ["git", "log", "--format=%H %aI", "--", str(full_path)],
                cwd=self.project.root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return None

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        commits.append({"hash": parts[0], "date": parts[1]})

            if len(commits) < 2:
                return None

            # Sample versions (first, middle, last)
            samples = [commits[0], commits[-1]]
            if len(commits) > 2:
                samples.insert(1, commits[len(commits) // 2])

            measurements = []
            for commit in samples:
                try:
                    # Get content at this commit
                    show_result = subprocess.run(
                        [
                            "git",
                            "show",
                            f"{commit['hash']}:{str(full_path.relative_to(self.project.root))}",
                        ],
                        cwd=self.project.root,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    if show_result.returncode == 0:
                        grade = self._calculate_grade_level(show_result.stdout)
                        measurements.append(
                            {
                                "date": commit["date"][:10],
                                "grade_level": grade,
                            }
                        )
                except Exception:
                    pass

            if len(measurements) < 2:
                return None

            initial = measurements[0]["grade_level"]
            current = measurements[-1]["grade_level"]
            drift = current - initial

            if drift > 1:
                direction = "more_complex"
                recommendation = (
                    "Content has become more complex. Consider simplifying for original audience."
                )
            elif drift < -1:
                direction = "simpler"
                recommendation = "Content has become simpler. Verify this matches audience needs."
            else:
                direction = "stable"
                recommendation = "Audience level has remained consistent."

            return AudienceDrift(
                document=doc_path,
                initial_grade_level=initial,
                current_grade_level=current,
                drift_direction=direction,
                drift_magnitude=abs(drift),
                measurements=measurements,
                recommendation=recommendation,
            )

        except Exception:
            return None

    def _calculate_grade_level(self, content: str) -> float:
        """Calculate reading grade level for content."""
        # Simple Flesch-Kincaid approximation
        words = re.findall(r"\b[a-zA-Z]+\b", content)
        sentences = re.split(r"[.!?]+", content)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return 0

        avg_sentence_len = len(words) / len(sentences)
        avg_syllables = sum(self._count_syllables(w) for w in words) / len(words)

        grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59
        return max(0, min(20, grade))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word."""
        word = word.lower()
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        return max(1, count)


class QuestionCoverageAnalyzer:
    """
    Analyzes question coverage in documentation.

    Identifies:
    - Explicit questions (in headers, lists)
    - Implicit questions (what the content answers)
    - Missing questions (common questions not addressed)
    """

    # Common question starters
    QUESTION_PATTERNS = [
        r"(?:^|\n)#+\s*(.+\?)\s*$",  # Question headers
        r"(?:^|\n)-\s*\*\*(.+\?)\*\*",  # Bold question list items
        r"(?:How|What|Why|When|Where|Which|Who)\s+.+\?",  # WH questions
        r"(?:Can|Could|Should|Would|Is|Are|Do|Does)\s+.+\?",  # Yes/no questions
    ]

    # Common questions for technical docs
    COMMON_QUESTIONS = [
        "How do I install",
        "How do I get started",
        "What are the requirements",
        "How do I configure",
        "What is the default",
        "How do I troubleshoot",
        "Where can I find",
        "How do I upgrade",
        "What are the limitations",
        "How does it work",
    ]

    def __init__(self, project):
        self.project = project

    def analyze(self, doc_path: Path) -> QuestionCoverage:
        """Analyze question coverage for a document."""
        full_path = self.project.content_dir / doc_path
        content = full_path.read_text(encoding="utf-8")

        # Find explicit questions
        explicit = []
        for pattern in self.QUESTION_PATTERNS:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            explicit.extend(matches)

        # Find implicit questions (based on section structure)
        implicit = self._extract_implicit_questions(content)

        # Find uncovered questions
        uncovered = self._find_uncovered_questions(content)

        # Calculate question density
        word_count = len(re.findall(r"\b\w+\b", content))
        density = (len(explicit) + len(implicit)) / (word_count / 1000) if word_count > 0 else 0

        # Determine if FAQ section would help
        faq_potential = len(explicit) < 3 and len(uncovered) >= 3

        return QuestionCoverage(
            document=doc_path,
            explicit_questions=list(set(explicit)),
            implicit_questions=implicit,
            uncovered_questions=uncovered,
            question_density=density,
            faq_potential=faq_potential,
        )

    def _extract_implicit_questions(self, content: str) -> list[str]:
        """Extract implicit questions from content structure."""
        implicit = []

        # Headers often answer "What is X?"
        headers = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
        for header in headers:
            if not header.endswith("?"):
                implicit.append(f"What is {header}?")

        # Code blocks often answer "How do I X?"
        if "```" in content:
            implicit.append("How do I use this in code?")

        # Configuration sections answer setup questions
        if re.search(r"config|setup|install", content, re.I):
            implicit.append("How do I set this up?")

        return implicit[:10]

    def _find_uncovered_questions(self, content: str) -> list[str]:
        """Find common questions not addressed in content."""
        uncovered = []
        content_lower = content.lower()

        for question in self.COMMON_QUESTIONS:
            # Check if this topic is covered
            keywords = question.split()[2:]  # Skip "How do I"
            if keywords:
                covered = any(kw.lower() in content_lower for kw in keywords)
                if not covered:
                    uncovered.append(question + "?")

        return uncovered


class CrossReferenceAnalyzer:
    """
    Analyzes cross-reference density and quality.

    Helps identify:
    - Orphan documents (not linked to/from)
    - Hub documents (highly connected)
    - Missing cross-references
    """

    def __init__(self, project):
        self.project = project
        self._link_graph: dict[str, dict] = {}
        self._build_link_graph()

    def _build_link_graph(self) -> None:
        """Build graph of document links."""
        if not self.project.content_dir.exists():
            return

        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for md_file in self.project.content_dir.rglob("*.md"):
            try:
                rel_path = str(md_file.relative_to(self.project.content_dir))
                content = md_file.read_text(encoding="utf-8")

                outgoing = []
                for _, url in link_pattern.findall(content):
                    if not url.startswith(("http://", "https://", "mailto:", "#")):
                        outgoing.append(url)

                self._link_graph[rel_path] = {
                    "outgoing": outgoing,
                    "incoming": [],
                    "word_count": len(content.split()),
                }
            except (OSError, ValueError):
                pass

        # Build incoming links
        for doc, data in self._link_graph.items():
            for link in data["outgoing"]:
                # Normalize link
                normalized = link.replace("\\", "/")
                if not normalized.endswith(".md"):
                    normalized += ".md"

                if normalized in self._link_graph:
                    self._link_graph[normalized]["incoming"].append(doc)

    def analyze(self, doc_path: Path) -> CrossReferenceMetrics:
        """Analyze cross-reference metrics for a document."""
        path_str = str(doc_path)

        if path_str not in self._link_graph:
            return CrossReferenceMetrics(
                document=doc_path,
                outgoing_links=0,
                incoming_links=0,
                link_density=0,
                orphan_score=1.0,
                hub_score=0,
                missing_cross_refs=[],
            )

        data = self._link_graph[path_str]
        outgoing = len(data["outgoing"])
        incoming = len(data["incoming"])
        word_count = data["word_count"]

        # Calculate link density
        density = (outgoing / (word_count / 1000)) if word_count > 0 else 0

        # Calculate orphan score (0 = well connected, 1 = orphan)
        total_docs = len(self._link_graph)
        if total_docs > 1:
            orphan_score = 1 - min(1, (incoming + outgoing) / (total_docs * 0.2))
        else:
            orphan_score = 0

        # Calculate hub score
        max_links = (
            max(len(d["outgoing"]) + len(d["incoming"]) for d in self._link_graph.values()) or 1
        )
        hub_score = (outgoing + incoming) / max_links

        # Find missing cross-references
        missing = self._find_missing_refs(doc_path)

        return CrossReferenceMetrics(
            document=doc_path,
            outgoing_links=outgoing,
            incoming_links=incoming,
            link_density=density,
            orphan_score=orphan_score,
            hub_score=hub_score,
            missing_cross_refs=missing,
        )

    def _find_missing_refs(self, doc_path: Path) -> list[str]:
        """Find concepts that should probably be cross-referenced."""
        missing = []
        full_path = self.project.content_dir / doc_path

        try:
            content = full_path.read_text(encoding="utf-8")

            # Find capitalized terms that might be concepts
            terms = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", content)
            term_counts = defaultdict(int)
            for term in terms:
                term_counts[term] += 1

            # Check if frequently mentioned terms are linked
            link_pattern = re.compile(r"\[([^\]]+)\]\([^)]+\)")
            linked_terms = set(link_pattern.findall(content))

            for term, count in term_counts.items():
                if count >= 3 and term not in linked_terms:
                    # Check if there's a doc about this term
                    term_slug = term.lower().replace(" ", "_")
                    if any(term_slug in str(p) for p in self._link_graph.keys()):
                        missing.append(term)

        except (OSError, UnicodeDecodeError):
            pass

        return missing[:5]


class StructureAnalyzer:
    """
    Analyzes document structure quality.

    Evaluates:
    - Heading hierarchy
    - Section balance
    - Logical flow
    """

    def __init__(self, project):
        self.project = project

    def analyze(self, doc_path: Path) -> StructureAnalysis:
        """Analyze document structure."""
        full_path = self.project.content_dir / doc_path
        content = full_path.read_text(encoding="utf-8")

        # Find all headings
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headings = [
            (len(m.group(1)), m.group(2), m.start()) for m in heading_pattern.finditer(content)
        ]

        if not headings:
            return StructureAnalysis(
                document=doc_path,
                heading_depth=0,
                section_count=0,
                avg_section_length=0,
                structure_balance=0,
                issues=["No headings found - consider adding structure"],
            )

        # Calculate metrics
        max_depth = max(h[0] for h in headings)
        section_count = len(headings)

        # Calculate section lengths
        section_lengths = []
        for i, (level, title, pos) in enumerate(headings):
            if i + 1 < len(headings):
                next_pos = headings[i + 1][2]
            else:
                next_pos = len(content)

            section_text = content[pos:next_pos]
            word_count = len(section_text.split())
            section_lengths.append(word_count)

        avg_length = sum(section_lengths) / len(section_lengths) if section_lengths else 0

        # Calculate balance (std dev of section lengths, normalized)
        if len(section_lengths) > 1:
            mean = avg_length
            variance = sum((x - mean) ** 2 for x in section_lengths) / len(section_lengths)
            std_dev = variance**0.5
            # Lower std dev = more balanced
            balance = max(0, 1 - (std_dev / (mean + 1)))
        else:
            balance = 1.0

        # Identify issues
        issues = []

        # Check for skipped heading levels
        prev_level = 0
        for level, title, _ in headings:
            if level > prev_level + 1:
                issues.append(f"Skipped heading level before '{title}'")
            prev_level = level

        # Check for very short or very long sections
        for i, length in enumerate(section_lengths):
            if length < 20 and i < len(headings):
                issues.append(f"Very short section: '{headings[i][1]}' ({length} words)")
            elif length > 1000 and i < len(headings):
                issues.append(f"Very long section: '{headings[i][1]}' - consider splitting")

        return StructureAnalysis(
            document=doc_path,
            heading_depth=max_depth,
            section_count=section_count,
            avg_section_length=avg_length,
            structure_balance=balance,
            issues=issues[:5],
        )


class StyleConsistencyAnalyzer:
    """
    Analyzes writing style consistency.

    Checks:
    - Active vs passive voice
    - Verb tense consistency
    - Person usage (first/second/third)
    - Formality level
    """

    # Passive voice indicators
    PASSIVE_PATTERNS = [
        r"\b(?:is|are|was|were|been|being)\s+\w+ed\b",
        r"\b(?:is|are|was|were|been|being)\s+\w+en\b",
    ]

    # Person indicators
    FIRST_PERSON = re.compile(r"\b(?:I|we|our|us|my)\b", re.I)
    SECOND_PERSON = re.compile(r"\b(?:you|your|yours)\b", re.I)
    THIRD_PERSON = re.compile(r"\b(?:they|their|he|she|it|its|them)\b", re.I)

    # Formality indicators
    INFORMAL_PATTERNS = [
        r"\b(?:gonna|wanna|gotta|kinda|sorta)\b",
        r"\b(?:cool|awesome|super|really|pretty)\b",
        r"!{2,}",  # Multiple exclamation marks
        r"\.\.\.",  # Ellipsis (informal usage)
    ]

    FORMAL_PATTERNS = [
        r"\b(?:therefore|however|furthermore|consequently)\b",
        r"\b(?:shall|hereby|aforementioned)\b",
    ]

    def __init__(self, project):
        self.project = project

    def analyze(self, doc_path: Path) -> StyleConsistency:
        """Analyze style consistency for a document."""
        full_path = self.project.content_dir / doc_path
        content = full_path.read_text(encoding="utf-8")

        # Remove code blocks for analysis
        clean_content = re.sub(r"```[\s\S]*?```", "", content)
        clean_content = re.sub(r"`[^`]+`", "", clean_content)

        sentences = re.split(r"[.!?]+", clean_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return StyleConsistency(
                document=doc_path,
                voice_consistency=100,
                tense_consistency=100,
                formality_level="unknown",
                person_usage={"first": 0, "second": 0, "third": 0},
                issues=[],
            )

        # Analyze voice
        passive_count = 0
        for pattern in self.PASSIVE_PATTERNS:
            passive_count += len(re.findall(pattern, clean_content, re.I))

        total_verbs = len(re.findall(r"\b(?:is|are|was|were|have|has|had)\b", clean_content, re.I))
        passive_ratio = passive_count / max(1, total_verbs)
        voice_consistency = 100 - abs(0.3 - passive_ratio) * 200  # Target ~30% passive

        # Analyze person usage
        first_count = len(self.FIRST_PERSON.findall(clean_content))
        second_count = len(self.SECOND_PERSON.findall(clean_content))
        third_count = len(self.THIRD_PERSON.findall(clean_content))
        total_person = first_count + second_count + third_count or 1

        person_usage = {
            "first": first_count / total_person * 100,
            "second": second_count / total_person * 100,
            "third": third_count / total_person * 100,
        }

        # Analyze formality
        informal_count = sum(
            len(re.findall(p, clean_content, re.I)) for p in self.INFORMAL_PATTERNS
        )
        formal_count = sum(len(re.findall(p, clean_content, re.I)) for p in self.FORMAL_PATTERNS)

        if formal_count > informal_count * 2:
            formality = "formal"
        elif informal_count > formal_count * 2:
            formality = "informal"
        else:
            formality = "mixed"

        # Calculate tense consistency (simplified - check for past vs present)
        past_tense = len(re.findall(r"\b\w+ed\b", clean_content))
        present_tense = len(re.findall(r"\b\w+s\b", clean_content))
        tense_total = past_tense + present_tense or 1
        tense_ratio = max(past_tense, present_tense) / tense_total
        tense_consistency = tense_ratio * 100

        # Identify issues
        issues = []
        if passive_ratio > 0.5:
            issues.append("High passive voice usage - consider using more active voice")
        if formality == "mixed":
            issues.append("Inconsistent formality level - standardize tone")
        if person_usage["first"] > 30 and person_usage["second"] > 30:
            issues.append("Mixed person usage - consider consistent perspective")

        return StyleConsistency(
            document=doc_path,
            voice_consistency=max(0, min(100, voice_consistency)),
            tense_consistency=max(0, min(100, tense_consistency)),
            formality_level=formality,
            person_usage=person_usage,
            issues=issues,
        )


class AdvancedAnalyzer:
    """
    Combined advanced analysis runner.

    Usage:
        from media_engine.advanced import AdvancedAnalyzer

        analyzer = AdvancedAnalyzer(project)
        report = analyzer.analyze_project()

        # Or analyze specific document
        report = analyzer.analyze_document(doc_path)
    """

    def __init__(self, project):
        self.project = project
        self.drift_analyzer = AudienceDriftAnalyzer(project)
        self.question_analyzer = QuestionCoverageAnalyzer(project)
        self.crossref_analyzer = CrossReferenceAnalyzer(project)
        self.structure_analyzer = StructureAnalyzer(project)
        self.style_analyzer = StyleConsistencyAnalyzer(project)

    def analyze_document(self, doc_path: Path) -> dict:
        """Run all analyses on a single document."""
        return {
            "audience_drift": self.drift_analyzer.analyze(doc_path),
            "question_coverage": self.question_analyzer.analyze(doc_path),
            "cross_references": self.crossref_analyzer.analyze(doc_path),
            "structure": self.structure_analyzer.analyze(doc_path),
            "style": self.style_analyzer.analyze(doc_path),
        }

    def analyze_project(self) -> AdvancedAnalysisReport:
        """Run all analyses on entire project."""
        drift_results = []
        question_results = []
        crossref_results = []
        structure_results = []
        style_results = []

        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                try:
                    rel_path = md_file.relative_to(self.project.content_dir)

                    drift = self.drift_analyzer.analyze(rel_path)
                    if drift:
                        drift_results.append(drift)

                    question_results.append(self.question_analyzer.analyze(rel_path))
                    crossref_results.append(self.crossref_analyzer.analyze(rel_path))
                    structure_results.append(self.structure_analyzer.analyze(rel_path))
                    style_results.append(self.style_analyzer.analyze(rel_path))

                except (OSError, ValueError):
                    pass

        # Calculate overall quality score
        scores = []
        for struct in structure_results:
            scores.append(struct.structure_balance * 100)
        for style in style_results:
            scores.append((style.voice_consistency + style.tense_consistency) / 2)

        overall = sum(scores) / len(scores) if scores else 0

        return AdvancedAnalysisReport(
            audience_drift=drift_results,
            question_coverage=question_results,
            cross_reference_metrics=crossref_results,
            structure_analyses=structure_results,
            style_consistency=style_results,
            overall_quality_score=overall,
        )


def run_advanced_analysis(project) -> AdvancedAnalysisReport:
    """Convenience function for advanced analysis."""
    analyzer = AdvancedAnalyzer(project)
    return analyzer.analyze_project()


__all__ = [
    "AdvancedAnalyzer",
    "AudienceDriftAnalyzer",
    "QuestionCoverageAnalyzer",
    "CrossReferenceAnalyzer",
    "StructureAnalyzer",
    "StyleConsistencyAnalyzer",
    "AudienceDrift",
    "QuestionCoverage",
    "CrossReferenceMetrics",
    "StructureAnalysis",
    "StyleConsistency",
    "AdvancedAnalysisReport",
    "run_advanced_analysis",
]
