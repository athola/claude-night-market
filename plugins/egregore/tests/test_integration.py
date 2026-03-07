"""Integration tests for egregore pipeline flow."""

from __future__ import annotations

from budget import Budget, load_budget, save_budget
from config import default_config, load_config, save_config
from manifest import Manifest, load_manifest, save_manifest


def test_full_pipeline_advancement():
    """Advance a work item through the entire 16-step pipeline."""
    m = Manifest(project_dir="/tmp/test-project")
    item = m.add_work_item(source="prompt", source_ref="test project")

    steps_seen = []
    while item.status == "active":
        steps_seen.append(f"{item.pipeline_stage}/{item.pipeline_step}")
        m.advance(item.id)

    assert item.status == "completed"
    assert steps_seen[0] == "intake/parse"
    assert steps_seen[-1] == "ship/merge"
    assert len(steps_seen) == 16


def test_roundtrip_all_state(tmp_path):
    """Save and load all three state files."""
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()

    # Manifest
    m = Manifest(project_dir=str(tmp_path))
    m.add_work_item(source="prompt", source_ref="test")
    save_manifest(m, egregore_dir / "manifest.json")
    loaded_m = load_manifest(egregore_dir / "manifest.json")
    assert len(loaded_m.work_items) == 1

    # Config
    cfg = default_config()
    save_config(cfg, egregore_dir / "config.json")
    loaded_cfg = load_config(egregore_dir / "config.json")
    assert loaded_cfg.alerts.on_crash is True

    # Budget
    b = Budget(window_type="7d")
    save_budget(b, egregore_dir / "budget.json")
    loaded_b = load_budget(egregore_dir / "budget.json")
    assert loaded_b.window_type == "7d"


def test_multiple_work_items_pipeline():
    """Process multiple items, first completes then second."""
    m = Manifest(project_dir="/tmp/test-project")
    item1 = m.add_work_item(source="prompt", source_ref="first")
    item2 = m.add_work_item(source="prompt", source_ref="second")

    # Advance item1 through entire pipeline
    while item1.status == "active":
        m.advance(item1.id)
    assert item1.status == "completed"

    # item2 still active
    assert m.next_active_item().id == item2.id

    # Advance item2
    while item2.status == "active":
        m.advance(item2.id)
    assert item2.status == "completed"
    assert m.next_active_item() is None


def test_failure_skips_to_next_item():
    """When an item fails, next_active_item moves on."""
    m = Manifest(project_dir="/tmp/test-project")
    item1 = m.add_work_item(source="prompt", source_ref="will-fail")
    item2 = m.add_work_item(source="prompt", source_ref="will-succeed")

    # Fail item1 three times
    item1.attempts = 3
    item1.max_attempts = 3
    m.fail_current_step(item1.id, reason="test failure")
    assert item1.status == "failed"

    # Next item should be item2
    assert m.next_active_item().id == item2.id
