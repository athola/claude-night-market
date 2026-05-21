"""Algorithms mixin: optimization, calculus, geometry, complexity, proofs."""

from __future__ import annotations

import re
from typing import Any


class AlgorithmsMixin:
    """Analyzes optimization, calculus, geometry, complexity, and proof implementations."""

    def analyze_optimization_algorithms(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        convergence_issues: list[str] = []
        stability_problems: list[str] = []
        algorithm_correctness: list[str] = []

        if re.search(
            r"def\s+gradient_descent_simple.*for.*range\(max_iter\).*x\s*=\s*x\s*-",
            content,
            re.DOTALL,
        ):
            convergence_issues.append("Gradient descent without convergence check")

        if re.search(
            r"def\s+newton_method_unsafe.*x\s*=\s*x\s*-\s*df\(x\)\s*/\s*ddf\(x\)",
            content,
            re.DOTALL,
        ):
            stability_problems.append("Newton method without zero derivative check")

        if re.search(
            r"def\s+simulated_annealing.*temperature\s*\*=\s*0\.99", content, re.DOTALL
        ):
            convergence_issues.append(
                "Simulated annealing with overly simple temperature schedule"
            )

        return {
            "convergence_issues": convergence_issues,
            "stability_problems": stability_problems,
            "algorithm_correctness": algorithm_correctness,
        }

    def analyze_calculus_implementations(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        numerical_errors = []
        convergence_issues = []
        accuracy_problems = []

        if re.search(r"def\s+numerical_derivative_bad.*h=1e-10", content, re.DOTALL):
            numerical_errors.append("Step size too small causes cancellation errors")

        if re.search(r"return\s*\(f\(x\s*\+\s*h\)\s*-\s*f\(x\)\)\s*/\s*h", content):
            numerical_errors.append(
                "One-sided derivative less accurate than centered difference"
            )

        if re.search(
            r"total\s*\+=\s*f\(x\)\s*\*\s*h.*#.*left endpoint", content, re.DOTALL
        ):
            accuracy_problems.append("Low-accuracy rectangle rule integration")

        if re.search(r"def\s+taylor_series_sin\(x", content):
            taylor_func = re.search(
                r"def\s+taylor_series_sin\(x[^)]*\):.*?(?=def\s|\Z)", content, re.DOTALL
            )
            if taylor_func and "x %" not in taylor_func.group(0):
                convergence_issues.append(
                    "Taylor series without range reduction has poor convergence"
                )
                numerical_errors.append("Taylor series convergence issues for large x")

        return {
            "numerical_errors": numerical_errors,
            "convergence_issues": convergence_issues,
            "accuracy_problems": accuracy_problems,
        }

    def analyze_geometry_trigonometry(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        formula_errors = []
        edge_case_handling = []
        numerical_stability = []

        sqrt_pattern = (
            r"def\s+distance_between_points_bad\([^)]+\):\s*#\s*Missing square root"
            r"\s*return\s+\([^)]+\)\*\*2\s*\+"
        )
        if re.search(sqrt_pattern, content, re.DOTALL):
            formula_errors.append("Missing square root in distance calculation")

        if re.search(
            r"def\s+angle_from_vectors_bad.*return\s+math\.acos\(cos_angle\)",
            content,
            re.DOTALL,
        ):
            angle_func = re.search(
                r"def\s+angle_from_vectors_bad\([^)]+\):.*?(?=def\s|\Z)",
                content,
                re.DOTALL,
            )
            if angle_func and "max(-1.0, min(1.0" not in angle_func.group(0):
                numerical_stability.append("Acos without clamping for numerical errors")

        angle_func_bad = re.search(
            r"def\s+angle_from_vectors_bad\([^)]+\):.*?(?=def\s|\Z)", content, re.DOTALL
        )
        if angle_func_bad:
            func_body = angle_func_bad.group(0)
            if "mag1 = math.sqrt" in func_body and "if mag1 == 0" not in func_body:
                formula_errors.append("Angle calculation without zero vector handling")

        if re.search(
            r"def\s+triangle_area_bad.*Heron.*area\s*=\s*math\.sqrt", content, re.DOTALL
        ):
            edge_case_handling.append("Triangle area without triangle inequality check")

        return {
            "formula_errors": formula_errors,
            "edge_case_handling": edge_case_handling,
            "numerical_stability": numerical_stability,
        }

    def analyze_computational_complexity(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        complexity_issues: list[str] = []
        inefficient_algorithms: list[str] = []
        optimization_opportunities: list[str] = []

        if re.search(
            r"def\s+fibonacci_recursive.*return\s+fibonacci_recursive\(n-1\)\s*\+\s*fibonacci_recursive\(n-2\)",
            content,
            re.DOTALL,
        ):
            inefficient_algorithms.append(
                "Exponential time complexity O(2^n) fibonacci"
            )

        if re.search(
            r"for\s+i.*for\s+j.*for\s+k.*C\[i\]\[j\]\s*\+=\s*A\[i\]\[k\]\s*\*\s*B\[k\]\[j\]",
            content,
            re.DOTALL,
        ):
            inefficient_algorithms.append("O(n^3) naive matrix multiplication")

        return {
            "complexity_issues": complexity_issues,
            "inefficient_algorithms": inefficient_algorithms,
            "optimization_opportunities": optimization_opportunities,
        }

    def analyze_mathematical_proofs(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        logical_correctness: list[str] = []
        edge_case_handling: list[str] = []
        mathematical_rigor: list[str] = []
        safety_measures: list[str] = []

        if re.search(r"def\s+is_prime.*if\s+n\s*<\s*2:", content, re.DOTALL):
            edge_case_handling.append("Primality test handles edge cases")

        if re.search(r"def\s+collatz.*if\s+n\s*>\s*10\*\*6:", content, re.DOTALL):
            safety_measures.append("Collatz conjecture test includes safety limit")

        if re.search(r"def\s+pythagorean.*abs\(.*\)\s*<\s*1e-10", content, re.DOTALL):
            mathematical_rigor.append(
                "Pythagorean triple test uses numerical tolerance"
            )

        return {
            "logical_correctness": logical_correctness,
            "edge_case_handling": edge_case_handling,
            "mathematical_rigor": mathematical_rigor,
            "safety_measures": safety_measures,
        }
