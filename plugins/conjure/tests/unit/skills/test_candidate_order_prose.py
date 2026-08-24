"""Rank claims written as prose must agree with the priority integers.

Four provider skills state where their provider sits in the candidate
order, in sentences like "ranks behind gemini, qwen and minimax in the
candidate order". That order is derived from one `priority` int per
service, so a one-line data change in `delegation_executor.SERVICES`
makes every one of those sentences wrong, and nothing noticed.

The claims were correct when this was written. That is the point: a
claim nothing checks is correct until the day it is not, and prose is
where a reader looks first.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[3] / "skills"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from delegation_executor import Delegator  # noqa: E402 - sys.path set above

ORDER = Delegator().candidate_order()
RANK = {name: i for i, name in enumerate(ORDER)}

#: A sentence naming providers this one ranks after.
BEHIND = re.compile(r"behind ([^.]*?) in the candidate order", re.IGNORECASE)

#: A sentence claiming this provider is last.
LAST = re.compile(r"last in the candidate order", re.IGNORECASE)


def _provider_of(skill: Path) -> str | None:
    """Return the service name a `<name>-delegation` skill speaks for."""
    name = skill.parent.name.removesuffix("-delegation")
    return name if name in RANK else None


def _skills_with_claims() -> list[tuple[Path, str]]:
    found = []
    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        provider = _provider_of(skill)
        if provider is None:
            continue
        text = skill.read_text(encoding="utf-8")
        if BEHIND.search(text) or LAST.search(text):
            found.append((skill, provider))
    return found


CLAIMANTS = _skills_with_claims()


def test_the_claims_are_still_being_found() -> None:
    """Guard the regex: a pattern matching nothing would pass everything."""
    assert len(CLAIMANTS) >= 4, (
        f"only {len(CLAIMANTS)} skill(s) found stating a candidate-order "
        "rank; the phrasing changed and this gate stopped reading them"
    )


@pytest.mark.parametrize(
    ("skill", "provider"), CLAIMANTS, ids=lambda v: getattr(v, "parent", v)
)
def test_a_rank_claim_matches_the_priority_order(skill: Path, provider: str) -> None:
    """Every provider a skill claims to rank behind must actually precede it."""
    text = skill.read_text(encoding="utf-8")

    for clause in BEHIND.findall(text):
        named = [name for name in RANK if re.search(rf"\b{name}\b", clause)]
        assert named, f"{skill.parent.name}: no known provider in {clause!r}"
        for ahead in named:
            assert RANK[ahead] < RANK[provider], (
                f"{skill.parent.name} says it ranks behind {ahead}, but the "
                f"candidate order is {ORDER}"
            )

    if LAST.search(text):
        assert RANK[provider] == len(ORDER) - 1, (
            f"{skill.parent.name} claims to be last; the candidate order "
            f"ends with {ORDER[-1]}"
        )
