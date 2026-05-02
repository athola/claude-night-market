"""Testing guide skill for parseltongue.

Package layout
--------------
_structure.py      -- AST parsing, test structure, coverage gaps,
                      mock usage, performance, and the async entry point
_quality.py        -- test quality scoring, maintainability, async validation
_recommendations.py -- TDD workflow, improvement suggestions, fixture
                       generation, tool and type recommendations, docs
"""

from __future__ import annotations

from ._constants import HEAVY_PARAMETRIZE_THRESHOLD, MIN_FUNCTIONS_FOR_PARAMETRIZE
from ._quality import TestQualityMixin
from ._recommendations import TestRecommendationMixin
from ._structure import TestStructureMixin

__all__ = [
    "HEAVY_PARAMETRIZE_THRESHOLD",
    "MIN_FUNCTIONS_FOR_PARAMETRIZE",
    "TestingGuideSkill",
]


class TestingGuideSkill(TestStructureMixin, TestQualityMixin, TestRecommendationMixin):
    """Analyze test quality and provide testing recommendations."""
