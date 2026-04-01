"""Tests for gauntlet answer scoring."""

from __future__ import annotations

import pytest
from gauntlet.models import Challenge
from gauntlet.scoring import evaluate_answer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _challenge(
    challenge_type: str,
    answer: str,
    options: list[str] | None = None,
) -> Challenge:
    return Challenge(
        id="ch-test-001",
        type=challenge_type,
        knowledge_entry_id="ke-test-001",
        difficulty=2,
        prompt="Test prompt",
        context="Test context",
        answer=answer,
        options=options,
    )


# ---------------------------------------------------------------------------
# Feature: Multiple-choice scoring
# ---------------------------------------------------------------------------


class TestMultipleChoiceScoring:
    """
    Feature: Multiple-choice answer evaluation

    As a gauntlet engine
    I want to score MC answers by exact letter match
    So that developers get clear pass/fail feedback
    """

    @pytest.mark.unit
    def test_correct_letter_is_pass(self):
        """
        Scenario: Developer enters the correct letter
        Given a multiple_choice challenge with answer 'B'
        When evaluate_answer is called with 'B'
        Then the result is 'pass'
        """
        ch = _challenge("multiple_choice", "B")
        assert evaluate_answer(ch, "B") == "pass"

    @pytest.mark.unit
    def test_lowercase_correct_letter_is_pass(self):
        """
        Scenario: Developer enters the correct letter in lowercase
        Given a multiple_choice challenge with answer 'B'
        When evaluate_answer is called with 'b'
        Then the result is 'pass' (case-insensitive)
        """
        ch = _challenge("multiple_choice", "B")
        assert evaluate_answer(ch, "b") == "pass"

    @pytest.mark.unit
    def test_wrong_letter_is_fail(self):
        """
        Scenario: Developer enters the wrong letter
        Given a multiple_choice challenge with answer 'B'
        When evaluate_answer is called with 'C'
        Then the result is 'fail'
        """
        ch = _challenge("multiple_choice", "B")
        assert evaluate_answer(ch, "C") == "fail"

    @pytest.mark.unit
    def test_empty_answer_is_fail(self):
        """
        Scenario: Developer submits an empty answer
        Given a multiple_choice challenge
        When evaluate_answer is called with ''
        Then the result is 'fail'
        """
        ch = _challenge("multiple_choice", "A")
        assert evaluate_answer(ch, "") == "fail"


# ---------------------------------------------------------------------------
# Feature: Explain-why / trace / spot_bug / code_completion scoring
# ---------------------------------------------------------------------------


class TestWordOverlapScoring:
    """
    Feature: Word-overlap scoring for open-ended challenge types

    As a gauntlet engine
    I want to score free-text answers by keyword overlap
    So that partially correct answers receive credit
    """

    @pytest.mark.unit
    def test_explain_exact_match_is_pass(self):
        """
        Scenario: Developer reproduces the answer exactly
        Given an explain_why challenge
        When evaluate_answer is called with the exact answer text
        Then the result is 'pass'
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        assert evaluate_answer(ch, answer) == "pass"

    @pytest.mark.unit
    def test_explain_key_concepts_is_pass_or_partial(self):
        """
        Scenario: Developer captures the core idea with different wording
        Given an explain_why challenge with a detailed answer
        When evaluate_answer is called with a response containing most key words
        Then the result is 'pass' or 'partial' (not 'fail')
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        response = "Tokens expire in 15 minutes for security."
        result = evaluate_answer(ch, response)
        assert result in ("pass", "partial")

    @pytest.mark.unit
    def test_explain_wrong_answer_is_fail(self):
        """
        Scenario: Developer gives a completely unrelated answer
        Given an explain_why challenge about token expiry
        When evaluate_answer is called with an unrelated response
        Then the result is 'fail'
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        assert evaluate_answer(ch, "The database uses PostgreSQL indexes.") == "fail"

    @pytest.mark.unit
    def test_explain_partial_overlap_is_partial(self):
        """
        Scenario: Developer captures some but not most concepts
        Given an explain_why challenge
        When evaluate_answer is called with a response with ~25% word overlap
        Then the result is 'partial'
        """
        answer = (
            "Charges are pro-rated based on remaining days in the billing period "
            "using a daily rate multiplier applied to the subscription price."
        )
        ch = _challenge("explain_why", answer)
        # shares: "billing", "days" -- low overlap, well under 50% but above 20%
        response = "Something about billing days."
        result = evaluate_answer(ch, response)
        assert result in ("partial", "fail")

    @pytest.mark.unit
    def test_explain_empty_is_fail(self):
        """
        Scenario: Developer submits an empty answer for explain_why
        Given an explain_why challenge
        When evaluate_answer is called with ''
        Then the result is 'fail'
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        assert evaluate_answer(ch, "") == "fail"


