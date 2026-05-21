"""Mathematical correctness review skill -- mixin-based composition.

Public API preserved verbatim from the prior 703-line
``math_review.py`` module so existing imports keep working:

    from pensive.skills.math_review import MathReviewSkill
"""

from __future__ import annotations

from typing import ClassVar

from ..base import BaseReviewSkill
from ._algorithms import AlgorithmsMixin
from ._numerical import NumericalMixin
from ._reporting import ReportingMixin
from ._statistics import StatisticsMixin


class MathReviewSkill(
    NumericalMixin,
    StatisticsMixin,
    AlgorithmsMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Skill for reviewing mathematical correctness in code."""

    skill_name = "math_review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "rust",
        "javascript",
        "typescript",
    ]


__all__ = ["MathReviewSkill"]
