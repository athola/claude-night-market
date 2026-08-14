"""Contract tests for the simplified-technical-english skill.

Each assertion anchors on a clause unique to the passage it guards, so
deleting that passage turns the test red. The claims pinned here are
the ones that are either legally load-bearing (what the project may not
say about ASD-STE100) or correctness-load-bearing (the boundary that
keeps the 20-word cap away from prose it would damage).

Numbers are pinned against ``scribe.ste`` rather than restated, so the
documentation cannot drift away from the code that implements it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / "src"))

from scribe.ste import (
    DESCRIPTIVE_MAX_WORDS,
    NOUN_CLUSTER_MAX_WORDS,
    PARAGRAPH_MAX_SENTENCES,
    PROCEDURAL_MAX_WORDS,
)

SKILL_DIR = Path(__file__).parents[3] / "skills" / "simplified-technical-english"
SKILL = SKILL_DIR / "SKILL.md"
MODULES = {
    "adopted": SKILL_DIR / "modules" / "adopted-rules.md",
    "scope": SKILL_DIR / "modules" / "scope-boundaries.md",
    "reconciliation": SKILL_DIR / "modules" / "reconciliation.md",
    "licensing": SKILL_DIR / "modules" / "licensing.md",
}


def _read(path: Path) -> str:
    assert path.exists(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


class TestSkillStructure:
    """Feature: the skill is a well-formed, registered hub."""

    @pytest.mark.unit
    def test_hub_exists_with_frontmatter(self) -> None:
        text = _read(SKILL)
        assert text.startswith("---\n")
        assert "name: simplified-technical-english" in text

    @pytest.mark.unit
    def test_every_declared_module_exists(self) -> None:
        """A module listed in frontmatter must be on disk."""
        text = _read(SKILL)
        declared = re.findall(r"^- (modules/[\w-]+\.md)$", text, re.MULTILINE)
        assert declared, "no modules declared in frontmatter"
        for rel in declared:
            assert (SKILL_DIR / rel).exists(), f"declared but missing: {rel}"

    @pytest.mark.unit
    def test_every_module_on_disk_is_declared(self) -> None:
        """A module on disk that nothing declares is unreachable."""
        text = _read(SKILL)
        for path in (SKILL_DIR / "modules").glob("*.md"):
            assert f"modules/{path.name}" in text, f"undeclared module: {path.name}"

    @pytest.mark.unit
    def test_skill_has_exit_criteria(self) -> None:
        """Required by .claude/rules/skill-exit-criteria.md."""
        text = _read(SKILL)
        assert "## Exit Criteria" in text
        section = text.split("## Exit Criteria", 1)[1]
        assert section.count("- [ ]") >= 3

    @pytest.mark.unit
    def test_skill_is_registered_in_plugin_manifest(self) -> None:
        manifest = Path(__file__).parents[3] / ".claude-plugin" / "plugin.json"
        skills = json.loads(manifest.read_text())["skills"]
        assert "./skills/simplified-technical-english" in skills


class TestLegalPosture:
    """Feature: the project never overclaims its relationship to ASD.

    These are the assertions that protect the repository rather than
    the reader. Each one corresponds to a statement ASD publishes.
    """

    @pytest.mark.unit
    def test_licensing_module_refuses_compliance_claims(self) -> None:
        text = _read(MODULES["licensing"])
        assert "not an implementation" in text or "not claim" in text
        assert "compliant" in text

    @pytest.mark.unit
    def test_licensing_module_states_the_dictionary_cannot_ship(self) -> None:
        text = _read(MODULES["licensing"]).lower()
        assert "dictionary" in text
        assert "redistribut" in text or "cannot ship" in text

    @pytest.mark.unit
    def test_licensing_module_records_the_endorsement_wording(self) -> None:
        """ASD's statement is scoped to sellers claiming full compliance.

        An earlier draft widened this to "does not endorse software
        tools", which is not what ASD says.
        """
        text = _read(MODULES["licensing"])
        assert "endorse" in text
        assert "fully compliant" in text

    @pytest.mark.unit
    def test_no_file_attributes_compliance_to_this_project(self) -> None:
        """No file may describe *this work* as compliant or certified.

        Scoped to self-attribution on purpose. The licensing module has
        to quote ASD's own phrase "fully compliant" to record what ASD
        says, so a blanket ban on the phrase would make the two
        requirements impossible to satisfy at once.
        """
        forbidden = re.compile(
            r"\b(?:this|these|our|the)\s+(?:\w+\s+){0,2}"
            r"(?:is|are)\s+(?:fully\s+)?(?:STE[- ])?(?:compliant|certified)\b",
            re.IGNORECASE,
        )
        for name, path in MODULES.items():
            match = forbidden.search(_read(path))
            assert match is None, f"compliance claim in {name}: {match!r}"
        assert forbidden.search(_read(SKILL)) is None


class TestRuleNumberDiscipline:
    """Feature: only verifiable rule numbers appear anywhere.

    Public sources corroborate the rule *content* but not the
    numbering. Rule 8.1 is the single exception. A bare "rule N.M"
    anywhere else is unverifiable and must not ship.
    """

    ALLOWED = {"8.1"}

    @pytest.mark.unit
    @pytest.mark.parametrize("key", ["adopted", "scope", "reconciliation", "licensing"])
    def test_module_cites_no_unverifiable_rule_numbers(self, key: str) -> None:
        cited = set(re.findall(r"\brules?\s+(\d+\.\d+)", _read(MODULES[key]), re.I))
        assert cited <= self.ALLOWED, f"unverifiable rule numbers in {key}: {cited}"

    @pytest.mark.unit
    def test_hub_cites_no_unverifiable_rule_numbers(self) -> None:
        cited = set(re.findall(r"\brules?\s+(\d+\.\d+)", _read(SKILL), re.I))
        assert cited <= self.ALLOWED

    @pytest.mark.unit
    def test_rule_count_is_the_corroborated_figure(self) -> None:
        """53 rules in 9 sections. An earlier draft said roughly 65."""
        text = _read(MODULES["adopted"])
        assert "53" in text
        assert "65" not in text


class TestScopeBoundary:
    """Feature: the boundary that keeps STE off prose it would damage.

    This is the correctness core. Without it a future agent applies the
    20-word cap to a docstring and deletes the reasoning it carries.
    """

    @pytest.mark.unit
    def test_scope_module_excludes_rationale_bearing_text(self) -> None:
        text = _read(MODULES["scope"]).lower()
        for excluded in ("docstring", "adr"):
            assert excluded in text, f"scope module never mentions {excluded}"

    @pytest.mark.unit
    def test_reconciliation_names_the_sentence_length_collision(self) -> None:
        """The slop detector and STE genuinely disagree here."""
        text = _read(MODULES["reconciliation"])
        assert "slop-detector" in text or "slop detector" in text
        assert "15-25" in text or "15–25" in text

    @pytest.mark.unit
    def test_reconciliation_states_which_regime_governs_these_docs(self) -> None:
        """Without this row, the checker gets pointed at its own docs.

        These skill files are descriptive repo prose. The house rules
        govern them, not STE.
        """
        text = _read(MODULES["reconciliation"]).lower()
        assert "house" in text
        assert "this skill" in text or "these docs" in text or "repo prose" in text


class TestDocumentedNumbersMatchTheCode:
    """Feature: documentation cannot drift from the implementation."""

    @pytest.mark.unit
    def test_hub_states_the_four_limits(self) -> None:
        text = _read(SKILL)
        for value in (
            PROCEDURAL_MAX_WORDS,
            DESCRIPTIVE_MAX_WORDS,
            PARAGRAPH_MAX_SENTENCES,
            NOUN_CLUSTER_MAX_WORDS,
        ):
            assert str(value) in text, f"hub never states the limit {value}"

    @pytest.mark.unit
    def test_hub_discloses_the_noun_cluster_noise(self) -> None:
        """A 76%-of-files check must not be presented as a gate."""
        text = _read(SKILL)
        assert "76%" in text
        assert "advisory" in text.lower() or "do not rewrite" in text.lower()

    @pytest.mark.unit
    def test_hub_discloses_the_unclassified_share(self) -> None:
        """A clean run is weak evidence, and the skill must say so."""
        text = _read(SKILL)
        assert "61%" in text

    @pytest.mark.unit
    def test_hub_explains_what_a_medium_finding_means(self) -> None:
        """A checker that cannot settle a register must publish that."""
        text = _read(SKILL)
        assert "medium" in text
        assert "register" in text.lower()

    @pytest.mark.unit
    def test_hub_names_the_corpus_the_numbers_came_from(self) -> None:
        """Percentages without a denominator are not evidence."""
        assert "5984" in _read(SKILL)

    @pytest.mark.unit
    def test_hub_documents_the_runnable_entry_point(self) -> None:
        """A check reachable only by hand-written Python is not run twice."""
        text = _read(SKILL)
        assert "python -m scribe.ste" in text
        assert "--no-noun-clusters" in text

    @pytest.mark.unit
    def test_documented_snippets_use_python3_not_bare_python(self) -> None:
        """Bare `python` does not resolve in this environment."""
        for path in [SKILL, *MODULES.values()]:
            for line in _read(path).splitlines():
                assert not re.match(r"\s*python\s+\S", line), f"bare python in {path}"
