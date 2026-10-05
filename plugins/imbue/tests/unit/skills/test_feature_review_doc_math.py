"""The feature-review scoring docs agree with their own arithmetic.

Math review findings C15, C16 and C17. The worked example printed 1.42
and labeled it Medium, which the module's own table puts in Low. SKILL.md
averaged factors equally while the framework module defines a weighted
average with documented default weights. The module also claimed a
logarithmic normalization that no formula or example applies.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "feature-review"
SKILL = (SKILL_DIR / "SKILL.md").read_text()
FRAMEWORK = (SKILL_DIR / "modules" / "scoring-framework.md").read_text()


def _example() -> str:
    start = FRAMEWORK.index("## Calculation Example")
    return FRAMEWORK[start : FRAMEWORK.index("## Interpreting Scores")]


def _factor(name: str) -> float:
    found = re.search(rf"^{name}: ([\d.]+)", _example(), re.M)
    assert found, name
    return float(found.group(1))


def _default_weights() -> dict[str, float]:
    block = FRAMEWORK[FRAMEWORK.index("## Custom Weights") :]
    return {
        key: float(value)
        for key, value in re.findall(r"^\s+(\w+): ([\d.]+)", block, re.M)[:7]
    }


def _band(score: float) -> str:
    rows = re.findall(r"^\| ([\d.]+) - ([\d.]+) \| (\w+) \|", FRAMEWORK, re.M)
    for low, high, label in rows:
        if float(low) <= score < float(high):
            return label
    raise AssertionError(f"no band for {score}")


@pytest.mark.unit
def test_the_worked_example_uses_the_default_weights() -> None:
    """C16: the example's value and cost are the weighted averages."""
    w = _default_weights()
    value = (
        _factor("Reach") * w["reach"]
        + _factor("Impact") * w["impact"]
        + _factor("Business Value") * w["business_value"]
        + _factor("Time Criticality") * w["time_criticality"]
    )
    cost = (
        _factor("Effort") * w["effort"]
        + _factor("Risk") * w["risk"]
        + _factor("Complexity") * w["complexity"]
    )

    printed_value = re.search(r"^Value Score = .* = ([\d.]+)$", _example(), re.M)
    printed_cost = re.search(r"^Cost Score = .* = ([\d.]+)$", _example(), re.M)
    assert printed_value and printed_cost

    assert float(printed_value.group(1)) == pytest.approx(value, abs=0.005)
    assert float(printed_cost.group(1)) == pytest.approx(cost, abs=0.005)


@pytest.mark.unit
def test_the_worked_example_priority_matches_the_band_table() -> None:
    """C15: the label is the band the printed score falls in."""
    score = re.search(r"^Feature Score = .* = ([\d.]+)$", _example(), re.M)
    label = re.search(r"^Priority: (\w+)", _example(), re.M)
    assert score and label

    assert label.group(1) == _band(float(score.group(1)))


@pytest.mark.unit
def test_skill_md_uses_the_weighted_definition() -> None:
    """C16: one definition of Value and Cost across the skill."""
    assert "Value Score = weighted_avg(" in SKILL
    assert "Cost Score = weighted_avg(" in SKILL
    assert "/ 4" not in SKILL


@pytest.mark.unit
def test_no_logarithmic_normalization_is_claimed() -> None:
    """C17: nothing in the formula or the example applies a log."""
    assert "logarithmic" not in FRAMEWORK.lower()
