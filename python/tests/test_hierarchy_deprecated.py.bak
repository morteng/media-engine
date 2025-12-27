"""
Tests for the hierarchy module.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from media_engine.hierarchy import (
    DocumentType,
    Lifecycle,
    RelationshipType,
    StalenessReason,
    DerivationSource,
    ConsistencyAnchor,
    HierarchyNode,
    Breadcrumb,
    NavigationContext,
    HierarchyValidationError,
    HierarchyRegistry,
    HierarchyGraph,
    HierarchyValidator,
    ValidationResult,
    AnchorChangeType,
    Anchor,
    AnchorReference,
    AnchorChange,
    AnchorValidationResult,
    AnchorRegistry,
    ImpactType,
    ImpactSeverity,
    ImpactItem,
    ImpactReport,
    ImpactAnalyzer,
    GapPriority,
    GapType,
    CoverageReport,
    CoverageAnalyzer,
    CoverageGap,
)


class TestDocumentType:
    """Tests for DocumentType enum."""

    def test_source_types(self):
        """Source types should include strategy, research, requirements."""
        source_types = DocumentType.source_types()
        assert DocumentType.STRATEGY in source_types
        assert DocumentType.RESEARCH in source_types
        assert DocumentType.REQUIREMENTS in source_types
        assert DocumentType.ARCHITECTURE not in source_types

    def test_derived_types(self):
        """Derived types should include architecture, implementation, operations."""
        derived_types = DocumentType.derived_types()
        assert DocumentType.ARCHITECTURE in derived_types
        assert DocumentType.IMPLEMENTATION in derived_types
        assert DocumentType.OPERATIONS in derived_types
        assert DocumentType.STRATEGY not in derived_types

    def test_communication_types(self):
        """Communication types should include pitch, marketing, etc."""
        comm_types = DocumentType.communication_types()
        assert DocumentType.PITCH in comm_types
        assert DocumentType.MARKETING in comm_types
        assert DocumentType.USER_DOCS in comm_types


class TestDerivationSource:
    """Tests for DerivationSource dataclass."""

    def test_creation(self):
        """Can create a derivation source."""
        source = DerivationSource(
            path=Path("requirements/prd.md"),
            version="1.2.0",
            relationship=RelationshipType.IMPLEMENTS,
            claims_used=["max_users", "pricing"],
        )
        assert source.path == Path("requirements/prd.md")
        assert source.version == "1.2.0"
        assert source.relationship == RelationshipType.IMPLEMENTS

    def test_to_dict(self):
        """Can serialize to dict."""
        source = DerivationSource(
            path=Path("requirements/prd.md"),
            version="1.0.0",
        )
        d = source.to_dict()
        assert d["path"] == "requirements/prd.md"
        assert d["version"] == "1.0.0"
        assert d["relationship"] == "implements"

    def test_from_dict(self):
        """Can deserialize from dict."""
        data = {
            "path": "requirements/prd.md",
            "version": "1.0.0",
            "relationship": "summarizes",
            "claims_used": ["fact1"],
        }
        source = DerivationSource.from_dict(data)
        assert source.path == Path("requirements/prd.md")
        assert source.version == "1.0.0"
        assert source.relationship == RelationshipType.SUMMARIZES


class TestHierarchyNode:
    """Tests for HierarchyNode dataclass."""

    def test_creation(self):
        """Can create a hierarchy node."""
        node = HierarchyNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            parent=Path("chapters/overview.md"),
            level=1,
            sequence_order=1,
            doc_type=DocumentType.CHAPTER,
        )
        assert node.title == "Introduction"
        assert node.level == 1
        assert node.doc_type == DocumentType.CHAPTER

    def test_to_dict_and_back(self):
        """Can round-trip through dict serialization."""
        node = HierarchyNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            parent=Path("chapters/overview.md"),
            level=1,
            sequence_order=1,
            doc_type=DocumentType.ARCHITECTURE,
            lifecycle=Lifecycle.VERSIONED,
            derived_from=[
                DerivationSource(path=Path("requirements/prd.md"), version="1.0.0")
            ],
            owner="team-docs",
            approvers=["alice", "bob"],
            is_stale=True,
            stale_reason=StalenessReason.SOURCE_UPDATED,
        )

        d = node.to_dict()
        restored = HierarchyNode.from_dict(d)

        assert restored.path == node.path
        assert restored.title == node.title
        assert restored.parent == node.parent
        assert restored.doc_type == node.doc_type
        assert restored.lifecycle == node.lifecycle
        assert len(restored.derived_from) == 1
        assert restored.owner == "team-docs"
        assert restored.is_stale is True
        assert restored.stale_reason == StalenessReason.SOURCE_UPDATED


class TestConsistencyAnchor:
    """Tests for ConsistencyAnchor dataclass."""

    def test_creation(self):
        """Can create a consistency anchor."""
        anchor = ConsistencyAnchor(
            id="max_users",
            value=10000,
            value_type="numeric",
            defined_in=Path("requirements/prd.md"),
            referenced_in=[Path("architecture/system.md"), Path("pitch/deck.md")],
        )
        assert anchor.id == "max_users"
        assert anchor.value == 10000
        assert len(anchor.referenced_in) == 2

    def test_to_dict_and_back(self):
        """Can round-trip through dict serialization."""
        anchor = ConsistencyAnchor(
            id="supported_langs",
            value=["en", "no", "de"],
            value_type="list",
            defined_in=Path("config/project.yaml"),
        )

        d = anchor.to_dict()
        restored = ConsistencyAnchor.from_dict(d)

        assert restored.id == anchor.id
        assert restored.value == anchor.value
        assert restored.value_type == anchor.value_type


class TestBreadcrumb:
    """Tests for Breadcrumb dataclass."""

    def test_creation(self):
        """Can create a breadcrumb."""
        crumb = Breadcrumb(
            path=Path("chapters/intro.md"),
            title="Introduction",
            doc_type=DocumentType.CHAPTER,
            level=1,
        )
        assert crumb.title == "Introduction"

    def test_to_dict(self):
        """Can serialize to dict."""
        crumb = Breadcrumb(
            path=Path("chapters/intro.md"),
            title="Intro",
            doc_type=DocumentType.CHAPTER,
            level=1,
        )
        d = crumb.to_dict()
        assert d["title"] == "Intro"
        assert d["doc_type"] == "chapter"


class TestNavigationContext:
    """Tests for NavigationContext dataclass."""

    def test_creation(self):
        """Can create navigation context."""
        ctx = NavigationContext(
            document=Path("chapters/api.md"),
            title="API Guide",
            breadcrumbs=[
                Breadcrumb(Path("chapters/overview.md"), "Overview", DocumentType.CHAPTER, 0),
                Breadcrumb(Path("chapters/api.md"), "API Guide", DocumentType.CHAPTER, 1),
            ],
            previous_sibling=Path("chapters/intro.md"),
            next_sibling=Path("chapters/advanced.md"),
            position_in_siblings=2,
            total_siblings=3,
        )
        assert ctx.title == "API Guide"
        assert len(ctx.breadcrumbs) == 2
        assert ctx.position_in_siblings == 2


class TestHierarchyValidationError:
    """Tests for HierarchyValidationError dataclass."""

    def test_creation(self):
        """Can create a validation error."""
        error = HierarchyValidationError(
            error_type="circular_reference",
            severity="error",
            document=Path("chapters/a.md"),
            message="Circular parent chain detected",
            related_documents=[Path("chapters/b.md"), Path("chapters/c.md")],
        )
        assert error.error_type == "circular_reference"
        assert error.severity == "error"
        assert len(error.related_documents) == 2


class TestHierarchyRegistry:
    """Tests for HierarchyRegistry class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        # Create minimal project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()

        # Create a mock project object
        class MockProject:
            root = project_dir
            languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject()

    def test_empty_registry(self, mock_project):
        """Registry starts empty."""
        registry = HierarchyRegistry(mock_project)
        assert registry.get_roots() == []
        assert registry.get_all_nodes() == []

    def test_set_and_get_node(self, mock_project):
        """Can add and retrieve nodes."""
        registry = HierarchyRegistry(mock_project)

        node = HierarchyNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            doc_type=DocumentType.CHAPTER,
        )
        registry.set_node(node)

        retrieved = registry.get_node(Path("chapters/intro.md"))
        assert retrieved is not None
        assert retrieved.title == "Introduction"

    def test_parent_child_relationships(self, mock_project):
        """Can track parent-child relationships."""
        registry = HierarchyRegistry(mock_project)

        # Create parent
        parent = HierarchyNode(
            path=Path("chapters/overview.md"),
            title="Overview",
        )
        registry.set_node(parent)

        # Create child
        child = HierarchyNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            parent=Path("chapters/overview.md"),
        )
        registry.set_node(child)

        # Verify relationships
        assert registry.get_parent(Path("chapters/intro.md")) == Path("chapters/overview.md")
        children = registry.get_children(Path("chapters/overview.md"))
        assert Path("chapters/intro.md") in children

    def test_roots(self, mock_project):
        """Can identify root nodes."""
        registry = HierarchyRegistry(mock_project)

        # Add root
        root = HierarchyNode(path=Path("chapters/overview.md"), title="Overview")
        registry.set_node(root)

        # Add child
        child = HierarchyNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            parent=Path("chapters/overview.md"),
        )
        registry.set_node(child)

        roots = registry.get_roots()
        assert len(roots) == 1
        assert roots[0] == Path("chapters/overview.md")

    def test_persistence(self, mock_project):
        """Registry persists to disk."""
        registry = HierarchyRegistry(mock_project)

        node = HierarchyNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
        )
        registry.set_node(node)

        # Create new registry instance
        registry2 = HierarchyRegistry(mock_project)
        retrieved = registry2.get_node(Path("chapters/intro.md"))
        assert retrieved is not None
        assert retrieved.title == "Introduction"


