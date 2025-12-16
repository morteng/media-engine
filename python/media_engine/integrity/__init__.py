"""
Asset Integrity & Terminology Consistency for Media Engine

Provides:
- Asset checksums to detect unauthorized modifications
- Terminology glossary enforcement across documents
- Consistent language and phrasing checks
"""

import json
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from collections import defaultdict


# === Asset Integrity ===

@dataclass
class AssetChecksum:
    """Checksum record for an asset file."""
    path: str
    checksum: str
    algorithm: str = "sha256"
    size_bytes: int = 0
    recorded_at: str = ""
    recorded_by: Optional[str] = None


class AssetIntegrityChecker:
    """
    Tracks and verifies asset file integrity.

    Detects:
    - Modified assets (checksum mismatch)
    - Missing assets
    - New untracked assets
    """

    def __init__(self, project):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.data_path = self.data_dir / "asset_checksums.json"
        self._checksums: dict[str, AssetChecksum] = {}
        self._load()

    def _load(self):
        """Load checksum data from disk."""
        if self.data_path.exists():
            with open(self.data_path) as f:
                data = json.load(f)
                for path, info in data.items():
                    self._checksums[path] = AssetChecksum(
                        path=path,
                        checksum=info["checksum"],
                        algorithm=info.get("algorithm", "sha256"),
                        size_bytes=info.get("size_bytes", 0),
                        recorded_at=info.get("recorded_at", ""),
                        recorded_by=info.get("recorded_by"),
                    )

    def _save(self):
        """Save checksum data to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {}
        for path, cs in self._checksums.items():
            data[path] = {
                "checksum": cs.checksum,
                "algorithm": cs.algorithm,
                "size_bytes": cs.size_bytes,
                "recorded_at": cs.recorded_at,
                "recorded_by": cs.recorded_by,
            }
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def record_asset(self, file_path: Path, recorded_by: str = None):
        """Record checksum for an asset."""
        from datetime import datetime

        if not file_path.exists():
            return None

        checksum = self.compute_checksum(file_path)
        relative = str(file_path.relative_to(self.project.root))

        self._checksums[relative] = AssetChecksum(
            path=relative,
            checksum=checksum,
            size_bytes=file_path.stat().st_size,
            recorded_at=datetime.now().isoformat(),
            recorded_by=recorded_by,
        )
        self._save()
        return self._checksums[relative]

    def verify_asset(self, file_path: Path) -> dict:
        """
        Verify an asset's integrity.

        Returns dict with status: "valid", "modified", "missing", "untracked"
        """
        relative = str(file_path.relative_to(self.project.root))

        if relative not in self._checksums:
            if file_path.exists():
                return {"status": "untracked", "path": relative}
            return {"status": "missing", "path": relative}

        if not file_path.exists():
            return {
                "status": "missing",
                "path": relative,
                "expected_checksum": self._checksums[relative].checksum,
            }

        current = self.compute_checksum(file_path)
        expected = self._checksums[relative].checksum

        if current == expected:
            return {"status": "valid", "path": relative, "checksum": current}
        else:
            return {
                "status": "modified",
                "path": relative,
                "expected_checksum": expected,
                "current_checksum": current,
            }

    def verify_all(self) -> dict:
        """Verify all tracked assets."""
        results = {
            "valid": [],
            "modified": [],
            "missing": [],
            "untracked": [],
        }

        # Check tracked assets
        for relative in self._checksums:
            file_path = self.project.root / relative
            result = self.verify_asset(file_path)
            results[result["status"]].append(result)

        # Find untracked assets
        for asset_path in self._find_all_assets():
            relative = str(asset_path.relative_to(self.project.root))
            if relative not in self._checksums:
                results["untracked"].append({
                    "status": "untracked",
                    "path": relative,
                })

        return results

    def _find_all_assets(self) -> list[Path]:
        """Find all asset files in the project."""
        asset_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx",
            ".mp3", ".mp4", ".wav", ".mov",
            ".ttf", ".otf", ".woff", ".woff2",
        }

        assets = []
        assets_dir = self.project.assets_dir
        if assets_dir.exists():
            for ext in asset_extensions:
                assets.extend(assets_dir.rglob(f"*{ext}"))

        return assets

    def record_all(self, recorded_by: str = None) -> int:
        """Record checksums for all assets."""
        count = 0
        for asset_path in self._find_all_assets():
            self.record_asset(asset_path, recorded_by)
            count += 1
        return count

    def generate_report(self) -> dict:
        """Generate integrity report."""
        verification = self.verify_all()
        return {
            "summary": {
                "total_tracked": len(self._checksums),
                "valid": len(verification["valid"]),
                "modified": len(verification["modified"]),
                "missing": len(verification["missing"]),
                "untracked": len(verification["untracked"]),
            },
            "issues": {
                "modified": verification["modified"],
                "missing": verification["missing"],
            },
            "untracked": verification["untracked"],
        }


# === Terminology Consistency ===

@dataclass
class GlossaryTerm:
    """A term in the glossary."""
    term: str
    definition: str
    preferred_forms: list[str] = field(default_factory=list)
    avoid_forms: list[str] = field(default_factory=list)
    context: Optional[str] = None
    language: str = "en"


class TerminologyChecker:
    """
    Enforces terminology consistency across documents.

    Features:
    - Glossary management
    - Inconsistent term detection
    - Suggested replacements
    - Multi-language support
    """

    def __init__(self, project):
        self.project = project
        self.data_dir = project.root / ".media-engine"
        self.glossary_path = self.data_dir / "glossary.json"
        self._terms: dict[str, list[GlossaryTerm]] = defaultdict(list)
        self._load()

    def _load(self):
        """Load glossary from disk."""
        if self.glossary_path.exists():
            with open(self.glossary_path) as f:
                data = json.load(f)
                for term_data in data.get("terms", []):
                    term = GlossaryTerm(
                        term=term_data["term"],
                        definition=term_data.get("definition", ""),
                        preferred_forms=term_data.get("preferred_forms", []),
                        avoid_forms=term_data.get("avoid_forms", []),
                        context=term_data.get("context"),
                        language=term_data.get("language", "en"),
                    )
                    self._terms[term.language].append(term)

    def _save(self):
        """Save glossary to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        terms = []
        for lang_terms in self._terms.values():
            for term in lang_terms:
                terms.append({
                    "term": term.term,
                    "definition": term.definition,
                    "preferred_forms": term.preferred_forms,
                    "avoid_forms": term.avoid_forms,
                    "context": term.context,
                    "language": term.language,
                })
        with open(self.glossary_path, "w") as f:
            json.dump({"terms": terms}, f, indent=2)

    def add_term(
        self,
        term: str,
        definition: str,
        preferred_forms: list[str] = None,
        avoid_forms: list[str] = None,
        language: str = "en",
    ):
        """Add a term to the glossary."""
        glossary_term = GlossaryTerm(
            term=term,
            definition=definition,
            preferred_forms=preferred_forms or [term],
            avoid_forms=avoid_forms or [],
            language=language,
        )
        self._terms[language].append(glossary_term)
        self._save()

    def check_document(self, doc_path: Path, language: str = None) -> list[dict]:
        """
        Check a document for terminology issues.

        Returns list of issues found.
        """
        from ..cms.document import Document

        doc = Document.load(doc_path)
        content = doc.content.lower()
        lang = language or doc.metadata.get("language", "en")

        issues = []
        for term in self._terms.get(lang, []):
            # Check for forms to avoid
            for avoid in term.avoid_forms:
                pattern = r'\b' + re.escape(avoid.lower()) + r'\b'
                for match in re.finditer(pattern, content):
                    issues.append({
                        "type": "avoid_form",
                        "term": term.term,
                        "found": avoid,
                        "preferred": term.preferred_forms[0] if term.preferred_forms else term.term,
                        "position": match.start(),
                        "context": content[max(0, match.start()-30):match.end()+30],
                    })

        return issues

    def check_all_documents(self) -> dict[str, list[dict]]:
        """Check all documents for terminology issues."""
        results = {}
        for lang in self.project.languages:
            for chapter in self.project.list_chapters(lang):
                issues = self.check_document(chapter, lang)
                if issues:
                    results[str(chapter)] = issues
        return results

    def get_glossary(self, language: str = None) -> list[GlossaryTerm]:
        """Get glossary terms for a language."""
        if language:
            return self._terms.get(language, [])
        return [term for terms in self._terms.values() for term in terms]

    def export_glossary(self, output_path: Path, format: str = "markdown") -> Path:
        """Export glossary to file."""
        if format == "markdown":
            lines = ["# Glossary\n"]
            for lang, terms in self._terms.items():
                lines.append(f"\n## {lang.upper()}\n")
                for term in sorted(terms, key=lambda t: t.term.lower()):
                    lines.append(f"### {term.term}")
                    lines.append(f"{term.definition}\n")
                    if term.preferred_forms:
                        lines.append(f"**Preferred**: {', '.join(term.preferred_forms)}")
                    if term.avoid_forms:
                        lines.append(f"**Avoid**: {', '.join(term.avoid_forms)}")
                    lines.append("")
            with open(output_path, "w") as f:
                f.write("\n".join(lines))
        elif format == "json":
            with open(output_path, "w") as f:
                json.dump({"terms": self.get_glossary()}, f, indent=2, default=str)
        return output_path

    def generate_report(self) -> dict:
        """Generate terminology report."""
        all_issues = self.check_all_documents()
        total_issues = sum(len(issues) for issues in all_issues.values())

        return {
            "summary": {
                "total_terms": sum(len(terms) for terms in self._terms.values()),
                "languages": list(self._terms.keys()),
                "documents_with_issues": len(all_issues),
                "total_issues": total_issues,
            },
            "issues_by_document": {
                path: len(issues) for path, issues in all_issues.items()
            },
            "sample_issues": [
                {"document": path, "issue": issues[0]}
                for path, issues in list(all_issues.items())[:5]
                if issues
            ],
        }


# === Combined Integrity Report ===

def generate_full_integrity_report(project) -> dict:
    """Generate comprehensive integrity report."""
    asset_checker = AssetIntegrityChecker(project)
    term_checker = TerminologyChecker(project)

    return {
        "assets": asset_checker.generate_report(),
        "terminology": term_checker.generate_report(),
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }


__all__ = [
    "AssetChecksum",
    "AssetIntegrityChecker",
    "GlossaryTerm",
    "TerminologyChecker",
    "generate_full_integrity_report",
]
