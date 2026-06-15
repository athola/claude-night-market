"""Heuristic data for Rust code review.

Contains regex patterns, severity classifications,
recommendation templates, and report templates extracted
from RustReviewSkill to keep the main module focused on
analysis logic.
"""

from __future__ import annotations

import re
from typing import TypedDict


class Finding(TypedDict):
    """The uniform per-line record every rust-review detector emits.

    Declaring the shape once gives mypy a schema to check the inline dict
    literals against, instead of the record living implicitly across the
    per-concern detector modules (PR #577 finding D2). All four keys are
    required; the strictness is the point.
    """

    line: int
    type: str
    recommendation: str
    clippy_lint: str


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
    (
        r"match\s+\w+\s*\{[^}]*=>\s*true\s*,[^}]*=>\s*false",
        "match_like_matches_macro",
        "matches!(x, Pattern)",
        "clippy::match_like_matches_macro",
    ),
]

# Exclusion patterns: functions that should NOT be flagged
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

# ── Native type-modeling patterns (#native-type-modeling) ────
#
# Detects code that compares or branches on bare primitives where a
# native Rust enum would let the compiler check the cases. Covers the
# "enums for comparisons" and "boolean blindness" ports. Newtype and
# type-state are documentation-only (modules/native-type-modeling.md)
# because reliable detection has too many false positives at I/O and
# storage boundaries.

# Identifier compared to a NON-EMPTY string literal: `status == "active"`.
# The `[^"]+` requires at least one char, so `s == ""` (an emptiness
# check, not a stringly-typed enum candidate) is intentionally excluded.
NATIVE_STRINGLY_COMPARISON_PATTERN = r'[A-Za-z_]\w*(?:\.\w+\(\))?\s*(?:==|!=)\s*"[^"]+"'
NATIVE_STRINGLY_COMPARISON_REC = (
    "model the value as an enum and compare with `matches!` or `==` "
    "(clippy::match_like_matches_macro)"
)

# Function signature carrying two or more `: bool` parameters:
# `fn paint(immediate: bool, antialias: bool)`. A single bool param is
# idiomatic and is not matched (no second `: bool`).
NATIVE_BOOLEAN_BLINDNESS_PATTERN = (
    r"\bfn\s+\w+[^(]*\([^)]*:\s*bool\b[^)]*,[^)]*:\s*bool\b[^)]*\)"
)
NATIVE_BOOLEAN_BLINDNESS_REC = (
    "replace bool parameters with two-variant enums so call sites are "
    "self-documenting and arguments cannot be transposed (avoids "
    "boolean blindness)"
)

# A named integer state constant: `const STATUS_ACTIVE: u8 = 0;`. The
# name must carry a state-ish stem and the value must be a plain decimal
# literal. Requiring `= <decimal>;` excludes bitmask shifts (`1 << 2`)
# and hex (`0x01`), which are `bitflags!` candidates rather than enums,
# keeping this conservative.
NATIVE_INT_STATE_CONST_PATTERN = (
    r"\bconst\s+[A-Z0-9_]*(?:STATUS|STATE|MODE|KIND|PHASE|STEP)"
    r"[A-Z0-9_]*\s*:\s*(?:u8|u16|u32|u64|usize|i8|i16|i32|i64|isize)"
    r"\s*=\s*\d+\s*;"
)
NATIVE_INT_STATE_CONST_REC = (
    "model these integer state constants as an enum (add explicit "
    "`= <n>` discriminants if the wire values matter); use `bitflags` "
    "instead when the values are composable masks"
)

# Lines that should never trigger native-modeling findings.
NATIVE_MODELING_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments
    r"#\[\w*cfg\(",  # cfg attributes
    r"matches!\s*\(",  # already using the idiom
]

# ── Idiomatic elision patterns (#idiomatic-elision) ──────────
#
# Flags annotations the compiler already infers: explicit lifetimes
# that lifetime elision would supply, and trailing `return` statements
# that the block's tail expression makes redundant. Grounded in the
# Rust Reference (src/lifetime-elision.md, src/expressions/block-expr.md)
# and clippy::needless_lifetimes / clippy::needless_return.

