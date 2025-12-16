"""
Media Engine Packs Module

Curated deliverable packages:
- Investor pack (pitch deck, one-pager, executive summary)
- Pilot pack (pilot proposal, agreement, ROI calculator)
- Custom packs from configuration
"""

from .generator import (
    PackConfig,
    PackItem,
    PackResult,
    generate_investor_pack,
    generate_pack,
    generate_pilot_pack,
)

__all__ = [
    "PackConfig",
    "PackResult",
    "PackItem",
    "generate_pack",
    "generate_investor_pack",
    "generate_pilot_pack",
]
