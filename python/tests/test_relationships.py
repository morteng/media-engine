"""
Tests for the Unified Relationship Registry.

Tests the RegistryManager singleton, UnifiedRegistry, and related components.
"""

from pathlib import Path

import pytest
from media_engine.relationships import (
    ChangeInfo,
    DocumentNode,
    EdgeType,
    RelationshipEdge,
    UnifiedRegistry,
    get_registry_manager,
    init_registry_manager,
    reset_registry_manager,
)


class TestEdgeType:
    """Tests for EdgeType enum."""

    def test_all_types_exist(self):
        """All expected edge types should exist."""
        assert EdgeType.PARENT is not None
        assert EdgeType.IMPLEMENTS is not None
        assert EdgeType.EXTENDS is not None
        assert EdgeType.SUMMARIZES is not None
        assert EdgeType.TRANSLATES is not None
        assert EdgeType.REFERENCES is not None
        assert EdgeType.USES_ASSET is not None
        assert EdgeType.ANCHOR_REF is not None
        assert EdgeType.DEPENDS_ON is not None

    def test_value_is_string(self):
        """Edge type values should be strings."""
        assert EdgeType.PARENT.value == "parent"
        assert EdgeType.TRANSLATES.value == "translates"


class TestDocumentNode:
    """Tests for DocumentNode dataclass."""

    def test_creation(self):
        """Can create a document node."""
        node = DocumentNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            doc_type="chapter",
        )
        assert node.path == Path("chapters/intro.md")
        assert node.title == "Introduction"
        assert node.is_stale is False
        assert node.stale_reasons == []

    def test_to_dict(self):
        """Can serialize to dict."""
        node = DocumentNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            doc_type="chapter",
            is_stale=True,
            stale_reasons=["source_updated"],
        )
        d = node.to_dict()
        assert d["path"] == "chapters/intro.md"
        assert d["title"] == "Introduction"
        assert d["is_stale"] is True
        assert "source_updated" in d["stale_reasons"]

    def test_from_dict(self):
        """Can deserialize from dict."""
        data = {
            "path": "chapters/intro.md",
            "title": "Introduction",
            "doc_type": "chapter",
            "is_stale": True,
            "stale_reasons": ["expired"],
        }
        node = DocumentNode.from_dict(data)
        assert node.path == Path("chapters/intro.md")
        assert node.title == "Introduction"
        assert node.is_stale is True


class TestRelationshipEdge:
    """Tests for RelationshipEdge dataclass."""

    def test_creation(self):
        """Can create a relationship edge."""
        edge = RelationshipEdge(
            source=Path("chapters/derived.md"),
            target=Path("chapters/source.md"),
            edge_type=EdgeType.IMPLEMENTS,
        )
        assert edge.source == Path("chapters/derived.md")
        assert edge.target == Path("chapters/source.md")
        assert edge.edge_type == EdgeType.IMPLEMENTS
        assert edge.is_stale is False

    def test_to_dict(self):
        """Can serialize to dict."""
        edge = RelationshipEdge(
            source=Path("derived.md"),
            target=Path("source.md"),
            edge_type=EdgeType.TRANSLATES,
            target_hash="def67890",
        )
        d = edge.to_dict()
        assert d["source"] == "derived.md"
        assert d["target"] == "source.md"
        assert d["edge_type"] == "translates"
        assert d["target_hash"] == "def67890"