# Captures a single-lifetime, no-type-param fn signature so the mixin
# can count how many input references use that lifetime. Group 1 is the
# lifetime token, group 2 the parameter list, group 3 the return type.
# A type param (`<'a, T>`) does not match: bounds may force the
# annotation, so that case is conservatively skipped.
ELISION_FN_LIFETIME_SIG_PATTERN = (
    r"\bfn\s+\w+\s*<\s*('[a-z_][a-z0-9_]*)\s*>\s*\(([^)]*)\)\s*->\s*([^{;]*)"
)
ELISION_NEEDLESS_LIFETIME_REC = (
    "elide the lifetime: a single input lifetime is assigned to the "
    "output by elision rules 2/3 (clippy::needless_lifetimes); prefer "
    "`'_` over a named lifetime in paths where one is still required"
)

# A `return <expr>;` statement. Requiring `\S` after `return` excludes a
# bare `return;`. The mixin only flags it when the next non-blank line
# closes the block, i.e. it is the tail, not an early guard.
ELISION_RETURN_STMT_PATTERN = r"^\s*return\s+\S.*;\s*$"
ELISION_NEEDLESS_RETURN_REC = (
    "drop `return` and the semicolon; the block's tail expression is "
    "its value (clippy::needless_return)"
)

# ── Numeric cast-safety patterns (#numeric-cast-safety) ──────
#
# Flags `as` casts that lose information. Grounded in the Rust Reference
# type-cast rules (src/expressions/operator-expr.md): "Casting from a
# larger integer to a smaller integer (e.g. u32 -> u8) will truncate";
# float-to-int saturates and `NaN` maps to 0; integer-to-float and
# f64->f32 round and may lose precision. clippy::cast_possible_truncation
# and clippy::cast_precision_loss.
#
# Direction is undecidable from a single line, so detection anchors on
# shape that *implies* loss rather than on the cast alone:
#   - `.len()`/`.count()`/`.capacity()` return usize (64-bit), so casting
#     their result to a narrower fixed-width int can truncate.
#   - `as u8`/`as i8` target the smallest integer types; a widening cast
#     to them is impossible, so they are essentially always narrowing.
#   - `as f32` is the precision-loss target for f64/i64/u64 sources.

# A usize-width length/size produced by a method call, narrowed by a
# cast. The method names are the common usize-returning queries; the
# target is any fixed-width integer narrower than usize on 64-bit.
NUMERIC_LEN_TRUNCATION_CAST_PATTERN = (
    r"\.(?:len|count|capacity)\(\)\s+as\s+(?:u8|u16|u32|i8|i16|i32)\b"
)
NUMERIC_LEN_TRUNCATION_CAST_REC = (
    "a length/size is usize (64-bit); casting it to a narrower integer "
    "truncates silently. Use `u32::try_from(x.len())?` (or `try_into`) "
    "so an over-large length is an error, not a wrapped value "
    "(clippy::cast_possible_truncation)"
)

# A cast whose target is the smallest integer type. Nothing is narrower
# than a byte, so `as u8`/`as i8` cannot be a widening (lossless) cast.
# `as *const`/`as *mut` (pointer casts) and `as _` are excluded by the
# mixin before this is tested.
NUMERIC_BYTE_CAST_PATTERN = r"\bas\s+(?:u8|i8)\b"
NUMERIC_BYTE_CAST_REC = (
    "casting to `u8`/`i8` cannot widen, so this truncates (and `as` "
    "between signednesses reinterprets the bits). Use `u8::try_from(x)?` "
    "for a checked conversion (clippy::cast_possible_truncation)"
)

# A cast to f32: from f64 this loses mantissa bits, and from i64/u64 it
# loses precision past 2**24. `f32::from(x)` exists only for losslessly
# convertible sources, so reaching for `as` here is the smell.
NUMERIC_F32_CAST_PATTERN = r"\bas\s+f32\b"
NUMERIC_F32_CAST_REC = (
    "casting to `f32` can lose precision (f64 mantissa bits, or integer "
    "magnitudes past 2**24). Prefer `f32::from(x)` where it is lossless, "
    "or make the rounding explicit (clippy::cast_precision_loss)"
)

