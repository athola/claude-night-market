"""Security reporting and recommendation generation for Rust review."""

from __future__ import annotations

from typing import Any

__all__ = ["ReportingMixin"]

# Rust analysis thresholds
MIN_TEST_COVERAGE = 0.8  # Minimum acceptable test coverage
MAX_DEPENDENCIES = 20  # Maximum recommended dependencies

# A-11: severity buckets as frozensets so each call avoids list allocation.
# Severity classification for rust_review finding types. Every emitted
# "type" should appear in exactly one set; an unmapped type falls through
# to "low", which under-triages real memory-safety bugs. See
# categorize_rust_severity below and test_rust_review_severity.py.
_CRITICAL_TYPES = frozenset(
    {
        # Memory-undefined-behavior and data races.
        "buffer_overflow",
        "data_race",
        "transmute",  # reinterpret cast: UB when sizes differ
        "transmute_copy",  # copy-cast: UB
        "repr_packed",  # unaligned reference to a packed field: UB
        "mutable_static",  # `static mut`: the source of data races
        "use_after_move",  # use after move: memory unsafety
        "pointer_offset",  # unchecked pointer arithmetic: OOB is UB
        "box_from_raw",  # unsafe raw-pointer construction: double-free risk
    }
)
_HIGH_TYPES = frozenset(
    {
        # Security-relevant, concurrency UB, or likely-exploitable correctness.
        "deprecated_dependency",
        "refcell_threading",  # RefCell shared across threads: UB
        "rc_in_async",  # Rc is not Send: data-race risk in async
        "mixed_borrows",  # aliased mutable + immutable borrow: UB
        "sql_format_interpolation",  # SQL injection
        "potential_overflow",  # integer overflow: panic or wraparound
        "index_access",  # unchecked indexing: OOB panic
        "narrowing_to_byte_cast",  # numeric truncation: correctness/security
        "precision_loss_cast",  # lossy numeric cast
        "length_truncation_cast",  # length truncation
        "mutex_usage",  # MutexGuard held across .await: deadlock
    }
)
_MEDIUM_TYPES = frozenset(
    {
        # Likely-incorrect usage, best-practice, or resource leaks.
        "unwrap_usage",
        "missing_docs",
        "unsafe_block",
        "unsafe_function",
        "float_exact_compare",  # exact float comparison: logic error
        "mem_forget",  # resource leak via mem::forget
        "drop_ref",  # dropped reference: resource leak
        "unwrap",
        "unwrap_panic",
        "explicit_panic",
        "missing_await",  # future dropped without await: correctness
        "blocking_sleep",  # blocking call inside async
        "wildcard_panic",
        "wildcard_unreachable",
        "wildcard_empty_arm",
        "ptr_arg",  # &Vec<T> should be &[T]
        "from_over_into",  # conversion direction
        "discarded_conversion_error",
        "silent_discard",  # result/Result dropped without inspection
        "short_error_message",
        "boolean_blindness",
        "stringly_typed_comparison",
        "vec_as_set_or_map",  # O(n) lookup where a set/map fits
        "box_free",  # needless heap allocation
        "rc_refcell_cycle",  # reference-count cycle: memory leak
        "atomic_usage",  # concurrency worth reviewing
        "custom_linker",
        "hidden_control_flow",
        "undocumented_unsafe_macro",
        "cfg_test_outside_mod",
        "magic_number_state_constant",
    }
)


