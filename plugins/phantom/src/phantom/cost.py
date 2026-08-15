"""Token cost tracking per agent loop iteration.

Estimates token usage from screenshots and API responses,
tracks cumulative costs, and enforces budget limits.
"""

from __future__ import annotations

from dataclasses import dataclass

# Anthropic list pricing (per million tokens, USD), verified 2026-08-02
# against https://platform.claude.com/docs/en/about-claude/models/overview
#
# Refresh via Skill(night-market-model-and-harness-updates), which reads
# the model card as a mandatory source. Two entries here were wrong
# before that sweep: Opus 4.6 carried Opus 4.1's $15/$75 rate, and
# Haiku 4.5 was priced at $0.80/$4.00 rather than $1/$5.
#
# Sonnet 5 carries introductory pricing of $2/$10 through 2026-08-31.
# List price is used deliberately: a budget guard that assumes the
# promotional rate under-charges the moment it lapses.
PRICING = {
    # Current
    "claude-fable-5": {"input": 10.0, "output": 50.0},
    "claude-opus-5": {"input": 5.0, "output": 25.0},
    "claude-sonnet-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
    # Legacy, still callable
    "claude-opus-4-8": {"input": 5.0, "output": 25.0},
    "claude-opus-4-7": {"input": 5.0, "output": 25.0},
    "claude-opus-4-6": {"input": 5.0, "output": 25.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-opus-4-5-20251101": {"input": 5.0, "output": 25.0},
    # Deprecated, see DEPRECATED_MODELS
    "claude-opus-4-1-20250805": {"input": 15.0, "output": 75.0},
    # An unknown model is priced at the highest current published rate
    # on purpose. This table feeds CostTracker.budget_exceeded, and a
    # budget guard must fail toward stopping early. The previous
    # default was Sonnet's $3/$15, so an unrecognized frontier model
    # burned 3.3x its budget before the guard noticed.
    "default": {"input": 10.0, "output": 50.0},
}

# Priced above every current model but on its way out, so it is excluded
# when deriving the fallback rate. Opus 4.1 costs 1.5x Fable 5 and
# retires 2026-08-05; letting it set the floor would overcharge every
# unrecognized model for a rate nobody can be billed.
DEPRECATED_MODELS = frozenset({"claude-opus-4-1-20250805"})


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
