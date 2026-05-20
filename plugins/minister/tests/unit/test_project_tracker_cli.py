# ruff: noqa: D101,D102,D103,D205,D212,PLR2004,E501
"""Unit tests for the project_tracker CLI surface.

Targets the uncovered CLI block (lines 285-471 of project_tracker.py):
build_cli_parser, _collect_updates, run_cli, _output_result, _output_error.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from minister import project_tracker as pt_module
from minister.project_tracker import (
    ProjectTracker,
    Task,
    _collect_updates,
    _output_error,
    _output_result,
    build_cli_parser,
    run_cli,
)

# =============================================================================
# build_cli_parser
# =============================================================================


class TestBuildCliParser:
    """Feature: CLI parser wiring."""

    @pytest.mark.unit
    def test_returns_argument_parser(self) -> None:
        parser = build_cli_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @pytest.mark.unit
    def test_add_subcommand_requires_required_args(self) -> None:
        parser = build_cli_parser()
        # All these flags are required for `add`; exit on missing
        with pytest.raises(SystemExit):
            parser.parse_args(["add", "--id", "X"])

    @pytest.mark.unit
    def test_add_subcommand_accepts_full_args(self) -> None:
        parser = build_cli_parser()
        args = parser.parse_args(
            [
                "add",
                "--id",
                "T1",
                "--title",
                "Title",
                "--initiative",
                "Init",
                "--phase",
                "Phase 1",
                "--priority",
                "High",
                "--owner",
                "alice",
                "--effort",
                "2.5",
                "--due",
                "2026-12-31",
                "--github-issue",
                "https://github.com/org/repo/issues/9",
            ]
        )
        assert args.command == "add"
        assert args.id == "T1"
        assert args.effort == 2.5
        assert args.github_issue == "https://github.com/org/repo/issues/9"

    @pytest.mark.unit
    def test_invalid_phase_choice_rejected(self) -> None:
        parser = build_cli_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "add",
                    "--id",
                    "T",
                    "--title",
                    "T",
                    "--initiative",
                    "I",
                    "--phase",
                    "Phase 4",  # invalid
                    "--priority",
                    "High",
                    "--owner",
                    "o",
                    "--effort",
                    "1",
                    "--due",
                    "2026-01-01",
                ]
            )

    @pytest.mark.unit
    def test_update_subcommand_requires_id(self) -> None:
        parser = build_cli_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["update", "--status", "Done"])

    @pytest.mark.unit
    def test_status_subcommand_supports_github_comment_flag(self) -> None:
        parser = build_cli_parser()
        args = parser.parse_args(["status", "--github-comment"])
        assert args.command == "status"
        assert args.github_comment is True

    @pytest.mark.unit
    def test_export_subcommand_requires_output(self) -> None:
        parser = build_cli_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["export"])

    @pytest.mark.unit
    def test_output_json_is_global_flag(self) -> None:
        parser = build_cli_parser()
        args = parser.parse_args(["--output-json", "status"])
        assert args.output_json is True


# =============================================================================
# _collect_updates
# =============================================================================


class TestCollectUpdates:
    """Feature: Build updates dict from CLI args."""

    @pytest.mark.unit
    def test_collects_status(self) -> None:
        ns = argparse.Namespace(status="Done", completion=None, github_issue=None)
        assert _collect_updates(ns) == {"status": "Done"}

    @pytest.mark.unit
    def test_collects_completion(self) -> None:
        ns = argparse.Namespace(status=None, completion=75.0, github_issue=None)
        assert _collect_updates(ns) == {"completion_percent": 75.0}

    @pytest.mark.unit
    def test_collects_github_issue(self) -> None:
        ns = argparse.Namespace(status=None, completion=None, github_issue="#42")
        assert _collect_updates(ns) == {"github_issue": "#42"}

    @pytest.mark.unit
    def test_collects_all_three(self) -> None:
        ns = argparse.Namespace(status="In Progress", completion=50.0, github_issue="x")
        out = _collect_updates(ns)
        assert out == {
            "status": "In Progress",
            "completion_percent": 50.0,
            "github_issue": "x",
        }

    @pytest.mark.unit
    def test_empty_when_all_unset(self) -> None:
        ns = argparse.Namespace(status=None, completion=None, github_issue=None)
        assert _collect_updates(ns) == {}

    @pytest.mark.unit
    def test_completion_zero_is_kept(self) -> None:
        # 0.0 is a valid completion value distinct from None
        ns = argparse.Namespace(status=None, completion=0.0, github_issue=None)
        assert _collect_updates(ns) == {"completion_percent": 0.0}


# =============================================================================
# _output_result / _output_error formatters
# =============================================================================


class TestOutputFormatters:
    """Feature: Result and error output formatting."""

    @pytest.mark.unit
    def test_result_human_readable_format(self, capsys) -> None:
        ns = argparse.Namespace(output_json=False)
        _output_result({"command": "add", "task_id": "T1", "title": "Hello"}, ns)
        captured = capsys.readouterr().out
        assert "'add' completed successfully" in captured
        assert "task_id: T1" in captured
        assert "title: Hello" in captured

    @pytest.mark.unit
    def test_result_json_format(self, capsys) -> None:
        ns = argparse.Namespace(output_json=True)
        _output_result({"command": "x", "value": 42}, ns)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["success"] is True
        assert parsed["data"]["command"] == "x"
        assert parsed["data"]["value"] == 42

    @pytest.mark.unit
    def test_result_json_handles_non_serialisable_via_default_str(
        self, capsys, tmp_path: Path
    ) -> None:
        ns = argparse.Namespace(output_json=True)
        # Path objects are not JSON-serialisable but default=str handles them
        weird = tmp_path / "marker"
        _output_result({"command": "x", "path": weird}, ns)
        parsed = json.loads(capsys.readouterr().out)
        assert str(weird) in parsed["data"]["path"]

    @pytest.mark.unit
    def test_error_human_readable_to_stderr(self, capsys) -> None:
        ns = argparse.Namespace(output_json=False)
        _output_error("oops", ns)
        cap = capsys.readouterr()
        assert cap.err.startswith("Error: oops")

    @pytest.mark.unit
    def test_error_json_to_stdout(self, capsys) -> None:
        ns = argparse.Namespace(output_json=True)
        _output_error("bad", ns)
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["success"] is False
        assert parsed["error"] == "bad"


# =============================================================================
# run_cli end-to-end with patched ProjectTracker
# =============================================================================


@pytest.fixture
def patched_tracker(monkeypatch, tmp_path):
    """Patch ProjectTracker to write to an isolated tmp data file.

    Returns the data_file path so tests can inspect persisted state.
    """
    data_file = tmp_path / "project-data.json"
    real_init = ProjectTracker.__init__

    def patched_init(self, data_file_arg=None, initiatives=None):
        real_init(self, data_file=data_file, initiatives=initiatives)

    monkeypatch.setattr(ProjectTracker, "__init__", patched_init)
    return data_file


class TestRunCli:
    """Feature: CLI dispatch via run_cli."""

    @pytest.mark.unit
    def test_no_command_prints_help_returns_zero(self, capsys) -> None:
        code = run_cli([])
        assert code == 0
        # Help output mentions the subcommands
        out = capsys.readouterr().out
        assert "add" in out and "update" in out

    @pytest.mark.unit
    def test_add_command_persists_task(self, patched_tracker: Path, capsys) -> None:
        code = run_cli(
            [
                "--output-json",
                "add",
                "--id",
                "TSK-CLI-1",
                "--title",
                "From CLI",
                "--initiative",
                "Test Init",
                "--phase",
                "Phase 1",
                "--priority",
                "Medium",
                "--owner",
                "tester",
                "--effort",
                "1.5",
                "--due",
                "2026-12-31",
            ]
        )
        assert code == 0
        # File written
        assert patched_tracker.exists()
        data = json.loads(patched_tracker.read_text())
        assert any(t["id"] == "TSK-CLI-1" for t in data["tasks"])
        # Output is JSON success
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["success"] is True

    @pytest.mark.unit
    def test_update_command_with_no_fields_emits_message(
        self, patched_tracker: Path, capsys
    ) -> None:
        # Seed a task first
        tracker = ProjectTracker()
        tracker.add_task(
            Task(
                id="U1",
                title="t",
                initiative="i",
                phase="Phase 1",
                priority="High",
                status="To Do",
                owner="o",
                effort_hours=1.0,
                completion_percent=0.0,
                due_date="2026-01-01",
                created_date="2026-01-01",
                updated_date="2026-01-01",
            )
        )
        capsys.readouterr()  # clear

        code = run_cli(["--output-json", "update", "--id", "U1"])
        assert code == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["data"]["message"] == "No updates specified"

    @pytest.mark.unit
    def test_update_command_with_status_writes_change(
        self, patched_tracker: Path, capsys
    ) -> None:
        tracker = ProjectTracker()
        tracker.add_task(
            Task(
                id="U2",
                title="t",
                initiative="i",
                phase="Phase 1",
                priority="High",
                status="To Do",
                owner="o",
                effort_hours=1.0,
                completion_percent=0.0,
                due_date="2026-01-01",
                created_date="2026-01-01",
                updated_date="2026-01-01",
            )
        )
        capsys.readouterr()
        code = run_cli(["--output-json", "update", "--id", "U2", "--status", "Done"])
        assert code == 0
        data = json.loads(patched_tracker.read_text())
        match = next(t for t in data["tasks"] if t["id"] == "U2")
        assert match["status"] == "Done"

    @pytest.mark.unit
    def test_status_command_human_readable(self, patched_tracker: Path, capsys) -> None:
        code = run_cli(["status"])
        assert code == 0
        out = capsys.readouterr().out
        assert "'status' completed successfully" in out

    @pytest.mark.unit
    def test_status_github_comment_prints_markdown(
        self, patched_tracker: Path, capsys
    ) -> None:
        code = run_cli(["status", "--github-comment"])
        assert code == 0
        # Output is whatever format_github_comment returns; just check non-empty
        out = capsys.readouterr().out
        assert out.strip()

    @pytest.mark.unit
    def test_status_json_format(self, patched_tracker: Path, capsys) -> None:
        code = run_cli(["--output-json", "status"])
        assert code == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["success"] is True
        assert "report" in parsed["data"]

    @pytest.mark.unit
    def test_export_command_writes_csv(
        self, patched_tracker: Path, tmp_path: Path, capsys
    ) -> None:
        out_csv = tmp_path / "out.csv"
        code = run_cli(["--output-json", "export", "--output", str(out_csv)])
        assert code == 0
        assert out_csv.exists()
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["data"]["output_file"] == str(out_csv)

    @pytest.mark.unit
    def test_unhandled_exception_returns_one_with_error_output(
        self, patched_tracker: Path, monkeypatch, capsys
    ) -> None:
        # Force the tracker to fail on construction
        def boom(*args, **kwargs):
            raise RuntimeError("forced")

        monkeypatch.setattr(pt_module.ProjectTracker, "__init__", boom)
        code = run_cli(["--output-json", "status"])
        assert code == 1
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["success"] is False
        assert "forced" in parsed["error"]
