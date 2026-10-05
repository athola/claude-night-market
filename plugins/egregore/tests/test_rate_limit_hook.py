"""The StopFailure hook records a rate limit without the model's help.

summon/SKILL.md step 7 asks the model to record a rate limit in
budget.json, but the turn that hits the limit is the one that cannot act:
it ends on the API error. StopFailure fires instead of Stop when a turn
ends that way, with `error: "rate_limit"` (code.claude.com/docs/en/hooks
"StopFailure"), so the hook writes the cooldown the watchdog reads.
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
from budget import load_budget
from rate_limit_hook import main

HOOKS_JSON = Path(__file__).resolve().parents[1] / "hooks" / "hooks.json"


def _run(tmp_path, monkeypatch, payload, items):
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(json.dumps({"work_items": items}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    return egregore_dir / "budget.json"


def test_rate_limit_during_a_loop_records_a_cooldown(tmp_path, monkeypatch):
    budget_path = _run(
        tmp_path,
        monkeypatch,
        {"hook_event_name": "StopFailure", "error": "rate_limit"},
        [{"id": "wrk_001", "status": "active"}],
    )
    budget = load_budget(budget_path)
    assert budget.last_rate_limit_at is not None
    assert budget.cooldown_until is not None


def test_other_api_errors_leave_the_budget_alone(tmp_path, monkeypatch):
    budget_path = _run(
        tmp_path,
        monkeypatch,
        {"hook_event_name": "StopFailure", "error": "server_error"},
        [{"id": "wrk_001", "status": "active"}],
    )
    assert not budget_path.exists()


def test_no_active_loop_writes_nothing(tmp_path, monkeypatch):
    budget_path = _run(
        tmp_path,
        monkeypatch,
        {"hook_event_name": "StopFailure", "error": "rate_limit"},
        [{"id": "wrk_001", "status": "completed"}],
    )
    assert not budget_path.exists()


def test_hook_is_registered_on_rate_limit_stop_failures():
    groups = json.loads(HOOKS_JSON.read_text())["hooks"]["StopFailure"]
    commands = [
        handler["command"]
        for group in groups
        if group.get("matcher") == "rate_limit"
        for handler in group["hooks"]
    ]
    assert any("rate_limit_hook.py" in command for command in commands)
