"""Tests for abstract.errors helpers."""

from pathlib import Path

import pytest

from abstract.errors import ErrorHandler, safe_file_read, safe_file_write


def test_safe_file_write_includes_exception_type(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """safe_file_write includes exception type in user-facing error."""
    error_handler = ErrorHandler(f"test_errors_{tmp_path.name}")

    target = tmp_path / "as_dir"
    target.mkdir()

    with pytest.raises(SystemExit):
        safe_file_write(target, "content", error_handler)

    captured = capsys.readouterr()
    assert "IO_ERROR" in captured.err
    # Check for directory error indication (message content, not type name)
    assert "Is a directory" in captured.err


def test_safe_file_read_includes_exception_type_for_decode_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """safe_file_read includes exception type for non-OSError failures."""
    error_handler = ErrorHandler(f"test_errors_{tmp_path.name}")

    target = tmp_path / "invalid_utf8.txt"
    target.write_bytes(b"\xff")

    with pytest.raises(SystemExit):
        safe_file_read(target, error_handler)

    captured = capsys.readouterr()
    assert "UNEXPECTED_ERROR" in captured.err
    # Check for decode error indication (message content, not type name)
    assert "codec can't decode" in captured.err


def test_safe_execute_includes_exception_type_in_logged_error(tmp_path: Path) -> None:
    """safe_execute logs exception type so callers can diagnose the failure."""
    error_handler = ErrorHandler(f"test_errors_{tmp_path.name}")

    def explode() -> None:
        raise ZeroDivisionError("boom")

    with pytest.raises(ZeroDivisionError):
        error_handler.safe_execute(explode, "exploding")

    assert error_handler.errors
    # Check error was logged with operation context and error message
    assert "exploding" in error_handler.errors[-1].message
    assert "boom" in error_handler.errors[-1].message


def test_later_handler_asking_for_a_log_file_writes_to_that_file(
    tmp_path: Path,
) -> None:
    tool_name = f"test_errors_logfile_{tmp_path.name}"
    log_file = tmp_path / "tool.log"
    ErrorHandler(tool_name)

    later = ErrorHandler(tool_name, log_file=log_file)
    later.logger.info("written to the file")

    try:
        assert "written to the file" in log_file.read_text(encoding="utf-8")
        assert len(later.logger.handlers) == 1
    finally:
        for handler in list(later.logger.handlers):
            later.logger.removeHandler(handler)
            handler.close()


def test_repeated_handler_for_the_same_target_keeps_one_log_handler(
    tmp_path: Path,
) -> None:
    tool_name = f"test_errors_repeat_{tmp_path.name}"
    log_file = tmp_path / "tool.log"
    ErrorHandler(tool_name, log_file=log_file)
    later = ErrorHandler(tool_name, log_file=log_file)
    try:
        assert len(later.logger.handlers) == 1
    finally:
        for handler in list(later.logger.handlers):
            later.logger.removeHandler(handler)
            handler.close()
