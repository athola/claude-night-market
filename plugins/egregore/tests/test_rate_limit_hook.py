"""The StopFailure hook records a rate limit without the model's help.

summon/SKILL.md step 7 asks the model to record a rate limit in
budget.json, but the turn that hits the limit is the one that cannot act:
it ends on the API error. StopFailure fires instead of Stop when a turn
ends that way, with `error: "rate_limit"` (code.claude.com/docs/en/hooks
"StopFailure"), so the hook writes the cooldown the watchdog reads.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
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


def _write_budget(tmp_path, cooldown_until):
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "budget.json").write_text(
        json.dumps({"cooldown_until": cooldown_until.isoformat()})
    )


def _cooldown_after_hook(tmp_path, monkeypatch):
    """Run the hook on a rate limit and return the recorded instant."""
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir(exist_ok=True)
    (egregore_dir / "manifest.json").write_text(
        json.dumps({"work_items": [{"id": "wrk_001", "status": "active"}]})
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.stdin",
        StringIO(json.dumps({"hook_event_name": "StopFailure", "error": "rate_limit"})),
    )
    with pytest.raises(SystemExit):
        main()
    recorded = load_budget(egregore_dir / "budget.json").cooldown_until
    assert recorded is not None
    return datetime.fromisoformat(recorded)


class TestTheHookOnlyExtendsACooldown:
    """Math review finding C4: a known reset must survive the padding floor."""

    def test_a_later_header_derived_reset_is_kept(self, tmp_path, monkeypatch):
        """A reset four hours out is not replaced by ten minutes of padding."""
        reset = datetime.now(timezone.utc) + timedelta(hours=4)
        _write_budget(tmp_path, reset)

        assert _cooldown_after_hook(tmp_path, monkeypatch) == reset

    def test_an_earlier_cooldown_is_extended_to_the_padding(
        self, tmp_path, monkeypatch
    ):
        """A cooldown one minute out moves to now plus the padding."""
        before = datetime.now(timezone.utc)
        _write_budget(tmp_path, before + timedelta(minutes=1))

        recorded = _cooldown_after_hook(tmp_path, monkeypatch)

        assert recorded >= before + timedelta(minutes=10)

    def test_the_configured_padding_is_used(self, tmp_path, monkeypatch):
        """``budget.cooldown_padding_minutes`` in config.json sets the floor."""
        egregore_dir = tmp_path / ".egregore"
        egregore_dir.mkdir()
        (egregore_dir / "config.json").write_text(
            json.dumps({"budget": {"cooldown_padding_minutes": 25}})
        )
        before = datetime.now(timezone.utc)

        recorded = _cooldown_after_hook(tmp_path, monkeypatch)

        assert before + timedelta(minutes=25) <= recorded
        assert recorded <= datetime.now(timezone.utc) + timedelta(minutes=25)

    def test_an_unreadable_config_falls_back_to_the_default_padding(
        self, tmp_path, monkeypatch
    ):
        """A corrupt config.json still records the default ten minutes."""
        egregore_dir = tmp_path / ".egregore"
        egregore_dir.mkdir()
        (egregore_dir / "config.json").write_text("{not json")
        before = datetime.now(timezone.utc)

        recorded = _cooldown_after_hook(tmp_path, monkeypatch)

        assert before + timedelta(minutes=10) <= recorded
        assert recorded <= datetime.now(timezone.utc) + timedelta(minutes=10)
