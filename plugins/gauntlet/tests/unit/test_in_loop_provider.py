"""Tests for the in-loop variation provider.

Issue #464: when gauntlet runs inside Claude Code, the default
``anthropic_variation_provider`` makes a wasteful API roundtrip to
spawn a sibling Claude. This test pins the in-loop alternative.

Feature: in_loop_variation_provider produces deterministic problem
variations without calling the Anthropic SDK.
"""

from __future__ import annotations

from gauntlet.models import BankProblem, Difficulty
from gauntlet.providers.in_loop import (
    in_loop_variation_provider,
    is_running_in_claude_code,
)


def _sample_problem() -> BankProblem:
    return BankProblem(
        id="two-sum",
        title="Two Sum",
        category="hashmap",
        difficulty=Difficulty.EASY,
        prompt=(
            "Given an array of 5 integers and a target value 9, return "
            "the indices of the two numbers that add up to the target."
        ),
        hints=["use a hash map"],
        tags=["array", "hashmap"],
    )


class TestInLoopProvider:
    """Feature: the provider varies seed prompts without an SDK call."""

    def test_provider_returns_string(self) -> None:
        """Scenario: provider returns a string for any seed problem.

        Given the in-loop provider and a seed problem
        When I invoke the provider
        Then it returns a string (or None if no variation possible).
        """
        result = in_loop_variation_provider("ignored", _sample_problem())
        assert result is None or isinstance(result, str)

    def test_provider_makes_no_anthropic_calls(self, monkeypatch) -> None:
        """Scenario: provider does not import anthropic.

        Given the in-loop provider
        When invoked
        Then no anthropic.Anthropic client is constructed.
        """
        called = {"count": 0}

        def fake_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "anthropic":
                called["count"] += 1
            import importlib

            return importlib.__import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", fake_import)
        in_loop_variation_provider("ignored", _sample_problem())
        assert called["count"] == 0

    def test_variation_is_deterministic(self) -> None:
        """Scenario: same input produces the same output.

        Given identical inputs
        When the provider runs twice
        Then it returns the same string both times.
        """
        problem = _sample_problem()
        first = in_loop_variation_provider("template", problem)
        second = in_loop_variation_provider("template", problem)
        assert first == second

    def test_variation_differs_from_seed(self) -> None:
        """Scenario: the variation is not byte-equal to the seed.

        Given a seed prompt with an integer
        When the provider returns a variation
        Then the variation differs from the seed.
        """
        problem = _sample_problem()
        variation = in_loop_variation_provider("template", problem)
        assert variation is not None
        assert variation.strip() != problem.prompt.strip()

    def test_returns_none_when_no_variation_possible(self) -> None:
        """Scenario: prompt with no integers cannot be varied locally.

        Given a seed prompt with no integers and no varyable identifiers
        When the provider runs
        Then it returns None to signal fallback to seed.
        """
        problem = BankProblem(
            id="empty",
            title="Empty",
            category="other",
            difficulty=Difficulty.EASY,
            prompt="reverse the linked list",
            hints=[],
            tags=[],
        )
        result = in_loop_variation_provider("template", problem)
        assert result is None


class TestRunningInClaudeCode:
    """Feature: detect whether the runtime is inside Claude Code."""

    def test_returns_true_when_plugin_root_set(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", "/some/path")
        assert is_running_in_claude_code() is True

    def test_returns_false_when_env_unset(self, monkeypatch) -> None:
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
        monkeypatch.delenv("CLAUDECODE", raising=False)
        assert is_running_in_claude_code() is False


class TestAutoRegistration:
    """Feature: switch active provider when running inside Claude Code."""

    def test_register_outside_claude_code_returns_false(self, monkeypatch) -> None:
        """Scenario: outside Claude Code the registration is a no-op.

        Given CLAUDE_PLUGIN_ROOT and CLAUDECODE are unset
        When register_in_loop_provider_if_inside_claude_code runs
        Then it returns False and leaves the active provider alone.
        """
        from gauntlet.providers.in_loop import (
            register_in_loop_provider_if_inside_claude_code,
        )

        from gauntlet import challenges

        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
        monkeypatch.delenv("CLAUDECODE", raising=False)
        previous = challenges.get_variation_provider()
        result = register_in_loop_provider_if_inside_claude_code()
        try:
            assert result is False
            assert challenges.get_variation_provider() is previous
        finally:
            challenges.set_variation_provider(previous)

    def test_register_inside_claude_code_switches_provider(self, monkeypatch) -> None:
        """Scenario: inside Claude Code the in-loop provider becomes active.

        Given CLAUDE_PLUGIN_ROOT is set and the default Anthropic provider
        When register_in_loop_provider_if_inside_claude_code runs
        Then the active provider is in_loop_variation_provider.
        """
        from gauntlet.providers.in_loop import (
            register_in_loop_provider_if_inside_claude_code,
        )

        from gauntlet import challenges

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", "/tmp/gauntlet-test")
        previous = challenges.get_variation_provider()
        challenges.set_variation_provider(challenges.anthropic_variation_provider)
        try:
            result = register_in_loop_provider_if_inside_claude_code()
            assert result is True
            assert challenges.get_variation_provider() is in_loop_variation_provider
        finally:
            challenges.set_variation_provider(previous)

    def test_explicit_custom_provider_is_preserved(self, monkeypatch) -> None:
        """Scenario: a caller-set custom provider is respected.

        Given CLAUDE_PLUGIN_ROOT is set and a custom provider is active
        When register_in_loop_provider_if_inside_claude_code() runs
        Then it returns False and leaves the custom provider in place.
        """
        from gauntlet.providers.in_loop import (
            register_in_loop_provider_if_inside_claude_code,
        )

        from gauntlet import challenges

        def custom(_template: str, _problem) -> str:  # noqa: ANN001 - test stub matches VariationProvider Callable typing
            return "custom"

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", "/tmp/gauntlet-test")
        previous = challenges.get_variation_provider()
        challenges.set_variation_provider(custom)
        try:
            result = register_in_loop_provider_if_inside_claude_code()
            assert result is False
            assert challenges.get_variation_provider() is custom
        finally:
            challenges.set_variation_provider(previous)

    def test_force_swap_overrides_custom_provider(self, monkeypatch) -> None:
        """Scenario: force=True swaps even when a custom provider is active.

        Given CLAUDE_PLUGIN_ROOT is set and a custom provider is active
        When register_in_loop_provider_if_inside_claude_code(force=True) runs
        Then the custom provider is replaced with in-loop.
        """
        from gauntlet.providers.in_loop import (
            register_in_loop_provider_if_inside_claude_code,
        )

        from gauntlet import challenges

        def custom(_template: str, _problem) -> str:  # noqa: ANN001 - test stub matches VariationProvider Callable typing
            return "custom"

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", "/tmp/gauntlet-test")
        previous = challenges.get_variation_provider()
        challenges.set_variation_provider(custom)
        try:
            result = register_in_loop_provider_if_inside_claude_code(force=True)
            assert result is True
            assert challenges.get_variation_provider() is in_loop_variation_provider
        finally:
            challenges.set_variation_provider(previous)
