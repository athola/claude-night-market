# ruff: noqa: D101,D102,D103,S603,S607
"""Tests for sanctum deferred_capture.py wrapper (reference implementation).

Validates the sanctum wrapper delegates correctly to the shared
leyline module with the full label taxonomy. Comprehensive shared
logic tests live in plugins/leyline/tests/unit/src/test_deferred_capture.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "deferred_capture.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestSanctumConfig:
    """Feature: sanctum wrapper uses the full label taxonomy."""

    def test_dry_run_produces_valid_json(self) -> None:
        result = _run(
            "--title",
            "Test",
            "--source",
            "brainstorm",
            "--context",
            "ctx",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"

    def test_labels_include_all_sources(self) -> None:
        """Sanctum uses the full label taxonomy from the contract."""
        for source in [
            "war-room",
            "brainstorm",
            "scope-guard",
            "feature-review",
            "review",
            "regression",
            "egregore",
        ]:
            result = _run(
                "--title",
                "T",
                "--source",
                source,
                "--context",
                "c",
                "--dry-run",
            )
            labels = json.loads(result.stdout)["labels"]
            assert "deferred" in labels
            assert source in labels, f"{source} not in labels"

    def test_extra_labels_merged(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "review",
            "--context",
            "c",
            "--labels",
            "blocked,needs-design",
            "--dry-run",
        )
        labels = json.loads(result.stdout)["labels"]
        assert "blocked" in labels
        assert "needs-design" in labels

    def test_title_gets_deferred_prefix(self) -> None:
        result = _run(
            "--title",
            "My feature",
            "--source",
            "brainstorm",
            "--context",
            "ctx",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] My feature"

    def test_body_contains_required_sections(self) -> None:
        result = _run(
            "--title",
            "Body test",
            "--source",
            "war-room",
            "--context",
            "Testing body",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "## Deferred Item" in body
        assert "**Source:**" in body
        assert "### Context" in body
        assert "### Next Steps" in body

    def test_missing_required_args_fails(self) -> None:
        result = _run("--source", "review", "--context", "c")
        assert result.returncode != 0

    def test_no_enrichment_applied(self) -> None:
        """Sanctum has no enrich_context — body matches raw context."""
        result = _run(
            "--title",
            "T",
            "--source",
            "brainstorm",
            "--context",
            "Raw context only",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "Raw context only" in body
        # No enrichment markers from other plugins
        assert "regression detection" not in body
        assert "worthiness scoring" not in body
        assert "pipeline step" not in body