# Lines that should never trigger numeric-cast findings.
NUMERIC_CAST_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments
    r"\bas\s+\*(?:const|mut)\b",  # pointer casts, not numeric
    r"\bas\s+_\b",  # inferred-target cast, left to the compiler
]

# ── Mutable static patterns (#mutable-static-audit) ──────────
#
# Flags `static mut` declarations. Grounded in the Rust Reference static
# items chapter (src/items/static-items.md): "an `unsafe` block is
# required when either reading or writing a mutable static variable" and
# mutable statics are "a very large source of race conditions or other
# bugs". Reading or writing through a `static mut` reference is the
# deny-by-default `static_mut_refs` lint (Rust 2024).

# A mutable static declaration, with optional visibility/`unsafe`
# qualifiers in front: `static mut X`, `pub static mut X`,
# `pub(crate) static mut X`. `const` does not match (it is not a static).
MUTABLE_STATIC_PATTERN = r"\bstatic\s+mut\s+[A-Za-z_]"
MUTABLE_STATIC_REC = (
    "replace `static mut` with a thread-safe alternative: `OnceLock`/"
    "`LazyLock` for set-once globals, an `Atomic*` for counters/flags, "
    "or a `Mutex`/`RwLock` for shared mutable data. A `static mut` needs "
    "`unsafe` to touch and is a primary source of data races "
    "(deny-by-default `static_mut_refs`)"
)

# Lines that should never trigger mutable-static findings.
MUTABLE_STATIC_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments (covers `///` doc comments too)
]

# ── Match wildcard patterns (#match-wildcard) ────────────────
#
# Flags catch-all `_ =>` arms that defeat the compiler's exhaustiveness
# check. Grounded in the Rust Reference match chapter
# (src/expressions/match-expr.md): match arms must be exhaustive, and a
# wildcard `_` arm satisfies that by matching everything left over. When
# the scrutinee is an enum, an explicit-variant match makes a newly added
# variant a compile error; a `_` arm that panics or is empty turns it
# into a runtime panic or a silently ignored case instead.
# clippy::wildcard_enum_match_arm, clippy::match_wildcard_for_single_variants.
#
# Only the panic / empty forms are flagged. A `_ =>` arm that returns a
# real value is a legitimate default over an open set (integers, chars,
# strings) and is left alone.

# `_ => unreachable!(...)`: a new variant becomes a runtime panic.
MATCH_WILDCARD_UNREACHABLE_PATTERN = r"^\s*_\s*=>\s*unreachable!"
MATCH_WILDCARD_UNREACHABLE_REC = (
    "a `_ => unreachable!()` arm claims exhaustiveness the compiler can "
    "no longer verify; a new enum variant becomes a runtime panic. List "
    "the remaining variants explicitly so the change is a compile error "
    "(clippy::wildcard_enum_match_arm)"
)

# `_ => panic!|todo!|unimplemented!(...)`: same exhaustiveness defeat.
MATCH_WILDCARD_PANIC_PATTERN = r"^\s*_\s*=>\s*(?:panic!|todo!|unimplemented!)"
MATCH_WILDCARD_PANIC_REC = (
    "a `_` arm that panics hides un-handled variants behind a runtime "
    "crash. Match the remaining variants explicitly so the compiler "
    "flags new ones (clippy::wildcard_enum_match_arm)"
)

# `_ => {}`: an empty wildcard arm silently swallows every other case.
MATCH_WILDCARD_EMPTY_PATTERN = r"^\s*_\s*=>\s*\{\s*\}\s*,?\s*$"
MATCH_WILDCARD_EMPTY_REC = (
    "an empty `_ => {}` arm silently ignores every unmatched case; a new "
    "enum variant is dropped without a trace. Handle the variants "
    "explicitly, or make the no-op intentional and documented "
    "(clippy::wildcard_enum_match_arm)"
)

# Lines that should never trigger match-wildcard findings.
MATCH_WILDCARD_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments (covers `///` doc comments too)
]

