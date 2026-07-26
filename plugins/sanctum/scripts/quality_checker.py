#!/usr/bin/env python3
"""Test Quality Checker.

Validates test quality using static analysis, dynamic execution,
and metrics tracking. Part of the test-updates skill tooling suite.

Usage:
    python quality_checker.py --check /path/to/tests
    python quality_checker.py --coverage /path/to/project
    python quality_checker.py --validate test_file.py
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import logging
import os
import re
import subprocess
import sys as _sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# D-13: pull canonical CLI envelope helpers from leyline.
_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
if str(_LEYLINE_SRC) not in _sys.path:
    _sys.path.insert(0, str(_LEYLINE_SRC))

from leyline.cli_envelope import (  # noqa: E402 - import after sys.path setup
    error_envelope,
    success_envelope,
)

# Constants for quality thresholds
MIN_TEST_NAME_LENGTH = 10
EXCELLENT_QUALITY_SCORE = 90
GOOD_QUALITY_SCORE = 80
FAIR_QUALITY_SCORE = 70
MIN_DOCUMENTATION_RATIO = 0.1
MAX_TEST_DURATION = 5
MAX_TEST_LENGTH = 50
MIN_ASSERTIONS_PER_TEST = 2


class QualityLevel(Enum):
    """Test quality levels for classification."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class QualityIssue:
    """Represents a quality issue found in tests."""

    severity: str  # 'error', 'warning', 'info'
    category: str
    message: str
    line_number: int | None = None
    suggestion: str | None = None


