"""Tests for shared CLI scaffolding module.

Feature: Shared CLI scaffolding for abstract wrapper scripts

As a plugin developer
I want common CLI boilerplate extracted into a shared module
So that wrapper scripts stay DRY and consistent
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from scripts.cli_scaffold import (
    create_parser,
    format_result,
    setup_src_path,
    write_output,
)


class TestSetupSrcPath:
    """Feature: Source path setup

    As a CLI wrapper script
    I want to add the plugin src directory to sys.path
    So that I can import core modules without manual path manipulation
    """

    @pytest.mark.unit
    def test_adds_src_to_sys_path(self):
        """Scenario: First-time path setup
        Given sys.path does not contain the src directory
        When setup_src_path is called
        Then the src directory is added to sys.path
        """
        src_path = str((Path(__file__).parents[2] / "src").resolve())

        # Remove if present to test fresh addition
        original = sys.path.copy()
        sys.path = [p for p in sys.path if str(Path(p).resolve()) != src_path]

        try:
            setup_src_path()
            resolved_paths = [str(Path(p).resolve()) for p in sys.path]
            assert src_path in resolved_paths
        finally:
            sys.path = original

    @pytest.mark.unit
    def test_does_not_duplicate_path(self):
        """Scenario: Path already present
        Given sys.path already contains the src directory
        When setup_src_path is called again
        Then the src directory is not duplicated
        """
        setup_src_path()
        count_before = len(sys.path)
        setup_src_path()
        count_after = len(sys.path)

        assert count_after == count_before


class TestCreateParser:
    """Feature: Parser creation with common flags

    As a CLI wrapper script
    I want a parser pre-configured with --output
    So that output handling is consistent across scripts
    """

    @pytest.mark.unit
    def test_parser_has_output_arg(self):
        """Scenario: Basic parser creation
        Given a description string
        When create_parser is called
        Then the returned parser accepts --output
        """
        parser = create_parser("test description")
        args = parser.parse_args(["--output", "/tmp/out.txt"])
        assert args.output == Path("/tmp/out.txt")

    @pytest.mark.unit
    def test_parser_output_defaults_none(self):
        """Scenario: No output flag provided
        Given a parser
        When parsed with no --output
        Then output defaults to None
        """
        parser = create_parser("test")
        args = parser.parse_args([])
        assert args.output is None

    @pytest.mark.unit
    def test_parser_with_format_flag(self):
        """Scenario: Format flag requested
        Given add_format=True
        When create_parser is called
        Then --format accepts text and json choices
        """
        parser = create_parser("test", add_format=True)
        args = parser.parse_args(["--format", "json"])
        assert args.format == "json"

    @pytest.mark.unit
    def test_parser_format_defaults_text(self):
        """Scenario: Format flag defaults to text
        Given add_format=True
        When parsed with no --format
        Then format defaults to "text"
        """
        parser = create_parser("test", add_format=True)
        args = parser.parse_args([])
        assert args.format == "text"

    @pytest.mark.unit
    def test_parser_without_format_flag(self):
        """Scenario: Format flag not requested
        Given add_format=False (default)
        When create_parser is called
        Then --format is not an option
        """
        parser = create_parser("test")
        args = parser.parse_args([])
        assert not hasattr(args, "format")


class TestWriteOutput:
    """Feature: Output writing

    As a CLI wrapper script
    I want a helper that writes to file or stdout
    So that all scripts handle output consistently
    """

    @pytest.mark.unit
    def test_writes_to_file(self, tmp_path):
        """Scenario: Output path provided
        Given a text string and a file path
        When write_output is called
        Then the text is written to the file
        """
        out_file = tmp_path / "result.txt"
        write_output("hello world", out_file)
        assert out_file.read_text() == "hello world"

    @pytest.mark.unit
    def test_prints_to_stdout_when_no_path(self, capsys):
        """Scenario: No output path
        Given a text string and output_path=None
        When write_output is called
        Then the text is printed to stdout
        """
        write_output("hello stdout", None)
        captured = capsys.readouterr()
        assert "hello stdout" in captured.out


class TestFormatResult:
    """Feature: Result formatting

    As a CLI wrapper script
    I want to format results as JSON or text
    So that output format switching is consistent
    """

    @pytest.mark.unit
    def test_json_format(self):
        """Scenario: JSON output
        Given a dict and fmt="json"
        When format_result is called
        Then valid JSON string is returned
        """
        data = {"count": 5, "items": ["a", "b"]}
        result = format_result(data, fmt="json")
        parsed = json.loads(result)
        assert parsed == data

    @pytest.mark.unit
    def test_text_format_with_callback(self):
        """Scenario: Text output with custom formatter
        Given a dict and a text_fn callback
        When format_result is called with fmt="text"
        Then the callback produces the text
        """
        data = {"name": "test", "score": 42}
        result = format_result(
            data,
            fmt="text",
            text_fn=lambda d: f"{d['name']}: {d['score']}",
        )
        assert result == "test: 42"

    @pytest.mark.unit
    def test_text_format_falls_back_to_str(self):
        """Scenario: Text output without callback
        Given a dict and no text_fn
        When format_result is called with fmt="text"
        Then str(data) is returned
        """
        data = {"key": "val"}
        result = format_result(data, fmt="text")
        assert result == str(data)