# ── Transmute-audit patterns (#transmute-audit) ──────────────
#
# Flags `mem::transmute` and `transmute_copy`. The Rust Reference lists
# producing an invalid value (which a wrong-layout transmute does) under
# behavior considered undefined (src/behavior-considered-undefined.md),
# and the std::mem::transmute docs call it "incredibly unsafe". A
# transmute reinterprets the source bytes as the target type with no
# layout check, so it is UB whenever the two layouts disagree.
# clippy::transmute_* family.
#
# `(?<![.\w])` keeps a free `transmute(`/`mem::transmute(` call while
# excluding a method (`x.transmute(`) or a longer name (`transmuter(`).
# `transmute\s*(?:::<|\()` requires a call or turbofish right after the
# name, so `transmuter(` (next char `r`) cannot match.

TRANSMUTE_PATTERN = r"(?<![.\w])transmute\s*(?:::<|\()"
TRANSMUTE_REC = (
    "`transmute` reinterprets bytes with no layout check and is undefined "
    "behavior when the source and target layouts disagree. Prefer a typed "
    "conversion: `f32::from_bits`/`to_le_bytes`/`from_le_bytes` for "
    "number<->bytes, `as`/`.cast()` for pointers, `bytemuck`/`zerocopy` "
    "for plain-old-data, or `From`/`TryFrom` (clippy::transmute_int_to_float "
    "and the transmute_* family)"
)

# `transmute_copy` does not even require the sizes to match and reads
# from a reference; it is strictly more dangerous than `transmute`.
TRANSMUTE_COPY_PATTERN = r"(?<![.\w])transmute_copy\s*\("
TRANSMUTE_COPY_REC = (
    "`transmute_copy` skips even the size check `transmute` enforces and "
    "can read past the source. Use a typed conversion (`from_le_bytes`, "
    "`bytemuck::pod_read_unaligned`) or `ptr::read` with an explicit, "
    "audited safety contract instead"
)

# Lines that should never trigger transmute findings.
TRANSMUTE_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments (covers `///` doc comments too)
]

# ── Float-equality patterns (#float-equality) ────────────────
#
# Flags `==`/`!=` against a floating-point literal. The Rust Reference
# defines `f32`/`f64` as IEEE-754 types (src/types/numeric.md) whose
# arithmetic rounds, so two values that are mathematically equal often
# differ in the last bits. An exact `==` then silently does the wrong
# thing. clippy::float_cmp.
#
# A float literal is detected by a decimal point (`1.5`, `0.0`) or a
# float type suffix (`2f32`, `1.0f64`); an integer literal (`5`) has
# neither and is left alone. The literal may sit on either side of the
# operator, so two patterns cover both directions. `<=`/`>=` are not
# `==`/`!=` and ordering comparisons on floats are legitimate, so they
# do not match.

FLOAT_CMP_RHS_PATTERN = r"(?:==|!=)\s*-?\d+(?:\.\d+(?:f(?:32|64))?|f(?:32|64))\b"
FLOAT_CMP_LHS_PATTERN = r"-?\d+(?:\.\d+(?:f(?:32|64))?|f(?:32|64))\s*(?:==|!=)"
FLOAT_CMP_REC = (
    "comparing floats with `==`/`!=` tests IEEE-754 values for bit-exact "
    "equality, which rounding makes unreliable. Compare against a "
    "tolerance instead: `(a - b).abs() < f64::EPSILON` (or a "
    "domain-appropriate epsilon) (clippy::float_cmp)"
)

# Lines that should never trigger float-equality findings.
FLOAT_CMP_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments (covers `///` doc comments too)
]

# ── Mem-forget patterns (#mem-forget-audit) ──────────────────
#
# Flags `mem::forget(x)` (skips the destructor, leaking the resource)
# and `drop(&x)` (drops a borrow, a no-op, so the owned value lives on).
# The Rust Reference destructors chapter (src/destructors.md) explains
# that `forget` runs no destructor and that `drop` consumes the owned
# value. clippy::mem_forget, clippy::drop_ref.
#
# `(?<![.\w])` keeps a free `forget(`/`mem::forget(`/`drop(` while
# excluding a method (`cache.forget(`, `guard.drop(`) or a longer name.

