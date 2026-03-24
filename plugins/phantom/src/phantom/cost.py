"""Token cost tracking per agent loop iteration.

Estimates token usage from screenshots and API responses,
tracks cumulative costs, and enforces budget limits.
"""

from __future__ import annotations

from dataclasses import dataclass

# Anthropic pricing (per million tokens, USD) as of 2026-03
# These are approximate and should be updated as pricing changes.
PRICING = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4-5-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "default": {"input": 3.0, "output": 15.0},
}


def estimate_screenshot_tokens(width: int, height: int) -> int:
    """Estimate tokens consumed by a screenshot at given resolution.

    Anthropic's vision model processes images in tiles. A rough
    estimate: ~0.85 tokens per 32x32 pixel tile, plus overhead.
    This is an approximation for budget planning.
    """
    if width == 0 or height == 0:
        return 0

    # Approximate: image is resized so longest edge <= 1568px,
    # then tiled into 32x32 blocks. Each tile ~ 0.85 tokens.
    scale = min(1.0, 1568 / max(width, height))
    scaled_w = int(width * scale)
    scaled_h = int(height * scale)

    tiles = (scaled_w // 32 + 1) * (scaled_h // 32 + 1)
    # Base token count per tile plus fixed overhead
    return int(tiles * 0.85) + 85


@dataclass
class IterationCost:
    """Cost data for a single agent loop iteration."""

    iteration: int
    input_tokens: int = 0
    output_tokens: int = 0
    screenshot_tokens_est: int = 0
    model: str = "default"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.screenshot_tokens_est

    def estimated_cost_usd(self, model: str | None = None) -> float:
        """Estimate USD cost for this iteration."""
        m = model or self.model
        prices = PRICING.get(m, PRICING["default"])
        total_in = self.input_tokens + self.screenshot_tokens_est
        input_cost = total_in * prices["input"] / 1_000_000
        output_cost = self.output_tokens * prices["output"] / 1_000_000
        return input_cost + output_cost


class CostTracker:
    """Track cumulative token usage and costs across iterations."""

    def __init__(
        self,
        model: str = "default",
        budget_usd: float | None = None,
    ) -> None:
        self.model = model
        self._budget_usd = budget_usd
        self.iterations: list[IterationCost] = []

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)

    @property
    def total_input_tokens(self) -> int:
        return sum(i.input_tokens for i in self.iterations)

    @property
    def total_output_tokens(self) -> int:
        return sum(i.output_tokens for i in self.iterations)

    @property
    def total_screenshot_tokens(self) -> int:
        return sum(i.screenshot_tokens_est for i in self.iterations)

    @property
    def total_cost_usd(self) -> float:
        return sum(i.estimated_cost_usd(self.model) for i in self.iterations)

    @property
    def budget_exceeded(self) -> bool:
        if self._budget_usd is None:
            return False
        return self.total_cost_usd > self._budget_usd

    def record(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        screenshot_tokens_est: int = 0,
    ) -> IterationCost:
        """Record one iteration's token usage."""
        cost = IterationCost(
            iteration=self.iteration_count + 1,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            screenshot_tokens_est=screenshot_tokens_est,
            model=self.model,
        )
        self.iterations.append(cost)
        return cost

    def summary(self) -> str:
        """Return a human-readable cost summary."""
        lines = [
            f"Iterations: {self.iteration_count}",
            f"Total input tokens:      {self.total_input_tokens:>10,}",
            f"Total output tokens:     {self.total_output_tokens:>10,}",
            f"Total screenshot tokens: {self.total_screenshot_tokens:>10,}",
            f"Estimated cost:          ${self.total_cost_usd:>9.4f}",
        ]
        if self._budget_usd is not None:
            remaining = self._budget_usd - self.total_cost_usd
            lines.append(f"Budget remaining:        ${remaining:>9.4f}")
        return "\n".join(lines)
