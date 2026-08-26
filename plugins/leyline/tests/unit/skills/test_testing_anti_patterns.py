"""The anti-pattern catalog covers tests that should not exist at all.

Review on PR #662 asked that test guidance be grounded in business
logic and invariants rather than treating any added test as a gain.
The catalog covered how a test is written (implementation details,
over-mocking, missing assertions) and said nothing about whether the
constraint it pins was ever required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MODULE = (
    Path(__file__).parents[3]
    / "skills"
    / "testing-quality-standards"
    / "modules"
    / "anti-patterns.md"
)


@pytest.fixture
def content() -> str:
    """Whitespace-collapsed so assertions do not pin the line wrapping."""
    return " ".join(MODULE.read_text().split())


def test_catalog_covers_tests_that_pin_an_unrequired_constraint(
    content: str,
) -> None:
    """A frozen convenience default is named as an anti-pattern."""
    assert "Assertions on a Constraint Nobody Requires" in content
    assert "reports failure when nothing broke" in content


def test_catalog_gives_a_check_that_separates_rule_from_decision(
    content: str,
) -> None:
    """The domain-language check is stated, not just asserted to exist."""
    assert "naming no function and no file" in content
