"""Test review skill for analyzing test quality and coverage."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from .base import BaseReviewSkill

# Test quality thresholds
MIN_COVERAGE_RATIO = 0.8
ACCEPTABLE_COVERAGE_RATIO = 0.5
MIN_ASSERTION_DENSITY = 0.5
MIN_MUTATION_SCORE = 0.7
MIN_COVERAGE_PERCENT = 80
MIN_MOCK_RATIO = 0.2
MAX_AVG_TEST_DURATION = 2.0
SLOW_TEST_THRESHOLD = 10.0
VERY_SLOW_TEST_THRESHOLD = 5.0
MIN_COMPLEX_ASSERTIONS = 3
MIN_EDGE_CASES = 5
MAX_ANTI_PATTERNS = 5
MAX_UNSAFE_BLOCKS = 20


class TestReviewSkill(BaseReviewSkill):
    """Skill for reviewing test quality, coverage, and patterns."""

    skill_name: ClassVar[str] = "test-review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "javascript",
        "typescript",
        "rust",
    ]

    def analyze_test_coverage(self, context: Any) -> dict[str, Any]:
        """Analyze test coverage metrics and gaps."""
        files = context.get_files()
        source_files = [
            f for f in files if "src/" in str(f) and not str(f).endswith(".test")
        ]
        test_files = [f for f in files if "test" in str(f)]

        # Extract functions from source files
        source_functions = set()
        for source_file in source_files:
            content = context.get_file_content(source_file)
            # Match Python function definitions
            func_matches = re.findall(r"def\s+(\w+)\s*\(", content)
            source_functions.update(func_matches)

        # Extract tested functions from test files
        tested_functions = set()
        for test_file in test_files:
            content = context.get_file_content(test_file)
            # Match import statements and function calls
            for func in source_functions:
                if func in content:
                    tested_functions.add(func)

        # Calculate coverage metrics
        total_functions = len(source_functions)
        tested_count = len(tested_functions)
        uncovered = source_functions - tested_functions

        # Analyze branch coverage by looking for complex functions
        branch_heavy_functions = []
        for source_file in source_files:
            content = context.get_file_content(source_file)
            # Count if statements for branch complexity
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

    def analyze_test_structure(
        self, context: Any, file_path: str = ""
    ) -> dict[str, Any]:
        """Analyze test file structure and organization."""
        content = context.get_file_content(file_path)

        # Check for test class organization
        has_test_classes = bool(re.search(r"class\s+Test\w+", content))

        # Check for setup/teardown methods
        has_setup = bool(re.search(r"def\s+setup_method\s*\(", content))
        has_teardown = bool(re.search(r"def\s+teardown_method\s*\(", content))

        # Check for docstrings
        docstring_count = len(re.findall(r'""".*?"""', content, re.DOTALL))
        test_count = len(re.findall(r"def\s+test_\w+", content))
        documentation_ratio = docstring_count / test_count if test_count > 0 else 0

        # Check for parametrized tests
        has_parametrize = bool(re.search(r"@pytest\.mark\.parametrize", content))

        # Check for proper mocking
        has_mocking = bool(re.search(r"from unittest\.mock import|@patch", content))

        # Check for exception testing
        has_exception_tests = bool(re.search(r"pytest\.raises", content))

        # Calculate structure score
        score = 0.0
        if has_test_classes:
            score += 0.2
        if has_setup:
            score += 0.15
        if has_teardown:
            score += 0.1
        if documentation_ratio > MIN_COVERAGE_RATIO:
            score += 0.2
        if has_parametrize:
            score += 0.15
        if has_mocking:
            score += 0.1
        if has_exception_tests:
            score += 0.1

        organization_issues = []
        if not has_test_classes:
            organization_issues.append("No test class organization found")
        if documentation_ratio < ACCEPTABLE_COVERAGE_RATIO:
            organization_issues.append("Low documentation coverage")

        best_practices = []
        if has_parametrize:
            best_practices.append("Uses parametrized tests")
        if has_mocking:
            best_practices.append("Uses proper mocking")
        if has_exception_tests:
            best_practices.append("Tests exception handling")
        if has_setup:
            best_practices.append("Uses setup methods for fixtures")

        return {
            "structure_score": score,
            "organization_issues": organization_issues,
            "best_practices": best_practices,
            "documentation_quality": documentation_ratio,
        }

    def evaluate_tdd_compliance(self, context: Any) -> dict[str, Any]:
        """Evaluate adherence to TDD principles."""
        history = context.get_git_history()

        # Track test-first pattern
        test_first_count = 0
        code_first_count = 0
        test_created = False

        for _i, entry in enumerate(history):
            is_test_file = "test" in entry["file"]

            if is_test_file and entry["action"] == "created":
                # Check if next entry is source file
                test_first_count += 1
                test_created = True
            elif not is_test_file and entry["action"] == "created":
                if not test_created:
                    code_first_count += 1

        total_patterns = test_first_count + code_first_count
        tdd_score = test_first_count / total_patterns if total_patterns > 0 else 0.0

        # Check for red-green-refactor pattern
        red_green_refactor = self._detect_red_green_refactor(history)

        compliance_issues = []
        if tdd_score < ACCEPTABLE_COVERAGE_RATIO:
            compliance_issues.append("Low test-first adherence")
        if not red_green_refactor:
            compliance_issues.append("Red-green-refactor pattern not detected")

        return {
            "tdd_score": tdd_score,
            "test_first_pattern": test_first_count > code_first_count,
            "red_green_refactor": red_green_refactor,
            "compliance_issues": compliance_issues,
        }

    def _detect_red_green_refactor(self, history: list[dict[str, Any]]) -> bool:
        """Detect red-green-refactor pattern in history."""
        # Look for pattern of test creation -> source modification -> test modification
        for i in range(len(history) - 2):
            if (
                "test" in history[i]["file"]
                and history[i]["action"] == "created"
                and "test" not in history[i + 1]["file"]
                and history[i + 1]["action"] in ["created", "modified"]
            ):
                return True
        return False

    def analyze_bdd_patterns(self, context: Any, file_path: str = "") -> dict[str, Any]:
        """Analyze BDD patterns (Given-When-Then) usage."""
        content = context.get_file_content(file_path)

        # Detect BDD frameworks
        bdd_detected = bool(
            re.search(r"from behave import|import behave|@given|@when|@then", content)
        )

        # Find Given-When-Then patterns
        given_when_then = []

        # Look for behave decorators
        given_matches = re.findall(r"@given\(['\"](.+?)['\"]\)", content)
        when_matches = re.findall(r"@when\(['\"](.+?)['\"]\)", content)
        then_matches = re.findall(r"@then\(['\"](.+?)['\"]\)", content)

        for g, w, t in zip(given_matches, when_matches, then_matches, strict=False):
            given_when_then.append({"given": g, "when": w, "then": t})

        # Look for inline BDD comments
        inline_bdd = re.findall(
            r"#\s*(Given|When|Then):?\s*(.+)", content, re.IGNORECASE
        )
        if inline_bdd:
            given_when_then.append(
                {
                    "type": "inline",
                    "patterns": [f"{kw}: {desc}" for kw, desc in inline_bdd],
                }
            )

        # Look for BDD-style docstrings
        docstring_bdd = re.findall(
            r'""".*?(Given .+?\n.*?When .+?\n.*?Then .+?).*?"""',
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if docstring_bdd:
            given_when_then.append({"type": "docstring", "specs": docstring_bdd})

        # Extract behavior specifications
        behavior_specs = []
        # Find test functions with BDD-style naming or docstrings
        test_funcs = re.findall(
            r"def\s+(test_\w+)\s*\([^)]*\):\s*(?:\"\"\"(.+?)\"\"\")?",
            content,
            re.DOTALL,
        )
        for func_name, docstring in test_funcs:
            if docstring and (
                "given" in docstring.lower() or "when" in docstring.lower()
            ):
                behavior_specs.append(
                    {"function": func_name, "spec": docstring.strip()}
                )

        # Detect Gherkin features
        gherkin_features = bool(re.search(r"Feature:|Scenario:|Background:", content))

        return {
            "bdd_detected": bdd_detected
            or len(given_when_then) > 0
            or gherkin_features,
            "given_when_then": given_when_then,
            "behavior_specifications": behavior_specs,
            "gherkin_features": gherkin_features,
        }

    def identify_test_anti_patterns(
        self, context: Any, file_path: str = ""
    ) -> list[dict[str, Any]]:
        """Identify common test anti-patterns."""
        content = context.get_file_content(file_path)
        anti_patterns = []

        # External dependencies
        if re.search(r"requests\.(get|post|put|delete)", content):
            matches = re.finditer(r"requests\.(get|post|put|delete)", content)
            for match in matches:
                anti_patterns.append(
                    {
                        "type": "external_dependency",
                        "message": "Test depends on external HTTP requests",
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        # Shared state (global variables)
        global_vars = re.findall(r"^(\w+)\s*=\s*.+$", content, re.MULTILINE)
        if global_vars:
            for var in global_vars:
                if var not in ["import", "from", "def", "class"]:
                    anti_patterns.append(
                        {
                            "type": "shared_state",
                            "message": f"Global '{var}' may cause state issues",
                            "variable": var,
                        }
                    )

        # Hardcoded values
        magic_numbers = re.finditer(
            r"assert\s+\w+\s*==\s*(\d+)\s*(?:#.*)?$", content, re.MULTILINE
        )
        for match in magic_numbers:
            if not re.search(r"#.*(?:explain|why)", match.group(0)):
                anti_patterns.append(
                    {
                        "type": "hardcoded_values",
                        "message": "Magic number without explanation",
                        "value": match.group(1),
                    }
                )

        # Slow tests (sleep/delays)
        sleep_calls = re.finditer(r"time\.sleep\((\d+(?:\.\d+)?)\)", content)
        for match in sleep_calls:
            delay = float(match.group(1))
            if delay > 1.0:
                anti_patterns.append(
                    {
                        "type": "slow_test",
                        "message": f"Unnecessary delay of {delay}s found",
                        "duration": delay,
                    }
                )

        # Tests without assertions
        test_funcs = re.finditer(
            r"def\s+(test_\w+)\s*\([^)]*\):(.*?)(?=\ndef|\Z)", content, re.DOTALL
        )
        for match in test_funcs:
            func_name = match.group(1)
            func_body = match.group(2)
            if not re.search(r"\bassert\b|\.assert_", func_body):
                anti_patterns.append(
                    {
                        "type": "no_assertions",
                        "message": f"Test '{func_name}' has no assertions",
                        "function": func_name,
                    }
                )

        # Multiple assertions testing different concerns
        for match in test_funcs:
            func_body = match.group(2)
            assert_count = len(re.findall(r"\bassert\b", func_body))
            if assert_count > MIN_EDGE_CASES:
                anti_patterns.append(
                    {
                        "type": "multiple_concerns",
                        "message": f"Test has {assert_count} assertions - too many",
                        "assertion_count": assert_count,
                    }
                )

        # Bare except clauses
        if re.search(r"except\s*:", content):
            anti_patterns.append(
                {
                    "type": "exception_swallowing",
                    "message": "Bare except clause catches all exceptions",
                }
            )

        return anti_patterns

    def analyze_test_data_management(
        self, context: Any, file_path: str = ""
    ) -> dict[str, Any]:
        """Analyze test data setup and management patterns."""
        content = context.get_file_content(file_path)

        # Analyze fixture quality
        fixture_count = len(re.findall(r"@pytest\.fixture", content))
        fixtures_with_docs = len(
            re.findall(
                r'@pytest\.fixture.*?\n\s*def\s+\w+.*?:\s*"""',
                content,
                re.DOTALL,
            )
        )
        fixtures_with_cleanup = len(
            re.findall(r"yield.*?(?:cleanup|close|teardown)", content, re.DOTALL)
        )

        fixture_quality = {
            "total_fixtures": fixture_count,
            "documented": fixtures_with_docs,
            "with_cleanup": fixtures_with_cleanup,
            "quality_score": (fixtures_with_docs + fixtures_with_cleanup)
            / (fixture_count * 2)
            if fixture_count > 0
            else 0.0,
        }

        # Detect factory usage
        factory_usage = bool(
            re.search(r"Factory\.(create|build|create_batch)", content)
        )

        # Find hardcoded data
        hardcoded_data = []
        # Look for large dict/list literals in test functions
        test_funcs = re.finditer(r"def\s+test_\w+.*?(?=\ndef|\Z)", content, re.DOTALL)
        for match in test_funcs:
            func_body = match.group(0)
            # Find dict literals with multiple keys
            dict_literals = re.finditer(r"\{[^}]{50,}\}", func_body, re.DOTALL)
            for dict_match in dict_literals:
                if dict_match.group(0).count(":") >= MIN_COMPLEX_ASSERTIONS:
                    hardcoded_data.append(
                        {
                            "type": "dict_literal",
                            "size": dict_match.group(0).count(":"),
                        }
                    )

        # Analyze data isolation
        has_database_fixture = bool(
            re.search(r"@pytest\.fixture.*?database", content, re.DOTALL)
        )
        has_cleanup = bool(re.search(r"\bcleanup\b|\bdrop\b|\bdelete\b", content))

        return {
            "fixture_quality": fixture_quality,
            "factory_usage": factory_usage,
            "hardcoded_data": hardcoded_data,
            "data_isolation": {
                "has_database_fixtures": has_database_fixture,
                "has_cleanup": has_cleanup,
            },
        }

    def analyze_mock_usage(self, context: Any, file_path: str = "") -> dict[str, Any]:
        """Analyze mock and stub usage patterns."""
        content = context.get_file_content(file_path)

        # Identify mock patterns
        mock_patterns = []
        if re.search(r"Mock\(\)", content):
            mock_patterns.append("unittest.mock")
        if re.search(r"@patch", content):
            mock_patterns.append("patch_decorator")
        if re.search(r"MagicMock", content):
            mock_patterns.append("magic_mock")

        # Detect over-mocking (too many patches in one test)
        over_mocking = []
        test_funcs = re.finditer(
            r"def\s+(test_\w+)\s*\([^)]*\):(.*?)(?=\ndef|\Z)",
            content,
            re.DOTALL,
        )
        for match in test_funcs:
            func_name = match.group(1)
            func_full = match.group(0)
            # Count patches, including multi-line with statements
            # Handle @patch and "with patch" statements (multi-line ok)
            # Count individual patch calls by looking for patch('...')
            patch_matches = re.findall(r"patch\(['\"][\w.]+['\"]", func_full)
            patch_count = len(patch_matches)
            if patch_count >= MIN_COMPLEX_ASSERTIONS:
                over_mocking.append(
                    {
                        "function": func_name,
                        "patch_count": patch_count,
                    }
                )

        # Analyze verification quality
        mock_verifications = len(
            re.findall(r"\.assert_called|\.assert_not_called", content)
        )
        mock_creation = len(re.findall(r"Mock\(|MagicMock\(|@patch", content))
        verification_ratio = (
            mock_verifications / mock_creation if mock_creation > 0 else 0.0
        )

        # Detect spy usage (patch.object)
        spy_usage = bool(re.search(r"patch\.object", content))

        return {
            "mock_patterns": mock_patterns,
            "over_mocking": over_mocking,
            "verification_quality": {
                "verification_count": mock_verifications,
                "mock_count": mock_creation,
                "ratio": verification_ratio,
            },
            "spy_usage": spy_usage,
        }

    def analyze_test_performance(self, context: Any) -> dict[str, Any]:
        """Analyze test execution performance."""
        perf_data = context.get_test_performance_data()

        # Identify slow tests (>1 second)
        slow_tests = [test for test in perf_data["tests"] if test["duration"] > 1.0]

        # Identify performance bottlenecks
        bottlenecks = []
        for test in slow_tests:
            if test["duration"] > SLOW_TEST_THRESHOLD:
                bottlenecks.append(
                    {
                        "test": test["name"],
                        "duration": test["duration"],
                        "severity": "critical",
                    }
                )
            elif test["duration"] > VERY_SLOW_TEST_THRESHOLD:
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

        # Suggest optimizations
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

        # Analyze parallelization potential
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
        """Analyze integration test coverage."""
        files = context.get_files()

        # Categorize tests
        unit_tests = [
            f
            for f in files
            if "unit" in str(f) or ("test" in str(f) and "integration" not in str(f))
        ]
        integration_tests = [f for f in files if "integration" in str(f)]

        # Analyze integration scenarios
        integration_scenarios = []
        for test_file in integration_tests:
            content = context.get_file_content(test_file)
            # Look for multi-component integration
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

        # Calculate test pyramid balance
        total_tests = len(unit_tests) + len(integration_tests)
        unit_ratio = len(unit_tests) / total_tests if total_tests > 0 else 0.0

        # Identify coverage gaps
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

        # Analyze test result patterns
        flaky_tests = []
        flakiness_patterns = []
        root_causes = []

        for test_data in history:
            test_name = test_data["test"]
            results = test_data["results"]

            # Calculate flakiness score
            pass_count = results.count("pass")
            fail_count = results.count("fail")
            total = len(results)

            # Flaky if it has both passes and failures
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

                # Identify pattern
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

                # Suggest root causes based on test name
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

        # Generate recommendations
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

    def create_test_quality_report(self, analysis: dict[str, Any]) -> str:
        """Create a detailed test quality report."""
        report_lines = [
            "## Test Quality Assessment",
            "",
            f"**Overall Score**: {analysis['overall_score']}/10",
            f"**Test Count**: {analysis['test_count']}",
            "",
            "## Coverage Analysis",
            "",
            f"**Coverage**: {analysis['coverage_percentage']}%",
            f"**Total Tests**: {analysis['test_count']}",
            "",
            "## Test Pyramid",
            "",
            f"- Unit Tests: {analysis['unit_tests']}",
            f"- Integration Tests: {analysis['integration_tests']}",
            f"- End-to-End Tests: {analysis['end_to_end_tests']}",
            "",
            "## Quality Issues",
            "",
            f"- Slow Tests: {analysis['slow_tests']}",
            f"- Flaky Tests: {analysis['flaky_tests']}",
            f"- Anti-patterns: {analysis['anti_patterns']}",
            f"- TDD Compliance: {int(analysis['tdd_compliance'] * 100)}%",
            "",
            "## Recommendations",
            "",
        ]

        # Add findings if present
        if "findings" in analysis:
            for finding in analysis["findings"]:
                report_lines.append(f"- {finding}")

        return "\n".join(report_lines)

    def generate_testing_recommendations(
        self, current_state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate recommendations for improving test quality."""
        recommendations = []

        # Coverage recommendations
        if current_state["coverage"] < MIN_COVERAGE_PERCENT:
            recommendations.append(
                {
                    "category": "coverage",
                    "priority": "high",
                    "action": "Increase test coverage to at least 80%",
                    "benefit": "Reduce bugs and improve code quality",
                    "implementation": "Add tests for uncovered functions/branches",
                }
            )

        # TDD recommendations
        if current_state["tdd_compliance"] < ACCEPTABLE_COVERAGE_RATIO:
            recommendations.append(
                {
                    "category": "tdd",
                    "priority": "medium",
                    "action": "Adopt test-first development practices",
                    "benefit": "Better test coverage and design",
                    "implementation": "Write failing tests before implementation",
                }
            )

        # Integration test recommendations
        if current_state["integration_ratio"] < MIN_MOCK_RATIO:
            recommendations.append(
                {
                    "category": "integration",
                    "priority": "medium",
                    "action": "Add more integration tests",
                    "benefit": "Catch integration issues early",
                    "implementation": "Write tests that verify component interactions",
                }
            )

        # Performance recommendations
        if current_state["avg_test_duration"] > MAX_AVG_TEST_DURATION:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "high",
                    "action": "Optimize slow tests",
                    "benefit": "Faster feedback and CI/CD pipeline",
                    "implementation": "Mock external deps and use in-memory DBs",
                }
            )

        # Flaky test recommendations
        if current_state["flaky_tests"] > 0:
            recommendations.append(
                {
                    "category": "reliability",
                    "priority": "high",
                    "action": f"Fix {current_state['flaky_tests']} flaky tests",
                    "benefit": "Improve CI/CD reliability and developer confidence",
                    "implementation": "Remove non-deterministic behavior and deps",
                }
            )

        # Anti-pattern recommendations
        if current_state["anti_patterns"] > MAX_ANTI_PATTERNS:
            recommendations.append(
                {
                    "category": "quality",
                    "priority": "medium",
                    "action": "Refactor tests to remove anti-patterns",
                    "benefit": "More maintainable and reliable tests",
                    "implementation": "Follow testing best practices and patterns",
                }
            )

        return recommendations
