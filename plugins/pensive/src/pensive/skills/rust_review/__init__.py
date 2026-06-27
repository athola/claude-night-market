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

from dataclasses import dataclass
from typing import Any, ClassVar

from ..base import AnalysisResult, BaseReviewSkill
from .builtins import BuiltinsMixin
from .cargo import CargoBuildMixin
from .coercion_params import CoercionParamsMixin
from .conversion_traits import ConversionTraitsMixin
from .float_equality import FloatEqualityMixin
from .idiomatic_elision import IdiomaticElisionMixin
from .match_wildcard import MatchWildcardMixin
from .mem_forget import MemForgetMixin
from .mutable_statics import MutableStaticMixin
from .native_modeling import NativeModelingMixin
from .numeric_cast import NumericCastMixin
from .ownership import OwnershipMixin
from .patterns import PatternsMixin
from .reporting import MAX_DEPENDENCIES, MIN_TEST_COVERAGE, ReportingMixin
from .repr_packed import ReprPackedMixin
from .safety import SafetyMixin
from .structure import StructureMixin
from .transmute_audit import TransmuteAuditMixin

__all__ = [
    "MAX_DEPENDENCIES",
    "MIN_TEST_COVERAGE",
    "RUST_AUDIT_REGISTRY",
    "RustAuditSpec",
    "RustReviewSkill",
]


@dataclass(frozen=True)
class RustAuditSpec:
    """Declarative description of one Rust audit.

    The registry below is the single source of truth for which audits
    run and in what order. ``analyze()`` iterates the registry instead
    of enumerating each audit by hand, so adding an audit means adding
    one row here (plus the mixin that supplies the method) rather than
    editing the orchestrator body in a second place.
    """

    info_key: str
    method_name: str
    scope: str  # "file" runs only with a file_path; "context" always runs


# Order is load-bearing: ``analyze()`` builds ``result.info`` by
# iterating this tuple, so the insertion order of the output dict
# matches the order here. File-scoped audits precede context-scoped
# audits to preserve the original behavior.
RUST_AUDIT_REGISTRY: tuple[RustAuditSpec, ...] = (
    RustAuditSpec("unsafe_code", "analyze_unsafe_code", "file"),
    RustAuditSpec("ownership", "analyze_ownership", "file"),
    RustAuditSpec("data_races", "analyze_data_races", "file"),
    RustAuditSpec("memory_safety", "analyze_memory_safety", "file"),
    RustAuditSpec("panic_propagation", "analyze_panic_propagation", "file"),
    RustAuditSpec("async_patterns", "analyze_async_patterns", "file"),
    RustAuditSpec("macros", "analyze_macros", "file"),
    RustAuditSpec("traits", "analyze_traits", "file"),
    RustAuditSpec("const_generics", "analyze_const_generics", "file"),
    RustAuditSpec("silent_returns", "analyze_silent_returns", "file"),
    RustAuditSpec("collection_types", "analyze_collection_types", "file"),
    RustAuditSpec("sql_injection", "analyze_sql_injection", "file"),
    RustAuditSpec("cfg_test_misuse", "analyze_cfg_test_misuse", "file"),
    RustAuditSpec("error_messages", "analyze_error_messages", "file"),
    RustAuditSpec("builtin_preference", "analyze_builtin_preference", "file"),
    RustAuditSpec("native_type_modeling", "analyze_native_type_modeling", "file"),
    RustAuditSpec("idiomatic_elision", "analyze_idiomatic_elision", "file"),
    RustAuditSpec("coercion_params", "analyze_coercion_params", "file"),
    RustAuditSpec("conversion_traits", "analyze_conversion_traits", "file"),
    RustAuditSpec("numeric_cast", "analyze_numeric_cast_safety", "file"),
    RustAuditSpec("mutable_statics", "analyze_mutable_statics", "file"),
    RustAuditSpec("match_exhaustiveness", "analyze_match_exhaustiveness", "file"),
    RustAuditSpec("transmute", "analyze_transmute_safety", "file"),
    RustAuditSpec("float_equality", "analyze_float_equality", "file"),
    RustAuditSpec("mem_forget", "analyze_mem_forget", "file"),
    RustAuditSpec("repr_packed", "analyze_repr_packed", "file"),
    RustAuditSpec("duplicate_validators", "analyze_duplicate_validators", "file"),
    RustAuditSpec("dependencies", "analyze_dependencies", "context"),
    RustAuditSpec("build_configuration", "analyze_build_configuration", "context"),
)


class RustReviewSkill(
    SafetyMixin,
    OwnershipMixin,
    CargoBuildMixin,
    StructureMixin,
    PatternsMixin,
    BuiltinsMixin,
    NativeModelingMixin,
    IdiomaticElisionMixin,
    CoercionParamsMixin,
    ConversionTraitsMixin,
    NumericCastMixin,
    MutableStaticMixin,
    MatchWildcardMixin,
    TransmuteAuditMixin,
    FloatEqualityMixin,
    MemForgetMixin,
    ReprPackedMixin,
    ReportingMixin,
    BaseReviewSkill,
):
    """Skill for reviewing Rust code with safety and security focus."""

    skill_name: ClassVar[str] = "rust_review"
    supported_languages: ClassVar[list[str]] = ["rust"]

    audit_registry: ClassVar[tuple[RustAuditSpec, ...]] = RUST_AUDIT_REGISTRY

    def analyze(self, context: Any, file_path: str = "") -> AnalysisResult:
        result = AnalysisResult()
        info: dict[str, Any] = {}

        for spec in self.audit_registry:
            if spec.scope == "file":
                if not file_path:
                    continue
                info[spec.info_key] = getattr(self, spec.method_name)(
                    context, file_path
                )
            else:
                info[spec.info_key] = getattr(self, spec.method_name)(context)

        result.info = info
        return result
