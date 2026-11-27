# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Tests for output hygiene across commit-message and PR workflows.

Covers two contracts the sanctum workflows must honor for every piece
of text they emit (commit messages, PR comments, thread replies,
summaries):

1. Character-level slop markers are stripped before posting: the
   prose-conjunction "+", em-dash, double-dash, ASCII/unicode arrows,
   and smart quotes.
2. Commit messages never describe a change as removing AI slop or AI
   content. The change is classified by its substantive effect.

The shared module is the single source of truth; each consumer also
carries an inline fallback so the rule holds when the shared module is
not installed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SANCTUM = REPO_ROOT / "plugins" / "sanctum"

SHARED_MODULE = SANCTUM / "commands" / "shared" / "output-hygiene.md"

# Consumers that must reference the shared module AND carry an inline
# fallback for the character-level markers.
CONSUMERS = [
    SANCTUM / "commands" / "commit-msg.md",
    SANCTUM / "skills" / "commit-messages" / "SKILL.md",
    SANCTUM / "commands" / "pr-review" / "modules" / "review-workflow-phases-1-4.md",
    SANCTUM / "commands" / "fix-pr-modules" / "steps" / "4-fix.md",
    SANCTUM / "commands" / "fix-pr-modules" / "steps" / "6-complete" / "summary.md",
]

# Consumers whose commit messages must also carry the no-AI-mention rule.
COMMIT_CONSUMERS = [
    SANCTUM / "commands" / "commit-msg.md",
    SANCTUM / "skills" / "commit-messages" / "SKILL.md",
    SANCTUM / "commands" / "fix-pr-modules" / "steps" / "4-fix.md",
]


class TestSharedOutputHygieneModule:
    """Feature: a shared module defines both output-hygiene contracts."""

    def test_shared_module_exists(self) -> None:
        assert SHARED_MODULE.is_file(), f"missing {SHARED_MODULE}"

    def test_shared_module_lists_character_markers(self) -> None:
        text = SHARED_MODULE.read_text(encoding="utf-8")
        # em-dash, double-dash separator, ASCII + unicode arrows
        assert "—" in text, "em-dash marker not documented"
        assert " -- " in text, "double-dash marker not documented"
        assert "->" in text, "ASCII arrow marker not documented"
        assert "→" in text, "unicode arrow marker not documented"
        # the "+" prose-conjunction rule
        assert re.search(r'"\+"|`\+`', text), '"+" conjunction rule not documented'
        # smart quotes
        assert "“" in text or "smart quote" in text.lower()

    def test_shared_module_forbids_ai_removal_mentions(self) -> None:
        text = SHARED_MODULE.read_text(encoding="utf-8").lower()
        assert "ai slop" in text
        assert "ai content" in text or "ai-generated" in text
        # The rule must be a prohibition, not just a mention.
        assert "never" in text or "do not" in text or "must not" in text

    def test_shared_module_forbids_naming_stripped_content(self) -> None:
        """Contract B also bars naming the specific marker removed."""
        text = SHARED_MODULE.read_text(encoding="utf-8").lower()
        # The module must call out that naming em-dashes / phrasing /
        # smart quotes in the commit message is itself a leak.
        assert "em-dash" in text or "em dash" in text
        assert "phrasing" in text
        assert "effect" in text  # "describe the change by its effect"


class TestConsumersReferenceSharedModule:
    """Feature: every consumer references the shared module."""

    @pytest.mark.parametrize("path", CONSUMERS, ids=lambda p: p.name)
    def test_consumer_references_shared_module(self, path: Path) -> None:
        assert path.is_file(), f"missing consumer {path}"
        text = path.read_text(encoding="utf-8")
        assert "output-hygiene" in text, (
            f"{path.name} does not reference shared/output-hygiene.md"
        )

    @pytest.mark.parametrize("path", CONSUMERS, ids=lambda p: p.name)
    def test_consumer_has_inline_fallback_markers(self, path: Path) -> None:
        """Each consumer carries an inline fallback for the key markers."""
        text = path.read_text(encoding="utf-8")
        # em-dash and the "+" conjunction are the two most common leaks;
        # the inline fallback must name both.
        assert "—" in text, f"{path.name} inline fallback missing em-dash"
        assert re.search(r'"\+"|`\+`', text), (
            f"{path.name} inline fallback missing '+' conjunction rule"
        )


class TestCommitMessageNoAiMention:
    """Feature: commit messages never advertise AI-slop/content removal."""

    @pytest.mark.parametrize("path", COMMIT_CONSUMERS, ids=lambda p: p.name)
    def test_commit_consumer_forbids_ai_mention(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8").lower()
        assert "ai slop" in text, f"{path.name} missing no-AI-mention rule"
        assert "never" in text or "do not" in text or "must not" in text
