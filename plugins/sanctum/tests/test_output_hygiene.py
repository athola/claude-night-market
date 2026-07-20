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


class TestCharacterMarkerDetectionLogic:
    """Feature: detect character-level slop markers in emitted text.

    These encode the detection spec the workflows implement so a
    regression in the rule set is caught here.
    """

    def test_detects_plus_used_as_conjunction(self) -> None:
        bad = "feat: add parser + validator"
        # "+" surrounded by spaces between words is a prose conjunction.
        assert re.search(r"\w \+ \w", bad), "should flag '+' conjunction"

    def test_allows_plus_in_version_and_code(self) -> None:
        ok_samples = ["chore: bump to 1.2.0+build", "fix: handle a+=1 overflow"]
        for sample in ok_samples:
            assert not re.search(r"\w \+ \w", sample), f"false positive: {sample}"

    def test_detects_em_dash(self) -> None:
        sample = "fix: guard nulls — prevents crash"
        assert "—" in sample

    def test_detects_double_dash_separator(self) -> None:
        sample = "fix: guard nulls -- prevents crash"
        assert " -- " in sample

    def test_detects_arrow_connectors(self) -> None:
        ascii_sample = "docs: map input -> output"
        unicode_sample = "docs: map input → output"
        assert "->" in ascii_sample
        assert "→" in unicode_sample

    def test_detects_smart_quotes(self) -> None:
        sample = "docs: clarify “usage” section"
        assert "“" in sample


class TestCommitSubjectMatterLogic:
    """Feature: reject commit subjects that name AI-slop removal OR the
    specific stripped content (em-dashes, AI phrasing, smart quotes).
    """

    # Mentions that leak either the AI origin or the specific marker
    # the commit removed. A slop-removal commit names neither.
    FORBIDDEN_MENTIONS = [
        # origin / process
        "ai slop",
        "ai-generated",
        "ai generated",
        "ai phrasing",
        "ai markers",
        "slop marker",
        "de-slop",
        "deslop",
        "remove ai",
        "removed ai",
        "strip ai",
        # specific stripped artifacts
        "em-dash",
        "em dash",
        "emdash",
        "smart quote",
        "curly quote",
    ]

    def test_detects_origin_removal_subjects(self) -> None:
        bad_subjects = [
            "docs: remove AI slop from README",
            "style: strip AI slop markers",
            "chore: de-slop the tutorial",
            "docs: remove AI-generated content",
            "docs: strip AI phrasing from guide",
        ]
        for subject in bad_subjects:
            low = subject.lower()
            assert any(p in low for p in self.FORBIDDEN_MENTIONS), (
                f"should flag origin-removal subject: {subject}"
            )

    def test_detects_named_marker_subjects(self) -> None:
        """Naming the specific marker removed is also forbidden."""
        bad_subjects = [
            "style: replace em-dashes with colons",
            "style: remove em dashes from README",
            "docs: replace smart quotes with straight quotes",
        ]
        for subject in bad_subjects:
            low = subject.lower()
            assert any(p in low for p in self.FORBIDDEN_MENTIONS), (
                f"should flag named-marker subject: {subject}"
            )

    def test_accepts_effect_focused_rewordings(self) -> None:
        """Only subjects describing the reader-facing effect pass."""
        good_subjects = [
            "docs: tighten README install steps",
            "docs: clarify the setup section",
            "docs: rewrite tutorial intro for clarity",
            "docs: simplify the overview wording",
        ]
        for subject in good_subjects:
            low = subject.lower()
            assert not any(p in low for p in self.FORBIDDEN_MENTIONS), (
                f"false positive on effect-focused subject: {subject}"
            )
