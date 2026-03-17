"""Tests for egregore session start hook."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from session_start_hook import find_manifest, main


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


# --- Tests for main() entry point ---


def test_main_no_manifest(tmp_path, monkeypatch, capsys):
    """main() exits 0 with no output when manifest does not exist."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == ""


def test_main_no_active_items(tmp_path, monkeypatch, capsys):
    """main() exits 0 with no output when manifest has no active items."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "completed"}]}
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == ""


def test_main_with_active_items(tmp_path, monkeypatch, capsys):
    """main() prints hookSpecificOutput JSON when active items exist."""
    manifest = {
        "work_items": [
            {
                "id": "wrk_042",
                "status": "active",
                "pipeline_stage": "build",
                "pipeline_step": "compile",
            }
        ]
    }
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert "hookSpecificOutput" in output
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "SessionStart"
    assert "wrk_042" in hook_output["additionalContext"]
    assert "build" in hook_output["additionalContext"]
    assert "compile" in hook_output["additionalContext"]


def test_main_corrupt_manifest(tmp_path, monkeypatch, capsys):
    """main() exits 0 gracefully when manifest contains invalid JSON."""
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text("not valid json {{")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == ""
