"""API review skill: mixin-based composition.

Public API preserved verbatim from the prior 760-line
``api_review.py`` module so existing imports keep working:

    from pensive.skills.api_review import ApiReviewSkill
"""

from __future__ import annotations

from typing import ClassVar

from ..base import BaseReviewSkill
from ._language import LanguageMixin
from ._quality import QualityMixin
from ._reporting import ReportingMixin

__all__ = ["ApiReviewSkill"]


class ApiReviewSkill(
    LanguageMixin,
    QualityMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Review API surface and quality."""

    skill_name: ClassVar[str] = "api_review"
    supported_languages: ClassVar[list[str]] = [
        "typescript",
        "javascript",
        "python",
        "rust",
    ]
