"""
LLM-Powered Quality Evaluation for Media Engine

ARCHITECTURE NOTE:
==================
This module provides DATA STRUCTURES and PROMPTS for LLM-based quality evaluation.
However, the RECOMMENDED approach is to use the MCP server's reporting tools:

    - quality_report_comprehensive() - Full programmatic analysis
    - quality_report_document(path) - Per-document analysis
    - quality_report_module(name) - Specific module data

The LLM agent (Claude Code) should:
1. Call MCP tools to get PROGRAMMATIC analysis data
2. Apply its own LLM judgment on top of that data
3. NOT use this module's direct LLM calls (to avoid double-calling)

This module's LLMQualityEvaluator class makes DIRECT LLM API calls,
which duplicates what the agent already does. Use it only if you need
standalone LLM evaluation outside of an agent context.

The data structures (QualityFinding, CompletenessReport, etc.) can still
be used by programmatic code to structure quality data.

Supports: Claude (Anthropic), OpenAI, local models via LiteLLM
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ReviewPerspective(str, Enum):
    """Different reviewer perspectives for multi-agent review."""

    TECHNICAL = "technical"  # Technical accuracy and depth
    USER = "user"  # User-friendliness and clarity
    EDITOR = "editor"  # Writing quality and structure
    SECURITY = "security"  # Security implications
    ACCESSIBILITY = "accessibility"  # Accessibility and inclusivity


@dataclass
class QualityFinding:
    """A quality issue or observation from LLM analysis."""

    category: str  # "completeness", "prerequisite", "example", "outdated", "structure"
    severity: str  # "critical", "warning", "suggestion", "praise"
    message: str
    location: Optional[str] = None  # Section or line reference
    suggestion: str = ""
    confidence: float = 0.8  # LLM confidence (0-1)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }


@dataclass
class CompletenessReport:
    """Report on content completeness."""

    is_complete: bool
    missing_sections: list[str]
    incomplete_sections: list[str]
    coverage_score: float  # 0-100
    findings: list[QualityFinding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_complete": self.is_complete,
            "missing_sections": self.missing_sections,
            "incomplete_sections": self.incomplete_sections,
            "coverage_score": self.coverage_score,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class PrerequisiteReport:
    """Report on prerequisite coverage."""

    has_all_prerequisites: bool
    missing_prerequisites: list[str]
    assumed_knowledge: list[str]
    suggestion_links: list[dict]  # [{topic, suggested_doc}, ...]
    findings: list[QualityFinding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "has_all_prerequisites": self.has_all_prerequisites,
            "missing_prerequisites": self.missing_prerequisites,
            "assumed_knowledge": self.assumed_knowledge,
            "suggestion_links": self.suggestion_links,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ExampleAssessment:
    """Assessment of code examples in content."""

    total_examples: int
    quality_score: float  # 0-100
    issues: list[dict]  # [{example_id, issue, suggestion}, ...]
    findings: list[QualityFinding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_examples": self.total_examples,
            "quality_score": self.quality_score,
            "issues": self.issues,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class OutdatedClaimReport:
    """Report on potentially outdated claims."""

    outdated_claims: list[dict]  # [{claim, reason, confidence}, ...]
    date_references: list[dict]  # [{text, date_found}, ...]
    version_references: list[dict]  # [{text, version}, ...]
    findings: list[QualityFinding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "outdated_claims": self.outdated_claims,
            "date_references": self.date_references,
            "version_references": self.version_references,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class AgentReview:
    """Review from a specific agent perspective."""

    perspective: ReviewPerspective
    overall_score: float  # 0-100
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    findings: list[QualityFinding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "perspective": self.perspective.value,
            "overall_score": self.overall_score,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class LLMQualityReport:
    """Comprehensive LLM quality evaluation report."""

    document: Path
    completeness: Optional[CompletenessReport] = None
    prerequisites: Optional[PrerequisiteReport] = None
    examples: Optional[ExampleAssessment] = None
    outdated_claims: Optional[OutdatedClaimReport] = None
    agent_reviews: list[AgentReview] = field(default_factory=list)
    overall_score: float = 0.0
    all_findings: list[QualityFinding] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.now)
    model_used: str = ""

    def to_dict(self) -> dict:
        return {
            "document": str(self.document),
            "completeness": self.completeness.to_dict() if self.completeness else None,
            "prerequisites": self.prerequisites.to_dict() if self.prerequisites else None,
            "examples": self.examples.to_dict() if self.examples else None,
            "outdated_claims": self.outdated_claims.to_dict() if self.outdated_claims else None,
            "agent_reviews": [r.to_dict() for r in self.agent_reviews],
            "overall_score": self.overall_score,
            "all_findings": [f.to_dict() for f in self.all_findings],
            "evaluated_at": self.evaluated_at.isoformat(),
            "model_used": self.model_used,
        }


class LLMClient:
    """
    Abstraction layer for LLM providers.

    Supports Claude, OpenAI, and any LiteLLM-compatible provider.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = None,
        api_key: str = None,
    ):
        """
        Initialize LLM client.

        Args:
            provider: "anthropic", "openai", or "litellm"
            model: Model name (default varies by provider)
            api_key: API key (uses env var if not provided)
        """
        self.provider = provider
        self.api_key = api_key

        # Default models
        default_models = {
            "anthropic": "claude-sonnet-4-20250514",
            "openai": "gpt-4o",
            "litellm": "gpt-4o-mini",
        }
        self.model = model or default_models.get(provider, "gpt-4o-mini")

        # Initialize client based on provider
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate client."""
        if self.provider == "anthropic":
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")

        elif self.provider == "openai":
            try:
                import openai

                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required: pip install openai")

        elif self.provider == "litellm":
            try:
                import litellm

                self._client = litellm
            except ImportError:
                raise ImportError("litellm package required: pip install litellm")

    def complete(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> str:
        """
        Get completion from LLM.

        Args:
            prompt: User prompt
            system: System prompt
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            LLM response text
        """
        if self.provider == "anthropic":
            messages = [{"role": "user", "content": prompt}]
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system or "You are a helpful assistant.",
                messages=messages,
            )
            return response.content[0].text

        elif self.provider == "openai":
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

        elif self.provider == "litellm":
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self._client.completion(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

        raise ValueError(f"Unknown provider: {self.provider}")


class LLMQualityEvaluator:
    """
    LLM-powered documentation quality evaluator.

    Usage:
        from media_engine.llm_quality import LLMQualityEvaluator

        evaluator = LLMQualityEvaluator(project)

        # Evaluate completeness
        completeness = evaluator.evaluate_completeness(doc_path)

        # Check prerequisites
        prereqs = evaluator.check_prerequisites(doc_path)

        # Assess examples
        examples = evaluator.assess_examples(doc_path)

        # Detect outdated claims
        outdated = evaluator.detect_outdated_claims(doc_path)

        # Multi-agent review
        reviews = evaluator.multi_agent_review(doc_path)

        # Full evaluation
        report = evaluator.evaluate_document(doc_path)
    """

    # System prompts for different evaluation tasks
    COMPLETENESS_SYSTEM = """You are a documentation completeness evaluator.
