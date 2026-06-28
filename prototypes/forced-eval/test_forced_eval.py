"""TDD tests for the forced-eval activation hook prototype.

Written FIRST (red). The implementation in forced_eval.py is added
afterwards to turn them green. Run: python -m pytest test_forced_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path

import forced_eval


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
