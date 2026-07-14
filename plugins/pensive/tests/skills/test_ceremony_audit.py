"""Test: the ceremony audit module documents its signals and its limits.

The ceremony audit is a manual reading lens for mapping layers that do not
diverge: passthrough mappers, twin types, speculative DTOs, and interfaces
with one implementation. It is not an AST detector, so the detector-test
rule in architecture-review does not apply to it. That claim has to be
visible in the module itself, following the precedent set by
performance-review/modules/memory-allocation-lenses.md.

The counter-signal matters as much as the signals. An audit that flags IO
boundary mappers would delete the one mapper that is load-bearing.

Feature: ceremony-audit documents four signals, a counter-signal, and its
own scope.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
ARCH_REVIEW = PLUGIN_ROOT / "skills" / "architecture-review"
CEREMONY_MODULE = ARCH_REVIEW / "modules" / "ceremony-audit.md"
ARCH_REVIEW_SKILL = ARCH_REVIEW / "SKILL.md"


def _normalize(text: str) -> str:
    """Collapse whitespace runs so anchors survive an 80-column reflow.

    The repo wraps prose at 80 characters, so any anchor phrase long enough
    to be meaningful will eventually straddle a line break. Matching raw
    text would make these tests fail on a pure reflow, and would tempt an
    author to "fix" a red test by unwrapping a line.

    Collapsing whitespace keeps the property that matters: deleting the
    guarded paragraph still turns the test red. It only drops the
    dependency on where the line breaks happen to fall.
    """
    return re.sub(r"\s+", " ", text)


@pytest.fixture
def module_text() -> str:
    """The ceremony-audit module body, whitespace-normalized."""
    assert CEREMONY_MODULE.exists(), f"missing module: {CEREMONY_MODULE}"
    return _normalize(CEREMONY_MODULE.read_text(encoding="utf-8"))


class TestCeremonySignals:
    """Feature: all four ceremony signals carry detection and verdict."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_passthrough_mapper_signal(self, module_text: str) -> None:
        """
        Scenario: a mapper copies every field 1:1
        Given the ceremony audit module
        When the signal table is read
        Then the passthrough mapper is detectable and its verdict is delete.
        """
        assert "Passthrough mapper" in module_text
        assert "1:1 copy" in module_text, (
            "passthrough mapper must be detected by its 1:1 field copies"
        )
        assert "share the type" in module_text, (
            "passthrough mapper verdict must be to delete and share the type"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_twin_types_signal(self, module_text: str) -> None:
        """
        Scenario: two layers hold structurally identical types
        Given the ceremony audit module
        When the signal table is read
        Then twin types collapse to one until they diverge.
        """
        assert "Twin types" in module_text
        assert "structurally identical" in module_text, (
            "twin types must be detected by structural identity"
        )
        assert "until they diverge" in module_text, (
            "twin types verdict must be to collapse until divergence"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_speculative_dto_signal(self, module_text: str) -> None:
        """
        Scenario: a DTO mirrors its entity and no contract pins its shape
        Given the ceremony audit module
        When the signal table is read
        Then the speculative DTO is deleted and reintroduced on divergence.
        """
        assert "Speculative DTO" in module_text
        assert "no external contract" in module_text, (
            "speculative DTO must be detected by the absence of a contract"
        )
        assert "reintroduce on divergence" in module_text, (
            "speculative DTO verdict must defer the DTO to divergence"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_single_implementation_interface_signal(self, module_text: str) -> None:
        """
        Scenario: an interface has exactly one implementation
        Given the ceremony audit module
        When the signal table is read
        Then it is inlined, citing Karpathy AP-3.
        """
        assert "one implementation" in module_text.lower()
        assert "no test double" in module_text, (
            "single-impl interface must be detected by the absence of a double"
        )
        assert "AP-3" in module_text, (
            "single-impl interface verdict must cite Karpathy AP-3"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_every_finding_must_name_the_need(self, module_text: str) -> None:
        """
        Scenario: an auditor flags ceremony without saying what it would serve
        Given the ceremony audit module
        When the reporting rule is read
        Then each finding must name the need the ceremony would serve.
        """
        assert "the ceremony is the finding" in module_text, (
            "audit must require naming the need, else the ceremony is a finding"
        )


class TestCounterSignal:
    """Feature: the audit does not delete load-bearing boundary mappers."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_io_boundary_mapper_is_never_flagged(self, module_text: str) -> None:
        """
        Scenario: an IO boundary mapper looks like a passthrough today
        Given the ceremony audit module
        When the counter-signal is read
        Then the audit is told not to flag it, because its job is to stop
        future internal fields from escaping.

        Without this the audit over-corrects and deletes the one mapper that
        earns its keep. Mirrors the anti-goals discipline in slop-detector.
        """
        assert "Counter-signal" in module_text, (
            "module must carry an explicit counter-signal section"
        )
        assert "load-bearing even when it looks like a passthrough" in (module_text), (
            "counter-signal must protect the IO boundary mapper from the audit"
        )
        assert "must not flag it" in module_text, (
            "counter-signal must instruct the audit not to flag boundary mappers"
        )


class TestModuleScope:
    """Feature: the module declares itself a manual lens, not a detector."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_declares_itself_a_manual_lens(self, module_text: str) -> None:
        """
        Scenario: a maintainer looks for the AST detector behind the audit
        Given the ceremony audit module
        When the scope note is read
        Then the module states it is a manual lens with no AST detector.

        The phrase is asserted verbatim rather than by keyword, because a
        loose keyword check ('manual' anywhere in the file) is exactly the
        weak assertion PR #612 caught passing its revert test by accident.
        """
        assert "manual review lens" in module_text, (
            "module must declare itself a manual review lens"
        )
        assert "not an AST detector" in module_text, (
            "module must state no AST detector backs it"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_architecture_review_loads_the_module(self) -> None:
        """
        Scenario: the ceremony audit exists but nothing invokes it
        Given the architecture-review SKILL.md
        When the progressive loading list is read
        Then ceremony-audit.md is registered so the workflow can load it.
        """
        skill_text = _normalize(ARCH_REVIEW_SKILL.read_text(encoding="utf-8"))

        assert "modules/ceremony-audit.md" in skill_text, (
            "architecture-review must register modules/ceremony-audit.md, "
            "otherwise the module is unreachable from the workflow"
        )