class TestHierarchyGraph:
    """Tests for HierarchyGraph class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()

        class MockProject:
            root = project_dir
            languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject()

    @pytest.fixture
    def graph_with_tree(self, mock_project):
        """Create a graph with a sample tree structure."""
        graph = HierarchyGraph(mock_project)

        # Create tree:
        # overview (root)
        #   ├── intro (1)
        #   ├── content (2)
        #   │   ├── structure (1)
        #   │   └── frontmatter (2)
        #   └── video (3)

        nodes = [
            HierarchyNode(Path("overview.md"), "Overview", sequence_order=0),
            HierarchyNode(Path("intro.md"), "Introduction", parent=Path("overview.md"), sequence_order=1),
            HierarchyNode(Path("content.md"), "Content", parent=Path("overview.md"), sequence_order=2),
            HierarchyNode(Path("structure.md"), "Structure", parent=Path("content.md"), sequence_order=1),
            HierarchyNode(Path("frontmatter.md"), "Frontmatter", parent=Path("content.md"), sequence_order=2),
            HierarchyNode(Path("video.md"), "Video", parent=Path("overview.md"), sequence_order=3),
        ]

        for node in nodes:
            graph.registry.set_node(node)

        return graph

    def test_get_ancestors(self, graph_with_tree):
        """Can get ancestors."""
        ancestors = graph_with_tree.get_ancestors(Path("structure.md"))
        assert len(ancestors) == 2
        assert Path("content.md") in ancestors
        assert Path("overview.md") in ancestors

    def test_get_descendants(self, graph_with_tree):
        """Can get descendants."""
        descendants = graph_with_tree.get_descendants(Path("overview.md"))
        assert len(descendants) == 5
        assert Path("intro.md") in descendants
        assert Path("structure.md") in descendants

    def test_get_level(self, graph_with_tree):
        """Can calculate depth level."""
        assert graph_with_tree.get_level(Path("overview.md")) == 0
        assert graph_with_tree.get_level(Path("content.md")) == 1
        assert graph_with_tree.get_level(Path("structure.md")) == 2

    def test_walk_preorder(self, graph_with_tree):
        """Pre-order walk visits parent before children."""
        order = list(graph_with_tree.walk_preorder(Path("overview.md")))
        assert order[0] == Path("overview.md")  # Root first
        # Children before grandchildren
        intro_idx = order.index(Path("intro.md"))
        content_idx = order.index(Path("content.md"))
        structure_idx = order.index(Path("structure.md"))
        assert content_idx < structure_idx

    def test_walk_levelorder(self, graph_with_tree):
        """Level-order walk visits by depth."""
        order = list(graph_with_tree.walk_levelorder(Path("overview.md")))
        # Level 0
        assert order[0] == Path("overview.md")
        # Level 1 (intro, content, video)
        level1 = order[1:4]
        assert Path("intro.md") in level1
        assert Path("content.md") in level1
        assert Path("video.md") in level1
        # Level 2 (structure, frontmatter)
        level2 = order[4:]
        assert Path("structure.md") in level2
        assert Path("frontmatter.md") in level2

    def test_get_breadcrumbs(self, graph_with_tree):
        """Can generate breadcrumbs."""
        crumbs = graph_with_tree.get_breadcrumbs(Path("structure.md"))
        assert len(crumbs) == 3
        assert crumbs[0].title == "Overview"
        assert crumbs[1].title == "Content"
        assert crumbs[2].title == "Structure"

    def test_navigation_context(self, graph_with_tree):
        """Can get navigation context."""
        ctx = graph_with_tree.get_navigation_context(Path("content.md"))
        assert ctx is not None
        assert ctx.title == "Content"
        assert ctx.parent.title == "Overview"
        assert len(ctx.children) == 2
        assert ctx.previous_sibling == Path("intro.md")
        assert ctx.next_sibling == Path("video.md")
        assert ctx.position_in_siblings == 2
        assert ctx.total_siblings == 3

    def test_find_common_ancestor(self, graph_with_tree):
        """Can find common ancestor."""
        # structure.md and frontmatter.md share content.md
        common = graph_with_tree.find_common_ancestor(
            Path("structure.md"), Path("frontmatter.md")
        )
        assert common == Path("content.md")

        # structure.md and video.md share overview.md
        common = graph_with_tree.find_common_ancestor(
            Path("structure.md"), Path("video.md")
        )
        assert common == Path("overview.md")

    def test_tree_string(self, graph_with_tree):
        """Can generate tree string."""
        tree_str = graph_with_tree.to_tree_string()
        assert "Overview" in tree_str
        assert "Content" in tree_str
        assert "Structure" in tree_str


class TestHierarchyValidator:
    """Tests for HierarchyValidator class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()

        class MockProject:
            root = project_dir
            languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject()

    def test_valid_hierarchy(self, mock_project):
        """Valid hierarchy passes validation."""
        graph = HierarchyGraph(mock_project)

        # Create valid tree
        nodes = [
            HierarchyNode(Path("overview.md"), "Overview"),
            HierarchyNode(Path("intro.md"), "Intro", parent=Path("overview.md")),
        ]
        for node in nodes:
            graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        result = validator.validate_all()

        assert result.is_valid
        assert result.error_count == 0

    def test_detect_cycle(self, mock_project):
        """Detects circular parent references."""
        graph = HierarchyGraph(mock_project)

        # Create cycle: a -> b -> c -> a
        nodes = [
            HierarchyNode(Path("a.md"), "A", parent=Path("c.md")),
            HierarchyNode(Path("b.md"), "B", parent=Path("a.md")),
            HierarchyNode(Path("c.md"), "C", parent=Path("b.md")),
        ]
        for node in nodes:
            graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        errors = validator.detect_cycles()

        assert len(errors) > 0
        assert any(e.error_type == "circular_reference" for e in errors)

    def test_find_orphans(self, mock_project):
        """Detects documents with missing parents."""
        graph = HierarchyGraph(mock_project)

        # Create orphan (parent doesn't exist)
        node = HierarchyNode(
            Path("orphan.md"),
            "Orphan",
            parent=Path("nonexistent.md"),
        )
        graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        errors = validator.find_orphans()

        assert len(errors) == 1
        assert errors[0].error_type == "missing_parent"
        assert errors[0].document == Path("orphan.md")

    def test_duplicate_sequence_order(self, mock_project):
        """Detects duplicate sequence orders among siblings."""
        graph = HierarchyGraph(mock_project)

        # Create parent and two children with same order
        nodes = [
            HierarchyNode(Path("parent.md"), "Parent"),
            HierarchyNode(Path("child1.md"), "Child 1", parent=Path("parent.md"), sequence_order=1),
            HierarchyNode(Path("child2.md"), "Child 2", parent=Path("parent.md"), sequence_order=1),
        ]
        for node in nodes:
            graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        warnings = validator.check_sequence_order()

        assert len(warnings) == 1
        assert warnings[0].error_type == "duplicate_order"

    def test_level_mismatch(self, mock_project):
        """Detects level mismatches."""
        graph = HierarchyGraph(mock_project)

        # Create node with wrong level
        nodes = [
            HierarchyNode(Path("parent.md"), "Parent", level=0),
            HierarchyNode(Path("child.md"), "Child", parent=Path("parent.md"), level=5),  # Should be 1
        ]
        for node in nodes:
            graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        warnings = validator.check_level_consistency()

        assert len(warnings) == 1
        assert warnings[0].error_type == "level_mismatch"
        assert warnings[0].document == Path("child.md")

    def test_invalid_derivation(self, mock_project):
        """Detects invalid derivation sources."""
        graph = HierarchyGraph(mock_project)

        # Create node with non-existent derivation source
        node = HierarchyNode(
            Path("derived.md"),
            "Derived",
            derived_from=[DerivationSource(path=Path("nonexistent.md"))],
        )
        graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        errors = validator.check_derivation_integrity()

        assert len(errors) == 1
        assert errors[0].error_type == "invalid_derivation"

    def test_validate_all(self, mock_project):
        """validate_all aggregates all checks."""
        graph = HierarchyGraph(mock_project)

        # Create hierarchy with multiple issues
        nodes = [
            HierarchyNode(Path("parent.md"), "Parent"),
            HierarchyNode(Path("child1.md"), "Child 1", parent=Path("parent.md"), sequence_order=1),
            HierarchyNode(Path("child2.md"), "Child 2", parent=Path("parent.md"), sequence_order=1),  # Duplicate
            HierarchyNode(Path("orphan.md"), "Orphan", parent=Path("missing.md")),  # Missing parent
        ]
        for node in nodes:
            graph.registry.set_node(node)

        validator = HierarchyValidator(graph)
        result = validator.validate_all()

        assert not result.is_valid  # Has critical error (missing parent)
        assert result.error_count >= 1
        assert result.warning_count >= 1

    def test_validation_result_to_dict(self, mock_project):
        """ValidationResult can be serialized."""
        result = ValidationResult(
            is_valid=False,
            errors=[
                HierarchyValidationError(
                    error_type="missing_parent",
                    severity="error",
                    document=Path("doc.md"),
                    message="Parent missing",
                )
            ],
            warnings=[],
        )

        d = result.to_dict()
        assert d["is_valid"] is False
        assert d["error_count"] == 1
        assert len(d["errors"]) == 1