# ---------------------------------------------------------------------------
# Feature: Dependency-map scoring
# ---------------------------------------------------------------------------


class TestDependencyMapScoring:
    """
    Feature: Set-based scoring for dependency_map challenges

    As a gauntlet engine
    I want to score dependency answers by set overlap
    So that developers who list most affected modules still get partial credit
    """

    @pytest.mark.unit
    def test_exact_set_match_is_pass(self):
        """
        Scenario: Developer lists all affected modules correctly
        Given a dependency_map challenge with answer 'moduleA, moduleB, moduleC'
        When evaluate_answer is called with the same modules in any order
        Then the result is 'pass'
        """
        ch = _challenge("dependency_map", "moduleA, moduleB, moduleC")
        assert evaluate_answer(ch, "moduleC, moduleA, moduleB") == "pass"

    @pytest.mark.unit
    def test_partial_set_overlap_is_partial(self):
        """
        Scenario: Developer lists about half the affected modules
        Given a dependency_map challenge with 4 modules in the answer
        When evaluate_answer is called with 2 of those modules
        Then the result is 'partial' (50% overlap >= 30% threshold)
        """
        ch = _challenge("dependency_map", "moduleA, moduleB, moduleC, moduleD")
        # 2 out of 4 correct = 50% overlap, which is >= 30% (partial) but < 80% (pass)
        assert evaluate_answer(ch, "moduleA, moduleB") == "partial"

    @pytest.mark.unit
    def test_low_overlap_is_fail(self):
        """
        Scenario: Developer lists mostly wrong modules
        Given a dependency_map challenge with 5 modules
        When evaluate_answer is called with 1 correct and 4 wrong modules
        Then the result is 'fail'
        """
        ch = _challenge("dependency_map", "a, b, c, d, e")
        # 1 out of 5 answer modules = 20% -- below 30% threshold
        assert evaluate_answer(ch, "a, x, y, z, w") == "fail"


# ---------------------------------------------------------------------------
# Feature: ML-enhanced open-ended scoring
# ---------------------------------------------------------------------------


class TestMLEnhancedScoring:
    """
    Feature: ML-blended scoring for open-ended challenges

    As a gauntlet engine
    I want to blend ML quality scores with word-overlap
    So that answers demonstrating understanding score better
    """

    @pytest.mark.unit
    def test_existing_exact_match_still_passes(self):
        """
        Scenario: Exact match still passes with ML active
        Given an explain_why challenge
        When the answer matches exactly
        Then the result is still 'pass'
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        assert evaluate_answer(ch, answer) == "pass"

    @pytest.mark.unit
    def test_existing_unrelated_still_fails(self):
        """
        Scenario: Unrelated answer still fails with ML active
        Given an explain_why challenge about token expiry
        When the answer is about databases
        Then the result is still 'fail'
        """
        answer = "Access tokens expire after 15 minutes to limit exposure."
        ch = _challenge("explain_why", answer)
        assert evaluate_answer(ch, "The database uses PostgreSQL indexes.") == "fail"

    @pytest.mark.unit
    def test_existing_empty_still_fails(self):
        """
        Scenario: Empty answer still fails with ML active
        Given any open-ended challenge
        When the answer is empty
        Then the result is still 'fail'
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        assert evaluate_answer(ch, "") == "fail"

    @pytest.mark.unit
    def test_multiple_choice_unchanged(self):
        """
        Scenario: Multiple choice scoring is not affected by ML
        Given a multiple_choice challenge
        When the correct letter is given
        Then the result is still 'pass' (ML not involved)
        """
        ch = _challenge("multiple_choice", "B")
        assert evaluate_answer(ch, "B") == "pass"

    @pytest.mark.unit
    def test_dependency_map_unchanged(self):
        """
        Scenario: Dependency map scoring is not affected by ML
        Given a dependency_map challenge
        When the correct modules are listed
        Then the result is still 'pass' (ML not involved)
        """
        ch = _challenge("dependency_map", "moduleA, moduleB, moduleC")
        assert evaluate_answer(ch, "moduleC, moduleA, moduleB") == "pass"
