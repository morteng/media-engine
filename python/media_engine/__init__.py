"""
Media Engine - Agent-based media production framework.

Modules:
    cms: Document management with frontmatter, versioning, quality checks
    video: Timeline sequencing, capture, voiceover, captions
    diagrams: Matplotlib-based diagram generation
    builders: HTML, PPTX, XLSX generation
    templates: Professional HTML templates with sidebar, theme toggle
    assets: Font downloading, asset bundling
    quality: Content quality checks (placeholders, terminology, encoding)
    publish: Complete deliverable packaging with navigation
    status: Comprehensive project status dashboards and views
    search: Full-text search index generation
    validation: Schema and reference validation
    packs: Curated deliverable packages (investor, pilot)
    core: Configuration and theming utilities
    settings: Centralized configuration and defaults

Advanced Analysis Modules:
    semantic: Semantic similarity, duplicate detection, terminology drift
    llm_quality: LLM-powered quality evaluation and multi-agent review
    knowledge: Knowledge graph with concept extraction and prerequisite validation
    codesync: Enhanced code-documentation synchronization checking
    engagement: User engagement metrics integration
    advanced: Audience drift, question coverage, style consistency
    freshness.predictive: Predictive staleness detection
    readability.norwegian: Norwegian LIX readability analysis
"""

__version__ = "1.0.0"  # x-release-please-version

# Re-export commonly used items
from .assets import bundle_project_assets, download_google_fonts
from .cms import Document, DocumentCollection
from .core.project import Project, find_project
from .core.theme import COPPER_AND_CREAM, Theme, load_theme
from .packs import PackResult, generate_investor_pack, generate_pilot_pack
from .publish import PublishConfig, publish_project
from .quality import QualityReport, run_quality_checks
from .search import SearchIndex, build_search_index
from .settings import (
    CACHE,
    DIRS,
    ENV,
    FILES,
    NETWORK,
    QUALITY,
    VIDEO,
    VOICEOVER,
    WEB,
    get_default,
)
from .status import get_project_dashboard, print_dashboard
from .templates import TemplateRegistry, LayoutPreset, get_preset, PRESETS
from .validation import ValidationReport, validate_project

# Advanced analysis modules (lazy imports to avoid heavy dependencies)
# These are imported on-demand when used
try:
    from .semantic import SemanticAnalyzer, SemanticMatch, TerminologyDrift
except ImportError:
    SemanticAnalyzer = None  # type: ignore
    SemanticMatch = None  # type: ignore
    TerminologyDrift = None  # type: ignore

try:
    from .llm_quality import LLMQualityEvaluator, ReviewPerspective
except ImportError:
    LLMQualityEvaluator = None  # type: ignore
    ReviewPerspective = None  # type: ignore

try:
    from .knowledge import ConceptExtractor, KnowledgeGraph
except ImportError:
    KnowledgeGraph = None  # type: ignore
    ConceptExtractor = None  # type: ignore

try:
    from .codesync import EnhancedCodeSyncChecker
except ImportError:
    EnhancedCodeSyncChecker = None  # type: ignore

try:
    from .engagement import EngagementAnalyzer
except ImportError:
    EngagementAnalyzer = None  # type: ignore

try:
    from .advanced import AdvancedAnalyzer
except ImportError:
    AdvancedAnalyzer = None  # type: ignore

try:
    from .freshness.predictive import FreshnessPredictor
except ImportError:
    FreshnessPredictor = None  # type: ignore

try:
    from .readability.norwegian import NorwegianReadabilityChecker
except ImportError:
    NorwegianReadabilityChecker = None  # type: ignore

__all__ = [
    "__version__",
    # Settings
    "VIDEO",
    "VOICEOVER",
    "WEB",
    "NETWORK",
    "QUALITY",
    "CACHE",
    "DIRS",
    "FILES",
    "ENV",
    "get_default",
    # Theme
    "Theme",
    "COPPER_AND_CREAM",
    "load_theme",
    # Project
    "Project",
    "find_project",
    # CMS
    "Document",
    "DocumentCollection",
    # Templates
    "TemplateRegistry",
    "LayoutPreset",
    "get_preset",
    "PRESETS",
    # Assets
    "download_google_fonts",
    "bundle_project_assets",
    # Quality
    "run_quality_checks",
    "QualityReport",
    # Publish
    "publish_project",
    "PublishConfig",
    # Status
    "get_project_dashboard",
    "print_dashboard",
    # Search
    "SearchIndex",
    "build_search_index",
    # Validation
    "validate_project",
    "ValidationReport",
    # Packs
    "generate_investor_pack",
    "generate_pilot_pack",
    "PackResult",
    # Advanced Analysis (optional imports)
    "SemanticAnalyzer",
    "SemanticMatch",
    "TerminologyDrift",
    "LLMQualityEvaluator",
    "ReviewPerspective",
    "KnowledgeGraph",
    "ConceptExtractor",
    "EnhancedCodeSyncChecker",
    "EngagementAnalyzer",
    "AdvancedAnalyzer",
    "FreshnessPredictor",
    "NorwegianReadabilityChecker",
]