Analyze the document and identify:
1. Missing sections that should be present
2. Incomplete sections that need more content
3. Coverage score (0-100) based on topic depth

Respond in JSON format:
{
    "is_complete": true/false,
    "missing_sections": ["section1", "section2"],
    "incomplete_sections": ["section3"],
    "coverage_score": 85,
    "findings": [{"category": "completeness", "severity": "warning", "message": "..."}]
}"""

    PREREQUISITE_SYSTEM = """You are a prerequisite analyzer for documentation.
Analyze the document and identify:
1. Knowledge assumed but not explained
2. Concepts that need prior understanding
3. Suggested links to prerequisite content

Respond in JSON format:
{
    "has_all_prerequisites": true/false,
    "missing_prerequisites": ["concept1", "concept2"],
    "assumed_knowledge": ["knowledge1"],
    "suggestion_links": [{"topic": "concept1", "suggested_doc": "basics.md"}],
    "findings": [{"category": "prerequisite", "severity": "warning", "message": "..."}]
}"""

    EXAMPLE_SYSTEM = """You are a code example quality reviewer.
Analyze the code examples and identify:
1. Clarity and correctness issues
2. Missing context or setup
3. Outdated patterns or deprecated APIs
4. Overall quality score (0-100)

Respond in JSON format:
{
    "total_examples": 5,
    "quality_score": 80,
    "issues": [{"example_id": 1, "issue": "...", "suggestion": "..."}],
    "findings": [{"category": "example", "severity": "warning", "message": "..."}]
}"""

    OUTDATED_SYSTEM = """You are a content freshness analyzer.
