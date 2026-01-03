#!/usr/bin/env python3
"""Test Analysis Tool.

Analyzes codebase to identify test gaps, coverage issues, and areas needing
test updates. Part of the test-updates skill tooling suite.

Usage:
    python test_analyzer.py --scan /path/to/codebase
    python test_analyzer.py --coverage /path/to/tests
    python test_analyzer.py --changes /path/to/repo
"""

import argparse
import ast
import json
import shutil
import subprocess
from pathlib import Path


class TestAnalyzer:
    """Analyzes codebases for test coverage and gaps."""

    def __init__(self, codebase_path: Path) -> None:
        """Initialize the test analyzer."""
        self.codebase_path = Path(codebase_path)
        self.test_patterns = ["test_*.py", "*_test.py"]
        self.source_patterns = ["*.py"]

    def scan_for_test_gaps(self) -> dict[str, any]:
        """Scan codebase for files without corresponding tests."""
        results = {
            "source_files": [],
            "test_files": [],
            "uncovered_files": [],
            "coverage_gaps": [],
        }

        # Find all source files
        for pattern in self.source_patterns:
            results["source_files"].extend(self.codebase_path.rglob(pattern))

        # Filter out test files and __init__.py
        results["source_files"] = [
            f
            for f in results["source_files"]
            if not any(p in f.name for p in ["test_", "_test.py"])
            and f.name != "__init__.py"
            and "test" not in f.parts
        ]

        # Find all test files
        for pattern in self.test_patterns:
            results["test_files"].extend(self.codebase_path.rglob(pattern))

        # Find uncovered files
        source_names = {self._get_test_name(f) for f in results["source_files"]}
        test_names = {f.stem for f in results["test_files"]}

        results["uncovered_files"] = list(source_names - test_names)

        # Analyze coverage gaps
        for source_file in results["source_files"]:
            gap_info = self._analyze_file_coverage(source_file, results["test_files"])
            if gap_info:
                results["coverage_gaps"].append(gap_info)

        return results

    def _get_test_name(self, source_file: Path) -> str:
        """Get expected test name for source file."""
        if source_file.stem.startswith("test_"):
            return source_file.stem
        return f"test_{source_file.stem}"

    def _analyze_file_coverage(self, source_file: Path, test_files: list[Path]) -> dict:
        """Analyze coverage for a specific source file."""
        # Parse source file
        try:
            with open(source_file) as f:
                source_tree = ast.parse(f.read())
        except (OSError, SyntaxError):
            return None

        # Extract functions and classes
        functions = [
            node.name
            for node in ast.walk(source_tree)
            if isinstance(node, ast.FunctionDef)
        ]
        classes = [
            node.name
            for node in ast.walk(source_tree)
            if isinstance(node, ast.ClassDef)
        ]

        # Find corresponding test file
        test_file = self._find_test_file(source_file, test_files)
        if not test_file:
            return {
                "file": str(source_file),
                "missing_tests": functions + classes,
                "test_file": None,
                "coverage_percentage": 0,
            }

        # Parse test file
        try:
            with open(test_file) as f:
                test_tree = ast.parse(f.read())
        except (OSError, SyntaxError):
            return {
                "file": str(source_file),
                "missing_tests": functions + classes,
                "test_file": str(test_file),
                "coverage_percentage": 0,
            }

        # Find tested functions/classes
        test_functions = []
        for node in ast.walk(test_tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Extract what's being tested from test name
                test_functions.append(node.name[5:])  # Remove 'test_' prefix

        # Calculate coverage
        missing = []
        for item in functions + classes:
            if not any(item.lower() in func.lower() for func in test_functions):
                missing.append(item)

        total_items = len(functions) + len(classes)
        coverage_percentage = (
            ((total_items - len(missing)) / total_items * 100) if total_items > 0 else 0
        )

        return {
            "file": str(source_file),
            "missing_tests": missing,
            "test_file": str(test_file),
            "coverage_percentage": coverage_percentage,
        }

    def _find_test_file(self, source_file: Path, test_files: list[Path]) -> Path:
        """Find corresponding test file for source file."""
        # Try various naming patterns
        test_name_patterns = [
            f"test_{source_file.stem}.py",
            f"{source_file.stem}_test.py",
        ]

        # Look in test directories
        test_dirs = ["tests", "test", "tests/unit", "tests/integration"]

        for test_dir in test_dirs:
            test_dir_path = self.codebase_path / test_dir
            if test_dir_path.exists():
                for pattern in test_name_patterns:
                    test_file = test_dir_path / pattern
                    if test_file in test_files:
                        return test_file

        # Look in same directory
        for pattern in test_name_patterns:
            test_file = source_file.parent / pattern
            if test_file in test_files:
                return test_file

        return None

    def analyze_git_changes(self) -> dict[str, any]:
        """Analyze git changes to identify files needing test updates."""
        try:
            # Get changed files
            git_executable = shutil.which("git") or "git"
            # nosec: S607 - git_executable is from shutil.which, commands are safe
            result = subprocess.run(  # noqa: S603 safe: git_executable from PATH, args constant
                [git_executable, "diff", "--name-only", "HEAD~1"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.codebase_path,
            )

            if result.returncode != 0:
                return {"error": "Not a git repository or no history"}

            changed_files = [
                Path(f.strip())
                for f in result.stdout.split("\n")
                if f.strip() and f.strip().endswith(".py")
            ]

            # Categorize changes
            categories = {"modified": [], "added": [], "deleted": [], "renamed": []}

            for file_path in changed_files:
                if file_path.exists():
                    # Get diff type
                    # nosec: S607 - git_executable is from shutil.which, commands are safe
                    diff_result = subprocess.run(  # noqa: S603 safe: git_executable from PATH, args constant
                        [
                            git_executable,
                            "diff",
                            "--name-status",
                            "HEAD~1",
                            "--",
                            str(file_path),
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        cwd=self.codebase_path,
                    )

                    if diff_result.returncode == 0:
                        status = diff_result.stdout.split("\t")[0]
                        if "M" in status:
                            categories["modified"].append(file_path)
                        elif "A" in status:
                            categories["added"].append(file_path)

            return {
                "changed_files": [str(f) for f in changed_files],
                "categories": {k: [str(f) for f in v] for k, v in categories.items()},
                "needs_tests": categories["added"] + categories["modified"],
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_report(self, analysis_type: str = "coverage") -> str:
        """Generate analysis report."""
        if analysis_type == "coverage":
            results = self.scan_for_test_gaps()
        elif analysis_type == "changes":
            results = self.analyze_git_changes()
        else:
            return "Invalid analysis type. Use 'coverage' or 'changes'."

        return json.dumps(results, indent=2)


def main() -> None:
    """CLI entry point.

    Returns (JSON when --output-json):
        success (bool): Whether analysis completed
        data.source_files (list): Source files found
        data.test_files (list): Test files found
        data.uncovered_files (list): Files without tests
        data.coverage_gaps (list): Detailed coverage gap info
    """
    parser = argparse.ArgumentParser(
        description="Analyze codebase for test coverage gaps and changes"
    )
    parser.add_argument("--scan", type=str, help="Scan directory for test gaps")
    parser.add_argument("--coverage", type=str, help="Analyze test coverage")
    parser.add_argument("--changes", type=str, help="Analyze git changes needing tests")
    parser.add_argument(
        "--report",
        choices=["coverage", "changes"],
        default="coverage",
        help="Report type to generate",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON for programmatic use",
    )

    args = parser.parse_args()

    target_path = args.scan or args.coverage or args.changes
    if not target_path:
        parser.print_help()
        return

    try:
        analyzer = TestAnalyzer(target_path)

        if args.changes:
            results = analyzer.analyze_git_changes()
        else:
            results = analyzer.scan_for_test_gaps()

        # Convert Path objects to strings for JSON serialization
        serializable_results = _make_serializable(results)

        if args.output_json:
            output = {
                "success": True,
                "data": serializable_results,
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("=" * 60)
            print("Test Analysis Report")
            print("=" * 60)
            print(f"\nTarget: {target_path}")
            print(f"Report type: {args.report}")

            if "uncovered_files" in results:
                print(f"\nUncovered files ({len(results['uncovered_files'])}):")
                for f in results["uncovered_files"][:10]:
                    print(f"  - {f}")
                if len(results["uncovered_files"]) > 10:
                    print(f"  ... and {len(results['uncovered_files']) - 10} more")

            if "coverage_gaps" in results:
                print(f"\nCoverage gaps ({len(results['coverage_gaps'])}):")
                for gap in results["coverage_gaps"][:5]:
                    print(
                        f"  - {gap.get('file', 'unknown')}: {gap.get('reason', 'no details')}"
                    )

            print("\nFor full JSON output, use --output-json")

    except Exception as e:
        if args.output_json:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            print(f"Error: {e}")
        raise SystemExit(1) from e


def _make_serializable(obj):
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, Path):
        return str(obj)
    else:
        return obj


if __name__ == "__main__":
    main()
