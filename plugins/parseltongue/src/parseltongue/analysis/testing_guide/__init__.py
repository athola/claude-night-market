"""Testing guide skill for parseltongue.

Package layout
--------------
_structure.py       -- AST parsing, test structure, coverage gaps,
                       mock usage, performance, and the async entry
                       point. Stateful (uses ``self``); kept as a
                       mixin.
_quality.py         -- Stateless test-quality scoring functions
                       (C9, issue #485).
_recommendations.py -- Stateless TDD workflow / fixture / tool /
                       doc recommendation functions (C9, #485).

C9 (PR #470 review): the prior layout used three mixins composed
into ``TestingGuideSkill`` via multiple inheritance. The two
stateless namespaces (quality + recommendations) were demoted to
module-level functions; this class now delegates to them while
keeping its public method surface unchanged so existing callers
(``cli.py``, the test suite) need no changes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import _quality, _recommendations
from ._constants import HEAVY_PARAMETRIZE_THRESHOLD, MIN_FUNCTIONS_FOR_PARAMETRIZE
from ._structure import TestStructureMixin

if TYPE_CHECKING:
    import ast

__all__ = [
    "HEAVY_PARAMETRIZE_THRESHOLD",
    "MIN_FUNCTIONS_FOR_PARAMETRIZE",
    "TestingGuideSkill",
]


class TestingGuideSkill(TestStructureMixin):
    """Analyze test quality and provide testing recommendations.

    Stateless quality- and recommendation-shaped methods delegate
    to module-level functions in ``_quality`` and
    ``_recommendations``; AST-based structure analysis stays on the
    base mixin where ``self`` is genuinely used for shared parsing
    state across the public ``analyze_testing`` workflow.
    """

    # --- _quality (delegates) -------------------------------------------

    def evaluate_test_quality(self, code: str) -> dict[str, Any]:
        return _quality.evaluate_test_quality(code)

    def evaluate_maintainability(self, code: str) -> dict[str, Any]:
        return _quality.evaluate_maintainability(code)

    def validate_async_testing(self, code: str) -> dict[str, Any]:
        return _quality.validate_async_testing(code)

    # --- _recommendations (delegates) -----------------------------------

    def recommend_tdd_workflow(self, code: str) -> dict[str, Any]:
        return _recommendations.recommend_tdd_workflow(code)

    def suggest_improvements(self, code: str) -> dict[str, Any]:
        return _recommendations.suggest_improvements(code)

    def generate_test_fixtures(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        return _recommendations.generate_test_fixtures(code, _tree=_tree)

    def recommend_test_types(self, code: str) -> dict[str, Any]:
        return _recommendations.recommend_test_types(code)

    def recommend_testing_tools(self, code: Any) -> dict[str, Any]:
        return _recommendations.recommend_testing_tools(code)

    def generate_test_documentation(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        return _recommendations.generate_test_documentation(code, _tree=_tree)
