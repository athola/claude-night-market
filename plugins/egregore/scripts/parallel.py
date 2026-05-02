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

    O(n): bucket active items by source_ref preserving first-seen
    order, then distribute one item per bucket per group (round-robin).
    """
    buckets: dict[str | None, list[str]] = {}
    bucket_order: list[str | None] = []

    for item in work_items:
        if item.get("status") != "active":
            continue
        ref = item.get("source_ref")
        if ref not in buckets:
            buckets[ref] = []
            bucket_order.append(ref)
        buckets[ref].append(item["id"])

    if not buckets:
        return []

    max_depth = max(len(buckets[ref]) for ref in bucket_order)
    return [
        [buckets[ref][i] for ref in bucket_order if i < len(buckets[ref])]
        for i in range(max_depth)
    ]


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
