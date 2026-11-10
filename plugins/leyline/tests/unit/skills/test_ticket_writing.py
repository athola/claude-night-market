"""Tests for leyline:ticket-writing.

Feature: Tickets a reader can assess at a glance
  As someone arriving at a ticket from a merge request
  I want the decision and its reason on the first screen, or one link away
  So that I can judge why the work was done without reading a thread
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

LEYLINE = Path(__file__).parents[3]
SKILL = LEYLINE / "skills" / "ticket-writing" / "SKILL.md"
MODULE = LEYLINE / "skills" / "ticket-writing" / "modules" / "tracker-mechanics.md"
CREATE_ISSUE = LEYLINE.parent / "minister" / "commands" / "create-issue.md"

MAX_PROSE_LINE_LENGTH = 80
MAX_TEMPLATE_HEADINGS = 3
BANNED_WORDS = ("seamless", "robust", "comprehensive", "leverage", "delve")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _template_headings(command_text: str, template_title: str) -> list[str]:
    """Return the headings inside one named fenced template of the command."""
    section = command_text.split(f"### {template_title}", 1)[1]
    fenced_body = section.split("```markdown", 1)[1].split("```", 1)[0]
    return re.findall(r"^## .+$", fenced_body, flags=re.MULTILINE)


class TestSkillRegistration:
    """Feature: The skill can be loaded by name."""

    @pytest.mark.unit
    def test_skill_is_registered_in_plugin_manifest(self) -> None:
        manifest = json.loads(
            _read(LEYLINE / ".claude-plugin" / "plugin.json"),
        )
        assert "./skills/ticket-writing" in manifest["skills"]

    @pytest.mark.unit
    def test_description_says_when_to_use_it(self) -> None:
        frontmatter = _read(SKILL).split("---", 2)[1]
        assert "name: ticket-writing" in frontmatter
        assert "Use when" in frontmatter


class TestGlanceRule:
    """Feature: The skill decides what a ticket must carry."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "required_phrase",
        [
            "arriving from the merge request",
            "first screen",
            "Why inline",
            "Decision plus link",
            "Do not paste",
            "Bugs",
        ],
    )
    def test_skill_states_the_rule(self, required_phrase: str) -> None:
        assert required_phrase in _read(SKILL)

    @pytest.mark.unit
    def test_skill_admits_length_is_unmeasured(self) -> None:
        assert "No study found measures" in _read(SKILL)


class TestProjectTemplateFirst:
    """Feature: A project's own ticket shape wins over the default.

    In the ARIA Jira project the user rewrote every agent ticket from the
    default shape (Why:, Done when:, Repro:) into the team's h3 template,
    and once restored it after the agent overwrote it (ARIA-184).
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "required_phrase",
        [
            "Project template first",
            "recent tickets of the same type",
            "### Impact",
            "### Expected behavior",
            "### Actual behavior",
            "### Steps to reproduce",
            "### Acceptance criteria",
            "should",
            "Contractions are fine",
        ],
    )
    def test_skill_states_the_template_rule(self, required_phrase: str) -> None:
        assert required_phrase in _read(SKILL)

    @pytest.mark.unit
    def test_skill_keeps_the_change_out_of_the_ticket(self) -> None:
        assert "belongs in the merge request" in _read(SKILL)

    @pytest.mark.unit
    def test_skill_patches_the_live_description(self) -> None:
        skill = _read(SKILL)
        assert "Read the live description" in skill
        assert "never regenerate" in skill

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "markup",
        ["{{code}}", "[text|url]", "h3.", "descriptionVersion"],
    )
    def test_module_states_jira_markup(self, markup: str) -> None:
        assert markup in _read(MODULE)


class TestTrackerMechanics:
    """Feature: Each tracker's linking facts are stated, not implied."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "fact",
        [
            "## GitHub",
            "## GitLab",
            "## Jira",
            "Related to #",
            ".gitlab/issue_templates/",
            ".github/ISSUE_TEMPLATE",
            "`gh issue create --parent`",
            "capital letters",
            "/rest/api/3/search/jql",
        ],
    )
    def test_module_states_the_fact(self, fact: str) -> None:
        assert fact in _read(MODULE)


class TestProseLimits:
    """Feature: The rule obeys itself."""

    @pytest.mark.unit
    @pytest.mark.parametrize("document", [SKILL, MODULE])
    def test_prose_lines_wrap_and_avoid_banned_words(self, document: Path) -> None:
        text = _read(document)
        in_fence = False
        body = text.split("---", 2)[2] if text.startswith("---") else text
        for line in body.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or line.startswith("|") or "http" in line:
                continue
            assert len(line) <= MAX_PROSE_LINE_LENGTH, line
        for banned_word in BANNED_WORDS:
            assert banned_word not in text.lower(), banned_word


class TestCreateIssueCommand:
    """Feature: The manual issue path produces the glanceable shape."""

    @pytest.mark.unit
    def test_command_points_at_the_skill(self) -> None:
        assert "Skill(leyline:ticket-writing)" in _read(CREATE_ISSUE)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "template_title",
        ["Bug Report Template", "Feature Request Template"],
    )
    def test_template_stays_short(self, template_title: str) -> None:
        headings = _template_headings(_read(CREATE_ISSUE), template_title)
        assert len(headings) <= MAX_TEMPLATE_HEADINGS, headings

    @pytest.mark.unit
    def test_feature_template_carries_the_decision_and_its_reason(self) -> None:
        headings = _template_headings(
            _read(CREATE_ISSUE),
            "Feature Request Template",
        )
        assert "## Why" in headings
