"""Design pattern detection skill for parseltongue.

Package layout
--------------
_constants.py      -- shared numeric thresholds and frozen sets
_core.py           -- AST parsing, class/factory/decorator detection,
                      find_patterns, match_patterns
_test_patterns.py  -- recognize_test_patterns
_ddd.py            -- DDD: Entity, Value Object, Repository, Service
_gof.py            -- GoF patterns, async patterns
_analysis.py       -- performance, architectural, anti-patterns
_improvements.py   -- DSL, suggestions, consistency, variations,
                      general recognition, docs, comparison
"""

from __future__ import annotations

from ._analysis import AnalysisPatternMixin
from ._constants import (
    _OBSERVER_METHODS,
    MIN_FACTORY_RETURN_CLASSES,
    MIN_OBSERVER_METHODS,
    MIN_REPO_METHODS,
)
from ._core import PatternMatchingCoreMixin
from ._ddd import DDDPatternMixin
from ._gof import GoFPatternMixin
from ._improvements import ImprovementsMixin
from ._test_patterns import TestPatternMixin

__all__ = [
    "MIN_FACTORY_RETURN_CLASSES",
    "MIN_OBSERVER_METHODS",
    "MIN_REPO_METHODS",
    "_OBSERVER_METHODS",
    "PatternMatchingSkill",
]


class PatternMatchingSkill(
    PatternMatchingCoreMixin,
    TestPatternMixin,
    DDDPatternMixin,
    GoFPatternMixin,
    AnalysisPatternMixin,
    ImprovementsMixin,
):
    """Detect design patterns in Python code using AST analysis."""
