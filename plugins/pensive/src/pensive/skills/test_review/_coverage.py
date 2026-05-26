"""Coverage mixin: test coverage, performance, integration, and flakiness."""

from __future__ import annotations

import re
from typing import Any

from ._constants import (
    MIN_MUTATION_SCORE,
    SLOW_TEST_THRESHOLD,
    VERY_SLOW_TEST_THRESHOLD,
)


class CoverageMixin:
    """Analyze test coverage, performance, integration scenarios, and flakiness."""

    def analyze_test_coverage(self, context: Any) -> dict[str, Any]:
        """Analyze test coverage metrics and gaps."""
        files = context.get_files()
        source_files = [
            f for f in files if "src/" in str(f) and not str(f).endswith(".test")
        ]
        test_files = [f for f in files if "test" in str(f)]

        source_functions: set[str] = set()
        for source_file in source_files:
            content = context.get_file_content(source_file)
            func_matches = re.findall(r"def\s+(\w+)\s*\(", content)
            source_functions.update(func_matches)

        tested_functions: set[str] = set()
        for test_file in test_files:
            content = context.get_file_content(test_file)
            for func in source_functions:
                if func in content:
                    tested_functions.add(func)

        total_functions = len(source_functions)
        tested_count = len(tested_functions)
        uncovered = source_functions - tested_functions

        branch_heavy_functions = []
        for source_file in source_files:
            content = context.get_file_content(source_file)
            if_count = len(re.findall(r"\bif\s+", content))
            branch_heavy_functions.append({"file": source_file, "branches": if_count})

        coverage_percentage = (
            (tested_count / total_functions * 100) if total_functions > 0 else 0
        )

        return {
            "overall_coverage": coverage_percentage,
            "file_coverage": {
                source_file: {
                    "covered": bool(
                        any(f in str(source_file) for f in tested_functions)
                    )
                }
                for source_file in source_files
            },
            "uncovered_functions": list(uncovered),
            "branch_coverage": {
                "total_branches": sum(f["branches"] for f in branch_heavy_functions),
                "complex_functions": branch_heavy_functions,
            },
        }

    def analyze_test_performance(self, context: Any) -> dict[str, Any]:
        """Analyze test execution performance."""
        perf_data = context.get_test_performance_data()

        slow_tests = [test for test in perf_data["tests"] if test["duration"] > 1.0]

        bottlenecks = []
        for test in slow_tests:
            if test["duration"] > VERY_SLOW_TEST_THRESHOLD:
                bottlenecks.append(
                    {
                        "test": test["name"],
                        "duration": test["duration"],
                        "severity": "critical",
                    }
                )
            elif test["duration"] > SLOW_TEST_THRESHOLD:
                bottlenecks.append(
                    {
                        "test": test["name"],
                        "duration": test["duration"],
                        "severity": "high",
                    }
                )
            else:
                bottlenecks.append(
                    {
                        "test": test["name"],
                        "duration": test["duration"],
                        "severity": "medium",
                    }
                )

        optimizations = []
        for test in slow_tests:
            if "database" in test["name"].lower():
                optimizations.append(
                    {
                        "test": test["name"],
                        "suggestion": "Use in-memory database or mock database calls",
                    }
                )
            elif "api" in test["name"].lower():
                optimizations.append(
                    {
                        "test": test["name"],
                        "suggestion": "Mock external API calls",
                    }
                )
            elif "file" in test["name"].lower():
                optimizations.append(
                    {
                        "test": test["name"],
                        "suggestion": "Use in-memory file system or mock I/O",
                    }
                )

        parallelizable = perf_data.get("parallelizable", [])
        non_parallel = [
            t["name"] for t in perf_data["tests"] if t["name"] not in parallelizable
        ]

        return {
            "slow_tests": slow_tests,
            "performance_bottlenecks": bottlenecks,
            "optimization_opportunities": optimizations,
            "parallelization_potential": {
                "parallelizable": parallelizable,
                "non_parallelizable": non_parallel,
                "parallel_ratio": len(parallelizable) / len(perf_data["tests"])
                if perf_data["tests"]
                else 0.0,
            },
        }

    def analyze_integration_test_coverage(
        self, context: Any, _file_path: str = ""
    ) -> dict[str, Any]:
        """Categorize tests under ``context`` and score multi-component coverage."""
        files = context.get_files()

        unit_tests = [
            f
            for f in files
            if "unit" in str(f) or ("test" in str(f) and "integration" not in str(f))
        ]
        integration_tests = [f for f in files if "integration" in str(f)]

        integration_scenarios = []
        for test_file in integration_tests:
            content = context.get_file_content(test_file)
            if re.search(
                r"Service.*database|database.*Service", content, re.IGNORECASE
            ):
                integration_scenarios.append(
                    {
                        "file": test_file,
                        "type": "database_integration",
                    }
                )
            if re.search(r"client|TestClient|app", content):
                integration_scenarios.append(
                    {
                        "file": test_file,
                        "type": "api_integration",
                    }
                )

        total_tests = len(unit_tests) + len(integration_tests)
        unit_ratio = len(unit_tests) / total_tests if total_tests > 0 else 0.0

        coverage_gaps = []
        if unit_ratio < MIN_MUTATION_SCORE:
            coverage_gaps.append("Insufficient unit test coverage (should be ~70%)")
        if len(integration_tests) == 0:
            coverage_gaps.append("No integration tests found")
        if len(integration_tests) > len(unit_tests):
            coverage_gaps.append(
                "Integration tests outnumber unit tests (inverted pyramid)"
            )

        return {
            "unit_test_ratio": unit_ratio,
            "integration_scenarios": integration_scenarios,
            "coverage_gaps": coverage_gaps,
            "test_pyramid_balance": {
                "unit_tests": len(unit_tests),
                "integration_tests": len(integration_tests),
                "ratio": f"{int(unit_ratio * 100)}:{int((1 - unit_ratio) * 100)}",
            },
        }

    def detect_test_flakiness(self, context: Any) -> dict[str, Any]:
        """Detect potentially flaky tests."""
        history = context.get_test_history()

        flaky_tests = []
        flakiness_patterns = []
        root_causes = []

        for test_data in history:
            test_name = test_data["test"]
            results = test_data["results"]

            pass_count = results.count("pass")
            fail_count = results.count("fail")
            total = len(results)

            if pass_count > 0 and fail_count > 0:
                flakiness_score = min(pass_count, fail_count) / total
                flaky_tests.append(
                    {
                        "test": test_name,
                        "pass_rate": pass_count / total,
                        "flakiness_score": flakiness_score,
                        "results": results,
                    }
                )

                if results == ["pass", "fail"] * (total // 2):
                    flakiness_patterns.append(
                        {
                            "test": test_name,
                            "pattern": "alternating",
                        }
                    )
                elif results[0] != results[-1]:
                    flakiness_patterns.append(
                        {
                            "test": test_name,
                            "pattern": "intermittent",
                        }
                    )

                if "random" in test_name.lower():
                    root_causes.append(
                        {
                            "test": test_name,
                            "cause": "Non-deterministic data (random values)",
                        }
                    )
                elif "time" in test_name.lower():
                    root_causes.append(
                        {
                            "test": test_name,
                            "cause": "Time-dependent behavior",
                        }
                    )
                elif "concurrent" in test_name.lower() or "thread" in test_name.lower():
                    root_causes.append(
                        {
                            "test": test_name,
                            "cause": "Race conditions or concurrency issues",
                        }
                    )
                elif (
                    "external" in test_name.lower() or "dependency" in test_name.lower()
                ):
                    root_causes.append(
                        {
                            "test": test_name,
                            "cause": "External dependency instability",
                        }
                    )

        recommendations = []
        if flaky_tests:
            recommendations.append("Fix flaky tests to improve CI/CD reliability")
            recommendations.append("Use fixed seeds for random data in tests")
            recommendations.append("Mock time-dependent operations")
            recommendations.append(
                "Add retries or stabilization for external dependencies"
            )

        return {
            "flaky_tests": flaky_tests,
            "flakiness_patterns": flakiness_patterns,
            "root_causes": root_causes,
            "recommendations": recommendations,
        }
