"""Tests for egregore deferred_capture.py wrapper.

Tests validate CLI interface, body template, dry-run output,
and egregore-specific context enrichment per the leyline contract.
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
            "Autonomous agent finding",
            "--source",
            "egregore",
            "--context",
            "Detected during autonomous pipeline run",
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
            "Pipeline finding",
            "--source",
            "egregore",
            "--context",
            "Needs human review",
            "--session-id",
            "egregore-session-12",
            "--artifact-path",
            "/tmp/pipeline.log",
            "--captured-by",
            "safety-net",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["source"] == "egregore"
        assert data["session_id"] == "egregore-session-12"
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
            "Label merge test",
            "--source",
            "egregore",
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
        assert "egregore" in labels
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
            "egregore",
            "--context",
            "Some context",
        )
        assert result.returncode != 0

    def test_title_gets_deferred_prefix(self) -> None:
        """
        Scenario: Plain titles are prefixed with [Deferred]

        Given --title "My egregore finding"
        When the script runs with --dry-run
        Then the title in output is "[Deferred] My egregore finding"
        """
        result = run_script(
            "--title",
            "My egregore finding",
            "--source",
            "egregore",
            "--context",
            "Out of scope for now",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] My egregore finding"

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
            "egregore",
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
            "egregore",
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


class TestEgregoreEnrichment:
    """
    Feature: egregore-specific context enrichment

    As an egregore pipeline
    I want deferred items to include the pipeline step context
    So that triagers know at which step the item was captured
    """

    def test_egregore_step_enriches_context_when_env_set(self) -> None:
        """
        Scenario: EGREGORE_STEP env var is appended to context

        Given EGREGORE_STEP=harvest and --dry-run
        When the script runs
        Then the body contains the pipeline step name
        """
        result = run_script(
            "--title",
            "Pipeline step enrichment test",
            "--source",
            "egregore",
            "--context",
            "Found during pipeline",
            "--dry-run",
            env={"EGREGORE_STEP": "harvest"},
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "harvest" in data["body"]

    def test_no_enrichment_without_env(self) -> None:
        """
        Scenario: EGREGORE_STEP not set means no pipeline step in body

        Given EGREGORE_STEP is unset and --dry-run
        When the script runs
        Then the body does not contain "Egregore pipeline step:"
        """
        env = {k: v for k, v in os.environ.items() if k != "EGREGORE_STEP"}
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--title",
                "No step enrichment test",
                "--source",
                "egregore",
                "--context",
                "No EGREGORE_STEP set",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "Egregore pipeline step:" not in data["body"]

    def test_step_enrichment_applies_to_all_sources(self) -> None:
        """
        Scenario: EGREGORE_STEP enrichment applies regardless of source

        Given EGREGORE_STEP=scout and source is "test"
        When the script runs with --dry-run
        Then the body contains the pipeline step name
        """
        result = run_script(
            "--title",
            "Cross-source enrichment",
            "--source",
            "test",
            "--context",
            "Testing step enrichment",
            "--dry-run",
            env={"EGREGORE_STEP": "scout"},
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "scout" in data["body"]
