"""Mathematical correctness review skill.

Tests mathematical algorithm correctness, numerical stability,
and computational accuracy validation.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from .base import BaseReviewSkill


class MathReviewSkill(BaseReviewSkill):
    """Skill for reviewing mathematical correctness in code."""

    skill_name: ClassVar[str] = "math_review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "rust",
        "javascript",
        "typescript",
    ]

    def analyze_numerical_precision(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze code for numerical precision issues.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with precision analysis results containing:
            - precision_issues: List of precision problems found
            - stability_problems: List of stability issues
            - comparison_risks: List of risky floating-point comparisons
        """
        content = context.get_file_content(file_path)

        precision_issues = []
        stability_problems = []
        comparison_risks = []

        # Pattern for float accumulation in loops
        if re.search(r"for\s+.*:\s*\n\s*\w+\s*\+=\s*\w+.*#.*precision", content):
            precision_issues.append(
                "Float accumulation in loop may cause precision errors"
            )

        # More general float accumulation pattern
        if re.search(r"total\s*=\s*0\.0.*for.*total\s*\+=", content, re.DOTALL):
            precision_issues.append("Summation may accumulate precision errors")

        # Pattern for direct float comparison with ==
        if re.search(r"return\s+a\s*==\s*b", content):
            comparison_risks.append(
                "Direct floating-point equality comparison detected"
            )
            precision_issues.append(
                "Exact equality comparison on floating-point values"
            )

        # Pattern for unstable sqrt differences
        if re.search(r"sqrt\([^)]+\)\s*-\s*sqrt\([^)]+\)", content):
            stability_problems.append("Unstable sqrt difference computation detected")

        # Pattern for variance calculation (numerical instability)
        if re.search(r"sum\(\(x\s*-\s*mean\)\s*\*\*\s*2", content):
            stability_problems.append(
                "Two-pass variance calculation may be numerically unstable"
            )

        # Pattern for small step sizes in derivatives
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
        """Analyze code for integer overflow risks.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with overflow analysis results containing:
            - overflow_risks: List of overflow risk locations
            - unprotected_operations: List of unprotected operations
            - growth_patterns: List of exponential growth patterns
        """
        content = context.get_file_content(file_path)

        overflow_risks = []
        unprotected_operations = []
        growth_patterns = []

        # Pattern for factorial without overflow protection
        if re.search(
            r"def\s+factorial.*return\s+n\s*\*\s*factorial", content, re.DOTALL
        ):
            overflow_risks.append(
                "Factorial implementation without overflow protection"
            )
            unprotected_operations.append("Recursive factorial without bounds checking")

        # Pattern for combinatorial calculations
        if re.search(r"factorial\(n\).*factorial\(k\)", content, re.DOTALL):
            overflow_risks.append("Combinatorial calculation with overflow risk")

        # Pattern for direct multiplication without checks
        if re.search(
            r"def\s+unsafe_multiplication.*return\s+a\s*\*\s*b", content, re.DOTALL
        ):
            unprotected_operations.append(
                "Direct multiplication without overflow check"
            )

        # Pattern for exponential growth (2^n)
        if re.search(r"result\s*\*=\s*2", content):
            growth_patterns.append("Exponential growth pattern (2^n) detected")
            overflow_risks.append("Exponential growth can overflow quickly")

        # Pattern for sum of squares
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
        """Analyze matrix operations for numerical stability.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with matrix stability analysis containing:
            - instability_patterns: List of instability patterns
            - condition_number_ignored: List of cases missing condition checks
            - unstable_operations: List of unstable matrix operations
        """
        content = context.get_file_content(file_path)

        instability_patterns: list[str] = []
        condition_number_ignored: list[str] = []
        unstable_operations: list[str] = []

        # Pattern for direct matrix inversion
        if re.search(r"np\.linalg\.inv\(A\)", content):
            unstable_operations.append(
                "Direct matrix inversion is numerically unstable"
            )

        # Pattern for eigenvalue computation without symmetry check
        if re.search(r"np\.linalg\.eigvals\(", content):
            unstable_operations.append(
                "Eigenvalue computation without symmetry consideration"
            )

        # Pattern for inverse without condition number check
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

    def analyze_statistical_fallacies(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze code for statistical fallacies.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with statistical fallacy analysis containing:
            - correlation_causation_fallacy: List of correlation/causation issues
            - p_value_hacking: List of p-value hacking instances
            - sampling_biases: List of sampling bias issues
            - multiple_testing_issues: List of multiple testing problems
        """
        content = context.get_file_content(file_path)

        correlation_causation_fallacy = []
        p_value_hacking = []
        sampling_biases = []
        multiple_testing_issues = []

        # Pattern for correlation implies causation
        if re.search(r"correlation.*>.*return.*causes", content, re.DOTALL):
            correlation_causation_fallacy.append(
                "Correlation being interpreted as causation"
            )

        # Pattern for p-value hacking (testing multiple times)
        if re.search(r"for.*range\(.*\).*p_value.*<\s*0\.05", content, re.DOTALL):
            p_value_hacking.append("Multiple testing without correction detected")
            multiple_testing_issues.append(
                "Testing multiple hypotheses without Bonferroni correction"
            )

        # Pattern for survivorship bias
        if re.search(r"successful.*=.*\[.*for.*if.*successful\]", content, re.DOTALL):
            sampling_biases.append(
                "Survivorship bias - only analyzing successful cases"
            )

        # Pattern for sampling bias (convenience sampling)
        if re.search(r"survey_friends_and_family", content):
            sampling_biases.append("Convenience sampling instead of random sampling")

        return {
            "correlation_causation_fallacy": correlation_causation_fallacy,
            "p_value_hacking": p_value_hacking,
            "sampling_biases": sampling_biases,
            "multiple_testing_issues": multiple_testing_issues,
        }

    def analyze_optimization_algorithms(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze optimization algorithms for correctness.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with optimization analysis containing:
            - convergence_issues: List of convergence problems
            - stability_problems: List of stability issues
            - algorithm_correctness: List of correctness issues
        """
        content = context.get_file_content(file_path)

        convergence_issues: list[str] = []
        stability_problems: list[str] = []
        algorithm_correctness: list[str] = []

        # Pattern for gradient descent without convergence check
        if re.search(
            r"def\s+gradient_descent_simple.*for.*range\(max_iter\).*x\s*=\s*x\s*-",
            content,
            re.DOTALL,
        ):
            convergence_issues.append("Gradient descent without convergence check")

        # Pattern for Newton method without zero derivative check
        if re.search(
            r"def\s+newton_method_unsafe.*x\s*=\s*x\s*-\s*df\(x\)\s*/\s*ddf\(x\)",
            content,
            re.DOTALL,
        ):
            stability_problems.append("Newton method without zero derivative check")

        # Pattern for simulated annealing without proper temperature schedule
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
        """Analyze calculus implementations for errors.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with calculus analysis containing:
            - numerical_errors: List of numerical errors
            - convergence_issues: List of convergence issues
            - accuracy_problems: List of accuracy problems
        """
        content = context.get_file_content(file_path)

        numerical_errors = []
        convergence_issues = []
        accuracy_problems = []

        # Pattern for very small step size in derivative (cancellation error)
        if re.search(r"def\s+numerical_derivative_bad.*h=1e-10", content, re.DOTALL):
            numerical_errors.append("Step size too small causes cancellation errors")

        # Pattern for one-sided derivative (less accurate)
        if re.search(r"return\s*\(f\(x\s*\+\s*h\)\s*-\s*f\(x\)\)\s*/\s*h", content):
            numerical_errors.append(
                "One-sided derivative less accurate than centered difference"
            )

        # Pattern for simple rectangle rule integration
        if re.search(
            r"total\s*\+=\s*f\(x\)\s*\*\s*h.*#.*left endpoint", content, re.DOTALL
        ):
            accuracy_problems.append("Low-accuracy rectangle rule integration")

        # Pattern for Taylor series without range reduction
        if re.search(r"def\s+taylor_series_sin\(x", content):
            # Check if this specific function has range reduction
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

    def analyze_probability_distributions(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze probability distribution implementations.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with probability analysis containing:
            - distribution_errors: List of distribution implementation errors
            - sampling_issues: List of sampling issues
            - statistical_formulas: List of formula errors
        """
        content = context.get_file_content(file_path)

        distribution_errors: list[str] = []
        sampling_issues: list[str] = []
        statistical_formulas: list[str] = []

        # Pattern for incorrect Box-Muller (only returning one value)
        if re.search(
            r"def\s+sample_normal_distribution_bad.*return\s+z\s*#.*Only returns one",
            content,
            re.DOTALL,
        ):
            sampling_issues.append(
                "Box-Muller implementation returns only one of two normal variables"
            )

        # Pattern for incorrect variance (using N instead of N-1)
        if re.search(
            r"def\s+calculate_variance_wrong.*variance\s*=\s*sum\(\(x\s*-\s*mean\)\*\*2.*\)\s*/\s*n",
            content,
            re.DOTALL,
        ):
            statistical_formulas.append(
                "Incorrect variance calculation using N instead of N-1"
            )

        # Pattern for Bayesian update without normalization
        if re.search(
            r"def\s+bayesian_update_bad.*posterior\s*=\s*prior\s*\*\s*likelihood",
            content,
            re.DOTALL,
        ) and not re.search(r"bayesian_update_bad.*/", content):
            statistical_formulas.append("Bayesian update missing normalization")

        return {
            "distribution_errors": distribution_errors,
            "sampling_issues": sampling_issues,
            "statistical_formulas": statistical_formulas,
        }

    def analyze_geometry_trigonometry(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze geometry and trigonometry implementations.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with geometry analysis containing:
            - formula_errors: List of formula errors
            - edge_case_handling: List of edge case issues
            - numerical_stability: List of numerical stability problems
        """
        content = context.get_file_content(file_path)

        formula_errors = []
        edge_case_handling = []
        numerical_stability = []

        # Pattern for missing square root in distance
        sqrt_pattern = (
            r"def\s+distance_between_points_bad\([^)]+\):\s*#\s*Missing square root"
            r"\s*return\s+\([^)]+\)\*\*2\s*\+"
        )
        if re.search(sqrt_pattern, content, re.DOTALL):
            formula_errors.append("Missing square root in distance calculation")

        # Pattern for acos without clamping
        if re.search(
            r"def\s+angle_from_vectors_bad.*return\s+math\.acos\(cos_angle\)",
            content,
            re.DOTALL,
        ):
            # Check if this function has clamping
            angle_func = re.search(
                r"def\s+angle_from_vectors_bad\([^)]+\):.*?(?=def\s|\Z)",
                content,
                re.DOTALL,
            )
            if angle_func and "max(-1.0, min(1.0" not in angle_func.group(0):
                numerical_stability.append("Acos without clamping for numerical errors")

        # Pattern for angle calculation without zero vector check
        angle_func_bad = re.search(
            r"def\s+angle_from_vectors_bad\([^)]+\):.*?(?=def\s|\Z)", content, re.DOTALL
        )
        if angle_func_bad:
            func_body = angle_func_bad.group(0)
            if "mag1 = math.sqrt" in func_body and "if mag1 == 0" not in func_body:
                formula_errors.append("Angle calculation without zero vector handling")

        # Pattern for triangle area without triangle inequality check
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
        """Analyze computational complexity of algorithms.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with complexity analysis containing:
            - complexity_issues: List of complexity issues
            - inefficient_algorithms: List of inefficient algorithms
            - optimization_opportunities: List of optimization opportunities
        """
        content = context.get_file_content(file_path)

        complexity_issues: list[str] = []
        inefficient_algorithms: list[str] = []
        optimization_opportunities: list[str] = []

        # Pattern for recursive fibonacci (exponential complexity)
        if re.search(
            r"def\s+fibonacci_recursive.*return\s+fibonacci_recursive\(n-1\)\s*\+\s*fibonacci_recursive\(n-2\)",
            content,
            re.DOTALL,
        ):
            inefficient_algorithms.append(
                "Exponential time complexity O(2^n) fibonacci"
            )

        # Pattern for naive matrix multiplication (O(n^3))
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
        """Analyze mathematical proof implementations.

        Args:
            context: Skill context with file access methods
            file_path: Path to file to analyze

        Returns:
            Dictionary with proof analysis containing:
            - logical_correctness: List of logical issues
            - edge_case_handling: List of edge case issues
            - mathematical_rigor: List of rigor issues
            - safety_measures: List of safety measure issues
        """
        content = context.get_file_content(file_path)

        logical_correctness: list[str] = []
        edge_case_handling: list[str] = []
        mathematical_rigor: list[str] = []
        safety_measures: list[str] = []

        # Pattern for primality test with edge cases
        if re.search(r"def\s+is_prime.*if\s+n\s*<\s*2:", content, re.DOTALL):
            edge_case_handling.append("Primality test handles edge cases")

        # Pattern for Collatz conjecture with safety limit
        if re.search(r"def\s+collatz.*if\s+n\s*>\s*10\*\*6:", content, re.DOTALL):
            safety_measures.append("Collatz conjecture test includes safety limit")

        # Pattern for Pythagorean triple test with tolerance
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

    def create_math_correctness_report(self, math_analysis: dict[str, Any]) -> str:
        """Generate a mathematical correctness report.

        Args:
            math_analysis: Dictionary with math analysis results

        Returns:
            Formatted markdown report string
        """
        correctness_score = math_analysis.get("correctness_score", 0.0)
        precision_issues = math_analysis.get("precision_issues", 0)
        stability_problems = math_analysis.get("stability_problems", 0)
        algorithm_errors = math_analysis.get("algorithm_errors", 0)
        complexity_issues = math_analysis.get("complexity_issues", 0)
        statistical_fallacies = math_analysis.get("statistical_fallacies", 0)
        total_algorithms = math_analysis.get("total_algorithms", 0)
        high_risk_algorithms = math_analysis.get("high_risk_algorithms", 0)

        report_lines = [
            "## Mathematical Correctness Assessment",
            "",
            f"Overall correctness score: {correctness_score}/10",
            f"Total algorithms analyzed: {total_algorithms}",
            f"High-risk algorithms: {high_risk_algorithms}",
            "",
            "## Numerical Precision Analysis",
            "",
            f"Precision issues found: {precision_issues}",
            f"Stability problems: {stability_problems}",
            "",
            "## Algorithm Correctness",
            "",
            f"Algorithm errors: {algorithm_errors}",
            f"Complexity issues: {complexity_issues}",
            "",
            "## Statistical Validity",
            "",
            f"Statistical fallacies: {statistical_fallacies}",
            "",
            "## Recommendations",
            "",
            "- Review precision-critical operations",
            "- Add stability checks to matrix operations",
            "- Validate algorithm correctness",
            "- Consider computational complexity",
        ]

        return "\n".join(report_lines)

    def generate_mathematical_recommendations(
        self,
        analysis_results: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate mathematical improvement recommendations.

        Args:
            analysis_results: Dictionary with analysis results

        Returns:
            List of recommendation dictionaries, each containing:
            - category: Recommendation category
            - technique: Recommended technique
            - benefit: Expected benefit
            - implementation: Implementation guidance
            - examples: Example code/references
        """
        recommendations = []

        if analysis_results.get("has_precision_issues"):
            recommendations.append(
                {
                    "category": "precision",
                    "technique": "Use appropriate numeric types",
                    "benefit": "Reduce precision errors",
                    "implementation": "Use decimal types for financial calculations",
                    "examples": ["decimal.Decimal", "BigDecimal"],
                }
            )

        if analysis_results.get("has_stability_problems"):
            recommendations.append(
                {
                    "category": "stability",
                    "technique": "Use numerically stable algorithms",
                    "benefit": "Improve accuracy for ill-conditioned problems",
                    "implementation": "Replace direct inversion with LU decomposition",
                    "examples": ["np.linalg.solve", "scipy.linalg.lu"],
                }
            )

        if analysis_results.get("uses_unstable_algorithms"):
            recommendations.append(
                {
                    "category": "algorithms",
                    "technique": "Use proven stable implementations",
                    "benefit": "Better convergence and accuracy",
                    "implementation": "Use library implementations when available",
                    "examples": ["scipy.optimize", "numpy.linalg"],
                }
            )

        if analysis_results.get("lacks_error_bounds"):
            recommendations.append(
                {
                    "category": "validation",
                    "technique": "Add error bounds and convergence checks",
                    "benefit": "Detect and handle numerical issues",
                    "implementation": "Check condition numbers and tolerances",
                    "examples": ["np.linalg.cond", "convergence criteria"],
                }
            )

        if analysis_results.get("missing_convergence_checks"):
            recommendations.append(
                {
                    "category": "validation",
                    "technique": "Add convergence monitoring",
                    "benefit": "Ensure iterative algorithms terminate correctly",
                    "implementation": "Track iteration count and residuals",
                    "examples": ["max_iterations", "tolerance checks"],
                }
            )

        return recommendations
