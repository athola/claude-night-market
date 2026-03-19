"""Tests for imbue deferred_capture.py wrapper.

Tests validate CLI interface, body template, dry-run output,
and imbue-specific context enrichment per the leyline contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "deferred_capture.py"


def run_script(*args: str) -> subprocess.CompletedProcess:
    """Run deferred_capture.py with given args, capture output."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
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
            "My scope-guard deferral",
            "--source",
            "scope-guard",
            "--context",
            "Out of scope for current sprint",
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
            "Feature review item",
            "--source",
            "feature-review",
            "--context",
            "Needs more design work",
            "--session-id",
            "imbue-session-7",
            "--artifact-path",
            "/tmp/spec.md",
            "--captured-by",
            "safety-net",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["source"] == "feature-review"
        assert data["session_id"] == "imbue-session-7"
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
            "scope-guard",
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
        assert "scope-guard" in labels
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
            "scope-guard",
            "--context",
            "Some context",
        )
        assert result.returncode != 0

    def test_title_gets_deferred_prefix(self) -> None:
        """
        Scenario: Plain titles are prefixed with [Deferred]

        Given --title "My imbue feature"
        When the script runs with --dry-run
        Then the title in output is "[Deferred] My imbue feature"
        """
        result = run_script(
            "--title",
            "My imbue feature",
            "--source",
            "scope-guard",
            "--context",
            "Out of scope for now",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] My imbue feature"

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
            "feature-review",
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
            "scope-guard",
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
            "scope-guard",
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


class TestImbueEnrichment:
    """
    Feature: imbue-specific context enrichment

    As an imbue skill
    I want scope-guard items to note that worthiness scoring applies
    So that triagers know to apply the worthiness rubric
    """

    def test_scope_guard_enriches_context(self) -> None:
        """
        Scenario: scope-guard source adds worthiness scoring note

        Given source is "scope-guard" and --dry-run
        When the script runs
        Then the body contains the worthiness scoring note
        """
        result = run_script(
            "--title",
            "Worthiness scoring test",
            "--source",
            "scope-guard",
            "--context",
            "Feature request from user",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "worthiness scoring" in data["body"]

    def test_feature_review_source_not_enriched(self) -> None:
        """
        Scenario: feature-review source does not add worthiness note

        Given source is "feature-review" and --dry-run
        When the script runs
        Then the body does not contain the worthiness scoring note
        """
        result = run_script(
            "--title",
            "Feature review item",
            "--source",
            "feature-review",
            "--context",
            "Needs more design work",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "worthiness scoring" not in data["body"]