class TestStalenessChecker:
    """Tests for staleness propagation."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""

        class MockProject:
            def __init__(self, root):
                self.root = root
                self.languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject(tmp_path)

    @pytest.fixture
    def graph_with_derivations(self, mock_project):
        """Create graph with derivation relationships."""
        graph = HierarchyGraph(mock_project)

        # Source document
        source = HierarchyNode(
            Path("source.md"),
            "Source",
            doc_type=DocumentType.ARCHITECTURE,
        )

        # Derived document pointing to source
        derived = HierarchyNode(
            Path("derived.md"),
            "Derived",
            doc_type=DocumentType.IMPLEMENTATION,
            derived_from=[
                DerivationSource(
                    path=Path("source.md"),
                    version="1.0.0",
                    relationship=RelationshipType.IMPLEMENTS,
                )
            ],
        )

        # Another level of derivation
        operations = HierarchyNode(
            Path("runbook.md"),
            "Runbook",
            doc_type=DocumentType.OPERATIONS,
            derived_from=[
                DerivationSource(
                    path=Path("derived.md"),
                    version="1.0.0",
                    relationship=RelationshipType.IMPLEMENTS,
                )
            ],
        )

        for node in [source, derived, operations]:
            graph.registry.set_node(node)

        return graph

    def test_check_all_fresh(self, graph_with_derivations):
        """All documents start fresh."""
        from media_engine.hierarchy import StalenessChecker

        checker = StalenessChecker(graph_with_derivations)
        report = checker.check_all()

        assert report.total_documents == 3
        # Initially all fresh (no cascade triggers)
        assert report.stale_count == 0

    def test_mark_stale(self, graph_with_derivations):
        """Can mark document as stale."""
        from media_engine.hierarchy import StalenessChecker, StalenessReason

        checker = StalenessChecker(graph_with_derivations)

        result = checker.mark_stale(
            Path("source.md"),
            StalenessReason.EXPIRED,
        )

        assert result is True

        # Verify node is marked
        node = graph_with_derivations.registry.get_node(Path("source.md"))
        assert node.is_stale is True
        assert node.stale_reason == StalenessReason.EXPIRED

    def test_mark_fresh(self, graph_with_derivations):
        """Can mark document as fresh."""
        from media_engine.hierarchy import StalenessChecker, StalenessReason

        checker = StalenessChecker(graph_with_derivations)

        # Mark stale first
        checker.mark_stale(Path("derived.md"), StalenessReason.SOURCE_UPDATED)

        # Then mark fresh
        result = checker.mark_fresh(Path("derived.md"))

        assert result is True
        node = graph_with_derivations.registry.get_node(Path("derived.md"))
        assert node.is_stale is False
        assert node.stale_reason is None

    def test_propagate_staleness(self, graph_with_derivations):
        """Staleness propagates through derivation chain."""
        from media_engine.hierarchy import StalenessChecker

        checker = StalenessChecker(graph_with_derivations)

        # Mark source stale and get impacted docs
        impacted = checker.propagate_staleness(Path("source.md"))

        # Should impact derived.md (derives from source)
        impacted_paths = [str(i.path) for i in impacted]
        assert "derived.md" in impacted_paths

    def test_staleness_report_to_dict(self, graph_with_derivations):
        """Report can be serialized."""
        from media_engine.hierarchy import StalenessChecker

        checker = StalenessChecker(graph_with_derivations)
        report = checker.check_all()

        d = report.to_dict()
        assert "stale_documents" in d
        assert "total_documents" in d
        assert "stale_percentage" in d
        assert "generated_at" in d

    def test_version_comparison(self, mock_project):
        """Version comparison works correctly."""
        from media_engine.hierarchy import StalenessChecker

        graph = HierarchyGraph(mock_project)
        checker = StalenessChecker(graph)

        # Test version comparisons
        assert checker._is_version_newer("1.0.0", "2.0.0") is True
        assert checker._is_version_newer("1.0.0", "1.1.0") is True
        assert checker._is_version_newer("1.0.0", "1.0.1") is True
        assert checker._is_version_newer("2.0.0", "1.0.0") is False
        assert checker._is_version_newer("1.0.0", "1.0.0") is False
        assert checker._is_version_newer(None, "1.0.0") is False
        assert checker._is_version_newer("1.0.0", None) is False

    def test_get_stale_chain(self, graph_with_derivations):
        """Can trace staleness back to root cause."""
        from media_engine.hierarchy import StalenessChecker, StalenessReason

        checker = StalenessChecker(graph_with_derivations)

        # Create chain: source -> derived -> runbook
        checker.mark_stale(
            Path("source.md"),
            StalenessReason.EXPIRED,
        )

        # Get chain from runbook back to source
        chain = checker.get_stale_chain(Path("source.md"))

        assert len(chain) >= 1
        assert Path("source.md") in chain


class TestAnchor:
    """Tests for Anchor dataclass."""

    def test_creation(self):
        """Can create an anchor."""
        anchor = Anchor(
            name="max_users",
            value=10000,
            document_path=Path("requirements/prd.md"),
            description="Maximum supported users",
        )
        assert anchor.name == "max_users"
        assert anchor.value == 10000
        assert anchor.description == "Maximum supported users"

    def test_equality(self):
        """Anchors are equal if name and document match."""
        anchor1 = Anchor(
            name="max_users",
            value=10000,
            document_path=Path("prd.md"),
        )
        anchor2 = Anchor(
            name="max_users",
            value=5000,  # Different value
            document_path=Path("prd.md"),
        )
        assert anchor1 == anchor2  # Same name and doc

    def test_hash(self):
        """Anchors can be used in sets."""
        anchors = {
            Anchor("a", 1, Path("doc.md")),
            Anchor("a", 2, Path("doc.md")),  # Duplicate
            Anchor("b", 1, Path("doc.md")),
        }
        assert len(anchors) == 2  # 'a' deduplicated


class TestAnchorReference:
    """Tests for AnchorReference dataclass."""

    def test_creation(self):
        """Can create an anchor reference."""
        ref = AnchorReference(
            source_document=Path("requirements/prd.md"),
            anchor_name="max_users",
            referencing_document=Path("architecture/system.md"),
            expected_value=10000,
        )
        assert ref.anchor_name == "max_users"
        assert ref.expected_value == 10000


class TestAnchorChange:
    """Tests for AnchorChange dataclass."""

    def test_creation(self):
        """Can create an anchor change."""
        change = AnchorChange(
            anchor_name="max_users",
            document_path=Path("prd.md"),
            change_type=AnchorChangeType.MODIFIED,
            old_value=10000,
            new_value=20000,
            affected_documents=[Path("system.md"), Path("api.md")],
        )
        assert change.change_type == AnchorChangeType.MODIFIED
        assert len(change.affected_documents) == 2


class TestAnchorRegistry:
    """Tests for AnchorRegistry class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()

        class MockProject:
            root = project_dir
            languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject()

    @pytest.fixture
    def registry_with_anchors(self, mock_project):
        """Create registry with anchor data."""
        from media_engine.hierarchy import HierarchyRegistry

        hierarchy_reg = HierarchyRegistry(mock_project)

        # Source document with anchors
        source = HierarchyNode(
            path=Path("requirements/prd.md"),
            title="PRD",
            anchors={
                "max_users": 10000,
                "supported_formats": ["html", "pdf", "pptx"],
                "api_version": {"value": "2.0", "description": "Current API version"},
            },
        )
        hierarchy_reg.set_node(source)

        # Document that references anchors
        arch = HierarchyNode(
            path=Path("architecture/system.md"),
            title="System Architecture",
            raw_metadata={
                "anchor_refs": [
                    {"source": "requirements/prd.md", "anchor": "max_users"},
                    {"source": "requirements/prd.md", "anchor": "api_version", "expected_value": "2.0"},
                ]
            },
        )
        hierarchy_reg.set_node(arch)

        # Another referencing document
        api = HierarchyNode(
            path=Path("docs/api.md"),
            title="API Docs",
            raw_metadata={
                "anchor_refs": [
                    {"source": "requirements/prd.md", "anchor": "api_version"},
                ]
            },
        )
        hierarchy_reg.set_node(api)

        # Build anchor registry
        anchor_reg = AnchorRegistry(hierarchy_reg)
        anchor_reg.build()

        return anchor_reg

    def test_build(self, registry_with_anchors):
        """Registry builds from hierarchy entries."""
        reg = registry_with_anchors

        # Should have anchors from source document
        anchors = reg.get_document_anchors(Path("requirements/prd.md"))
        assert len(anchors) == 3
        assert "max_users" in anchors
        assert "api_version" in anchors

    def test_get_anchor(self, registry_with_anchors):
        """Can retrieve specific anchor."""
        anchor = registry_with_anchors.get_anchor(
            Path("requirements/prd.md"),
            "max_users"
        )
        assert anchor is not None
        assert anchor.value == 10000

    def test_get_extended_anchor(self, registry_with_anchors):
        """Extended format anchors extract value correctly."""
        anchor = registry_with_anchors.get_anchor(
            Path("requirements/prd.md"),
            "api_version"
        )
        assert anchor is not None
        assert anchor.value == "2.0"
        assert anchor.description == "Current API version"

    def test_get_document_references(self, registry_with_anchors):
        """Can get references from a document."""
        refs = registry_with_anchors.get_document_references(
            Path("architecture/system.md")
        )
        assert len(refs) == 2
        anchor_names = [r.anchor_name for r in refs]
        assert "max_users" in anchor_names
        assert "api_version" in anchor_names

    def test_get_referencing_documents(self, registry_with_anchors):
        """Can find which documents reference an anchor."""
        refs = registry_with_anchors.get_referencing_documents(
            Path("requirements/prd.md"),
            "api_version"
        )
        assert len(refs) == 2
        ref_strs = [str(r) for r in refs]
        assert "architecture/system.md" in ref_strs
        assert "docs/api.md" in ref_strs

    def test_get_all_anchors(self, registry_with_anchors):
        """Can get all anchors."""
        all_anchors = registry_with_anchors.get_all_anchors()
        assert len(all_anchors) == 3

    def test_validate_references_valid(self, registry_with_anchors):
        """Valid references pass validation."""
        result = registry_with_anchors.validate_references()
        # All references are valid
        assert result.valid
        assert len(result.missing_anchors) == 0
        assert len(result.orphan_references) == 0

    def test_validate_references_missing(self, mock_project):
        """Detects references to missing anchors."""
        from media_engine.hierarchy import HierarchyRegistry

        hierarchy_reg = HierarchyRegistry(mock_project)

        # Source without the referenced anchor
        source = HierarchyNode(
            path=Path("source.md"),
            title="Source",
            anchors={"other_anchor": 123},
        )
        hierarchy_reg.set_node(source)

        # Reference to non-existent anchor
        ref_doc = HierarchyNode(
            path=Path("ref.md"),
            title="Ref",
            raw_metadata={
                "anchor_refs": [
                    {"source": "source.md", "anchor": "missing_anchor"},
                ]
            },
        )
        hierarchy_reg.set_node(ref_doc)

        anchor_reg = AnchorRegistry(hierarchy_reg)
        anchor_reg.build()

        result = anchor_reg.validate_references()
        assert not result.valid
        assert len(result.missing_anchors) == 1
        assert result.missing_anchors[0][1] == "missing_anchor"

    def test_validate_references_orphan(self, mock_project):
        """Detects references to non-existent source documents."""
        from media_engine.hierarchy import HierarchyRegistry

        hierarchy_reg = HierarchyRegistry(mock_project)

        # Reference to non-existent document
        ref_doc = HierarchyNode(
            path=Path("ref.md"),
            title="Ref",
            raw_metadata={
                "anchor_refs": [
                    {"source": "nonexistent.md", "anchor": "some_anchor"},
                ]
            },
        )
        hierarchy_reg.set_node(ref_doc)

        anchor_reg = AnchorRegistry(hierarchy_reg)
        anchor_reg.build()

        result = anchor_reg.validate_references()
        assert not result.valid
        assert len(result.orphan_references) == 1

    def test_validate_references_mismatch(self, mock_project):
        """Detects value mismatches when expected_value is specified."""
        from media_engine.hierarchy import HierarchyRegistry

        hierarchy_reg = HierarchyRegistry(mock_project)

        source = HierarchyNode(
            path=Path("source.md"),
            title="Source",
            anchors={"version": "2.0"},
        )
        hierarchy_reg.set_node(source)

        # Reference with wrong expected value
        ref_doc = HierarchyNode(
            path=Path("ref.md"),
            title="Ref",
            raw_metadata={
                "anchor_refs": [
                    {"source": "source.md", "anchor": "version", "expected_value": "1.0"},
                ]
            },
        )
        hierarchy_reg.set_node(ref_doc)

        anchor_reg = AnchorRegistry(hierarchy_reg)
        anchor_reg.build()

        result = anchor_reg.validate_references()
        # Valid because anchor exists, but mismatch recorded
        assert result.valid  # Still valid (anchor exists)
        assert len(result.value_mismatches) == 1
        mismatch = result.value_mismatches[0]
        assert mismatch[2] == "1.0"  # expected
        assert mismatch[3] == "2.0"  # actual

    def test_detect_changes_modified(self, registry_with_anchors):
        """Detects modified anchors."""
        changes = registry_with_anchors.detect_changes(
            Path("requirements/prd.md"),
            {"max_users": 20000, "supported_formats": ["html", "pdf", "pptx"], "api_version": "2.0"},
        )

        modified = [c for c in changes if c.change_type == AnchorChangeType.MODIFIED]
        assert len(modified) == 1
        assert modified[0].anchor_name == "max_users"
        assert modified[0].old_value == 10000
        assert modified[0].new_value == 20000

    def test_detect_changes_added(self, registry_with_anchors):
        """Detects added anchors."""
        changes = registry_with_anchors.detect_changes(
            Path("requirements/prd.md"),
            {
                "max_users": 10000,
                "supported_formats": ["html", "pdf", "pptx"],
                "api_version": "2.0",
                "new_anchor": "new_value",
            },
        )

        added = [c for c in changes if c.change_type == AnchorChangeType.ADDED]
        assert len(added) == 1
        assert added[0].anchor_name == "new_anchor"

    def test_detect_changes_removed(self, registry_with_anchors):
        """Detects removed anchors."""
        changes = registry_with_anchors.detect_changes(
            Path("requirements/prd.md"),
            {"max_users": 10000, "supported_formats": ["html", "pdf", "pptx"]},
            # api_version removed
        )

        removed = [c for c in changes if c.change_type == AnchorChangeType.REMOVED]
        assert len(removed) == 1
        assert removed[0].anchor_name == "api_version"
        # Should show affected documents
        assert len(removed[0].affected_documents) == 2  # system.md and api.md

    def test_detect_changes_type_changed(self, registry_with_anchors):
        """Detects type changes."""
        changes = registry_with_anchors.detect_changes(
            Path("requirements/prd.md"),
            {"max_users": "many", "supported_formats": ["html", "pdf", "pptx"], "api_version": "2.0"},
            # max_users changed from int to string
        )

        type_changed = [c for c in changes if c.change_type == AnchorChangeType.TYPE_CHANGED]
        assert len(type_changed) == 1
        assert type_changed[0].anchor_name == "max_users"

    def test_impact_summary(self, registry_with_anchors):
        """Can generate impact summary."""
        summary = registry_with_anchors.get_impact_summary()

        assert summary["total_anchors"] == 3
        assert summary["total_references"] == 3  # 2 from system.md + 1 from api.md
        assert summary["documents_with_anchors"] == 1
        assert summary["documents_with_refs"] == 2


