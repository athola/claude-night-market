"""Parallel work item execution via git worktrees."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class WorktreeAssignment:
    """Tracks which worktree a work item is assigned to."""

    item_id: str
    worktree_path: str = ""
    branch: str = ""
    status: str = "pending"  # pending, active, completed, failed, merged

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorktreeAssignment:
        """Deserialize from a plain dictionary."""
        return cls(
            item_id=data["item_id"],
            worktree_path=data.get("worktree_path", ""),
            branch=data.get("branch", ""),
            status=data.get("status", "pending"),
        )


def detect_independent_items(
    work_items: list[dict[str, Any]],
) -> list[list[str]]:
    """Group work items into independent sets that can run in parallel.

    Items are independent if they don't share source files or
    dependencies.  Returns a list of groups where items within each
    group are independent of one another.

    The heuristic: active items with different ``source_ref`` values
    are assumed independent.  Items that share a ``source_ref`` are
    placed in separate groups so they run sequentially.
    """
    groups: list[list[str]] = []
    seen: set[str] = set()

    for item in work_items:
        if item.get("status") != "active" or item["id"] in seen:
            continue

        group = [item["id"]]
        seen.add(item["id"])

        for other in work_items:
            if other["id"] in seen or other.get("status") != "active":
                continue
            if other.get("source_ref") != item.get("source_ref"):
                group.append(other["id"])
                seen.add(other["id"])

        groups.append(group)

    return groups


def build_agent_dispatch(
    item_ids: list[str],
    max_concurrent: int = 3,
) -> list[dict[str, Any]]:
    """Build agent dispatch instructions for parallel execution.

    Returns a list of batch descriptors, each containing up to
    ``max_concurrent`` item IDs that can execute simultaneously in
    separate worktrees.
    """
    batches: list[dict[str, Any]] = []
    for i in range(0, len(item_ids), max_concurrent):
        batch = item_ids[i : i + max_concurrent]
        batches.append(
            {
                "batch_index": i // max_concurrent,
                "item_ids": batch,
                "use_worktree": True,
                "isolation": "worktree",
            }
        )
    return batches


def merge_worktree_result(
    item_id: str,
    worktree_branch: str,
    target_branch: str = "master",
) -> dict[str, Any]:
    """Generate git commands to merge a worktree result back.

    Returns a dict with the merge strategy and the shell commands
    needed to perform the merge.
    """
    return {
        "item_id": item_id,
        "source_branch": worktree_branch,
        "target_branch": target_branch,
        "commands": [
            f"git checkout {target_branch}",
            f"git merge --no-ff {worktree_branch} -m 'Merge {item_id} from worktree'",
        ],
        "conflict_strategy": "mark_failed",
    }
