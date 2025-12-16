"""
MCP Server for Media Engine

Provides agent-agnostic integration via Model Context Protocol.
Works with Claude Code, Cursor, VS Code, and any MCP-compatible client.
"""

from .server import MediaEngineMCPServer

__all__ = ["MediaEngineMCPServer"]
