"""
Document registry and packs routes.
"""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_registry_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register registry and packs routes."""
    import yaml

    @router.get("/api/registry")
    async def get_document_registry():
        """Get the complete document registry from documents.yaml."""
        project = get_project()

        registry_paths = [
            project.root / "docs" / "system" / ".schema" / "documents.yaml",
            project.root / "documents.yaml",
            project.root / ".schema" / "documents.yaml",
        ]

        registry = None
        for path in registry_paths:
            if path.exists():
                with open(path) as f:
                    registry = yaml.safe_load(f)
                break

        if not registry:
            return {"found": False, "registry": None}

        categories = {
            "source_documents": registry.get("source_documents", {}),
            "deliverables": registry.get("deliverables", {}),
            "video_scripts": registry.get("video_scripts", {}),
            "diagrams": registry.get("diagrams", {}),
            "templates": registry.get("templates", {}),
            "demo": registry.get("demo", {}),
            "brand": registry.get("brand", {}),
            "shared_data": registry.get("shared_data", {}),
            "priorities": registry.get("priorities", {}),
        }

        status_counts = {"not_started": 0, "draft": 0, "review": 0, "final": 0, "complete": 0}
        for cat_name, cat_docs in categories.items():
            if isinstance(cat_docs, dict):
                for doc_id, doc in cat_docs.items():
                    if isinstance(doc, dict) and "status" in doc:
                        status = doc.get("status", "not_started")
                        if status in status_counts:
                            status_counts[status] += 1

        return {
            "found": True,
            "categories": categories,
            "status_counts": status_counts,
            "version": registry.get("version", "unknown"),
            "last_updated": registry.get("last_updated", "unknown"),
        }

    @router.get("/api/packs")
    async def get_packs():
        """Get available media packs and their contents."""
        project = get_project()

        packs = {
            "investor": {
                "name": "Investor Pack",
                "description": "Materials for investor presentations",
                "contents": [
                    {
                        "type": "document",
                        "name": "Executive Summary",
                        "path": "docs/deliverables/investor/executive_summary.md",
                    },
                    {
                        "type": "document",
                        "name": "Pitch Deck",
                        "path": "docs/deliverables/investor/pitch_deck_standard.md",
                    },
                    {
                        "type": "document",
                        "name": "Data Sheet",
                        "path": "docs/deliverables/investor/data_sheet.md",
                    },
                    {
                        "type": "document",
                        "name": "FAQ",
                        "path": "docs/deliverables/investor/faq.md",
                    },
                    {
                        "type": "document",
                        "name": "One Pager",
                        "path": "docs/deliverables/investor/one_pager.md",
                    },
                    {
                        "type": "video",
                        "name": "Teaser Video",
                        "path": "output/videos/teaser.mp4",
                    },
                    {
                        "type": "diagrams",
                        "name": "Architecture Diagrams",
                        "path": "docs/proposal/diagrams/",
                    },
                ],
                "audience": "Investors, VCs, Angels",
            },
            "pilot": {
                "name": "Pilot Customer Pack",
                "description": "Materials for pilot customer engagement",
                "contents": [
                    {
                        "type": "document",
                        "name": "Pilot Proposal",
                        "path": "docs/deliverables/pilot/pilot_proposal.md",
                    },
                    {
                        "type": "document",
                        "name": "Pilot Deck",
                        "path": "docs/deliverables/pilot/pilot_deck.md",
                    },
                    {
                        "type": "document",
                        "name": "Pilot Agreement",
                        "path": "docs/deliverables/legal/pilot_agreement_template.md",
                    },
                    {
                        "type": "document",
                        "name": "NDA",
                        "path": "docs/deliverables/legal/nda_template.md",
                    },
                    {
                        "type": "document",
                        "name": "Pilot Playbook",
                        "path": "docs/deliverables/playbooks/pilot_playbook.md",
                    },
                    {
                        "type": "demo",
                        "name": "Interactive Demo",
                        "path": "docs/deliverables/demo/en/interactive-demo.html",
                    },
                ],
                "audience": "Restaurant Managers, Operations Directors",
            },
        }

        for pack_id, pack in packs.items():
            for item in pack["contents"]:
                item_path = project.root / item["path"]
                item["exists"] = item_path.exists() or item_path.is_dir()

        return {"packs": packs}
