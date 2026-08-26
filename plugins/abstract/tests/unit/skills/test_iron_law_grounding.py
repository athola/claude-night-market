"""The Iron Law has to say what a test is for, not only that one exists.

Review on PR #662: "we want to add tests and behavior directives not
simply for the sake of adding them ... we need to be grounded in
validating and ensuring adherence to business logic and invariants."

The module read as an unqualified "test first, always", which is the
reading that produces a suite where every changed line grew an
assertion. Every test is a claim about what must stay true, so a test
pinning something nobody required reports failure when nothing broke,
and the cost lands on whoever changes that code next.

These assertions anchor on the grounding section. Delete it and they
turn red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MODULE = Path(__file__).parents[3] / "shared-modules" / "iron-law-enforcement.md"


@pytest.fixture
def content() -> str:
    """Whitespace-collapsed, so an assertion cannot straddle an 80-col wrap.

    Asserting on the literal text would pin the line breaking rather than
    the claim, which is the implementation-detail failure mode the section
    under test warns about.
    """
    return " ".join(MODULE.read_text().split())


@pytest.mark.bdd
def test_module_names_the_constraint_a_red_test_must_protect(content: str) -> None:
    """Scenario: the author is asked what the test protects before writing it.

    Given the Iron Law module
    When an author reaches the RED phase
    Then the module asks which constraint the test defends.
    """
    assert "What the Failing Test Has to Protect" in content
    for constraint in ("business rule", "invariant", "contract at a boundary"):
        assert constraint in content, f"missing constraint category: {constraint}"


@pytest.mark.bdd
def test_module_permits_a_reasoned_no_test_answer(content: str) -> None:
    """Scenario: no constraint fits, and saying so is a valid outcome.

    Given a change that defends no business rule, invariant or contract
    When the author works through the grounding table
    Then the module accepts "this needs no test first" with a reason.
    """
    assert "does not need a test first" in content


@pytest.mark.bdd
def test_module_states_the_cost_of_a_wrong_constraint_test(content: str) -> None:
    """Scenario: a test pinning the wrong thing is a liability, not neutral.

    Given a test that asserts an implementation detail
    When the implementation legitimately changes
    Then the module says the test reports failure though nothing broke.
    """
    assert "reports failure when nothing broke" in content