MEM_FORGET_PATTERN = r"(?<![.\w])forget\s*\("
MEM_FORGET_REC = (
    "`mem::forget` skips the value's destructor, leaking files, locks, or "
    "memory it owns. Use `ManuallyDrop` when you must defer cleanup, hand "
    "ownership across an FFI boundary explicitly, or just let the value "
    "drop at end of scope (clippy::mem_forget)"
)

# `drop(&x)` drops a reference, not the value: a no-op the compiler
# accepts. The real value is never freed at that point.
DROP_REF_PATTERN = r"(?<![.\w])drop\s*\(\s*&"
DROP_REF_REC = (
    "`drop(&x)` drops a reference, which is a no-op: the value still lives "
    "and its destructor has not run. Drop the owned value (`drop(x)`), or "
    "remove the call if the borrow ends here anyway (clippy::drop_ref)"
)

# Lines that should never trigger mem-forget findings.
MEM_FORGET_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments (covers `///` doc comments too)
]

# ── Repr-packed patterns (#repr-packed-audit) ────────────────
#
# Flags `#[repr(packed)]` struct attributes. The Rust Reference
# type-layout chapter (src/type-layout.md) defines the `packed`
# representation, which drops the padding that keeps fields naturally
# aligned. Taking a reference to an under-aligned field is undefined
# behavior; the `unaligned_references` lint makes it a hard error.
#
# Matches `#[repr(packed)]`, `#[repr(C, packed)]`, and `#[repr(packed(2))]`
# while leaving `#[repr(C)]` and `#[repr(transparent)]` alone (no
# `packed` token inside the parentheses).

REPR_PACKED_PATTERN = r"#\s*\[\s*repr\s*\([^)]*\bpacked\b"
REPR_PACKED_REC = (
    "`#[repr(packed)]` under-aligns fields, so borrowing one (`&s.field`, "
    "or any method taking `&self` on the field) creates an unaligned "
    "reference, which is undefined behavior (the `unaligned_references` "
    "hard error). Copy the field into a local first "
    "(`let v = s.field;`) using `{ s }.field` or `ptr::addr_of!`, or drop "
    "`packed` if the layout is not dictated by an external format"
)

