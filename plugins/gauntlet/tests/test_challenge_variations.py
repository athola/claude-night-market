"""Tests for Claude-backed problem variation generation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from anthropic.types import TextBlock
from gauntlet.challenges import (
    _generate_problem_variation,
    _is_valid_variation,
    generate_bank_challenge,
)
from gauntlet.models import BankProblem, Difficulty

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_PROMPT = "Given an array, return the maximum value."


def _make_problem(prompt: str = _DEFAULT_PROMPT) -> BankProblem:
    """Create a minimal BankProblem fixture for use in tests."""
    return BankProblem(
        id="test-001",
        title="Test Problem",
        category="arrays-and-hashing",
        difficulty=Difficulty.EASY,
        prompt=prompt,
        hints=["Use a loop"],
        solution_outline="Iterate once, track max.",
        tags=["arrays"],
    )


def _make_anthropic_response(text: str) -> MagicMock:
    """Build a mock anthropic Messages response with a real TextBlock."""
    response = MagicMock()
    response.content = [TextBlock(type="text", text=text)]
    return response


# ---------------------------------------------------------------------------
# _is_valid_variation
# ---------------------------------------------------------------------------


class TestIsValidVariation:
    """Unit tests for the _is_valid_variation predicate."""

    def test_empty_string_is_invalid(self):
        assert _is_valid_variation("") is False

    def test_short_string_is_invalid(self):
        assert _is_valid_variation("short") is False

    def test_nineteen_chars_is_invalid(self):
        # Boundary: exactly 19 chars, no imperative verb or "?"
        assert _is_valid_variation("a" * 19) is False

    def test_question_mark_makes_valid(self):
        assert _is_valid_variation("What is the correct answer here?") is True

    def test_return_keyword_makes_valid(self):
        assert _is_valid_variation("Given an array, return the maximum value.") is True

    def test_write_keyword_makes_valid(self):
        assert _is_valid_variation("Write a function that sums a list.") is True

    def test_implement_keyword_makes_valid(self):
        assert _is_valid_variation("Implement a stack using two queues.") is True

    def test_given_keyword_makes_valid(self):
        assert _is_valid_variation("Given a binary tree, find the depth.") is True

    def test_find_keyword_makes_valid(self):
        assert _is_valid_variation("Find all pairs that sum to target k.") is True

    def test_design_keyword_makes_valid(self):
        assert _is_valid_variation("Design a rate limiter for an API endpoint.") is True

    def test_no_keywords_no_question_is_invalid(self):
        # Long enough but no imperative verb and no "?"
        text = "A" * 30
        assert _is_valid_variation(text) is False

    def test_leading_trailing_whitespace_handled(self):
        assert _is_valid_variation("  Given a list, return the sum.  ") is True


# ---------------------------------------------------------------------------
# _generate_problem_variation
# ---------------------------------------------------------------------------


class TestGenerateProblemVariation:
    """Unit tests for _generate_problem_variation with a mocked Anthropic client."""

    def test_returns_varied_problem_on_success(self):
        problem = _make_problem()
        varied_text = "Given a sequence of integers, return the largest element."

        mock_response = _make_anthropic_response(varied_text)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            result = _generate_problem_variation(problem)

        assert result.prompt == varied_text
        assert result.id == problem.id
        assert result.difficulty == problem.difficulty
        assert result.title == problem.title
        assert result.hints == problem.hints
        assert result.solution_outline == problem.solution_outline

    def test_calls_correct_model(self):
        problem = _make_problem()
        varied_text = "Given a list, return the maximum element."

        mock_response = _make_anthropic_response(varied_text)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            _generate_problem_variation(problem)

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"

    def test_falls_back_on_api_exception(self):
        problem = _make_problem()

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = RuntimeError("network error")

            result = _generate_problem_variation(problem)

        assert result is problem

    def test_falls_back_on_anthropic_api_error(self):
        problem = _make_problem()

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("APIStatusError")

            result = _generate_problem_variation(problem)

        assert result is problem

    def test_falls_back_when_response_is_not_text_block(self):
        problem = _make_problem()
        # A MagicMock content block does not pass isinstance(_, TextBlock)
        non_text_block = MagicMock()
        response = MagicMock()
        response.content = [non_text_block]

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = response

            result = _generate_problem_variation(problem)

        assert result is problem

    def test_falls_back_when_validation_fails(self):
        problem = _make_problem()
        # Response that fails validation (too short, no imperative verb, no "?")
        invalid_text = "nope"

        mock_response = _make_anthropic_response(invalid_text)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            result = _generate_problem_variation(problem)

        assert result is problem

    def test_strips_whitespace_from_variation(self):
        problem = _make_problem()
        varied_text = "  Given a sorted array, return the index of target.  "

        mock_response = _make_anthropic_response(varied_text)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            result = _generate_problem_variation(problem)

        assert result.prompt == varied_text.strip()

    def test_prompt_includes_original_problem(self):
        problem = _make_problem("Given an array, return the maximum value.")
        varied_text = "Given a list of numbers, find the largest."

        mock_response = _make_anthropic_response(varied_text)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            _generate_problem_variation(problem)

        messages = mock_client.messages.create.call_args.kwargs["messages"]
        assert problem.prompt in messages[0]["content"]


# ---------------------------------------------------------------------------
# generate_bank_challenge (integration with variation)
# ---------------------------------------------------------------------------


class TestGenerateBankChallenge:
    """Integration tests for generate_bank_challenge with variation logic."""

    def test_returns_challenge_with_varied_prompt(self):
        problem = _make_problem()
        varied_text = "Given a list, implement a function to find the max element."

        mock_response = _make_anthropic_response(varied_text)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            challenge = generate_bank_challenge(problem)

        assert challenge.prompt == varied_text

    def test_returns_challenge_with_original_prompt_on_failure(self):
        problem = _make_problem()

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("timeout")

            challenge = generate_bank_challenge(problem)

        assert challenge.prompt == problem.prompt
