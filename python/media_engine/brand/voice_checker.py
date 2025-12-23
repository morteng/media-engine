"""
Voice Consistency Checker

Integrates StyleConsistencyAnalyzer with brand voice profile
to check content against voice guidelines.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .voice import VoiceProfile


@dataclass
class VoiceIssue:
    """A voice consistency issue found in a document."""

    type: str  # passive_voice, tone_mismatch, first_person_usage, etc.
    severity: str = "warning"  # info, warning, error
    message: str = ""
    suggestion: str = ""
    location: Optional[str] = None  # Line or section reference

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
            "location": self.location,
        }


@dataclass
class VoiceCheckResult:
    """Result of voice consistency check on a document."""

    document: Path
    issues: List[VoiceIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": str(self.document),
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
            "passed": self.passed,
        }


class VoiceConsistencyChecker:
    """
    Checks document content against brand voice guidelines.

    Analyzes:
    - Active vs passive voice ratio
    - Person usage (first/second/third)
    - Formality level
    - Sentence length
    - Avoided phrases
    - Preferred terminology
    """

    # Passive voice patterns
    PASSIVE_PATTERNS = [
        r"\b(?:is|are|was|were|been|being)\s+\w+ed\b",
        r"\b(?:is|are|was|were|been|being)\s+\w+en\b",
    ]

    # Person indicators
    FIRST_PERSON = re.compile(r"\b(?:I|we|our|us|my)\b", re.IGNORECASE)
    SECOND_PERSON = re.compile(r"\b(?:you|your|yours)\b", re.IGNORECASE)
    THIRD_PERSON = re.compile(r"\b(?:they|their|he|she|it|its|them)\b", re.IGNORECASE)

    # Formality indicators
    INFORMAL_PATTERNS = [
        r"\b(?:gonna|wanna|gotta|kinda|sorta)\b",
        r"\b(?:cool|awesome|super|really|pretty)\b",
        r"!{2,}",
    ]
    FORMAL_PATTERNS = [
        r"\b(?:therefore|however|furthermore|consequently|moreover)\b",
        r"\b(?:shall|hereby|aforementioned|herein)\b",
    ]

    def __init__(self, voice_profile: Optional[VoiceProfile] = None):
        """
        Initialize checker with voice profile.

        Args:
            voice_profile: Brand voice profile to check against.
                          If None, uses sensible defaults.
        """
        self.voice_profile = voice_profile

    def check_content(
        self,
        content: str,
        doc_path: Path,
        doc_type: Optional[str] = None,
        audience: Optional[str] = None,
    ) -> VoiceCheckResult:
        """
        Check content against voice guidelines.

        Args:
            content: The document content to check
            doc_path: Path to the document (for reporting)
            doc_type: Document type for context-specific rules
            audience: Target audience for context-specific rules

        Returns:
            VoiceCheckResult with issues and metrics
        """
        issues: List[VoiceIssue] = []
        metrics: Dict[str, Any] = {}

        # Get effective voice profile for context
        if self.voice_profile:
            effective_profile = self.voice_profile.get_for_context(doc_type, audience)
        else:
            effective_profile = None

        # Clean content (remove code blocks)
        clean_content = self._clean_content(content)

        if not clean_content.strip():
            return VoiceCheckResult(document=doc_path, passed=True)

        # Analyze and check various aspects
        issues.extend(self._check_active_voice(clean_content, effective_profile, metrics))
        issues.extend(self._check_person_usage(clean_content, effective_profile, metrics))
        issues.extend(self._check_formality(clean_content, effective_profile, metrics))
        issues.extend(self._check_sentence_length(clean_content, effective_profile, metrics))
        issues.extend(self._check_avoided_phrases(clean_content, effective_profile))
        issues.extend(self._check_terminology(clean_content, effective_profile))

        # Determine pass/fail (fail if any error severity, or > 3 warnings)
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        passed = error_count == 0 and warning_count <= 3

        return VoiceCheckResult(
            document=doc_path,
            issues=issues,
            metrics=metrics,
            passed=passed,
        )

    def _clean_content(self, content: str) -> str:
        """Remove code blocks and inline code from content."""
        # Remove fenced code blocks
        clean = re.sub(r"```[\s\S]*?```", "", content)
        # Remove inline code
        clean = re.sub(r"`[^`]+`", "", clean)
        # Remove frontmatter
        clean = re.sub(r"^---[\s\S]*?---", "", clean)
        return clean

    def _check_active_voice(
        self, content: str, profile: Optional[VoiceProfile], metrics: Dict[str, Any]
    ) -> List[VoiceIssue]:
        """Check active voice percentage against target."""
        issues = []

        # Count passive voice instances
        passive_count = 0
        for pattern in self.PASSIVE_PATTERNS:
            passive_count += len(re.findall(pattern, content, re.IGNORECASE))

        # Estimate total verb phrases
        total_verbs = len(re.findall(r"\b(?:is|are|was|were|have|has|had|do|does|did)\b", content, re.IGNORECASE))
        total_verbs = max(total_verbs, 1)

        active_ratio = 1 - (passive_count / total_verbs)
        active_pct = active_ratio * 100

        metrics["active_voice_percentage"] = round(active_pct, 1)
        metrics["passive_count"] = passive_count

        # Get target
        target = 0.8  # Default
        if profile and profile.style:
            target = profile.style.active_voice_target

        target_pct = target * 100

        if active_pct < target_pct - 10:  # Allow 10% tolerance
            severity = "warning" if active_pct >= target_pct - 20 else "error"
            issues.append(
                VoiceIssue(
                    type="passive_voice",
                    severity=severity,
                    message=f"Active voice at {active_pct:.0f}%, target is {target_pct:.0f}%",
                    suggestion="Rewrite passive sentences to active voice",
                )
            )

        return issues

    def _check_person_usage(
        self, content: str, profile: Optional[VoiceProfile], metrics: Dict[str, Any]
    ) -> List[VoiceIssue]:
        """Check person usage (first/second/third) against preferences."""
        issues = []

        first_count = len(self.FIRST_PERSON.findall(content))
        second_count = len(self.SECOND_PERSON.findall(content))
        third_count = len(self.THIRD_PERSON.findall(content))
        total = first_count + second_count + third_count or 1

        metrics["person_usage"] = {
            "first": round(first_count / total * 100, 1),
            "second": round(second_count / total * 100, 1),
            "third": round(third_count / total * 100, 1),
        }

        if profile and profile.style:
            # Check first person
            if not profile.style.use_first_person and first_count > 5:
                issues.append(
                    VoiceIssue(
                        type="first_person_usage",
                        severity="info",
                        message=f"First person ('I', 'we') used {first_count} times, brand prefers avoiding it",
                        suggestion="Consider rephrasing to remove first person references",
                    )
                )

            # Check second person
            if not profile.style.use_second_person and second_count > 5:
                issues.append(
                    VoiceIssue(
                        type="second_person_usage",
                        severity="info",
                        message=f"Second person ('you', 'your') used {second_count} times",
                        suggestion="Consider using third person instead",
                    )
                )

        return issues

    def _check_formality(
        self, content: str, profile: Optional[VoiceProfile], metrics: Dict[str, Any]
    ) -> List[VoiceIssue]:
        """Check formality level matches tone."""
        issues = []

        # Count formality indicators
        informal_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in self.INFORMAL_PATTERNS)
        formal_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in self.FORMAL_PATTERNS)

        if formal_count > informal_count * 2:
            detected_formality = "formal"
        elif informal_count > formal_count * 2:
            detected_formality = "informal"
        else:
            detected_formality = "conversational"

        metrics["detected_formality"] = detected_formality
        metrics["informal_markers"] = informal_count
        metrics["formal_markers"] = formal_count

        # Compare to expected tone
        if profile:
            expected_tone = profile.tone
            formality_level = profile.formality_level

            # Map tones to expected formality
            tone_formality_map = {
                "formal": "formal",
                "technical": "formal",
                "conversational": "conversational",
                "casual": "informal",
                "procedural": "conversational",
                "persuasive": "conversational",
            }

            expected_formality = tone_formality_map.get(expected_tone, "conversational")

            # Check for mismatch
            if detected_formality != expected_formality:
                # Only flag if significant mismatch
                if (detected_formality == "formal" and expected_formality == "informal") or \
                   (detected_formality == "informal" and expected_formality == "formal"):
                    issues.append(
                        VoiceIssue(
                            type="tone_mismatch",
                            severity="warning",
                            message=f"Document tone is '{detected_formality}', expected '{expected_formality}' for {expected_tone} content",
                            suggestion=f"Adjust language formality to match {expected_tone} tone",
                        )
                    )

        return issues

    def _check_sentence_length(
        self, content: str, profile: Optional[VoiceProfile], metrics: Dict[str, Any]
    ) -> List[VoiceIssue]:
        """Check average sentence length against target."""
        issues = []

        # Split into sentences
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return issues

        # Calculate word counts
        word_counts = [len(s.split()) for s in sentences]
        avg_length = sum(word_counts) / len(word_counts)

        metrics["avg_sentence_length"] = round(avg_length, 1)
        metrics["sentence_count"] = len(sentences)
        metrics["long_sentences"] = sum(1 for c in word_counts if c > 30)

        # Get target
        target = 18  # Default
        if profile and profile.style:
            target = profile.style.sentence_length_target

        # Check deviation
        deviation = abs(avg_length - target)
        if deviation > 8:
            direction = "long" if avg_length > target else "short"
            issues.append(
                VoiceIssue(
                    type="sentence_length",
                    severity="info",
                    message=f"Average sentence length is {avg_length:.0f} words, target is {target}",
                    suggestion=f"Consider {'shortening' if direction == 'long' else 'expanding'} sentences",
                )
            )

        return issues

    def _check_avoided_phrases(
        self, content: str, profile: Optional[VoiceProfile]
    ) -> List[VoiceIssue]:
        """Check for phrases that should be avoided."""
        issues = []

        if not profile or not profile.avoid_phrases:
            return issues

        content_lower = content.lower()
        found_phrases = []

        for phrase in profile.avoid_phrases:
            if phrase.lower() in content_lower:
                found_phrases.append(phrase)

        if found_phrases:
            issues.append(
                VoiceIssue(
                    type="avoided_phrase",
                    severity="warning",
                    message=f"Contains avoided phrases: {', '.join(found_phrases[:5])}",
                    suggestion="Rephrase to remove these expressions",
                )
            )

        return issues

    def _check_terminology(
        self, content: str, profile: Optional[VoiceProfile]
    ) -> List[VoiceIssue]:
        """Check for non-preferred terminology."""
        issues = []

        if not profile or not profile.preferred_terms:
            return issues

        content_lower = content.lower()
        found_issues = []

        for term_pref in profile.preferred_terms:
            for avoid_term in term_pref.avoid:
                # Use word boundary matching
                pattern = r"\b" + re.escape(avoid_term.lower()) + r"\b"
                if re.search(pattern, content_lower):
                    found_issues.append(f"'{avoid_term}' -> '{term_pref.prefer}'")

        if found_issues:
            issues.append(
                VoiceIssue(
                    type="terminology",
                    severity="info",
                    message=f"Non-preferred terms: {', '.join(found_issues[:5])}",
                    suggestion="Consider using preferred terminology",
                )
            )

        return issues


def check_document_voice(
    content: str,
    doc_path: Path,
    voice_profile: Optional[VoiceProfile] = None,
    doc_type: Optional[str] = None,
    audience: Optional[str] = None,
) -> VoiceCheckResult:
    """
    Convenience function to check a document against voice guidelines.

    Args:
        content: Document content
        doc_path: Path to document
        voice_profile: Brand voice profile (optional)
        doc_type: Document type for context
        audience: Target audience for context

    Returns:
        VoiceCheckResult with issues and metrics
    """
    checker = VoiceConsistencyChecker(voice_profile)
    return checker.check_content(content, doc_path, doc_type, audience)
