#!/usr/bin/env python3
"""CLI Framework for Abstract scripts.

Provides standardized CLI creation with common arguments, output formatting,
and integration with core Abstract functionality.
"""

import argparse
import json
import sys
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from .base import AbstractScript
from .config import AbstractConfig
from .errors import ErrorHandler

# Type variable for generic result types
T = TypeVar("T")


@dataclass
class CLIResult(Generic[T]):
    """Standard result wrapper for CLI operations."""

    success: bool
    data: T | None = None
    error: str | None = None
    warnings: list[str] | None = None


class OutputFormatter:
    """Handles output formatting for CLI results."""

    @staticmethod
    def format_json(data: Any) -> str:
        """Format data as JSON.

        Args:
            data: Data to format.

        Returns:
            JSON string.

        """
        if is_dataclass(data) and not isinstance(data, type):
            data = asdict(data)
        elif isinstance(data, list):
            data = [asdict(item) if is_dataclass(item) else item for item in data]
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def format_summary(
        data: Any,
        summary_func: Callable[[Any], str] | None = None,
    ) -> str:
        """Format data as a summary.

        Args:
            data: Data to format.
            summary_func: Optional function to generate summary.

        Returns:
            Summary string.

        """
        if summary_func:
            return summary_func(data)
        if is_dataclass(data) and not isinstance(data, type):
            return str(data)
        return str(data)

    @staticmethod
    def format_table(
        rows: list[dict[str, Any]],
        columns: list[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Format data as a table.

        Args:
            rows: List of row dictionaries.
            columns: Columns to include (all if None).
            headers: Header labels for columns.

        Returns:
            Table string.

        """
        if not rows:
            return "No data"

        columns = columns or list(rows[0].keys())
        headers = headers or {col: col.replace("_", " ").title() for col in columns}

        # Calculate column widths
        widths = {col: len(headers.get(col, col)) for col in columns}
        for row in rows:
            for col in columns:
                val = str(row.get(col, ""))
                widths[col] = max(widths[col], len(val))

        # Build table
        lines = []

        # Header
        header_line = " | ".join(
            headers.get(col, col).ljust(widths[col]) for col in columns
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in rows:
            row_line = " | ".join(
                str(row.get(col, "")).ljust(widths[col]) for col in columns
            )
            lines.append(row_line)

        return "\n".join(lines)


class AbstractCLI(ABC):
    """Base class for Abstract CLI tools.

    Provides standardized argument parsing, output formatting,
    and integration with core Abstract functionality.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
    ) -> None:
        """Initialize the CLI.

        Args:
            name: CLI tool name.
            description: CLI tool description.
            version: CLI tool version.

        """
        self.name = name
        self.description = description
        self.version = version
        self._script = AbstractScript(name)
        self._parser: argparse.ArgumentParser | None = None
        self._formatter = OutputFormatter()

    @property
    def config(self) -> AbstractConfig:
        """Get the configuration."""
        return self._script.config

    @config.setter
    def config(self, value: AbstractConfig) -> None:
        """Set the configuration."""
        self._script.config = value

    @property
    def error_handler(self) -> ErrorHandler:
        """Get the error handler."""
        return self._script.error_handler

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with common arguments.

        Returns:
            Configured ArgumentParser.

        """
        if self._parser is not None:
            return self._parser

        self._parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add common arguments
        self._add_common_arguments(self._parser)

        # Add tool-specific arguments
        self.add_arguments(self._parser)

        return self._parser

    def _add_common_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add common arguments shared by all CLIs.

        Args:
            parser: ArgumentParser to add arguments to.

        """
        # Version
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {self.version}",
        )

        # Output format
        parser.add_argument(
            "--format",
            "-f",
            choices=["text", "json", "summary", "table"],
            default="text",
            help="Output format (default: text)",
        )

        # Verbosity
        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (can be repeated)",
        )

        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Suppress non-essential output",
        )

        # Project root
        parser.add_argument(
            "--project-root",
            type=Path,
            help="Project root directory (auto-detected if not specified)",
        )

        # Config file
        parser.add_argument(
            "--config",
            type=Path,
            help="Path to configuration file",
        )

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add tool-specific arguments.

        Args:
            parser: ArgumentParser to add arguments to.

        """

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> CLIResult:
        """Execute the CLI command.

        Args:
            args: Parsed command line arguments.

        Returns:
            CLIResult with operation result.

        """

    def format_output(
        self,
        result: CLIResult,
        format_type: str,
        summary_func: Callable[[Any], str] | None = None,
        table_columns: list[str] | None = None,
    ) -> str:
        """Format the result for output.

        Args:
            result: CLIResult to format.
            format_type: Output format type.
            summary_func: Optional summary formatting function.
            table_columns: Columns for table format.

        Returns:
            Formatted output string.

        """
        if not result.success:
            return f"Error: {result.error}"

        data = result.data
        output: str

        if format_type == "json":
            output = self._formatter.format_json(data)
        elif format_type == "summary":
            output = self._formatter.format_summary(data, summary_func)
        elif format_type == "table":
            output = self._format_table_data(data, table_columns)
        else:  # text
            output = self.format_text(data)

        return output

    def _format_table_data(self, data: Any, table_columns: list[str] | None) -> str:
        """Format data for table output.

        Args:
            data: Data to format.
            table_columns: Columns for table format.

        Returns:
            Formatted table string.

        """
        if isinstance(data, list):
            rows = [asdict(d) if is_dataclass(d) else d for d in data]
            return self._formatter.format_table(rows, table_columns)
        if is_dataclass(data):
            return self._formatter.format_table([asdict(data)], table_columns)
        return str(data)

    def format_text(self, data: Any) -> str:
        """Format data as human-readable text.

        Override this method for custom text formatting.

        Args:
            data: Data to format.

        Returns:
            Formatted text string.

        """
        if is_dataclass(data) and not isinstance(data, type):
            return str(data)
        return str(data)

    def run(self, argv: list[str] | None = None) -> int:
        """Run the CLI.

        Args:
            argv: Command line arguments (uses sys.argv if None).

        Returns:
            Exit code (0 for success, non-zero for failure).

        """
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # Handle project root (for future use)
        _project_root = args.project_root or self._script.find_project_root()

        # Load config if specified
        if args.config:
            try:
                self.config = AbstractConfig.from_yaml(args.config)
            except Exception:
                return 1

        try:
            result = self.execute(args)
        except KeyboardInterrupt:
            return 130
        except Exception:
            if args.verbose > 0:
                traceback.print_exc()
            return 1

        # Handle warnings
        if result.warnings and not args.quiet:
            for warning in result.warnings:
                print(f"Warning: {warning}", file=sys.stderr)

        # Format and print output
        if not args.quiet or result.success:
            output = self.format_output(
                result,
                args.format,
                summary_func=getattr(self, "summary_func", None),
                table_columns=getattr(self, "table_columns", None),
            )
            if output:
                print(output)

        return 0 if result.success else 1


def cli_main(cli_class: type[AbstractCLI], **kwargs) -> None:
    """Run a CLI class with the given arguments.

    Args:
        cli_class: The CLI class to instantiate and run.
        **kwargs: Arguments to pass to CLI constructor.

    """
    cli = cli_class(**kwargs)
    sys.exit(cli.run())


class PathArgumentMixin:
    """Mixin providing common path-related arguments."""

    @staticmethod
    def add_path_arguments(
        parser: argparse.ArgumentParser,
        file_help: str = "Path to file to process",
        dir_help: str = "Path to directory to process",
        require_one: bool = True,
    ) -> None:
        """Add file and directory path arguments.

        Args:
            parser: ArgumentParser to add arguments to.
            file_help: Help text for file argument.
            dir_help: Help text for directory argument.
            require_one: Whether to require at least one path.

        """
        group = parser.add_mutually_exclusive_group(required=require_one)
        group.add_argument(
            "--file",
            type=Path,
            help=file_help,
        )
        group.add_argument(
            "--directory",
            "-d",
            type=Path,
            help=dir_help,
        )

    @staticmethod
    def add_skill_path_argument(
        parser: argparse.ArgumentParser,
        required: bool = True,
    ) -> None:
        """Add skill path argument.

        Args:
            parser: ArgumentParser to add arguments to.
            required: Whether the argument is required.

        """
        parser.add_argument(
            "--skill-path",
            type=Path,
            required=required,
            help="Path to SKILL.md file",
        )


class FilterArgumentMixin:
    """Mixin providing common filter arguments."""

    @staticmethod
    def add_severity_filter(
        parser: argparse.ArgumentParser,
        choices: list[str] | None = None,
    ) -> None:
        """Add severity filter argument.

        Args:
            parser: ArgumentParser to add arguments to.
            choices: Valid severity levels.

        """
        parser.add_argument(
            "--severity",
            choices=choices or ["critical", "high", "medium", "low"],
            help="Filter by minimum severity level",
        )

    @staticmethod
    def add_category_filter(
        parser: argparse.ArgumentParser,
        choices: list[str] | None = None,
    ) -> None:
        """Add category filter argument.

        Args:
            parser: ArgumentParser to add arguments to.
            choices: Valid categories.

        """
        parser.add_argument(
            "--category",
            choices=choices,
            help="Filter by category",
        )
