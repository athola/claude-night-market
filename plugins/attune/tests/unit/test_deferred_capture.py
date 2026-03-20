# ruff: noqa: D101,D102,D103,S603,S607
"""Tests for attune deferred_capture.py wrapper.

Validates plugin-specific config and enrichment. Shared logic
is tested in plugins/leyline/tests/unit/src/test_deferred_capture.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "deferred_capture.py"


def _run(*args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )


class TestAttuneConfig:
    """Feature: attune wrapper uses correct labels and enrichment."""

    def test_dry_run_produces_valid_json(self) -> None:
        result = _run(
            "--title",
            "Test",
            "--source",
            "war-room",
            "--context",
            "ctx",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"

    def test_labels_include_attune_sources(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "war-room",
            "--context",
            "c",
            "--dry-run",
        )
        labels = json.loads(result.stdout)["labels"]
        assert "deferred" in labels
        assert "war-room" in labels

    def test_war_room_enrichment_with_session_dir(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "war-room",
            "--context",
            "Base",
            "--dry-run",
            env_extra={"STRATEGEION_SESSION_DIR": "/tmp/session"},
        )
        body = json.loads(result.stdout)["body"]
        assert "Strategeion session: /tmp/session" in body

    def test_no_enrichment_without_session_dir(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "brainstorm",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "Strategeion session" not in body
