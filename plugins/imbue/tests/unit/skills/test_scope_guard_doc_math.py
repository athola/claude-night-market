"""The scope-guard bands have one answer per score and examples on scale.

Math review findings C24 and C25. Integer Fibonacci sums land on the band
edges often (all factors 3 gives exactly 1.0), and the plan check
"Worthiness > 1.0" rejected a 1.0 the bands call Discuss. The baseline
scenario scored factors 0, below the scale's minimum of 1.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "scope-guard"
SKILL = (SKILL_DIR / "SKILL.md").read_text()
FRAMEWORK = (SKILL_DIR / "modules" / "decision-framework.md").read_text()
BASELINE = (SKILL_DIR / "modules" / "baseline-scenarios.md").read_text()
FIBONACCI = {1, 2, 3, 5, 8, 13}


@pytest.mark.unit
@pytest.mark.parametrize("text", [SKILL, FRAMEWORK], ids=["SKILL", "framework"])
def test_the_discuss_band_states_that_both_edges_are_inclusive(text: str) -> None:
    """C24: 1.0 and 2.0 each belong to exactly one band, Discuss."""
    assert "1.0 - 2.0 (inclusive)" in text
    assert "> 2.0" in text
    assert "< 1.0" in text


@pytest.mark.unit
def test_the_plan_check_admits_the_discuss_band() -> None:
    """C24: verification rejects only the Defer band."""
    assert "Worthiness > 1.0" not in SKILL
    assert "Worthiness >= 1.0" in SKILL


@pytest.mark.unit
def test_baseline_factor_scores_are_on_the_fibonacci_scale() -> None:
    """C25: every factor score in the worked scenario is 1, 2, 3, 5, 8 or 13."""
    scores = re.findall(
        r"(?:Business Value|Time Criticality|Risk Reduction|Complexity|"
        r"Token Cost|Scope Drift): (\d+)(?:-(\d+))?",
        BASELINE,
    )
    assert scores
    for low, high in scores:
        assert int(low) in FIBONACCI
        if high:
            assert int(high) in FIBONACCI


@pytest.mark.unit
def test_baseline_worthiness_follows_from_its_factors() -> None:
    """C25: the printed range is numerator 3-4 over denominator 8-10."""
    assert "Worthiness = 0.3-0.5" in BASELINE
