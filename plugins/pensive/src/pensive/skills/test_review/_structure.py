"""Structure mixin: test organization, TDD compliance, BDD patterns."""

from __future__ import annotations

import re
from typing import Any

from ._constants import ACCEPTABLE_COVERAGE_RATIO, MIN_COVERAGE_RATIO


class StructureMixin:
    """Analyze test structure, TDD adherence, and BDD pattern usage."""

    def analyze_test_structure(
        self, context: Any, file_path: str = ""
    ) -> dict[str, Any]:
        """Analyze test file structure and organization."""
        content = context.get_file_content(file_path)

        has_test_classes = bool(re.search(r"class\s+Test\w+", content))
        has_setup = bool(re.search(r"def\s+setup_method\s*\(", content))
        has_teardown = bool(re.search(r"def\s+teardown_method\s*\(", content))

        docstring_count = len(re.findall(r'""".*?"""', content, re.DOTALL))
        test_count = len(re.findall(r"def\s+test_\w+", content))
        documentation_ratio = docstring_count / test_count if test_count > 0 else 0

        has_parametrize = bool(re.search(r"@pytest\.mark\.parametrize", content))
        has_mocking = bool(re.search(r"from unittest\.mock import|@patch", content))
        has_exception_tests = bool(re.search(r"pytest\.raises", content))

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

        test_first_count = 0
        code_first_count = 0
        test_created = False

        for entry in history:
            is_test_file = "test" in entry["file"]

            if is_test_file and entry["action"] == "created":
                test_first_count += 1
                test_created = True
            elif not is_test_file and entry["action"] == "created":
                if not test_created:
                    code_first_count += 1

        total_patterns = test_first_count + code_first_count
        tdd_score = test_first_count / total_patterns if total_patterns > 0 else 0.0

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

        bdd_detected = bool(
            re.search(r"from behave import|import behave|@given|@when|@then", content)
        )

        given_when_then = []

        given_matches = re.findall(r"@given\(['\"](.+?)['\"]\)", content)
        when_matches = re.findall(r"@when\(['\"](.+?)['\"]\)", content)
        then_matches = re.findall(r"@then\(['\"](.+?)['\"]\)", content)

        for g, w, t in zip(given_matches, when_matches, then_matches):
            given_when_then.append({"given": g, "when": w, "then": t})

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

        docstring_bdd = re.findall(
            r'""".*?(Given .+?\n.*?When .+?\n.*?Then .+?).*?"""',
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if docstring_bdd:
            given_when_then.append({"type": "docstring", "specs": docstring_bdd})

        behavior_specs = []
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

        gherkin_features = bool(re.search(r"Feature:|Scenario:|Background:", content))

        return {
            "bdd_detected": bdd_detected
            or len(given_when_then) > 0
            or gherkin_features,
            "given_when_then": given_when_then,
            "behavior_specifications": behavior_specs,
            "gherkin_features": gherkin_features,
        }
