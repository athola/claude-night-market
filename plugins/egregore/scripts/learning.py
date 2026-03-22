"""Cross-item learning via decision log analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Minimum success rate to label a pattern as SUCCESS vs CAUTION.
SUCCESS_THRESHOLD: float = 0.5


@dataclass
class LearnedPattern:
    """A pattern extracted from decision logs."""

    category: str  # "tech_stack", "failure_mode", "architecture", "approach"
    description: str
    frequency: int = 1
    last_seen: str = ""
    success_count: int = 0
    source_items: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Compute success rate from integer counts (no drift)."""
        if self.frequency == 0:
            return 0.0
        return self.success_count / self.frequency

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "category": self.category,
            "description": self.description,
            "frequency": self.frequency,
            "last_seen": self.last_seen,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "source_items": list(self.source_items),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearnedPattern:
        """Deserialize from a plain dictionary."""
        known = {
            "category",
            "description",
            "frequency",
            "last_seen",
            "success_count",
            "source_items",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        # Backward compat: reconstruct success_count from success_rate
        if "success_count" not in filtered and "success_rate" in data:
            freq = filtered.get("frequency", 1)
            filtered["success_count"] = round(data["success_rate"] * freq)
        return cls(**filtered)


def _categorize_decision(step: str, choice: str) -> str:
    """Categorize a decision based on step and choice content."""
    choice_lower = choice.lower()
    if any(kw in choice_lower for kw in ["stack", "framework", "library", "tool"]):
        return "tech_stack"
    if any(kw in choice_lower for kw in ["fail", "error", "retry", "skip"]):
        return "failure_mode"
    if any(kw in choice_lower for kw in ["pattern", "architecture", "design"]):
        return "architecture"
    return "approach"


def extract_patterns(
    work_items: list[dict[str, Any]],
    max_patterns: int = 20,
) -> list[LearnedPattern]:
    """Extract patterns from completed work items' decision logs.

    Analyzes decisions from completed items to find:

    - Frequently chosen approaches
    - Common failure modes (from failed items)
    - Successful architectural choices
    """
    patterns: dict[str, LearnedPattern] = {}

    for item in work_items:
        item_id = item.get("id", "")
        status = item.get("status", "")
        decisions = item.get("decisions", [])

        for decision in decisions:
            step = decision.get("step", "")
            chose = decision.get("chose", "")
            why = decision.get("why", "")

            if not chose:
                continue

            # Key by step+choice for deduplication
            key = f"{step}:{chose}"

            if key in patterns:
                pattern = patterns[key]
                pattern.frequency += 1
                pattern.source_items.append(item_id)
                if status == "completed":
                    pattern.success_count += 1
            else:
                patterns[key] = LearnedPattern(
                    category=_categorize_decision(step, chose),
                    description=f"{step}: {chose}" + (f" ({why})" if why else ""),
                    frequency=1,
                    last_seen=item.get("started_at", ""),
                    success_count=1 if status == "completed" else 0,
                    source_items=[item_id],
                )

    # Sort by frequency * success_rate (weighted relevance)
    sorted_patterns = sorted(
        patterns.values(),
        key=lambda p: p.frequency * p.success_rate,
        reverse=True,
    )
    return sorted_patterns[:max_patterns]


def build_learning_context(
    patterns: list[LearnedPattern],
    max_tokens_estimate: int = 500,
) -> str:
    """Build a context string from learned patterns for injection.

    Produces a concise summary of relevant patterns that can be
    prepended to the orchestrator's context for the current item.
    """
    if not patterns:
        return ""

    lines = ["## Learned Patterns from Previous Work Items", ""]

    for pattern in patterns:
        if pattern.success_rate >= SUCCESS_THRESHOLD:
            indicator = "SUCCESS"
        else:
            indicator = "CAUTION"
        lines.append(
            f"- [{indicator}] {pattern.description} "
            f"(seen {pattern.frequency}x, {pattern.success_rate:.0%} success)"
        )

    return "\n".join(lines)


def weight_by_recency(
    patterns: list[LearnedPattern],
    decay_factor: float = 0.9,
) -> list[LearnedPattern]:
    """Weight patterns by recency, giving more weight to recent decisions.

    Sorts patterns by last_seen date and applies exponential decay
    to frequency scores for older patterns.
    """
    sorted_patterns = sorted(
        patterns,
        key=lambda p: p.last_seen or "",
        reverse=True,
    )

    for i, pattern in enumerate(sorted_patterns):
        weight = decay_factor**i
        pattern.frequency = max(1, round(pattern.frequency * weight))
        pattern.success_count = max(0, round(pattern.success_count * weight))

    return sorted_patterns


def save_patterns(patterns: list[LearnedPattern], path: Path) -> None:
    """Save learned patterns to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [p.to_dict() for p in patterns]
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_patterns(path: Path) -> list[LearnedPattern]:
    """Load learned patterns from JSON."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [LearnedPattern.from_dict(d) for d in data]
    except (json.JSONDecodeError, OSError):
        return []
