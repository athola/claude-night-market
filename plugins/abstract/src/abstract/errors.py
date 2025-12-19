#!/usr/bin/env python3
"""Centralized error handling utilities for Abstract tools.

Provides consistent error reporting, logging, and user-friendly messages.
"""

import logging
import os
import sys
import traceback
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]
    warnings.warn(
        (
            "PyYAML is not installed; YAML parsing features are disabled. "
            "Install with: pip install pyyaml"
        ),
        category=RuntimeWarning,
        stacklevel=2,
    )


class ErrorSeverity(Enum):
    """Error severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ToolError:
    """Structured error information."""

    severity: ErrorSeverity
    error_code: str
    message: str
    details: str | None = None
    suggestion: str | None = None
    exit_code: int = 1
    context: dict[str, Any] | None = None


class ErrorHandler:
    """Centralized error handling for Abstract tools."""

    def __init__(self, tool_name: str, log_file: Path | None = None) -> None:
        """Initialize error handler for a specific tool."""
        self.tool_name = tool_name
        self.errors: list[ToolError] = []

        # Setup logging
        self.logger = logging.getLogger(tool_name)
        self.logger.setLevel(logging.INFO)

        handler: logging.Handler
        handler = logging.FileHandler(log_file) if log_file else logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def handle_file_error(self, file_path: Path, operation: str) -> ToolError:
        """Handle file-related errors."""
        if not file_path.exists():
            return ToolError(
                severity=ErrorSeverity.CRITICAL,
                error_code="FILE_NOT_FOUND",
                message=f"File not found: {file_path}",
                suggestion=(
                    f"Check that the file exists and the path is correct: {file_path}"
                ),
                context={"operation": operation, "file_path": str(file_path)},
            )

        if not file_path.is_file():
            return ToolError(
                severity=ErrorSeverity.HIGH,
                error_code="NOT_A_FILE",
                message=f"Path is not a file: {file_path}",
                suggestion="Ensure the path points to a file, not a directory",
                context={"operation": operation, "file_path": str(file_path)},
            )

        if not os.access(file_path, os.R_OK):
            return ToolError(
                severity=ErrorSeverity.HIGH,
                error_code="FILE_PERMISSION",
                message=f"Cannot read file: {file_path}",
                suggestion="Check file permissions and ensure the file is readable",
                context={"operation": operation, "file_path": str(file_path)},
            )

        return ToolError(
            severity=ErrorSeverity.LOW,
            error_code="FILE_ACCESS_UNKNOWN",
            message=f"Unknown file access error: {file_path}",
            suggestion="Check file path and permissions",
            context={"operation": operation, "file_path": str(file_path)},
        )

    def handle_directory_error(self, dir_path: Path, operation: str) -> ToolError:
        """Handle directory-related errors."""
        if not dir_path.exists():
            return ToolError(
                severity=ErrorSeverity.CRITICAL,
                error_code="DIR_NOT_FOUND",
                message=f"Directory not found: {dir_path}",
                suggestion=f"Create the directory or check the path: {dir_path}",
                context={"operation": operation, "dir_path": str(dir_path)},
            )

        if not dir_path.is_dir():
            return ToolError(
                severity=ErrorSeverity.HIGH,
                error_code="NOT_A_DIRECTORY",
                message=f"Path is not a directory: {dir_path}",
                suggestion="Ensure the path points to a directory, not a file",
                context={"operation": operation, "dir_path": str(dir_path)},
            )

        if not os.access(dir_path, os.R_OK | os.X_OK):
            return ToolError(
                severity=ErrorSeverity.HIGH,
                error_code="DIR_PERMISSION",
                message=f"Cannot access directory: {dir_path}",
                suggestion="Check directory permissions (read and execute)",
                context={"operation": operation, "dir_path": str(dir_path)},
            )

        return ToolError(
            severity=ErrorSeverity.LOW,
            error_code="DIR_ACCESS_UNKNOWN",
            message=f"Unknown directory access error: {dir_path}",
            suggestion="Check directory path and permissions",
            context={"operation": operation, "dir_path": str(dir_path)},
        )

    def handle_yaml_error(self, yaml_error: Exception, file_path: Path) -> ToolError:
        """Handle YAML parsing errors."""
        return ToolError(
            severity=ErrorSeverity.HIGH,
            error_code="YAML_PARSE_ERROR",
            message=f"YAML parsing error in {file_path}: {yaml_error!s}",
            suggestion="Check YAML syntax, indentation, and special characters",
            details=str(yaml_error),
            context={"file_path": str(file_path), "yaml_error": str(yaml_error)},
        )

    def handle_io_error(self, io_error: Exception, operation: str) -> ToolError:
        """Handle I/O errors."""
        return ToolError(
            severity=ErrorSeverity.MEDIUM,
            error_code="IO_ERROR",
            message=f"I/O error during {operation}: {io_error!s}",
            suggestion="Check file system permissions and disk space",
            details=str(io_error),
            context={"operation": operation, "io_error": str(io_error)},
        )

    def handle_validation_error(
        self,
        validation_error: str,
        context: dict[str, Any] | None = None,
    ) -> ToolError:
        """Handle validation errors."""
        return ToolError(
            severity=ErrorSeverity.MEDIUM,
            error_code="VALIDATION_ERROR",
            message=f"Validation error: {validation_error}",
            suggestion="Review input requirements and format specifications",
            context=context or {},
        )

    def handle_argument_error(self, arg_error: str) -> ToolError:
        """Handle command-line argument errors."""
        return ToolError(
            severity=ErrorSeverity.MEDIUM,
            error_code="ARGUMENT_ERROR",
            message=f"Argument error: {arg_error}",
            suggestion="Check command-line arguments and help documentation",
            exit_code=2,
        )

    def log_error(self, error: ToolError) -> None:
        """Log error and store for reporting."""
        self.errors.append(error)

        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"[{error.error_code}] {error.message}")
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"[{error.error_code}] {error.message}")
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"[{error.error_code}] {error.message}")
        else:
            self.logger.info(f"[{error.error_code}] {error.message}")

    def print_error(self, error: ToolError) -> None:
        """Print user-friendly error message."""
        severity_symbols = {
            ErrorSeverity.CRITICAL: "[CRIT]",
            ErrorSeverity.HIGH: "[HIGH]",
            ErrorSeverity.MEDIUM: "[MED]",
            ErrorSeverity.LOW: "[LOW]",
            ErrorSeverity.INFO: "[INFO]",
        }

        symbol = severity_symbols.get(error.severity, "[?]")
        message = f"{symbol} [{error.error_code}] {error.message}"
        print(message, file=sys.stderr)

        if error.details:
            print(f"  Details: {error.details}", file=sys.stderr)

        if error.suggestion:
            print(f"  Suggestion: {error.suggestion}", file=sys.stderr)

    def print_error_summary(self) -> None:
        """Print summary of all errors encountered."""
        if not self.errors:
            return

        severity_counts: dict[ErrorSeverity, int] = {}
        for error in self.errors:
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1

        symbol_map = {
            "critical": "[CRIT]",
            "high": "[HIGH]",
            "medium": "[MED]",
            "low": "[LOW]",
            "info": "[INFO]",
        }

        print("Error summary:", file=sys.stderr)
        for severity, count in severity_counts.items():
            symbol = symbol_map.get(severity.value, "[?]")
            print(f"  {symbol} {severity.value.title()}: {count}", file=sys.stderr)

    def exit_with_error(self, error: ToolError) -> None:
        """Log error and exit program."""
        self.log_error(error)
        self.print_error(error)
        self.print_error_summary()
        sys.exit(error.exit_code)

    def exit_if_errors(
        self,
        min_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> None:
        """Exit if errors of specified severity or higher exist."""
        critical_errors = [
            e for e in self.errors if e.severity.value in ["critical", "high"]
        ]
        if critical_errors or (min_severity == ErrorSeverity.MEDIUM and self.errors):
            self.print_error_summary()
            sys.exit(1)

    def safe_execute(
        self,
        operation: Callable[..., T],
        operation_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute operation with error handling."""
        try:
            return operation(*args, **kwargs)
        except FileNotFoundError as e:
            error = ToolError(
                severity=ErrorSeverity.CRITICAL,
                error_code="FILE_NOT_FOUND",
                message=f"File not found during {operation_name}: {e!s}",
                context={"operation": operation_name},
            )
            self.log_error(error)
            raise
        except PermissionError as e:
            error = ToolError(
                severity=ErrorSeverity.HIGH,
                error_code="PERMISSION_ERROR",
                message=f"Permission denied during {operation_name}: {e!s}",
                suggestion="Check file and directory permissions",
                context={"operation": operation_name},
            )
            self.log_error(error)
            raise
        except OSError as e:
            error = self.handle_io_error(e, operation_name)
            self.log_error(error)
            raise
        except Exception as e:
            error = ToolError(
                severity=ErrorSeverity.HIGH,
                error_code="UNEXPECTED_ERROR",
                message=f"Unexpected error during {operation_name}: {e!s}",
                details=traceback.format_exc(),
                suggestion="Check input data and system resources",
                context={"operation": operation_name},
            )
            self.log_error(error)
            raise


