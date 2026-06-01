"""Test review skill: mixin-based composition.

Public API preserved verbatim from the prior 902-line
``test_review.py`` module so existing imports keep working:

    from pensive.skills.test_review import TestReviewSkill
"""

from __future__ import annotations

from typing import ClassVar

from ..base import BaseReviewSkill
from ._coverage import CoverageMixin
from ._patterns import PatternsMixin
from ._reporting import ReportingMixin
from ._structure import StructureMixin

__all__ = ["TestReviewSkill"]


class TestReviewSkill(
    CoverageMixin,
    StructureMixin,
    PatternsMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Skill for reviewing test quality, coverage, and patterns."""

    __test__ = False  # Not a pytest test class
    skill_name: ClassVar[str] = "test-review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "javascript",
        "typescript",
        "rust",
    ]
