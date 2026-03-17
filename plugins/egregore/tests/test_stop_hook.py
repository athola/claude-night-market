"""Tests for egregore stop hook."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from stop_hook import has_active_work, main


def test_has_active_work_with_active_items(tmp_path):
    """Stop hook should detect active work items."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "active"}]}
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is True


def test_has_active_work_with_paused_items(tmp_path):
    """Paused items also count as active work."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "paused"}]}
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is True


def test_has_active_work_all_completed(tmp_path):
    """No active work when all items completed."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "completed"}]}
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is False


def test_has_active_work_no_manifest(tmp_path):
    """No active work when manifest doesn't exist."""
    path = tmp_path / ".egregore" / "manifest.json"
    assert has_active_work(path) is False


def test_has_active_work_empty_items(tmp_path):
    """No active work when work_items is empty."""
    manifest = {"work_items": []}
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is False


def test_has_active_work_invalid_json(tmp_path):
    """Gracefully handle invalid JSON."""
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text("not valid json")
    assert has_active_work(path) is False


def test_has_active_work_mixed_statuses(tmp_path):
    """Active work when mix of statuses includes active."""
    manifest = {
        "work_items": [
            {"id": "wrk_001", "status": "completed"},
            {"id": "wrk_002", "status": "failed"},
            {"id": "wrk_003", "status": "active"},
        ]
    }
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is True


# --- Tests for main() entry point ---


def test_main_no_manifest(tmp_path, monkeypatch, capsys):
    """main() prints allow decision when manifest does not exist."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "allow"


def test_main_no_active_items(tmp_path, monkeypatch, capsys):
    """main() prints allow decision when no active work items."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "completed"}]}
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "allow"


def test_main_with_active_items(tmp_path, monkeypatch, capsys):
    """main() prints block decision when active work items exist."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "active"}]}
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "block"
    assert "reason" in output
    assert "active work items" in output["reason"]


def test_main_with_relaunch_prompt(tmp_path, monkeypatch, capsys):
    """main() uses relaunch-prompt.md content as block reason."""
    manifest = {"work_items": [{"id": "wrk_001", "status": "active"}]}
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(json.dumps(manifest))
    (egregore_dir / "relaunch-prompt.md").write_text(
        "Continue building the widget from step 3."
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "block"
    assert output["reason"] == "Continue building the widget from step 3."