# Lines that should never trigger repr-packed findings.
REPR_PACKED_EXCLUSION_PATTERNS: list[str] = [
    r"^\s*//",  # comments (covers `///` doc comments too)
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

# ── Pre-compiled regex (A-01) ────────────────────────────────
#
# These compiled forms are imported by the analyzer mixins so
# patterns are parsed once at module load instead of inside
# per-line scans. Plain string forms above remain the source of
# truth; the compiled forms below are derived mechanically.

UNSAFE_BLOCK_RE = re.compile(UNSAFE_BLOCK_PATTERN)
UNSAFE_FN_RE = re.compile(UNSAFE_FN_PATTERN)
SAFETY_DOC_RE = re.compile(SAFETY_DOC_PATTERN)
RC_REFCELL_RE = re.compile(RC_REFCELL_PATTERN)
RC_NEW_REFCELL_RE = re.compile(RC_NEW_REFCELL_PATTERN)
MIXED_BORROWS_MUT_RE = re.compile(MIXED_BORROWS_MUT_PATTERN)
MIXED_BORROWS_REF_RE = re.compile(MIXED_BORROWS_REF_PATTERN)
ARC_MUTEX_RE = re.compile(ARC_MUTEX_PATTERN)
MUTEX_NEW_RE = re.compile(MUTEX_NEW_PATTERN)
POINTER_OFFSET_RE = re.compile(POINTER_OFFSET_PATTERN)
LARGE_OFFSET_RE = re.compile(LARGE_OFFSET_PATTERN)
LIFETIME_ANNOTATION_RE = re.compile(LIFETIME_ANNOTATION_PATTERN)
PANIC_CALL_RE = re.compile(PANIC_CALL_PATTERN)
UNWRAP_CALL_RE = re.compile(UNWRAP_CALL_PATTERN)
INDEX_ACCESS_RE = re.compile(INDEX_ACCESS_PATTERN)
ASYNC_FN_RE = re.compile(ASYNC_FN_PATTERN)
ASYNC_CALL_RE = re.compile(ASYNC_CALL_PATTERN)
DERIVE_MACRO_RE = re.compile(DERIVE_MACRO_PATTERN)
MACRO_RULES_RE = re.compile(MACRO_RULES_PATTERN)
DOC_COMMENT_RE = re.compile(DOC_COMMENT_PATTERN)
TRAIT_DEF_RE = re.compile(TRAIT_DEF_PATTERN)
TRAIT_METHOD_RE = re.compile(TRAIT_METHOD_PATTERN)
GENERIC_METHOD_RE = re.compile(GENERIC_METHOD_PATTERN)
STATIC_METHOD_RE = re.compile(STATIC_METHOD_PATTERN)
IMPL_FOR_RE = re.compile(IMPL_FOR_PATTERN)
CONST_GENERIC_STRUCT_RE = re.compile(CONST_GENERIC_STRUCT_PATTERN)
CONST_MAX_RE = re.compile(CONST_MAX_PATTERN)
CARGO_DEP_RE = re.compile(CARGO_DEP_PATTERN)
TARGET_SECTION_RE = re.compile(TARGET_SECTION_PATTERN)

# Builtin preference compiled forms

BUILTIN_TO_METHOD_RE = re.compile(BUILTIN_TO_METHOD_PATTERN)
BUILTIN_TO_STRING_RE = re.compile(BUILTIN_TO_STRING_PATTERN)

# Each entry is a triple: compiled regex, trait name, recommendation text.
BUILTIN_CONVERSION_PATTERNS_RE: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(p), t, r) for p, t, r in BUILTIN_CONVERSION_PATTERNS
]
BUILTIN_STANDARD_TRAIT_PATTERNS_RE: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(p), t, r) for p, t, r in BUILTIN_STANDARD_TRAIT_PATTERNS
]
BUILTIN_ERROR_CONVERSION_PATTERNS_RE: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(p), t, r) for p, t, r in BUILTIN_ERROR_CONVERSION_PATTERNS
]
# Each entry: DOTALL-compiled regex, lint name, replacement, clippy lint id.
BUILTIN_MANUAL_COMBINATOR_PATTERNS_RE: list[tuple[re.Pattern[str], str, str, str]] = [
    (re.compile(p, re.DOTALL), n, repl, lint)
    for p, n, repl, lint in BUILTIN_MANUAL_COMBINATOR_PATTERNS
]
BUILTIN_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in BUILTIN_EXCLUSION_PATTERNS
]

# Native type-modeling compiled forms

NATIVE_STRINGLY_COMPARISON_RE = re.compile(NATIVE_STRINGLY_COMPARISON_PATTERN)
NATIVE_BOOLEAN_BLINDNESS_RE = re.compile(NATIVE_BOOLEAN_BLINDNESS_PATTERN)
NATIVE_INT_STATE_CONST_RE = re.compile(NATIVE_INT_STATE_CONST_PATTERN)

# Idiomatic elision compiled forms

ELISION_FN_LIFETIME_SIG_RE = re.compile(ELISION_FN_LIFETIME_SIG_PATTERN)
ELISION_RETURN_STMT_RE = re.compile(ELISION_RETURN_STMT_PATTERN)
NATIVE_MODELING_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in NATIVE_MODELING_EXCLUSION_PATTERNS
]

# Numeric cast-safety compiled forms

NUMERIC_LEN_TRUNCATION_CAST_RE = re.compile(NUMERIC_LEN_TRUNCATION_CAST_PATTERN)
NUMERIC_BYTE_CAST_RE = re.compile(NUMERIC_BYTE_CAST_PATTERN)
NUMERIC_F32_CAST_RE = re.compile(NUMERIC_F32_CAST_PATTERN)
NUMERIC_CAST_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in NUMERIC_CAST_EXCLUSION_PATTERNS
]

# Mutable static compiled forms

