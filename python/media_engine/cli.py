#!/usr/bin/env python3
"""
Media Engine CLI

Agent-friendly command line interface for media production.

This module is maintained for backwards compatibility.
The actual implementation is in media_engine.cli package.

Usage:
    media-engine status [--json]
    media-engine build [--only FORMAT] [--force] [--lang LANG]
    media-engine publish [--formats LIST]
    media-engine stale [--json]
    media-engine cache status
    media-engine cache clear [--voiceover] [--builds]
"""

from .cli import main

if __name__ == "__main__":
    main()
