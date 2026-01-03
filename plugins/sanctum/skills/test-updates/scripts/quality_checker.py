#!/usr/bin/env python3
"""Test Quality Checker.

Validates test quality using static analysis, dynamic execution,
and metrics tracking. Part of the test-updates skill tooling suite.

Usage:
    python quality_checker.py --check /path/to/tests
    python quality_checker.py --coverage /path/to/project
    python quality_checker.py --validate test_file.py
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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
    """Validates and scores test quality."""

    def __init__(self, test_path: Path, source_path: Path | None = None) -> None:
        """Initialize the test quality checker.

        Args:
            test_path: Path to the test file or directory
            source_path: Optional path to the source code being tested

        """
        self.test_path = Path(test_path)
        self.source_path = Path(source_path) if source_path else None
        self.issues: list[QualityIssue] = []

    def run_full_validation(self) -> dict[str, any]:
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
        results["quality_score"] = self._calculate_overall_score(results)
        results["quality_level"] = self._determine_quality_level(
            results["quality_score"],
        )
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def run_static_analysis(self) -> dict[str, any]:
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

        with open(self.test_path) as f:
            test_content = f.read()

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
        self._check_bdd_compliance(test_content, analysis)
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

        # Check for test classes
        [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
        ]

        # Check for imports
        imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
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

    def _check_assertion_quality(self, tree: ast.AST, analysis: dict) -> None:
        """Check assertion quality and patterns."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                assertions = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]

                if not assertions:
                    analysis["assertion_issues"].append(
                        QualityIssue(
                            "error",
                            "assertion",
                            f"Test '{node.name}' has no assertions",
                            node.lineno,
                        ),
                    )
                elif len(assertions) == 1:
                    # Check for specific assertions
                    for assert_node in assertions:
                        if isinstance(assert_node.test, ast.Compare):
                            # Check for vague assertions
                            if (
                                isinstance(assert_node.test.left, ast.Name)
                                and assert_node.test.left.id == "result"
                            ):
                                analysis["assertion_issues"].append(
                                    QualityIssue(
                                        "warning",
                                        "assertion",
                                        f"Vague assertion in '{node.name}' - "
                                        f"be more specific",
                                        assert_node.lineno,
                                        "Example: assert result.status == 'success'",
                                    ),
                                )

    def _check_bdd_compliance(self, test_content: str, analysis: dict) -> None:
        """Check BDD pattern compliance."""
        bdd_patterns = {
            "given": r"(?i)given\s+",
            "when": r"(?i)when\s+",
            "then": r"(?i)then\s+",
            "and": r"(?i)and\s+",
        }

        test_functions = re.findall(r"def (test_[^(]+)", test_content)

        for test_name in test_functions:
            test_match = re.search(
                f"def {test_name}\\(.*?\\):(.*?)(?=def |class |$)",
                test_content,
                re.DOTALL,
            )

            if test_match:
                test_body = test_match.group(1)

                # Check for BDD keywords in docstrings
                docstring_match = re.search(r'"""(.*?)"""', test_body, re.DOTALL)
                if docstring_match:
                    docstring = docstring_match.group(1)
                    missing_patterns = []

                    for pattern_name, pattern_regex in bdd_patterns.items():
                        if not re.search(pattern_regex, docstring):
                            missing_patterns.append(pattern_name.upper())

                    if missing_patterns:
                        analysis["bdd_compliance"].append(
                            QualityIssue(
                                "warning",
                                "bdd",
                                f"Test '{test_name}' missing BDD patterns",
                                suggestion=(
                                    f"Add {', '.join(missing_patterns)} patterns"
                                ),
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

    def run_dynamic_validation(self) -> dict[str, any]:
        """Run tests and validate dynamic behavior."""
        validation = {
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
            python_path = shutil.which("python")
            if not python_path:
                raise RuntimeError("Python not found")

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as tmp_file:
                tmp_path = tmp_file.name

            try:
                result = subprocess.run(  # noqa: S603 safe: python_path from PATH, args fixed
                    [
                        python_path,
                        "-m",
                        "pytest",
                        str(self.test_path),
                        "--json-report",
                        f"--json-report-file={tmp_path}",
                        "-q",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                validation["test_duration"] = time.time() - start_time
                validation["execution_result"] = result.returncode

                # Parse results if available
                try:
                    with open(tmp_path) as f:
                        report = json.load(f)
                        validation["passed"] = report.get("summary", {}).get(
                            "passed", 0
                        )
                        validation["failures"] = report.get("summary", {}).get(
                            "failed", 0
                        )
                        validation["errors"] = report.get("summary", {}).get("error", 0)
                        validation["skipped"] = report.get("summary", {}).get(
                            "skipped", 0
                        )
                except (json.JSONDecodeError, FileNotFoundError, OSError):
                    # Fallback to parsing output
                    if result.returncode == 0:
                        validation["passed"] = 1
                    else:
                        validation["failures"] = 1

            except subprocess.TimeoutExpired:
                validation["errors"].append("Test execution timed out (>30s)")
                validation["test_duration"] = 30
            except Exception as e:
                validation["errors"].append(f"Test execution failed: {e}")
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except (OSError, FileNotFoundError):
                    pass

        except Exception as e:
            validation["errors"].append(f"Test setup failed: {e}")

        return validation

    def calculate_metrics(self) -> dict[str, any]:
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

        with open(self.test_path) as f:
            content = f.read()

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
                node, ast.If | ast.While | ast.For | ast.With | ast.ExceptHandler
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

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

        # Consider test execution
        dynamic = results["dynamic_validation"]
        if dynamic["execution_result"] != 0:
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
        if dynamic["execution_result"] != 0:
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

    try:
        if args.check or args.validate:
            test_path = Path(args.check or args.validate)
            if not test_path.exists():
                output_error(f"Test path not found: {test_path}", args)
                return

            checker = TestQualityChecker(test_path)
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

        else:
            parser.print_help()

    except Exception as e:
        output_error(f"Error checking quality: {e}", args)


def output_result(result: dict, args) -> None:
    """Output result in requested format."""
    output = json.dumps(
        {
            "success": True,
            "data": result,
        },
        indent=2,
        default=str,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)


def output_error(message: str, args) -> None:
    """Output error in requested format."""
    error_output = json.dumps(
        {
            "success": False,
            "error": message,
        },
        indent=2,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(error_output)
    else:
        print(error_output)


def format_report(results: dict) -> str:
    """Format quality report for human reading."""
    report = f"""
Test Quality Report
==================

Overall Quality Score: {results["quality_score"]}/100
Quality Level: {results["quality_level"].upper()}

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
