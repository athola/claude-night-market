"""Tests for parallel work item execution via git worktrees.

Feature: Parallel work item execution
    As the egregore orchestrator
    I want to detect independent work items and dispatch them in parallel
    So that independent tasks complete faster using git worktrees
"""

from __future__ import annotations

from parallel import (
    WorktreeAssignment,
    build_agent_dispatch,
    detect_independent_items,
    merge_worktree_result,
)


class TestWorktreeAssignment:
    """Feature: Worktree assignment tracking.

    As the orchestrator
    I want to track which worktree each work item uses
    So that I can manage worktree lifecycles correctly
    """

    def test_default_assignment_is_pending(self) -> None:
        """Scenario: New worktree assignment starts as pending
        Given a work item ID
        When I create a WorktreeAssignment
        Then its status is 'pending' with empty path and branch
        """
        a = WorktreeAssignment(item_id="wrk_001")
        assert a.item_id == "wrk_001"
        assert a.worktree_path == ""
        assert a.branch == ""
        assert a.status == "pending"

    def test_to_dict_roundtrip(self) -> None:
        """Scenario: Assignment survives serialization roundtrip
        Given a fully populated WorktreeAssignment
        When I serialize and deserialize it
        Then all fields are preserved
        """
        a = WorktreeAssignment(
            item_id="wrk_002",
            worktree_path="/worktrees/wt-002",
            branch="egregore/wrk-002-feat",
            status="active",
        )
        d = a.to_dict()
        assert isinstance(d, dict)
        assert d["item_id"] == "wrk_002"
        assert d["status"] == "active"

        restored = WorktreeAssignment.from_dict(d)
        assert restored.item_id == a.item_id
        assert restored.worktree_path == a.worktree_path
        assert restored.branch == a.branch
        assert restored.status == a.status

    def test_from_dict_with_missing_optional_fields(self) -> None:
        """Scenario: Deserialize with only required fields
        Given a dict with only item_id
        When I call from_dict
        Then defaults are applied for optional fields
        """
        d = {"item_id": "wrk_003"}
        a = WorktreeAssignment.from_dict(d)
        assert a.item_id == "wrk_003"
        assert a.worktree_path == ""
        assert a.branch == ""
        assert a.status == "pending"


class TestDetectIndependentItems:
    """Feature: Independence detection for parallel execution.

    As the orchestrator
    I want to identify which work items can run concurrently
    So that I avoid conflicts from shared files
    """

    def test_empty_list_returns_empty(self) -> None:
        """Scenario: No work items yields no groups
        Given an empty work items list
        When I detect independent items
        Then I get an empty list of groups
        """
        assert detect_independent_items([]) == []

    def test_single_active_item_returns_one_group(self) -> None:
        """Scenario: Single active item forms its own group
        Given one active work item
        When I detect independent items
        Then I get one group containing that item
        """
        items = [{"id": "wrk_001", "status": "active", "source_ref": "#10"}]
        groups = detect_independent_items(items)
        assert groups == [["wrk_001"]]

    def test_different_source_refs_are_independent(self) -> None:
        """Scenario: Items with different source refs are grouped together
        Given two active items with different source_ref values
        When I detect independent items
        Then both appear in the same parallel group
        """
        items = [
            {"id": "wrk_001", "status": "active", "source_ref": "#10"},
            {"id": "wrk_002", "status": "active", "source_ref": "#20"},
        ]
        groups = detect_independent_items(items)
        assert len(groups) == 1
        assert set(groups[0]) == {"wrk_001", "wrk_002"}

    def test_same_source_ref_items_are_not_grouped(self) -> None:
        """Scenario: Items sharing a source ref run sequentially
        Given two active items with the same source_ref
        When I detect independent items
        Then they appear in separate groups
        """
        items = [
            {"id": "wrk_001", "status": "active", "source_ref": "#10"},
            {"id": "wrk_002", "status": "active", "source_ref": "#10"},
        ]
        groups = detect_independent_items(items)
        # wrk_001 forms a group; wrk_002 cannot join because same source_ref
        assert len(groups) == 2
        assert groups[0] == ["wrk_001"]
        assert groups[1] == ["wrk_002"]

    def test_non_active_items_are_excluded(self) -> None:
        """Scenario: Completed and failed items are ignored
        Given a mix of active, completed, and failed items
        When I detect independent items
        Then only active items appear in groups
        """
        items = [
            {"id": "wrk_001", "status": "completed", "source_ref": "#10"},
            {"id": "wrk_002", "status": "active", "source_ref": "#20"},
            {"id": "wrk_003", "status": "failed", "source_ref": "#30"},
        ]
        groups = detect_independent_items(items)
        assert groups == [["wrk_002"]]

    def test_mixed_independence(self) -> None:
        """Scenario: Three items, two independent and one sharing a ref
        Given items A(#10), B(#20), C(#10) all active
        When I detect independent items
        Then A and B form one parallel group, C is separate
        """
        items = [
            {"id": "wrk_001", "status": "active", "source_ref": "#10"},
            {"id": "wrk_002", "status": "active", "source_ref": "#20"},
            {"id": "wrk_003", "status": "active", "source_ref": "#10"},
        ]
        groups = detect_independent_items(items)
        assert len(groups) == 2
        # First group: wrk_001 picks up wrk_002 (different ref)
        assert set(groups[0]) == {"wrk_001", "wrk_002"}
        # Second group: wrk_003 is alone (shares ref with wrk_001)
        assert groups[1] == ["wrk_003"]


