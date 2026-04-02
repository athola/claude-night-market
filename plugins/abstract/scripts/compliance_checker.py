#!/usr/bin/env python3
"""CLI wrapper for compliance-checker script.

Uses core functionality from src/abstract/skills_eval.
"""

from __future__ import annotations

from pathlib import Path

from cli_scaffold import create_parser, format_result, setup_src_path, write_output

setup_src_path()

from abstract.skills_eval import (  # noqa: E402 - import after setup_src_path() call
    ComplianceChecker as CoreComplianceChecker,
)


class ComplianceChecker(CoreComplianceChecker):
    """CLI wrapper for core compliance checking functionality."""


# For direct execution
if __name__ == "__main__":
    parser = create_parser(
        "Check compliance of skills in directory",
        add_format=True,
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing skills to check",
    )
    parser.add_argument("--rules-file", type=Path, help="Custom rules file")

    args = parser.parse_args()

    checker = ComplianceChecker(args.directory, args.rules_file)
    output = format_result(
        checker.check_compliance(),
        fmt=args.format,
        text_fn=lambda _: checker.generate_report(),
    )
    write_output(output, args.output)
