"""Regression tests for rollout collateral documentation."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read_text(relative_path: str) -> str:
    """Load a repository file as UTF-8 text."""
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_rollout_docs_cover_required_sections() -> None:
    """Rollout documentation should include required sections and links."""
    dry_run_doc = _read_text("docs/runbooks/memory-palace-rollout-dry-run.md")
    assert "# Dry Run Transcript" in dry_run_doc
    assert "## Validation Checklist" in dry_run_doc

    cache_dashboard = _read_text("docs/metrics/cache-hit-dashboard.md")
    assert "## KPIs" in cache_dashboard
    assert "Rollback Guide" in cache_dashboard

    autonomy_dashboard = _read_text("docs/metrics/autonomy-dashboard.md")
    assert "## Escalation Criteria" in autonomy_dashboard
    assert "## Recovery Actions" in autonomy_dashboard

    rollout_playbook = _read_text("docs/runbooks/memory-palace-rollout.md")
    assert "memory-palace-rollout-dry-run.md" in rollout_playbook
    assert "cache-hit-dashboard.md" in rollout_playbook
    assert "autonomy-dashboard.md" in rollout_playbook

    telemetry_log = _read_text(
        "plugins/memory-palace/telemetry/dry_runs/cache-intercept-staging.md"
    )
    assert "memory-palace-rollout-dry-run.md" in telemetry_log
