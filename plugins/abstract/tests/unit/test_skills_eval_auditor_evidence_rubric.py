"""The skill auditor scores what the evidence ties to skill outcomes.

The earlier rubric rewarded numbered lines, code blocks and
``tags``/``category`` in every skill. Anthropic's skill guidance matches
prescriptiveness to the task's fragility instead, SkillsBench
(arXiv 2602.12670) finds compact skills beat exhaustive ones, and Claude
Code reads only ``name`` and ``description`` for discovery. The rubric
now scores a description with triggers, a checkable Exit Criteria
section, and size.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract import skills_eval
from abstract.skills_eval.auditor import SkillsAuditor

_FRONT = (
    "---\n"
    "name: demo\n"
    "description: Checks demo widgets. Use when a widget changes.\n"
    "---\n"
)
_EXIT = "\n## Exit Criteria\n\n- [ ] Report written to out.md\n- [ ] Exit code 0\n"


def _metrics(tmp_path: Path, content: str):
    skill = tmp_path / "skills" / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(content)
    return SkillsAuditor(tmp_path / "skills")._analyze_skill_file(skill)


@pytest.mark.unit
def test_numbered_steps_and_code_blocks_do_not_change_the_score(
    tmp_path: Path,
) -> None:
    """A map-style skill scores the same as one padded with steps and code."""
    plain = _FRONT + "# Demo\n\nCheck the widget against its schema.\n" + _EXIT
    padded = (
        _FRONT + "# Demo\n\n## Quick Start\n\n1. Open it\n2. Check it\n3. Close it\n\n"
        "```bash\nls\n```\n\n```bash\npwd\n```\n" + _EXIT
    )
    assert _metrics(tmp_path / "a", plain).score == pytest.approx(
        _metrics(tmp_path / "b", padded).score, abs=1.0
    )


@pytest.mark.unit
def test_tags_category_and_steps_are_not_reported_missing(tmp_path: Path) -> None:
    """Fields Claude Code never reads, and absent steps, are not defects."""
    issues = _metrics(tmp_path, _FRONT + "# Demo\n\nBody.\n" + _EXIT).issues
    assert not any("tags" in i or "category" in i for i in issues)
    assert not any("step-by-step" in i or "code examples" in i for i in issues)


@pytest.mark.unit
def test_description_without_a_trigger_is_reported_and_scores_lower(
    tmp_path: Path,
) -> None:
    """Discovery reads the description, so it must say when to use the skill."""
    vague = "---\nname: demo\ndescription: Demo widget helper.\n---\n"
    weak = _metrics(tmp_path / "a", vague + "# Demo\n" + _EXIT)
    good = _metrics(tmp_path / "b", _FRONT + "# Demo\n" + _EXIT)
    assert any("trigger" in i for i in weak.issues)
    assert weak.score < good.score


@pytest.mark.unit
@pytest.mark.parametrize(
    "description",
    [
        "Checks setup. Use at the start of every session.",
        "Checks setup. Use during a review.",
        "Checks setup. Use whenever a hook changes.",
        "Checks setup. Use this skill when asked to audit hooks.",
        "Checks setup. Invoke when a hook changes.",
    ],
)
def test_common_trigger_phrasings_are_recognized(
    tmp_path: Path, description: str
) -> None:
    """'Use at', 'Use during' and 'Use whenever' all say when to use a skill."""
    front = f"---\nname: demo\ndescription: {description}\n---\n"
    issues = _metrics(tmp_path, front + "# Demo\n" + _EXIT).issues
    assert not any("trigger" in i for i in issues)


@pytest.mark.unit
def test_missing_exit_criteria_is_reported_and_scores_lower(tmp_path: Path) -> None:
    """Exit Criteria are required of every skill by this repository."""
    without = _metrics(tmp_path / "a", _FRONT + "# Demo\n\nBody.\n")
    with_it = _metrics(tmp_path / "b", _FRONT + "# Demo\n\nBody.\n" + _EXIT)
    assert any("Exit Criteria" in i for i in without.issues)
    assert without.score < with_it.score


@pytest.mark.unit
def test_exit_criteria_with_one_checkable_item_is_reported(tmp_path: Path) -> None:
    """One item is rarely a verifiable finish line."""
    one = _FRONT + "# Demo\n\n## Exit Criteria\n\n- [ ] Done\n"
    assert any("checkable" in i for i in _metrics(tmp_path, one).issues)


@pytest.mark.unit
def test_plain_bullet_criteria_count_as_checkable_items(tmp_path: Path) -> None:
    """Checkbox syntax is not required: plain bullets are criteria too."""
    bullets = _FRONT + "# Demo\n\n## Exit Criteria\n\n- Report written\n- Exit 0\n"
    assert not any("checkable" in i for i in _metrics(tmp_path, bullets).issues)


@pytest.mark.unit
def test_body_over_500_lines_is_reported(tmp_path: Path) -> None:
    """Anthropic and the Agent Skills spec both cap SKILL.md at 500 lines."""
    long_body = _FRONT + "# Demo\n" + "line\n" * 520 + _EXIT
    assert any("500 lines" in i for i in _metrics(tmp_path, long_body).issues)


@pytest.mark.unit
def test_compact_skill_with_trigger_and_exit_criteria_scores_90_plus(
    tmp_path: Path,
) -> None:
    """The shape the evidence favors is what scores well."""
    skill = _FRONT + "# Demo\n\nCheck the widget against its schema.\n" + _EXIT
    assert _metrics(tmp_path, skill).score >= 90


@pytest.mark.unit
def test_line_cap_counts_the_body_not_the_frontmatter(tmp_path: Path) -> None:
    """The 500-line limit applies to the SKILL.md body."""
    front = "---\nname: demo\ndescription: Use when testing.\n" + "k: v\n" * 30
    body = "# Demo\n" + "line\n" * 480 + _EXIT
    assert not any(
        "500 lines" in i for i in _metrics(tmp_path, front + "---\n" + body).issues
    )


@pytest.mark.unit
def test_rubric_constants_are_exported_from_the_package() -> None:
    """Like every other auditor constant, the rubric's are package exports."""
    for name in (
        "DESCRIPTION_TRIGGER",
        "EXIT_CRITERIA_HEADING",
        "MAX_BODY_LINES",
        "MAX_DESCRIPTION_CHARS",
        "MIN_EXIT_CRITERIA_ITEMS",
    ):
        assert name in skills_eval.__all__
