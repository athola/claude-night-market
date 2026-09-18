"""The judge panel must count the judges it dispatched, not the survivors.

Feature: A dropped judge cannot change the verdict silently.

As the operator reading a panel verdict
I want the majority computed over the three lenses dispatched
So that one judge returning nothing leaves a visible hole rather than a
two-judge panel that reads as unanimous

Found in the 2026-09 workflow audit (ADR-0025): ``judged.filter(Boolean)``
set the denominator after dropping nulls, so two missing judges let a
single survivor return ``complete`` and the return value carried no sign
of it. Every other workflow under-reported on a dropped agent; this one
moved the verdict.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "workflows" / "judge-panel.js"


@pytest.fixture(scope="module")
def script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


class TestTheDenominatorIsTheRoster:
    """Scenario: the majority is computed over the lenses dispatched."""

    @pytest.mark.unit
    def test_majority_is_over_lenses_dispatched(self, script: str) -> None:
        """
        Given three lenses are dispatched
        Then the majority test divides by LENSES.length, not by the survivors
        """
        assert re.search(r"satisfied\.length\s*>\s*LENSES\.length\s*/\s*2", script)
        assert "verdicts.length / 2" not in script

    @pytest.mark.unit
    def test_missing_judges_are_returned_by_lens(self, script: str) -> None:
        """
        Given a judge returned nothing
        Then the return names its lens under ``missing``
        """
        assert re.search(
            r"const missing = LENSES\.filter\(\(lens, index\) => !judged\[index\]\)",
            script,
        )
        assert re.search(r"return \{[^}]*missing", script, re.S)

    @pytest.mark.unit
    def test_a_panel_with_a_missing_judge_cannot_be_complete(self, script: str) -> None:
        """
        Given a lens has no verdict
        Then the verdict is ``inconclusive`` rather than ``complete``

            A lens nobody judged is not a lens that passed.
        """
        assert "'inconclusive'" in script
        assert re.search(r"missing\.length\s*\?\s*'inconclusive'", script)
