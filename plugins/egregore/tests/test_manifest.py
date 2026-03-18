"""Tests for egregore manifest state management."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from manifest import (
    PIPELINE,
    STAGE_ORDER,
    Manifest,
    WorkItem,
    load_manifest,
    save_manifest,
)


class TestWorkItem:
    """Tests for WorkItem dataclass."""

    def test_create_work_item_defaults(self) -> None:
        item = WorkItem(id="wrk_001", source="prompt", source_ref="do the thing")
        assert item.id == "wrk_001"
        assert item.source == "prompt"
        assert item.source_ref == "do the thing"
        assert item.branch == ""
        assert item.pipeline_stage == "intake"
        assert item.pipeline_step == "parse"
        assert item.status == "active"
        assert item.attempts == 0
        assert item.max_attempts == 3
        assert item.decisions == []
        assert item.failure_reason is None

    def test_to_dict_roundtrip(self) -> None:
        item = WorkItem(
            id="wrk_002",
            source="issue",
            source_ref="#42",
            branch="egregore/wrk-002-fix-bug",
        )
        d = item.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == "wrk_002"
        assert d["source"] == "issue"
        restored = WorkItem.from_dict(d)
        assert restored.id == item.id
        assert restored.source == item.source
        assert restored.source_ref == item.source_ref
        assert restored.branch == item.branch
        assert restored.pipeline_stage == item.pipeline_stage
        assert restored.pipeline_step == item.pipeline_step
        assert restored.status == item.status

    def test_from_dict_preserves_all_fields(self) -> None:
        item = WorkItem(
            id="wrk_003",
            source="prompt",
            source_ref="build a widget",
            branch="egregore/wrk-003-widget",
            pipeline_stage="build",
            pipeline_step="specify",
            attempts=2,
            max_attempts=5,
            status="active",
            decisions=[{"step": "parse", "chose": "A", "why": "better"}],
            failure_reason=None,
        )
        d = item.to_dict()
        restored = WorkItem.from_dict(d)
        assert restored.attempts == 2
        assert restored.max_attempts == 5
        assert restored.decisions == [{"step": "parse", "chose": "A", "why": "better"}]

    def test_worktree_path_default_empty(self) -> None:
        """WorkItem.worktree_path defaults to empty string."""
        item = WorkItem(id="wrk_004", source="prompt", source_ref="task")
        assert item.worktree_path == ""

    def test_worktree_path_roundtrip(self) -> None:
        """WorkItem.worktree_path survives to_dict/from_dict."""
        item = WorkItem(
            id="wrk_004",
            source="prompt",
            source_ref="task",
            worktree_path="/worktrees/wt-004",
        )
        d = item.to_dict()
        assert d["worktree_path"] == "/worktrees/wt-004"
        restored = WorkItem.from_dict(d)
        assert restored.worktree_path == "/worktrees/wt-004"

    def test_worktree_path_missing_in_dict_defaults(self) -> None:
        """from_dict handles missing worktree_path gracefully."""
        d = {
            "id": "wrk_005",
            "source": "prompt",
            "source_ref": "task",
        }
        item = WorkItem.from_dict(d)
        assert item.worktree_path == ""


class TestManifest:
    """Tests for Manifest dataclass."""

    def test_create_empty_manifest(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        assert m.work_items == []
        assert m.project_dir == "/tmp/test-project"
        assert m.session_count == 0
        assert m.continuation_count == 0
        assert m.created_at is not None

    def test_add_work_item_from_prompt(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="build a login page")
        assert item.id == "wrk_001"
        assert item.source == "prompt"
        assert item.source_ref == "build a login page"
        assert item.status == "active"
        assert item.pipeline_stage == "intake"
        assert item.pipeline_step == "parse"
        assert "egregore/wrk-001" in item.branch
        assert len(m.work_items) == 1

    def test_add_work_item_from_issue(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="issue", source_ref="#99")
        assert item.id == "wrk_001"
        assert item.source == "issue"
        assert item.source_ref == "#99"
        assert item.status == "active"
        assert "egregore/wrk-001" in item.branch

    def test_add_multiple_work_items_increments_id(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item1 = m.add_work_item(source="prompt", source_ref="first")
        item2 = m.add_work_item(source="prompt", source_ref="second")
        item3 = m.add_work_item(source="issue", source_ref="#10")
        assert item1.id == "wrk_001"
        assert item2.id == "wrk_002"
        assert item3.id == "wrk_003"

    def test_next_id_avoids_collision_after_removal(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        m.add_work_item(source="prompt", source_ref="first")
        m.add_work_item(source="prompt", source_ref="second")
        m.add_work_item(source="prompt", source_ref="third")
        # Simulate removal of the middle item
        m.work_items = [m.work_items[0], m.work_items[2]]
        # Next ID should be wrk_004 (max existing is wrk_003)
        item4 = m.add_work_item(source="prompt", source_ref="fourth")
        assert item4.id == "wrk_004"

    def test_advance_within_stage(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        # Start at intake/parse
        assert item.pipeline_stage == "intake"
        assert item.pipeline_step == "parse"
        # Advance to intake/validate
        m.advance(item.id)
        assert item.pipeline_stage == "intake"
        assert item.pipeline_step == "validate"
        # Advance to intake/prioritize
        m.advance(item.id)
        assert item.pipeline_stage == "intake"
        assert item.pipeline_step == "prioritize"

    def test_advance_across_stages(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        # Advance through all of intake: parse -> validate -> prioritize
        m.advance(item.id)  # validate
        m.advance(item.id)  # prioritize
        m.advance(item.id)  # should cross to build/brainstorm
        assert item.pipeline_stage == "build"
        assert item.pipeline_step == "brainstorm"

    def test_advance_through_entire_pipeline(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        # Count total steps across all stages
        total_steps = sum(len(steps) for steps in PIPELINE.values())
        # We start at step 0, so need total_steps - 1 advances to reach
        # the last step, then one more to mark completed.
        for _ in range(total_steps - 1):
            m.advance(item.id)
            assert item.status == "active"
        # One final advance should mark it completed
        m.advance(item.id)
        assert item.status == "completed"

    def test_advance_corrupt_step_marks_failed(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        # Corrupt the pipeline step to a value not in the stage
        item.pipeline_step = "nonexistent-step"
        m.advance(item.id)
        assert item.status == "failed"
        assert "Corrupt pipeline step" in item.failure_reason
        assert "nonexistent-step" in item.failure_reason

    def test_advance_completed_item_is_noop(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        total_steps = sum(len(steps) for steps in PIPELINE.values())
        for _ in range(total_steps):
            m.advance(item.id)
        assert item.status == "completed"
        # Advancing again should not error or change anything
        m.advance(item.id)
        assert item.status == "completed"

    def test_fail_current_step_increments_attempts(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        assert item.attempts == 0
        m.fail_current_step(item.id, reason="parse error")
        assert item.attempts == 1
        assert item.status == "active"  # not yet at max_attempts

    def test_fail_current_step_marks_failed_at_max(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        item.max_attempts = 2
        m.fail_current_step(item.id, reason="first failure")
        assert item.status == "active"
        m.fail_current_step(item.id, reason="second failure")
        assert item.status == "failed"
        assert item.failure_reason == "second failure"

    def test_next_active_item_returns_first(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item1 = m.add_work_item(source="prompt", source_ref="first")
        m.add_work_item(source="prompt", source_ref="second")
        result = m.next_active_item()
        assert result is not None
        assert result.id == item1.id

    def test_next_active_item_skips_completed(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item1 = m.add_work_item(source="prompt", source_ref="first")
        item2 = m.add_work_item(source="prompt", source_ref="second")
        # Complete the first item
        total_steps = sum(len(steps) for steps in PIPELINE.values())
        for _ in range(total_steps):
            m.advance(item1.id)
        assert item1.status == "completed"
        result = m.next_active_item()
        assert result is not None
        assert result.id == item2.id

    def test_next_active_item_returns_none_when_all_done(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item1 = m.add_work_item(source="prompt", source_ref="only")
        total_steps = sum(len(steps) for steps in PIPELINE.values())
        for _ in range(total_steps):
            m.advance(item1.id)
        result = m.next_active_item()
        assert result is None

    def test_next_active_item_skips_failed(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item1 = m.add_work_item(source="prompt", source_ref="first")
        item2 = m.add_work_item(source="prompt", source_ref="second")
        item1.max_attempts = 1
        m.fail_current_step(item1.id, reason="boom")
        assert item1.status == "failed"
        result = m.next_active_item()
        assert result is not None
        assert result.id == item2.id

    def test_record_decision(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        m.record_decision(
            item_id=item.id,
            step="parse",
            chose="option-a",
            why="it was simpler",
        )
        assert len(item.decisions) == 1
        assert item.decisions[0]["step"] == "parse"
        assert item.decisions[0]["chose"] == "option-a"
        assert item.decisions[0]["why"] == "it was simpler"

    def test_record_multiple_decisions(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        item = m.add_work_item(source="prompt", source_ref="task")
        m.record_decision(item.id, "parse", "A", "reason1")
        m.record_decision(item.id, "validate", "B", "reason2")
        assert len(item.decisions) == 2

    def test_history_starts_empty(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        assert m.history == []

    def test_record_history_appends_entry(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        m.record_history("advance", "moved wrk_001 to build/specify")
        assert len(m.history) == 1
        assert m.history[0]["event"] == "advance"
        assert m.history[0]["detail"] == "moved wrk_001 to build/specify"
        assert "timestamp" in m.history[0]

    def test_record_history_multiple_entries(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        m.record_history("start", "session started")
        m.record_history("advance", "moved forward")
        assert len(m.history) == 2

    def test_history_roundtrips_through_dict(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        m.record_history("test", "roundtrip check")
        d = m.to_dict()
        assert "history" in d
        assert len(d["history"]) == 1
        restored = Manifest.from_dict(d)
        assert len(restored.history) == 1
        assert restored.history[0]["event"] == "test"

    def test_from_dict_without_history_defaults_empty(self) -> None:
        data = {"project_dir": "/tmp/test", "work_items": []}
        m = Manifest.from_dict(data)
        assert m.history == []

    def test_manifest_to_dict_from_dict_roundtrip(self) -> None:
        m = Manifest(project_dir="/tmp/test-project")
        m.session_count = 3
        m.continuation_count = 1
        item = m.add_work_item(source="prompt", source_ref="task")
        m.advance(item.id)
        m.record_decision(item.id, "parse", "A", "reason")
        d = m.to_dict()
        assert isinstance(d, dict)
        restored = Manifest.from_dict(d)
        assert restored.project_dir == m.project_dir
        assert restored.session_count == 3
        assert restored.continuation_count == 1
        assert len(restored.work_items) == 1
        assert restored.work_items[0].id == "wrk_001"
        assert restored.work_items[0].pipeline_step == "validate"
        assert len(restored.work_items[0].decisions) == 1

    def test_max_concurrent_worktrees_default(self) -> None:
        """Manifest.max_concurrent_worktrees defaults to 3."""
        m = Manifest(project_dir="/tmp/test-project")
        assert m.max_concurrent_worktrees == 3

    def test_max_concurrent_worktrees_roundtrip(self) -> None:
        """max_concurrent_worktrees survives to_dict/from_dict."""
        m = Manifest(project_dir="/tmp/test-project")
        m.max_concurrent_worktrees = 5
        d = m.to_dict()
        assert d["max_concurrent_worktrees"] == 5
        restored = Manifest.from_dict(d)
        assert restored.max_concurrent_worktrees == 5

    def test_max_concurrent_worktrees_missing_in_dict(self) -> None:
        """from_dict handles missing max_concurrent_worktrees."""
        d = {"project_dir": "/tmp/test-project"}
        m = Manifest.from_dict(d)
        assert m.max_concurrent_worktrees == 3


class TestSaveLoad:
    """Tests for save_manifest and load_manifest."""

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "subdir" / "manifest.json"
        m = Manifest(project_dir="/tmp/test-project")
        m.add_work_item(source="prompt", source_ref="build it")
        m.session_count = 5
        save_manifest(m, manifest_path)
        assert manifest_path.exists()
        # Verify it's valid JSON
        with open(manifest_path) as f:
            data = json.load(f)
        assert "work_items" in data
        # Load it back
        loaded = load_manifest(manifest_path)
        assert loaded.project_dir == m.project_dir
        assert loaded.session_count == 5
        assert len(loaded.work_items) == 1
        assert loaded.work_items[0].source_ref == "build it"

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        deep_path = tmp_path / "a" / "b" / "c" / "manifest.json"
        m = Manifest(project_dir="/tmp/test-project")
        save_manifest(m, deep_path)
        assert deep_path.exists()

    def test_load_nonexistent_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises((FileNotFoundError, OSError)):
            load_manifest(tmp_path / "nope.json")


class TestPipelineConstants:
    """Tests for pipeline constants."""

    def test_stage_order_matches_pipeline_keys(self) -> None:
        assert list(PIPELINE.keys()) == STAGE_ORDER

    def test_all_stages_have_steps(self) -> None:
        for stage in STAGE_ORDER:
            assert len(PIPELINE[stage]) > 0

    def test_pipeline_structure(self) -> None:
        assert PIPELINE["intake"] == ["parse", "validate", "prioritize"]
        assert PIPELINE["build"] == [
            "brainstorm",
            "specify",
            "blueprint",
            "execute",
        ]
        assert PIPELINE["quality"] == [
            "code-review",
            "unbloat",
            "code-refinement",
            "update-tests",
            "update-docs",
        ]
        assert PIPELINE["ship"] == [
            "prepare-pr",
            "pr-review",
            "fix-pr",
            "merge",
        ]