class TestImpactItem:
    """Tests for ImpactItem dataclass."""

    def test_creation(self):
        """Can create an impact item."""
        item = ImpactItem(
            path=Path("docs/derived.md"),
            impact_type=ImpactType.DERIVED,
            severity=ImpactSeverity.HIGH,
            reason="Derives from source.md",
            depth=1,
            suggested_action="Review and update",
        )
        assert item.impact_type == ImpactType.DERIVED
        assert item.severity == ImpactSeverity.HIGH
        assert item.depth == 1

    def test_to_dict(self):
        """Can serialize to dict."""
        item = ImpactItem(
            path=Path("docs/derived.md"),
            impact_type=ImpactType.TRANSITIVE,
            severity=ImpactSeverity.MEDIUM,
            reason="Transitively derives",
        )
        d = item.to_dict()
        assert d["impact_type"] == "transitive"
        assert d["severity"] == "medium"


class TestImpactReport:
    """Tests for ImpactReport dataclass."""

    def test_creation(self):
        """Can create an impact report."""
        report = ImpactReport(
            changed_document=Path("source.md"),
            change_type="content",
            change_description="Updated source content",
            impacted_documents=[
                ImpactItem(Path("a.md"), ImpactType.DERIVED, ImpactSeverity.HIGH, "Derives", 1),
                ImpactItem(Path("b.md"), ImpactType.TRANSITIVE, ImpactSeverity.MEDIUM, "Transitive", 2),
            ],
        )
        assert report.total_impacted == 2
        assert report.by_severity["high"] == 1
        assert report.by_severity["medium"] == 1
        assert report.by_type["derived"] == 1

    def test_has_critical(self):
        """Can check for critical impacts."""
        report_no_critical = ImpactReport(
            changed_document=Path("source.md"),
            change_type="content",
            change_description="Minor change",
            impacted_documents=[
                ImpactItem(Path("a.md"), ImpactType.DERIVED, ImpactSeverity.MEDIUM, "Derives", 1),
            ],
        )
        assert not report_no_critical.has_critical

        report_critical = ImpactReport(
            changed_document=Path("source.md"),
            change_type="delete",
            change_description="Deletion",
            impacted_documents=[
                ImpactItem(Path("a.md"), ImpactType.DERIVED, ImpactSeverity.CRITICAL, "Derives", 1),
            ],
        )
        assert report_critical.has_critical

    def test_to_dict(self):
        """Can serialize to dict."""
        report = ImpactReport(
            changed_document=Path("source.md"),
            change_type="content",
            change_description="Test",
        )
        d = report.to_dict()
        assert d["changed_document"] == "source.md"
        assert d["change_type"] == "content"
        assert "generated_at" in d


