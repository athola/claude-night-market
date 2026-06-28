"""TDD tests for the forced-eval activation hook prototype.

Written FIRST (red). The implementation in forced_eval.py is added
afterwards to turn them green. Run: python -m pytest test_forced_eval.py
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import forced_eval
import pytest


def test_discover_skill_names_extracts_frontmatter(tmp_path: Path) -> None:
    skills = tmp_path / "skills"
    (skills / "alpha").mkdir(parents=True)
    (skills / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: a thing\n---\nbody\n"
    )
    (skills / "beta").mkdir(parents=True)
    (skills / "beta" / "SKILL.md").write_text(
        "---\nname: beta-skill\ndescription: another\n---\nbody\n"
    )
    names = forced_eval.discover_skill_names(tmp_path)
    assert "alpha" in names
    assert "beta-skill" in names


def test_build_eval_reminder_names_skills_and_instructs() -> None:
    reminder = forced_eval.build_eval_reminder(["alpha", "beta-skill"])
    assert "alpha" in reminder
    assert "beta-skill" in reminder
    # Must instruct the model to evaluate skills before acting.
    assert "skill" in reminder.lower()


def test_format_response_matches_userpromptsubmit_contract() -> None:
    out = forced_eval.format_response("hello world")
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert out["hookSpecificOutput"]["additionalContext"] == "hello world"
    # Must be JSON-serialisable: this is what the hook prints.
    json.dumps(out)


def test_build_eval_reminder_empty_list_is_safe() -> None:
    # No skills -> no injection (avoid noisy context).
    assert forced_eval.build_eval_reminder([]) == ""


def test_main_emits_contract_when_skills_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    GIVEN a root with one skill and FORCED_EVAL_ROOT set to it
    WHEN the hook entrypoint runs
    THEN it prints the UserPromptSubmit additionalContext contract
    """
    skill = tmp_path / "skills" / "x"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: x\n---\nbody\n")
    monkeypatch.setenv("FORCED_EVAL_ROOT", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO(""))

    with pytest.raises(SystemExit):
        forced_eval.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "x" in payload["hookSpecificOutput"]["additionalContext"]


def test_main_emits_nothing_when_no_skills(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    GIVEN a root with no skills directory
    WHEN the hook entrypoint runs
    THEN it prints nothing (no noisy injection)
    """
    monkeypatch.setenv("FORCED_EVAL_ROOT", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO(""))

    with pytest.raises(SystemExit):
        forced_eval.main()

    assert capsys.readouterr().out == ""
