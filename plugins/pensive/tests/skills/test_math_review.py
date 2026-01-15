"""Unit tests for the math review skill.

Tests mathematical algorithm correctness, numerical stability,
and computational accuracy validation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import the skill we're testing
from pensive.skills.math_review import MathReviewSkill


class TestMathReviewSkill:
    """Test suite for MathReviewSkill business logic."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = MathReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_numerical_precision_issues(self, mock_skill_context) -> None:
        """Given floating-point ops, skill flags precision issues."""
        # Arrange
        precision_issues_code = """
        import math

        def problematic_summation(numbers):
            total = 0.0
            for num in numbers:
                total += num  # Can accumulate precision errors
            return total

        def dangerous_comparison(a, b):
            return a == b  # Exact floating-point comparison is dangerous

        def sqrt_instability(x):
            # Unstable for very small or very large x
            return math.sqrt(x + 1) - math.sqrt(x)

        def unstable_variance_calculation(data):
            # Numerically unstable variance formula
            n = len(data)
            mean = sum(data) / n
            variance = sum((x - mean) ** 2 for x in data) / n
            return variance

        # Better alternative
        def stable_variance_calculation(data):
            # Welford's algorithm for numerical stability
            n = 0
            mean = 0.0
            M2 = 0.0
            for x in data:
                n += 1
                delta = x - mean
                mean += delta / n
                delta2 = x - mean
                M2 += delta * delta2
            return M2 / n if n > 0 else 0.0
        """

        mock_skill_context.get_file_content.return_value = precision_issues_code

        # Act
        precision_analysis = self.skill.analyze_numerical_precision(
            mock_skill_context,
            "math_utils.py",
        )

        # Assert
        assert "precision_issues" in precision_analysis
        assert "stability_problems" in precision_analysis
        assert "comparison_risks" in precision_analysis
        assert len(precision_analysis["precision_issues"]) >= 3

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_integer_overflow_risks(self, mock_skill_context) -> None:
        """Given integer operations, when skill analyzes, then flags overflow risks."""
        # Arrange
        overflow_code = """
        def factorial(n):
            # No overflow protection
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        def combinatorial_calculation(n, k):
            # Overflow risk in intermediate calculations
            numerator = factorial(n)
            denominator = factorial(k) * factorial(n - k)
            return numerator // denominator

        def unsafe_multiplication(a, b):
            # Direct multiplication without overflow check
            return a * b

        def safe_multiplication(a, b):
            # With overflow protection
            if a > 2**63 // b:
                raise OverflowError("Multiplication would overflow")
            return a * b

        def exponential_growth(n):
            # Can overflow quickly
            result = 1
            for i in range(n):
                result *= 2  # 2^n grows very fast
            return result

        def sum_of_squares(n):
            # Potential overflow for large n
            total = 0
            for i in range(n):
                total += i * i
            return total
        """

        mock_skill_context.get_file_content.return_value = overflow_code

        # Act
        overflow_analysis = self.skill.analyze_integer_overflow(
            mock_skill_context,
            "combinatorics.py",
        )

        # Assert
        assert "overflow_risks" in overflow_analysis
        assert "unprotected_operations" in overflow_analysis
        assert "growth_patterns" in overflow_analysis
        assert len(overflow_analysis["overflow_risks"]) >= 4

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_matrix_operation_stability(self, mock_skill_context) -> None:
        """Given matrix ops, skill assesses numerical stability."""
        # Arrange
        matrix_code = """
        import numpy as np

        def solve_linear_system(A, b):
            # Direct matrix inversion is numerically unstable
            A_inv = np.linalg.inv(A)
            return A_inv @ b

        def stable_solve(A, b):
            # Use LU decomposition instead
            return np.linalg.solve(A, b)

        def compute_eigenvalues(matrix):
            # Can be unstable for non-symmetric matrices
            return np.linalg.eigvals(matrix)

        def stable_eigen_decomposition(matrix):
            # Better approach for symmetric matrices
            if np.allclose(matrix, matrix.T):
                return np.linalg.eigh(matrix)  # For symmetric matrices
            else:
                return np.linalg.eig(matrix)

        def compute_condition_number(matrix):
            # High condition number indicates ill-conditioning
            return np.linalg.cond(matrix)

        def problematic_inverse(matrix):
            # No check for singular or near-singular matrices
            return np.linalg.inv(matrix)

        def safe_inverse(matrix):
            # Check condition number first
            if np.linalg.cond(matrix) > 1e12:
                raise ValueError("Matrix is ill-conditioned")
            return np.linalg.inv(matrix)
        """

        mock_skill_context.get_file_content.return_value = matrix_code

        # Act
        matrix_analysis = self.skill.analyze_matrix_stability(
            mock_skill_context,
            "linear_algebra.py",
        )

        # Assert
        assert "instability_patterns" in matrix_analysis
        assert "condition_number_ignored" in matrix_analysis
        assert "unstable_operations" in matrix_analysis
        assert len(matrix_analysis["unstable_operations"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_statistical_fallacies(self, mock_skill_context) -> None:
        """Given statistical code, skill flags fallacies."""
        # Arrange
        statistical_code = """
        import numpy as np
        from scipy import stats

        def flawed_correlation(x, y):
            # Correlation doesn't imply causation
            correlation = np.corrcoef(x, y)[0, 1]
            if correlation > 0.8:
                return "x causes y"
            return "no causal relationship"

        def p_value_hacking(data):
            # Multiple testing without correction
            p_values = []
            for i in range(100):  # Testing many hypotheses
                _, p_value = stats.ttest_1samp(data[:i+1], 0)
                p_values.append(p_value)
                if p_value < 0.05:
                    return f"Significant result after {i+1} samples!"
            return "No significant result found"

        def survivorship_bias(data):
            # Only analyzing successful cases
            successful_companies = [company for company in data if company.successful]
            avg_return = np.mean([company.returns for company in successful_companies])
            return f"Average return: {avg_return:.2f}%"  # Biased upward

        def sampling_bias():
            # Convenience sample instead of random sample
            survey_data = survey_friends_and_family()  # Not representative
            avg_age = np.mean([person.age for person in survey_data])
            return f"Average population age: {avg_age}"

        def proper_statistical_analysis(data, alpha=0.05):
            # Multiple testing correction
            p_values = [stats.ttest_1samp(sample, 0)[1] for sample in data]
            # Bonferroni correction
            corrected_alpha = alpha / len(p_values)
            significant = [p for p in p_values if p < corrected_alpha]
            return len(significant)
        """

        mock_skill_context.get_file_content.return_value = statistical_code

        # Act
        statistical_analysis = self.skill.analyze_statistical_fallacies(
            mock_skill_context,
            "statistics.py",
        )

        # Assert
        assert "correlation_causation_fallacy" in statistical_analysis
        assert "p_value_hacking" in statistical_analysis
        assert "sampling_biases" in statistical_analysis
        assert "multiple_testing_issues" in statistical_analysis
        assert len(statistical_analysis["sampling_biases"]) >= 2

    @pytest.mark.unit
    def test_analyzes_optimization_algorithm_correctness(
        self, mock_skill_context
    ) -> None:
        """Given optimization algorithms, skill checks convergence and correctness."""
        # Arrange
        optimization_code = """
        import numpy as np

        def gradient_descent_simple(f, df, x0, learning_rate=0.01, max_iter=1000):
            x = x0
            for i in range(max_iter):
                gradient = df(x)
                x = x - learning_rate * gradient
                # No convergence check
            return x

        def gradient_descent_proper(
            f, df, x0, learning_rate=0.01, max_iter=1000, tol=1e-6
        ):
            x = x0
            for i in range(max_iter):
                gradient = df(x)
                x_new = x - learning_rate * gradient

                # Check for convergence
                if np.linalg.norm(x_new - x) < tol:
                    print(f"Converged after {i+1} iterations")
                    break

                x = x_new
            return x

        def newton_method_unsafe(f, df, ddf, x0, max_iter=100):
            x = x0
            for i in range(max_iter):
                # No check for zero second derivative
                x = x - df(x) / ddf(x)
            return x

        def newton_method_safe(f, df, ddf, x0, max_iter=100):
            x = x0
            for i in range(max_iter):
                second_deriv = ddf(x)
                if abs(second_deriv) < 1e-10:
                    # Use gradient descent step if second derivative is too small
                    x = x - 0.01 * df(x)
                else:
                    x = x - df(x) / second_deriv
            return x

        def simulated_annealing():
            # Missing temperature schedule
            temperature = 1.0
            while temperature > 0:
                # Optimization step
                temperature *= 0.99  # Should be more sophisticated
            return best_solution
        """

        mock_skill_context.get_file_content.return_value = optimization_code

        # Act
        optimization_analysis = self.skill.analyze_optimization_algorithms(
            mock_skill_context,
            "optimization.py",
        )

        # Assert
        assert "convergence_issues" in optimization_analysis
        assert "stability_problems" in optimization_analysis
        assert "algorithm_correctness" in optimization_analysis
        assert len(optimization_analysis["convergence_issues"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_calculus_implementation_errors(self, mock_skill_context) -> None:
        """Given calculus code, skill flags mathematical errors."""
        # Arrange
        calculus_code = """
        import numpy as np

        def numerical_derivative_bad(f, x, h=1e-10):
            # Problematic: too small step size causes cancellation errors
            return (f(x + h) - f(x)) / h

        def numerical_derivative_good(f, x, h=1e-5):
            # Better: centered difference with appropriate step size
            return (f(x + h) - f(x - h)) / (2 * h)

        def numerical_integration_bad(f, a, b, n=1000):
            # Simple rectangle rule, low accuracy
            h = (b - a) / n
            total = 0.0
            for i in range(n):
                x = a + i * h
                total += f(x) * h  # Always using left endpoint
            return total

        def numerical_integration_good(f, a, b, n=1000):
            # Simpson's rule for better accuracy
            if n % 2 == 1:
                n += 1  # Simpson's rule requires even number of intervals
            h = (b - a) / n
            total = f(a) + f(b)
            for i in range(1, n):
                x = a + i * h
                coeff = 4 if i % 2 == 1 else 2
                total += coeff * f(x)
            return total * h / 3

        def taylor_series_sin(x, n_terms=5):
            # Taylor series for sin(x) - has convergence issues for large x
            result = 0.0
            for n in range(n_terms):
                result += ((-1)**n / math.factorial(2*n + 1)) * x**(2*n + 1)
            return result

        def adaptive_taylor_sin(x, n_terms=5):
            # Reduce angle to principal range for better convergence
            x_reduced = x % (2 * math.pi)
            if x_reduced > math.pi:
                x_reduced = 2 * math.pi - x_reduced
            result = 0.0
            for n in range(n_terms):
                result += ((-1)**n / math.factorial(2*n + 1)) * x_reduced**(2*n + 1)
            return result
        """

        mock_skill_context.get_file_content.return_value = calculus_code

        # Act
        calculus_analysis = self.skill.analyze_calculus_implementations(
            mock_skill_context,
            "calculus.py",
        )

        # Assert
        assert "numerical_errors" in calculus_analysis
        assert "convergence_issues" in calculus_analysis
        assert "accuracy_problems" in calculus_analysis
        assert len(calculus_analysis["numerical_errors"]) >= 3

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_probability_distributions(self, mock_skill_context) -> None:
        """Given probability code, skill checks distribution correctness."""
        # Arrange
        probability_code = """
        import numpy as np
        import random

        def sample_normal_distribution_bad():
            # Incorrect Box-Muller implementation
            u1 = random.random()
            u2 = random.random()
            z = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
            return z  # Only returns one of two normal variables

        def sample_normal_distribution_good():
            # Correct Box-Muller implementation
            u1 = random.random()
            u2 = random.random()
            z1 = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
            z2 = np.sqrt(-2 * np.log(u1)) * np.sin(2 * np.pi * u2)
            return z1, z2

        def calculate_variance_wrong(data):
            # Incorrect variance calculation (using N instead of N-1)
            n = len(data)
            mean = sum(data) / n
            variance = sum((x - mean)**2 for x in data) / n
            return variance  # Should divide by (n-1) for sample variance

        def calculate_variance_correct(data):
            # Correct sample variance calculation
            n = len(data)
            if n < 2:
                return 0.0
            mean = sum(data) / n
            variance = sum((x - mean)**2 for x in data) / (n - 1)
            return variance

        def bayesian_update_bad(prior, likelihood):
            # Missing normalization
            posterior = prior * likelihood
            return posterior

        def bayesian_update_good(prior, likelihood, evidence):
            # Proper Bayes' rule with normalization
            posterior = (prior * likelihood) / evidence
            return posterior
        """

        mock_skill_context.get_file_content.return_value = probability_code

        # Act
        probability_analysis = self.skill.analyze_probability_distributions(
            mock_skill_context,
            "probability.py",
        )

        # Assert
        assert "distribution_errors" in probability_analysis
        assert "sampling_issues" in probability_analysis
        assert "statistical_formulas" in probability_analysis
        assert len(probability_analysis["statistical_formulas"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_geometry_trigonometry_errors(self, mock_skill_context) -> None:
        """Given geometry/trig code, skill flags math errors."""
        # Arrange
        geometry_code = """
        import math

        def distance_between_points_bad(x1, y1, x2, y2):
            # Missing square root
            return (x2 - x1)**2 + (y2 - y1)**2

        def distance_between_points_good(x1, y1, x2, y2):
            return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        def angle_from_vectors_bad(v1, v2):
            # Doesn't handle zero vectors or numerical stability
            dot_product = sum(a * b for a, b in zip(v1, v2))
            mag1 = math.sqrt(sum(a * a for a in v1))
            mag2 = math.sqrt(sum(b * b for b in v2))
            cos_angle = dot_product / (mag1 * mag2)
            return math.acos(cos_angle)  # Can error if cos_angle > 1 due to precision

        def angle_from_vectors_good(v1, v2):
            dot_product = sum(a * b for a, b in zip(v1, v2))
            mag1 = math.sqrt(sum(a * a for a in v1))
            mag2 = math.sqrt(sum(b * b for b in v2))

            if mag1 == 0 or mag2 == 0:
                return 0.0  # One vector is zero

            cos_angle = dot_product / (mag1 * mag2)
            # Clamp to handle numerical errors
            cos_angle = max(-1.0, min(1.0, cos_angle))
            return math.acos(cos_angle)

        def triangle_area_bad(a, b, c):
            # Heron's formula without checking triangle inequality
            s = (a + b + c) / 2
            area = math.sqrt(s * (s - a) * (s - b) * (s - c))
            return area  # Can be negative for invalid triangles

        def triangle_area_good(a, b, c):
            # Check triangle inequality first
            if a + b <= c or a + c <= b or b + c <= a:
                raise ValueError("Invalid triangle side lengths")
            s = (a + b + c) / 2
            area_squared = s * (s - a) * (s - b) * (s - c)
            if area_squared < 0:
                return 0.0  # Numerical error
            return math.sqrt(area_squared)
        """

        mock_skill_context.get_file_content.return_value = geometry_code

        # Act
        geometry_analysis = self.skill.analyze_geometry_trigonometry(
            mock_skill_context,
            "geometry.py",
        )

        # Assert
        assert "formula_errors" in geometry_analysis
        assert "edge_case_handling" in geometry_analysis
        assert "numerical_stability" in geometry_analysis
        assert len(geometry_analysis["formula_errors"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_computational_complexity(self, mock_skill_context) -> None:
        """Given algorithms, skill assesses computational complexity."""
        # Arrange
        complexity_code = """
        def fibonacci_recursive(n):
            # Exponential time complexity O(2^n)
            if n <= 1:
                return n
            return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

        def fibonacci_iterative(n):
            # Linear time complexity O(n)
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b

        def matrix_multiplication_naive(A, B):
            # O(n^3) naive multiplication
            n = len(A)
            C = [[0 for _ in range(n)] for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        C[i][j] += A[i][k] * B[k][j]
            return C

        def prime_factors_naive(n):
            # Inefficient O(sqrt(n)) factoring
            factors = []
            d = 2
            while d * d <= n:
                while n % d == 0:
                    factors.append(d)
                    n //= d
                d += 1
            if n > 1:
                factors.append(n)
            return factors

        def gcd_euclidean(a, b):
            # Efficient O(log(min(a,b))) algorithm
            while b:
                a, b = b, a % b
            return a
        """

        mock_skill_context.get_file_content.return_value = complexity_code

        # Act
        complexity_analysis = self.skill.analyze_computational_complexity(
            mock_skill_context,
            "algorithms.py",
        )

        # Assert
        assert "complexity_issues" in complexity_analysis
        assert "inefficient_algorithms" in complexity_analysis
        assert "optimization_opportunities" in complexity_analysis
        assert len(complexity_analysis["inefficient_algorithms"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_validates_mathematical_proofs(self, mock_skill_context) -> None:
        """Given proofs, skill checks logical correctness."""
        # Arrange
        proof_code = """
        def is_prime_bruteforce(n):
            \"\"\"Check if n is prime by testing divisibility.\"\"\"
            if n < 2:
                return False
            if n == 2:
                return True
            if n % 2 == 0:
                return False
            # Only need to check up to sqrt(n)
            for i in range(3, int(n**0.5) + 1, 2):
                if n % i == 0:
                    return False
            return True

        def goldbach_conjecture_test(limit):
            \"\"\"Test Goldbach's conjecture up to limit.\"\"\"
            for n in range(4, limit + 1, 2):
                found = False
                for p in range(2, n // 2 + 1):
                    if is_prime_bruteforce(p) and is_prime_bruteforce(n - p):
                        found = True
                        break
                if not found:
                    print(f"Counterexample found: {n}")
                    return False
            return True

        def collatz_conjecture_test(n):
            \"\"\"Test Collatz conjecture for a given n.\"\"\"
            original_n = n
            while n != 1:
                if n % 2 == 0:
                    n = n // 2
                else:
                    n = 3 * n + 1
                # Add safety to prevent infinite loops
                if n > 10**6:
                    print(f"Sequence for {original_n} exceeded limit")
                    return None
            return True

        def pythagorean_triple_test(a, b, c):
            \"\"\"Test if (a, b, c) forms a Pythagorean triple.\"\"\"
            # Sort to validate c is the largest
            sides = sorted([a, b, c])
            return abs(sides[0]**2 + sides[1]**2 - sides[2]**2) < 1e-10
        """

        mock_skill_context.get_file_content.return_value = proof_code

        # Act
        proof_analysis = self.skill.analyze_mathematical_proofs(
            mock_skill_context,
            "proofs.py",
        )

        # Assert
        assert "logical_correctness" in proof_analysis
        assert "edge_case_handling" in proof_analysis
        assert "mathematical_rigor" in proof_analysis
        assert "safety_measures" in proof_analysis

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generates_math_correctness_report(self, sample_findings) -> None:
        """Given full math analysis, skill creates structured summary."""
        # Arrange
        math_analysis = {
            "correctness_score": 7.5,
            "precision_issues": 3,
            "stability_problems": 2,
            "algorithm_errors": 1,
            "complexity_issues": 4,
            "statistical_fallacies": 2,
            "total_algorithms": 15,
            "high_risk_algorithms": 3,
            "findings": sample_findings,
        }

        # Act
        report = self.skill.create_math_correctness_report(math_analysis)

        # Assert
        assert "## Mathematical Correctness Assessment" in report
        assert "## Numerical Precision Analysis" in report
        assert "## Algorithm Correctness" in report
        assert "## Statistical Validity" in report
        assert "## Recommendations" in report
        assert "7.5" in report  # Correctness score
        assert "15" in report  # Total algorithms

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_mathematical_improvements(self, mock_skill_context) -> None:
        """Given math analysis, skill recommends improvements."""
        # Arrange
        analysis_results = {
            "has_precision_issues": True,
            "has_stability_problems": True,
            "uses_unstable_algorithms": True,
            "lacks_error_bounds": True,
            "missing_convergence_checks": True,
        }

        # Act
        recommendations = self.skill.generate_mathematical_recommendations(
            analysis_results,
        )

        # Assert
        assert len(recommendations) > 0
        categories = [rec["category"] for rec in recommendations]
        assert "precision" in categories
        assert "stability" in categories
        assert "algorithms" in categories
        assert "validation" in categories

        for rec in recommendations:
            assert "technique" in rec
            assert "benefit" in rec
            assert "implementation" in rec
            assert "examples" in rec
