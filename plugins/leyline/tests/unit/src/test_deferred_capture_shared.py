# ruff: noqa: D101,D102,D103,PLR2004,PLC0415,PLW1510,S108,S603,S607
"""Tests for the shared leyline deferred_capture module.

Tests validate helpers, body template, dry-run, argument parsing,
and the run_capture entry point per the deferred-capture contract.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(_SRC))

from leyline.deferred_capture import (
    PluginConfig,
    build_body,
    build_labels,
    build_title,
    find_duplicate,
    get_session_id,
    run_capture,
)

# A minimal config for tests that need one
_TEST_CONFIG = PluginConfig(
    plugin_name="test",
    label_colors={
        "deferred": "#7B61FF",
        "brainstorm": "#1D76DB",
        "war-room": "#B60205",
        "review": "#0E8A16",
        "regression": "#D73A4A",
    },
    source_help="Origin skill",
)

SCRIPT = Path(__file__).resolve().parents[3] / "src" / "leyline"


def _run_via_wrapper(*args: str) -> subprocess.CompletedProcess:
    """Run sanctum wrapper (which delegates to the shared module)."""
    wrapper = (
        Path(__file__).resolve().parents[4]
        / "sanctum"
        / "scripts"
        / "deferred_capture.py"
    )
    return subprocess.run(
        [sys.executable, str(wrapper), *args],
        capture_output=True,
        text=True,
    )


class TestDryRun:
    """Feature: --dry-run prints JSON without creating a GitHub issue."""

    def test_dry_run_outputs_valid_json(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "My feature idea",
            "--source",
            "brainstorm",
            "--context",
            "Came up during session but out of scope",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"

    def test_dry_run_includes_all_fields(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "Another idea",
            "--source",
            "war-room",
            "--context",
            "Discussed but deferred for scope reasons",
            "--session-id",
            "test-session-42",
            "--artifact-path",
            "/tmp/notes.md",
            "--captured-by",
            "safety-net",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["source"] == "war-room"
        assert data["session_id"] == "test-session-42"
        assert "body" in data

    def test_dry_run_with_extra_labels(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "Label test",
            "--source",
            "review",
            "--context",
            "Testing label merge",
            "--labels",
            "needs-design,blocked",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        labels = data["labels"]
        assert "deferred" in labels
        assert "review" in labels
        assert "needs-design" in labels
        assert "blocked" in labels


class TestArgParsing:
    """Feature: Argument parsing follows the contract CLI interface."""

    def test_missing_required_args_fails(self) -> None:
        result = _run_via_wrapper(
            "--source",
            "review",
            "--context",
            "Some context",
        )
        assert result.returncode != 0

    def test_title_gets_deferred_prefix(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "My feature",
            "--source",
            "brainstorm",
            "--context",
            "Out of scope for now",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] My feature"

    def test_title_not_double_prefixed(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "[Deferred] Already prefixed",
            "--source",
            "brainstorm",
            "--context",
            "Pre-prefixed",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] Already prefixed"

    def test_session_id_defaults_to_env_or_timestamp(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "Session id test",
            "--source",
            "regression",
            "--context",
            "Testing default session id",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["session_id"] != ""


class TestBodyTemplate:
    """Feature: Issue body follows the leyline contract template."""

    def test_body_contains_required_sections(self) -> None:
        result = _run_via_wrapper(
            "--title",
            "Body template test",
            "--source",
            "brainstorm",
            "--context",
            "Testing body structure",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        body = json.loads(result.stdout)["body"]
        assert "## Deferred Item" in body
        assert "**Source:**" in body
        assert "### Context" in body
        assert "### Next Steps" in body


# -------------------------------------------------------------------
# Unit tests for helper functions (no subprocess overhead)
# -------------------------------------------------------------------


class TestBuildTitle:
    def test_plain_title_gets_prefix(self) -> None:
        assert build_title("Add OAuth") == "[Deferred] Add OAuth"

    def test_already_prefixed_title_unchanged(self) -> None:
        assert build_title("[Deferred] Add OAuth") == "[Deferred] Add OAuth"

    def test_empty_title(self) -> None:
        assert build_title("") == "[Deferred] "


class TestBuildLabels:
    def test_base_labels_include_deferred_and_source(self) -> None:
        assert build_labels("war-room", []) == ["deferred", "war-room"]

    def test_extras_are_appended(self) -> None:
        labels = build_labels("brainstorm", ["blocked", "needs-design"])
        assert "deferred" in labels
        assert "brainstorm" in labels
        assert "blocked" in labels

    def test_duplicate_labels_are_deduped(self) -> None:
        labels = build_labels("review", ["review", "deferred"])
        assert labels.count("review") == 1
        assert labels.count("deferred") == 1

    def test_whitespace_labels_are_stripped(self) -> None:
        labels = build_labels("review", ["  blocked  ", "", "  "])
        assert "blocked" in labels
        assert "" not in labels


class TestGetSessionId:
    def test_explicit_id_takes_precedence(self) -> None:
        assert get_session_id("my-session-42") == "my-session-42"

    def test_env_var_fallback(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "env-99"}):
            assert get_session_id(None) == "env-99"

    def test_timestamp_fallback(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_SESSION_ID", None)
            sid = get_session_id(None)
        assert len(sid) == 15
        assert "-" in sid


class TestBuildBody:
    def test_body_includes_all_sections(self) -> None:
        with patch(
            "leyline.deferred_capture.get_current_branch",
            return_value="test-branch",
        ):
            body = build_body(
                source="war-room",
                session_id="s-123",
                context="Test context",
                artifact_path="/tmp/artifact.md",
                captured_by="explicit",
            )
        assert "## Deferred Item" in body
        assert "**Source:** war-room" in body
        assert "session s-123" in body
        assert "test-branch" in body
        assert "/tmp/artifact.md" in body

    def test_body_uses_na_when_no_artifact(self) -> None:
        with patch(
            "leyline.deferred_capture.get_current_branch",
            return_value="main",
        ):
            body = build_body(
                source="brainstorm",
                session_id="s-1",
                context="No artifact",
                artifact_path=None,
                captured_by="safety-net",
            )
        assert "N/A" in body


class TestFindDuplicate:
    def test_returns_matching_issue(self) -> None:
        gh_output = json.dumps(
            [{"number": 42, "title": "[Deferred] Add OAuth", "url": "u"}]
        )
        mock = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=gh_output, stderr=""
        )
        with patch("leyline.deferred_capture.subprocess.run", return_value=mock):
            dupe = find_duplicate("Add OAuth")
        assert dupe is not None
        assert dupe["number"] == 42

    def test_returns_none_when_no_match(self) -> None:
        gh_output = json.dumps([{"number": 1, "title": "[Deferred] Other", "url": "u"}])
        mock = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=gh_output, stderr=""
        )
        with patch("leyline.deferred_capture.subprocess.run", return_value=mock):
            assert find_duplicate("Add OAuth") is None

    def test_returns_none_on_gh_failure(self) -> None:
        mock = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error"
        )
        with patch("leyline.deferred_capture.subprocess.run", return_value=mock):
            assert find_duplicate("Add OAuth") is None


class TestRunCaptureWithEnrichment:
    """Feature: run_capture applies plugin-specific context enrichment."""

    def test_enrich_context_is_called(self) -> None:
        def _enrich(source: str, ctx: str) -> str:
            return f"{ctx}\n\nENRICHED by {source}"

        config = PluginConfig(
            plugin_name="test",
            label_colors={"deferred": "#7B61FF", "brainstorm": "#1D76DB"},
            enrich_context=_enrich,
        )
        with patch(
            "leyline.deferred_capture.get_current_branch",
            return_value="test",
        ):
            rc = run_capture(
                config,
                [
                    "--title",
                    "T",
                    "--source",
                    "brainstorm",
                    "--context",
                    "Base",
                    "--dry-run",
                ],
            )
        assert rc == 0

    def test_no_enrich_context_is_fine(self) -> None:
        config = PluginConfig(
            plugin_name="test",
            label_colors={"deferred": "#7B61FF"},
        )
        with patch(
            "leyline.deferred_capture.get_current_branch",
            return_value="test",
        ):
            rc = run_capture(
                config,
                ["--title", "T", "--source", "x", "--context", "C", "--dry-run"],
            )
        assert rc == 0