class TestImpactAnalyzer:
    """Tests for ImpactAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()

        class MockProject:
            root = project_dir
            languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject()

    @pytest.fixture
    def graph_with_derivations(self, mock_project):
        """Create graph with derivation relationships."""
        graph = HierarchyGraph(mock_project)

        # Source document with anchors
        source = HierarchyNode(
            path=Path("source.md"),
            title="Source",
            doc_type=DocumentType.ARCHITECTURE,
            anchors={"api_version": "2.0"},
        )
        graph.registry.set_node(source)

        # Direct derivative
        derived1 = HierarchyNode(
            path=Path("derived1.md"),
            title="Derived 1",
            doc_type=DocumentType.IMPLEMENTATION,
            derived_from=[
                DerivationSource(
                    path=Path("source.md"),
                    version="1.0.0",
                    relationship=RelationshipType.IMPLEMENTS,
                )
            ],
        )
        graph.registry.set_node(derived1)

        # Another direct derivative
        derived2 = HierarchyNode(
            path=Path("derived2.md"),
            title="Derived 2",
            doc_type=DocumentType.OPERATIONS,
            derived_from=[
                DerivationSource(
                    path=Path("source.md"),
                    version="1.0.0",
                    relationship=RelationshipType.IMPLEMENTS,
                )
            ],
        )
        graph.registry.set_node(derived2)

        # Transitive derivative (derives from derived1)
        transitive = HierarchyNode(
            path=Path("transitive.md"),
            title="Transitive",
            doc_type=DocumentType.USER_DOCS,
            derived_from=[
                DerivationSource(
                    path=Path("derived1.md"),
                    version="1.0.0",
                )
            ],
        )
        graph.registry.set_node(transitive)

        # Document with anchor reference
        anchor_ref = HierarchyNode(
            path=Path("ref.md"),
            title="Reference",
            raw_metadata={
                "anchor_refs": [
                    {"source": "source.md", "anchor": "api_version"},
                ]
            },
        )
        graph.registry.set_node(anchor_ref)

        return graph

    def test_analyze_change(self, graph_with_derivations):
        """Can analyze impact of a change."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        report = analyzer.analyze_change(
            Path("source.md"),
            change_type="content",
            change_description="Updated API documentation",
        )

        assert report.changed_document == Path("source.md")
        assert report.total_impacted >= 2  # At least derived1 and derived2

        # Check direct derivatives are included
        impacted_paths = [str(i.path) for i in report.impacted_documents]
        assert "derived1.md" in impacted_paths
        assert "derived2.md" in impacted_paths

    def test_analyze_change_finds_transitive(self, graph_with_derivations):
        """Can find transitive derivatives."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        report = analyzer.analyze_change(Path("source.md"))

        # Check transitive derivative is included
        impacted_paths = [str(i.path) for i in report.impacted_documents]
        assert "transitive.md" in impacted_paths

        # Find the transitive item
        transitive_item = next(
            i for i in report.impacted_documents if str(i.path) == "transitive.md"
        )
        assert transitive_item.impact_type == ImpactType.TRANSITIVE
        assert transitive_item.depth == 2

    def test_analyze_change_finds_anchor_refs(self, graph_with_derivations):
        """Can find anchor references."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        report = analyzer.analyze_change(Path("source.md"), change_type="anchor")

        # Check anchor reference is included
        impacted_paths = [str(i.path) for i in report.impacted_documents]
        assert "ref.md" in impacted_paths

        # Find the anchor ref item
        anchor_item = next(
            i for i in report.impacted_documents if str(i.path) == "ref.md"
        )
        assert anchor_item.impact_type == ImpactType.ANCHOR_REF

    def test_analyze_deletion(self, graph_with_derivations):
        """Deletion analysis upgrades severities."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        report = analyzer.analyze_deletion(Path("source.md"))

        assert report.change_type == "delete"

        # Direct derivatives should be critical
        derived_items = [
            i for i in report.impacted_documents
            if i.impact_type == ImpactType.DERIVED
        ]
        for item in derived_items:
            assert item.severity == ImpactSeverity.CRITICAL

    def test_get_impact_chain(self, graph_with_derivations):
        """Can get impact chains."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        chains = analyzer.get_impact_chain(Path("source.md"))

        assert len(chains) >= 2  # At least source->derived1 and source->derived2

        # Check one chain goes to transitive
        has_transitive_chain = any(
            Path("transitive.md") in chain for chain in chains
        )
        assert has_transitive_chain

    def test_get_summary(self, graph_with_derivations):
        """Can get derivation summary."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        summary = analyzer.get_summary()

        assert summary["total_documents"] == 5
        assert summary["derived_documents"] >= 3  # derived1, derived2, transitive
        assert summary["max_derivation_depth"] >= 1

    def test_report_sorting(self, graph_with_derivations):
        """Report sorts by severity then depth."""
        analyzer = ImpactAnalyzer(graph_with_derivations)

        report = analyzer.analyze_change(Path("source.md"))

        # Check sorting - high severity items should come before medium
        severities = [i.severity for i in report.impacted_documents]
        high_indices = [i for i, s in enumerate(severities) if s == ImpactSeverity.HIGH]
        medium_indices = [i for i, s in enumerate(severities) if s == ImpactSeverity.MEDIUM]

        if high_indices and medium_indices:
            assert max(high_indices) < min(medium_indices)


class TestCoverageReport:
    """Tests for CoverageReport dataclass."""

    def test_creation(self):
        """Can create a coverage report."""
        report = CoverageReport(
            gaps=[
                CoverageGap(
                    gap_type="missing_derived",
                    expected_doc_type=DocumentType.ARCHITECTURE,
                    should_derive_from=Path("requirements/prd.md"),
                    suggested_path="architecture/prd.md",
                    priority="critical",
                    reason="Architecture needed",
                ),
            ],
            coverage_score=75.0,
            total_documents=10,
            source_documents=3,
            derived_documents=7,
        )
        assert len(report.gaps) == 1
        assert report.coverage_score == 75.0
        assert len(report.critical_gaps) == 1

    def test_by_type(self):
        """Can get gaps by type."""
        report = CoverageReport(
            gaps=[
                CoverageGap("missing_derived", DocumentType.ARCHITECTURE, Path("a.md"), "b.md", "high", ""),
                CoverageGap("missing_derived", DocumentType.IMPLEMENTATION, Path("c.md"), "d.md", "medium", ""),
                CoverageGap("orphan_document", DocumentType.CHAPTER, Path("e.md"), "e.md", "low", ""),
            ],
        )
        assert report.by_type["missing_derived"] == 2
        assert report.by_type["orphan_document"] == 1

    def test_to_dict(self):
        """Can serialize to dict."""
        report = CoverageReport(
            coverage_score=80.0,
            total_documents=5,
        )
        d = report.to_dict()
        assert d["coverage_score"] == 80.0
        assert d["statistics"]["total_documents"] == 5
        assert "generated_at" in d


class TestCoverageAnalyzer:
    """Tests for CoverageAnalyzer class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()

        class MockProject:
            root = project_dir
            languages = ["en"]

            def list_chapters(self, lang):
                return []

        return MockProject()

    @pytest.fixture
    def graph_with_coverage_gaps(self, mock_project):
        """Create graph with various coverage scenarios."""
        graph = HierarchyGraph(mock_project)

        # Requirements document (source)
        requirements = HierarchyNode(
            path=Path("requirements/prd.md"),
            title="Product Requirements",
            doc_type=DocumentType.REQUIREMENTS,
        )
        graph.registry.set_node(requirements)

        # Architecture that implements requirements (good)
        architecture = HierarchyNode(
            path=Path("architecture/system.md"),
            title="System Architecture",
            doc_type=DocumentType.ARCHITECTURE,
            derived_from=[
                DerivationSource(
                    path=Path("requirements/prd.md"),
                    version="1.0.0",
                    relationship=RelationshipType.IMPLEMENTS,
                )
            ],
        )
        graph.registry.set_node(architecture)

        # Orphan document (no parent, no derivation, not a source type)
        orphan = HierarchyNode(
            path=Path("docs/orphan.md"),
            title="Orphan Doc",
            doc_type=DocumentType.CHAPTER,
        )
        graph.registry.set_node(orphan)

        # Research document (source, no derivatives yet - should create gap)
        research = HierarchyNode(
            path=Path("research/market.md"),
            title="Market Research",
            doc_type=DocumentType.RESEARCH,
        )
        graph.registry.set_node(research)

        return graph

    def test_analyze(self, graph_with_coverage_gaps):
        """Can analyze coverage."""
        analyzer = CoverageAnalyzer(graph_with_coverage_gaps)
        report = analyzer.analyze()

        assert report.total_documents == 4
        assert report.source_documents >= 2  # requirements, research
        assert report.derived_documents >= 1  # architecture
        assert report.orphan_documents >= 1  # orphan

    def test_finds_missing_derived(self, graph_with_coverage_gaps):
        """Can find missing derived documents."""
        analyzer = CoverageAnalyzer(graph_with_coverage_gaps)
        report = analyzer.analyze()

        # Research should have a requirements gap
        missing_derived = [g for g in report.gaps if g.gap_type == "missing_derived"]
        research_gaps = [g for g in missing_derived if "research" in str(g.should_derive_from)]

        # Research should suggest creating requirements
        assert len(research_gaps) > 0

    def test_finds_orphans(self, graph_with_coverage_gaps):
        """Can find orphan documents."""
        analyzer = CoverageAnalyzer(graph_with_coverage_gaps)
        report = analyzer.analyze()

        orphan_gaps = [g for g in report.gaps if g.gap_type == "orphan_document"]
        assert len(orphan_gaps) >= 1
        assert any("orphan" in str(g.should_derive_from) for g in orphan_gaps)

    def test_get_suggestions(self, graph_with_coverage_gaps):
        """Can get prioritized suggestions."""
        analyzer = CoverageAnalyzer(graph_with_coverage_gaps)
        suggestions = analyzer.get_suggestions()

        # Should have suggestions
        assert len(suggestions) > 0

        # Check structure
        if suggestions:
            s = suggestions[0]
            assert "priority" in s
            assert "action" in s
            assert "target" in s

    def test_get_completeness_by_type(self, graph_with_coverage_gaps):
        """Can get completeness metrics by type."""
        analyzer = CoverageAnalyzer(graph_with_coverage_gaps)
        by_type = analyzer.get_completeness_by_type()

        # Should have types
        assert "requirements" in by_type
        assert by_type["requirements"]["count"] >= 1

        # Architecture should have derivation
        if "architecture" in by_type:
            assert by_type["architecture"]["with_derivation"] >= 1

    def test_incomplete_chain_detection(self, mock_project):
        """Can detect incomplete derivation chains."""
        graph = HierarchyGraph(mock_project)

        # Document that derives from non-existent source
        derived = HierarchyNode(
            path=Path("docs/derived.md"),
            title="Derived",
            doc_type=DocumentType.IMPLEMENTATION,
            derived_from=[
                DerivationSource(
                    path=Path("nonexistent/source.md"),
                    version="1.0.0",
                )
            ],
        )
        graph.registry.set_node(derived)

        analyzer = CoverageAnalyzer(graph)
        report = analyzer.analyze()

        incomplete_gaps = [g for g in report.gaps if g.gap_type == "incomplete_chain"]
        assert len(incomplete_gaps) >= 1

    def test_coverage_score_calculation(self, graph_with_coverage_gaps):
        """Coverage score is calculated correctly."""
        analyzer = CoverageAnalyzer(graph_with_coverage_gaps)
        report = analyzer.analyze()

        # Score should be between 0 and 100
        assert 0 <= report.coverage_score <= 100

        # Score should be penalized for critical/high gaps
        if report.critical_gaps or report.high_gaps:
            assert report.coverage_score < 100