Analyze the document and identify:
1. Claims that may be outdated
2. Date references that need updating
3. Version references that may be stale

Respond in JSON format:
{
    "outdated_claims": [{"claim": "...", "reason": "...", "confidence": 0.8}],
    "date_references": [{"text": "...", "date_found": "2023"}],
    "version_references": [{"text": "...", "version": "1.0"}],
    "findings": [{"category": "outdated", "severity": "warning", "message": "..."}]
}"""

    AGENT_SYSTEMS = {
        ReviewPerspective.TECHNICAL: """You are a senior technical reviewer.
Focus on: technical accuracy, depth of coverage, correct terminology, API accuracy.
Score and provide specific findings.""",
        ReviewPerspective.USER: """You are a user experience reviewer for documentation.
Focus on: clarity, ease of understanding, learning path, practical usefulness.
Score and provide specific findings.""",
        ReviewPerspective.EDITOR: """You are a professional technical editor.
Focus on: writing quality, structure, flow, grammar, consistency.
Score and provide specific findings.""",
        ReviewPerspective.SECURITY: """You are a security-focused reviewer.
Focus on: security best practices, dangerous patterns, credential handling.
Score and provide specific findings.""",
        ReviewPerspective.ACCESSIBILITY: """You are an accessibility reviewer.
Focus on: inclusive language, alt text, readability, internationalization.
Score and provide specific findings.""",
    }

    def __init__(
        self,
        project,
        llm_client: LLMClient = None,
        provider: str = "anthropic",
        model: str = None,
    ):
        """
        Initialize LLM quality evaluator.

        Args:
            project: Media Engine project
            llm_client: Pre-configured LLM client
            provider: LLM provider if no client provided
            model: Model name if no client provided
        """
        self.project = project

        if llm_client:
            self.llm = llm_client
        else:
            self.llm = LLMClient(provider=provider, model=model)

    def _load_document(self, doc_path: Path) -> tuple[str, dict]:
        """Load document content and metadata."""
        if not doc_path.is_absolute():
            doc_path = self.project.content_dir / doc_path

        content = doc_path.read_text(encoding="utf-8")

        # Parse frontmatter
        metadata = {}
        if content.startswith("---"):
            try:
                import yaml

                end = content.index("---", 3)
                metadata = yaml.safe_load(content[3:end]) or {}
                content = content[end + 3 :]
            except (ValueError, ImportError):
                pass

        return content, metadata

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        # Try to extract JSON from response
        try:
            # Direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    def evaluate_completeness(self, doc_path: Path) -> CompletenessReport:
        """
        Evaluate document completeness using LLM.

        Args:
            doc_path: Path to document

        Returns:
            CompletenessReport with findings
        """
        content, metadata = self._load_document(doc_path)

        prompt = f"""Analyze this document for completeness:

Title: {metadata.get("title", "Unknown")}
Type: {metadata.get("type", "chapter")}

Content:
{content[:8000]}

Evaluate completeness and respond in JSON format."""

        response = self.llm.complete(prompt, system=self.COMPLETENESS_SYSTEM)
        data = self._parse_json_response(response)

        findings = [QualityFinding(**f) for f in data.get("findings", []) if isinstance(f, dict)]

        return CompletenessReport(
            is_complete=data.get("is_complete", True),
            missing_sections=data.get("missing_sections", []),
            incomplete_sections=data.get("incomplete_sections", []),
            coverage_score=data.get("coverage_score", 100),
            findings=findings,
        )

    def check_prerequisites(self, doc_path: Path) -> PrerequisiteReport:
        """
        Check if document covers all prerequisites.

        Args:
            doc_path: Path to document

        Returns:
            PrerequisiteReport with findings
        """
        content, metadata = self._load_document(doc_path)

        # Get list of available documents for context
        available_docs = []
        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                try:
                    rel = md_file.relative_to(self.project.content_dir)
                    available_docs.append(str(rel))
                except ValueError:
                    pass

        prompt = f"""Analyze this document for prerequisite knowledge:

Title: {metadata.get("title", "Unknown")}

Available related documents:
{chr(10).join(available_docs[:20])}

Content:
{content[:8000]}

