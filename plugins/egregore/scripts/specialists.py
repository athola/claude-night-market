"""Agent specialization with persistent expertise for egregore pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class SpecialistProfile:
    """Profile for a specialist agent type.

    Each specialist maps to one or more pipeline steps and accumulates
    context and performance metrics across sessions.
    """

    role: str  # "reviewer", "documenter", "tester"
    description: str
    pipeline_steps: list[str]  # Steps this specialist handles
    context_file: str = ""  # Path to persisted context
    items_processed: int = 0
    last_active: str = ""
    performance_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "role": self.role,
            "description": self.description,
            "pipeline_steps": list(self.pipeline_steps),
            "context_file": self.context_file,
            "items_processed": self.items_processed,
            "last_active": self.last_active,
            "performance_metrics": dict(self.performance_metrics),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpecialistProfile:
        """Deserialize from a plain dictionary, ignoring unknown keys."""
        known = {
            "role",
            "description",
            "pipeline_steps",
            "context_file",
            "items_processed",
            "last_active",
            "performance_metrics",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


# Default specialist definitions
DEFAULT_SPECIALISTS: list[SpecialistProfile] = [
    SpecialistProfile(
        role="reviewer",
        description="Code review specialist with accumulated codebase knowledge",
        pipeline_steps=[
            "code-review",
            "code-refinement",
            "pr-review",
            "fix-pr",
        ],
    ),
    SpecialistProfile(
        role="documenter",
        description="Documentation specialist maintaining consistent style",
        pipeline_steps=["update-docs", "prepare-pr"],
    ),
    SpecialistProfile(
        role="tester",
        description="Testing specialist focused on coverage and quality",
        pipeline_steps=["update-tests"],
    ),
]


def get_specialist_for_step(
    step: str,
    specialists: list[SpecialistProfile],
) -> Optional[SpecialistProfile]:  # noqa: UP045
    """Find the specialist assigned to a pipeline step.

    Returns None if no specialist is mapped to the given step.
    """
    for spec in specialists:
        if step in spec.pipeline_steps:
            return spec
    return None


def build_specialist_context(
    specialist: SpecialistProfile,
    egregore_dir: Path,
) -> str:
    """Build context prompt for a specialist from persisted knowledge.

    Reads the specialist's markdown context file if it exists.
    Returns an empty string when no prior context is available.
    """
    context_path = egregore_dir / "specialists" / f"{specialist.role}.md"
    if context_path.exists():
        return context_path.read_text()
    return ""


def save_specialist_context(
    specialist: SpecialistProfile,
    context: str,
    egregore_dir: Path,
) -> Path:
    """Persist specialist context for future sessions.

    Creates the specialists directory if needed, writes the context
    file, and updates the specialist's metadata.
    """
    context_dir = egregore_dir / "specialists"
    context_dir.mkdir(parents=True, exist_ok=True)
    context_path = context_dir / f"{specialist.role}.md"
    context_path.write_text(context)
    specialist.context_file = str(context_path)
    specialist.last_active = datetime.now(timezone.utc).isoformat()  # noqa: UP017
    return context_path


def record_specialist_metrics(
    specialist: SpecialistProfile,
    step: str,
    success: bool,
    duration_seconds: float = 0.0,
) -> None:
    """Record performance metrics for a specialist.

    Tracks per-step attempts, successes, and cumulative duration.
    """
    specialist.items_processed += 1
    specialist.last_active = datetime.now(timezone.utc).isoformat()  # noqa: UP017
    metrics = specialist.performance_metrics
    if "steps" not in metrics:
        metrics["steps"] = {}
    if step not in metrics["steps"]:
        metrics["steps"][step] = {
            "attempts": 0,
            "successes": 0,
            "total_duration": 0.0,
        }
    metrics["steps"][step]["attempts"] += 1
    if success:
        metrics["steps"][step]["successes"] += 1
    metrics["steps"][step]["total_duration"] += duration_seconds


def save_specialists(specialists: list[SpecialistProfile], path: Path) -> None:
    """Save specialist profiles to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [s.to_dict() for s in specialists]
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_specialists(path: Path) -> list[SpecialistProfile]:
    """Load specialist profiles from JSON, returning defaults if missing."""
    if not path.exists():
        return [
            SpecialistProfile(
                role=s.role,
                description=s.description,
                pipeline_steps=list(s.pipeline_steps),
            )
            for s in DEFAULT_SPECIALISTS
        ]
    try:
        data = json.loads(path.read_text())
        return [SpecialistProfile.from_dict(d) for d in data]
    except (json.JSONDecodeError, OSError):
        return list(DEFAULT_SPECIALISTS)