def safe_file_read(file_path: Path, error_handler: ErrorHandler) -> str:
    """Safely read file with error handling."""
    if not file_path.exists():
        error = error_handler.handle_file_error(file_path, "read")
        error_handler.exit_with_error(error)
        raise SystemExit(error.exit_code)  # Unreachable but satisfies mypy

    try:
        return error_handler.safe_execute(
            file_path.read_text,
            f"reading file {file_path}",
            encoding="utf-8",
        )
    except Exception as exc:
        error = error_handler.handle_file_error(file_path, "read")
        error_handler.exit_with_error(error)
        raise SystemExit(error.exit_code) from exc  # Unreachable but satisfies mypy


def safe_file_write(file_path: Path, content: str, error_handler: ErrorHandler) -> None:
    """Safely write file with error handling."""
    try:
        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        error_handler.safe_execute(
            file_path.write_text,
            f"writing file {file_path}",
            content,
            encoding="utf-8",
        )
    except Exception:
        error = error_handler.handle_file_error(file_path, "write")
        error_handler.exit_with_error(error)


def safe_yaml_load(
    content: str,
    file_path: Path,
    error_handler: ErrorHandler,
) -> dict[str, Any]:
    """Safely load YAML with error handling."""
    if yaml is None:
        error = ToolError(
            severity=ErrorSeverity.CRITICAL,
            error_code="MISSING_DEPENDENCY",
            message="PyYAML is not installed. Install with: pip install pyyaml",
            context={"file": str(file_path)},
        )
        error_handler.exit_with_error(error)
        raise SystemExit(1)  # Unreachable but satisfies mypy

    try:
        result = error_handler.safe_execute(
            yaml.safe_load,
            f"parsing YAML from {file_path}",
            content,
        )
        if result is None:
            return {}
        if not isinstance(result, dict):
            error_handler.log_error(
                error_handler.handle_validation_error(
                    f"Expected YAML dict, got {type(result).__name__}",
                    context={"file_path": str(file_path)},
                )
            )
            return {}
        return result
    except Exception as e:
        error = error_handler.handle_yaml_error(e, file_path)
        error_handler.exit_with_error(error)
        raise SystemExit(error.exit_code) from e  # Unreachable but satisfies mypy


def validate_path_exists(
    path: Path,
    path_type: str,
    error_handler: ErrorHandler,
) -> Path:
    """Validate path exists and is of correct type."""
    if not path.exists():
        if path_type == "file":
            error = error_handler.handle_file_error(path, "access")
        else:
            error = error_handler.handle_directory_error(path, "access")
        error_handler.exit_with_error(error)

    if path_type == "file" and not path.is_file():
        error = ToolError(
            severity=ErrorSeverity.HIGH,
            error_code="INVALID_FILE_TYPE",
            message=f"Path is not a file: {path}",
            context={
                "expected_type": "file",
                "actual_type": "directory" if path.is_dir() else "unknown",
            },
        )
        error_handler.exit_with_error(error)

    if path_type == "directory" and not path.is_dir():
        error = ToolError(
            severity=ErrorSeverity.HIGH,
            error_code="INVALID_DIRECTORY_TYPE",
            message=f"Path is not a directory: {path}",
            context={
                "expected_type": "directory",
                "actual_type": "file" if path.is_file() else "unknown",
            },
        )
        error_handler.exit_with_error(error)

    return path
