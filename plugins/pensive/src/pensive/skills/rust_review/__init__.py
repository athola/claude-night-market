"""Rust code review skill for pensive.

Provides Rust-specific analysis capabilities including:
- Unsafe code block detection and validation
- Ownership and borrowing pattern analysis
- Concurrency and data race detection
- Memory safety verification
- Error handling and panic propagation
- Async/await pattern checking
- Dependency and security auditing
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..base import AnalysisResult, BaseReviewSkill
from .builtins import BuiltinsMixin
from .cargo import CargoBuildMixin
from .ownership import OwnershipMixin
from .patterns import PatternsMixin
from .reporting import MAX_DEPENDENCIES, MIN_TEST_COVERAGE, ReportingMixin
from .safety import SafetyMixin
from .structure import StructureMixin

__all__ = [
    "RustReviewSkill",
    "MIN_TEST_COVERAGE",
    "MAX_DEPENDENCIES",
]


class RustReviewSkill(
    SafetyMixin,
    OwnershipMixin,
    CargoBuildMixin,
    StructureMixin,
    PatternsMixin,
    BuiltinsMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Skill for reviewing Rust code with safety and security focus."""

    skill_name: ClassVar[str] = "rust_review"
    supported_languages: ClassVar[list[str]] = ["rust"]

    def __init__(self) -> None:
        super().__init__()
        self._cached_content: str = ""
        self._cached_lines: list[str] = []

    def _get_lines(self, content: str) -> list[str]:
        if self._cached_content is not content:
            self._cached_content = content
            self._cached_lines = content.splitlines()
        return self._cached_lines

    def analyze(self, context: Any, file_path: str = "") -> AnalysisResult:
        result = AnalysisResult()
        info: dict[str, Any] = {}

        if file_path:
            info["unsafe_code"] = self.analyze_unsafe_code(context, file_path)
            info["ownership"] = self.analyze_ownership(context, file_path)
            info["data_races"] = self.analyze_data_races(context, file_path)
            info["memory_safety"] = self.analyze_memory_safety(context, file_path)
            info["panic_propagation"] = self.analyze_panic_propagation(
                context, file_path
            )
            info["async_patterns"] = self.analyze_async_patterns(context, file_path)
            info["macros"] = self.analyze_macros(context, file_path)
            info["traits"] = self.analyze_traits(context, file_path)
            info["const_generics"] = self.analyze_const_generics(context, file_path)
            info["silent_returns"] = self.analyze_silent_returns(context, file_path)
            info["collection_types"] = self.analyze_collection_types(context, file_path)
            info["sql_injection"] = self.analyze_sql_injection(context, file_path)
            info["cfg_test_misuse"] = self.analyze_cfg_test_misuse(context, file_path)
            info["error_messages"] = self.analyze_error_messages(context, file_path)
            info["builtin_preference"] = self.analyze_builtin_preference(
                context, file_path
            )
            info["duplicate_validators"] = self.analyze_duplicate_validators(
                context, file_path
            )

        info["dependencies"] = self.analyze_dependencies(context)
        info["build_configuration"] = self.analyze_build_configuration(context)

        result.info = info
        return result
