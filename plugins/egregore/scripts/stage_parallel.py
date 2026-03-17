"""Parallel pipeline stage execution for independent quality gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Step dependency graph: step -> list of steps it depends on.
# Steps with empty dependency lists can run in parallel.
STEP_DEPENDENCIES: dict[str, list[str]] = {
    # Quality stage parallelizable groups
    "code-review": [],
    "unbloat": [],
    "update-docs": [],
    "code-refinement": ["code-review"],
    "update-tests": ["code-review"],
}


@dataclass
class StageExecutionPlan:
    """Plan for executing steps within a stage, with parallelism.

    Steps are grouped into waves. All steps in a wave can run
    concurrently because they share no interdependencies. Waves
    execute sequentially: wave N must finish before wave N+1 starts.
    """

    stage: str
    waves: list[list[str]] = field(default_factory=list)

    @property
    def is_parallel(self) -> bool:
        """True if the plan has any wave with more than one step."""
        return any(len(w) > 1 for w in self.waves)

    @property
    def total_steps(self) -> int:
        """Total number of steps across all waves."""
        return sum(len(w) for w in self.waves)


def plan_stage_execution(
    stage: str,
    steps: list[str],
) -> StageExecutionPlan:
    """Plan parallel execution waves for steps in a stage.

    Groups steps into waves based on STEP_DEPENDENCIES.
    Steps in the same wave have no interdependencies and can
    run concurrently. Steps with unmet dependencies are deferred
    to later waves.

    If a circular dependency or unknown configuration prevents
    progress, remaining steps are placed in a final catch-all wave
    to avoid deadlock.
    """
    plan = StageExecutionPlan(stage=stage)
    remaining = list(steps)
    completed: set[str] = set()

    while remaining:
        wave: list[str] = []
        for step in remaining:
            deps = STEP_DEPENDENCIES.get(step, [])
            if all(d in completed for d in deps):
                wave.append(step)
        if not wave:
            # Circular dependency or unknown steps: run sequentially
            plan.waves.append(remaining)
            break
        plan.waves.append(wave)
        for s in wave:
            remaining.remove(s)
            completed.add(s)

    return plan


def build_parallel_dispatch(
    wave: list[str],
    item_id: str,
) -> list[dict[str, Any]]:
    """Build agent dispatch instructions for a parallel wave.

    Returns one dispatch entry per step, each containing the
    step name, work item ID, skill reference, and arguments
    needed to invoke the quality gate.
    """
    return [
        {
            "step": step,
            "item_id": item_id,
            "skill": "egregore:quality-gate",
            "args": f"step={step}",
        }
        for step in wave
    ]


@dataclass
class WaveResult:
    """Result of executing a parallel wave."""

    wave_index: int
    results: dict[str, str] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        """True if every step in the wave passed."""
        return all(r == "pass" for r in self.results.values())

    @property
    def failed_steps(self) -> list[str]:
        """Return the names of steps that did not pass."""
        return [s for s, r in self.results.items() if r != "pass"]
