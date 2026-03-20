# ruff: noqa: D101,D102,D103,S603,S607
"""Tests for imbue deferred_capture.py wrapper.

Validates plugin-specific config and enrichment. Shared logic
is tested in plugins/leyline/tests/unit/src/test_deferred_capture.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "deferred_capture.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestImbueConfig:
    """Feature: imbue wrapper uses correct labels and enrichment."""

    def test_dry_run_produces_valid_json(self) -> None:
        result = _run(
            "--title",
            "Test",
            "--source",
            "scope-guard",
            "--context",
            "ctx",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"

    def test_labels_include_imbue_sources(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "scope-guard",
            "--context",
            "c",
            "--dry-run",
        )
        labels = json.loads(result.stdout)["labels"]
        assert "deferred" in labels
        assert "scope-guard" in labels

    def test_scope_guard_enrichment(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "scope-guard",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "worthiness scoring" in body

    def test_no_enrichment_for_feature_review(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "feature-review",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "worthiness scoring" not in body