class TestUnifiedRegistry:
    """Tests for UnifiedRegistry class."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()
        (project_dir / "content").mkdir()
        (project_dir / "content" / "en").mkdir()
        (project_dir / "content" / "en" / "chapters").mkdir()

        class MockProject:
            root = project_dir
            content_dir = project_dir / "content"
            languages = {"en": {"name": "English"}}
            source_language = "en"

            def list_chapters(self, lang):
                return []

        return MockProject()

    def test_empty_registry(self, mock_project):
        """Registry starts empty."""
        registry = UnifiedRegistry(mock_project)
        nodes = list(registry.all_nodes())
        assert len(nodes) == 0

    def test_add_and_get_node(self, mock_project):
        """Can add and retrieve nodes."""
        registry = UnifiedRegistry(mock_project)

        node = DocumentNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
            doc_type="chapter",
        )
        registry.add_node(node)

        retrieved = registry.get_node(Path("chapters/intro.md"))
        assert retrieved is not None
        assert retrieved.title == "Introduction"

    def test_add_and_get_edge(self, mock_project):
        """Can add and retrieve edges."""
        registry = UnifiedRegistry(mock_project)

        # Add nodes first
        source = DocumentNode(path=Path("source.md"), title="Source")
        derived = DocumentNode(path=Path("derived.md"), title="Derived")
        registry.add_node(source)
        registry.add_node(derived)

        # Add edge
        edge = RelationshipEdge(
            source=Path("derived.md"),
            target=Path("source.md"),
            edge_type=EdgeType.IMPLEMENTS,
        )
        registry.add_edge(edge)

        # Get outgoing edges
        edges = registry.get_outgoing_edges(Path("derived.md"))
        assert len(edges) == 1
        assert edges[0].target == Path("source.md")

    def test_get_children(self, mock_project):
        """Can get children of a parent node."""
        registry = UnifiedRegistry(mock_project)

        # Add parent and children
        parent = DocumentNode(path=Path("parent.md"), title="Parent")
        child1 = DocumentNode(path=Path("child1.md"), title="Child 1")
        child2 = DocumentNode(path=Path("child2.md"), title="Child 2")
        registry.add_node(parent)
        registry.add_node(child1)
        registry.add_node(child2)

        # Add parent edges
        registry.add_edge(RelationshipEdge(
            source=Path("child1.md"),
            target=Path("parent.md"),
            edge_type=EdgeType.PARENT,
        ))
        registry.add_edge(RelationshipEdge(
            source=Path("child2.md"),
            target=Path("parent.md"),
            edge_type=EdgeType.PARENT,
        ))

        children = registry.get_children(Path("parent.md"))
        assert len(children) == 2

    def test_get_parent(self, mock_project):
        """Can get parent of a child node."""
        registry = UnifiedRegistry(mock_project)

        parent = DocumentNode(path=Path("parent.md"), title="Parent")
        child = DocumentNode(path=Path("child.md"), title="Child")
        registry.add_node(parent)
        registry.add_node(child)

        registry.add_edge(RelationshipEdge(
            source=Path("child.md"),
            target=Path("parent.md"),
            edge_type=EdgeType.PARENT,
        ))

        parent_path = registry.get_parent(Path("child.md"))
        assert parent_path == Path("parent.md")

    def test_get_roots(self, mock_project):
        """Can identify root nodes (sources that aren't targets)."""
        registry = UnifiedRegistry(mock_project)

        # Root points to dependency but nothing points to root
        root = DocumentNode(path=Path("root.md"), title="Root")
        dep = DocumentNode(path=Path("dep.md"), title="Dependency")
        registry.add_node(root)
        registry.add_node(dep)

        registry.add_edge(RelationshipEdge(
            source=Path("root.md"),
            target=Path("dep.md"),
            edge_type=EdgeType.REFERENCES,
        ))

        roots = registry.get_roots()
        assert len(roots) == 1
        assert Path("root.md") in roots

    def test_get_impact(self, mock_project):
        """Can get documents affected by a change."""
        registry = UnifiedRegistry(mock_project)

        source = DocumentNode(path=Path("source.md"), title="Source")
        derived1 = DocumentNode(path=Path("derived1.md"), title="Derived 1")
        derived2 = DocumentNode(path=Path("derived2.md"), title="Derived 2")
        registry.add_node(source)
        registry.add_node(derived1)
        registry.add_node(derived2)

        registry.add_edge(RelationshipEdge(
            source=Path("derived1.md"),
            target=Path("source.md"),
            edge_type=EdgeType.IMPLEMENTS,
        ))
        registry.add_edge(RelationshipEdge(
            source=Path("derived2.md"),
            target=Path("source.md"),
            edge_type=EdgeType.TRANSLATES,
        ))

        affected = registry.get_impact(Path("source.md"))
        assert len(affected) == 2
        assert Path("derived1.md") in affected
        assert Path("derived2.md") in affected

    def test_generate_report(self, mock_project):
        """Can generate summary report."""
        registry = UnifiedRegistry(mock_project)

        source = DocumentNode(path=Path("source.md"), title="Source")
        derived = DocumentNode(path=Path("derived.md"), title="Derived")
        registry.add_node(source)
        registry.add_node(derived)

        # Add a stale edge - staleness is determined by edges, not node flag
        registry.add_edge(RelationshipEdge(
            source=Path("derived.md"),
            target=Path("source.md"),
            edge_type=EdgeType.IMPLEMENTS,
            is_stale=True,
            stale_reason="source content changed",
        ))

        report = registry.generate_report()
        assert report["summary"]["total_documents"] == 2
        assert report["summary"]["total_relationships"] == 1
        assert report["summary"]["stale_documents"] == 1

    def test_persistence(self, mock_project):
        """Registry persists to disk."""
        registry = UnifiedRegistry(mock_project)

        node = DocumentNode(
            path=Path("chapters/intro.md"),
            title="Introduction",
        )
        registry.add_node(node)
        registry.save()

        # Create new registry instance
        registry2 = UnifiedRegistry(mock_project)
        retrieved = registry2.get_node(Path("chapters/intro.md"))
        assert retrieved is not None
        assert retrieved.title == "Introduction"


class TestRegistryManager:
    """Tests for RegistryManager singleton."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()
        (project_dir / "content").mkdir()

        class MockProject:
            root = project_dir
            content_dir = project_dir / "content"
            languages = {"en": {"name": "English"}}
            source_language = "en"

            def list_chapters(self, lang):
                return []

        return MockProject()

    def test_singleton_pattern(self, mock_project):
        """Manager is a singleton per project."""
        # Reset first
        reset_registry_manager()

        manager1 = init_registry_manager(mock_project)
        manager2 = get_registry_manager(mock_project)

        assert manager1 is manager2

    def test_get_stale_documents(self, mock_project):
        """Can get list of stale documents."""
        reset_registry_manager()
        manager = init_registry_manager(mock_project)

        # Add document with stale edge (staleness comes from edges)
        node = DocumentNode(
            path=Path("stale.md"),
            title="Stale Doc",
        )
        target = DocumentNode(
            path=Path("target.md"),
            title="Target Doc",
        )
        manager.registry.add_node(node)
        manager.registry.add_node(target)

        # Add stale edge
        manager.registry.add_edge(RelationshipEdge(
            source=Path("stale.md"),
            target=Path("target.md"),
            edge_type=EdgeType.REFERENCES,
            is_stale=True,
            stale_reason="source_updated",
        ))

        stale = manager.get_stale_documents()
        assert len(stale) == 1
        assert stale[0].title == "Stale Doc"

    def test_mark_fresh(self, mock_project):
        """Can mark a document as fresh."""
        reset_registry_manager()
        manager = init_registry_manager(mock_project)

        node = DocumentNode(
            path=Path("stale.md"),
            title="Stale Doc",
            is_stale=True,
            stale_reasons=["source_updated"],
        )
        manager.registry.add_node(node)

        manager.mark_fresh(Path("stale.md"))

        updated = manager.registry.get_node(Path("stale.md"))
        assert updated.is_stale is False

    def test_refresh(self, mock_project):
        """Can refresh the registry."""
        reset_registry_manager()
        manager = init_registry_manager(mock_project)

        result = manager.refresh()
        assert "documents" in result
        assert "relationships" in result
        assert "elapsed_seconds" in result


class TestStalenessTracking:
    """Tests for staleness tracking."""

    @pytest.fixture
    def mock_project(self, tmp_path):
        """Create a mock project for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".media-engine").mkdir()
        (project_dir / "content").mkdir()

        class MockProject:
            root = project_dir
            content_dir = project_dir / "content"
            languages = {"en": {"name": "English"}}
            source_language = "en"

            def list_chapters(self, lang):
                return []

        return MockProject()

    def test_stale_edge_detection(self, mock_project):
        """Can detect stale edges via hash comparison."""
        registry = UnifiedRegistry(mock_project)

        source = DocumentNode(path=Path("source.md"), title="Source")
        derived = DocumentNode(path=Path("derived.md"), title="Derived")
        registry.add_node(source)
        registry.add_node(derived)

        # Add edge marked as stale (simulating source changed)
        edge = RelationshipEdge(
            source=Path("derived.md"),
            target=Path("source.md"),
            edge_type=EdgeType.IMPLEMENTS,
            target_hash="abc12345",
            is_stale=True,
            stale_reason="source content changed",
        )
        registry.add_edge(edge)

        edges = registry.get_outgoing_edges(Path("derived.md"))
        assert len(edges) == 1
        assert edges[0].is_stale is True
        assert "changed" in edges[0].stale_reason


class TestChangeInfo:
    """Tests for ChangeInfo dataclass."""

    def test_creation(self):
        """Can create a change info object."""
        info = ChangeInfo(
            document=Path("updated.md"),
            change_type="modified",
            old_hash="abc123",
            new_hash="def456",
            affected_documents=[Path("derived.md")],
        )
        assert info.document == Path("updated.md")
        assert info.change_type == "modified"
        assert len(info.affected_documents) == 1

    def test_to_dict(self):
        """Can serialize to dict."""
        info = ChangeInfo(
            document=Path("deleted.md"),
            change_type="deleted",
        )
        d = info.to_dict()
        assert d["document"] == "deleted.md"
        assert d["change_type"] == "deleted"
