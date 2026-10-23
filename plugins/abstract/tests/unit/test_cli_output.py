"""Tests for the shared ``--output`` writer used by scripts and the CLI framework.

Feature: One output writer for every abstract CLI

As a user passing --output to an abstract command
I want an unwritable path reported as an error with a non-zero exit
So that a typo in a path fails loudly without a traceback
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from scripts import cli_scaffold

from abstract.cli_output import write_output

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"


class TestWriteOutput:
    """Feature: write text to a file or stdout, reporting a failed write."""

    @pytest.mark.unit
    def test_writes_text_to_file_unchanged_and_reports_success(self, tmp_path):
        out_file = tmp_path / "report.txt"
        assert write_output("hello world", out_file) is True
        assert out_file.read_text() == "hello world"

    @pytest.mark.unit
    def test_prints_to_stdout_when_no_path(self, capsys):
        assert write_output("hello stdout", None) is True
        assert capsys.readouterr().out == "hello stdout\n"

    @pytest.mark.unit
    def test_unwritable_path_returns_false_and_names_path_on_stderr(
        self, tmp_path, capsys
    ):
        out_file = tmp_path / "missing-dir" / "report.txt"
        assert write_output("hello", out_file) is False
        err = capsys.readouterr().err
        assert err.startswith("Error: cannot write")
        assert str(out_file) in err
        assert not out_file.exists()

    @pytest.mark.unit
    def test_cli_scaffold_reexports_the_shared_writer(self):
        assert cli_scaffold.write_output is write_output


class TestScriptOutputFlag:
    """Feature: a scaffold script fails cleanly on an unwritable --output."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "script",
        [
            "token_usage_tracker.py",
            "compliance_checker.py",
            "skills_auditor.py",
            "tool_performance_analyzer.py",
        ],
    )
    def test_script_exits_nonzero_without_traceback_on_unwritable_output(
        self, tmp_path, script
    ):
        out_file = tmp_path / "missing-dir" / "report.txt"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / script),
                str(tmp_path),
                "--output",
                str(out_file),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert completed.returncode == 1
        assert "Traceback" not in completed.stderr
        assert f"Error: cannot write {out_file}" in completed.stderr