MUTABLE_STATIC_RE = re.compile(MUTABLE_STATIC_PATTERN)
MUTABLE_STATIC_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in MUTABLE_STATIC_EXCLUSION_PATTERNS
]

# Match wildcard compiled forms

MATCH_WILDCARD_UNREACHABLE_RE = re.compile(MATCH_WILDCARD_UNREACHABLE_PATTERN)
MATCH_WILDCARD_PANIC_RE = re.compile(MATCH_WILDCARD_PANIC_PATTERN)
MATCH_WILDCARD_EMPTY_RE = re.compile(MATCH_WILDCARD_EMPTY_PATTERN)
MATCH_WILDCARD_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in MATCH_WILDCARD_EXCLUSION_PATTERNS
]

# Transmute-audit compiled forms

TRANSMUTE_RE = re.compile(TRANSMUTE_PATTERN)
TRANSMUTE_COPY_RE = re.compile(TRANSMUTE_COPY_PATTERN)
TRANSMUTE_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in TRANSMUTE_EXCLUSION_PATTERNS
]

# Float-equality compiled forms

FLOAT_CMP_RHS_RE = re.compile(FLOAT_CMP_RHS_PATTERN)
FLOAT_CMP_LHS_RE = re.compile(FLOAT_CMP_LHS_PATTERN)
FLOAT_CMP_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in FLOAT_CMP_EXCLUSION_PATTERNS
]

# Mem-forget compiled forms

MEM_FORGET_RE = re.compile(MEM_FORGET_PATTERN)
DROP_REF_RE = re.compile(DROP_REF_PATTERN)
MEM_FORGET_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in MEM_FORGET_EXCLUSION_PATTERNS
]

# Repr-packed compiled forms

REPR_PACKED_RE = re.compile(REPR_PACKED_PATTERN)
REPR_PACKED_EXCLUSION_PATTERNS_RE: list[re.Pattern[str]] = [
    re.compile(p) for p in REPR_PACKED_EXCLUSION_PATTERNS
]

# ── Idiomatic-elision: explicit unit return (#idiomatic-elision) ──
#
# An explicit `-> ()` writes the unit return type the compiler already
# elides. Grounded in clippy::unused_unit ("Checks for unit `()`
# expressions that can be removed ... add no value, but can make the code
# less readable"). Only the redundant `-> ()` form is flagged.
ELISION_UNIT_RETURN_PATTERN = r"->\s*\(\s*\)"
ELISION_UNIT_RETURN_REC = (
    "drop the explicit `-> ()`; the unit return type is the default and "
    "is elided (clippy::unused_unit)"
)
ELISION_UNIT_RETURN_RE = re.compile(ELISION_UNIT_RETURN_PATTERN)

# ── Coercion params (#coercion-params) ──────────────────────
#
# Flags function/binding types `&String`, `&Vec<T>`, `&PathBuf` that
# defeat deref coercion. Grounded in the Rust Reference type-coercions
# chapter (src/type-coercions.md): "`&T` or `&mut T` to `&U` if `T`
# implements `Deref<Target = U>`", with function arguments listed as a
# coercion site; std Deref impls (String->str, Vec<T>->[T], PathBuf->Path).
# A `&str`/`&[T]`/`&Path` parameter accepts both an owned value's borrow
# and a borrowed one, so it is strictly more general. clippy::ptr_arg.
#
# Detection keys on the typed-binding form `: &Type` (predominantly
# parameters): the colon excludes return types (`-> &String`), and
# requiring `&` adjacent to the type name excludes the load-bearing
# `&mut String`/`&mut Vec<T>` growth cases. An optional lifetime
# (`&'a String`) is tolerated. clippy::ptr_arg deliberately does NOT
# flag `&Box<T>`, so neither does this detector.
_COERCION_REF = r":\s*&(?:'[a-z_][a-z0-9_]*\s+)?"
COERCION_STRING_PARAM_PATTERN = _COERCION_REF + r"String\b"
COERCION_VEC_PARAM_PATTERN = _COERCION_REF + r"Vec\s*<"
COERCION_PATHBUF_PARAM_PATTERN = _COERCION_REF + r"PathBuf\b"
COERCION_STRING_PARAM_REC = (
    "take `&str` instead of `&String`: deref coercion (String: "
    "Deref<Target=str>) lets a caller pass either an owned String's "
    "borrow or a `&str`, so `&str` is strictly more general "
    "(clippy::ptr_arg)"
)
COERCION_VEC_PARAM_REC = (
    "take `&[T]` instead of `&Vec<T>`: deref coercion (Vec<T>: "
    "Deref<Target=[T]>) accepts either a borrowed Vec or a slice, so "
    "`&[T]` is strictly more general (clippy::ptr_arg)"
)
COERCION_PATHBUF_PARAM_REC = (
    "take `&Path` instead of `&PathBuf`: deref coercion (PathBuf: "
    "Deref<Target=Path>) accepts either, so `&Path` is strictly more "
    "general (clippy::ptr_arg)"
)
# A comment line is not code.
COERCION_COMMENT_PATTERN = r"^\s*//"
COERCION_STRING_PARAM_RE = re.compile(COERCION_STRING_PARAM_PATTERN)
COERCION_VEC_PARAM_RE = re.compile(COERCION_VEC_PARAM_PATTERN)
COERCION_PATHBUF_PARAM_RE = re.compile(COERCION_PATHBUF_PARAM_PATTERN)
COERCION_COMMENT_RE = re.compile(COERCION_COMMENT_PATTERN)

