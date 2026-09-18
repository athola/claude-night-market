"""Tests for the warn-slop-in-markdown bundled rule.

The catalog already has `require-slop-scan-for-docs`, which fires on a
user prompt that sounds like documentation work. Nothing looks at the
markdown actually being written, so slop arriving through an edit made
for another reason is invisible until CI or a manual sweep.

This rule reads `new_text` on a markdown write. It warns and never
blocks, matching the posture the rest of the slop tooling holds: a
pattern a person has to judge does not stop the work.

The regexes are inlined in the rule frontmatter rather than loaded from
`en.yaml`. Hooks run on the system Python, which is 3.9 here and has no
pyyaml, so importing the pattern loader would break the hook on the
machines it is meant to protect. The subset is the cheap, high
confidence half; the full sweep is one command, named in the message.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hookify.core.config_loader import ConfigLoader
from hookify.core.rule_engine import RuleEngine

RULE_FILE = (
    Path(__file__).parent.parent
    / "skills"
    / "rule-catalog"
    / "rules"
    / "documentation"
    / "warn-slop-in-markdown.md"
)


class TestRuleFile:
    """Feature: the rule loads with the metadata the catalog expects."""

    def test_rule_file_exists(self) -> None:
        assert RULE_FILE.exists(), f"Rule file not found: {RULE_FILE}"

    def test_rule_loads_without_error(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.name == "warn-slop-in-markdown"

    def test_rule_is_enabled_by_default(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.enabled is True

    def test_rule_fires_on_file_writes(self) -> None:
        """Scenario: the trigger is the content, not the prompt.

        `require-slop-scan-for-docs` covers intent. This one covers the
        write, which is the case where the author was not thinking
        about documentation at all.
        """
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.event == "file"

    def test_rule_warns_rather_than_blocks(self) -> None:
        """Guard: a judgment call must not stop a write."""
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.action == "warn"

    def test_message_names_the_audit_command(self) -> None:
        """Scenario: the warning has to end the hand-written prompt.

        A warning that says "there is slop here" and stops leaves the
        author to write the long prompt again. The message carries the
        one command that locates every finding.
        """
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert "--audit" in rule.message
        assert "slop_score.py" in rule.message


class TestMatching:
    """Feature: the six patterns the operator has to hunt by hand."""

    @pytest.fixture()
    def engine(self) -> RuleEngine:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        return RuleEngine([rule])

    def _matched(self, engine: RuleEngine, text: str, path: str = "README.md") -> bool:
        results = engine.evaluate_event("file", {"file_path": path, "new_text": text})
        return any(result.matched for result in results)

    # --- should warn ---

    def test_em_dash(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The cache is warm — the probe is not.")

    def test_spaced_double_dash(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The cache is warm -- the probe is not.")

    def test_plus_sign_as_conjunction(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The hooks + skills load together.")

    def test_semicolon_splicing_two_clauses(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The system is fast; it scales.")

    def test_trailing_contrastive_negation(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The result is clear, not clever.")

    def test_copula_led_contrastive_negation(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "It's a tool, not a toy.")

    def test_smart_quotes(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The flag is named “verbose” here.")

    # --- should stay quiet ---

    def test_clean_prose_does_not_warn(self, engine: RuleEngine) -> None:
        assert not self._matched(
            engine, "The exporter emits one row per session. The cache holds ten."
        )

    def test_a_non_markdown_file_does_not_warn(self, engine: RuleEngine) -> None:
        """Guard: `a + b` is arithmetic in Python, not a conjunction."""
        assert not self._matched(
            engine, "total = a + b\n", path="plugins/scribe/src/scribe/sum.py"
        )

    def test_a_semicolon_inside_a_list_does_not_warn(self, engine: RuleEngine) -> None:
        """Guard: the one durable keep is a list with internal commas.

        `slop-scan-for-docs.md` says so explicitly. A pattern that fired
        on it would train authors to ignore the warning.
        """
        assert not self._matched(
            engine,
            "Three inputs: the path, which may be relative; the tier; the budget.",
        )


class TestNegationMatching:
    """Feature: negative-tense reliance is warned at write time too.

    The hand-written prompt this rule replaces named "doesn't do this"
    and "because cannot do that" as the last thing to hunt. Only the
    high-confidence forms from `en.yaml` belong here: a vacuous negation
    claims weight and supplies none, and a litotes says one positive
    thing through two negations. `negative_definition` stays out, since
    a warn-on-every-write hook firing on "does not support" would
    contradict the reason `en.yaml` gates it off.
    """

    @pytest.fixture()
    def engine(self) -> RuleEngine:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        return RuleEngine([rule])

    def _matched(self, engine: RuleEngine, text: str) -> bool:
        results = engine.evaluate_event(
            "file", {"file_path": "README.md", "new_text": text}
        )
        return any(result.matched for result in results)

    def test_mid_sentence_not_just_tail(self, engine: RuleEngine) -> None:
        assert self._matched(
            engine, "The third sends your code, not just a status check."
        )

    def test_vacuous_negation(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "The value of tests cannot be overstated.")
        assert self._matched(engine, "Needless to say, the gate passes.")

    def test_litotes(self, engine: RuleEngine) -> None:
        assert self._matched(engine, "It is not uncommon for the probe to stall.")

    def test_a_negation_carrying_a_fact_does_not_warn(self, engine: RuleEngine) -> None:
        """Guard: "the hook cannot reach the registry" states a behavior."""
        assert not self._matched(
            engine, "The hook cannot reach the registry. The probe does not run."
        )

    def test_message_lists_the_negation_rewrite(self, engine: RuleEngine) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert "overstated" in rule.message