class TestQualityChecker:
    """Validate and score test quality."""

    def __init__(self, test_path: Path, source_path: Path | None = None) -> None:
        """Initialize the test quality checker.

        Args:
            test_path: Path to the test file or directory
            source_path: Optional path to the source code being tested

        """
        self.test_path = Path(test_path)
        self.source_path = Path(source_path) if source_path else None
        self.issues: list[QualityIssue] = []
        self._cached_content: str | None = None

    def _get_test_content(self) -> str:
        if self._cached_content is None:
            with open(self.test_path) as f:
                self._cached_content = f.read()
        return self._cached_content

    def run_full_validation(self) -> dict[str, Any]:
        """Run complete quality validation."""
        results = {
            "static_analysis": self.run_static_analysis(),
            "dynamic_validation": self.run_dynamic_validation(),
            "metrics": self.calculate_metrics(),
            "quality_score": 0,
            "quality_level": QualityLevel.POOR,
            "recommendations": [],
        }

        # Calculate overall score
        quality_score = self._calculate_overall_score(results)
        results["quality_score"] = quality_score
        results["quality_level"] = self._determine_quality_level(quality_score)
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def run_static_analysis(self) -> dict[str, Any]:
        """Perform static code analysis."""
        analysis = {
            "structure_issues": [],
            "naming_issues": [],
            "assertion_issues": [],
            "bdd_compliance": [],
            "documentation": [],
        }

        if not self.test_path.exists():
            analysis["structure_issues"].append(
                QualityIssue(
                    "error",
                    "structure",
                    f"Test file not found: {self.test_path}",
                ),
            )
            return analysis

        test_content = self._get_test_content()

        try:
            tree = ast.parse(test_content)
        except SyntaxError as e:
            analysis["structure_issues"].append(
                QualityIssue(
                    "error",
                    "structure",
                    f"Syntax error in test file: {e}",
                    e.lineno,
                    "Fix syntax errors before proceeding",
                ),
            )
            return analysis

        # Check test structure
        self._check_test_structure(tree, analysis)
        self._check_naming_conventions(tree, analysis)
        self._check_assertion_quality(tree, analysis)
        self._check_bdd_compliance(tree, analysis)
        self._check_documentation(test_content, analysis)

        return analysis

    def _check_test_structure(self, tree: ast.AST, analysis: dict) -> None:
        """Check test file structure."""
        # Check for test functions
        test_functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]

        if not test_functions:
            analysis["structure_issues"].append(
                QualityIssue("error", "structure", "No test functions found"),
            )

        # Check for imports
        imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

        if not imports:
            analysis["structure_issues"].append(
                QualityIssue(
                    "warning",
                    "structure",
                    "No imports found - may need pytest or unittest",
                ),
            )

    def _check_naming_conventions(self, tree: ast.AST, analysis: dict) -> None:
        """Check test naming conventions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Check descriptive names
                if len(node.name) < MIN_TEST_NAME_LENGTH:
                    analysis["naming_issues"].append(
                        QualityIssue(
                            "warning",
                            "naming",
                            f"Test name '{node.name}' too short - be more descriptive",
                            node.lineno,
                        ),
                    )

                # Check for underscore separation
                if " " in node.name:
                    analysis["naming_issues"].append(
                        QualityIssue(
                            "error",
                            "naming",
                            f"Test name '{node.name}' contains spaces",
                            node.lineno,
                            "Use underscores: test_example_behavior",
                        ),
                    )

    def _is_vague_result_assertion(self, assert_node: ast.Assert) -> bool:
        """Return True when the assertion compares a bare ``result`` name.

        Catches ``assert result == <value>`` patterns where the generic
        variable name gives no information about what was verified.
        """
        return (
            isinstance(assert_node.test, ast.Compare)
            and isinstance(assert_node.test.left, ast.Name)
            and assert_node.test.left.id == "result"
        )

    @staticmethod
    def _is_raises_context(node: ast.AST) -> bool:
        """Return True for a ``with pytest.raises``/``warns`` context block.

        These context managers assert that their body raises or warns, so a
        test built around one is not assertion-free even with no ``assert``.
        """
        if not isinstance(node, ast.With):
            return False
        for item in node.items:
            call = item.context_expr
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                name = ""
            if name in {"raises", "warns"}:
                return True
        return False

    def _check_assertion_quality(self, tree: ast.AST, analysis: dict) -> None:
        """Check assertion quality and patterns."""
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ):
                continue
            assertions = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
            raises_blocks = [n for n in ast.walk(node) if self._is_raises_context(n)]

            if not assertions and not raises_blocks:
                analysis["assertion_issues"].append(
                    QualityIssue(
                        "error",
                        "assertion",
                        f"Test '{node.name}' has no assertions",
                        node.lineno,
                    ),
                )
            elif (
                len(assertions) == 1
                and not raises_blocks
                and self._is_vague_result_assertion(assertions[0])
            ):
                analysis["assertion_issues"].append(
                    QualityIssue(
                        "warning",
                        "assertion",
                        f"Vague assertion in '{node.name}' - be more specific",
                        assertions[0].lineno,
                        "Example: assert result.status == 'success'",
                    ),
                )

    _BDD_KEYWORDS = ("given", "when", "then", "and")

    def _check_bdd_compliance(self, tree: ast.AST, analysis: dict) -> None:
        """Check BDD pattern compliance using AST docstring extraction."""
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ):
                continue
            docstring = ast.get_docstring(node)
            if not docstring:
                continue
            lower = docstring.lower()
            missing = [kw.upper() for kw in self._BDD_KEYWORDS if kw not in lower]
            if missing:
                analysis["bdd_compliance"].append(
                    QualityIssue(
                        "warning",
                        "bdd",
                        f"Test '{node.name}' missing BDD patterns",
                        suggestion=f"Add {', '.join(missing)} patterns",
                    ),
                )

    def _check_documentation(self, test_content: str, analysis: dict) -> None:
        """Check test documentation quality."""
        # Check for module docstring
        if not test_content.startswith('"""'):
            analysis["documentation"].append(
                QualityIssue(
                    "warning",
                    "documentation",
                    "Missing module docstring - describe what these tests cover",
                ),
            )

        # Check test function docstrings
        test_functions = re.finditer(
            r'def (test_[^(]+).*?"""(.*?)"""',
            test_content,
            re.DOTALL,
        )

        documented_tests = sum(1 for _ in test_functions)
        total_tests = len(re.findall(r"def test_", test_content))

        if documented_tests < total_tests:
            analysis["documentation"].append(
                QualityIssue(
                    "info",
                    "documentation",
                    f"{total_tests - documented_tests} tests lack documentation",
                ),
            )

    def run_dynamic_validation(self) -> dict[str, Any]:
        """Run tests and validate dynamic behavior."""
        validation: dict[str, Any] = {
            "execution_result": None,
            "test_duration": 0,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 0,
        }

        try:
            # Run pytest with JSON output
            start_time = time.time()
            # Use the interpreter already running this checker rather than
            # resolving `python` from PATH: bare `python` does not exist on
            # Debian/WSL boxes, and a PATH interpreter may not be the
            # environment whose pytest/pytest_jsonreport we probed above.
            python_path = _sys.executable

            # The json-report plugin gives rich pass/fail data but is optional.
            # Only request it when installed, otherwise a missing plugin makes
            # pytest exit with a usage error that looks like a failing run.
            report_path = None
            json_args = []
            if importlib.util.find_spec("pytest_jsonreport") is not None:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as tmp_file:
                    report_path = tmp_file.name
                json_args = ["--json-report", f"--json-report-file={report_path}"]

            try:
                result = subprocess.run(
                    [
                        python_path,
                        "-m",
                        "pytest",
                        str(self.test_path),
                        *json_args,
                        "-q",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                validation["test_duration"] = time.time() - start_time
                validation["execution_result"] = result.returncode

                parsed = self._parse_test_report(
                    report_path, fallback_returncode=result.returncode
                )
                validation["passed"] = parsed["passed"]
                validation["failures"] = parsed["failures"]
                validation["errors"] = parsed["errors"]
                validation["skipped"] = parsed["skipped"]

            except subprocess.TimeoutExpired:
                validation["errors"].append("Test execution timed out (>30s)")
                validation["test_duration"] = 30
            except Exception as e:
                validation["errors"].append(f"Test execution failed: {e}")
            finally:
                # Clean up temp file when one was created
                if report_path is not None:
                    try:
                        os.unlink(report_path)
                    except (OSError, FileNotFoundError):
                        pass

        except Exception as e:
            validation["errors"].append(f"Test setup failed: {e}")

        return validation

    def _parse_test_report(
        self, report_path, fallback_returncode: int
    ) -> dict[str, Any]:
        """Parse a pytest JSON report file into a summary dict.

        Falls back to synthetic counts when the file is missing or unreadable.
        The return code is trusted only for the unambiguous cases: 0 means all
        passed and 1 means real failures. Other codes (interrupted, usage error
        from a missing plugin, or no tests collected) mean the run could not be
        measured, not that tests failed, so no synthetic failure is recorded.
        """
        try:
            with open(report_path) as f:
                report = json.load(f)
            summary = report.get("summary", {})
            return {
                "passed": summary.get("passed", 0),
                "failures": summary.get("failed", 0),
                "errors": summary.get("error", 0),
                "skipped": summary.get("skipped", 0),
            }
        except (json.JSONDecodeError, FileNotFoundError, OSError, TypeError):
            if fallback_returncode == 0:
                return {"passed": 1, "failures": 0, "errors": 0, "skipped": 0}
            if fallback_returncode == 1:
                return {"passed": 0, "failures": 1, "errors": 0, "skipped": 0}
            # Exit >= 2 -- interrupted (2), internal error (3), usage error
            # (4), or no tests collected (5) -- means the run could not be
            # measured. It is not a test failure (failures/errors stay 0, so
            # the "real failures" predicate is unaffected), but the explicit
            # inconclusive flag stops a crashed or uncollectable suite from
            # scoring clean with no warning.
            return {
                "passed": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "inconclusive": True,
            }

    def calculate_metrics(self) -> dict[str, Any]:
        """Calculate quality metrics."""
        metrics = {
            "test_count": 0,
            "assertion_count": 0,
            "average_test_length": 0,
            "complexity_score": 0,
            "documentation_ratio": 0,
        }

        if not self.test_path.exists():
            return metrics

        content = self._get_test_content()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return metrics

        # Count tests
        test_functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        metrics["test_count"] = len(test_functions)

        # Count assertions
        metrics["assertion_count"] = sum(
            1 for node in ast.walk(tree) if isinstance(node, ast.Assert)
        )

        # Calculate average test length
        if test_functions:
            total_lines = 0
            for test in test_functions:
                if hasattr(test, "end_lineno"):
                    total_lines += test.end_lineno - test.lineno + 1
                else:
                    total_lines += len(test.body)
            metrics["average_test_length"] = total_lines / len(test_functions)

        # Calculate complexity (simplified)
        metrics["complexity_score"] = self._calculate_complexity(tree)

        # Documentation ratio
        docstring_lines = sum(
            len(doc.split("\n"))
            for doc in re.findall(r'"""(.*?)"""', content, re.DOTALL)
        )
        total_lines = len(content.split("\n"))
        metrics["documentation_ratio"] = (
            docstring_lines / total_lines if total_lines > 0 else 0
        )

        return metrics

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(
                node, (ast.If, ast.While, ast.For, ast.With, ast.ExceptHandler)
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    @staticmethod
    def _has_real_failures(dynamic: dict) -> bool:
        """Return True when the run recorded genuine failures or errors.

        Documents the shared 'the run had real problems' predicate in one
        place: a nonzero pytest exit code alone never qualifies (a coverage
        gate can fail an all-passing run), but recorded failures or errors do.
        An inconclusive run (pytest exit >= 2) is handled separately via the
        ``inconclusive`` flag, not here.
        """
        return bool(dynamic["failures"] or dynamic["errors"])

    def _calculate_overall_score(self, results: dict) -> int:
        """Calculate overall quality score (0-100)."""
        score = 100

        # Deduct points for issues
        static = results["static_analysis"]
        for category in static.values():
            for issue in category:
                if issue.severity == "error":
                    score -= 10
                elif issue.severity == "warning":
                    score -= 5
                elif issue.severity == "info":
                    score -= 2

        # Consider test execution. A nonzero pytest exit code alone does not
        # mean tests failed (a coverage threshold can fail the run while every
        # test passes), so penalize on real failures/errors or on a run that
        # could not be measured (inconclusive); never on exit code alone.
        dynamic = results["dynamic_validation"]
        if self._has_real_failures(dynamic) or dynamic.get("inconclusive"):
            score -= 20

        # Consider metrics
        metrics = results["metrics"]
        if metrics["test_count"] == 0:
            score -= 30

        if metrics["documentation_ratio"] < MIN_DOCUMENTATION_RATIO:
            score -= 10

        # Bonus points for good practices
        if dynamic["passed"] == metrics["test_count"] and metrics["test_count"] > 0:
            score += 5

        score = max(0, min(100, score))
        return int(score)

    def _determine_quality_level(self, score: int) -> QualityLevel:
        """Determine quality level from score."""
        if score >= EXCELLENT_QUALITY_SCORE:
            return QualityLevel.EXCELLENT
        if score >= GOOD_QUALITY_SCORE:
            return QualityLevel.GOOD
        if score >= FAIR_QUALITY_SCORE:
            return QualityLevel.FAIR
        return QualityLevel.POOR

    def _generate_recommendations(self, results: dict) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # From static analysis
        static = results["static_analysis"]
        if static["structure_issues"]:
            recommendations.append("Fix structural issues before adding new tests")

        if static["naming_issues"]:
            recommendations.append(
                "Use descriptive, snake_case test names that describe behavior",
            )

        if static["assertion_issues"]:
            recommendations.append(
                "Write specific, meaningful assertions that verify behavior",
            )

        if static["bdd_compliance"]:
            recommendations.append(
                "Add Given/When/Then clauses to test docstrings for BDD compliance",
            )

        if static["documentation"]:
            recommendations.append(
                "Add detailed documentation to explain test scenarios",
            )

        # From dynamic validation
        dynamic = results["dynamic_validation"]
        if dynamic.get("inconclusive"):
            recommendations.append(
                "Test run was inconclusive (pytest exit code >= 2); "
                "investigate the suite before trusting this score",
            )
        elif self._has_real_failures(dynamic):
            recommendations.append("Fix failing tests before proceeding")

        if dynamic["test_duration"] > MAX_TEST_DURATION:
            recommendations.append(
                "Optimize test performance - tests should run quickly",
            )

        # From metrics
        metrics = results["metrics"]
        if metrics["average_test_length"] > MAX_TEST_LENGTH:
            recommendations.append("Break down long tests into smaller, focused tests")

        if (
            metrics["assertion_count"] / max(metrics["test_count"], 1)
            < MIN_ASSERTIONS_PER_TEST
        ):
            recommendations.append("Add more assertions to thoroughly test behavior")

        return recommendations


def _run_check_or_validate(checker: TestQualityChecker, args) -> None:
    """Run a check/validate command and emit output per args settings."""
    results = checker.run_full_validation()
    if args.output_json:
        output_result(results, args)
    else:
        output = format_report(results)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Check test quality")
    parser.add_argument("--check", type=str, help="Test file or directory to check")
    parser.add_argument("--coverage", type=str, help="Check test coverage for project")
    parser.add_argument("--validate", type=str, help="Validate specific test file")
    parser.add_argument("--output", type=str, help="Output report to file")
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON for programmatic use",
    )

    args = parser.parse_args()

    # Both failure arms below emit an error envelope and then exit nonzero.
    # They previously fell through to a 0 exit, so a missing test path and a
    # crash mid-check were indistinguishable from a clean run to any caller
    # reading the status rather than parsing the JSON.
    try:
        if args.check or args.validate:
            test_path = Path(args.check or args.validate)
            if not test_path.exists():
                output_error(f"Test path not found: {test_path}", args)
                raise SystemExit(1)

            checker = TestQualityChecker(test_path)
            _run_check_or_validate(checker, args)

        else:
            parser.print_help()

    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in quality_checker")
        output_error(f"Error checking quality: {e}", args)
        raise SystemExit(1) from e


def output_result(result: dict, args) -> None:
    """Output result in requested format."""
    output = json.dumps(success_envelope(result), indent=2, default=str)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)


def output_error(message: str, args) -> None:
    """Output error in requested format."""
    error_output = json.dumps(error_envelope(message), indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(error_output)
    else:
        print(error_output)


def format_report(results: dict) -> str:
    """Format quality report for human reading."""
    level = results["quality_level"]
    level_str = level.value if isinstance(level, QualityLevel) else str(level)
    report = f"""
Test Quality Report
==================

Overall Quality Score: {results["quality_score"]}/100
Quality Level: {level_str.upper()}

Dynamic Validation
------------------
Tests Passed: {results["dynamic_validation"]["passed"]}
Tests Failed: {results["dynamic_validation"]["failures"]}
Tests Errors: {results["dynamic_validation"]["errors"]}
Test Duration: {results["dynamic_validation"]["test_duration"]:.2f}s

Metrics
-------
Test Count: {results["metrics"]["test_count"]}
Assertion Count: {results["metrics"]["assertion_count"]}
Average Test Length: {results["metrics"]["average_test_length"]:.1f} lines
Documentation Ratio: {results["metrics"]["documentation_ratio"]:.1%}

Recommendations
--------------
"""
    for i, rec in enumerate(results["recommendations"], 1):
        report += f"{i}. {rec}\n"

    return report


if __name__ == "__main__":
    main()