# ── Conversion traits (#conversion-traits) ──────────────────
#
# Two conversion smells. Grounded in the Rust API Guidelines
# C-CONV-TRAITS ("never implement `Into`/`TryInto`; the blanket impl
# derives them from `From`/`TryFrom`") and std::convert docs ("always
# prefer implementing `From<T>`/`TryFrom<T>`"); clippy::from_over_into.
#
# 1. `impl Into<X> for Y` should be `impl From<Y> for X` (gives Into for
#    free and composes with `?` via the std error blanket impl). The
#    pattern anchors on a line-leading `impl ... Into<...> for <Type>`,
#    so a generic *bound* `T: Into<U>` (which is correct) is never
#    matched. Group 1 is the target X, group 2 the source Y.
# 2. `.try_into().unwrap()` / `T::try_from(..).unwrap()` discards the
#    error `TryFrom` exists to surface; propagate it with `?` instead.
CONVERSION_IMPL_INTO_PATTERN = (
    r"^\s*impl(?:\s*<[^>]*>)?\s+Into\s*<\s*([^>]+?)\s*>\s+for\s+(\w+)"
)
CONVERSION_IMPL_INTO_REC = (
    "implement `impl From<{src}> for {dst}` instead of `impl Into<{dst}> "
    "for {src}`: From gives the Into impl for free and composes with `?` "
    "(clippy::from_over_into). Exception: if `{dst}` is a foreign type, "
    "the orphan rule forbids the From impl and Into is the only option"
)
CONVERSION_TRY_INTO_UNWRAP_PATTERN = r"\.try_into\(\)\s*\.\s*(?:unwrap|expect)\("
CONVERSION_TRY_FROM_UNWRAP_PATTERN = (
    r"\btry_from\s*\([^)]*\)\s*\.\s*(?:unwrap|expect)\("
)
CONVERSION_DISCARDED_ERROR_REC = (
    "a fallible conversion's error is discarded by `.unwrap()`/"
    "`.expect()`; propagate it with `?` or handle it. `TryFrom` exists "
    "to surface this error rather than panic (clippy::unwrap_used)"
)
CONVERSION_COMMENT_PATTERN = r"^\s*//"
CONVERSION_IMPL_INTO_RE = re.compile(CONVERSION_IMPL_INTO_PATTERN)
CONVERSION_TRY_INTO_UNWRAP_RE = re.compile(CONVERSION_TRY_INTO_UNWRAP_PATTERN)
CONVERSION_TRY_FROM_UNWRAP_RE = re.compile(CONVERSION_TRY_FROM_UNWRAP_PATTERN)
CONVERSION_COMMENT_RE = re.compile(CONVERSION_COMMENT_PATTERN)
