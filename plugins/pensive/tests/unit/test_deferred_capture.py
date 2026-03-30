# ruff: noqa: D101,D102,D103,S603,S607
"""Tests for pensive deferred_capture.py wrapper.

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
        check=False,
    )


class TestPensiveConfig:
    """Feature: pensive wrapper uses correct labels and enrichment."""

    def test_dry_run_produces_valid_json(self) -> None:
        result = _run(
            "--title",
            "Test",
            "--source",
            "review",
            "--context",
            "ctx",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"

    def test_labels_include_review(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "review",
            "--context",
            "c",
            "--dry-run",
        )
        labels = json.loads(result.stdout)["labels"]
        assert "deferred" in labels
        assert "review" in labels

    def test_review_enrichment(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "review",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "code/PR review findings" in body

    def test_no_enrichment_for_other_sources(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "deferred",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "review findings" not in body
