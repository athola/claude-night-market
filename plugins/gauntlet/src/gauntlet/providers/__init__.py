"""Variation providers for gauntlet challenge generation.

Each provider conforms to ``gauntlet.challenges.VariationProvider``:
``Callable[[str, BankProblem], str | None]``. Returning ``None``
signals graceful fallback to the seed problem.
"""

from gauntlet.providers.in_loop import (
    in_loop_variation_provider,
    is_running_in_claude_code,
    register_in_loop_provider_if_inside_claude_code,
)

__all__ = [
    "in_loop_variation_provider",
    "is_running_in_claude_code",
    "register_in_loop_provider_if_inside_claude_code",
]