Identify assumed knowledge and missing prerequisites. Respond in JSON format."""

        response = self.llm.complete(prompt, system=self.PREREQUISITE_SYSTEM)
        data = self._parse_json_response(response)

        findings = [QualityFinding(**f) for f in data.get("findings", []) if isinstance(f, dict)]

        return PrerequisiteReport(
            has_all_prerequisites=data.get("has_all_prerequisites", True),
            missing_prerequisites=data.get("missing_prerequisites", []),
            assumed_knowledge=data.get("assumed_knowledge", []),
            suggestion_links=data.get("suggestion_links", []),
            findings=findings,
        )

    def assess_examples(self, doc_path: Path) -> ExampleAssessment:
        """
        Assess quality of code examples.

        Args:
            doc_path: Path to document

        Returns:
            ExampleAssessment with findings
        """
        content, metadata = self._load_document(doc_path)

        # Extract code blocks
        code_blocks = re.findall(r"```(\w+)?\n([\s\S]*?)```", content)

        if not code_blocks:
            return ExampleAssessment(
                total_examples=0,
                quality_score=100,
                issues=[],
                findings=[],
            )

        examples_text = "\n\n".join(
            f"Example {i + 1} ({lang or 'unknown'}):\n{code}"
            for i, (lang, code) in enumerate(code_blocks)
        )

        prompt = f"""Analyze these code examples from documentation:

Document: {metadata.get("title", "Unknown")}

{examples_text}

Assess quality and identify issues. Respond in JSON format."""

        response = self.llm.complete(prompt, system=self.EXAMPLE_SYSTEM)
        data = self._parse_json_response(response)

        findings = [QualityFinding(**f) for f in data.get("findings", []) if isinstance(f, dict)]

        return ExampleAssessment(
            total_examples=data.get("total_examples", len(code_blocks)),
            quality_score=data.get("quality_score", 80),
            issues=data.get("issues", []),
            findings=findings,
        )

    def detect_outdated_claims(self, doc_path: Path) -> OutdatedClaimReport:
        """
        Detect potentially outdated claims.

        Args:
            doc_path: Path to document

        Returns:
            OutdatedClaimReport with findings
        """
        content, metadata = self._load_document(doc_path)

        prompt = f"""Analyze this document for outdated information:

Title: {metadata.get("title", "Unknown")}
Last updated: {metadata.get("updated", "Unknown")}

Content:
{content[:8000]}

Identify outdated claims, date references, and version references. Respond in JSON format."""

        response = self.llm.complete(prompt, system=self.OUTDATED_SYSTEM)
        data = self._parse_json_response(response)

        findings = [QualityFinding(**f) for f in data.get("findings", []) if isinstance(f, dict)]

        return OutdatedClaimReport(
            outdated_claims=data.get("outdated_claims", []),
            date_references=data.get("date_references", []),
            version_references=data.get("version_references", []),
            findings=findings,
        )

    def agent_review(
        self,
        doc_path: Path,
        perspective: ReviewPerspective,
    ) -> AgentReview:
        """
        Get review from a specific agent perspective.

        Args:
            doc_path: Path to document
            perspective: Review perspective

        Returns:
            AgentReview with findings
        """
        content, metadata = self._load_document(doc_path)

        system = self.AGENT_SYSTEMS[perspective]

        prompt = f"""Review this documentation from your perspective:

Title: {metadata.get("title", "Unknown")}
Type: {metadata.get("type", "chapter")}

Content:
{content[:8000]}

Provide:
1. Overall score (0-100)
2. Brief summary
3. Top 3 strengths
4. Top 3 weaknesses
5. Specific findings

