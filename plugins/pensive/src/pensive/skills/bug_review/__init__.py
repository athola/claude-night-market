"""Bug review skill: mixin-based composition.

Public API preserved verbatim from the prior 749-line
``bug_review.py`` module so existing imports keep working:

    from pensive.skills.bug_review import BugReviewSkill
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...utils import content_parser as _content_parser
from ..base import AnalysisResult, BaseReviewSkill, PatternSearch
from ._analysis import AnalysisMixin
from ._detection import DetectionMixin
from ._reporting import ReportingMixin

# Re-export for any callers that imported these from bug_review directly.
__all__ = ["BugReviewSkill"]

# Suppress unused-import warnings: content_parser and PatternSearch are
# referenced by the mixins via inherited self._detect_patterns; keeping
# them here documents the dependency surface.
_ = (_content_parser, PatternSearch, AnalysisResult)


class BugReviewSkill(
    DetectionMixin,
    AnalysisMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Detect and analyze software bugs."""

    skill_name = "bug_review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "javascript",
        "typescript",
        "rust",
        "java",
        "php",
    ]

    def analyze(self, context: Any, file_path: str) -> AnalysisResult:
        """Analyze a file for bugs."""
        findings = []

        detectors = [
            self.detect_null_pointer_dereference,
            self.detect_race_conditions,
            self.detect_memory_leaks,
            self.detect_sql_injection,
            self.detect_off_by_one_errors,
            self.detect_integer_overflow,
            self.detect_resource_leaks,
            self.detect_logical_errors,
            self.detect_type_confusion,
            self.detect_timing_attacks,
        ]

        for detector in detectors:
            for bug in detector(context, file_path):
                findings.append(bug)

        return AnalysisResult(issues=[], warnings=[], info={"bugs": findings})
