"""Makefile review skill -- mixin-based composition.

Public API preserved verbatim from the prior 921-line
``makefile_review.py`` module so existing imports keep working:

    from pensive.skills.makefile_review import MakefileReviewSkill
"""

from __future__ import annotations

from typing import ClassVar

from ..base import BaseReviewSkill
from ._analysis import AnalysisMixin
from ._helpers import HelpersMixin
from ._quality import QualityMixin
from ._reporting import ReportingMixin

__all__ = ["MakefileReviewSkill"]


class MakefileReviewSkill(
    HelpersMixin,
    AnalysisMixin,
    QualityMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Skill for reviewing makefiles and build system configurations."""

    skill_name: ClassVar[str] = "makefile_review"
    supported_languages: ClassVar[list[str]] = ["makefile", "make"]

    def __init__(self) -> None:
        """Initialize the makefile review skill."""
        super().__init__()
