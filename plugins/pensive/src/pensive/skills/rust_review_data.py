"""Heuristic data for Rust code review.

Contains regex patterns, severity classifications,
recommendation templates, and report templates extracted
from RustReviewSkill to keep the main module focused on
analysis logic.
"""

from __future__ import annotations

# ── Regex patterns used across analysis methods ──────────────

# Unsafe code detection
UNSAFE_BLOCK_PATTERN = r"unsafe\s*\{"
UNSAFE_FN_PATTERN = r"unsafe\s+fn\s+(\w+)"
SAFETY_DOC_PATTERN = r"(?://+|///)\s*#?\s*Safety"

# Ownership and borrowing
RC_REFCELL_PATTERN = r"Rc<RefCell<"
RC_NEW_REFCELL_PATTERN = r"Rc::new\(RefCell"
MIXED_BORROWS_MUT_PATTERN = r"&mut\s+\w+"
MIXED_BORROWS_REF_PATTERN = r"&\s+\w+"

# Concurrency
ARC_MUTEX_PATTERN = r"Arc<Mutex<"
MUTEX_NEW_PATTERN = r"Mutex::new"
ATOMIC_TYPES = ("AtomicI32", "AtomicU32", "AtomicBool")

# Memory safety
POINTER_OFFSET_PATTERN = r"\*\w+\.offset\("
LARGE_OFFSET_PATTERN = r"\.offset\((10|[2-9]\d+)\)"
LIFETIME_ANNOTATION_PATTERN = r"fn\s+\w+<'a>.*->.*&'a"

# Panic / error handling
PANIC_CALL_PATTERN = r"panic!\s*\("
UNWRAP_CALL_PATTERN = r"\.unwrap\(\)"
INDEX_ACCESS_PATTERN = r"\w+\[\d+\]"

# Async patterns
ASYNC_FN_PATTERN = r"async\s+fn\s+\w+"
ASYNC_CALL_PATTERN = r"let\s+\w+\s*=\s*\w+\(\)"

# Macros
DERIVE_MACRO_PATTERN = r"#\[derive\("
MACRO_RULES_PATTERN = r"macro_rules!\s+(\w+)"
DOC_COMMENT_PATTERN = r"///|//!"

# Traits
TRAIT_DEF_PATTERN = r"trait\s+(\w+)"
TRAIT_METHOD_PATTERN = r"fn\s+(\w+)"
GENERIC_METHOD_PATTERN = r"fn\s+\w+<\w+>"
STATIC_METHOD_PATTERN = r"fn\s+\w+\(\)"
IMPL_FOR_PATTERN = r"impl\s+(\w+)\s+for\s+(\w+)"

# Const generics
CONST_GENERIC_STRUCT_PATTERN = r"struct\s+(\w+)<.*const\s+(\w+):\s*usize"
CONST_MAX_PATTERN = r"const\s+MAX:\s*usize"

# Build / Cargo
CARGO_DEP_PATTERN = r'(\w+)\s*=\s*"([^"]+)"'
TARGET_SECTION_PATTERN = r"\[target\.([^\]]+)\]"

# ── Severity classification map ──────────────────────────────

SEVERITY_MAP: dict[str, str] = {
    # Critical: memory corruption or concurrency bugs
    "buffer_overflow": "critical",
    "data_race": "critical",
    # High: security or dependency risks
    "deprecated_dependency": "high",
    # Medium: likely-incorrect usage
    "unwrap_usage": "medium",
    "missing_docs": "medium",
}

DEFAULT_SEVERITY = "low"

# ── Recommendation templates ─────────────────────────────────
#
# Each key matches a boolean flag in the analysis dict.
# The value is the recommendation dict returned by
# generate_rust_recommendations.

RECOMMENDATION_TEMPLATES: dict[str, dict[str, str]] = {
    "uses_unsafe": {
        "category": "unsafe",
        "practice": "Document all unsafe code blocks",
        "benefit": "Improves code review and maintenance",
        "implementation": "Add safety documentation to all unsafe blocks",
    },
    "async_code": {
        "category": "async",
        "practice": "Use tokio::time instead of std::thread::sleep",
        "benefit": "Prevents blocking the async runtime",
        "implementation": "Replace blocking ops with async equivalents",
    },
    "macro_heavy": {
        "category": "macros",
        "practice": "Document complex macros",
        "benefit": "Makes code easier to understand",
        "implementation": "Add doc comments to all custom macros",
    },
}

TESTING_RECOMMENDATION: dict[str, str] = {
    "category": "testing",
    "practice": "Increase test coverage",
    "benefit": "Catches bugs earlier in development",
    "implementation": "Add unit tests for uncovered code paths",
}

DEPENDENCY_RECOMMENDATION: dict[str, str] = {
    "category": "dependencies",
    "practice": "Audit and minimize dependencies",
    "benefit": "Reduces attack surface and build times",
    "implementation": "Review dependencies and remove unused ones",
}

# ── Security report template ─────────────────────────────────

SECURITY_REPORT_TEMPLATE = """\
## Rust Security Assessment

Security Score: {security_score}/10

## Unsafe Code Analysis

Total unsafe blocks: {unsafe_blocks}
Documented unsafe blocks: {unsafe_documented}
Undocumented unsafe blocks: {undocumented_unsafe}

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
