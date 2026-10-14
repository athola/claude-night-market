"""Mode selection compares the reversibility score without float error.

Executed literally in floats, the documented
``RS <= profile.express_ceiling`` with the cautious express ceiling 0.30
and the do-issue adjustment -0.10 compares 0.2 <= 0.19999999999999998,
so an all-1s decision (RS = 5/25 = 0.2) escalated instead of going
express. Every table value has two decimals, so hundredths are exact.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

SKILL = (
    Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"
).read_text()


def _hundredths(text: str) -> int:
    return round(Fraction(text) * 100)


def _profiles() -> list[list[str]]:
    return re.findall(r"^\| \w+ \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|", SKILL, re.M)


def _adjustments() -> list[str]:
    return ["0", *re.findall(r"^\| [^|]+ \| (-[\d.]+) \|", SKILL, re.M)]


@pytest.mark.unit
def test_the_documented_comparison_is_in_integer_hundredths() -> None:
    """The pseudo-code compares 4 * Sum against a ceiling in hundredths."""
    assert "RS <= profile." not in SKILL
    assert "rs_pct = 4 * score_sum" in SKILL
    assert "rs_pct <= ceiling_pct(profile.express, adjustment)" in SKILL


@pytest.mark.unit
def test_hundredths_agree_with_exact_arithmetic_on_every_table_value() -> None:
    """4 * Sum <= ceiling hundredths is RS <= ceiling, for every row."""
    profiles = _profiles()
    assert profiles and len(_adjustments()) > 1
    for row in profiles:
        for ceiling in row:
            for adjustment in _adjustments():
                exact = Fraction(ceiling) + Fraction(adjustment)
                pct = _hundredths(ceiling) + _hundredths(adjustment)
                for score_sum in range(5, 26):
                    assert (4 * score_sum <= pct) == (Fraction(score_sum, 25) <= exact)


def _mode_block() -> str:
    section = SKILL.split("### Step 3: Mode Selection", 1)[1]
    return re.search(r"```\n(.*?)```", section, re.S).group(1)


@pytest.mark.unit
@pytest.mark.parametrize(
    "score_sum,adjustment,expected",
    [(5, -0.10, "express"), (5, 0, "express"), (13, 0, "full_council")],
)
def test_the_mode_pseudocode_runs_as_written(
    score_sum: int, adjustment: float, expected: str
) -> None:
    """Every name the block reads is an input it states; none is undefined.

    Run against the cautious profile, an all-1s decision under the
    do-issue adjustment stays express.
    """
    cautious = SimpleNamespace(express=0.30, lightweight=0.50, full_council=0.70)
    scope = {
        "score_sum": score_sum,
        "profile": cautious,
        "command_adjustment": adjustment,
    }

    exec(_mode_block(), scope)  # noqa: S102 - runs the skill's own pseudocode  # nosec B102 - same reason

    assert scope["mode"] == expected
