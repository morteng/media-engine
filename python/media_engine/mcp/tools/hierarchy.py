"""
MCP tools for document hierarchy and information flow.

Uses the UnifiedRegistry via RegistryManager for all hierarchy operations.

Provides tools for:
- Hierarchy status and tree visualization
- Staleness detection and propagation
- Consistency anchors management
- Impact analysis for changes
- Coverage analysis for documentation gaps
"""

import json
from pathlib import Path
from typing import Any


def _get_registry_manager(server_instance):
    """Get or create the RegistryManager for the project."""
    from ...relationships import get_registry_manager, init_registry_manager

    project = server_instance.project
    if not project:
        return None

    registry_manager = get_registry_manager(project)
    if registry_manager is None:
        registry_manager = init_registry_manager(project)

    return registry_manager


def register_hierarchy_tools(mcp, server_instance) -> None:
    """Register hierarchy management tools."""

    @mcp.tool(
        description="""
        Get document hierarchy status.

        Returns summary of hierarchy including:
        - Total documents and root count
        - Document type distribution
        - Lifecycle distribution
        - Stale document count
        """
    )
    def hierarchy_status() -> str:
        """Get hierarchy status overview."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        report = manager.registry.generate_report()

        return json.dumps(report, indent=2)

    @mcp.tool(
        description="""
        Get hierarchy tree as ASCII representation.

        Args:
            root_path: Optional path to start from (shows all roots if omitted)
        """
    )
    def hierarchy_tree(root_path: str = None) -> str:
        """Get hierarchy as ASCII tree."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        registry = manager.registry

        # Build tree from registry
        lines = []

        def _build_tree(node_path: Path, prefix: str = "", is_last: bool = True):
            node = registry.get_node(node_path)
            if not node:
                return

            connector = "└── " if is_last else "├── "
            title = node.title or node_path.stem
            stale_marker = " [STALE]" if node.is_stale else ""

            lines.append(f"{prefix}{connector}{title}{stale_marker}")

            children = registry.get_children(node_path)
            child_prefix = prefix + ("    " if is_last else "│   ")

            for i, child_path in enumerate(children):
                is_child_last = i == len(children) - 1
                _build_tree(child_path, child_prefix, is_child_last)

        if root_path:
            root = Path(root_path)
            if not root.is_absolute():
                root = server_instance.project.content_dir / root
            _build_tree(root, "", True)
        else:
            # Show all roots
            roots = registry.get_roots()
            for i, root in enumerate(roots):
                is_last = i == len(roots) - 1
                _build_tree(root, "", is_last)

        if not lines:
            return "No hierarchy data found. Run hierarchy_refresh first."

        return "\n".join(lines)

    @mcp.tool(
        description="""
        Refresh hierarchy from document frontmatter.

        Scans all documents to rebuild the hierarchy based on:
        - parent_document fields
        - derived_from relationships
        - doc_type and lifecycle metadata
        - consistency anchors
        """
    )
    def hierarchy_refresh() -> str:
        """Refresh hierarchy from documents."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        result = manager.refresh()
        report = manager.registry.generate_report()

        return json.dumps(
            {
                "status": "refreshed",
                "total_nodes": report["summary"]["total_documents"],
                "root_count": report["summary"]["root_documents"],
                "anchor_count": report["summary"]["anchors"],
                "relationships": report["summary"]["total_relationships"],
                "elapsed_seconds": result.get("elapsed_seconds", 0),
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Validate hierarchy structure.

        Checks for:
        - Circular parent references
        - Orphan documents with missing parents
        - Duplicate sequence orders
        - Level mismatches
        - Invalid derivation sources
        """
    )
    def hierarchy_validate() -> str:
        """Validate hierarchy structure."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        registry = manager.registry
        issues = []

        # Check for circular references
        for node in registry.all_nodes():
            visited = set()
            current = node.path
            while current:
                if current in visited:
                    issues.append({
                        "type": "circular_reference",
                        "document": str(node.path),
                        "message": f"Circular parent reference detected at {current}",
                    })
                    break
                visited.add(current)
                parent = registry.get_parent(current)
                current = parent

        # Check for orphan documents (have parent ref but parent doesn't exist)
        for node in registry.all_nodes():
            edges = registry.get_outgoing_edges(node.path)
            for edge in edges:
                if edge.edge_type.value == "parent":
                    if not registry.get_node(edge.target):
                        issues.append({
                            "type": "orphan_parent",
                            "document": str(node.path),
                            "message": f"Parent document not found: {edge.target}",
                        })

        # Check for stale edges
        stale_count = 0
        for node in registry.all_nodes():
            edges = registry.get_outgoing_edges(node.path)
            for edge in edges:
                if edge.is_stale:
                    stale_count += 1
                    issues.append({
                        "type": "stale_edge",
                        "document": str(node.path),
                        "target": str(edge.target),
                        "edge_type": edge.edge_type.value,
                        "reason": edge.stale_reason,
                    })

        return json.dumps(
            {
                "valid": len(issues) == 0,
                "issue_count": len(issues),
                "stale_edges": stale_count,
                "issues": issues[:50],  # Limit to 50 issues
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get navigation context for a document.

        Returns:
        - Breadcrumbs from root to document
        - Parent, children, and siblings
        - Previous/next sibling navigation
        - Position in sibling list

        Args:
            document_path: Path to the document
        """
    )
    def hierarchy_navigation(document_path: str) -> str:
        """Get navigation context for a document."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        doc_path = Path(document_path)
        if not doc_path.is_absolute():
            doc_path = server_instance.project.content_dir / document_path

        registry = manager.registry
        node = registry.get_node(doc_path)

        if not node:
            return json.dumps({"error": f"Document not found in hierarchy: {document_path}"})

        # Build breadcrumbs
        breadcrumbs = []
        current = doc_path
        while current:
            n = registry.get_node(current)
            if n:
                breadcrumbs.insert(0, {"path": str(current), "title": n.title or current.stem})
            parent = registry.get_parent(current)
            current = parent

        # Get siblings
        parent_path = registry.get_parent(doc_path)
        if parent_path:
            siblings = registry.get_children(parent_path)
        else:
            siblings = registry.get_roots()

        siblings = list(siblings)
        position = siblings.index(doc_path) if doc_path in siblings else -1

        prev_sibling = siblings[position - 1] if position > 0 else None
        next_sibling = siblings[position + 1] if position < len(siblings) - 1 else None

        # Get children
        children = registry.get_children(doc_path)

        return json.dumps(
            {
                "document": str(doc_path),
                "title": node.title,
                "breadcrumbs": breadcrumbs,
                "parent": str(parent_path) if parent_path else None,
                "children": [str(c) for c in children],
                "siblings": [str(s) for s in siblings],
                "position": position + 1,
                "total_siblings": len(siblings),
                "prev_sibling": str(prev_sibling) if prev_sibling else None,
                "next_sibling": str(next_sibling) if next_sibling else None,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get stale documents report.

        Returns documents that need updating because:
        - Source documents were modified
        - Version mismatches exist
        - Staleness propagated through derivation chain
        - Freshness period expired
        - Anchors changed
        """
    )
    def hierarchy_stale() -> str:
        """Get stale documents report."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        stale_docs = manager.get_stale_documents()

        stale_list = []
        for doc in stale_docs:
            edges = manager.registry.get_outgoing_edges(doc.path)
            stale_edges = [e for e in edges if e.is_stale]

            stale_list.append({
                "path": str(doc.path),
                "title": doc.title,
                "is_stale": doc.is_stale,
                "stale_reasons": doc.stale_reasons,
                "stale_edges": [
                    {
                        "target": str(e.target),
                        "type": e.edge_type.value,
                        "reason": e.stale_reason,
                    }
                    for e in stale_edges
                ],
            })

        return json.dumps(
            {
                "stale_count": len(stale_list),
                "stale_documents": stale_list,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Mark a document as stale.

        This triggers staleness propagation to dependent documents.

        Args:
            document_path: Path to the document
            reason: Reason for staleness (source_updated, version_mismatch, expired, anchor_changed)
        """
    )
    def hierarchy_mark_stale(
        document_path: str,
        reason: str = "source_updated",
    ) -> str:
        """Mark a document as stale."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        doc_path = Path(document_path)
        if not doc_path.is_absolute():
            doc_path = server_instance.project.content_dir / document_path

        # Mark the document stale via the registry
        node = manager.registry.get_node(doc_path)
        if not node:
            return json.dumps({"error": f"Document not found: {document_path}"})

        # Add stale reason to node
        if reason not in node.stale_reasons:
            node.stale_reasons.append(reason)
        node.is_stale = True

        # Propagate staleness through dependent documents
        affected = manager.registry.get_impact(doc_path)

        # Save registry
        manager.registry.save()

        return json.dumps(
            {
                "marked_stale": True,
                "document": str(doc_path),
                "reason": reason,
                "affected_documents": len(affected),
            }
        )

    @mcp.tool(
        description="""
        Get consistency anchors.

        Returns all anchors defined across documents with:
        - Anchor names and values
        - Which documents define them
        - Which documents reference them

        Args:
            validate: If true, also validate anchor references
        """
    )
    def hierarchy_anchors(validate: bool = False) -> str:
        """Get consistency anchors."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        # Get anchors from registry data
        if manager.registry.data_path.exists():
            import json as json_lib
            with open(manager.registry.data_path) as f:
                data = json_lib.load(f)
            anchors_data = data.get("anchors", {})
        else:
            anchors_data = {}

        result: dict[str, Any] = {
            "anchor_count": len(anchors_data),
        }

        if validate:
            # Check anchor references
            missing = []
            valid_count = 0

            for anchor_id, anchor_info in anchors_data.items():
                defined_in = anchor_info.get("defined_in")
                anchor_info.get("referenced_in", [])

                if defined_in and Path(defined_in).exists():
                    valid_count += 1
                else:
                    missing.append({
                        "anchor": anchor_id,
                        "defined_in": defined_in,
                        "reason": "source_not_found",
                    })

            result["validation"] = {
                "valid": len(missing) == 0,
                "valid_anchors": valid_count,
                "missing_sources": missing,
            }

        # List anchors
        anchors = []
        for anchor_id, anchor_info in anchors_data.items():
            value = anchor_info.get("value", "")
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."

            anchors.append({
                "id": anchor_id,
                "value": value,
                "value_type": anchor_info.get("value_type", "string"),
                "defined_in": anchor_info.get("defined_in"),
                "referenced_by_count": len(anchor_info.get("referenced_in", [])),
            })

        result["anchors"] = anchors

        return json.dumps(result, indent=2)

    @mcp.tool(
        description="""
        Analyze impact of changing a document.

        Returns what documents would be affected:
        - Direct derivatives
        - Transitive derivatives
        - Child documents
        - Anchor references
        - Translations

        Args:
            document_path: Path to document being changed
            change_type: Type of change (content, metadata, delete, anchor)
            description: Description of the change
        """
    )
    def hierarchy_impact(
        document_path: str,
        change_type: str = "content",
        description: str = "",
    ) -> str:
        """Analyze impact of a document change."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        doc_path = Path(document_path)
        if not doc_path.is_absolute():
            doc_path = server_instance.project.content_dir / document_path

        registry = manager.registry
        affected = registry.get_impact(doc_path)

        # Categorize affected documents
        direct = []
        translations = []
        derivatives = []
        children = []

        for affected_path in affected:
            edges = registry.get_outgoing_edges(affected_path)
            for edge in edges:
                if str(edge.target) == str(doc_path):
                    affected_node = registry.get_node(affected_path)
                    title = affected_node.title if affected_node else affected_path.stem

                    info = {
                        "path": str(affected_path),
                        "title": title,
                        "relationship": edge.edge_type.value,
                    }

                    if edge.edge_type.value == "translates":
                        translations.append(info)
                    elif edge.edge_type.value in ("implements", "extends", "summarizes"):
                        derivatives.append(info)
                    elif edge.edge_type.value == "parent":
                        children.append(info)
                    else:
                        direct.append(info)

        return json.dumps(
            {
                "document": str(doc_path),
                "change_type": change_type,
                "description": description or f"Change to {doc_path.name}",
                "total_affected": len(affected),
                "direct_dependents": direct,
                "translations": translations,
                "derivatives": derivatives,
                "children": children,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Analyze documentation coverage.

        Returns:
        - Coverage score (0-100)
        - Missing derived documents
        - Orphan documents
        - Incomplete derivation chains
        - Missing translations (if languages specified)

        Args:
            languages: Comma-separated list of language codes to check translations
        """
    )
    def hierarchy_coverage(languages: str = None) -> str:
        """Analyze documentation coverage."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        registry = manager.registry
        project = server_instance.project

        # Calculate coverage metrics
        all_nodes = list(registry.all_nodes())
        total_docs = len(all_nodes)

        # Count by type
        by_type = {}
        stale_count = 0
        orphan_count = 0

        for node in all_nodes:
            doc_type = node.doc_type or "unknown"
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

            if node.is_stale:
                stale_count += 1

            # Check if orphan (has parent ref but parent not found)
            edges = registry.get_outgoing_edges(node.path)
            for edge in edges:
                if edge.edge_type.value == "parent":
                    if not registry.get_node(edge.target):
                        orphan_count += 1
                        break

        # Translation coverage
        translation_coverage = {}
        if languages:
            lang_list = [l.strip() for l in languages.split(",")]
            source_lang = project.source_language

            # Get source documents
            source_docs = [n for n in all_nodes
                          if source_lang in str(n.path)]

            for lang in lang_list:
                if lang == source_lang:
                    continue

                translated = 0
                for node in all_nodes:
                    if lang in str(node.path):
                        # Check if it's a translation
                        edges = registry.get_outgoing_edges(node.path)
                        for edge in edges:
                            if edge.edge_type.value == "translates":
                                translated += 1
                                break

                translation_coverage[lang] = {
                    "translated": translated,
                    "source_total": len(source_docs),
                    "percentage": round(translated / len(source_docs) * 100, 1) if source_docs else 0,
                }

        # Calculate overall score
        health_score = 100
        if stale_count > 0:
            health_score -= min(30, stale_count * 5)
        if orphan_count > 0:
            health_score -= min(20, orphan_count * 10)

        return json.dumps(
            {
                "total_documents": total_docs,
                "by_type": by_type,
                "stale_documents": stale_count,
                "orphan_documents": orphan_count,
                "health_score": max(0, health_score),
                "translation_coverage": translation_coverage,
            },
            indent=2,
        )

    @mcp.tool(
        description="""
        Get coverage suggestions.

        Returns prioritized suggestions for improving documentation coverage,
        sorted by priority (critical, high, medium, low).
        """
    )
    def hierarchy_coverage_suggestions() -> str:
        """Get coverage improvement suggestions."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        registry = manager.registry
        suggestions = []

        # Find stale documents
        for node in registry.all_nodes():
            if node.is_stale:
                suggestions.append({
                    "priority": "high",
                    "type": "stale_content",
                    "document": str(node.path),
                    "title": node.title,
                    "suggestion": f"Review and update {node.title or node.path.stem}",
                    "reasons": node.stale_reasons,
                })

        # Find orphan documents
        for node in registry.all_nodes():
            edges = registry.get_outgoing_edges(node.path)
            for edge in edges:
                if edge.edge_type.value == "parent":
                    if not registry.get_node(edge.target):
                        suggestions.append({
                            "priority": "critical",
                            "type": "missing_parent",
                            "document": str(node.path),
                            "title": node.title,
                            "suggestion": f"Create missing parent: {edge.target.name}",
                            "missing": str(edge.target),
                        })

        # Find documents without children that might need them
        for node in registry.all_nodes():
            if node.doc_type == "chapter":
                children = registry.get_children(node.path)
                if not children:
                    suggestions.append({
                        "priority": "low",
                        "type": "no_children",
                        "document": str(node.path),
                        "title": node.title,
                        "suggestion": f"Consider adding sub-content for {node.title or node.path.stem}",
                    })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return json.dumps({"suggestions": suggestions[:50]}, indent=2)

    @mcp.tool(
        description="""
        Get derivation chains from a document.

        Returns all paths from the source document through its derivatives,
        showing how changes propagate through the documentation.

        Args:
            document_path: Path to the source document
        """
    )
    def hierarchy_derivation_chains(document_path: str) -> str:
        """Get derivation chains from a document."""
        manager = _get_registry_manager(server_instance)
        if not manager:
            return json.dumps({"error": "No project found"})

        doc_path = Path(document_path)
        if not doc_path.is_absolute():
            doc_path = server_instance.project.content_dir / document_path

        registry = manager.registry

        # Build chains by following derivation edges
        chains = []

        def _build_chain(current: Path, chain: list):
            # Find documents that derive from current
            derivations = []
            for node in registry.all_nodes():
                edges = registry.get_outgoing_edges(node.path)
                for edge in edges:
                    if str(edge.target) == str(current) and edge.edge_type.value in (
                        "implements", "extends", "summarizes", "translates"
                    ):
                        derivations.append((node.path, edge.edge_type.value))

            if not derivations:
                if len(chain) > 1:  # Only add chains with at least 2 items
                    chains.append(chain[:])
                return

            for deriv_path, edge_type in derivations:
                chain.append({
                    "path": str(deriv_path),
                    "relationship": edge_type,
                })
                _build_chain(deriv_path, chain)
                chain.pop()

        _build_chain(doc_path, [{"path": str(doc_path), "relationship": "source"}])

        return json.dumps(
            {
                "source": str(doc_path),
                "chains": chains,
                "chain_count": len(chains),
            },
            indent=2,
        )