class ReportingMixin:
    """Mixin providing report generation and recommendation logic."""

    def create_rust_security_report(
        self,
        analysis: dict[str, Any],
    ) -> str:
        """Generate a Rust security-focused report.

        Args:
            analysis: Complete Rust analysis results

        Returns:
            Markdown formatted security report
        """
        unsafe_code = analysis.get("unsafe_code", {})
        unsafe_block_list = unsafe_code.get("unsafe_blocks", [])
        unsafe_blocks = len(unsafe_block_list)
        unsafe_documented = sum(
            1 for b in unsafe_block_list if not b.get("lacks_documentation", True)
        )

        ownership = analysis.get("ownership", {})
        ownership_violations = len(ownership.get("violations", []))

        data_race_info = analysis.get("data_races", 0)
        data_races = (
            data_race_info
            if isinstance(data_race_info, int)
            else len(data_race_info.get("data_races", []))
        )

        memory_safety = analysis.get("memory_safety", {})
        memory_safety_issues = (
            len(memory_safety.get("unsafe_operations", []))
            + len(memory_safety.get("buffer_overflows", []))
            + len(memory_safety.get("use_after_free", []))
        )

        deps = analysis.get("dependencies", {})
        dependency_vulnerabilities = len(deps.get("security_concerns", []))

        panic_info = analysis.get("panic_propagation", {})
        panic_points = len(panic_info.get("panic_points", []))

        security_score = analysis.get("security_score", 0.0)

        report = f"""## Rust Security Assessment

Security Score: {security_score}/10

## Unsafe Code Analysis

Total unsafe blocks: {unsafe_blocks}
Documented unsafe blocks: {unsafe_documented}
Undocumented unsafe blocks: {unsafe_blocks - unsafe_documented}

## Memory Safety

Memory safety issues detected: {memory_safety_issues}
Ownership violations: {ownership_violations}

## Concurrency Safety

Potential data races: {data_races}

## Dependency Security

Dependency vulnerabilities: {dependency_vulnerabilities}

## Error Handling

Panic points detected: {panic_points}
"""

        findings = analysis.get("findings", [])
        if findings:
            report += "\n## Detailed Findings\n\n"
            for finding in findings:
                report += f"- {finding}\n"

        return report

    def categorize_rust_severity(
        self,
        issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Assign severity levels to Rust issues.

        Args:
            issues: List of Rust issues to categorize

        Returns:
            List of issues with severity added
        """
        categorized = []
        for issue in issues:
            issue_copy = issue.copy()
            issue_type = issue.get("type", "")

            if issue_type in _CRITICAL_TYPES:
                issue_copy["severity"] = "critical"
            elif issue_type in _HIGH_TYPES:
                issue_copy["severity"] = "high"
            elif issue_type in _MEDIUM_TYPES:
                issue_copy["severity"] = "medium"
            else:
                issue_copy["severity"] = "low"

            categorized.append(issue_copy)

        return categorized

    def generate_rust_recommendations(
        self,
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate Rust best practice recommendations.

        Args:
            analysis: Codebase analysis results

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        if analysis.get("uses_unsafe"):
            recommendations.append(
                {
                    "category": "unsafe",
                    "practice": "Document all unsafe code blocks",
                    "benefit": "Improves code review and maintenance",
                    "implementation": ("Add safety documentation to all unsafe blocks"),
                }
            )

        if analysis.get("async_code"):
            recommendations.append(
                {
                    "category": "async",
                    "practice": ("Use tokio::time instead of std::thread::sleep"),
                    "benefit": "Prevents blocking the async runtime",
                    "implementation": ("Replace blocking ops with async equivalents"),
                }
            )

        if analysis.get("test_coverage", 1.0) < MIN_TEST_COVERAGE:
            recommendations.append(
                {
                    "category": "testing",
                    "practice": "Increase test coverage",
                    "benefit": "Catches bugs earlier in development",
                    "implementation": ("Add unit tests for uncovered code paths"),
                }
            )

        if analysis.get("dependency_count", 0) > MAX_DEPENDENCIES:
            recommendations.append(
                {
                    "category": "dependencies",
                    "practice": "Audit and minimize dependencies",
                    "benefit": "Reduces attack surface and build times",
                    "implementation": ("Review dependencies and remove unused ones"),
                }
            )

        if analysis.get("macro_heavy"):
            recommendations.append(
                {
                    "category": "macros",
                    "practice": "Document complex macros",
                    "benefit": "Makes code easier to understand",
                    "implementation": ("Add doc comments to all custom macros"),
                }
            )

        return recommendations
