"""Tests for the coordination workspace manager.

Tests workspace initialization, findings file parsing,
selective synthesis, archive, and cleanup.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from scripts.coordination_workspace import (
    WorkspaceManager,
    parse_findings_file,
)

# --------------- workspace lifecycle ---------------


class TestWorkspaceLifecycle:
    """Feature: Manage .coordination/ workspace directory.

    As a multi-agent coordinator
    I want a structured workspace for agent findings
    So that agents write to files instead of parent context.
    """

    @pytest.mark.unit
    def test_init_creates_directory_structure(self, tmp_path: Path) -> None:
        """Given an empty directory, init creates the workspace."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()

        assert (tmp_path / ".coordination").is_dir()
        assert (tmp_path / ".coordination" / "agents").is_dir()
        assert (tmp_path / ".coordination" / "handoffs").is_dir()
        assert (tmp_path / ".coordination" / "tasks.json").is_file()

    @pytest.mark.unit
    def test_init_is_idempotent(self, tmp_path: Path) -> None:
        """Given an existing workspace, init does not fail or overwrite."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()
        # Write a task
        tasks_path = tmp_path / ".coordination" / "tasks.json"
        tasks_path.write_text(json.dumps([{"id": "t1"}]))

        # Re-init should not overwrite
        ws.init()
        tasks = json.loads(tasks_path.read_text())
        assert tasks == [{"id": "t1"}]

    @pytest.mark.unit
    def test_tasks_json_schema(self, tmp_path: Path) -> None:
        """Given a fresh workspace, tasks.json is an empty array."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()
        tasks = json.loads((tmp_path / ".coordination" / "tasks.json").read_text())
        assert tasks == []

    @pytest.mark.unit
    def test_archive_on_success(self, tmp_path: Path) -> None:
        """Given a completed workspace, archive moves it."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()
        # Add a findings file
        (tmp_path / ".coordination" / "agents" / "test.findings.md").write_text(
            "## Summary\nDone."
        )

        archive_path = ws.archive()

        assert not (tmp_path / ".coordination").exists()
        assert archive_path.exists()
        assert (archive_path / "agents" / "test.findings.md").exists()

    @pytest.mark.unit
    def test_preserve_on_failure(self, tmp_path: Path) -> None:
        """Given a failed workflow, preserve adds failure reason."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()

        ws.preserve_on_failure("Agent timed out")

        assert (tmp_path / ".coordination").exists()
        reason_file = tmp_path / ".coordination" / "_failure_reason.md"
        assert reason_file.exists()
        assert "Agent timed out" in reason_file.read_text()


# --------------- findings file parsing ---------------


class TestFindingsFileParsing:
    """Feature: Parse structured agent findings files.

    As a synthesizer
    I want to parse findings with frontmatter
    So that I can read summaries without loading full detail.
    """

    @pytest.mark.unit
    def test_parse_complete_findings(self) -> None:
        """Given a well-formed findings file, parse all fields."""
        text = textwrap.dedent("""\
            ---
            agent: reviewer
            area: plugins/imbue
            tier: 2
            evidence_count: 5
            validation_status: PASS
            ---

            ## Summary

            Found 2 issues in validation logic.

            ## Detailed Findings

            Issue details here.

            [E1] Command: grep -n "def validate" src/v.py
                 Output: 42: def validate(self):

            ## Evidence

            See above.
        """)
        result = parse_findings_file(text)
        assert result.agent == "reviewer"
        assert result.area == "plugins/imbue"
        assert result.tier == 2
        assert result.evidence_count == 5
        assert "Found 2 issues" in result.summary

    @pytest.mark.unit
    def test_parse_extracts_summary_section(self) -> None:
        """Given findings with summary, extract only summary text."""
        text = textwrap.dedent("""\
            ---
            agent: auditor
            ---

            ## Summary

            This is the summary.
            It has two lines.

            ## Detailed Findings

            This should NOT be in the summary.
        """)
        result = parse_findings_file(text)
        assert "This is the summary" in result.summary
        assert "NOT be in the summary" not in result.summary

    @pytest.mark.unit
    def test_parse_handles_missing_frontmatter(self) -> None:
        """Given findings without frontmatter, use defaults."""
        text = "## Summary\n\nJust a summary.\n"
        result = parse_findings_file(text)
        assert result.agent == "unknown"
        assert result.summary == "Just a summary."


# --------------- task manifest ---------------


class TestTaskManifest:
    """Feature: Track agent tasks in tasks.json.

    As a coordinator
    I want to track task status per agent
    So that I know what's done and what's pending.
    """

    @pytest.mark.unit
    def test_add_task(self, tmp_path: Path) -> None:
        """Given a workspace, add a task to the manifest."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()
        ws.add_task(
            task_id="t1",
            agent="reviewer",
            contract_ref="code-review",
        )
        tasks = ws.load_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == "t1"
        assert tasks[0]["agent"] == "reviewer"
        assert tasks[0]["status"] == "pending"

    @pytest.mark.unit
    def test_update_task_status(self, tmp_path: Path) -> None:
        """Given a pending task, update its status to done."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()
        ws.add_task(task_id="t1", agent="reviewer")
        ws.update_task_status("t1", "done")
        tasks = ws.load_tasks()
        assert tasks[0]["status"] == "done"

    @pytest.mark.unit
    def test_list_pending_tasks(self, tmp_path: Path) -> None:
        """Given mixed task statuses, list only pending."""
        ws = WorkspaceManager(tmp_path / ".coordination")
        ws.init()
        ws.add_task(task_id="t1", agent="a")
        ws.add_task(task_id="t2", agent="b")
        ws.update_task_status("t1", "done")
        pending = ws.pending_tasks()
        assert len(pending) == 1
        assert pending[0]["id"] == "t2"