Respond in JSON format:
{{
    "overall_score": 85,
    "summary": "...",
    "strengths": ["...", "...", "..."],
    "weaknesses": ["...", "...", "..."],
    "findings": [{{"category": "{perspective.value}", "severity": "...", "message": "..."}}]
}}"""

        response = self.llm.complete(prompt, system=system)
        data = self._parse_json_response(response)

        findings = [QualityFinding(**f) for f in data.get("findings", []) if isinstance(f, dict)]

        return AgentReview(
            perspective=perspective,
            overall_score=data.get("overall_score", 70),
            summary=data.get("summary", ""),
            strengths=data.get("strengths", [])[:5],
            weaknesses=data.get("weaknesses", [])[:5],
            findings=findings,
        )

    def multi_agent_review(
        self,
        doc_path: Path,
        perspectives: list[ReviewPerspective] = None,
    ) -> list[AgentReview]:
        """
        Get reviews from multiple agent perspectives.

        Args:
            doc_path: Path to document
            perspectives: List of perspectives (default: TECHNICAL, USER, EDITOR)

        Returns:
            List of AgentReview instances
        """
        if perspectives is None:
            perspectives = [
                ReviewPerspective.TECHNICAL,
                ReviewPerspective.USER,
                ReviewPerspective.EDITOR,
            ]

        reviews = []
        for perspective in perspectives:
            review = self.agent_review(doc_path, perspective)
            reviews.append(review)

        return reviews

    def evaluate_document(
        self,
        doc_path: Path,
        include_agents: bool = True,
    ) -> LLMQualityReport:
        """
        Perform comprehensive LLM quality evaluation.

        Args:
            doc_path: Path to document
            include_agents: Include multi-agent review

        Returns:
            LLMQualityReport with all evaluations
        """
        if not isinstance(doc_path, Path):
            doc_path = Path(doc_path)

        # Run all evaluations
        completeness = self.evaluate_completeness(doc_path)
        prerequisites = self.check_prerequisites(doc_path)
        examples = self.assess_examples(doc_path)
        outdated = self.detect_outdated_claims(doc_path)

        agent_reviews = []
        if include_agents:
            agent_reviews = self.multi_agent_review(doc_path)

        # Aggregate findings
        all_findings = (
            completeness.findings + prerequisites.findings + examples.findings + outdated.findings
        )
        for review in agent_reviews:
            all_findings.extend(review.findings)

        # Calculate overall score
        scores = [completeness.coverage_score, examples.quality_score]
        scores.extend(r.overall_score for r in agent_reviews)
        overall_score = sum(scores) / len(scores) if scores else 0

        return LLMQualityReport(
            document=doc_path,
            completeness=completeness,
            prerequisites=prerequisites,
            examples=examples,
            outdated_claims=outdated,
            agent_reviews=agent_reviews,
            overall_score=overall_score,
            all_findings=all_findings,
            model_used=self.llm.model,
        )

    def evaluate_project(
        self,
        max_documents: int = 20,
    ) -> dict:
        """
        Evaluate quality across project documents.

        Args:
            max_documents: Maximum documents to evaluate (LLM calls are expensive)

        Returns:
            Project-wide quality summary
        """
        reports = []
        evaluated = 0

        if self.project.content_dir.exists():
            for md_file in self.project.content_dir.rglob("*.md"):
                if evaluated >= max_documents:
                    break

                try:
                    rel_path = md_file.relative_to(self.project.content_dir)
                    report = self.evaluate_document(rel_path, include_agents=False)
                    reports.append(report.to_dict())
                    evaluated += 1
                except Exception as e:
                    print(f"Error evaluating {md_file}: {e}")

        # Aggregate
        if reports:
            avg_score = sum(r["overall_score"] for r in reports) / len(reports)
            all_findings = []
            for r in reports:
                all_findings.extend(r["all_findings"])
        else:
            avg_score = 0
            all_findings = []

        return {
            "summary": {
                "documents_evaluated": len(reports),
                "average_score": round(avg_score, 1),
                "total_findings": len(all_findings),
                "critical_findings": len([f for f in all_findings if f["severity"] == "critical"]),
            },
            "documents": reports,
            "model_used": self.llm.model,
        }


def evaluate_with_llm(project, doc_path: Path = None) -> dict:
    """
    Convenience function for LLM quality evaluation.

    Args:
        project: Media Engine project
        doc_path: Specific document or None for project-wide

    Returns:
        Evaluation results as dict
    """
    evaluator = LLMQualityEvaluator(project)

    if doc_path:
        report = evaluator.evaluate_document(doc_path)
        return report.to_dict()
    else:
        return evaluator.evaluate_project()


__all__ = [
    "LLMQualityEvaluator",
    "LLMClient",
    "ReviewPerspective",
    "QualityFinding",
    "CompletenessReport",
    "PrerequisiteReport",
    "ExampleAssessment",
    "OutdatedClaimReport",
    "AgentReview",
    "LLMQualityReport",
    "evaluate_with_llm",
]
