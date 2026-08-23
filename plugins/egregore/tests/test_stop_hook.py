"""Tests for egregore stop hook."""

from __future__ import annotations

import json
import os
from io import StringIO

import pytest
from _manifest_utils import ACTIVE_STATUSES, get_items
from stop_hook import DEFAULT_MAX_STALLS, STATE_FILENAME, has_active_work, main


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
    """main() prints approve decision when manifest does not exist."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO("{}"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "approve"


def test_main_no_active_items(tmp_path, monkeypatch, capsys):
    """main() prints approve decision when no active work items."""
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
    assert output["decision"] == "approve"


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


# --- Direct unit tests for get_items helper ---


def test_get_items_prefers_work_items():
    """get_items returns work_items when present."""
    data = {"work_items": [{"id": "w1"}], "items": [{"id": "i1"}]}
    result = get_items(data)
    assert result == [{"id": "w1"}]


def test_get_items_falls_back_to_items():
    """get_items falls back to items when work_items is absent."""
    data = {"items": [{"id": "i1"}]}
    result = get_items(data)
    assert result == [{"id": "i1"}]


def test_get_items_empty_work_items_falls_back():
    """get_items falls back to items when work_items is empty list."""
    data = {"work_items": [], "items": [{"id": "i1"}]}
    result = get_items(data)
    assert result == [{"id": "i1"}]


def test_get_items_neither_key():
    """get_items returns empty list when neither key exists."""
    result = get_items({})
    assert result == []


def test_active_statuses_tuple():
    """ACTIVE_STATUSES includes active, paused, and pending."""
    assert "active" in ACTIVE_STATUSES
    assert "paused" in ACTIVE_STATUSES
    assert "pending" in ACTIVE_STATUSES
    assert "completed" not in ACTIVE_STATUSES
    assert "failed" not in ACTIVE_STATUSES


# --- Bug fix tests: items key and pending status ---


def test_has_active_work_items_key(tmp_path):
    """Manifests may use 'items' instead of 'work_items'."""
    manifest = {"items": [{"id": "DEEP-001", "status": "active"}]}
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is True


def test_has_active_work_pending_items(tmp_path):
    """Pending items count as remaining work."""
    manifest = {
        "items": [
            {"id": "DEEP-001", "status": "completed"},
            {"id": "INTEGRATION-001", "status": "pending"},
        ]
    }
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is True


def test_has_active_work_all_completed_items_key(tmp_path):
    """No active work when all 'items' are completed."""
    manifest = {
        "items": [
            {"id": "DEEP-001", "status": "completed"},
            {"id": "DEEP-002", "status": "completed"},
        ]
    }
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is False


def test_has_active_work_all_failed_items_key(tmp_path):
    """No active work when all items completed or failed."""
    manifest = {
        "items": [
            {"id": "DEEP-001", "status": "completed"},
            {"id": "DEEP-002", "status": "failed"},
        ]
    }
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    assert has_active_work(path) is False


# --- Stall bound: the Stop hook must not re-inject forever ---


def _manifest_with_active_work(tmp_path, marker="a"):
    """Write a manifest with one active item; marker varies its bytes."""
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir(exist_ok=True)
    manifest = {
        "work_items": [
            {"id": "wrk_001", "status": "active", "step": marker},
        ]
    }
    (egregore_dir / "manifest.json").write_text(json.dumps(manifest))
    return egregore_dir


def _run_stop_hook(monkeypatch, tmp_path, session_id="sess-1"):
    """Invoke main() with a payload and return the decision dict."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.stdin",
        StringIO(json.dumps({"session_id": session_id, "stop_hook_active": True})),
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    return exc_info


def test_block_records_one_stall(tmp_path, monkeypatch, capsys):
    """The first block writes state showing a single consecutive block."""
    egregore_dir = _manifest_with_active_work(tmp_path)
    _run_stop_hook(monkeypatch, tmp_path)
    assert json.loads(capsys.readouterr().out)["decision"] == "block"
    state = json.loads((egregore_dir / STATE_FILENAME).read_text())
    assert state["consecutive_blocks"] == 1
    assert state["session_id"] == "sess-1"


def test_stalled_loop_is_released(tmp_path, monkeypatch, capsys):
    """After MAX stalls with no manifest change, the hook approves the stop."""
    _manifest_with_active_work(tmp_path)
    decisions = []
    for _ in range(DEFAULT_MAX_STALLS + 1):
        _run_stop_hook(monkeypatch, tmp_path)
        decisions.append(json.loads(capsys.readouterr().out)["decision"])
    assert decisions == ["block"] * DEFAULT_MAX_STALLS + ["approve"]


def test_release_persists_until_progress(tmp_path, monkeypatch, capsys):
    """A released loop stays released while the manifest is unchanged."""
    _manifest_with_active_work(tmp_path)
    for _ in range(DEFAULT_MAX_STALLS + 1):
        _run_stop_hook(monkeypatch, tmp_path)
        capsys.readouterr()
    _run_stop_hook(monkeypatch, tmp_path)
    assert json.loads(capsys.readouterr().out)["decision"] == "approve"


def test_manifest_progress_resets_the_counter(tmp_path, monkeypatch, capsys):
    """A changed manifest is progress: blocking resumes from zero."""
    _manifest_with_active_work(tmp_path, marker="a")
    for _ in range(DEFAULT_MAX_STALLS):
        _run_stop_hook(monkeypatch, tmp_path)
        capsys.readouterr()
    _manifest_with_active_work(tmp_path, marker="b")
    _run_stop_hook(monkeypatch, tmp_path)
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_new_session_resets_the_counter(tmp_path, monkeypatch, capsys):
    """A watchdog relaunch is a new session and starts with a fresh budget."""
    _manifest_with_active_work(tmp_path)
    for _ in range(DEFAULT_MAX_STALLS + 1):
        _run_stop_hook(monkeypatch, tmp_path, session_id="sess-1")
        capsys.readouterr()
    _run_stop_hook(monkeypatch, tmp_path, session_id="sess-2")
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_stall_limit_is_configurable(tmp_path, monkeypatch, capsys):
    """EGREGORE_STOP_MAX_STALLS overrides the default budget."""
    monkeypatch.setenv("EGREGORE_STOP_MAX_STALLS", "1")
    _manifest_with_active_work(tmp_path)
    _run_stop_hook(monkeypatch, tmp_path)
    assert json.loads(capsys.readouterr().out)["decision"] == "block"
    _run_stop_hook(monkeypatch, tmp_path)
    assert json.loads(capsys.readouterr().out)["decision"] == "approve"


def test_corrupt_state_file_starts_a_fresh_count(tmp_path, monkeypatch, capsys):
    """Unreadable state is treated as absent, not as a reason to crash."""
    egregore_dir = _manifest_with_active_work(tmp_path)
    (egregore_dir / STATE_FILENAME).write_text("not valid json")
    _run_stop_hook(monkeypatch, tmp_path)
    assert json.loads(capsys.readouterr().out)["decision"] == "block"
    state = json.loads((egregore_dir / STATE_FILENAME).read_text())
    assert state["consecutive_blocks"] == 1


def test_unwritable_state_releases_the_stop(tmp_path, monkeypatch, capsys):
    """Without durable state the loop cannot be bounded, so it is not blocked."""
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("root ignores directory permissions")
    egregore_dir = _manifest_with_active_work(tmp_path)
    egregore_dir.chmod(0o500)
    try:
        _run_stop_hook(monkeypatch, tmp_path)
    finally:
        egregore_dir.chmod(0o700)
    assert json.loads(capsys.readouterr().out)["decision"] == "approve"
