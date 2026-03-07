"""Tests for egregore session start hook."""

from __future__ import annotations

import sys
from pathlib import Path

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from session_start_hook import find_manifest


def test_find_manifest_in_cwd(tmp_path, monkeypatch):
    """Find manifest when in project root."""
    manifest_path = tmp_path / ".egregore" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{}")
    monkeypatch.chdir(tmp_path)
    result = find_manifest()
    assert result == manifest_path


def test_find_manifest_in_subdirectory(tmp_path, monkeypatch):
    """Find manifest when in a subdirectory."""
    manifest_path = tmp_path / ".egregore" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{}")
    subdir = tmp_path / "src" / "deep"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    result = find_manifest()
    assert result == manifest_path


def test_find_manifest_not_found(tmp_path, monkeypatch):
    """Return default path when no manifest found."""
    monkeypatch.chdir(tmp_path)
    result = find_manifest()
    assert str(result).endswith(".egregore/manifest.json")
