"""Severity coverage for rust_review finding types.

Regression guard for the severity-mapping gap found in the
conserve-updates-1.9.12 review: the 13 new audit modules emit finding
types that were absent from the critical/high/medium sets, so
memory-undefined-behavior patterns (transmute, repr_packed,
mutable_static) silently fell through to the default "low" severity.
These tests pin the mapping so it cannot regress.
"""

from __future__ import annotations

import pytest

from pensive.skills.rust_review import RustReviewSkill
from pensive.skills.rust_review.reporting import (
    _CRITICAL_TYPES,
    _HIGH_TYPES,
    _MEDIUM_TYPES,
)


@pytest.mark.unit
class TestRustReviewSeverityCoverage:
    """Security-critical types must not fall through to the default 'low'."""

    @pytest.mark.parametrize(
        "issue_type",
        [
            "transmute",
            "transmute_copy",
            "repr_packed",
            "mutable_static",
            "use_after_move",
            "pointer_offset",
            "box_from_raw",
        ],
    )
    def test_memory_safety_types_are_critical(self, issue_type: str) -> None:
        assert issue_type in _CRITICAL_TYPES, (
            f"{issue_type!r} must be critical (memory UB / data race), "
            "not the default 'low'"
        )

    @pytest.mark.parametrize(
        "issue_type",
        [
            "sql_format_interpolation",
            "refcell_threading",
            "rc_in_async",
            "mixed_borrows",
            "potential_overflow",
            "index_access",
        ],
    )
    def test_security_and_concurrency_types_are_high(self, issue_type: str) -> None:
        assert issue_type in _HIGH_TYPES, f"{issue_type!r} must be high"

    @pytest.mark.parametrize(
        "issue_type", ["float_exact_compare", "mem_forget", "drop_ref"]
    )
    def test_likely_incorrect_types_are_medium(self, issue_type: str) -> None:
        assert issue_type in _MEDIUM_TYPES, f"{issue_type!r} must be medium"

    def test_sets_are_mutually_exclusive(self) -> None:
        """A type mapped to two severities would make categorization ambiguous."""
        overlap = _CRITICAL_TYPES & _HIGH_TYPES
        assert not overlap, f"critical/high overlap: {overlap}"
        overlap = _CRITICAL_TYPES & _MEDIUM_TYPES
        assert not overlap, f"critical/medium overlap: {overlap}"
        overlap = _HIGH_TYPES & _MEDIUM_TYPES
        assert not overlap, f"high/medium overlap: {overlap}"


@pytest.mark.unit
class TestCategorizeRustSeverity:
    """categorize_rust_severity assigns the mapped severity at runtime.

    The method does not read ``self``, so it can be invoked on the class
    directly without constructing a skill instance.
    """

    @pytest.mark.parametrize(
        "issue_type,expected",
        [
            ("transmute", "critical"),
            ("repr_packed", "critical"),
            ("mutable_static", "critical"),
            ("pointer_offset", "critical"),
            ("sql_format_interpolation", "high"),
            ("mixed_borrows", "high"),
            ("float_exact_compare", "medium"),
            ("mem_forget", "medium"),
            ("needless_lifetime", "low"),
            ("unused_unit", "low"),
            ("some_unknown_type", "low"),
        ],
    )
    def test_severity_assignment(self, issue_type: str, expected: str) -> None:
        out = RustReviewSkill.categorize_rust_severity(
            None, [{"type": issue_type, "line": 1}]
        )
        assert out[0]["severity"] == expected
