"""Tests for CLI framework classes.

Covers OutputFormatter, CLIResult, PathArgumentMixin, FilterArgumentMixin,
and AbstractCLI base class behavior.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from abstract.cli_framework import (
    AbstractCLI,
    CLIResult,
    FilterArgumentMixin,
    OutputFormatter,
    PathArgumentMixin,
    cli_main,
)

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@dataclass
class _SampleData:
    name: str
    value: int


class _ConcreteCLI(AbstractCLI):
    """Minimal concrete subclass of AbstractCLI for testing."""

    def __init__(self, execute_result: CLIResult | None = None) -> None:
        super().__init__(
            name="test-tool",
            description="A test CLI",
            version="2.0.0",
        )
        self._execute_result = execute_result or CLIResult(success=True, data="ok")

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--flag", action="store_true", help="A flag")

    def execute(self, args: argparse.Namespace) -> CLIResult:
        return self._execute_result


# ===========================================================================
# CLIResult
# ===========================================================================


class TestCLIResult:
    """CLIResult dataclass stores result state correctly."""

    @pytest.mark.unit
    def test_success_true(self):
        """Given success=True, result reports success."""
        r = CLIResult(success=True, data={"key": "val"})
        assert r.success is True
        assert r.data == {"key": "val"}
        assert r.error is None
        assert r.warnings is None

    @pytest.mark.unit
    def test_failure_stores_error(self):
        """Given success=False, error message is preserved."""
        r = CLIResult(success=False, error="something went wrong")
        assert r.success is False
        assert r.error == "something went wrong"
        assert r.data is None

    @pytest.mark.unit
    def test_warnings_list(self):
        """Given warnings list, they are stored in the result."""
        r = CLIResult(success=True, data=None, warnings=["w1", "w2"])
        assert r.warnings == ["w1", "w2"]

    @pytest.mark.unit
    def test_generic_data_type(self):
        """Given a typed data payload, CLIResult preserves it."""
        sample = _SampleData(name="foo", value=42)
        r: CLIResult[_SampleData] = CLIResult(success=True, data=sample)
        assert r.data is sample
        assert r.data.name == "foo"


# ===========================================================================
# OutputFormatter
# ===========================================================================


class TestOutputFormatterJson:
    """format_json converts various data shapes to JSON strings."""

    @pytest.mark.unit
    def test_plain_dict(self):
        """Given a plain dict, output is valid JSON."""
        import json

        result = OutputFormatter.format_json({"a": 1})
        parsed = json.loads(result)
        assert parsed == {"a": 1}

    @pytest.mark.unit
    def test_dataclass_serialised(self):
        """Given a dataclass instance, it is serialised via asdict."""
        import json

        sample = _SampleData(name="hello", value=7)
        result = OutputFormatter.format_json(sample)
        parsed = json.loads(result)
        assert parsed == {"name": "hello", "value": 7}

    @pytest.mark.unit
    def test_list_of_dataclasses(self):
        """Given a list of dataclasses, each is serialised."""
        import json

        items = [_SampleData(name="a", value=1), _SampleData(name="b", value=2)]
        result = OutputFormatter.format_json(items)
        parsed = json.loads(result)
        assert parsed == [{"name": "a", "value": 1}, {"name": "b", "value": 2}]

    @pytest.mark.unit
    def test_list_of_plain_dicts(self):
        """Given a list of plain dicts, output is valid JSON array."""
        import json

        data = [{"x": 1}, {"x": 2}]
        result = OutputFormatter.format_json(data)
        parsed = json.loads(result)
        assert parsed == data

    @pytest.mark.unit
    def test_path_serialised_as_string(self):
        """Given a Path in a dict, output encodes it as string."""
        import json

        result = OutputFormatter.format_json({"p": Path("/tmp/test")})
        parsed = json.loads(result)
        assert parsed["p"] == "/tmp/test"


class TestOutputFormatterSummary:
    """format_summary returns a string representation of data."""

    @pytest.mark.unit
    def test_uses_summary_func_when_provided(self):
        """Given a summary_func, its return value is used."""
        result = OutputFormatter.format_summary("data", summary_func=lambda d: "CUSTOM")
        assert result == "CUSTOM"

    @pytest.mark.unit
    def test_dataclass_falls_back_to_str(self):
        """Given a dataclass and no summary_func, str() is returned."""
        sample = _SampleData(name="n", value=5)
        result = OutputFormatter.format_summary(sample)
        assert "name" in result or "_SampleData" in result

    @pytest.mark.unit
    def test_plain_string(self):
        """Given a plain string, format_summary returns it unchanged."""
        result = OutputFormatter.format_summary("hello world")
        assert result == "hello world"


class TestOutputFormatterTable:
    """format_table renders rows as aligned ASCII table."""

    @pytest.mark.unit
    def test_empty_rows_returns_no_data(self):
        """Given empty rows list, 'No data' is returned."""
        result = OutputFormatter.format_table([])
        assert result == "No data"

    @pytest.mark.unit
    def test_single_row_rendered(self):
        """Given one row, header and row appear in output."""
        rows = [{"name": "Alice", "age": "30"}]
        result = OutputFormatter.format_table(rows)
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "30" in result

    @pytest.mark.unit
    def test_column_subset(self):
        """Given columns subset, only specified columns appear."""
        rows = [{"name": "Alice", "age": "30", "city": "NYC"}]
        result = OutputFormatter.format_table(rows, columns=["name"])
        assert "Name" in result
        assert "Alice" in result
        assert "Age" not in result
        assert "City" not in result

    @pytest.mark.unit
    def test_custom_headers(self):
        """Given custom headers dict, header row uses custom labels."""
        rows = [{"n": "Bob"}]
        result = OutputFormatter.format_table(rows, headers={"n": "Full Name"})
        assert "Full Name" in result
        assert "Bob" in result

    @pytest.mark.unit
    def test_multiple_rows_separator_present(self):
        """Given multiple rows, a separator line appears after the header."""
        rows = [{"col": "a"}, {"col": "b"}]
        result = OutputFormatter.format_table(rows)
        lines = result.splitlines()
        # lines[0] = header, lines[1] = separator, lines[2+] = rows
        assert len(lines) >= 4
        assert set(lines[1].replace(" ", "").replace("|", "")) == {"-"}

    @pytest.mark.unit
    def test_column_widths_fit_content(self):
        """Given long cell value, column is wide enough to contain it."""
        rows = [{"col": "a" * 50}]
        result = OutputFormatter.format_table(rows)
        assert "a" * 50 in result


# ===========================================================================
# AbstractCLI (via _ConcreteCLI)
# ===========================================================================


class TestAbstractCLICreateParser:
    """create_parser produces a parser with common arguments."""

    @pytest.mark.unit
    def test_returns_argument_parser(self):
        """Given a concrete CLI, create_parser returns ArgumentParser."""
        cli = _ConcreteCLI()
        parser = cli.create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    @pytest.mark.unit
    def test_parser_cached_on_second_call(self):
        """Given create_parser called twice, same object is returned."""
        cli = _ConcreteCLI()
        p1 = cli.create_parser()
        p2 = cli.create_parser()
        assert p1 is p2

    @pytest.mark.unit
    def test_format_argument_present(self):
        """Given parser creation, --format argument is registered."""
        cli = _ConcreteCLI()
        parser = cli.create_parser()
        args = parser.parse_args(["--format", "json"])
        assert args.format == "json"

    @pytest.mark.unit
    def test_verbose_argument_present(self):
        """Given parser creation, --verbose/-v argument is registered."""
        cli = _ConcreteCLI()
        parser = cli.create_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose == 1

    @pytest.mark.unit
    def test_quiet_argument_present(self):
        """Given parser creation, --quiet argument is registered."""
        cli = _ConcreteCLI()
        parser = cli.create_parser()
        args = parser.parse_args(["--quiet"])
        assert args.quiet is True

    @pytest.mark.unit
    def test_project_root_argument_present(self):
        """Given parser creation, --project-root accepts a path."""
        cli = _ConcreteCLI()
        parser = cli.create_parser()
        args = parser.parse_args(["--project-root", "/tmp"])
        assert args.project_root == Path("/tmp")

    @pytest.mark.unit
    def test_config_argument_present(self):
        """Given parser creation, --config accepts a path."""
        cli = _ConcreteCLI()
        parser = cli.create_parser()
        args = parser.parse_args(["--config", "/tmp/conf.yaml"])
        assert args.config == Path("/tmp/conf.yaml")


class TestAbstractCLIRun:
    """AbstractCLI.run() returns correct exit codes."""

    @pytest.mark.unit
    def test_run_success_returns_zero(self):
        """Given execute returns success, run returns 0."""
        cli = _ConcreteCLI(CLIResult(success=True, data="all good"))
        exit_code = cli.run([])
        assert exit_code == 0

    @pytest.mark.unit
    def test_run_failure_returns_one(self):
        """Given execute returns failure, run returns 1."""
        cli = _ConcreteCLI(CLIResult(success=False, error="oops"))
        exit_code = cli.run([])
        assert exit_code == 1

    @pytest.mark.unit
    def test_run_keyboard_interrupt_returns_130(self):
        """Given execute raises KeyboardInterrupt, run returns 130."""

        class _InterruptCLI(_ConcreteCLI):
            def execute(self, args):
                raise KeyboardInterrupt

        exit_code = _InterruptCLI().run([])
        assert exit_code == 130

    @pytest.mark.unit
    def test_run_exception_returns_one(self, capsys):
        """Given execute raises an unexpected exception, run returns 1."""

        class _RaisingCLI(_ConcreteCLI):
            def execute(self, args):
                raise ValueError("unexpected error")

        exit_code = _RaisingCLI().run([])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    @pytest.mark.unit
    def test_run_prints_warnings_to_stderr(self, capsys):
        """Given warnings in result, they are printed to stderr."""
        cli = _ConcreteCLI(CLIResult(success=True, data="ok", warnings=["watch out"]))
        cli.run([])
        captured = capsys.readouterr()
        assert "watch out" in captured.err

    @pytest.mark.unit
    def test_run_quiet_suppresses_warnings(self, capsys):
        """Given --quiet, warnings are suppressed."""
        cli = _ConcreteCLI(CLIResult(success=True, data="ok", warnings=["watch out"]))
        cli.run(["--quiet"])
        captured = capsys.readouterr()
        assert "watch out" not in captured.err

    @pytest.mark.unit
    def test_run_verbose_prints_traceback(self, capsys):
        """Given -v and an exception, traceback is printed to stderr."""

        class _RaisingCLI(_ConcreteCLI):
            def execute(self, args):
                raise RuntimeError("boom")

        exit_code = _RaisingCLI().run(["-v"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "RuntimeError" in captured.err

    @pytest.mark.unit
    def test_run_missing_config_file_returns_one(self, capsys):
        """Given a nonexistent --config path, run returns 1."""
        cli = _ConcreteCLI()
        exit_code = cli.run(["--config", "/nonexistent/path/config.yaml"])
        assert exit_code == 1

    @pytest.mark.unit
    def test_run_json_format_output(self, capsys):
        """Given --format json, output is JSON-formatted."""
        cli = _ConcreteCLI(CLIResult(success=True, data={"k": "v"}))
        cli.run(["--format", "json"])
        captured = capsys.readouterr()
        import json

        parsed = json.loads(captured.out.strip())
        assert parsed == {"k": "v"}


class TestAbstractCLIFormatOutput:
    """format_output delegates to the correct formatter."""

    @pytest.mark.unit
    def test_error_result_formats_error_message(self):
        """Given failed result, format_output returns error string."""
        cli = _ConcreteCLI()
        result = CLIResult(success=False, error="bad thing")
        output = cli.format_output(result, "text")
        assert "Error" in output
        assert "bad thing" in output

    @pytest.mark.unit
    def test_json_format_delegates_to_formatter(self):
        """Given format=json, JSON output is produced."""
        import json

        cli = _ConcreteCLI()
        result = CLIResult(success=True, data={"x": 1})
        output = cli.format_output(result, "json")
        parsed = json.loads(output)
        assert parsed == {"x": 1}

    @pytest.mark.unit
    def test_summary_format_uses_summary_func(self):
        """Given format=summary and a summary_func, its return is used."""
        cli = _ConcreteCLI()
        result = CLIResult(success=True, data="payload")
        output = cli.format_output(result, "summary", summary_func=lambda d: "SUM")
        assert output == "SUM"

    @pytest.mark.unit
    def test_table_format_list_data(self):
        """Given format=table and list data, table is rendered."""
        cli = _ConcreteCLI()
        result = CLIResult(success=True, data=[{"col": "val"}])
        output = cli.format_output(result, "table")
        assert "Col" in output
        assert "val" in output

    @pytest.mark.unit
    def test_text_format_returns_string(self):
        """Given format=text, format_text result is returned."""
        cli = _ConcreteCLI()
        result = CLIResult(success=True, data="some text")
        output = cli.format_output(result, "text")
        assert "some text" in output


class TestAbstractCLIFormatText:
    """format_text returns str representation of data."""

    @pytest.mark.unit
    def test_string_data_returned_unchanged(self):
        """Given string data, format_text returns the string."""
        cli = _ConcreteCLI()
        assert cli.format_text("hello") == "hello"

    @pytest.mark.unit
    def test_dataclass_data_uses_str(self):
        """Given dataclass data, format_text uses str()."""
        cli = _ConcreteCLI()
        sample = _SampleData(name="x", value=1)
        result = cli.format_text(sample)
        assert "_SampleData" in result or "name" in result


class TestAbstractCLIFormatTableData:
    """_format_table_data handles list and single dataclass."""

    @pytest.mark.unit
    def test_list_of_dicts(self):
        """Given a list of plain dicts, table is rendered."""
        cli = _ConcreteCLI()
        output = cli._format_table_data([{"a": "1"}], None)
        assert "1" in output

    @pytest.mark.unit
    def test_single_dataclass(self):
        """Given a single dataclass, table is rendered with one row."""
        cli = _ConcreteCLI()
        sample = _SampleData(name="z", value=99)
        output = cli._format_table_data(sample, None)
        assert "z" in output or "99" in output

    @pytest.mark.unit
    def test_non_list_non_dataclass(self):
        """Given a scalar, str() is returned."""
        cli = _ConcreteCLI()
        output = cli._format_table_data("raw", None)
        assert output == "raw"


# ===========================================================================
# cli_main
# ===========================================================================


class TestCliMain:
    """cli_main instantiates the CLI class and calls sys.exit."""

    @pytest.mark.unit
    def test_cli_main_calls_sys_exit(self):
        """Given a CLI class, cli_main calls sys.exit with the return code."""
        with patch("sys.argv", ["test-tool"]):
            with pytest.raises(SystemExit) as exc_info:
                cli_main(_ConcreteCLI)
        assert exc_info.value.code == 0


# ===========================================================================
# PathArgumentMixin
# ===========================================================================


class TestPathArgumentMixin:
    """PathArgumentMixin adds file/directory/skill-path arguments."""

    @pytest.mark.unit
    def test_add_path_arguments_file_option(self):
        """Given add_path_arguments, --file is registered."""
        parser = argparse.ArgumentParser()
        PathArgumentMixin.add_path_arguments(parser, require_one=False)
        args = parser.parse_args(["--file", "/tmp/x.md"])
        assert args.file == Path("/tmp/x.md")

    @pytest.mark.unit
    def test_add_path_arguments_directory_option(self):
        """Given add_path_arguments, --directory/-d is registered."""
        parser = argparse.ArgumentParser()
        PathArgumentMixin.add_path_arguments(parser, require_one=False)
        args = parser.parse_args(["-d", "/tmp/dir"])
        assert args.directory == Path("/tmp/dir")

    @pytest.mark.unit
    def test_add_path_arguments_mutually_exclusive(self):
        """Given both --file and --directory, parsing fails."""
        parser = argparse.ArgumentParser()
        PathArgumentMixin.add_path_arguments(parser, require_one=False)
        with pytest.raises(SystemExit):
            parser.parse_args(["--file", "/tmp/a.md", "--directory", "/tmp/b"])

    @pytest.mark.unit
    def test_add_skill_path_argument(self):
        """Given add_skill_path_argument, --skill-path is registered."""
        parser = argparse.ArgumentParser()
        PathArgumentMixin.add_skill_path_argument(parser, required=False)
        args = parser.parse_args(["--skill-path", "/tmp/SKILL.md"])
        assert args.skill_path == Path("/tmp/SKILL.md")

    @pytest.mark.unit
    def test_add_path_arguments_require_one_true_fails_without_arg(self):
        """Given require_one=True and no path provided, parsing fails."""
        parser = argparse.ArgumentParser()
        PathArgumentMixin.add_path_arguments(parser, require_one=True)
        with pytest.raises(SystemExit):
            parser.parse_args([])


# ===========================================================================
# FilterArgumentMixin
# ===========================================================================


class TestFilterArgumentMixin:
    """FilterArgumentMixin adds severity and category filter arguments."""

    @pytest.mark.unit
    def test_add_severity_filter_default_choices(self):
        """Given add_severity_filter, four severity levels are accepted."""
        parser = argparse.ArgumentParser()
        FilterArgumentMixin.add_severity_filter(parser)
        for level in ["critical", "high", "medium", "low"]:
            args = parser.parse_args(["--severity", level])
            assert args.severity == level

    @pytest.mark.unit
    def test_add_severity_filter_custom_choices(self):
        """Given custom choices, only those are accepted."""
        parser = argparse.ArgumentParser()
        FilterArgumentMixin.add_severity_filter(parser, choices=["red", "blue"])
        args = parser.parse_args(["--severity", "red"])
        assert args.severity == "red"

    @pytest.mark.unit
    def test_add_severity_filter_invalid_choice_fails(self):
        """Given an invalid severity, parsing fails."""
        parser = argparse.ArgumentParser()
        FilterArgumentMixin.add_severity_filter(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["--severity", "unknown"])

    @pytest.mark.unit
    def test_add_category_filter_with_choices(self):
        """Given add_category_filter with choices, registered correctly."""
        parser = argparse.ArgumentParser()
        FilterArgumentMixin.add_category_filter(parser, choices=["alpha", "beta"])
        args = parser.parse_args(["--category", "alpha"])
        assert args.category == "alpha"

    @pytest.mark.unit
    def test_add_category_filter_invalid_fails(self):
        """Given invalid category, parsing fails."""
        parser = argparse.ArgumentParser()
        FilterArgumentMixin.add_category_filter(parser, choices=["alpha"])
        with pytest.raises(SystemExit):
            parser.parse_args(["--category", "gamma"])

    @pytest.mark.unit
    def test_add_category_filter_no_choices(self):
        """Given no choices, any value is accepted."""
        parser = argparse.ArgumentParser()
        FilterArgumentMixin.add_category_filter(parser)
        args = parser.parse_args(["--category", "anything"])
        assert args.category == "anything"
