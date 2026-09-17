"""Tests for the require-slop-scan-for-docs bundled rule.

This rule fires on a prompt that sounds like documentation work. Its
message is the first thing an author sees, so it has to carry the whole
checklist the operator used to type by hand and the one command that
locates every item on it.
"""

from __future__ import annotations

from pathlib import Path

from hookify.core.config_loader import ConfigLoader

RULE_FILE = (
    Path(__file__).parent.parent
    / "skills"
    / "rule-catalog"
    / "rules"
    / "documentation"
    / "require-slop-scan-for-docs.md"
)


def _message() -> str:
    loader = ConfigLoader(include_bundled=True)
    return loader.load_rule(RULE_FILE, source="bundled").message


class TestMessageCarriesTheChecklist:
    """Feature: the prompt-time warning replaces the hand-written prompt."""

    def test_names_the_audit_command(self) -> None:
        assert "slop_score.py --audit" in _message()

    def test_names_every_pattern_the_operator_hunted_by_hand(self) -> None:
        message = _message()
        for tell in (
            "Em dash",
            "--",
            "Plus-sign",
            "Semicolon",
            "not just",
            "Over-explained",
            "Negative",
        ):
            assert tell in message, f"checklist omits: {tell}"

    def test_prose_uses_no_arrow_connectors(self) -> None:
        """Guard: the rule scored 16.82 on its own patterns, arrows included."""
        assert "→" not in _message()
