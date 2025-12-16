"""
Web Dashboard for Media Engine

Provides a browser-based UI for project management, content editing,
translation tracking, and real-time collaboration.
"""

from .app import create_app, run_dashboard

__all__ = ["create_app", "run_dashboard"]
