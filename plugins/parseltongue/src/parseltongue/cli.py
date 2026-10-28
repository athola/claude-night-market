"""Provide command-line interface for parseltongue."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

from parseltongue.analysis.async_analysis import analyze_async_functions
from parseltongue.analysis.code_transformation import CodeTransformationSkill
from parseltongue.analysis.compatibility_checker import CompatibilityChecker
from parseltongue.analysis.pattern_matching import PatternMatchingSkill
from parseltongue.analysis.testing_guide import analyze_testing


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

    parser.add_argument(
        "--test-path",
        type=Path,
        default=None,
        help="Test file to analyze alongside the source (test-guide only)",
    )

    args = parser.parse_args(argv)

    path: Path = args.path
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    if not re.fullmatch(r"\d+(\.\d+)*", args.target_version):
        print(
            f"Error: invalid target version {args.target_version!r}; "
            "expected a dotted number such as 3.9",
            file=sys.stderr,
        )
        return 1

    test_code = (
        args.test_path.read_text(encoding="utf-8", errors="replace")
        if args.test_path
        else ""
    )

    if path.is_file():
        sources = {path.name: path.read_text(encoding="utf-8", errors="replace")}
    else:
        sources = _read_directory(path)
    sources = {name: code for name, code in sources.items() if code}
    if not sources:
        print("No Python code found.", file=sys.stderr)
        return 1

    if path.is_file():
        result = _run_command(
            args.command, next(iter(sources.values())), args.target_version, test_code
        )
    else:
        files = {
            name: _run_command(args.command, code, args.target_version, test_code)
            for name, code in sources.items()
        }
        result = {"files": files}
        if any("error" in report for report in files.values()):
            result["error"] = "one or more files failed to analyze"
    print(json.dumps(result, indent=2, default=str))
    return 1 if "error" in result else 0


_SKIPPED_DIRECTORIES = frozenset(
    {"venv", "env", "node_modules", "site-packages", "__pycache__"}
)


def _read_directory(root: Path) -> dict[str, str]:
    """Read each .py file under root, skipping hidden and environment dirs."""
    sources: dict[str, str] = {}
    for py_file in sorted(root.rglob("*.py")):
        relative = py_file.relative_to(root)
        parents = relative.parts[:-1]
        if any(
            part.startswith(".") or part in _SKIPPED_DIRECTORIES for part in parents
        ):
            continue
        sources[relative.as_posix()] = py_file.read_text(
            encoding="utf-8", errors="replace"
        )
    return sources


def _run_command(
    command: str, code: str, target_version: str, test_code: str = ""
) -> dict:
    if command == "analyze-async":
        return asyncio.run(analyze_async_functions(code))

    if command == "check-compat":
        return CompatibilityChecker().check_compatibility(code, [target_version])

    if command == "detect-patterns":
        return asyncio.run(PatternMatchingSkill().find_patterns(code))

    if command == "test-guide":
        return asyncio.run(analyze_testing(code, test_code))

    if command == "transform":
        return asyncio.run(CodeTransformationSkill().transform_code(code))

    return {"error": f"Unknown command: {command}"}


if __name__ == "__main__":
    sys.exit(main())
