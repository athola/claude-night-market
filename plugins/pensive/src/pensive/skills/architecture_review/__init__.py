"""Architecture review skill -- mixin-based composition (AR-01).

Public API preserved verbatim from the prior 968-line
``architecture_review.py`` module so existing imports keep
working:

    from pensive.skills.architecture_review import ArchitectureReviewSkill

The skill body now composes five topical mixins
(patterns, principles, documentation, quality, reporting),
each in its own ~100-200 line module mirroring the
``rust_review/`` package layout.
"""

from __future__ import annotations

from typing import ClassVar

from ..base import BaseReviewSkill
from ._constants import (
    COHESION_SCORE_HIGH,
    COHESION_SCORE_MEDIUM,
    COUPLING_DEPENDENCY_SCALE,
    COUPLING_VIOLATION_WEIGHT,
    MIN_ADR_SECTIONS,
    MIN_EVENT_COMPONENTS,
    MIN_LAYERS_FOR_LAYERED,
    MIN_RESPONSIBILITIES_FOR_LOW_COHESION,
    MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION,
    MIN_SERVICES_FOR_MICROSERVICES,
    MIN_VIOLATIONS_TO_REPORT,
    _BUILTIN_EXC_NAMES,
    _SRP_KEYWORDS,
    logger,
)
from .documentation import DocumentationMixin
from .patterns import PatternsMixin
from .principles import PrinciplesMixin
from .quality import QualityMixin
from .reporting import ReportingMixin


class ArchitectureReviewSkill(
    PatternsMixin,
    PrinciplesMixin,
    DocumentationMixin,
    QualityMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Review software architecture and design patterns."""

    skill_name = "architecture_review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "typescript",
        "javascript",
        "java",
        "rust",
        "go",
    ]


__all__ = [
    "COHESION_SCORE_HIGH",
    "COHESION_SCORE_MEDIUM",
    "COUPLING_DEPENDENCY_SCALE",
    "COUPLING_VIOLATION_WEIGHT",
    "MIN_ADR_SECTIONS",
    "MIN_EVENT_COMPONENTS",
    "MIN_LAYERS_FOR_LAYERED",
    "MIN_RESPONSIBILITIES_FOR_LOW_COHESION",
    "MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION",
    "MIN_SERVICES_FOR_MICROSERVICES",
    "MIN_VIOLATIONS_TO_REPORT",
    "ArchitectureReviewSkill",
    "_BUILTIN_EXC_NAMES",
    "_SRP_KEYWORDS",
]
# AR-F2: ``logger`` is intentionally not exported. The original
# single-file module did not export it either; it stays an
# internal binding accessible via the per-mixin imports.
