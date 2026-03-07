"""Manifest state management for egregore work items and pipeline progress."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PIPELINE: dict[str, list[str]] = {
    "intake": ["parse", "validate", "prioritize"],
    "build": ["brainstorm", "specify", "blueprint", "execute"],
    "quality": [
        "code-review",
        "unbloat",
        "code-refinement",
        "update-tests",
        "update-docs",
    ],
    "ship": ["prepare-pr", "pr-review", "fix-pr", "merge"],
}

STAGE_ORDER: list[str] = ["intake", "build", "quality", "ship"]


def _make_slug(text: str, max_len: int = 30) -> str:
    """Create a branch-safe slug from arbitrary text."""
    slug = text.lower().strip()
    # Strip leading # (issue refs)
    slug = slug.lstrip("#")
    # Replace non-alphanum with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len].rstrip("-")


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WorkItem:
    """A single work item tracked by the egregore manifest."""

    id: str
    source: str
    source_ref: str
    branch: str = ""
    pipeline_stage: str = "intake"
    pipeline_step: str = "parse"
    started_at: str = field(default_factory=_now_iso)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 3
    status: str = "active"
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "source_ref": self.source_ref,
            "branch": self.branch,
            "pipeline_stage": self.pipeline_stage,
            "pipeline_step": self.pipeline_step,
            "started_at": self.started_at,
            "decisions": list(self.decisions),
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkItem:
        """Deserialize from a plain dictionary."""
        return cls(
            id=data["id"],
            source=data["source"],
            source_ref=data["source_ref"],
            branch=data.get("branch", ""),
            pipeline_stage=data.get("pipeline_stage", "intake"),
            pipeline_step=data.get("pipeline_step", "parse"),
            started_at=data.get("started_at", _now_iso()),
            decisions=data.get("decisions", []),
            attempts=data.get("attempts", 0),
            max_attempts=data.get("max_attempts", 3),
            status=data.get("status", "active"),
            failure_reason=data.get("failure_reason"),
        )


@dataclass
class Manifest:
    """Persistent state for egregore work items and pipeline progress."""

    project_dir: str
    work_items: list[WorkItem] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    session_count: int = 0
    continuation_count: int = 0

    def _next_id(self) -> str:
        """Generate the next sequential work item ID."""
        num = len(self.work_items) + 1
        return f"wrk_{num:03d}"

    def _find_item(self, item_id: str) -> WorkItem:
        """Look up a work item by ID."""
        for item in self.work_items:
            if item.id == item_id:
                return item
        raise KeyError(f"No work item with id: {item_id}")

    def add_work_item(
        self,
        source: str,
        source_ref: str,
    ) -> WorkItem:
        """Add a new work item to the manifest.

        Generates a sequential ID like "wrk_001" and a branch name
        like "egregore/wrk-001-slug".
        """
        item_id = self._next_id()
        slug = _make_slug(source_ref)
        branch_id = item_id.replace("_", "-")
        if slug:
            branch = f"egregore/{branch_id}-{slug}"
        else:
            branch = f"egregore/{branch_id}"

        item = WorkItem(
            id=item_id,
            source=source,
            source_ref=source_ref,
            branch=branch,
            pipeline_stage=STAGE_ORDER[0],
            pipeline_step=PIPELINE[STAGE_ORDER[0]][0],
        )
        self.work_items.append(item)
        return item

    def advance(self, item_id: str) -> None:
        """Advance a work item to the next pipeline step.

        Moves to the next step within the current stage, or to the
        first step of the next stage, or marks the item completed if
        it has finished the last step of the last stage.
        """
        item = self._find_item(item_id)

        if item.status != "active":
            return

        stage = item.pipeline_stage
        step = item.pipeline_step
        steps = PIPELINE[stage]
        step_idx = steps.index(step)

        if step_idx + 1 < len(steps):
            # More steps in this stage
            item.pipeline_step = steps[step_idx + 1]
            item.attempts = 0
        else:
            # Move to the next stage
            stage_idx = STAGE_ORDER.index(stage)
            if stage_idx + 1 < len(STAGE_ORDER):
                next_stage = STAGE_ORDER[stage_idx + 1]
                item.pipeline_stage = next_stage
                item.pipeline_step = PIPELINE[next_stage][0]
                item.attempts = 0
            else:
                # Pipeline complete
                item.status = "completed"

    def fail_current_step(self, item_id: str, reason: str) -> None:
        """Record a failure on the current step.

        Increments attempts. If attempts >= max_attempts, marks the
        item as failed.
        """
        item = self._find_item(item_id)
        item.attempts += 1
        if item.attempts >= item.max_attempts:
            item.status = "failed"
            item.failure_reason = reason

    def next_active_item(self) -> WorkItem | None:
        """Return the first work item with status 'active', or None."""
        for item in self.work_items:
            if item.status == "active":
                return item
        return None

    def record_decision(
        self,
        item_id: str,
        step: str,
        chose: str,
        why: str,
    ) -> None:
        """Record a decision made during a pipeline step."""
        item = self._find_item(item_id)
        item.decisions.append(
            {
                "step": step,
                "chose": chose,
                "why": why,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire manifest to a plain dictionary."""
        return {
            "project_dir": self.project_dir,
            "work_items": [wi.to_dict() for wi in self.work_items],
            "created_at": self.created_at,
            "session_count": self.session_count,
            "continuation_count": self.continuation_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        """Deserialize from a plain dictionary."""
        m = cls(
            project_dir=data["project_dir"],
            created_at=data.get("created_at", _now_iso()),
            session_count=data.get("session_count", 0),
            continuation_count=data.get("continuation_count", 0),
        )
        m.work_items = [WorkItem.from_dict(wi) for wi in data.get("work_items", [])]
        return m


def save_manifest(manifest: Manifest, path: Path) -> None:
    """Save a manifest to JSON, creating parent directories as needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest.to_dict(), f, indent=2)


def load_manifest(path: Path) -> Manifest:
    """Load a manifest from a JSON file."""
    path = Path(path)
    with open(path) as f:
        data = json.load(f)
    return Manifest.from_dict(data)
