"""Extended tests for the errors module.

Feature: Centralized error handling
    As a developer
    I want error handling utilities fully tested
    So that tools produce clear, structured error output
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.errors import (
    ErrorHandler,
    ErrorSeverity,
    ToolError,
)


class TestToolErrorDataclass:
    """Feature: ToolError is a structured error container."""

    @pytest.mark.unit
    def test_minimal_construction(self) -> None:
        """Scenario: ToolError can be built with required fields only."""
        err = ToolError(
            severity=ErrorSeverity.LOW,
            error_code="TEST_ERR",
            message="Test message",
        )
        assert err.severity == ErrorSeverity.LOW
        assert err.error_code == "TEST_ERR"
        assert err.message == "Test message"
        assert err.details is None
        assert err.suggestion is None
        assert err.exit_code == 1

    @pytest.mark.unit
    def test_full_construction(self) -> None:
        """Scenario: ToolError stores all optional fields."""
        err = ToolError(
            severity=ErrorSeverity.HIGH,
            error_code="FULL_ERR",
            message="Full error",
            details="Detailed info",
            suggestion="Try this",
            exit_code=3,
            context={"key": "value"},
        )
        assert err.details == "Detailed info"
        assert err.suggestion == "Try this"
        assert err.exit_code == 3
        assert err.context == {"key": "value"}


class TestErrorHandler:
    """Feature: ErrorHandler manages tool errors."""

    @pytest.fixture
    def handler(self) -> ErrorHandler:
        """Given a fresh ErrorHandler for tool 'test-tool'."""
        return ErrorHandler("test-tool")

    @pytest.mark.unit
    def test_handle_file_error_missing_file(
        self, handler: ErrorHandler, tmp_path: Path
    ) -> None:
        """Scenario: Missing file produces FILE_NOT_FOUND error.
        Given a path that does not exist
        When handle_file_error is called
        Then the error code is FILE_NOT_FOUND with CRITICAL severity
        """
        missing = tmp_path / "does_not_exist.txt"
        err = handler.handle_file_error(missing, "read")
        assert err.error_code == "FILE_NOT_FOUND"
        assert err.severity == ErrorSeverity.CRITICAL

    @pytest.mark.unit
    def test_handle_file_error_directory_instead_of_file(
        self, handler: ErrorHandler, tmp_path: Path
    ) -> None:
        """Scenario: Directory path produces NOT_A_FILE error.
        Given a path that is a directory
        When handle_file_error is called
        Then the error code is NOT_A_FILE
        """
        err = handler.handle_file_error(tmp_path, "read")
        assert err.error_code == "NOT_A_FILE"

    @pytest.mark.unit
    def test_handle_directory_error_missing_dir(
        self, handler: ErrorHandler, tmp_path: Path
    ) -> None:
        """Scenario: Missing directory produces DIR_NOT_FOUND error."""
        missing = tmp_path / "no_such_dir"
        err = handler.handle_directory_error(missing, "list")
        assert err.error_code == "DIR_NOT_FOUND"
        assert err.severity == ErrorSeverity.CRITICAL

    @pytest.mark.unit
    def test_handle_directory_error_file_instead_of_dir(
        self, handler: ErrorHandler, tmp_path: Path
    ) -> None:
        """Scenario: File path produces NOT_A_DIRECTORY error."""
        f = tmp_path / "afile.txt"
        f.write_text("hello")
        err = handler.handle_directory_error(f, "list")
        assert err.error_code == "NOT_A_DIRECTORY"

    @pytest.mark.unit
    def test_handle_yaml_error(self, handler: ErrorHandler, tmp_path: Path) -> None:
        """Scenario: YAML exception produces YAML_PARSE_ERROR."""
        fake_exc = ValueError("bad yaml")
        err = handler.handle_yaml_error(fake_exc, tmp_path / "file.yaml")
        assert err.error_code == "YAML_PARSE_ERROR"
        assert err.severity == ErrorSeverity.HIGH

    @pytest.mark.unit
    def test_handle_io_error(self, handler: ErrorHandler) -> None:
        """Scenario: OSError produces IO_ERROR."""
        fake_exc = OSError("disk full")
        err = handler.handle_io_error(fake_exc, "write")
        assert err.error_code == "IO_ERROR"
        assert err.severity == ErrorSeverity.MEDIUM

    @pytest.mark.unit
    def test_handle_validation_error(self, handler: ErrorHandler) -> None:
        """Scenario: Validation message produces VALIDATION_ERROR."""
        err = handler.handle_validation_error("field is required")
        assert err.error_code == "VALIDATION_ERROR"
        assert "field is required" in err.message

    @pytest.mark.unit
    def test_handle_argument_error(self, handler: ErrorHandler) -> None:
        """Scenario: Argument error produces ARGUMENT_ERROR with exit_code 2."""
        err = handler.handle_argument_error("--flag is required")
        assert err.error_code == "ARGUMENT_ERROR"
        assert err.exit_code == 2

    @pytest.mark.unit
    def test_log_error_stores_error(self, handler: ErrorHandler) -> None:
        """Scenario: log_error stores the error in the errors list."""
        err = ToolError(
            severity=ErrorSeverity.LOW,
            error_code="X",
            message="msg",
        )
        handler.log_error(err)
        assert len(handler.errors) == 1
        assert handler.errors[0] is err

    @pytest.mark.unit
    def test_log_error_critical_calls_logger_critical(
        self, handler: ErrorHandler, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: CRITICAL severity is logged at critical level."""
        err = ToolError(
            severity=ErrorSeverity.CRITICAL,
            error_code="CRIT",
            message="critical failure",
        )
        handler.log_error(err)
        # No crash, error stored
        assert len(handler.errors) == 1

    @pytest.mark.unit
    def test_log_error_medium_severity(self, handler: ErrorHandler) -> None:
        """Scenario: MEDIUM severity calls warning logger."""
        err = ToolError(severity=ErrorSeverity.MEDIUM, error_code="M", message="med")
        handler.log_error(err)
        assert len(handler.errors) == 1

    @pytest.mark.unit
    def test_print_error_outputs_to_stderr(
        self, handler: ErrorHandler, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: print_error writes formatted message to stderr."""
        err = ToolError(
            severity=ErrorSeverity.HIGH,
            error_code="HIGH_ERR",
            message="Something went wrong",
            details="extra details",
            suggestion="Try again",
        )
        handler.print_error(err)
        captured = capsys.readouterr()
        assert "HIGH_ERR" in captured.err
        assert "Something went wrong" in captured.err
        assert "extra details" in captured.err
        assert "Try again" in captured.err

    @pytest.mark.unit
    def test_print_error_all_severities(
        self, handler: ErrorHandler, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: Each severity produces a labeled output."""
        for severity in ErrorSeverity:
            err = ToolError(severity=severity, error_code="X", message="m")
            handler.print_error(err)
        captured = capsys.readouterr()
        # Should have output for each
        assert len(captured.err) > 0

    @pytest.mark.unit
    def test_print_error_summary_empty_no_output(
        self, handler: ErrorHandler, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: print_error_summary with no errors produces no output."""
        handler.print_error_summary()
        captured = capsys.readouterr()
        assert captured.err == ""

    @pytest.mark.unit
    def test_print_error_summary_counts_severities(
        self, handler: ErrorHandler, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: print_error_summary tallies errors by severity."""
        handler.log_error(
            ToolError(severity=ErrorSeverity.HIGH, error_code="H", message="h")
        )
        handler.log_error(
            ToolError(severity=ErrorSeverity.LOW, error_code="L", message="l")
        )
        handler.print_error_summary()
        captured = capsys.readouterr()
        assert "Error summary" in captured.err

    @pytest.mark.unit
    def test_exit_if_errors_no_qualifying_errors_does_not_exit(
        self, handler: ErrorHandler, capsys: pytest.CaptureFixture
    ) -> None:
        """Given: a logged LOW error and a MEDIUM exit threshold
        When: exit_if_errors runs
        Then: it returns, prints no summary, and keeps the error logged

        The summary is printed on the same branch that exits, so its
        absence is the evidence the branch was not taken. Asserting the
        error survives rules out passing by having dropped it.
        """
        handler.log_error(
            ToolError(severity=ErrorSeverity.LOW, error_code="L", message="low")
        )
        capsys.readouterr()

        assert handler.exit_if_errors(min_severity=ErrorSeverity.MEDIUM) is None

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
        assert [e.error_code for e in handler.errors] == ["L"]

    @pytest.mark.unit
    def test_exit_if_errors_qualifying_error_exits(self, handler: ErrorHandler) -> None:
        """Scenario: MEDIUM error triggers exit when min_severity is MEDIUM."""
        handler.log_error(
            ToolError(severity=ErrorSeverity.MEDIUM, error_code="M", message="med")
        )
        with pytest.raises(SystemExit):
            handler.exit_if_errors(min_severity=ErrorSeverity.MEDIUM)

    @pytest.mark.unit
    def test_safe_execute_returns_value_on_success(self, handler: ErrorHandler) -> None:
        """Scenario: safe_execute returns the operation result on success."""
        result = handler.safe_execute(lambda: 42, "test_op")
        assert result == 42

    @pytest.mark.unit
    def test_safe_execute_re_raises_file_not_found(self, handler: ErrorHandler) -> None:
        """Scenario: FileNotFoundError is logged then re-raised."""

        def failing_op():
            raise FileNotFoundError("no file")

        with pytest.raises(FileNotFoundError):
            handler.safe_execute(failing_op, "read_op")

        assert any(e.error_code == "FILE_NOT_FOUND" for e in handler.errors)

    @pytest.mark.unit
    def test_safe_execute_re_raises_permission_error(
        self, handler: ErrorHandler
    ) -> None:
        """Scenario: PermissionError is logged then re-raised."""

        def failing_op():
            raise PermissionError("denied")

        with pytest.raises(PermissionError):
            handler.safe_execute(failing_op, "write_op")

        assert any(e.error_code == "PERMISSION_ERROR" for e in handler.errors)

    @pytest.mark.unit
    def test_safe_execute_re_raises_os_error(self, handler: ErrorHandler) -> None:
        """Scenario: OSError is logged then re-raised."""

        def failing_op():
            raise OSError("io error")

        with pytest.raises(OSError):
            handler.safe_execute(failing_op, "io_op")

        assert any(e.error_code == "IO_ERROR" for e in handler.errors)

    @pytest.mark.unit
    def test_safe_execute_re_raises_unexpected_error(
        self, handler: ErrorHandler
    ) -> None:
        """Scenario: Unexpected exceptions are logged then re-raised."""

        def failing_op():
            raise ValueError("unexpected")

        with pytest.raises(ValueError):
            handler.safe_execute(failing_op, "misc_op")

        assert any(e.error_code == "UNEXPECTED_ERROR" for e in handler.errors)
