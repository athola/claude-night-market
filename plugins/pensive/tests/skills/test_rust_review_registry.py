"""Tests for the RustReviewSkill audit registry.

The registry (``RUST_AUDIT_REGISTRY``) is the single source of truth
for which audits ``RustReviewSkill.analyze()`` runs and in what order.
These tests guard the registry against drift: every expected audit must
be present, every registered method must exist, and the composite
``analyze()`` output must match the registry order exactly.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pensive.skills.rust_review import (
    RUST_AUDIT_REGISTRY,
    RustAuditSpec,
    RustReviewSkill,
)

# The complete, ordered set of audits the skill is expected to run.
# File-scoped audits precede context-scoped audits. Updating this list
# is intentional and must accompany a registry change.
EXPECTED_AUDITS: tuple[tuple[str, str, str], ...] = (
    ("unsafe_code", "analyze_unsafe_code", "file"),
    ("ownership", "analyze_ownership", "file"),
    ("data_races", "analyze_data_races", "file"),
    ("memory_safety", "analyze_memory_safety", "file"),
    ("panic_propagation", "analyze_panic_propagation", "file"),
    ("async_patterns", "analyze_async_patterns", "file"),
    ("macros", "analyze_macros", "file"),
    ("traits", "analyze_traits", "file"),
    ("const_generics", "analyze_const_generics", "file"),
    ("silent_returns", "analyze_silent_returns", "file"),
    ("collection_types", "analyze_collection_types", "file"),
    ("sql_injection", "analyze_sql_injection", "file"),
    ("cfg_test_misuse", "analyze_cfg_test_misuse", "file"),
    ("error_messages", "analyze_error_messages", "file"),
    ("builtin_preference", "analyze_builtin_preference", "file"),
    ("native_type_modeling", "analyze_native_type_modeling", "file"),
    ("idiomatic_elision", "analyze_idiomatic_elision", "file"),
    ("coercion_params", "analyze_coercion_params", "file"),
    ("conversion_traits", "analyze_conversion_traits", "file"),
    ("numeric_cast", "analyze_numeric_cast_safety", "file"),
    ("mutable_statics", "analyze_mutable_statics", "file"),
    ("match_exhaustiveness", "analyze_match_exhaustiveness", "file"),
    ("transmute", "analyze_transmute_safety", "file"),
    ("float_equality", "analyze_float_equality", "file"),
    ("mem_forget", "analyze_mem_forget", "file"),
    ("repr_packed", "analyze_repr_packed", "file"),
    ("duplicate_validators", "analyze_duplicate_validators", "file"),
    ("dependencies", "analyze_dependencies", "context"),
    ("build_configuration", "analyze_build_configuration", "context"),
)


@pytest.mark.unit
class TestRustAuditRegistry:
    """Test suite for the Rust audit registry."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = RustReviewSkill()
        self.mock_context = Mock()
        repo = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.repo_path = repo
        self.mock_context.working_dir = repo

    def test_registry_contains_all_expected_audits_in_order(self) -> None:
        """Registry matches the expected audit set, ordering included."""
        actual = tuple(
            (spec.info_key, spec.method_name, spec.scope)
            for spec in RUST_AUDIT_REGISTRY
        )
        assert actual == EXPECTED_AUDITS

    def test_registry_has_no_duplicate_keys(self) -> None:
        """Each info key appears exactly once in the registry."""
        keys = [spec.info_key for spec in RUST_AUDIT_REGISTRY]
        assert len(keys) == len(set(keys))

    def test_every_registered_method_is_callable(self) -> None:
        """Each registered method resolves to a callable on the skill."""
        for spec in RUST_AUDIT_REGISTRY:
            method = getattr(self.skill, spec.method_name, None)
            assert callable(method), f"{spec.method_name} is not callable"

    def test_every_scope_is_valid(self) -> None:
        """Every audit declares a known scope."""
        for spec in RUST_AUDIT_REGISTRY:
            assert spec.scope in {"file", "context"}

    def test_skill_registry_is_the_module_registry(self) -> None:
        """The class binds the module-level registry as its source."""
        assert RustReviewSkill.audit_registry is RUST_AUDIT_REGISTRY

    def test_analyze_with_file_path_emits_all_keys_in_order(
        self, mock_skill_context
    ) -> None:
        """With a file path, analyze() emits every audit key in order."""
        mock_skill_context.get_file_content.return_value = "fn main() {}\n"
        result = self.skill.analyze(mock_skill_context, "sample.rs")
        expected_keys = [spec.info_key for spec in RUST_AUDIT_REGISTRY]
        assert list(result.info.keys()) == expected_keys

    def test_analyze_without_file_path_emits_only_context_keys(
        self, mock_skill_context
    ) -> None:
        """Without a file path, only context-scoped audits run, in order."""
        mock_skill_context.get_file_content.return_value = "fn main() {}\n"
        result = self.skill.analyze(mock_skill_context)
        expected_keys = [
            spec.info_key for spec in RUST_AUDIT_REGISTRY if spec.scope == "context"
        ]
        assert list(result.info.keys()) == expected_keys

    def test_audit_spec_is_frozen(self) -> None:
        """RustAuditSpec instances are immutable."""
        spec = RUST_AUDIT_REGISTRY[0]
        with pytest.raises((AttributeError, TypeError)):
            spec.info_key = "mutated"  # type: ignore[misc] - intentional frozen-field write to prove immutability

    def test_spec_constructor_round_trips(self) -> None:
        """RustAuditSpec exposes its fields as constructed."""
        spec = RustAuditSpec("k", "analyze_k", "file")
        assert (spec.info_key, spec.method_name, spec.scope) == (
            "k",
            "analyze_k",
            "file",
        )
