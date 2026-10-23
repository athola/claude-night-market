"""The improvement suggester advises what the auditor scores.

It told every skill to add Overview, Quick Start, Examples and Resources
sections, code blocks, and more headings. The auditor no longer scores
those (see test_skills_eval_auditor_evidence_rubric.py), so advice to add
them would push skills toward padding the evidence says hurts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.skills_eval.improvements import ImprovementSuggester

_MAP_SKILL = (
    "---\n"
    "name: map-skill\n"
    "description: Checks widgets. Use when a widget changes.\n"
    "---\n\n"
    "# Map Skill\n\nCheck the widget against its schema.\n\n"
    "## Exit Criteria\n\n- [ ] Report written\n- [ ] Exit code 0\n"
)


def _suggester(tmp_path: Path, content: str) -> ImprovementSuggester:
    skill = tmp_path / "map-skill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(content)
    return ImprovementSuggester(tmp_path)


@pytest.mark.unit
def test_map_style_skill_gets_no_section_or_example_padding(tmp_path: Path) -> None:
    """A compact skill with triggers and Exit Criteria needs nothing added."""
    suggester = _suggester(tmp_path, _MAP_SKILL)
    advice = suggester.analyze_skill("map-skill")[
        "suggestions"
    ] + suggester.suggest_improved_structure("map-skill")
    padding = ("Overview", "Quick Start", "Examples", "Resources", "code blocks")
    assert not [a for a in advice if any(p in a for p in padding)]
    assert not [a for a in advice if "structured sections" in a]


@pytest.mark.unit
def test_missing_exit_criteria_is_suggested(tmp_path: Path) -> None:
    """Exit Criteria are the one section every skill must carry."""
    no_exit = _MAP_SKILL.split("## Exit Criteria", maxsplit=1)[0]
    suggester = _suggester(tmp_path, no_exit)
    analysis = suggester.analyze_skill("map-skill")
    assert any("Exit Criteria" in i for i in analysis["issues"])
    assert any("Exit Criteria" in s for s in analysis["suggestions"])


@pytest.mark.unit
def test_description_without_trigger_is_suggested(tmp_path: Path) -> None:
    """Discovery reads the description, so it must say when to use the skill."""
    vague = _MAP_SKILL.replace(
        "Checks widgets. Use when a widget changes.", "Widget helper."
    )
    suggestions = _suggester(tmp_path, vague).analyze_skill("map-skill")["suggestions"]
    assert any("description" in s and "when" in s for s in suggestions)


@pytest.mark.unit
def test_line_cap_suggestion_counts_body_only_like_the_auditor(
    tmp_path: Path,
) -> None:
    """495 body lines under 12 frontmatter lines is under the 500-line cap."""
    frontmatter = "---\n" + "".join(f"k{i}: v\n" for i in range(10)) + "---\n"
    body = "".join(f"line {i}\n" for i in range(495))
    suggester = _suggester(tmp_path, frontmatter + body)
    advice = suggester.suggest_improved_structure("map-skill")
    assert not [a for a in advice if "lines" in a]


@pytest.mark.unit
def test_line_cap_suggestion_fires_when_body_exceeds_cap(tmp_path: Path) -> None:
    """The body alone over 500 lines still draws the move-to-modules advice."""
    body = "".join(f"line {i}\n" for i in range(501))
    suggester = _suggester(tmp_path, "---\nname: map-skill\n---\n" + body)
    advice = suggester.suggest_improved_structure("map-skill")
    assert any("501 lines" in a for a in advice)