class TestBuildAgentDispatch:
    """Feature: Batch dispatch planning.

    As the orchestrator
    I want to split items into batches limited by concurrency
    So that I don't overwhelm the system with too many worktrees
    """

    def test_empty_ids_returns_empty(self) -> None:
        """Scenario: No item IDs produces no batches
        Given an empty list of item IDs
        When I build agent dispatch
        Then I get an empty batch list
        """
        assert build_agent_dispatch([]) == []

    def test_single_batch_under_limit(self) -> None:
        """Scenario: Few items fit in one batch
        Given 2 items with max_concurrent=3
        When I build agent dispatch
        Then I get one batch containing both items
        """
        batches = build_agent_dispatch(["wrk_001", "wrk_002"], max_concurrent=3)
        assert len(batches) == 1
        assert batches[0]["batch_index"] == 0
        assert batches[0]["item_ids"] == ["wrk_001", "wrk_002"]
        assert batches[0]["use_worktree"] is True
        assert batches[0]["isolation"] == "worktree"

    def test_splits_into_multiple_batches(self) -> None:
        """Scenario: More items than max_concurrent
        Given 5 items with max_concurrent=2
        When I build agent dispatch
        Then I get 3 batches (2, 2, 1)
        """
        ids = [f"wrk_{i:03d}" for i in range(1, 6)]
        batches = build_agent_dispatch(ids, max_concurrent=2)
        assert len(batches) == 3
        assert batches[0]["item_ids"] == ["wrk_001", "wrk_002"]
        assert batches[0]["batch_index"] == 0
        assert batches[1]["item_ids"] == ["wrk_003", "wrk_004"]
        assert batches[1]["batch_index"] == 1
        assert batches[2]["item_ids"] == ["wrk_005"]
        assert batches[2]["batch_index"] == 2

    def test_exact_multiple_of_max_concurrent(self) -> None:
        """Scenario: Items divide evenly into batches
        Given 6 items with max_concurrent=3
        When I build agent dispatch
        Then I get exactly 2 batches of 3
        """
        ids = [f"wrk_{i:03d}" for i in range(1, 7)]
        batches = build_agent_dispatch(ids, max_concurrent=3)
        assert len(batches) == 2
        assert len(batches[0]["item_ids"]) == 3
        assert len(batches[1]["item_ids"]) == 3

    def test_default_max_concurrent_is_three(self) -> None:
        """Scenario: Default concurrency limit
        Given 4 items with no explicit max_concurrent
        When I build agent dispatch
        Then the default limit of 3 produces 2 batches
        """
        ids = [f"wrk_{i:03d}" for i in range(1, 5)]
        batches = build_agent_dispatch(ids)
        assert len(batches) == 2
        assert len(batches[0]["item_ids"]) == 3
        assert len(batches[1]["item_ids"]) == 1


class TestMergeWorktreeResult:
    """Feature: Worktree merge command generation.

    As the orchestrator
    I want merge commands for completed worktree branches
    So that finished work integrates back into the target branch
    """

    def test_generates_merge_commands(self) -> None:
        """Scenario: Generate merge commands for a completed item
        Given an item ID and its worktree branch
        When I call merge_worktree_result
        Then I get checkout + merge commands targeting master
        """
        result = merge_worktree_result(
            item_id="wrk_001",
            worktree_branch="egregore/wrk-001-feat",
        )
        assert result["item_id"] == "wrk_001"
        assert result["source_branch"] == "egregore/wrk-001-feat"
        assert result["target_branch"] == "master"
        assert result["conflict_strategy"] == "mark_failed"
        assert len(result["commands"]) == 2
        assert "git checkout master" in result["commands"][0]
        assert "git merge --no-ff" in result["commands"][1]
        assert "wrk_001" in result["commands"][1]

    def test_custom_target_branch(self) -> None:
        """Scenario: Merge into a non-default target branch
        Given a custom target_branch of 'develop'
        When I call merge_worktree_result
        Then commands reference 'develop' instead of 'master'
        """
        result = merge_worktree_result(
            item_id="wrk_002",
            worktree_branch="egregore/wrk-002-fix",
            target_branch="develop",
        )
        assert result["target_branch"] == "develop"
        assert "git checkout develop" in result["commands"][0]
