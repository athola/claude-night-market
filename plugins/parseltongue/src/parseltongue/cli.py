"""Provide command-line interface for parseltongue."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from parseltongue.analysis.async_analysis import AsyncAnalysisSkill
from parseltongue.analysis.code_transformation import CodeTransformationSkill
from parseltongue.analysis.compatibility_checker import CompatibilityChecker
from parseltongue.analysis.pattern_matching import PatternMatchingSkill
from parseltongue.analysis.testing_guide import TestingGuideSkill


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Parseltongue - Python Analysis Tools")
        print("Usage: parseltongue <command> <path>")
        print(
            "Commands: analyze-async, check-compat, detect-patterns, test-guide, transform"
        )
        return 0

    parser = argparse.ArgumentParser(
        prog="parseltongue",
        description="Parseltongue Python analysis tools",
    )
    parser.add_argument(
        "command",
        choices=[
            "analyze-async",
            "check-compat",
            "detect-patterns",
            "test-guide",
            "transform",
        ],
    )
    parser.add_argument("path", type=Path, help="File or directory to analyze")
    parser.add_argument(
        "--target-version",
        default="3.9",
        help="Target Python version (for compat check)",
    )

    args = parser.parse_args(argv)

    path: Path = args.path
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    code = path.read_text() if path.is_file() else ""
    if not code and path.is_dir():
        # Concatenate all .py files in the directory
        parts = []
        for py_file in sorted(path.rglob("*.py")):
            parts.append(py_file.read_text())
        code = "\n".join(parts)

    if not code:
        print("No Python code found.", file=sys.stderr)
        return 1

    result = _run_command(args.command, code, args.target_version)
    print(json.dumps(result, indent=2, default=str))
    return 0


def _run_command(command: str, code: str, target_version: str) -> dict:
    if command == "analyze-async":
        return asyncio.run(AsyncAnalysisSkill().analyze_async_functions(code))

    if command == "check-compat":
        return CompatibilityChecker().check_compatibility(code, [target_version])

    if command == "detect-patterns":
        return asyncio.run(PatternMatchingSkill().find_patterns(code))

    if command == "test-guide":
        return asyncio.run(TestingGuideSkill().analyze_testing(code))

    if command == "transform":
        return asyncio.run(CodeTransformationSkill().transform_code(code))

    return {"error": f"Unknown command: {command}"}


if __name__ == "__main__":
    sys.exit(main())
