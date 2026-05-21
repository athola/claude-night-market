"""Numerical analysis mixin: precision, overflow, and matrix stability."""

from __future__ import annotations

import re
from typing import Any


class NumericalMixin:
    """Analyzes numerical precision, integer overflow, and matrix stability."""

    def analyze_numerical_precision(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        precision_issues = []
        stability_problems = []
        comparison_risks = []

        if re.search(r"for\s+.*:\s*\n\s*\w+\s*\+=\s*\w+.*#.*precision", content):
            precision_issues.append(
                "Float accumulation in loop may cause precision errors"
            )

        if re.search(r"total\s*=\s*0\.0.*for.*total\s*\+=", content, re.DOTALL):
            precision_issues.append("Summation may accumulate precision errors")

        if re.search(r"return\s+a\s*==\s*b", content):
            comparison_risks.append(
                "Direct floating-point equality comparison detected"
            )
            precision_issues.append(
                "Exact equality comparison on floating-point values"
            )

        if re.search(r"sqrt\([^)]+\)\s*-\s*sqrt\([^)]+\)", content):
            stability_problems.append("Unstable sqrt difference computation detected")

        if re.search(r"sum\(\(x\s*-\s*mean\)\s*\*\*\s*2", content):
            stability_problems.append(
                "Two-pass variance calculation may be numerically unstable"
            )

        if re.search(r"h\s*=\s*1e-10", content):
            precision_issues.append(
                "Very small step size may cause cancellation errors"
            )

        return {
            "precision_issues": precision_issues,
            "stability_problems": stability_problems,
            "comparison_risks": comparison_risks,
        }

    def analyze_integer_overflow(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        overflow_risks = []
        unprotected_operations = []
        growth_patterns = []

        if re.search(
            r"def\s+factorial.*return\s+n\s*\*\s*factorial", content, re.DOTALL
        ):
            overflow_risks.append(
                "Factorial implementation without overflow protection"
            )
            unprotected_operations.append("Recursive factorial without bounds checking")

        if re.search(r"factorial\(n\).*factorial\(k\)", content, re.DOTALL):
            overflow_risks.append("Combinatorial calculation with overflow risk")

        if re.search(
            r"def\s+unsafe_multiplication.*return\s+a\s*\*\s*b", content, re.DOTALL
        ):
            unprotected_operations.append(
                "Direct multiplication without overflow check"
            )

        if re.search(r"result\s*\*=\s*2", content):
            growth_patterns.append("Exponential growth pattern (2^n) detected")
            overflow_risks.append("Exponential growth can overflow quickly")

        if re.search(r"total\s*\+=\s*i\s*\*\s*i", content):
            overflow_risks.append("Sum of squares may overflow for large inputs")

        return {
            "overflow_risks": overflow_risks,
            "unprotected_operations": unprotected_operations,
            "growth_patterns": growth_patterns,
        }

    def analyze_matrix_stability(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        instability_patterns: list[str] = []
        condition_number_ignored: list[str] = []
        unstable_operations: list[str] = []

        if re.search(r"np\.linalg\.inv\(A\)", content):
            unstable_operations.append(
                "Direct matrix inversion is numerically unstable"
            )

        if re.search(r"np\.linalg\.eigvals\(", content):
            unstable_operations.append(
                "Eigenvalue computation without symmetry consideration"
            )

        if re.search(
            r"def\s+\w*inverse.*np\.linalg\.inv.*return", content, re.DOTALL
        ) and not re.search(r"np\.linalg\.cond", content):
            condition_number_ignored.append(
                "Matrix inversion without condition number check"
            )

        return {
            "instability_patterns": instability_patterns,
            "condition_number_ignored": condition_number_ignored,
            "unstable_operations": unstable_operations,
        }
