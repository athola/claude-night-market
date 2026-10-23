# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Contract tests for the commit-messages skill and the /commit-msg command.

Both are instructions for the model, not code. A commit message is only as
good as those instructions, so these tests pin the rules in them: the
types, the subject and body format, and the slop lists. The skill and the
command are two routes to the same message, so where both state a rule the
tests also hold them to the same answer.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = PLUGIN_ROOT / "skills" / "commit-messages" / "SKILL.md"
COMMAND_FILE = PLUGIN_ROOT / "commands" / "commit-msg.md"


def _step(text: str, heading: str) -> str:
    """Return one numbered step, from its bold heading to the next step."""
    match = re.search(
        rf"^\d+[a-z]?\. \*\*{re.escape(heading)}\*\*.*?(?=^\d+[a-z]?\. \*\*|^## )",
        text,
        re.DOTALL | re.MULTILINE,
    )
    assert match, f"step {heading!r} not found"
    return match.group(0)


def _types(text: str, heading: str) -> set[str]:
    return set(re.findall(r"`([a-z]+)`", _step(text, heading)))


def _skill_slop_table(text: str) -> dict[str, str]:
    """Map each word in the skill's Reject column to its replacement."""
    table = {}
    for reject, use in re.findall(
        r"^\s*\| ([a-z, ]+) \| ([a-z]+) \|$", _step(text, "Slop check"), re.MULTILINE
    ):
        for word in reject.split(","):
            table[word.strip()] = use
    return table


def _command_slop_list(text: str) -> set[str]:
    step = _step(text, "Slop check")
    banned = step.split("must NOT contain:", 1)[1].split("If found", 1)[0]
    return {
        item.strip().strip('"').lower()
        for item in re.split(r",\s*", banned)
        if item.strip()
    }


def _skill_slop_phrases(text: str) -> list[str]:
    also = _step(text, "Slop check").split("Also reject:", 1)[1]
    return [phrase.lower() for phrase in re.findall(r'"([^"]+)"', also)]


@pytest.fixture(scope="module")
def skill() -> str:
    return SKILL_FILE.read_text()


@pytest.fixture(scope="module")
def command() -> str:
    return COMMAND_FILE.read_text()


class TestCommitMessagesSkill:
    """Behavior-driven tests for the commit-messages skill."""

    def test_skill_and_command_both_offer_feat_and_the_type_scope_summary_format(
        self, skill: str, command: str
    ) -> None:
        """Both routes offer `feat` and draft `<type>(<scope>): <summary>`."""
        assert "feat" in _types(skill, "Classify")
        assert "feat" in _types(command, "Classify the change")
        assert "`<type>(<scope>): <imperative summary>`" in skill
        assert "<type>(<scope>): <imperative summary" in command

    def test_skill_and_command_both_offer_fix_type(
        self, skill: str, command: str
    ) -> None:
        """Both routes offer `fix` as a commit type."""
        assert "fix" in _types(skill, "Classify")
        assert "fix" in _types(command, "Classify the change")

    def test_skill_and_command_both_offer_docs_type(
        self, skill: str, command: str
    ) -> None:
        """Both routes offer `docs` as a commit type."""
        assert "docs" in _types(skill, "Classify")
        assert "docs" in _types(command, "Classify the change")

    def test_skill_and_command_offer_the_same_commit_types(
        self, skill: str, command: str
    ) -> None:
        """Both routes offer `refactor`, and they offer the same type set."""
        skill_types = _types(skill, "Classify")
        assert "refactor" in skill_types
        assert skill_types == _types(command, "Classify the change")

    def test_skill_documents_scope_in_subject_and_breaking_change_footer(
        self, skill: str, command: str
    ) -> None:
        """The footer carries BREAKING CHANGE, and the scope sits in the subject."""
        draft = _step(skill, "Draft the message")
        assert "**Footer**: BREAKING CHANGE" in draft
        assert "(<scope>)" in draft
        assert "BREAKING CHANGE" in _step(command, "Draft the message")

    def test_skill_and_command_gather_context_from_the_staged_diff(
        self, skill: str, command: str
    ) -> None:
        """Context comes from the staged diff, and stops when nothing is staged."""
        for text in (skill, command):
            gather = _step(text, "Gather context")
            assert "`git diff --cached`" in gather
            assert "`git diff --cached --stat`" in gather
        assert "If nothing is staged, tell the user and stop." in skill
        assert "If nothing is staged" in command

    def test_skill_and_command_cap_the_imperative_subject_at_50_chars(
        self, skill: str, command: str
    ) -> None:
        """The subject is an imperative summary capped at 50 characters."""
        assert "imperative summary>` (50 chars max)" in _step(
            skill, "Draft the message"
        )
        assert "<imperative summary, ≤50 chars>" in _step(command, "Draft the message")
        assert "is at most 50 characters" in skill

    def test_command_template_has_a_blank_line_between_subject_and_body(
        self, command: str
    ) -> None:
        """The command's template puts one blank line between subject and body."""
        template = re.search(
            r"```\n(.*?)```", _step(command, "Draft the message"), re.DOTALL
        )
        assert template
        lines = template.group(1).strip().splitlines()
        assert lines[0].lstrip().startswith("<type>(<scope>):")
        assert lines[1].strip() == ""
        assert lines[2].lstrip().startswith("<body:")

    def test_skill_and_command_wrap_the_body_at_72_chars(
        self, skill: str, command: str
    ) -> None:
        """Both routes wrap the body at 72 characters."""
        assert "wrapped at 72 chars" in _step(skill, "Draft the message")
        assert "wrapped at 72 chars" in _step(command, "Draft the message")


