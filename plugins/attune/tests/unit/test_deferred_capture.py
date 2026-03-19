"""Tests for attune deferred_capture.py wrapper.

Tests validate CLI interface, body template, dry-run output,
and attune-specific context enrichment per the leyline contract.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "deferred_capture.py"


def run_script(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run deferred_capture.py with given args, capture output."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=run_env,
        check=False,
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
            "My attune idea",
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
            "War-room idea",
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
            "brainstorm",
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
        assert "brainstorm" in labels
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
            "brainstorm",
            "--context",
            "Some context",
        )
        assert result.returncode != 0

    def test_title_gets_deferred_prefix(self) -> None:
        """
        Scenario: Plain titles are prefixed with [Deferred]

        Given --title "My attune feature"
        When the script runs with --dry-run
        Then the title in output is "[Deferred] My attune feature"
        """
        result = run_script(
            "--title",
            "My attune feature",
            "--source",
            "brainstorm",
            "--context",
            "Out of scope for now",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] My attune feature"

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
            "war-room",
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
            "brainstorm",
            "--context",
            "Testing default session id",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
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
            "brainstorm",
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


class TestAttuneEnrichment:
    """
    Feature: attune-specific context enrichment

    As an attune skill
    I want war-room items to include the strategeion session path
    So that the deferred issue provides full traceability
    """

    def test_war_room_enriches_context_when_env_set(self) -> None:
        """
        Scenario: war-room source with STRATEGEION_SESSION_DIR set

        Given source is "war-room" and STRATEGEION_SESSION_DIR=/tmp/session
        When the script runs with --dry-run
        Then the body contains the strategeion session path
        """
        result = run_script(
            "--title",
            "War-room enrichment test",
            "--source",
            "war-room",
            "--context",
            "Strategy discussion",
            "--dry-run",
            env={"STRATEGEION_SESSION_DIR": "/tmp/strategeion-test"},
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "/tmp/strategeion-test" in data["body"]

    def test_war_room_no_enrichment_without_env(self) -> None:
        """
        Scenario: war-room source without STRATEGEION_SESSION_DIR set

        Given source is "war-room" and STRATEGEION_SESSION_DIR is unset
        When the script runs with --dry-run
        Then the body does not mention "Strategeion session"
        """
        env = {k: v for k, v in os.environ.items() if k != "STRATEGEION_SESSION_DIR"}
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--title",
                "No enrichment test",
                "--source",
                "war-room",
                "--context",
                "No strategeion env",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "Strategeion session:" not in data["body"]

    def test_brainstorm_source_not_enriched(self) -> None:
        """
        Scenario: brainstorm source is not enriched regardless of env

        Given source is "brainstorm" and STRATEGEION_SESSION_DIR is set
        When the script runs with --dry-run
        Then the body does not contain the strategeion path
        """
        result = run_script(
            "--title",
            "Brainstorm not enriched",
            "--source",
            "brainstorm",
            "--context",
            "Brainstorm context",
            "--dry-run",
            env={"STRATEGEION_SESSION_DIR": "/tmp/strategeion-test"},
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "Strategeion session:" not in data["body"]
