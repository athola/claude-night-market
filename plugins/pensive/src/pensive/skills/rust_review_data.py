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

# ── Builtin preference patterns (#prefer-builtins) ─────────

# Conversion function name patterns that suggest a From/Into/
# TryFrom/TryInto/FromStr impl is more idiomatic.
BUILTIN_CONVERSION_PATTERNS: list[tuple[str, str, str]] = [
    (r"\bfn\s+parse_\w+\s*\(\s*\w+:\s*&str", "FromStr", "impl FromStr for <Type>"),
    (r"\bfn\s+\w+_from_\w+\s*\(", "From", "impl From<Source> for Target"),
    (r"\bfn\s+from_\w+\s*\(", "From", "impl From<Source> for Target"),
    (r"\bfn\s+try_convert\w*\s*\(", "TryFrom", "impl TryFrom<Source> for Target"),
    (r"\bfn\s+try_parse\w*\s*\(", "TryFrom", "impl TryFrom<Source> for Target"),
    (
        r"\bfn\s+into_\w+\s*\(",
        "Into",
        "impl From<Source> for Target (provides Into for free)",
    ),
    (r"\bfn\s+convert_\w+\s*\(", "From/TryFrom", "impl From<Source> for Target"),
]

# fn to_<type>(&self) -> suggest Into/From
BUILTIN_TO_METHOD_PATTERN = r"\bfn\s+to_\w+\s*\(\s*&self"
BUILTIN_TO_METHOD_TRAIT = "Into"
BUILTIN_TO_METHOD_REC = "impl From<&Self> for Target (provides Into for free)"

# fn *_to_string(&self) -> String -> suggest Display
BUILTIN_TO_STRING_PATTERN = r"\bfn\s+\w+_to_string\s*\(\s*&self\s*\)\s*->\s*String"
BUILTIN_TO_STRING_TRAIT = "Display"
BUILTIN_TO_STRING_REC = "impl Display for <Type> (provides ToString for free)"

# Standard trait replacement patterns
BUILTIN_STANDARD_TRAIT_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"\bfn\s+(?:default_\w+|new_default)\s*\(\s*\)\s*->",
        "Default",
        "impl Default or #[derive(Default)]",
    ),
    (r"\bfn\s+(?:format_\w+|display_\w+)\s*\(", "Display", "impl Display for <Type>"),
    (r"\bfn\s+as_\w+\s*\(\s*&self\s*\)\s*->\s*&", "AsRef", "impl AsRef<T> for <Type>"),
    (r"\bfn\s+(?:compare|equals?|is_equal)\s*\(", "PartialEq", "#[derive(PartialEq)]"),
]

# Error conversion helpers -> From<Error>
BUILTIN_ERROR_CONVERSION_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"\bfn\s+\w+_to_\w*err\w*\s*\(\s*\w+:\s*\w+",
        "From<Error>",
        "impl From<SourceError> for TargetError",
    ),
    (
        r"\bfn\s+(?:wrap|convert)_\w*err\w*\s*\(",
        "From<Error>",
        "impl From or thiserror #[from]",
    ),
]

# Manual combinator reimplementations
BUILTIN_MANUAL_COMBINATOR_PATTERNS: list[tuple[str, str, str, str]] = [
    (
        r"match\s+\w+\s*\{[^}]*Some\(\w+\)\s*=>\s*Some\(",
        "manual_map",
        ".map()",
        "clippy::manual_map",
    ),
    (
        r"match\s+\w+\s*\{[^}]*Some\(\w+\)\s*=>\s*\w+\s*,\s*None\s*=>",
        "manual_unwrap_or",
        ".unwrap_or()",
        "clippy::manual_unwrap_or",
    ),
    (
        r"if\s+\w+\.is_some\(\)\s*\{[^}]*\.unwrap\(\)",
        "manual_unwrap",
        "if let Some(v) = x",
        "",
    ),
]

# Exclusion patterns -- functions that should NOT be flagged
BUILTIN_EXCLUSION_PATTERNS: list[str] = [
    r"\bfn\s+to_lossy",
    r"\bfn\s+with_\w+\s*\(self",
    r"\bfn\s+serialize",
    r"\bfn\s+encode",
    r"\bfn\s+decode",
    r"\bfn\s+marshal",
    r"\bfn\s+unmarshal",
    # Multi-param conversions are context-dependent
    r"\bfn\s+(?:parse|convert|from)_\w+\([^)]*,[^)]*\)",
]

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
