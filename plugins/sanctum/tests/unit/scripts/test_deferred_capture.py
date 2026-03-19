# ruff: noqa: D101,D102,D103,PLR2004,PLC0415,PLW1510,S108,S603,S607
"""Tests for deferred_capture.py reference implementation.

Tests validate CLI interface, body template, dry-run output,
argument parsing, and helper functions per the leyline
deferred-capture contract.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parents[3] / "scripts" / "deferred_capture.py"
sys.path.insert(0, str(SCRIPT.parent))


def run_script(*args: str) -> subprocess.CompletedProcess:
    """Run deferred_capture.py with given args, capture output."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestDryRun:
    """
    Feature: --dry-run prints JSON without creating a GitHub issue

    As a plugin author
    I want to verify the script output without side effects
    So that I can test integrations safely
    """

    def test_dry_run_outputs_valid_json(self) -> None:
        """
        Scenario: --dry-run produces parseable JSON with status=dry_run

        Given valid required arguments and --dry-run
        When the script runs
        Then stdout is valid JSON with status="dry_run"
        """
        result = run_script(
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
        """
        Scenario: --dry-run output includes source, session_id, and body

        Given all optional arguments plus --dry-run
        When the script runs
        Then the JSON contains source, session_id, and body fields
        """
        result = run_script(
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
        assert "source" in data
        assert "session_id" in data
        assert "body" in data
        assert data["source"] == "war-room"
        assert data["session_id"] == "test-session-42"

    def test_dry_run_with_extra_labels(self) -> None:
        """
        Scenario: Extra --labels are merged with deferred + source

        Given --labels with extra values and --dry-run
        When the script runs
        Then the labels list contains deferred, source, and the extras
        """
        result = run_script(
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
    """
    Feature: Argument parsing follows the contract CLI interface

    As a caller script
    I want predictable argument behavior
    So that wrappers can rely on consistent behavior
    """

    def test_missing_required_args_fails(self) -> None:
        """
        Scenario: Omitting --title causes a non-zero exit

        Given no --title argument
        When the script runs
        Then it exits with a non-zero return code
        """
        result = run_script(
            "--source",
            "review",
            "--context",
            "Some context",
        )
        assert result.returncode != 0

    def test_title_gets_deferred_prefix(self) -> None:
        """
        Scenario: Plain titles are prefixed with [Deferred]

        Given --title "My feature"
        When the script runs with --dry-run
        Then the title in output is "[Deferred] My feature"
        """
        result = run_script(
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
        """
        Scenario: Titles already prefixed are not double-prefixed

        Given --title "[Deferred] Already prefixed"
        When the script runs with --dry-run
        Then the title remains "[Deferred] Already prefixed"
        """
        result = run_script(
            "--title",
            "[Deferred] Already prefixed",
            "--source",
            "scope-guard",
            "--context",
            "Pre-prefixed title",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] Already prefixed"

    def test_session_id_defaults_to_env_or_timestamp(self) -> None:
        """
        Scenario: session_id is non-empty when not explicitly provided

        Given no --session-id argument
        When the script runs with --dry-run
        Then session_id in output is a non-empty string
        """
        result = run_script(
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
        assert "session_id" in data
        assert data["session_id"] != ""


class TestBodyTemplate:
    """
    Feature: Issue body follows the leyline contract template

    As a consumer of deferred issues
    I want consistent body structure
    So that triaging deferred items is predictable
    """

    def test_body_contains_required_sections(self) -> None:
        """
        Scenario: Body includes all required sections from the contract

        Given valid arguments and --dry-run
        When the script runs
        Then the body contains all required section headers and fields
        """
        result = run_script(
            "--title",
            "Body template test",
            "--source",
            "egregore",
            "--context",
            "Testing body structure",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        body = data["body"]
        assert "## Deferred Item" in body
        assert "**Source:**" in body
        assert "### Context" in body
        assert "### Next Steps" in body


# ---------------------------------------------------------------------------
# Unit tests for helper functions (no subprocess overhead)
# ---------------------------------------------------------------------------


class TestBuildTitle:
    """Unit tests for build_title() prefix logic."""

    def test_plain_title_gets_prefix(self) -> None:
        """Plain title is prefixed with [Deferred]."""
        from deferred_capture import build_title

        assert build_title("Add OAuth") == "[Deferred] Add OAuth"

    def test_already_prefixed_title_unchanged(self) -> None:
        """Title starting with [Deferred] is returned as-is."""
        from deferred_capture import build_title

        assert build_title("[Deferred] Add OAuth") == "[Deferred] Add OAuth"

    def test_empty_title(self) -> None:
        """Empty string gets the prefix."""
        from deferred_capture import build_title

        assert build_title("") == "[Deferred] "


class TestBuildLabels:
    """Unit tests for build_labels() deduplication."""

    def test_base_labels_include_deferred_and_source(self) -> None:
        """Labels always include 'deferred' and the source."""
        from deferred_capture import build_labels

        labels = build_labels("war-room", [])
        assert labels == ["deferred", "war-room"]

    def test_extras_are_appended(self) -> None:
        """Extra labels are appended after deferred + source."""
        from deferred_capture import build_labels

        labels = build_labels("brainstorm", ["blocked", "needs-design"])
        assert "deferred" in labels
        assert "brainstorm" in labels
        assert "blocked" in labels
        assert "needs-design" in labels

    def test_duplicate_labels_are_deduped(self) -> None:
        """Duplicate labels in extras are removed."""
        from deferred_capture import build_labels

        labels = build_labels("review", ["review", "deferred"])
        assert labels.count("review") == 1
        assert labels.count("deferred") == 1

    def test_whitespace_labels_are_stripped(self) -> None:
        """Labels with whitespace are stripped; empty strings are excluded."""
        from deferred_capture import build_labels

        labels = build_labels("review", ["  blocked  ", "", "  "])
        assert "blocked" in labels
        assert "" not in labels


class TestGetSessionId:
    """Unit tests for get_session_id() fallback chain."""

    def test_explicit_id_takes_precedence(self) -> None:
        """An explicitly provided session ID is used as-is."""
        from deferred_capture import get_session_id

        assert get_session_id("my-session-42") == "my-session-42"

    def test_env_var_fallback(self) -> None:
        """Falls back to CLAUDE_SESSION_ID when no explicit ID."""
        from deferred_capture import get_session_id

        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "env-session-99"}):
            assert get_session_id(None) == "env-session-99"

    def test_timestamp_fallback(self) -> None:
        """Falls back to a UTC timestamp when no explicit ID and no env var."""
        from deferred_capture import get_session_id

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_SESSION_ID", None)
            sid = get_session_id(None)
        # Timestamp format: YYYYMMDD-HHMMSS
        assert len(sid) == 15
        assert "-" in sid


class TestBuildBody:
    """Unit tests for build_body() template rendering."""

    def test_body_includes_all_sections(self) -> None:
        """Body contains all required sections from the contract."""
        from deferred_capture import build_body

        with patch("deferred_capture.get_current_branch", return_value="test-branch"):
            body = build_body(
                source="war-room",
                session_id="s-123",
                context="Test context for deferral",
                artifact_path="/tmp/artifact.md",
                captured_by="explicit",
            )
        assert "## Deferred Item" in body
        assert "**Source:** war-room" in body
        assert "session s-123" in body
        assert "test-branch" in body
        assert "Test context for deferral" in body
        assert "/tmp/artifact.md" in body
        assert "**Captured by:** explicit" in body
        assert "### Next Steps" in body

    def test_body_uses_na_when_no_artifact(self) -> None:
        """Artifact path shows N/A when not provided."""
        from deferred_capture import build_body

        with patch("deferred_capture.get_current_branch", return_value="main"):
            body = build_body(
                source="brainstorm",
                session_id="s-1",
                context="No artifact",
                artifact_path=None,
                captured_by="safety-net",
            )
        assert "N/A" in body


class TestFindDuplicate:
    """Unit tests for find_duplicate() with mocked gh CLI."""

    def test_returns_matching_issue(self) -> None:
        """Returns the matching issue when title matches (case-insensitive)."""
        from deferred_capture import find_duplicate

        gh_output = json.dumps(
            [
                {
                    "number": 42,
                    "title": "[Deferred] Add OAuth",
                    "url": "https://example.com/42",
                }
            ]
        )
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=gh_output, stderr=""
        )
        with patch("deferred_capture.subprocess.run", return_value=mock_result):
            dupe = find_duplicate("Add OAuth")
        assert dupe is not None
        assert dupe["number"] == 42

    def test_returns_none_when_no_match(self) -> None:
        """Returns None when no title matches."""
        from deferred_capture import find_duplicate

        gh_output = json.dumps(
            [
                {
                    "number": 1,
                    "title": "[Deferred] Something else",
                    "url": "https://example.com/1",
                }
            ]
        )
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=gh_output, stderr=""
        )
        with patch("deferred_capture.subprocess.run", return_value=mock_result):
            dupe = find_duplicate("Add OAuth")
        assert dupe is None

    def test_returns_none_on_gh_failure(self) -> None:
        """Returns None when gh exits non-zero."""
        from deferred_capture import find_duplicate

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error"
        )
        with patch("deferred_capture.subprocess.run", return_value=mock_result):
            dupe = find_duplicate("Add OAuth")
        assert dupe is None
