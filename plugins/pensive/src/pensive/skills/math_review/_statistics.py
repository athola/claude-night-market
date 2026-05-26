"""Statistics mixin: fallacies and probability distributions."""

from __future__ import annotations

import re
from typing import Any


class StatisticsMixin:
    """Analyzes statistical fallacies and probability distribution errors."""

    def analyze_statistical_fallacies(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        correlation_causation_fallacy = []
        p_value_hacking = []
        sampling_biases = []
        multiple_testing_issues = []

        if re.search(r"correlation.*>.*return.*causes", content, re.DOTALL):
            correlation_causation_fallacy.append(
                "Correlation being interpreted as causation"
            )

        if re.search(r"for.*range\(.*\).*p_value.*<\s*0\.05", content, re.DOTALL):
            p_value_hacking.append("Multiple testing without correction detected")
            multiple_testing_issues.append(
                "Testing multiple hypotheses without Bonferroni correction"
            )

        if re.search(r"successful.*=.*\[.*for.*if.*successful\]", content, re.DOTALL):
            sampling_biases.append(
                "Survivorship bias - only analyzing successful cases"
            )

        if re.search(r"survey_friends_and_family", content):
            sampling_biases.append("Convenience sampling instead of random sampling")

        return {
            "correlation_causation_fallacy": correlation_causation_fallacy,
            "p_value_hacking": p_value_hacking,
            "sampling_biases": sampling_biases,
            "multiple_testing_issues": multiple_testing_issues,
        }

    def analyze_probability_distributions(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        content = context.get_file_content(file_path)

        distribution_errors: list[str] = []
        sampling_issues: list[str] = []
        statistical_formulas: list[str] = []

        if re.search(
            r"def\s+sample_normal_distribution_bad.*return\s+z\s*#.*Only returns one",
            content,
            re.DOTALL,
        ):
            sampling_issues.append(
                "Box-Muller implementation returns only one of two normal variables"
            )

        if re.search(
            r"def\s+calculate_variance_wrong.*variance\s*=\s*sum\(\(x\s*-\s*mean\)\*\*2.*\)\s*/\s*n",
            content,
            re.DOTALL,
        ):
            statistical_formulas.append(
                "Incorrect variance calculation using N instead of N-1"
            )

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
