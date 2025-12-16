"""
Shared test fixtures for Media Engine tests.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def sample_markdown(temp_dir):
    """Create a sample markdown file with frontmatter."""
    content = '''---
title: Test Document
version: 1.0.0
status: draft
last_modified: 2024-01-15
---

# Test Document

This is a test document for unit testing.

## Section One

Some content here.

## Section Two

More content here.
'''
    path = temp_dir / "test_doc.md"
    path.write_text(content)
    return path


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample config.yaml file."""
    content = '''
project:
  name: "Test Project"
  description: "A test project"

voiceover:
  provider: "elevenlabs"
  voice_id: "test-voice-id"
  stability: 0.5

video:
  width: 1920
  height: 1080
  fps: 30

paths:
  output: "./output"
  assets: "./assets"
'''
    path = temp_dir / "config.yaml"
    path.write_text(content)
    return path


@pytest.fixture
def sample_theme(temp_dir):
    """Create a sample theme.yaml file."""
    content = '''
name: "Test Theme"

colors:
  primary: "#000000"
  secondary: "#333333"
  accent: "#0066cc"
  background: "#ffffff"
  dark:
    background: "#1a1a1a"
    text: "#ffffff"

typography:
  heading: "Arial"
  body: "Helvetica"
'''
    path = temp_dir / "theme.yaml"
    path.write_text(content)
    return path


@pytest.fixture
def mock_theme():
    """Return a mock theme dictionary."""
    return {
        "name": "Mock Theme",
        "colors": {
            "primary": "#2c2522",
            "accent": "#c45c3c",
            "background": "#fdfbf9",
        },
        "typography": {
            "heading": "Fraunces",
            "body": "Source Sans 3",
        },
    }