class TestCommitMessageSlopDetection:
    """Feature: Detect and reject AI slop in commit messages.

    As a repository maintainer
    I want commit messages to be free of AI-generated content markers
    So that the git history reads naturally and professionally
    """

    # Tier 1 slop words that should ALWAYS be rejected
    TIER1_SLOP_WORDS = [
        "leverage",
        "utilize",
        "seamless",
        "comprehensive",
        "robust",
        "facilitate",
        "streamline",
        "delve",
        "multifaceted",
        "pivotal",
        "intricate",
        "nuanced",
    ]

    def test_command_rejects_every_tier1_slop_word(self, command: str) -> None:
        """Scenario: /commit-msg rejects every tier-1 slop word."""
        missing = set(self.TIER1_SLOP_WORDS) - _command_slop_list(command)
        assert not missing, f"/commit-msg does not reject: {sorted(missing)}"

    def test_skill_replacement_words_are_not_themselves_rejected(
        self, skill: str, command: str
    ) -> None:
        """Scenario: no replacement word the skill suggests is itself rejected."""
        replacements = set(_skill_slop_table(skill).values())
        banned = set(_skill_slop_table(skill)) | _command_slop_list(command)
        assert replacements
        assert not replacements & banned

    def test_command_rejects_every_slop_phrase_the_skill_rejects(
        self, skill: str, command: str
    ) -> None:
        """Scenario: every phrase the skill rejects, the command rejects too."""
        phrases = _skill_slop_phrases(skill)
        assert "it's worth noting" in phrases
        assert "at its core" in phrases
        missing = set(phrases) - _command_slop_list(command)
        assert not missing, f"/commit-msg does not reject: {sorted(missing)}"

    def test_skill_maps_each_slop_word_to_a_plain_alternative_the_command_also_rejects(
        self, skill: str, command: str
    ) -> None:
        """Scenario: the skill maps each rejected word to a plain alternative."""
        alternatives = {
            "leverage": "use",
            "utilize": "use",
            "comprehensive": "complete",
            "robust": "solid",
            "facilitate": "enable",
            "streamline": "simplify",
            "delve": "explore",
        }

        table = _skill_slop_table(skill)
        assert {word: table.get(word) for word in alternatives} == alternatives
        missing = set(table) - _command_slop_list(command)
        assert not missing, f"/commit-msg does not reject: {sorted(missing)}"
