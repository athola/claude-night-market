"""The utility skill's stated range follows from its component bounds.

Math review finding C27: SKILL.md states ``Utility range: [-2.3, 1.0]``,
which is ``0 - λ1·1 - λ2·1 - λ3·1`` and so assumes every subtracted term
lies in [0, 1]. Gain, Uncertainty and Redundancy declare that bound;
StepCost did not, and its dispatch overhead (+0.3) and an unbounded
token_ratio pushed it past 1, putting the floor at -2.6 or lower.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "utility"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES = SKILL_DIR / "modules"


def _lambda_defaults(skill_text: str) -> list[float]:
    return [
        float(v) for v in re.findall(r"^\| λ[₁₂₃] \| ([\d.]+) \|", skill_text, re.M)
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("module", "name"),
    [
        ("gain.md", "Gain"),
        ("uncertainty.md", "Uncertainty"),
        ("step-cost.md", "StepCost"),
    ],
)
def test_each_utility_term_declares_the_unit_interval(module: str, name: str) -> None:
    """Each term the range is computed from is bounded to [0, 1]."""
    text = (MODULES / module).read_text()

    assert f"`{name}(a | s_t) -> [0, 1]`" in text


@pytest.mark.unit
def test_stated_utility_floor_is_the_sum_of_the_weighted_maxima() -> None:
    """The floor equals -(λ1 + λ2 + λ3) when every term is at most 1."""
    text = SKILL_FILE.read_text()
    lambdas = _lambda_defaults(text)
    stated = re.search(r"Utility range: \*\*\[(-?[\d.]+), ([\d.]+)\]\*\*", text)

    assert len(lambdas) == 3
    assert stated is not None
    assert float(stated.group(1)) == pytest.approx(-sum(lambdas))
    assert float(stated.group(2)) == pytest.approx(1.0)
